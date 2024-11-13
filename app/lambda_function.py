import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import logging
import time
from storage import EWRStorage, LGAStorage, JFKStorage

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def setup_chrome():
    chrome_options = Options()
    chrome_options.binary_location = '/opt/chrome/chrome'  # Lambda layer chrome binary path
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--disable-dev-tools')
    chrome_options.add_argument('--no-zygote')
    chrome_options.add_argument('--user-data-dir=/tmp/chrome-user-data')
    
    return webdriver.Chrome(
        executable_path='/opt/chromedriver',
        options=chrome_options
    )

def scrape_airport_data(driver, airport_url):
    """Scrape both security and walk times for an airport"""
    try:
        driver.get(airport_url)
        wait = WebDriverWait(driver, 10)
        
        # Scrape security times
        security_data = []
        security_table = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'security-table'))
        )
        security_rows = security_table.find_elements(
            By.XPATH, ".//tr[contains(@class, 'security-row') or contains(@class, 'odd') or contains(@class, 'even')]"
        )
        
        timestamp = datetime.now().isoformat()
        
        for row in security_rows:
            try:
                terminal_name = extract_terminal_name(row)
                times = row.find_elements(
                    By.XPATH, ".//div[contains(@class, 'right-value')]"
                )
                
                general_time = clean_time(times[1].text) if len(times) > 1 else 'N/A'
                tsa_time = clean_time(times[2].text) if len(times) > 2 else 'N/A'
                
                security_data.append({
                    "terminal": terminal_name,
                    "general_line": general_time,
                    "tsa_pre": tsa_time,
                    "timestamp": timestamp
                })
            except Exception as e:
                logger.error(f"Error processing security row: {str(e)}")
                continue
        
        # Scrape walk times
        walk_times = []
        walk_time_div = wait.until(
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
                            
                            walk_times.append({
                                "terminal": term_name,
                                "gate": gate_text,
                                "walk_time": clean_time(walk_time),
                                "timestamp": timestamp
                            })
                    except Exception as e:
                        logger.error(f"Error processing gate in {term_name}: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error processing terminal: {str(e)}")
                continue
                
        return security_data, walk_times
        
    except Exception as e:
        logger.error(f"Error scraping airport data: {str(e)}")
        return None, None

def extract_terminal_name(row):
    """Extract terminal name from security table row"""
    try:
        return row.find_element(
            By.XPATH, ".//td[contains(@class, 'security-first-col')]//div[contains(@class, 'term-text')]//span"
        ).text.strip()
    except:
        try:
            img = row.find_element(
                By.XPATH, ".//td[contains(@class, 'security-first-col')]//img"
            )
            return img.get_attribute("title") or img.get_attribute("alt") or "Unknown Terminal"
        except:
            return "Unknown Terminal"

def clean_time(time_str):
    """Clean up time strings"""
    return time_str.replace('min', '').strip()

def lambda_handler(event, context):
    try:
        # Initialize storage
        ewr_storage = EWRStorage()
        lga_storage = LGAStorage()
        jfk_storage = JFKStorage()
        
        # Initialize webdriver
        driver = setup_chrome()
        
        try:
            # Scrape EWR
            logger.info("Starting EWR scrape...")
            security_data, walk_data = scrape_airport_data("https://www.newarkairport.com/")
            if security_data:
                ewr_storage.create_security_times(security_data)
            if walk_data:
                ewr_storage.create_walk_times(walk_data)
            
            # Scrape LGA
            logger.info("Starting LGA scrape...")
            security_data, walk_data = scrape_airport_data("https://www.laguardiaairport.com/")
            if security_data:
                lga_storage.create_security_times(security_data)
            if walk_data:
                lga_storage.create_walk_times(walk_data)
            
            # Scrape JFK
            logger.info("Starting JFK scrape...")
            security_data, walk_data = scrape_airport_data("https://www.jfkairport.com/")
            if security_data:
                jfk_storage.create_security_times(security_data)
            if walk_data:
                jfk_storage.create_walk_times(walk_data)
            
        finally:
            # Always close the driver
            driver.quit()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Airport data scraped successfully',
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }