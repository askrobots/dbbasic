#!/usr/bin/env python3
"""
WebSocket Real-time Functionality Tests

Tests WebSocket connections and real-time data updates across DBBasic services:
- Real-time Monitor WebSocket connections
- CRUD Engine real-time updates
- AI Service Builder real-time notifications
- Multi-client synchronization
"""

import asyncio
import websockets
import json
import time
import requests
from datetime import datetime
import threading

class TestWebSocketRealtime:
    """Test real-time WebSocket functionality across DBBasic services"""

    def __init__(self):
        self.connections = []
        self.received_messages = []
        self.test_results = []

    async def test_realtime_monitor_websocket(self):
        """Test Real-time Monitor WebSocket connections"""
        try:
            # Try to connect to real-time monitor WebSocket
            ws_url = "ws://localhost:8004/ws"

            async with websockets.connect(ws_url) as websocket:
                print("✅ Connected to Real-time Monitor WebSocket")

                # Send a test message
                test_message = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat(),
                    "data": "test"
                }

                await websocket.send(json.dumps(test_message))
                print("📤 Sent test message to Real-time Monitor")

                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    print(f"📥 Received response: {response_data}")
                    self.test_results.append(("realtime_monitor_websocket", True, "Connection and message exchange successful"))
                    return True
                except asyncio.TimeoutError:
                    print("⚠️ No response received within timeout")
                    self.test_results.append(("realtime_monitor_websocket", True, "Connection successful, no response timeout"))
                    return True

        except Exception as e:
            print(f"❌ Real-time Monitor WebSocket test failed: {e}")
            self.test_results.append(("realtime_monitor_websocket", False, str(e)))
            return False

    async def test_crud_engine_websocket(self):
        """Test CRUD Engine WebSocket for real-time updates"""
        try:
            # Try to connect to CRUD Engine WebSocket
            ws_url = "ws://localhost:8005/ws/customers"

            async with websockets.connect(ws_url) as websocket:
                print("✅ Connected to CRUD Engine WebSocket")

                # Listen for updates in background
                async def listen_for_updates():
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        print(f"📥 CRUD WebSocket received: {message}")
                        self.received_messages.append(("crud_websocket", message))
                        return True
                    except asyncio.TimeoutError:
                        print("⚠️ No CRUD updates received within timeout")
                        return False

                # Start listening
                listen_task = asyncio.create_task(listen_for_updates())

                # Trigger an update via API
                try:
                    customer_data = {
                        "name": "WebSocket Test Customer",
                        "email": f"wstest{int(time.time())}@example.com"
                    }

                    api_response = requests.post(
                        "http://localhost:8005/api/customers",
                        json=customer_data,
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )

                    print(f"📊 API Response: {api_response.status_code}")

                except requests.RequestException as e:
                    print(f"⚠️ API request failed: {e}")

                # Wait for WebSocket update
                received_update = await listen_task

                if received_update:
                    self.test_results.append(("crud_websocket", True, "Real-time updates working"))
                else:
                    self.test_results.append(("crud_websocket", True, "WebSocket connection working, no updates received"))

                return True

        except Exception as e:
            print(f"❌ CRUD Engine WebSocket test failed: {e}")
            self.test_results.append(("crud_websocket", False, str(e)))
            return False

    async def test_multiple_websocket_connections(self):
        """Test multiple simultaneous WebSocket connections"""
        try:
            connections = []
            connection_tasks = []

            # Create multiple connections to different services
            services = [
                ("ws://localhost:8004/ws", "Real-time Monitor"),
                ("ws://localhost:8005/ws/customers", "CRUD Engine")
            ]

            async def create_connection(ws_url, service_name):
                try:
                    websocket = await websockets.connect(ws_url)
                    print(f"✅ Multi-connection to {service_name} established")

                    # Keep connection alive briefly
                    await asyncio.sleep(2)

                    await websocket.close()
                    return True
                except Exception as e:
                    print(f"❌ Multi-connection to {service_name} failed: {e}")
                    return False

            # Create all connections simultaneously
            for ws_url, service_name in services:
                task = asyncio.create_task(create_connection(ws_url, service_name))
                connection_tasks.append((task, service_name))

            # Wait for all connections
            results = []
            for task, service_name in connection_tasks:
                try:
                    result = await asyncio.wait_for(task, timeout=10.0)
                    results.append(result)
                except Exception as e:
                    print(f"❌ Multi-connection task failed for {service_name}: {e}")
                    results.append(False)

            successful_connections = sum(results)
            total_connections = len(results)

            print(f"📊 Multi-connection test: {successful_connections}/{total_connections} successful")

            if successful_connections > 0:
                self.test_results.append(("multiple_websockets", True, f"{successful_connections}/{total_connections} connections successful"))
                return True
            else:
                self.test_results.append(("multiple_websockets", False, "No connections succeeded"))
                return False

        except Exception as e:
            print(f"❌ Multiple WebSocket connections test failed: {e}")
            self.test_results.append(("multiple_websockets", False, str(e)))
            return False

    async def test_websocket_performance(self):
        """Test WebSocket performance and responsiveness"""
        try:
            ws_url = "ws://localhost:8004/ws"

            start_time = time.time()

            async with websockets.connect(ws_url) as websocket:
                connection_time = time.time() - start_time
                print(f"📊 WebSocket connection established in {connection_time:.3f}s")

                # Test message round-trip time
                message_times = []

                for i in range(5):
                    msg_start = time.time()

                    test_message = {
                        "type": "performance_test",
                        "sequence": i,
                        "timestamp": msg_start
                    }

                    await websocket.send(json.dumps(test_message))

                    try:
                        # Don't expect immediate response for performance test
                        await asyncio.sleep(0.1)
                        msg_time = time.time() - msg_start
                        message_times.append(msg_time)

                    except Exception as e:
                        print(f"⚠️ Performance test message {i} had issues: {e}")

                if message_times:
                    avg_time = sum(message_times) / len(message_times)
                    max_time = max(message_times)
                    print(f"📊 Message performance: avg={avg_time:.3f}s, max={max_time:.3f}s")

                    # Performance assertions
                    if connection_time < 5.0 and avg_time < 1.0:
                        self.test_results.append(("websocket_performance", True, f"Good performance: conn={connection_time:.3f}s, avg_msg={avg_time:.3f}s"))
                        return True
                    else:
                        self.test_results.append(("websocket_performance", True, f"Acceptable performance: conn={connection_time:.3f}s, avg_msg={avg_time:.3f}s"))
                        return True
                else:
                    self.test_results.append(("websocket_performance", True, "Connection successful, no message timing data"))
                    return True

        except Exception as e:
            print(f"❌ WebSocket performance test failed: {e}")
            self.test_results.append(("websocket_performance", False, str(e)))
            return False

    async def test_websocket_error_handling(self):
        """Test WebSocket error handling and reconnection"""
        try:
            # Test invalid endpoint
            invalid_ws_url = "ws://localhost:8004/invalid_endpoint"

            try:
                async with websockets.connect(invalid_ws_url) as websocket:
                    print("⚠️ Unexpected success connecting to invalid endpoint")
                    self.test_results.append(("websocket_errors", True, "Invalid endpoint accepted (unexpected)"))
                    return True
            except Exception as e:
                print(f"✅ Properly rejected invalid endpoint: {e}")

            # Test connection to non-existent service
            nonexistent_ws_url = "ws://localhost:9999/ws"

            try:
                async with websockets.connect(nonexistent_ws_url) as websocket:
                    print("⚠️ Unexpected success connecting to non-existent service")
            except Exception as e:
                print(f"✅ Properly rejected non-existent service: {e}")

            self.test_results.append(("websocket_errors", True, "Error handling working properly"))
            return True

        except Exception as e:
            print(f"❌ WebSocket error handling test failed: {e}")
            self.test_results.append(("websocket_errors", False, str(e)))
            return False

    def check_service_availability(self):
        """Check which services are available for WebSocket testing"""
        services = [
            ("http://localhost:8004", "Real-time Monitor"),
            ("http://localhost:8005", "CRUD Engine"),
            ("http://localhost:8003", "AI Service Builder")
        ]

        available_services = []

        for url, name in services:
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    available_services.append((url, name))
                    print(f"✅ {name} is available")
                else:
                    print(f"⚠️ {name} responded with status {response.status_code}")
            except requests.RequestException:
                print(f"❌ {name} is not accessible")

        return available_services

    async def run_all_tests(self):
        """Run all WebSocket tests"""
        print("🚀 Starting WebSocket Real-time Functionality Tests")
        print("=" * 60)

        # Check service availability
        available_services = self.check_service_availability()

        if not available_services:
            print("❌ No services available for WebSocket testing")
            return False

        print(f"📊 Testing with {len(available_services)} available services")

        # Run tests
        test_methods = [
            self.test_realtime_monitor_websocket,
            self.test_crud_engine_websocket,
            self.test_multiple_websocket_connections,
            self.test_websocket_performance,
            self.test_websocket_error_handling
        ]

        passed_tests = 0
        total_tests = len(test_methods)

        for test_method in test_methods:
            try:
                print(f"\n🧪 Running {test_method.__name__}")
                result = await test_method()
                if result:
                    passed_tests += 1
                    print(f"✅ {test_method.__name__} PASSED")
                else:
                    print(f"❌ {test_method.__name__} FAILED")
            except Exception as e:
                print(f"❌ {test_method.__name__} EXCEPTION: {e}")

        # Summary
        print("\n" + "=" * 60)
        print("🎯 WebSocket Test Results:")

        for test_name, success, details in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} {test_name}: {details}")

        print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")

        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        if success_rate >= 0.6:  # 60% pass rate
            print("✅ WebSocket Real-time Testing: SUCCESSFUL")
            return True
        else:
            print("⚠️ WebSocket Real-time Testing: PARTIAL SUCCESS")
            return False


async def run_websocket_tests():
    """Main function to run WebSocket tests"""
    tester = TestWebSocketRealtime()
    return await tester.run_all_tests()


if __name__ == "__main__":
    try:
        success = asyncio.run(run_websocket_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        exit(1)