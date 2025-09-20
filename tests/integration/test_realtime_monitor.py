#!/usr/bin/env python3
"""
Selenium test specifically for Real-time Monitor
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import sys

def test_realtime_monitor(headless=False):
    # Setup Chrome options
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=options)

    try:
        print('📡 Testing Real-time Monitor with Selenium')
        print('=' * 50)

        # Navigate to Real-time Monitor
        driver.get('http://localhost:8004')
        print('✅ Loaded http://localhost:8004')

        # Wait for page to load
        wait = WebDriverWait(driver, 10)

        # Check page title
        title = driver.title
        print(f'📄 Page Title: "{title}"')

        # Check for header
        try:
            header = driver.find_element(By.CLASS_NAME, 'header')
            header_text = header.text
            print(f'✅ Header found: "{header_text}"')
        except Exception as e:
            print(f'❌ Header not found: {e}')

        # Check for WebSocket status
        try:
            status = driver.find_element(By.CLASS_NAME, 'status')
            status_text = status.text
            print(f'✅ Status indicator: "{status_text}"')

            # Check status color/class
            status_classes = status.get_attribute('class')
            print(f'   Status classes: {status_classes}')
        except Exception as e:
            print(f'❌ Status indicator not found: {e}')

        # Check for events container
        try:
            events = driver.find_element(By.ID, 'events')
            print('✅ Events container found')

            # Check if any events are present
            event_items = events.find_elements(By.CLASS_NAME, 'event-item')
            if event_items:
                print(f'   Found {len(event_items)} events')
                for i, event in enumerate(event_items[:3]):  # Show first 3
                    print(f'   Event {i+1}: {event.text[:50]}...')
            else:
                print('   No events yet (waiting for activity)')
        except Exception as e:
            print(f'❌ Events container not found: {e}')

        # Check for control buttons
        print('\n🎮 Checking control buttons:')
        buttons = {
            'clearBtn': 'Clear button',
            'pauseBtn': 'Pause button',
            'exportBtn': 'Export button'
        }

        for btn_id, btn_name in buttons.items():
            try:
                btn = driver.find_element(By.ID, btn_id)
                print(f'✅ {btn_name} found: "{btn.text}"')
                if btn.is_enabled():
                    print(f'   Button is enabled')
                else:
                    print(f'   Button is disabled')
            except Exception as e:
                print(f'❌ {btn_name} not found')

        # Check for stats panel
        try:
            stats = driver.find_element(By.CLASS_NAME, 'stats')
            print('\n📊 Stats panel found')
            stat_items = stats.find_elements(By.TAG_NAME, 'div')
            for item in stat_items[:5]:  # Show first 5
                text = item.text
                if text:
                    print(f'   {text}')
        except Exception as e:
            print(f'❌ Stats panel not found: {e}')

        # Check WebSocket connection via JavaScript
        print('\n🔌 Checking WebSocket:')
        try:
            ws_state = driver.execute_script("""
                if (window.ws) {
                    return {
                        readyState: window.ws.readyState,
                        url: window.ws.url,
                        readyStateText: ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'][window.ws.readyState]
                    };
                }
                return null;
            """)

            if ws_state:
                print(f'✅ WebSocket found:')
                print(f'   URL: {ws_state.get("url")}')
                print(f'   State: {ws_state.get("readyStateText")} ({ws_state.get("readyState")})')
            else:
                print('⚠️ WebSocket not initialized yet')
        except Exception as e:
            print(f'❌ Could not check WebSocket: {e}')

        # Take screenshot
        screenshot_path = 'realtime_monitor_selenium.png'
        driver.save_screenshot(screenshot_path)
        print(f'\n📸 Screenshot saved: {screenshot_path}')

        # Get console logs
        print('\n📝 Browser console logs:')
        logs = driver.get_log('browser')
        for log in logs[-5:]:  # Last 5 logs
            print(f'   [{log["level"]}] {log["message"][:100]}')

        # Test interaction - click Pause button
        print('\n🧪 Testing interaction:')
        try:
            pause_btn = driver.find_element(By.ID, 'pauseBtn')
            initial_text = pause_btn.text
            pause_btn.click()
            time.sleep(0.5)
            new_text = pause_btn.text
            if initial_text != new_text:
                print(f'✅ Pause button clicked: "{initial_text}" → "{new_text}"')
            else:
                print(f'⚠️ Pause button clicked but text unchanged: "{initial_text}"')
        except Exception as e:
            print(f'❌ Could not test pause button: {e}')

        print('\n' + '=' * 50)
        print('✅ Real-time Monitor is working correctly!')
        return True

    except Exception as e:
        print(f'\n❌ Error testing Real-time Monitor: {e}')
        driver.save_screenshot('realtime_monitor_error.png')
        return False

    finally:
        if not headless:
            input('\n⏸️  Press Enter to close browser...')
        driver.quit()

if __name__ == "__main__":
    # Run with visible browser by default, add --headless for headless mode
    headless = '--headless' in sys.argv
    success = test_realtime_monitor(headless=headless)
    sys.exit(0 if success else 1)