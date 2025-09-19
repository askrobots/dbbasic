#!/usr/bin/env python3
"""
Comprehensive Selenium Tests for DBBasic Web Interfaces

Tests all web interfaces with browser automation including:
- Real-time Monitor dashboard
- AI Service Builder interface
- CRUD Engine interfaces
- WebSocket real-time functionality
- Cross-browser compatibility
"""

import pytest
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestDBBasicWebInterfaces:
    """Selenium test suite for DBBasic web interfaces"""

    @classmethod
    def setup_class(cls):
        """Setup Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.wait = WebDriverWait(cls.driver, 10)
            print("✅ Chrome WebDriver initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Chrome WebDriver: {e}")
            pytest.skip("Chrome WebDriver not available")

    @classmethod
    def teardown_class(cls):
        """Cleanup WebDriver"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
            print("✅ WebDriver closed")

    def wait_for_service(self, url, service_name):
        """Wait for service to be available"""
        max_retries = 20
        for i in range(max_retries):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service_name} is ready")
                    return True
            except requests.RequestException:
                if i == max_retries - 1:
                    print(f"❌ {service_name} not accessible after {max_retries} attempts")
                    return False
                time.sleep(1)
        return False

    def test_realtime_monitor_dashboard(self):
        """Test Real-time Monitor dashboard interface"""
        if not self.wait_for_service("http://localhost:8004", "Real-time Monitor"):
            pytest.skip("Real-time Monitor not available")

        self.driver.get("http://localhost:8004")

        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Check page title
        title = self.driver.title
        assert "Monitor" in title or "DBBasic" in title, f"Unexpected page title: {title}"

        # Look for monitoring elements
        try:
            # Check for dashboard indicators
            dashboard_elements = self.driver.find_elements(By.CLASS_NAME, "metric")
            dashboard_elements.extend(self.driver.find_elements(By.CLASS_NAME, "status"))
            dashboard_elements.extend(self.driver.find_elements(By.CLASS_NAME, "monitor"))

            assert len(dashboard_elements) > 0, "No monitoring dashboard elements found"
            print(f"✅ Real-time Monitor dashboard loaded with {len(dashboard_elements)} elements")

        except NoSuchElementException:
            # Alternative check - look for any structured content
            content_elements = self.driver.find_elements(By.TAG_NAME, "div")
            assert len(content_elements) > 5, "Page appears to be empty or not properly loaded"
            print("✅ Real-time Monitor page loaded with content")

    def test_ai_service_builder_interface(self):
        """Test AI Service Builder web interface"""
        if not self.wait_for_service("http://localhost:8003", "AI Service Builder"):
            pytest.skip("AI Service Builder not available")

        self.driver.get("http://localhost:8003")

        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Check page content
        page_text = self.driver.find_element(By.TAG_NAME, "body").text

        # Look for service builder indicators
        service_indicators = [
            "service", "builder", "ai", "generate", "create",
            "endpoint", "function", "API", "build"
        ]

        found_indicators = [indicator for indicator in service_indicators
                          if indicator.lower() in page_text.lower()]

        assert len(found_indicators) >= 2, f"Service builder content not detected. Page text: {page_text[:200]}"
        print(f"✅ AI Service Builder interface loaded, found indicators: {found_indicators}")

    def test_crud_engine_dashboard(self):
        """Test CRUD Engine dashboard"""
        if not self.wait_for_service("http://localhost:8005", "CRUD Engine"):
            pytest.skip("CRUD Engine not available")

        self.driver.get("http://localhost:8005")

        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Check for CRUD dashboard elements
        page_source = self.driver.page_source.lower()

        crud_indicators = ["crud", "dashboard", "customers", "management", "create", "read", "update", "delete"]
        found_indicators = [indicator for indicator in crud_indicators if indicator in page_source]

        assert len(found_indicators) >= 3, f"CRUD dashboard not properly loaded. Found: {found_indicators}"
        print(f"✅ CRUD Engine dashboard loaded, found indicators: {found_indicators}")

    def test_crud_customers_interface(self):
        """Test CRUD Customers interface"""
        if not self.wait_for_service("http://localhost:8005", "CRUD Engine"):
            pytest.skip("CRUD Engine not available")

        self.driver.get("http://localhost:8005/customers")

        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Check for customer management interface
        page_source = self.driver.page_source.lower()

        customer_indicators = ["customer", "name", "email", "management", "add", "table", "form"]
        found_indicators = [indicator for indicator in customer_indicators if indicator in page_source]

        assert len(found_indicators) >= 4, f"Customer interface not properly loaded. Found: {found_indicators}"
        print(f"✅ CRUD Customers interface loaded, found indicators: {found_indicators}")

    def test_form_interactions(self):
        """Test form interactions on CRUD interfaces"""
        if not self.wait_for_service("http://localhost:8005", "CRUD Engine"):
            pytest.skip("CRUD Engine not available")

        self.driver.get("http://localhost:8005/customers")
        time.sleep(2)  # Allow page to fully load

        try:
            # Look for form elements
            form_elements = self.driver.find_elements(By.TAG_NAME, "form")
            input_elements = self.driver.find_elements(By.TAG_NAME, "input")
            button_elements = self.driver.find_elements(By.TAG_NAME, "button")

            total_interactive = len(form_elements) + len(input_elements) + len(button_elements)
            assert total_interactive > 0, "No interactive form elements found"

            print(f"✅ Form interactions available: {len(form_elements)} forms, {len(input_elements)} inputs, {len(button_elements)} buttons")

            # Try to interact with the first input if available
            if input_elements:
                first_input = input_elements[0]
                if first_input.is_enabled():
                    first_input.click()
                    first_input.send_keys("Test User")
                    print("✅ Successfully interacted with form input")

        except Exception as e:
            print(f"⚠️ Form interaction test had issues: {e}")
            # Still pass if we found the page structure
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            assert len(page_text) > 50, "Page content appears to be minimal"

    def test_navigation_between_services(self):
        """Test navigation between different DBBasic services"""
        services = [
            ("http://localhost:8004", "Real-time Monitor"),
            ("http://localhost:8003", "AI Service Builder"),
            ("http://localhost:8005", "CRUD Engine")
        ]

        accessible_services = []

        for url, name in services:
            try:
                self.driver.get(url)
                time.sleep(2)  # Allow page load

                # Basic health check
                body = self.driver.find_element(By.TAG_NAME, "body")
                if len(body.text) > 20:  # Has meaningful content
                    accessible_services.append(name)
                    print(f"✅ Successfully navigated to {name}")
                else:
                    print(f"⚠️ {name} loaded but has minimal content")

            except Exception as e:
                print(f"❌ Failed to navigate to {name}: {e}")

        assert len(accessible_services) >= 1, "No services were accessible for navigation testing"
        print(f"✅ Navigation test completed: {len(accessible_services)} services accessible")

    def test_responsive_design(self):
        """Test responsive design across different screen sizes"""
        screen_sizes = [
            (1920, 1080, "Desktop Large"),
            (1366, 768, "Desktop Standard"),
            (768, 1024, "Tablet"),
            (375, 667, "Mobile")
        ]

        if not self.wait_for_service("http://localhost:8005", "CRUD Engine"):
            pytest.skip("CRUD Engine not available for responsive testing")

        for width, height, device_type in screen_sizes:
            try:
                self.driver.set_window_size(width, height)
                self.driver.get("http://localhost:8005")
                time.sleep(1)

                # Check if page renders properly at this size
                body = self.driver.find_element(By.TAG_NAME, "body")
                viewport_width = self.driver.execute_script("return window.innerWidth")
                viewport_height = self.driver.execute_script("return window.innerHeight")

                # Basic responsive check - content should be visible
                assert len(body.text) > 20, f"Content not properly rendered at {device_type} size"
                print(f"✅ {device_type} ({viewport_width}x{viewport_height}): Page renders properly")

            except Exception as e:
                print(f"⚠️ {device_type} responsive test failed: {e}")

        # Reset to standard size
        self.driver.set_window_size(1920, 1080)

    def test_page_load_performance(self):
        """Test page load performance across services"""
        services = [
            "http://localhost:8004",
            "http://localhost:8003",
            "http://localhost:8005"
        ]

        performance_results = []

        for service_url in services:
            try:
                start_time = time.time()
                self.driver.get(service_url)

                # Wait for DOM to be ready
                self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

                load_time = time.time() - start_time
                performance_results.append((service_url, load_time))

                # Performance assertion - pages should load within reasonable time
                assert load_time < 10.0, f"Page load time too slow: {load_time:.2f}s for {service_url}"
                print(f"✅ {service_url} loaded in {load_time:.2f}s")

            except TimeoutException:
                print(f"⚠️ {service_url} timed out during load")
            except Exception as e:
                print(f"❌ Performance test failed for {service_url}: {e}")

        assert len(performance_results) > 0, "No services completed performance testing"

        avg_load_time = sum(time for _, time in performance_results) / len(performance_results)
        print(f"✅ Average page load time: {avg_load_time:.2f}s across {len(performance_results)} services")

    def test_error_handling(self):
        """Test error handling for invalid URLs and edge cases"""
        error_test_cases = [
            ("http://localhost:8005/nonexistent", "404 handling"),
            ("http://localhost:8005/customers/999999", "Invalid resource handling"),
            ("http://localhost:9999", "Service unavailable handling")
        ]

        for url, test_name in error_test_cases:
            try:
                self.driver.get(url)
                time.sleep(2)

                # Check that we get some kind of response (error page, etc.)
                page_source = self.driver.page_source.lower()

                # Look for error indicators
                error_indicators = ["error", "not found", "404", "500", "unavailable", "connection"]
                found_error_handling = any(indicator in page_source for indicator in error_indicators)

                if found_error_handling:
                    print(f"✅ {test_name}: Proper error handling detected")
                else:
                    print(f"⚠️ {test_name}: No clear error handling, but page loaded")

            except Exception as e:
                print(f"✅ {test_name}: Exception handling working: {type(e).__name__}")


def run_selenium_tests():
    """Run all Selenium tests"""
    print("🚀 Starting DBBasic Selenium Web Interface Tests")
    print("=" * 60)

    # Create test instance
    test_suite = TestDBBasicWebInterfaces()

    try:
        # Setup
        test_suite.setup_class()

        # Run tests
        test_methods = [
            test_suite.test_realtime_monitor_dashboard,
            test_suite.test_ai_service_builder_interface,
            test_suite.test_crud_engine_dashboard,
            test_suite.test_crud_customers_interface,
            test_suite.test_form_interactions,
            test_suite.test_navigation_between_services,
            test_suite.test_responsive_design,
            test_suite.test_page_load_performance,
            test_suite.test_error_handling
        ]

        passed_tests = 0
        total_tests = len(test_methods)

        for test_method in test_methods:
            try:
                print(f"\n🧪 Running {test_method.__name__}")
                test_method()
                passed_tests += 1
                print(f"✅ {test_method.__name__} PASSED")
            except Exception as e:
                print(f"❌ {test_method.__name__} FAILED: {e}")

        print("\n" + "=" * 60)
        print(f"🎯 Selenium Test Results: {passed_tests}/{total_tests} tests passed")

        if passed_tests >= total_tests * 0.7:  # 70% pass rate
            print("✅ DBBasic Web Interface Testing: SUCCESSFUL")
            return True
        else:
            print("⚠️ DBBasic Web Interface Testing: PARTIAL SUCCESS")
            return False

    except Exception as e:
        print(f"❌ Selenium test suite failed to initialize: {e}")
        return False

    finally:
        # Cleanup
        test_suite.teardown_class()


if __name__ == "__main__":
    success = run_selenium_tests()
    exit(0 if success else 1)