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

class TorontoPearsonScraper:
    def __init__(self, headless: bool = True):
        """
        Scraper for extracting TSA wait times from Toronto Pearson Airport website.
        :param headless: Whether to run the browser in headless mode.
        """
        self.BASE_URL = "https://www.torontopearson.com/en/departures"  # Update with correct page
        self.TIMEOUT = 10

        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, self.TIMEOUT)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()

    def scrape(self):
        """Scrapes Toronto Pearson Airport security wait times."""
        try:
            logger.info("Scraping Toronto Pearson TSA wait times...")
            self.driver.get(self.BASE_URL)

            security_data = []

            # Find all "wait-time-card" sections
            wait_time_cards = self.wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "wait-time-card"))
            )

            timestamp = datetime.utcnow().isoformat()

            for card in wait_time_cards:
                try:
                    # Extract category (Canada, International, USA)
                    category = card.find_element(By.CLASS_NAME, "wait-time-card__title").text.strip()

                    # Extract terminal details
                    wait_time_contents = card.find_elements(
                        By.CLASS_NAME, "wait-time-card__content"
                    )

                    for content in wait_time_contents:
                        terminal = content.find_element(
                            By.CLASS_NAME, "wait-time-card__terminal"
                        ).text.strip()

                        wait_time = content.find_element(
                            By.CLASS_NAME, "wait-time-card__wait-time"
                        ).text.strip()

                        security_data.append({
                            "category": category,
                            "terminal": terminal,
                            "wait_time": wait_time,
                            "timestamp": timestamp
                        })

                        logger.info(f"Scraped {category} - {terminal}: {wait_time}")

                except NoSuchElementException:
                    logger.error("Error extracting wait time details.")
                    continue

            return security_data

        except Exception as e:
            logger.error(f"Failed to scrape security wait times for Toronto Pearson: {str(e)}")
            return None

        finally:
            self.driver.quit()

def save_to_json(data, filename="toronto_wait_times.json"):
    """Saves the scraped TSA wait times to a JSON file."""
    try:
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=4)
        logger.info(f"✅ TSA wait times saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving to JSON: {str(e)}")

if __name__ == "__main__":
    with TorontoPearsonScraper() as scraper:
        wait_times = scraper.scrape()
        if wait_times:
            save_to_json(wait_times)
