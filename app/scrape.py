from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import logging
from typing import Dict, List, Optional
import time
from abc import ABC, abstractmethod
from storage import MongoDBStorage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('lga_scraper.log')
    ]
)
logger = logging.getLogger(__name__)

class LGAScraperException(Exception):
    """Custom exception for LGA scraper specific errors"""
    pass

class BaseLGAScraper(ABC):
    """Base class for LGA scrapers with common functionality"""
    
    BASE_URL = 'https://www.laguardiaairport.com/'
    TIMEOUT = 10
    
    def __init__(self, headless: bool = True):
        """
        Initialize the base scraper with configuration options.
        
        Args:
            headless (bool): Whether to run Chrome in headless mode
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        try:
            self.storage = MongoDBStorage()
            logger.info("MongoDB storage initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB storage: {str(e)}")
            raise
    
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
    
    @abstractmethod
    def scrape(self):
        """Abstract method to be implemented by child classes"""
        pass

class LGASecurityWaitTimeScraper(BaseLGAScraper):
    """Class to handle scraping of LaGuardia Airport security wait times"""
    
    def _clean_time(self, time_str: str) -> str:
        """Clean up time strings by removing 'min' and extra whitespace"""
        return time_str.replace('min', '').strip()
    
    def _extract_terminal_name(self, row) -> str:
        """Extract terminal name from the security table row"""
        try:
            terminal_div = row.find_element(
                By.XPATH, ".//td[contains(@class, 'security-first-col')]//div[contains(@class, 'term-text')]"
            )
            span_text = terminal_div.find_element(By.TAG_NAME, "span").text.strip()
            if span_text:
                return span_text
        except NoSuchElementException:
            pass

        try:
            img = row.find_element(
                By.XPATH, ".//td[contains(@class, 'security-first-col')]//img"
            )
            title = img.get_attribute("title")
            if title:
                return title
        except NoSuchElementException:
            pass

        try:
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
            logger.info("Starting LGA security wait time scrape")
            self.driver.get(self.BASE_URL)
            time.sleep(2)
            
            security_data = []
            security_table = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'security-table'))
            )
            
            security_rows = security_table.find_elements(
                By.XPATH, ".//tr[contains(@class, 'security-row') or contains(@class, 'odd') or contains(@class, 'even')]"
            )
            
            for row in security_rows:
                try:
                    terminal_name = self._extract_terminal_name(row)
                    times = row.find_elements(
                        By.XPATH, ".//div[contains(@class, 'right-value')]"
                    )
                    
                    general_time = self._clean_time(times[1].text) if len(times) > 1 else 'N/A'
                    tsa_time = self._clean_time(times[2].text) if len(times) > 2 else 'N/A'
                    
                    data = {
                        "terminal": terminal_name,
                        "general_line": general_time,
                        "tsa_pre": tsa_time,
                        "type": "security"
                    }
                    
                    # Store in MongoDB
                    self.storage.create_lga_data(data)
                    security_data.append(data)
                    logger.info(f"Security times for {terminal_name}: General={general_time}, TSA Pre✓={tsa_time}")
                    
                except Exception as e:
                    logger.error(f"Error processing security row: {str(e)}")
                    continue
            
            return security_data
            
        except Exception as e:
            logger.error(f"Error in security wait time scraper: {str(e)}", exc_info=True)
            return None

class LGAWalkTimeScraper(BaseLGAScraper):
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
            logger.info("Starting LGA walk time scrape")
            self.driver.get(self.BASE_URL)
            time.sleep(2)
            
            walk_times = []
            walk_time_div = self.wait.until(
                EC.presence_of_element_located((By.ID, "walk-timeDiv"))
            )
            
            terminals = walk_time_div.find_elements(By.CLASS_NAME, "terminal-container")
            
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
                                
                                walk_time = self._clean_time(walk_time)
                                
                                data = {
                                    "terminal": term_name,
                                    "gate": gate_text,
                                    "walk_time": walk_time,
                                    "type": "walk"
                                }
                                
                                # Store in MongoDB
                                self.storage.create_lga_data(data)
                                walk_times.append(data)
                                logger.debug(f"Processed: {term_name} - {gate_text}")
                                
                        except Exception as e:
                            logger.error(f"Error processing gate in {term_name}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error processing terminal: {str(e)}")
                    continue
            
            return walk_times
            
        except Exception as e:
            logger.error(f"Error in walk time scraper: {str(e)}", exc_info=True)

