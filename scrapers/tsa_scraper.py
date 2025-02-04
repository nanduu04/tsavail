from dataclasses import dataclass
from typing import List, Optional, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import logging
import asyncio
from pathlib import Path
from pytz import timezone
from firebase_config import initialize_firebase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class WaitTimeData:
    terminal: str
    general_line_wait: str
    tsa_pre_wait: str
    timestamp: str

@dataclass
class AirportData:
    airport: str
    terminals: List[WaitTimeData]

class TSAWaitTimesScraper:
    def __init__(self, headless: bool = True, timeout: int = 10):
        self.timeout = timeout
        self.options = self._setup_chrome_options(headless)
        self.service = Service(ChromeDriverManager().install())
        self.db = initialize_firebase()
        
    def _setup_chrome_options(self, headless: bool) -> webdriver.ChromeOptions:
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        return options
    
    def _create_driver(self) -> webdriver.Chrome:
        return webdriver.Chrome(service=self.service, options=self.options)
    
    def _clean_wait_time(self, time_str: str) -> str:
        if not time_str:
            return 'N/A'
            
        time_str = time_str.lower().strip()
        
        if 'no wait' in time_str:
            return '0'
        if 'closed' in time_str:
            return 'Closed'
        if 'na' in time_str or 'n/a' in time_str:
            return 'N/A'
            
        return ''.join(c for c in time_str if c.isdigit() or c == '-')
    
    async def _scrape_terminal_data(self, row: WebElement) -> Optional[WaitTimeData]:
        try:
            terminal_img = row.find_element(
                By.XPATH,
                ".//td[contains(@class, 'security-first-col')]//div[contains(@class, 'term-text')]//img"
            )
            terminal_name = terminal_img.get_attribute('alt').replace('Terminal ', '')
            
            wait_times = row.find_elements(
                By.XPATH,
                ".//div[contains(@class, 'right-value')]//div[contains(@class, 'NA')]"
            )
            
            general_time = self._clean_wait_time(wait_times[1].text if len(wait_times) > 1 else '')
            tsa_time = self._clean_wait_time(wait_times[2].text if len(wait_times) > 2 else '')
            
            return WaitTimeData(
                terminal=terminal_name,
                general_line_wait=general_time,
                tsa_pre_wait=tsa_time,
                timestamp=datetime.now(timezone('America/New_York')).isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error extracting terminal data: {str(e)}")
            return None
    
    async def scrape_airport(self, url: str, airport_code: str) -> Optional[AirportData]:
        driver = None
        try:
            logger.info(f"Starting scrape for {airport_code} at {url}")
            driver = self._create_driver()
            wait = WebDriverWait(driver, self.timeout)
            
            driver.get(url)
            
            security_table = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'security-table'))
            )
            
            rows = security_table.find_elements(
                By.XPATH,
                ".//tr[contains(@class, 'security-row') or contains(@class, 'odd') or contains(@class, 'even')]"
            )
            
            terminal_data = []
            for row in rows:
                if data := await self._scrape_terminal_data(row):
                    terminal_data.append(data)
            
            if not terminal_data:
                logger.warning(f"No terminal data found for {airport_code}")
                return None
                
            return AirportData(airport=airport_code, terminals=terminal_data)
            
        except Exception as e:
            logger.error(f"Failed to scrape {airport_code}: {str(e)}")
            return None
            
        finally:
            if driver:
                driver.quit()

    def _to_dict(self, obj):
        if isinstance(obj, (AirportData, WaitTimeData)):
            return {
                key: self._to_dict(getattr(obj, key))
                for key in obj.__dataclass_fields__
            }
        elif isinstance(obj, list):
            return [self._to_dict(item) for item in obj]
        else:
            return obj

    def save_to_firebase(self, data: Dict) -> None:
        """Save data to Firebase"""
        try:
            # Convert data to dictionary format
            firebase_data = self._to_dict(data)
            
            # Save current data to 'current' document
            current_ref = self.db.collection('tsa_wait_times').document('current')
            current_ref.set(firebase_data)
            
            # Save historical data
            history_ref = self.db.collection('tsa_wait_times_history')
            history_ref.add(firebase_data)
            
            logger.info("✅ Data saved to Firebase successfully")
            
        except Exception as e:
            logger.error(f"Failed to save to Firebase: {str(e)}")

class TSAWaitTimesManager:
    def __init__(self):
        self.scraper = TSAWaitTimesScraper()
        self.airports = [
            {"url": "https://www.jfkairport.com/", "code": "JFK"},
            {"url": "https://www.newarkairport.com/", "code": "EWR"},
            {"url": "https://www.laguardiaairport.com/", "code": "LGA"}
        ]
    
    async def _scrape_all_airports(self) -> Dict:
        tasks = []
        for airport in self.airports:
            task = self.scraper.scrape_airport(airport["url"], airport["code"])
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return {
            "last_updated": datetime.now(timezone('America/New_York')).isoformat(),
            "airports": [
                self.scraper._to_dict(result)
                for result in results
                if result is not None
            ]
        }
    
    async def run(self) -> None:
        try:
            data = await self._scrape_all_airports()
            self.scraper.save_to_firebase(data)
        except Exception as e:
            logger.error(f"Scraping operation failed: {str(e)}")

async def main():
    manager = TSAWaitTimesManager()
    await manager.run()

if __name__ == "__main__":
    asyncio.run(main())