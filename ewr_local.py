from app.storage import EWRStorage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional
import time
from abc import ABC, abstractmethod

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ewr_scraper.log')
    ]
)
logger = logging.getLogger(__name__)

class ewrScraperException(Exception):
    """Custom exception for ewr scraper specific errors"""
    pass

class BaseewrScraper(ABC):
    """Base class for ewr scrapers with common functionality"""
    
    BASE_URL = 'https://www.newarkairport.com/'
    TIMEOUT = 10
    
    def __init__(self, headless: bool = True, output_dir: str = "data"):
        """
        Initialize the base scraper with configuration options.
        
        Args:
            headless (bool): Whether to run Chrome in headless mode
            output_dir (str): Directory to save output files
        """
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.driver = None
        self.wait = None
    
    def __enter__(self):
        """Set up the Chrome driver when entering context"""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless=new')  # Updated for newer Chrome versions
        
        # Add additional Chrome options for stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, self.TIMEOUT)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the Chrome driver when exiting context"""
        if self.driver:
            self.driver.quit()
    
    def _save_to_json(self, data: List[Dict], prefix: str):
        """Save scraped data to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.output_dir / f'{prefix}_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        
        logger.info(f"Saved {len(data)} entries to {filename}")
    
    @abstractmethod
    def scrape(self):
        """Abstract method to be implemented by child classes"""
        pass

class ewrSecurityWaitTimeScraper(BaseewrScraper):
    """Class to handle scraping of LaGuardia Airport security wait times"""
    
    def _clean_time(self, time_str: str) -> str:
        """Clean up time strings by removing 'min' and extra whitespace"""
        return time_str.replace('min', '').strip()
    
    def _extract_terminal_name(self, row) -> str:
        """Extract terminal name from the security table row"""
        try:
            # First try: Look for terminal text in span element
            terminal_div = row.find_element(
                By.XPATH, ".//td[contains(@class, 'security-first-col')]//div[contains(@class, 'term-text')]"
            )
            span_text = terminal_div.find_element(By.TAG_NAME, "span").text.strip()
            if span_text:
                return span_text
        except NoSuchElementException:
            pass

        try:
            # Second try: Get from image title attribute
            img = row.find_element(
                By.XPATH, ".//td[contains(@class, 'security-first-col')]//img"
            )
            title = img.get_attribute("title")
            if title:
                return title
        except NoSuchElementException:
            pass

        try:
            # Third try: Get from alt attribute
            img = row.find_element(
                By.XPATH, ".//td[contains(@class, 'security-first-col')]//img"
            )
            alt = img.get_attribute("alt")
            if alt:
                return alt
        except NoSuchElementException:
            pass

        return "Unknown Terminal"
    
    def scrape(self) -> Optional[List[Dict]]:
        """
        Scrape security wait times for all terminals.
        
        Returns:
            List of dictionaries containing terminal security times,
            or None if scraping fails
        """
        try:
            logger.info("Starting ewr security wait time scrape")
            self.driver.get(self.BASE_URL)
            
            # Add a small delay to ensure page loads completely
            time.sleep(2)
            
            security_data = []
            security_table = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'security-table'))
            )
            
            # Updated selector to get security rows
            security_rows = security_table.find_elements(
                By.XPATH, ".//tr[contains(@class, 'security-row') or contains(@class, 'odd') or contains(@class, 'even')]"
            )
            
            timestamp = datetime.now().isoformat()
            
            for row in security_rows:
                try:
                    terminal_name = self._extract_terminal_name(row)
                    
                    # Get security times
                    times = row.find_elements(
                        By.XPATH, ".//div[contains(@class, 'right-value')]"
                    )
                    
                    # Skip the first element as it's usually empty or contains different information
                    general_time = self._clean_time(times[1].text) if len(times) > 1 else 'N/A'
                    tsa_time = self._clean_time(times[2].text) if len(times) > 2 else 'N/A'
                    
                    data = {
                        "terminal": terminal_name,
                        "general_line": general_time,
                        "tsa_pre": tsa_time,
                        "timestamp": timestamp
                    }
                    
                    security_data.append(data)
                    logger.info(f"Security times for {terminal_name}: General={general_time}, TSA Pre✓={tsa_time}")
                    
                except (NoSuchElementException, IndexError) as e:
                    logger.error(f"Error processing security row: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error processing security row: {str(e)}")
                    continue
            
            if security_data:
                self._save_to_json(security_data, "security_times")
            return security_data
            
        except Exception as e:
            logger.error(f"Error in security wait time scraper: {str(e)}", exc_info=True)
            return None

class ewrWalkTimeScraper(BaseewrScraper):
    """Class to handle scraping of LaGuardia Airport walk times"""
    
    def _clean_time(self, time_str: str) -> str:
        """Clean up time strings by removing 'min' and extra whitespace"""
        return time_str.replace('min', '').strip()
    
    def scrape(self) -> Optional[List[Dict]]:
        """
        Scrape walk times for all terminals and gates.
        
        Returns:
            List of dictionaries containing terminal and gate walk times,
            or None if scraping fails
        """
        try:
            logger.info("Starting ewr walk time scrape")
            self.driver.get(self.BASE_URL)
            
            # Add a small delay to ensure page loads completely
            time.sleep(2)
            
            walk_times = []
            walk_time_div = self.wait.until(
                EC.presence_of_element_located((By.ID, "walk-timeDiv"))
            )
            
            terminals = walk_time_div.find_elements(By.CLASS_NAME, "terminal-container")
            timestamp = datetime.now().isoformat()
            
            for terminal in terminals:
                try:
                    term_name = terminal.find_element(By.CLASS_NAME, "term-no").text.strip()
                    
                    gates = terminal.find_elements(
                        By.XPATH, ".//tr[contains(@class, 'test')]"
                    )
                    
                    for gate in gates:
                        try:
                            gate_cells = gate.find_elements(By.TAG_NAME, "td")
                            if len(gate_cells) >= 2:
                                gate_text = gate_cells[0].text.strip()
                                walk_time = gate_cells[1].find_element(
                                    By.CLASS_NAME, "lg-numbers"
                                ).text.strip()
                                
                                # Clean the walk time
                                walk_time = self._clean_time(walk_time)
                                
                                data = {
                                    "terminal": term_name,
                                    "gate": gate_text,
                                    "walk_time": walk_time,
                                    "timestamp": timestamp
                                }
                                walk_times.append(data)
                                logger.debug(f"Processed: {term_name} - {gate_text}")
                                
                        except (NoSuchElementException, IndexError) as e:
                            logger.error(f"Error processing gate in {term_name}: {str(e)}")
                            continue
                            
                except NoSuchElementException as e:
                    logger.error(f"Error processing terminal: {str(e)}")
                    continue
            
            if walk_times:
                self._save_to_json(walk_times, "walk_times")
            return walk_times
            
        except Exception as e:
            logger.error(f"Error in walk time scraper: {str(e)}", exc_info=True)
            return None


def main_ewr():
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize EWR MongoDB storage
    db_storage = EWRStorage()
    
    with ewrSecurityWaitTimeScraper(headless=True, output_dir=output_dir) as security_scraper:
        security_data = security_scraper.scrape()
        if security_data:
            logger.info("\nSaving EWR security wait time data to MongoDB...")
            db_storage.create_security_times(security_data)
            logger.info("Successfully saved EWR security wait time data")
    
    with ewrWalkTimeScraper(headless=True, output_dir=output_dir) as walk_scraper:
        walk_data = walk_scraper.scrape()
        if walk_data:
            logger.info("\nSaving EWR walk time data to MongoDB...")
            db_storage.create_walk_times(walk_data)
            logger.info("Successfully saved EWR walk time data")

if __name__ == "__main__":
    main_ewr()