from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
# Set up the WebDriver (Chrome in this case)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# URL of the JFK Airport page with walk times
url = 'https://www.jfkairport.com/'

# Open the URL
driver.get(url)
time.sleep(5)

# Wait for the elements to be present
driver.implicitly_wait(10)

# Locate the section with walk times
walk_time_div = driver.find_element(By.ID, "walk-timeDiv")

# Extract terminal information
terminals = walk_time_div.find_elements(By.CLASS_NAME, "terminal-container")

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

# Loop through terminals and print walk times
for terminal in terminals:
    term_name, gate_times = extract_gate_times(terminal)
    print(f"Terminal: {term_name}")
    for gate, time in gate_times.items():
        print(f"  {gate}: {time} mins")

# Close the WebDriver
driver.quit()