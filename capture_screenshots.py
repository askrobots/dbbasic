#!/usr/bin/env python3
"""Capture screenshots of all DBBasic interfaces for documentation"""

import os
import time
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

# Create screenshots directory
SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

def setup_driver(headless=False):
    """Setup Chrome driver with options"""
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=options)

def capture_interface(driver, url, name, wait_selector=None, wait_time=3):
    """Capture a screenshot of an interface"""
    print(f"📸 Capturing {name}...")
    driver.get(url)

    # Wait for page to load
    if wait_selector:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
            )
        except:
            print(f"  ⚠️ Selector {wait_selector} not found, continuing...")

    time.sleep(wait_time)  # Additional wait for dynamic content

    # Capture screenshot
    screenshot_path = SCREENSHOT_DIR / f"{name}.png"
    driver.save_screenshot(str(screenshot_path))
    print(f"  ✅ Saved to {screenshot_path}")
    return screenshot_path

def main():
    """Capture all interfaces"""
    print("🚀 Starting screenshot capture for DBBasic interfaces")
    print("=" * 60)

    driver = setup_driver(headless=False)  # Set to True for headless mode

    try:
        # Dictionary of interfaces to capture
        # Format: (URL, filename, status, wait_selector, wait_time)
        interfaces = [
            # IMPLEMENTED INTERFACES
            ("http://localhost:8000/static/mockups.html",
             "main_dashboard", "prototype", "#dashboard", 2),

            ("http://localhost:8003",
             "ai_service_builder", "implemented", "h1", 2),

            ("http://localhost:8004",
             "realtime_monitor", "implemented", "#activity-log", 3),

            ("http://localhost:8005",
             "crud_engine_list", "implemented", "table", 2),

            ("http://localhost:8005/customers/create",
             "crud_engine_form", "implemented", "form", 2),

            ("http://localhost:8006",
             "test_runner", "implemented", "#test-list", 2),

            # PROTOTYPE INTERFACES (from mockups)
            ("http://localhost:8000/static/mockups.html#query-builder",
             "prototype_query_builder", "prototype", "#query-builder", 2),

            ("http://localhost:8000/static/mockups.html#schema-designer",
             "prototype_schema_designer", "prototype", "#schema-designer", 2),

            ("http://localhost:8000/static/mockups.html#api-generator",
             "prototype_api_generator", "prototype", "#api-generator", 2),

            ("http://localhost:8000/static/mockups.html#workflow-builder",
             "prototype_workflow_builder", "prototype", "#workflow-builder", 2),
        ]

        # Capture each interface
        screenshots = {}
        for url, name, status, selector, wait in interfaces:
            try:
                path = capture_interface(driver, url, name, selector, wait)
                screenshots[name] = {
                    'path': path,
                    'status': status,
                    'url': url
                }
            except Exception as e:
                print(f"  ❌ Error capturing {name}: {e}")

        print("\n" + "=" * 60)
        print("📊 Screenshot Summary:")
        print("=" * 60)

        implemented = [k for k, v in screenshots.items() if v['status'] == 'implemented']
        prototypes = [k for k, v in screenshots.items() if v['status'] == 'prototype']

        print(f"✅ Implemented interfaces captured: {len(implemented)}")
        for name in implemented:
            print(f"   - {name}")

        print(f"\n🎨 Prototype interfaces captured: {len(prototypes)}")
        for name in prototypes:
            print(f"   - {name}")

        # Generate markdown for README
        print("\n" + "=" * 60)
        print("📝 Markdown for README.md:")
        print("=" * 60)

        markdown = """
## 📸 Interface Screenshots

### ✅ Implemented Interfaces

"""

        for name, info in screenshots.items():
            if info['status'] == 'implemented':
                title = name.replace('_', ' ').title()
                markdown += f"#### {title}\n"
                markdown += f"![{title}](screenshots/{name}.png)\n"
                markdown += f"*Live at: {info['url']}*\n\n"

        markdown += """
### 🎨 Prototype Interfaces (Coming Soon)

These interfaces are currently available as interactive prototypes at `http://localhost:8000/static/mockups.html`

"""

        for name, info in screenshots.items():
            if info['status'] == 'prototype':
                title = name.replace('prototype_', '').replace('_', ' ').title()
                markdown += f"#### {title}\n"
                markdown += f"![{title}](screenshots/{name}.png)\n"
                markdown += f"*Prototype preview - implementation pending*\n\n"

        # Save markdown to file
        with open(SCREENSHOT_DIR / "README_SCREENSHOTS.md", "w") as f:
            f.write(markdown)

        print(markdown)
        print("\n✅ Markdown saved to screenshots/README_SCREENSHOTS.md")

    finally:
        driver.quit()
        print("\n🎉 Screenshot capture complete!")

if __name__ == "__main__":
    # Check if services are running
    import requests

    services = [
        ("http://localhost:8000", "Main Dashboard"),
        ("http://localhost:8003", "AI Service Builder"),
        ("http://localhost:8004", "Realtime Monitor"),
        ("http://localhost:8005", "CRUD Engine"),
        ("http://localhost:8006", "Test Runner"),
    ]

    print("🔍 Checking services...")
    all_running = True
    for url, name in services:
        try:
            requests.get(url, timeout=1)
            print(f"  ✅ {name} is running")
        except:
            print(f"  ❌ {name} is not running at {url}")
            all_running = False

    if not all_running:
        print("\n⚠️ Warning: Not all services are running. Screenshots may be incomplete.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            exit(1)

    print()
    main()