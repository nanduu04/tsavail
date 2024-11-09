from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from storage import JsonStorage

# Set up Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Optional: run Chrome in headless mode

# Set up the WebDriver with the ChromeDriverManager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Function to scrape LaGuardia Airport TSA wait times
def scrape_lga():
    # Open the LaGuardia Airport TSA wait times page
    url = "https://www.laguardiaairport.com/"
    driver.get(url)

    # Wait for the page to load
    time.sleep(5)

    # Find the table containing the security wait times
    table = driver.find_element(By.CLASS_NAME, 'security-table')

    # Extract all rows of the table (excluding the header)
    rows = table.find_elements(By.TAG_NAME, 'tr')

    # Initialize a list to store the scraped data
    security_data = []

    # Loop through each row to extract the required information
    for row in rows:
        columns = row.find_elements(By.TAG_NAME, 'td')
        
        if len(columns) > 0:  # Ensure it's a valid row with data
            terminal = columns[0].text.strip()
            general_line = columns[4].text.strip()
            tsa_pre = columns[5].text.strip()
            
            # Create a dictionary for each scraped entry
            data = {
                "Terminal": terminal,
                "General Line Wait Time": general_line,
                "TSA Pre✓ Line Wait Time": tsa_pre
            }
            
            # Append to the list of security data
            security_data.append(data)

    # Create an instance of JsonStorage
    storage = JsonStorage()

    # Add the scraped data to the JSON file using create_lga_data
    for entry in security_data:
        # You can add additional metadata or modify the structure if needed
        storage.create_lga_data(entry)

    # Print confirmation of saved data
    print(f"Saved {len(security_data)} entries to LGA data.")

# Function to scrape JFK Airport walk times
def scrape_jfk():
    # URL of the JFK Airport page with walk times
    url = 'https://www.jfkairport.com/'
    driver.get(url)
    # time.sleep(5)

    # Wait for the elements to be present
    driver.implicitly_wait(10)

    # Locate the section with walk times
    walk_time_div = driver.find_element(By.ID, "walk-timeDiv")

    # Extract terminal information
    terminals = walk_time_div.find_elements(By.CLASS_NAME, "terminal-container")

    # Initialize a list to store the scraped data
    jfk_data = []

    # Function to extract gate times
    def extract_gate_times(terminal):
        term_name = terminal.find_element(By.CLASS_NAME, "term-no").text
        gates = terminal.find_elements(By.CLASS_NAME, "test")
        gate_times = {}
        for gate in gates:
            gate_name = gate.find_element(By.TAG_NAME, "td").text.strip()
            walk_time = gate.find_element(By.CLASS_NAME, "lg-numbers").text.strip()
            gate_times[gate_name] = walk_time
        return term_name, gate_times

    # Loop through terminals and store walk times
    for terminal in terminals:
        term_name, gate_times = extract_gate_times(terminal)
        for gate, time in gate_times.items():
            data = {
                "Terminal": term_name,
                "Gate": gate,
                "Walk Time": time
            }
            jfk_data.append(data)
    
    # Create an instance of JsonStorage
    storage = JsonStorage()

    # Add the scraped data to the JSON file using create_jfk_data
    for entry in jfk_data:
        storage.create_jfk_data(entry)

    # Print confirmation of saved data
    print(f"Saved {len(jfk_data)} entries to JFK data.")


def scrape_ewr():
    # Open the Newark Airport TSA wait times page
    url = "https://www.newarkairport.com/"
    driver.get(url)

    # Wait for the page to load
    time.sleep(5)

    # Find the table containing the security wait times
    table = driver.find_element(By.CLASS_NAME, 'security-table')

    # Extract all rows of the table (excluding the header)
    rows = table.find_elements(By.TAG_NAME, 'tr')

    # Initialize a list to store the scraped data
    ewr_data = []

    # Loop through each row to extract the required information
    for row in rows:
        columns = row.find_elements(By.TAG_NAME, 'td')
        
        if len(columns) > 0:
            terminal = columns[0].text.strip()
            general_line = columns[4].text.strip()
            tsa_pre = columns[5].text.strip()
            
            data = {
                "Terminal": terminal,
                "General Line Wait Time": general_line,
                "TSA Pre✓ Line Wait Time": tsa_pre
            }
            
            ewr_data.append(data)

    storage = JsonStorage()

    for entry in ewr_data:
        storage.create_ewr_data(entry)

    print(f"Saved {len(ewr_data)} entries to EWR data.")

# Run the scraping functions
# scrape_lga()
# scrape_jfk()
scrape_ewr() 
# Close the browser after scraping
driver.quit()