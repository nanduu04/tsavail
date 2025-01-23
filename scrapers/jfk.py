from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
from typing import List, Dict, Optional
import logging
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JFKScraper:
    def __init__(self, headless: bool = True):
        self.BASE_URL = 'https://www.jfkairport.com/'
        self.TIMEOUT = 10
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, self.TIMEOUT)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()

    def _clean_time(self, time_str: str) -> str:
        """Clean up time strings"""
        return time_str.replace('min', '').strip()

    def scrape(self) -> Optional[List[Dict]]:
        try:
            logger.info("Starting JFK security wait time scrape")
            self.driver.get(self.BASE_URL)
            
            security_data = []
            security_table = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'security-table'))
            )
            
            security_rows = security_table.find_elements(
                By.XPATH, ".//tr[contains(@class, 'security-row') or contains(@class, 'odd') or contains(@class, 'even')]"
            )
            
            timestamp = datetime.now().isoformat()
            
            for row in security_rows:
                try:
                    # Get terminal name
                    terminal_div = row.find_element(
                        By.XPATH, ".//td[contains(@class, 'security-first-col')]//div[contains(@class, 'term-text')]"
                    )
                    terminal_name = terminal_div.find_element(By.TAG_NAME, "span").text.strip()
                    
                    # Get wait times
                    times = row.find_elements(
                        By.XPATH, ".//div[contains(@class, 'right-value')]"
                    )
                    
                    general_time = self._clean_time(times[0].text) if len(times) > 0 else 'N/A'
                    tsa_time = self._clean_time(times[1].text) if len(times) > 1 else 'N/A'
                    
                    data = {
                        "terminal": terminal_name,
                        "general_line": general_time,
                        "tsa_pre": tsa_time,
                        "timestamp": timestamp
                    }
                    
                    security_data.append(data)
                    logger.info(f"Security times for {terminal_name}: General={general_time}, TSA Pre✓={tsa_time}")
                    
                except Exception as e:
                    logger.error(f"Error processing security row: {str(e)}")
                    continue
            
            return security_data
                
        except Exception as e:
            logger.error(f"Failed to scrape security wait times: {str(e)}")
            return None
        finally:
            self.driver.quit()