from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import schedule
import logging
from datetime import datetime
from storage import MongoDBStorage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class AirportScraper:
    def __init__(self):
        self.setup_driver()
    
    def setup_driver(self):
        """Initialize or reinitialize the Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            logging.info("Chrome driver initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise

    def scrape_lga(self):
            url = 'https://www.laguardiaairport.com/'
            self.driver.get(url)
            self.driver.implicitly_wait(10)

            walk_time_div = self.driver.find_element(By.ID, "walk-timeDiv")
            terminals = walk_time_div.find_elements(By.CLASS_NAME, "terminal-container")
            lga_data = []

            for terminal in terminals:
                term_name = terminal.find_element(By.CLASS_NAME, "term-no").text
                gates = terminal.find_elements(By.CLASS_NAME, "test")
                
                for gate in gates:
                    lga_data.append({
                        "Terminal": term_name,
                        "Gate": gate.find_element(By.TAG_NAME, "td").text.strip(),
                        "Walk Time": gate.find_element(By.CLASS_NAME, "lg-numbers").text.strip()
                    })

            storage = MongoDBStorage()
            for entry in lga_data:
                storage.create_lga_data(entry)

            logging.info(f"Successfully scraped LGA data: {len(lga_data)} entries")
            return True    

    def scrape_jfk(self):
        try:
            url = 'https://www.jfkairport.com/'
            self.driver.get(url)
            self.driver.implicitly_wait(10)

            walk_time_div = self.driver.find_element(By.ID, "walk-timeDiv")
            terminals = walk_time_div.find_elements(By.CLASS_NAME, "terminal-container")
            jfk_data = []

            for terminal in terminals:
                term_name = terminal.find_element(By.CLASS_NAME, "term-no").text
                gates = terminal.find_elements(By.CLASS_NAME, "test")
                
                for gate in gates:
                    jfk_data.append({
                        "Terminal": term_name,
                        "Gate": gate.find_element(By.TAG_NAME, "td").text.strip(),
                        "Walk Time": gate.find_element(By.CLASS_NAME, "lg-numbers").text.strip()
                    })

            storage = MongoDBStorage()
            for entry in jfk_data:
                storage.create_jfk_data(entry)

            logging.info(f"Successfully scraped JFK data: {len(jfk_data)} entries")
            return True
        except Exception as e:
            logging.error(f"Error scraping JFK: {str(e)}")
            return False

    def scrape_ewr(self):
        url = 'https://www.newarkairport.com/'
        self.driver.get(url)
        self.driver.implicitly_wait(10)

        walk_time_div = self.driver.find_element(By.ID, "walk-timeDiv")
        terminals = walk_time_div.find_elements(By.CLASS_NAME, "terminal-container")
        ewr_data = []

        for terminal in terminals:
            term_name = terminal.find_element(By.CLASS_NAME, "term-no").text
            gates = terminal.find_elements(By.CLASS_NAME, "test")
            
            for gate in gates:
                ewr_data.append({
                    "Terminal": term_name,
                    "Gate": gate.find_element(By.TAG_NAME, "td").text.strip(),
                    "Walk Time": gate.find_element(By.CLASS_NAME, "lg-numbers").text.strip()
                })

        storage = MongoDBStorage()
        for entry in ewr_data:
            storage.create_ewr_data(entry)

        logging.info(f"Successfully scraped EWR data: {len(ewr_data)} entries")
        return True    

    def run_all_scrapers(self):
        """Run all scrapers and handle any failures"""
        logging.info("Starting scraping job")
        try:
            # Reinitialize the driver for each run to prevent stale sessions
            self.setup_driver()
            
            self.scrape_lga()
            self.scrape_jfk()
            self.scrape_ewr()
            
            logging.info("Completed scraping job successfully")
        except Exception as e:
            logging.error(f"Error in scraping job: {str(e)}")
        finally:
            try:
                self.driver.quit()
                logging.info("Chrome driver closed successfully")
            except Exception as e:
                logging.error(f"Error closing Chrome driver: {str(e)}")

def main():
    scraper = AirportScraper()
    
    # Schedule the scraping job to run every 15 minutes
    schedule.every(15).minutes.do(scraper.run_all_scrapers)
    
    # Run once immediately on startup
    scraper.run_all_scrapers()
    
    logging.info("Scraper scheduled to run every 15 minutes")
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()