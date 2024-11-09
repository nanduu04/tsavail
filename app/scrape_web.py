from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
from app.storage import JsonStorage  # Import your storage class

# Set up Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Optional: run Chrome in headless mode

# Set up the WebDriver with the ChromeDriverManager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

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

# Close the browser after scraping
driver.quit()