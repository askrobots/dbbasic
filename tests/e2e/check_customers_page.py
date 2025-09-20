#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Setup Chrome options
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

try:
    # Load the customers page
    driver.get("http://localhost:8005/customers")
    time.sleep(2)

    # Find all rows in the table
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    print(f"Found {len(rows)} customer rows")

    # Check for Dan in the table
    page_source = driver.page_source
    if "Dan" in page_source:
        print("✓ 'Dan' found on the page")
    else:
        print("✗ 'Dan' NOT found on the page")

    # Look for pagination controls
    pagination = driver.find_elements(By.CSS_SELECTOR, ".pagination, .page, button")
    print(f"Found {len(pagination)} pagination-related elements")

    # Print customer names visible on the page
    print("\nCustomers visible on page:")
    for row in rows:
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 1:
                print(f"  - {cells[1].text}")  # Name is usually in the second column
        except:
            pass

    # Check if there's a way to show more records
    selects = driver.find_elements(By.TAG_NAME, "select")
    for select in selects:
        print(f"\nFound select element: {select.get_attribute('outerHTML')[:100]}...")

finally:
    driver.quit()