#!/usr/bin/env python3
"""
DBBasic Real-time Monitor - On-Demand Mode
Only processes services when there are actual requests, not continuous simulation
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
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

app = FastAPI(title="DBBasic Realtime Monitor - On Demand")

# Store for active connections
active_connections: List[WebSocket] = []

# Metrics storage
metrics = {
    "operations_per_second": deque(maxlen=60),
    "rows_per_second": 402000000,  # Our benchmark
    "active_connections": 0,
    "total_operations": 0,
    "service_calls": deque(maxlen=100),
    "last_activity": None,
    "mode": "on-demand"  # vs "continuous"
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

@app.post("/api/service/{service_name}")
async def call_service_endpoint(service_name: str, payload: Dict[str, Any]):
    """
    Call a service on-demand via API endpoint.
    This is the main difference - services only run when explicitly called!
    """
    if service_name not in services:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")

    try:
        # Record start time
        start_time = time.time()

        # Call the actual service
        service_func = services[service_name]
        result = await service_func(payload)

        # Calculate execution time
        execution_time = (time.time() - start_time) * 1000  # ms

        # Create activity event
        event = {
            "type": "service_call",
            "timestamp": datetime.now().isoformat(),
            "service": service_name,
            "execution_time_ms": round(execution_time, 3),
            "success": result.get("success", False),
            "data": result.get("data", {}),
            "mode": "on-demand"
        }

        # Store metrics
        metrics["service_calls"].append(event)
        metrics["total_operations"] += 1
        metrics["last_activity"] = datetime.now().isoformat()

        # Broadcast to connected clients
        await broadcast_message({
            **event,
            "data_preview": str(result.get("data", {}))[:100] + "..." if result.get("data") else "No data"
        })

        return JSONResponse(content={
            "success": True,
            "execution_time_ms": round(execution_time, 3),
            "result": result
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.post("/api/batch")
async def batch_process(requests: List[Dict[str, Any]]):
    """
    Process multiple service requests in batch.
    Useful for testing or bulk operations.
    """
    results = []

    for request in requests:
        service_name = request.get("service")
        payload = request.get("payload", {})

        if service_name in services:
            try:
                start_time = time.time()
                result = await services[service_name](payload)
                execution_time = (time.time() - start_time) * 1000

                results.append({
                    "service": service_name,
                    "success": True,
                    "execution_time_ms": round(execution_time, 3),
                    "result": result
                })

                # Update metrics
                metrics["total_operations"] += 1

            except Exception as e:
                results.append({
                    "service": service_name,
                    "success": False,
                    "error": str(e)
                })

    metrics["last_activity"] = datetime.now().isoformat()

    # Broadcast summary
    await broadcast_message({
        "type": "batch_complete",
        "timestamp": datetime.now().isoformat(),
        "total_requests": len(requests),
        "successful": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success"))
    })

    return JSONResponse(content={
        "batch_size": len(requests),
        "results": results
    })

async def calculate_metrics():
    """Calculate and broadcast system metrics periodically"""
    while True:
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # Calculate operations per second (based on last minute)
            now = datetime.now()
            recent_ops = [
                op for op in metrics["service_calls"]
                if op.get("timestamp") and
                (now - datetime.fromisoformat(op["timestamp"])).seconds < 60
            ]
            ops_per_sec = len(recent_ops) / 60 if recent_ops else 0

            # Prepare metrics message
            metrics_msg = {
                "type": "metrics",
                "timestamp": now.isoformat(),
                "data": {
                    "operations_per_second": round(ops_per_sec, 2),
                    "rows_per_second": metrics["rows_per_second"],
                    "active_connections": len(active_connections),
                    "total_operations": metrics["total_operations"],
                    "cpu_percent": cpu_percent,
                    "memory_used_gb": round(memory.used / (1024**3), 2),
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "mode": metrics["mode"],
                    "last_activity": metrics["last_activity"]
                }
            }

            await broadcast_message(metrics_msg)

        except Exception as e:
            print(f"Error calculating metrics: {e}")

        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(calculate_metrics())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "mode": "on-demand",
            "timestamp": datetime.now().isoformat()
        })

        while True:
            data = await websocket.receive_text()
            # Handle any commands from client if needed

    except WebSocketDisconnect:
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
    <title>DBBasic Monitor - On-Demand Mode</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e27;
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            flex-direction: column;
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

        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
            text-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }

        .mode-indicator {
            background: #2196F3;
            color: white;
            padding: 0.25rem 1rem;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
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
        }

        .test-controls {
            margin-top: 2rem;
        }

        .btn {
            width: 100%;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-secondary {
            background: rgba(76, 175, 80, 0.2);
            border: 1px solid #4CAF50;
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

        .idle-message {
            text-align: center;
            color: #666;
            padding: 2rem;
            font-style: italic;
        }

        .timestamp { color: #666; margin-right: 1rem; }
        .service-name { color: #4CAF50; font-weight: bold; margin-right: 1rem; }
        .exec-time { color: #2196F3; margin-right: 1rem; }
    </style>
</head>
<body>
    <div class="header">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div class="logo">DBBasic</div>
            <span style="color: #666; font-size: 14px;">Real-time Service Monitor</span>
        </div>
        <div class="mode-indicator">ON-DEMAND MODE</div>
        <div>
            <span id="connection-status">Connecting...</span>
            <span style="margin-left: 1rem;">Last Activity: <span id="last-activity">Never</span></span>
        </div>
    </div>

    <div class="main-container">
        <div class="sidebar">
            <h3 style="font-size: 12px; text-transform: uppercase; color: #4CAF50; margin-bottom: 1rem;">Services Available</h3>
            <div id="services-list"></div>

            <div class="test-controls">
                <h3 style="font-size: 12px; text-transform: uppercase; color: #4CAF50; margin-bottom: 1rem;">Test Controls</h3>
                <button class="btn" onclick="testSingleService()">Test Single Service</button>
                <button class="btn btn-secondary" onclick="testBatch()">Test Batch (10 calls)</button>
            </div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 1rem;">
            <div class="metrics-row">
                <div class="metric-card">
                    <div class="metric-value" id="ops-per-sec">0</div>
                    <div class="metric-label">Ops/sec (last min)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">402M</div>
                    <div class="metric-label">Max Rows/sec</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="total-ops">0</div>
                    <div class="metric-label">Total Ops</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="cpu-usage">0%</div>
                    <div class="metric-label">CPU Usage</div>
                </div>
            </div>

            <div class="data-stream">
                <h3 style="font-size: 14px; color: #4CAF50; margin-bottom: 1rem;">
                    Service Activity (On-Demand Only)
                </h3>
                <div class="stream-content" id="stream-content">
                    <div class="idle-message">
                        Waiting for service calls...<br><br>
                        Services only run when explicitly called.<br>
                        Use the test buttons or call the API endpoints directly.
                    </div>
                </div>
            </div>
        </div>

        <div class="sidebar">
            <h3 style="font-size: 12px; text-transform: uppercase; color: #4CAF50; margin-bottom: 1rem;">API Endpoints</h3>
            <div style="font-family: monospace; font-size: 11px; color: #999;">
                <div style="margin-bottom: 1rem;">
                    <div style="color: #4CAF50;">POST /api/service/{name}</div>
                    <div>Call a specific service</div>
                </div>
                <div style="margin-bottom: 1rem;">
                    <div style="color: #4CAF50;">POST /api/batch</div>
                    <div>Process multiple requests</div>
                </div>
                <div style="margin-bottom: 1rem;">
                    <div style="color: #4CAF50;">GET /api/metrics</div>
                    <div>Get current metrics</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const ws = new WebSocket('ws://localhost:8005/ws');
        const streamContent = document.getElementById('stream-content');
        const services = ['calculate_shipping', 'calculate_discount', 'calculate_order_total',
                         'send_notification', 'detect_fraud', 'segment_customer'];

        ws.onopen = () => {
            document.getElementById('connection-status').textContent = 'Connected';
            document.getElementById('connection-status').style.color = '#4CAF50';
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'service_call') {
                // Clear idle message on first real activity
                if (streamContent.querySelector('.idle-message')) {
                    streamContent.innerHTML = '';
                }

                const entry = document.createElement('div');
                entry.className = 'stream-entry';
                entry.innerHTML = `
                    <span class="timestamp">${new Date(data.timestamp).toLocaleTimeString()}</span>
                    <span class="service-name">${data.service}</span>
                    <span class="exec-time">${data.execution_time_ms}ms</span>
                    <span>${data.data_preview || 'No data'}</span>
                `;
                streamContent.insertBefore(entry, streamContent.firstChild);

                // Keep only last 50 entries
                while (streamContent.children.length > 50) {
                    streamContent.removeChild(streamContent.lastChild);
                }

            } else if (data.type === 'metrics') {
                document.getElementById('ops-per-sec').textContent = data.data.operations_per_second.toFixed(2);
                document.getElementById('total-ops').textContent = data.data.total_operations.toLocaleString();
                document.getElementById('cpu-usage').textContent = data.data.cpu_percent + '%';

                if (data.data.last_activity) {
                    const lastTime = new Date(data.data.last_activity);
                    document.getElementById('last-activity').textContent = lastTime.toLocaleTimeString();
                }
            }
        };

        ws.onclose = () => {
            document.getElementById('connection-status').textContent = 'Disconnected';
            document.getElementById('connection-status').style.color = '#f44336';
        };

        // Initialize services list
        document.getElementById('services-list').innerHTML = services.map(service => `
            <div style="padding: 0.5rem; margin-bottom: 0.5rem; background: rgba(76, 175, 80, 0.1);
                        border-radius: 4px; font-size: 12px;">
                ${service.replace(/_/g, ' ')}
            </div>
        `).join('');

        async function testSingleService() {
            const service = services[Math.floor(Math.random() * services.length)];
            const payload = generateTestPayload(service);

            const response = await fetch(`/api/service/${service}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            console.log('Service result:', result);
        }

        async function testBatch() {
            const requests = [];
            for (let i = 0; i < 10; i++) {
                const service = services[Math.floor(Math.random() * services.length)];
                requests.push({
                    service: service,
                    payload: generateTestPayload(service)
                });
            }

            const response = await fetch('/api/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requests)
            });

            const result = await response.json();
            console.log('Batch result:', result);
        }

        function generateTestPayload(service) {
            // Generate appropriate test data for each service
            const payloads = {
                calculate_shipping: {
                    weight: Math.random() * 20,
                    shipping_speed: ['standard', 'express', 'overnight'][Math.floor(Math.random() * 3)],
                    is_fragile: Math.random() > 0.5,
                    order_total: Math.random() * 500
                },
                calculate_discount: {
                    customer_tier: ['bronze', 'silver', 'gold', 'platinum'][Math.floor(Math.random() * 4)],
                    order_total: Math.random() * 1000,
                    items_count: Math.floor(Math.random() * 10) + 1
                },
                calculate_order_total: {
                    items: Array(Math.floor(Math.random() * 5) + 1).fill(0).map(() => ({
                        price: Math.random() * 100,
                        quantity: Math.floor(Math.random() * 5) + 1
                    })),
                    customer_location: {
                        state: ['CA', 'TX', 'NY', 'FL'][Math.floor(Math.random() * 4)],
                        city: ['San Francisco', 'Austin', 'New York', 'Miami'][Math.floor(Math.random() * 4)]
                    }
                },
                send_notification: {
                    notification_type: ['email', 'sms', 'push'][Math.floor(Math.random() * 3)],
                    recipient: { email: 'user@example.com' },
                    subject: 'Test Notification',
                    message: 'Test message content'
                },
                detect_fraud: {
                    order_data: { total: Math.random() * 5000 },
                    customer_data: {
                        account_age_days: Math.floor(Math.random() * 365),
                        previous_orders: Math.floor(Math.random() * 50)
                    },
                    payment_data: { method: ['card', 'paypal', 'prepaid_card'][Math.floor(Math.random() * 3)] }
                },
                segment_customer: {
                    customer_id: 'CUST' + Math.floor(Math.random() * 10000),
                    purchase_history: {
                        total_orders: Math.floor(Math.random() * 100),
                        lifetime_value: Math.random() * 10000,
                        days_since_last_order: Math.floor(Math.random() * 365)
                    },
                    engagement_metrics: {
                        email_open_rate: Math.random() * 0.5,
                        app_usage_days_per_month: Math.floor(Math.random() * 30)
                    }
                }
            };

            return payloads[service] || {};
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/metrics")
async def get_metrics():
    """Get current metrics as JSON"""
    return JSONResponse({
        "mode": "on-demand",
        "total_operations": metrics["total_operations"],
        "recent_calls": list(metrics["service_calls"])[-10:],
        "last_activity": metrics["last_activity"]
    })

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 DBBasic On-Demand Monitor Starting...")
    print("   Services only run when explicitly called")
    print("   No continuous simulation - pure on-demand processing\n")
    uvicorn.run(app, host="0.0.0.0", port=8005)