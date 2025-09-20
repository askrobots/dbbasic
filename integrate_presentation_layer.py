#!/usr/bin/env python3
"""
Integrate Presentation Layer into all DBBasic services
This script updates all service endpoints to use the new presentation layer
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

class ServiceIntegrator:
    """Integrate presentation layer into existing services"""

    def __init__(self):
        self.services_updated = 0
        self.endpoints_converted = 0
        self.files_modified = []

    def update_service_file(self, file_path: str, service_name: str) -> bool:
        """Update a service file to use presentation layer"""
        try:
            print(f"Updating {file_path}...")

            with open(file_path, 'r') as f:
                content = f.read()

            # Check if already using presentation layer
            if 'from presentation_layer import' in content:
                print(f"  ✅ Already using presentation layer")
                return True

            # Add imports at the top
            import_statement = """from presentation_layer import PresentationLayer
from bootstrap_components import ExtendedBootstrapRenderer
from dbbasic_unified_ui import get_master_layout, SERVICES

# Initialize presentation layer
PresentationLayer.add_renderer('bootstrap', ExtendedBootstrapRenderer())
"""

            # Find the right place to insert imports (after initial imports)
            import_pattern = r'((?:from .+ import .+\n|import .+\n)+)'
            match = re.search(import_pattern, content)

            if match:
                insert_pos = match.end()
                content = content[:insert_pos] + "\n" + import_statement + "\n" + content[insert_pos:]

            # Update HTMLResponse endpoints
            content = self.convert_endpoints(content, service_name)

            # Write back
            with open(file_path, 'w') as f:
                f.write(content)

            self.services_updated += 1
            self.files_modified.append(file_path)
            print(f"  ✅ Updated successfully")
            return True

        except Exception as e:
            print(f"  ❌ Error updating {file_path}: {e}")
            return False

    def convert_endpoints(self, content: str, service_name: str) -> str:
        """Convert HTML endpoints to use presentation layer"""

        # Pattern to find HTMLResponse with inline HTML
        pattern = r'@app\.get\("([^"]+)"\)[^{]*{[^}]*return HTMLResponse\(content="""([^"]*)"""'

        def replacement(match):
            route = match.group(1)
            self.endpoints_converted += 1

            # Generate appropriate UI based on route
            if route == "/" or route == "":
                ui_function = f"get_{service_name}_dashboard()"
            elif "template" in route:
                ui_function = "get_template_marketplace()"
            elif "model" in route:
                ui_function = "get_model_editor()"
            else:
                ui_function = f"get_{service_name}_ui()"

            return f'''@app.get("{route}")
async def {route.strip('/').replace('/', '_') or 'root'}():
    """Serve {service_name} interface using presentation layer"""
    ui_data = {ui_function}
    return HTMLResponse(content=PresentationLayer.render(ui_data, 'bootstrap'))'''

        # Apply conversions
        content = re.sub(pattern, replacement, content)

        return content

    def create_service_ui_modules(self):
        """Create UI modules for each service"""

        services = [
            ('realtime_monitor', 'monitor'),
            ('dbbasic_ai_service_builder', 'ai_services'),
            ('dbbasic_event_store', 'event_store'),
            ('dbbasic_crud_engine', 'data')
        ]

        for file_name, service_key in services:
            module_name = f"{file_name}_ui.py"

            if Path(module_name).exists():
                print(f"✓ UI module {module_name} already exists")
                continue

            print(f"Creating UI module: {module_name}")

            content = f'''#!/usr/bin/env python3
"""
{file_name.replace('_', ' ').title()} UI Module
Provides UI data structures for the service
"""

from dbbasic_unified_ui import get_master_layout

def get_{service_key}_dashboard():
    """Get dashboard UI for {service_key}"""
    return get_master_layout(
        title='{service_key.replace("_", " ").title()}',
        service_name='{service_key}',
        content=[
            {{
                'type': 'hero',
                'title': '{service_key.replace("_", " ").title()}',
                'subtitle': 'Service dashboard'
            }},
            {{
                'type': 'div',
                'id': 'content',
                'children': []
            }}
        ]
    )

def get_{service_key}_ui():
    """Get default UI for {service_key}"""
    return get_{service_key}_dashboard()
'''

            with open(module_name, 'w') as f:
                f.write(content)

            print(f"  ✅ Created {module_name}")

    def update_all_services(self):
        """Update all DBBasic services"""

        print("=" * 60)
        print("🔧 DBBasic Service Integration")
        print("=" * 60)

        # Create UI modules first
        self.create_service_ui_modules()

        # Update service files
        service_files = [
            ('realtime_monitor.py', 'monitor'),
            ('dbbasic_ai_service_builder.py', 'ai_services'),
            ('dbbasic_event_store.py', 'event_store'),
            ('dbbasic_crud_engine.py', 'data')
        ]

        print("\nUpdating service files...")
        for file_path, service_name in service_files:
            if Path(file_path).exists():
                self.update_service_file(file_path, service_name)

        self.print_summary()

    def print_summary(self):
        """Print integration summary"""
        print("\n" + "=" * 60)
        print("INTEGRATION SUMMARY")
        print("=" * 60)

        print(f"Services updated: {self.services_updated}")
        print(f"Endpoints converted: {self.endpoints_converted}")
        print(f"Files modified: {len(self.files_modified)}")

        if self.files_modified:
            print("\nModified files:")
            for file in self.files_modified:
                print(f"  • {file}")

        print("\n✅ Integration complete!")
        print("\nNext steps:")
        print("1. Test each service endpoint")
        print("2. Verify UI rendering")
        print("3. Check WebSocket connections")
        print("4. Deploy to production")


class ServiceLauncher:
    """Unified service launcher for DBBasic"""

    def __init__(self):
        self.services = []
        self.processes = []

    def create_launcher_script(self):
        """Create a unified launcher for all services"""

        launcher_content = '''#!/usr/bin/env python3
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
                'color': '\\033[92m'  # Green
            },
            {
                'name': 'Data Service',
                'file': 'dbbasic_crud_engine.py',
                'port': 8005,
                'color': '\\033[94m'  # Blue
            },
            {
                'name': 'AI Service Builder',
                'file': 'dbbasic_ai_service_builder.py',
                'port': 8003,
                'color': '\\033[95m'  # Purple
            },
            {
                'name': 'Event Store',
                'file': 'dbbasic_event_store.py',
                'port': 8006,
                'color': '\\033[93m'  # Yellow
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

            print(f"{service['color']}✅ {service['name']} started on port {service['port']}\\033[0m")
            return process
        except Exception as e:
            print(f"❌ Failed to start {service['name']}: {e}")
            return None

    def start_all(self):
        """Start all services"""
        print("=" * 60)
        print("🚀 DBBasic Platform Launcher")
        print("=" * 60)
        print("\\nStarting all services...\\n")

        for service in self.services:
            process = self.start_service(service)
            if process:
                self.processes.append(process)
            time.sleep(2)  # Give each service time to start

        print("\\n" + "=" * 60)
        print("✅ All services started!")
        print("=" * 60)
        print("\\n📌 Service URLs:")
        print("  • Dashboard: http://localhost:8004")
        print("  • Data Service: http://localhost:8005")
        print("  • AI Services: http://localhost:8003")
        print("  • Event Store: http://localhost:8006")
        print("  • API Docs: http://localhost:8005/docs")
        print("\\nPress Ctrl+C to stop all services\\n")

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
        print("\\n\\nStopping all services...")

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
'''

        with open('launch_dbbasic.py', 'w') as f:
            f.write(launcher_content)

        # Make it executable
        os.chmod('launch_dbbasic.py', 0o755)

        print("✅ Created launch_dbbasic.py")
        print("   Run with: python launch_dbbasic.py")


class WebSocketIntegrator:
    """Add WebSocket support for live UI updates"""

    def create_websocket_handler(self):
        """Create unified WebSocket handler"""

        ws_content = '''#!/usr/bin/env python3
"""
DBBasic WebSocket Handler
Unified WebSocket support for live UI updates
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio

class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.service_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, service: str = None):
        """Accept new connection"""
        await websocket.accept()
        self.active_connections.append(websocket)

        if service:
            if service not in self.service_connections:
                self.service_connections[service] = []
            self.service_connections[service].append(websocket)

    def disconnect(self, websocket: WebSocket, service: str = None):
        """Remove connection"""
        self.active_connections.remove(websocket)

        if service and service in self.service_connections:
            self.service_connections[service].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific connection"""
        await websocket.send_text(message)

    async def broadcast(self, message: str, service: str = None):
        """Broadcast to all or service-specific connections"""
        connections = self.service_connections.get(service, self.active_connections) if service else self.active_connections

        for connection in connections:
            try:
                await connection.send_text(message)
            except:
                # Connection closed, remove it
                await self.disconnect(connection, service)

# Global connection manager
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, service: str = None):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, service)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            # Process message
            message = json.loads(data)

            if message.get('type') == 'subscribe':
                # Subscribe to specific events
                pass
            elif message.get('type') == 'update':
                # Broadcast UI update
                await manager.broadcast(json.dumps({
                    'type': 'ui_update',
                    'target': message.get('target'),
                    'data': message.get('data')
                }), service)

    except WebSocketDisconnect:
        manager.disconnect(websocket, service)

async def send_ui_update(target_id: str, new_value: any, service: str = None):
    """Send UI update to all connected clients"""
    await manager.broadcast(json.dumps({
        'type': 'ui_update',
        'target': target_id,
        'value': new_value
    }), service)

async def send_metric_update(metrics: Dict, service: str = None):
    """Send metric updates"""
    await manager.broadcast(json.dumps({
        'type': 'metrics',
        'data': metrics
    }), service)
'''

        with open('dbbasic_websocket.py', 'w') as f:
            f.write(ws_content)

        print("✅ Created dbbasic_websocket.py")


def main():
    """Run all integration tasks"""

    print("🔧 Starting DBBasic Presentation Layer Integration")
    print("=" * 60)

    # Step 1: Integrate with services
    integrator = ServiceIntegrator()
    integrator.update_all_services()

    # Step 2: Create launcher
    launcher = ServiceLauncher()
    launcher.create_launcher_script()

    # Step 3: Add WebSocket support
    ws_integrator = WebSocketIntegrator()
    ws_integrator.create_websocket_handler()

    # Step 4: Create deployment script
    create_deployment_script()

    print("\n" + "=" * 60)
    print("🎉 INTEGRATION COMPLETE!")
    print("=" * 60)

    print("\n📋 Created files:")
    print("  • UI modules for each service")
    print("  • launch_dbbasic.py - Unified launcher")
    print("  • dbbasic_websocket.py - WebSocket handler")
    print("  • deploy_dbbasic.sh - Deployment script")

    print("\n🚀 To start DBBasic:")
    print("  python launch_dbbasic.py")

    print("\n📦 To deploy:")
    print("  ./deploy_dbbasic.sh")


def create_deployment_script():
    """Create deployment script"""

    deploy_content = '''#!/bin/bash

# DBBasic Deployment Script
# Deploy DBBasic with Presentation Layer

echo "======================================"
echo "🚀 DBBasic Deployment"
echo "======================================"

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\\d+\\.\\d+')
echo "✓ Python version: $python_version"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Generate UI files
echo "Generating UI with Presentation Layer..."
python generate_all_ui.py

# Run tests
echo "Running tests..."
python -m pytest tests/ -v

# Start services
echo "Starting DBBasic services..."
python launch_dbbasic.py &

echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "Services running at:"
echo "  • Dashboard: http://localhost:8004"
echo "  • Data Service: http://localhost:8005"
echo "  • AI Services: http://localhost:8003"
echo "  • Event Store: http://localhost:8006"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
wait
'''

    with open('deploy_dbbasic.sh', 'w') as f:
        f.write(deploy_content)

    os.chmod('deploy_dbbasic.sh', 0o755)

    print("✅ Created deploy_dbbasic.sh")


if __name__ == "__main__":
    main()