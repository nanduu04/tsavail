from storage import JFKStorage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import time
from abc import ABC, abstractmethod
import schedule
import sys
from contextlib import contextmanager
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure logging with rotation
log_file = Path("logs/jfk_scraper.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

class JFKScraperException(Exception):
    """Custom exception for JFK scraper specific errors"""
    pass

@contextmanager
def error_handler(operation: str):
    """Context manager for handling errors with specific operation context"""
    try:
        yield
    except Exception as e:
        logger.error(f"Error during {operation}: {str(e)}", exc_info=True)
        raise JFKScraperException(f"Failed during {operation}: {str(e)}")

class BasejfkScraper(ABC):
    """Base class for JFK scrapers with common functionality"""
    
    BASE_URL = 'https://www.jfkairport.com/'
    TIMEOUT = 10
    MAX_RETRIES = 3
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.wait = None
    
    def _setup_driver(self) -> None:
        """Set up Chrome driver with retry logic"""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-notifications')
        options.add_argument('--log-level=3')  # Suppress console logging
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, self.TIMEOUT)
            self.driver.set_page_load_timeout(self.TIMEOUT)
        except Exception as e:
            raise JFKScraperException(f"Failed to initialize Chrome driver: {str(e)}")
    
    def __enter__(self):
        with error_handler("driver setup"):
            self._setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing driver: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((TimeoutException, NoSuchElementException))
    )
    def _safe_get(self, url: str) -> None:
        """Safely navigate to URL with retry logic"""
        self.driver.get(url)
        time.sleep(2)  # Allow for dynamic content to load
    
    def _clean_time(self, time_str: str) -> str:
        """Clean up time strings by removing 'min' and extra whitespace"""
        return time_str.replace('min', '').strip()
    
    @abstractmethod
    def scrape(self) -> Optional[List[Dict]]:
        pass

class JFKSecurityWaitTimeScraper(BasejfkScraper):
    """Class to handle scraping of JFK Airport security wait times"""
    
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
            return img.get_attribute("title") or img.get_attribute("alt") or "Unknown Terminal"
        except NoSuchElementException:
            return "Unknown Terminal"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def scrape(self) -> Optional[List[Dict]]:
        try:
            with error_handler("security wait time scrape"):
                logger.info("Starting JFK security wait time scrape")
                self._safe_get(self.BASE_URL)
                
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
                        terminal_name = self._extract_terminal_name(row)
                        
                        times = row.find_elements(
                            By.XPATH, ".//div[contains(@class, 'right-value')]"
                        )
                        timesNA = row.find_elements(
                            By.XPATH, ".//div[contains(@class, 'NA')]"
                        )
                        
                        general_time = self._clean_time(times[0].text) if len(times) > 1 else 'N/A'
                        tsa_time = self._clean_time(times[1].text) if len(timesNA) > 1 else 'N/A'
                        
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
            logger.error(f"Failed to scrape security wait times: {str(e)}", exc_info=True)
            return None

class JFKWalkTimeScraper(BasejfkScraper):
    """Class to handle scraping of JFK Airport walk times"""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def scrape(self) -> Optional[List[Dict]]:
        try:
            with error_handler("walk time scrape"):
                logger.info("Starting JFK walk time scrape")
                self._safe_get(self.BASE_URL)
                
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
                                    
                                    walk_time = self._clean_time(walk_time)
                                    
                                    data = {
                                        "terminal": term_name,
                                        "gate": gate_text,
                                        "walk_time": walk_time,
                                        "timestamp": timestamp
                                    }
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
            logger.error(f"Failed to scrape walk times: {str(e)}", exc_info=True)
            return None

class JFKScheduler:
    def __init__(self, interval_minutes: int = 3):
        self.interval = interval_minutes
        self.is_running = False
        self.last_run = None
        self.db_storage = JFKStorage()
    
    def start(self):
        """Start the scheduler"""
        try:
            schedule.every(self.interval).minutes.do(self._run_task)
            self.is_running = True
            
            logger.info(f"Scheduler started. Running JFK scraper every {self.interval} minutes...")
            
            # Run immediately on start
            self._run_task()
            
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            self.stop()
    
    def stop(self):
        """Stop the scheduler gracefully"""
        self.is_running = False
        logger.info("Scheduler stopping...")
    
    def _run_task(self):
        """Run the scraping task with error handling"""
        try:
            logger.info("Starting scheduled task...")
            
            # Run security scraper
            with JFKSecurityWaitTimeScraper(headless=True) as security_scraper:
                security_data = security_scraper.scrape()
                if security_data:
                    logger.info("Saving JFK security wait time data to MongoDB...")
                    self.db_storage.create_security_times(security_data)
            
            # Run walk time scraper
            with JFKWalkTimeScraper(headless=True) as walk_scraper:
                walk_data = walk_scraper.scrape()
                if walk_data:
                    logger.info("Saving JFK walk time data to MongoDB...")
                    self.db_storage.create_walk_times(walk_data)
            
            self.last_run = datetime.now()
            logger.info("Scheduled task completed successfully")
            
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}", exc_info=True)

def main():
    """Main entry point for the application"""
    try:
        scheduler = JFKScheduler(interval_minutes=6)
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()