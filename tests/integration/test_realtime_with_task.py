#!/usr/bin/env python3
"""
Test Real-time Monitor with actual tasks to verify visibility
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import sys
import requests
import threading

def run_background_tasks():
    """Generate some API calls to create events"""
    time.sleep(2)  # Wait for browser to load
    
    # Make some API calls to generate events
    base_url = 'http://localhost:8003'
    
    try:
        # Config browser request
        requests.get(f'{base_url}/config')
        time.sleep(0.5)
        
        # View a specific config
        requests.get(f'{base_url}/api/config/shipping_config_example.yaml')
        time.sleep(0.5)
        
        # Another config
        requests.get(f'{base_url}/api/config/dashboard_config.yaml')
        time.sleep(0.5)
        
        # Main dashboard
        requests.get(base_url)
        
        print('📡 Background tasks sent')
    except Exception as e:
        print(f'❌ Error sending tasks: {e}')

def test_with_live_tasks(headless=True):
    # Setup Chrome
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=options)

    try:
        print('🚀 Starting Real-time Monitor test with live tasks')
        print('=' * 50)

        # Open Real-time Monitor
        driver.get('http://localhost:8004')
        wait = WebDriverWait(driver, 10)
        
        # Wait for initial load
        time.sleep(2)
        
        # Check initial state
        events_container = driver.find_element(By.ID, 'stream-content')
        initial_events = events_container.find_elements(By.CLASS_NAME, 'stream-entry')
        print(f'📊 Initial events count: {len(initial_events)}')
        
        # Start background task thread
        task_thread = threading.Thread(target=run_background_tasks)
        task_thread.start()
        
        # Wait for events to appear
        print('⏳ Waiting for new events to appear...')
        time.sleep(4)
        
        # Check for new events
        new_events = events_container.find_elements(By.CLASS_NAME, 'stream-entry')
        print(f'📊 Events after tasks: {len(new_events)}')
        
        if len(new_events) > len(initial_events):
            print(f'✅ SUCCESS: {len(new_events) - len(initial_events)} new events appeared!')
            
            # Show details of new events
            print('\n📝 New events details:')
            for i in range(len(initial_events), min(len(new_events), len(initial_events) + 5)):
                event = new_events[i]
                # Just print the event text since structure may vary
                print(f'  Event: {event.text[:100]}...')
        else:
            print('⚠️ No new events detected')
            
            # Check WebSocket status
            ws_state = driver.execute_script("""
                if (window.ws) {
                    return {
                        readyState: window.ws.readyState,
                        readyStateText: ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'][window.ws.readyState]
                    };
                }
                return null;
            """)
            
            if ws_state:
                print(f'WebSocket state: {ws_state.get("readyStateText")}')
            
        # Take screenshot
        driver.save_screenshot('realtime_with_tasks.png')
        print(f'\n📸 Screenshot saved: realtime_with_tasks.png')
        
        # Wait for thread to complete
        task_thread.join()
        
        print('\n' + '=' * 50)
        print('✅ Test completed!')
        return len(new_events) > len(initial_events)

    except Exception as e:
        print(f'\n❌ Error: {e}')
        driver.save_screenshot('realtime_error.png')
        return False

    finally:
        driver.quit()

if __name__ == "__main__":
    headless = '--headless' in sys.argv
    success = test_with_live_tasks(headless=headless)
    sys.exit(0 if success else 1)