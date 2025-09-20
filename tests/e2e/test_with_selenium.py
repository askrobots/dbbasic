#!/usr/bin/env python3
"""
Selenium-based automated testing for web interfaces
Supports headless Chrome/Firefox for CI/CD environments
"""

import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class WebUITester:
    def __init__(self, browser="chrome", headless=True, url="http://localhost:8003"):
        self.url = url
        self.browser_type = browser
        self.headless = headless
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Initialize the web driver with appropriate options"""
        if self.browser_type.lower() == "chrome":
            options = ChromeOptions()
            if self.headless:
                options.add_argument('--headless=new')  # New headless mode
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')

            try:
                self.driver = webdriver.Chrome(options=options)
            except Exception as e:
                print(f"Chrome driver failed: {e}")
                print("Trying with Firefox...")
                self.browser_type = "firefox"
                self.setup_firefox()
        else:
            self.setup_firefox()

    def setup_firefox(self):
        """Fallback to Firefox if Chrome isn't available"""
        options = FirefoxOptions()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--width=1920')
        options.add_argument('--height=1080')

        try:
            self.driver = webdriver.Firefox(options=options)
        except Exception as e:
            print(f"Firefox driver also failed: {e}")
            sys.exit(1)

    def test_syntax_highlighting(self):
        """Test that YAML syntax highlighting works correctly"""
        print("Testing syntax highlighting on config browser...")

        # Navigate to config page
        self.driver.get(f"{self.url}/config")

        # Wait for config cards to load
        wait = WebDriverWait(self.driver, 10)

        try:
            # Find and click first config card
            config_card = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "config-card"))
            )
            config_card.click()

            # Wait for modal to appear
            modal = wait.until(
                EC.visibility_of_element_located((By.ID, "configModal"))
            )

            # Get the config content
            config_content = self.driver.find_element(By.ID, "configContent")

            # Check HTML content for proper highlighting
            inner_html = config_content.get_attribute('innerHTML')
            text_content = config_content.text

            # Test 1: No raw style attributes should appear in text
            if 'style=' in text_content or 'color:' in text_content:
                print("❌ FAILED: Style attributes appearing as text!")
                print(f"Found: {text_content[:200]}...")
                return False

            # Test 2: Should have span elements with style attributes in HTML
            if '<span style' not in inner_html:
                print("❌ FAILED: No syntax highlighting spans found!")
                return False

            # Test 3: Check for specific color codes (hex or rgb format)
            # Chrome converts hex to rgb, so check for both formats
            expected_colors = [
                ('6a9955', 'rgb(106, 153, 85)'),   # Comments green
                ('9cdcfe', 'rgb(156, 220, 254)'),  # Keys blue
                ('ce9178', 'rgb(206, 145, 120)'),  # Strings orange
                ('569cd6', 'rgb(86, 156, 214)'),   # Booleans light blue
                ('b5cea8', 'rgb(181, 206, 168)')   # Numbers green
            ]

            colors_found = 0
            for hex_color, rgb_color in expected_colors:
                if hex_color in inner_html or rgb_color in inner_html:
                    colors_found += 1

            if colors_found == 0:
                print("❌ FAILED: No expected color codes found in HTML!")
                print(f"HTML sample: {inner_html[:500]}...")
                return False

            print(f"✅ PASSED: Syntax highlighting working correctly!")
            print(f"  - No style attributes in visible text")
            print(f"  - Found {colors_found}/{len(expected_colors)} expected colors")
            print(f"  - HTML structure is correct")

            # Take screenshot for debugging
            self.driver.save_screenshot("syntax_highlight_test.png")

            return True

        except TimeoutException:
            print("❌ FAILED: Timeout waiting for elements")
            return False
        except Exception as e:
            print(f"❌ FAILED: Unexpected error: {e}")
            return False

    def test_dashboard_links(self):
        """Test that dashboard has links to other services"""
        print("\nTesting dashboard links...")

        self.driver.get(self.url)

        try:
            # Check for service links
            links_to_check = [
                ("Real-time Monitor", "http://localhost:8004"),
                ("Test Runner", "http://localhost:8006")
            ]

            for link_text, expected_href in links_to_check:
                try:
                    # Find link by partial text
                    elements = self.driver.find_elements(By.PARTIAL_LINK_TEXT, link_text)
                    if not elements:
                        # Try finding by href
                        elements = self.driver.find_elements(By.CSS_SELECTOR, f'a[href="{expected_href}"]')

                    if elements:
                        print(f"✅ Found link: {link_text} -> {expected_href}")
                    else:
                        print(f"❌ Missing link: {link_text}")
                        return False
                except:
                    print(f"❌ Error finding link: {link_text}")
                    return False

            print("✅ PASSED: All dashboard links present")
            return True

        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False

    def test_config_count(self):
        """Test that expected number of configs are displayed"""
        print("\nTesting config count...")

        self.driver.get(f"{self.url}/config")
        time.sleep(2)  # Give time for JS to load

        try:
            # Count config cards
            config_cards = self.driver.find_elements(By.CLASS_NAME, "config-card")
            count = len(config_cards)

            if count >= 11:  # We expect at least 11 configs
                print(f"✅ PASSED: Found {count} config files")

                # List the configs found
                for card in config_cards[:5]:  # Show first 5
                    name = card.find_element(By.CLASS_NAME, "config-name").text
                    print(f"  - {name}")
                if count > 5:
                    print(f"  ... and {count - 5} more")

                return True
            else:
                print(f"❌ FAILED: Only found {count} configs (expected 11+)")
                return False

        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False

    def run_all_tests(self):
        """Run all tests and report results"""
        print(f"\n{'='*50}")
        print(f"Running automated tests with {self.browser_type}")
        print(f"Target: {self.url}")
        print(f"Headless: {self.headless}")
        print(f"{'='*50}")

        results = []

        # Run each test
        tests = [
            ("Dashboard Links", self.test_dashboard_links),
            ("Config Count", self.test_config_count),
            ("Syntax Highlighting", self.test_syntax_highlighting)
        ]

        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test '{test_name}' crashed: {e}")
                results.append((test_name, False))

        # Summary
        print(f"\n{'='*50}")
        print("TEST SUMMARY")
        print(f"{'='*50}")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")

        print(f"\nTotal: {passed}/{total} tests passed")

        return passed == total

    def cleanup(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description='Test DBBasic web UI with Selenium')
    parser.add_argument('--browser', default='chrome', choices=['chrome', 'firefox'],
                       help='Browser to use for testing')
    parser.add_argument('--show-browser', action='store_true',
                       help='Run with visible browser (not headless)')
    parser.add_argument('--url', default='http://localhost:8003',
                       help='URL to test')
    parser.add_argument('--test', help='Run specific test only')

    args = parser.parse_args()

    # Create tester
    tester = WebUITester(
        browser=args.browser,
        headless=not args.show_browser,
        url=args.url
    )

    try:
        if args.test:
            # Run specific test
            test_method = getattr(tester, f"test_{args.test}", None)
            if test_method:
                success = test_method()
            else:
                print(f"Unknown test: {args.test}")
                success = False
        else:
            # Run all tests
            success = tester.run_all_tests()

        return 0 if success else 1

    finally:
        tester.cleanup()

if __name__ == "__main__":
    sys.exit(main())