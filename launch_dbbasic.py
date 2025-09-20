#!/usr/bin/env python3
"""
DBBasic Unified Service Launcher
Start all DBBasic services with presentation layer
"""

import subprocess
import time
import signal
import sys
from pathlib import Path

class DBBasicLauncher:
    def __init__(self):
        self.processes = []

        # Service configurations
        self.services = [
            {
                'name': 'Real-time Monitor',
                'file': 'realtime_monitor.py',
                'port': 8004,
                'color': '\033[92m'  # Green
            },
            {
                'name': 'Data Service',
                'file': 'dbbasic_crud_engine.py',
                'port': 8005,
                'color': '\033[94m'  # Blue
            },
            {
                'name': 'AI Service Builder',
                'file': 'dbbasic_ai_service_builder.py',
                'port': 8003,
                'color': '\033[95m'  # Purple
            },
            {
                'name': 'Event Store',
                'file': 'dbbasic_event_store.py',
                'port': 8006,
                'color': '\033[93m'  # Yellow
            }
        ]

    def start_service(self, service):
        """Start a single service"""
        if not Path(service['file']).exists():
            print(f"❌ {service['name']}: File not found - {service['file']}")
            return None

        try:
            process = subprocess.Popen(
                ['python', service['file']],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            print(f"{service['color']}✅ {service['name']} started on port {service['port']}\033[0m")
            return process
        except Exception as e:
            print(f"❌ Failed to start {service['name']}: {e}")
            return None

    def start_all(self):
        """Start all services"""
        print("=" * 60)
        print("🚀 DBBasic Platform Launcher")
        print("=" * 60)
        print("\nStarting all services...\n")

        for service in self.services:
            process = self.start_service(service)
            if process:
                self.processes.append(process)
            time.sleep(2)  # Give each service time to start

        print("\n" + "=" * 60)
        print("✅ All services started!")
        print("=" * 60)
        print("\n📌 Service URLs:")
        print("  • Dashboard: http://localhost:8004")
        print("  • Data Service: http://localhost:8005")
        print("  • AI Services: http://localhost:8003")
        print("  • Event Store: http://localhost:8006")
        print("  • API Docs: http://localhost:8005/docs")
        print("\nPress Ctrl+C to stop all services\n")

        # Monitor processes
        try:
            while True:
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        print(f"⚠️ Service {self.services[i]['name']} stopped")
                        # Restart the service
                        self.processes[i] = self.start_service(self.services[i])
                time.sleep(5)
        except KeyboardInterrupt:
            self.stop_all()

    def stop_all(self):
        """Stop all services"""
        print("\n\nStopping all services...")

        for process in self.processes:
            if process:
                process.terminate()

        # Wait for processes to terminate
        for process in self.processes:
            if process:
                process.wait()

        print("✅ All services stopped")
        sys.exit(0)

    def signal_handler(self, sig, frame):
        """Handle Ctrl+C"""
        self.stop_all()

if __name__ == "__main__":
    launcher = DBBasicLauncher()

    # Register signal handler
    signal.signal(signal.SIGINT, launcher.signal_handler)

    # Start all services
    launcher.start_all()
