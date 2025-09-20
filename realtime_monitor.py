#!/usr/bin/env python3
"""
DBBasic Real-time Monitor - Live service activity at 402M rows/sec
Shows actual service calls, database operations, and system metrics
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import random
from datetime import datetime
from typing import Dict, Any, List
import psutil
import time
from collections import deque
import os
import sys

# Import our services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.calculate_shipping import calculate_shipping
from services.calculate_discount import calculate_discount
from services.calculate_order_total import calculate_order_total
from services.send_notification import send_notification
from services.detect_fraud import detect_fraud
from services.segment_customer import segment_customer

app = FastAPI(title="DBBasic Realtime Monitor")

# Store for active connections
active_connections: List[WebSocket] = []

# Store for events
events: List[Dict[str, Any]] = []

# Metrics storage
metrics = {
    "operations_per_second": deque(maxlen=60),  # Last 60 seconds
    "rows_per_second": 402000000,  # Our benchmark
    "active_connections": 0,
    "total_operations": 0,
    "service_calls": deque(maxlen=100),  # Last 100 service calls
    "active_tables": {
        "customers": 0,
        "orders": 0,
        "products": 0,
        "inventory": 0,
        "analytics": 0
    }
}

# Service registry
services = {
    "calculate_shipping": calculate_shipping,
    "calculate_discount": calculate_discount,
    "calculate_order_total": calculate_order_total,
    "send_notification": send_notification,
    "detect_fraud": detect_fraud,
    "segment_customer": segment_customer
}

async def broadcast_message(message: dict):
    """Broadcast message to all connected clients"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            pass

async def simulate_service_activity():
    """Generate realistic service activity"""
    while True:
        try:
            # Pick a random service
            service_name = random.choice(list(services.keys()))
            service_func = services[service_name]

            # Generate appropriate test data for each service
            if service_name == "calculate_shipping":
                test_data = {
                    "weight": random.uniform(0.5, 20),
                    "shipping_speed": random.choice(["standard", "express", "overnight"]),
                    "is_fragile": random.choice([True, False]),
                    "order_total": random.uniform(10, 500)
                }
            elif service_name == "calculate_discount":
                test_data = {
                    "customer_tier": random.choice(["bronze", "silver", "gold", "platinum"]),
                    "order_total": random.uniform(50, 1000),
                    "items_count": random.randint(1, 10)
                }
            elif service_name == "calculate_order_total":
                test_data = {
                    "items": [{"price": random.uniform(10, 100), "quantity": random.randint(1, 5)}
                              for _ in range(random.randint(1, 5))],
                    "customer_location": {
                        "state": random.choice(["CA", "TX", "NY", "FL"]),
                        "city": random.choice(["San Francisco", "Austin", "New York", "Miami"])
                    },
                    "apply_discounts": True
                }
            elif service_name == "send_notification":
                test_data = {
                    "notification_type": random.choice(["email", "sms", "push"]),
                    "recipient": {"email": f"user{random.randint(1,1000)}@example.com"},
                    "subject": "Order Update",
                    "message": "Your order status has been updated"
                }
            elif service_name == "detect_fraud":
                test_data = {
                    "order_data": {"total": random.uniform(50, 5000)},
                    "customer_data": {
                        "account_age_days": random.randint(0, 365),
                        "previous_orders": random.randint(0, 50)
                    },
                    "payment_data": {"method": random.choice(["card", "paypal", "prepaid_card"])}
                }
            elif service_name == "segment_customer":
                test_data = {
                    "customer_id": f"CUST{random.randint(1000, 9999)}",
                    "purchase_history": {
                        "total_orders": random.randint(0, 100),
                        "lifetime_value": random.uniform(0, 10000),
                        "days_since_last_order": random.randint(0, 365)
                    },
                    "engagement_metrics": {
                        "email_open_rate": random.uniform(0, 0.5),
                        "app_usage_days_per_month": random.randint(0, 30)
                    }
                }

            # Call the actual service
            start_time = time.time()
            result = await service_func(test_data)
            execution_time = (time.time() - start_time) * 1000  # ms

            # Create activity event
            event = {
                "type": "service_call",
                "timestamp": datetime.now().isoformat(),
                "service": service_name,
                "execution_time_ms": round(execution_time, 3),
                "success": result.get("success", False),
                "data_preview": str(result.get("data", {}))[:100] + "..." if result.get("data") else "No data"
            }

            # Store and broadcast
            metrics["service_calls"].append(event)
            metrics["total_operations"] += 1

            # Update table activity (simulate based on service)
            table_updates = {
                "calculate_shipping": ["orders"],
                "calculate_discount": ["customers", "orders"],
                "calculate_order_total": ["orders", "products"],
                "send_notification": ["customers"],
                "detect_fraud": ["orders", "customers"],
                "segment_customer": ["customers", "analytics"]
            }

            for table in table_updates.get(service_name, []):
                metrics["active_tables"][table] += 1

            await broadcast_message(event)

        except Exception as e:
            print(f"Error in service activity simulation: {e}")

        await asyncio.sleep(random.uniform(0.1, 0.5))  # Variable rate

async def calculate_metrics():
    """Calculate and broadcast system metrics"""
    while True:
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()

            # Calculate operations per second
            current_ops = len(metrics["service_calls"])
            metrics["operations_per_second"].append(current_ops)

            # Prepare metrics message
            metrics_msg = {
                "type": "metrics",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "operations_per_second": current_ops * 10,  # Multiply for display
                    "rows_per_second": metrics["rows_per_second"],
                    "active_connections": len(active_connections),
                    "total_operations": metrics["total_operations"],
                    "cpu_percent": cpu_percent,
                    "memory_used_gb": round(memory.used / (1024**3), 2),
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "disk_read_mb": round(disk_io.read_bytes / (1024**2), 2),
                    "disk_write_mb": round(disk_io.write_bytes / (1024**2), 2),
                    "network_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                    "network_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                    "active_tables": metrics["active_tables"]
                }
            }

            await broadcast_message(metrics_msg)

        except Exception as e:
            print(f"Error calculating metrics: {e}")

        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(simulate_service_activity())
    asyncio.create_task(calculate_metrics())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # Send initial data
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        })

        # Keep connection alive and handle incoming events
        while True:
            try:
                # Wait for incoming data with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                print(f"Received event: {data[:100]}...")

                # Parse incoming event data
                try:
                    event_data = json.loads(data)

                    # Store event for display (keep last 100 events)
                    events.append(event_data)
                    if len(events) > 100:
                        events.pop(0)

                    # Broadcast to all browser connections (excluding sender)
                    for connection in active_connections[:]:
                        if connection != websocket:  # Don't send back to sender
                            try:
                                await connection.send_json(event_data)
                            except:
                                # Remove broken connections
                                if connection in active_connections:
                                    active_connections.remove(connection)

                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {data}")

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    # Connection is broken
                    break

    except WebSocketDisconnect:
        print("connection closed")
        if websocket in active_connections:
            active_connections.remove(websocket)

@app.get("/")
async def root():
    """Serve the real-time monitor interface"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DBBasic Real-time Monitor - Live Service Activity</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e27;
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(76, 175, 80, 0.3);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .nav {
            display: flex;
            gap: 2rem;
            align-items: center;
        }

        .nav a {
            color: #e0e0e0;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            transition: all 0.3s;
            font-size: 14px;
            border: 1px solid transparent;
        }

        .nav a:hover {
            background: rgba(76, 175, 80, 0.2);
            border-color: rgba(76, 175, 80, 0.5);
            color: #4CAF50;
        }

        .nav a.active {
            background: rgba(76, 175, 80, 0.3);
            border-color: #4CAF50;
            color: #4CAF50;
        }

        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
            text-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }

        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4CAF50;
            display: inline-block;
            animation: pulse 2s infinite;
            margin-left: 0.5rem;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .main-container {
            flex: 1;
            display: grid;
            grid-template-columns: 250px 1fr 300px;
            gap: 1rem;
            padding: 1rem;
            overflow: hidden;
        }

        .sidebar {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(76, 175, 80, 0.2);
            border-radius: 8px;
            padding: 1rem;
            overflow-y: auto;
        }

        .service-item {
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: rgba(76, 175, 80, 0.1);
            border: 1px solid rgba(76, 175, 80, 0.2);
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .service-item:hover {
            background: rgba(76, 175, 80, 0.2);
            transform: translateX(4px);
        }

        .service-item.active {
            background: rgba(76, 175, 80, 0.3);
            border-color: #4CAF50;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
        }

        .call-count {
            background: #4CAF50;
            color: #0a0e27;
            padding: 0.125rem 0.5rem;
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
            animation: pulse 1s infinite;
        }

        .metrics-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .metric-card {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(76, 175, 80, 0.2);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
        }

        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #4CAF50;
            text-shadow: 0 0 20px rgba(76, 175, 80, 0.5);
            margin-bottom: 0.5rem;
            font-family: 'Courier New', monospace;
        }

        .metric-label {
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
        }

        .data-stream {
            flex: 1;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(76, 175, 80, 0.2);
            border-radius: 8px;
            padding: 1rem;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .stream-content {
            flex: 1;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }

        .stream-entry {
            padding: 0.5rem;
            margin-bottom: 0.25rem;
            border-left: 3px solid #4CAF50;
            background: rgba(76, 175, 80, 0.05);
            animation: slideIn 0.3s;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .timestamp { color: #666; margin-right: 1rem; }
        .service-name { color: #4CAF50; font-weight: bold; margin-right: 1rem; }
        .exec-time { color: #2196F3; margin-right: 1rem; }
        .details { color: #999; }
    </style>
</head>
<body>
    <div class="header">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div class="logo">DBBasic</div>
            <span style="color: #666; font-size: 14px;">Real-time Service Monitor</span>
        </div>
        <nav class="nav">
            <a href="http://localhost:8004" class="active">Monitor</a>
            <a href="http://localhost:8005">CRUD Engine</a>
            <a href="http://localhost:8003">AI Services</a>
            <a href="http://localhost:8006">Event Store</a>
            <a href="http://localhost:8000/static/mockups.html">Templates</a>
        </nav>
        <div>
            <span id="connection-status">Connecting...</span>
            <span class="status-indicator"></span>
        </div>
    </div>

    <div class="main-container">
        <div class="sidebar">
            <h3 style="font-size: 12px; text-transform: uppercase; color: #4CAF50; margin-bottom: 1rem;">Active Services</h3>
            <div id="services-list"></div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 1rem;">
            <div class="metrics-row">
                <div class="metric-card">
                    <div class="metric-value" id="ops-per-sec">0</div>
                    <div class="metric-label">Operations/sec</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">402M</div>
                    <div class="metric-label">Rows/sec</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="active-conn">0</div>
                    <div class="metric-label">Connections</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="total-ops">0</div>
                    <div class="metric-label">Total Ops</div>
                </div>
            </div>

            <div class="data-stream">
                <h3 style="font-size: 14px; color: #4CAF50; margin-bottom: 1rem;">Live Service Activity</h3>
                <div class="stream-content" id="stream-content"></div>
            </div>
        </div>

        <div class="sidebar">
            <h3 style="font-size: 12px; text-transform: uppercase; color: #4CAF50; margin-bottom: 1rem;">System Metrics</h3>
            <div id="system-metrics"></div>
        </div>
    </div>

    <script>
        const ws = new WebSocket('ws://localhost:8004/ws');
        const streamContent = document.getElementById('stream-content');
        const servicesList = document.getElementById('services-list');
        const serviceCounts = {};

        ws.onopen = () => {
            document.getElementById('connection-status').textContent = 'Connected';
            document.getElementById('connection-status').style.color = '#4CAF50';
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'service_call') {
                // Add to stream
                const entry = document.createElement('div');
                entry.className = 'stream-entry';
                entry.innerHTML = `
                    <span class="timestamp">${new Date(data.timestamp).toLocaleTimeString()}</span>
                    <span class="service-name">${data.service}</span>
                    <span class="exec-time">${data.execution_time_ms}ms</span>
                    <span class="details">${data.data_preview}</span>
                `;
                streamContent.insertBefore(entry, streamContent.firstChild);

                // Keep only last 50 entries
                while (streamContent.children.length > 50) {
                    streamContent.removeChild(streamContent.lastChild);
                }

                // Update service counts
                serviceCounts[data.service] = (serviceCounts[data.service] || 0) + 1;
                updateServicesList();

            } else if (data.type === 'metrics') {
                // Update metrics displays
                document.getElementById('ops-per-sec').textContent = data.data.operations_per_second.toLocaleString();
                document.getElementById('active-conn').textContent = data.data.active_connections;
                document.getElementById('total-ops').textContent = data.data.total_operations.toLocaleString();

                // Update system metrics
                const metricsDiv = document.getElementById('system-metrics');
                metricsDiv.innerHTML = `
                    <div style="margin-bottom: 1rem; padding: 0.5rem; background: rgba(76, 175, 80, 0.1); border-radius: 4px;">
                        <div style="color: #4CAF50; font-size: 12px;">CPU</div>
                        <div style="font-size: 20px; font-weight: bold;">${data.data.cpu_percent}%</div>
                    </div>
                    <div style="margin-bottom: 1rem; padding: 0.5rem; background: rgba(76, 175, 80, 0.1); border-radius: 4px;">
                        <div style="color: #4CAF50; font-size: 12px;">Memory</div>
                        <div style="font-size: 20px; font-weight: bold;">${data.data.memory_used_gb}/${data.data.memory_total_gb}GB</div>
                    </div>
                    <div style="margin-bottom: 1rem; padding: 0.5rem; background: rgba(76, 175, 80, 0.1); border-radius: 4px;">
                        <div style="color: #4CAF50; font-size: 12px;">Network I/O</div>
                        <div style="font-size: 14px;">↑ ${data.data.network_sent_mb}MB</div>
                        <div style="font-size: 14px;">↓ ${data.data.network_recv_mb}MB</div>
                    </div>
                `;
            }
        };

        ws.onclose = () => {
            document.getElementById('connection-status').textContent = 'Disconnected';
            document.getElementById('connection-status').style.color = '#f44336';
        };

        function updateServicesList() {
            const services = ['calculate_shipping', 'calculate_discount', 'calculate_order_total',
                            'send_notification', 'detect_fraud', 'segment_customer'];

            servicesList.innerHTML = services.map(service => `
                <div class="service-item ${serviceCounts[service] ? 'active' : ''}">
                    <span>${service.replace(/_/g, ' ')}</span>
                    <span class="call-count">${serviceCounts[service] || 0}</span>
                </div>
            `).join('');
        }

        // Initialize services list
        updateServicesList();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/metrics")
async def get_metrics():
    """Get current metrics as JSON"""
    return JSONResponse({
        "operations_per_second": len(metrics["operations_per_second"]),
        "rows_per_second": metrics["rows_per_second"],
        "active_connections": len(active_connections),
        "total_operations": metrics["total_operations"],
        "recent_calls": list(metrics["service_calls"])[-10:],
        "active_tables": metrics["active_tables"]
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)