from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import json
import logging
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirportTSAWaitScraper:
    def __init__(self, url: str, airport_name: str, headless: bool = True):
        """
        Scraper for extracting TSA wait times from airport websites.
        :param url: The URL of the airport security wait time page.
        :param airport_name: The name of the airport being scraped.
        :param headless: Whether to run the browser in headless mode.
        """
        self.BASE_URL = url
        self.AIRPORT_NAME = airport_name
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
        """Clean up time strings, remove unwanted text."""
        return time_str.replace('min', '').strip() if time_str else 'N/A'

    def scrape(self):
        """Scrapes security wait times from the airport's website."""
        try:
            logger.info(f"Scraping TSA wait times for {self.AIRPORT_NAME} ({self.BASE_URL})...")
            self.driver.get(self.BASE_URL)
            
            security_data = []
            
            security_table = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'security-table'))
            )

            security_rows = security_table.find_elements(
                By.XPATH, ".//tr[contains(@class, 'security-row') or contains(@class, 'odd') or contains(@class, 'even')]"
            )

            timestamp = datetime.utcnow().isoformat()

            for row in security_rows:
                try:
                    # Extract terminal name
                    terminal_div = row.find_element(
                        By.XPATH, ".//td[contains(@class, 'security-first-col')]//div[contains(@class, 'term-text')]"
                    )
                    terminal_name = terminal_div.find_element(By.TAG_NAME, "span").text.strip()

                    # Extract wait times
                    times = row.find_elements(
                        By.XPATH, ".//div[contains(@class, 'right-value')]"
                    )

                    general_time = self._clean_time(times[0].text) if len(times) > 0 else 'N/A'
                    tsa_time = self._clean_time(times[1].text) if len(times) > 1 else 'N/A'

                    data = {
                        "terminal": terminal_name,
                        "general_line_wait": general_time,
                        "tsa_pre_wait": tsa_time,
                        "timestamp": timestamp
                    }

                    security_data.append(data)
                    logger.info(f"Scraped {terminal_name}: General={general_time}, TSA Pre✓={tsa_time}")

                except Exception as e:
                    logger.error(f"Error processing security row: {str(e)}")
                    continue

            return security_data

        except Exception as e:
            logger.error(f"Failed to scrape security wait times for {self.AIRPORT_NAME}: {str(e)}")
            return None

        finally:
            self.driver.quit()

def save_to_json(data, filename="../tsa_wait_times.json"):
    """Saves the scraped TSA wait times to a JSON file."""
    try:
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=4)
        logger.info(f"✅ TSA wait times saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving to JSON: {str(e)}")

if __name__ == "__main__":
    # Define multiple airports to scrape
    airports = [
        {"url": "https://www.jfkairport.com/", "name": "JFK"},
        {"url": "https://www.newarkairport.com/", "name": "EWR"},
        {"url": "https://www.laguardiaairport.com/", "name": "LGA"}
    ]

    all_data = {"last_updated": datetime.utcnow().isoformat(), "airports": []}

    for airport in airports:
        with AirportTSAWaitScraper(airport["url"], airport["name"]) as scraper:
            tsa_data = scraper.scrape()
            if tsa_data:
                all_data["airports"].append({"airport": airport["name"], "terminals": tsa_data})

    # Save to JSON
    save_to_json(all_data)
