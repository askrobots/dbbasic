#!/usr/bin/env python3
"""
DBBasic Dashboard Service
Real-time dashboard with live metrics, system status, and operations overview
"""

import asyncio
import json
import logging
import time
import psutil
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

import duckdb
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    uptime_seconds: int
    active_connections: int
    timestamp: str

@dataclass
class DatabaseMetrics:
    total_tables: int
    total_records: int
    queries_per_second: float
    avg_query_time_ms: float
    database_size_mb: float
    timestamp: str

@dataclass
class ServiceStatus:
    name: str
    status: str  # running, stopped, error
    port: Optional[int]
    uptime_seconds: int
    last_activity: str

@dataclass
class RecentActivity:
    timestamp: str
    action: str
    resource: str
    user: str
    details: str

class DashboardService:
    """Real-time dashboard service providing system and application metrics"""

    def __init__(self):
        self.start_time = time.time()
        self.websocket_connections: List[WebSocket] = []
        self.query_counter = 0
        self.query_times = []

        # Initialize database connections for metrics
        self.metrics_db = duckdb.connect("dashboard_metrics.db")
        self._init_metrics_database()

    def _init_metrics_database(self):
        """Initialize metrics database tables"""
        self.metrics_db.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                timestamp TIMESTAMP PRIMARY KEY,
                cpu_percent FLOAT,
                memory_percent FLOAT,
                disk_usage_percent FLOAT,
                active_connections INTEGER
            )
        """)

        self.metrics_db.execute("""
            CREATE TABLE IF NOT EXISTS database_metrics (
                timestamp TIMESTAMP PRIMARY KEY,
                total_tables INTEGER,
                total_records INTEGER,
                queries_per_second FLOAT,
                avg_query_time_ms FLOAT,
                database_size_mb FLOAT
            )
        """)

        self.metrics_db.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP,
                action VARCHAR(100),
                resource VARCHAR(100),
                user_id VARCHAR(100),
                details TEXT
            )
        """)

    def get_system_metrics(self) -> SystemMetrics:
        """Get current system performance metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime = int(time.time() - self.start_time)

        metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=disk.percent,
            uptime_seconds=uptime,
            active_connections=len(self.websocket_connections),
            timestamp=datetime.now().isoformat()
        )

        # Store in database
        self.metrics_db.execute("""
            INSERT INTO system_metrics
            (timestamp, cpu_percent, memory_percent, disk_usage_percent, active_connections)
            VALUES (?, ?, ?, ?, ?)
        """, (metrics.timestamp, metrics.cpu_percent, metrics.memory_percent,
              metrics.disk_usage_percent, metrics.active_connections))

        return metrics

    def get_database_metrics(self) -> DatabaseMetrics:
        """Get database performance metrics"""
        try:
            # Count tables and records across all DBBasic databases
            total_tables = 0
            total_records = 0
            total_size_mb = 0

            # Scan for database files
            for db_file in Path('.').glob('*.db'):
                try:
                    conn = duckdb.connect(str(db_file))

                    # Get table count
                    tables = conn.execute("SHOW TABLES").fetchall()
                    total_tables += len(tables)

                    # Get record count
                    for table in tables:
                        table_name = table[0]
                        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        total_records += count

                    # Get file size
                    total_size_mb += db_file.stat().st_size / (1024 * 1024)

                    conn.close()
                except Exception:
                    continue

            # Calculate query performance
            qps = self.query_counter / max(1, time.time() - self.start_time)
            avg_query_time = sum(self.query_times) / max(1, len(self.query_times))

        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            total_tables = 0
            total_records = 0
            total_size_mb = 0
            qps = 0
            avg_query_time = 0

        metrics = DatabaseMetrics(
            total_tables=total_tables,
            total_records=total_records,
            queries_per_second=qps,
            avg_query_time_ms=avg_query_time,
            database_size_mb=total_size_mb,
            timestamp=datetime.now().isoformat()
        )

        # Store in database
        self.metrics_db.execute("""
            INSERT INTO database_metrics
            (timestamp, total_tables, total_records, queries_per_second, avg_query_time_ms, database_size_mb)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (metrics.timestamp, metrics.total_tables, metrics.total_records,
              metrics.queries_per_second, metrics.avg_query_time_ms, metrics.database_size_mb))

        return metrics

    def get_service_status(self) -> List[ServiceStatus]:
        """Get status of DBBasic services"""
        services = []

        # Common DBBasic services and their expected ports
        service_configs = [
            {"name": "CRUD Engine", "port": 8005, "process": "dbbasic_crud_engine.py"},
            {"name": "AI Service Builder", "port": 8003, "process": "dbbasic_ai_service_builder.py"},
            {"name": "Real-time Monitor", "port": 8004, "process": "realtime_monitor.py"},
            {"name": "Event Store", "port": 8006, "process": "dbbasic_event_store.py"},
            {"name": "Dashboard", "port": 8007, "process": "dbbasic_dashboard.py"},
        ]

        for config in service_configs:
            try:
                # Check if process is running
                is_running = False
                uptime = 0

                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if config['process'] in cmdline:
                            is_running = True
                            uptime = int(time.time() - proc.info['create_time'])
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                status = ServiceStatus(
                    name=config['name'],
                    status='running' if is_running else 'stopped',
                    port=config['port'],
                    uptime_seconds=uptime,
                    last_activity=datetime.now().isoformat()
                )
                services.append(status)

            except Exception as e:
                logger.error(f"Error checking service {config['name']}: {e}")
                services.append(ServiceStatus(
                    name=config['name'],
                    status='error',
                    port=config['port'],
                    uptime_seconds=0,
                    last_activity=datetime.now().isoformat()
                ))

        return services

    def get_recent_activity(self, limit: int = 10) -> List[RecentActivity]:
        """Get recent system activity"""
        try:
            activities = self.metrics_db.execute("""
                SELECT timestamp, action, resource, user_id, details
                FROM activity_log
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [RecentActivity(
                timestamp=row[0],
                action=row[1],
                resource=row[2],
                user=row[3] or "system",
                details=row[4] or ""
            ) for row in activities]

        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []

    def log_activity(self, action: str, resource: str, user_id: str = None, details: str = None):
        """Log system activity"""
        try:
            self.metrics_db.execute("""
                INSERT INTO activity_log (timestamp, action, resource, user_id, details)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now().isoformat(), action, resource, user_id, details))
        except Exception as e:
            logger.error(f"Error logging activity: {e}")

    def record_query(self, query_time_ms: float):
        """Record query execution time for performance metrics"""
        self.query_counter += 1
        self.query_times.append(query_time_ms)

        # Keep only last 1000 query times to prevent memory growth
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]

    async def broadcast_metrics(self):
        """Broadcast real-time metrics to all connected websockets"""
        if not self.websocket_connections:
            return

        try:
            system_metrics = self.get_system_metrics()
            database_metrics = self.get_database_metrics()
            service_status = self.get_service_status()
            recent_activity = self.get_recent_activity(5)

            dashboard_data = {
                "type": "metrics_update",
                "system_metrics": asdict(system_metrics),
                "database_metrics": asdict(database_metrics),
                "service_status": [asdict(s) for s in service_status],
                "recent_activity": [asdict(a) for a in recent_activity],
                "timestamp": datetime.now().isoformat()
            }

            # Send to all connected clients
            disconnected = []
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_text(json.dumps(dashboard_data))
                except Exception:
                    disconnected.append(websocket)

            # Remove disconnected clients
            for ws in disconnected:
                self.websocket_connections.remove(ws)

        except Exception as e:
            logger.error(f"Error broadcasting metrics: {e}")

    async def add_websocket(self, websocket: WebSocket):
        """Add new websocket connection"""
        await websocket.accept()
        self.websocket_connections.append(websocket)

        # Send initial data immediately
        await self.broadcast_metrics()

    def remove_websocket(self, websocket: WebSocket):
        """Remove websocket connection"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)

# Global dashboard service instance
dashboard_service = DashboardService()

# FastAPI application
app = FastAPI(title="DBBasic Dashboard", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard_page():
    """Serve the main dashboard page"""
    # Read the dashboard template and make it functional
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DBBasic Dashboard - Live Metrics</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
        }

        .header {
            background: #fff;
            border-bottom: 1px solid #e0e0e0;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo {
            font-family: 'Times New Roman', Times, serif;
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }

        .speed-badge {
            background: #4CAF50;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }

        .nav {
            display: flex;
            gap: 2rem;
        }

        .nav a {
            color: #666;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: all 0.2s;
        }

        .nav a:hover {
            background: #f0f0f0;
            color: #333;
        }

        .nav a.active {
            background: #4CAF50;
            color: white;
        }

        .main {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .metric-title {
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
        }

        .metric-unit {
            font-size: 16px;
            color: #666;
            margin-left: 0.5rem;
        }

        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            display: inline-block;
            margin-right: 0.5rem;
        }

        .status-indicator.warning {
            background: #FF9800;
        }

        .status-indicator.error {
            background: #f44336;
        }

        .progress-bar {
            background: #e0e0e0;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }

        .progress-fill {
            height: 100%;
            background: #4CAF50;
            transition: width 0.3s;
        }

        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .service-card {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .service-info h3 {
            font-size: 14px;
            margin-bottom: 0.25rem;
        }

        .service-details {
            font-size: 12px;
            color: #666;
        }

        .activity-feed {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .activity-header {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .activity-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .activity-item:last-child {
            border-bottom: none;
        }

        .activity-time {
            font-size: 12px;
            color: #666;
            min-width: 60px;
        }

        .activity-text {
            font-size: 14px;
        }

        .live-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 12px;
            color: #4CAF50;
            font-weight: bold;
        }

        .pulse {
            width: 8px;
            height: 8px;
            background: #4CAF50;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .offline {
            opacity: 0.6;
        }

        .offline .live-indicator {
            color: #f44336;
        }

        .offline .pulse {
            background: #f44336;
        }
    </style>
</head>
<body>
    <header class="header">
        <div>
            <div class="logo">DBBasic</div>
            <div class="speed-badge">402M rows/sec</div>
        </div>
        <nav class="nav">
            <a href="#" class="active">Dashboard</a>
            <a href="/">CRUD Engine</a>
            <a href="/static/ai_service_builder.html">AI Services</a>
            <a href="/static/mockups.html">Mockups</a>
            <a href="/docs">API Docs</a>
        </nav>
        <div class="live-indicator">
            <div class="pulse"></div>
            <span id="connection-status">LIVE</span>
        </div>
    </header>

    <main class="main">
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-title">CPU Usage</div>
                    <div class="status-indicator" id="cpu-status"></div>
                </div>
                <div class="metric-value" id="cpu-value">0<span class="metric-unit">%</span></div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpu-progress"></div>
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-title">Memory Usage</div>
                    <div class="status-indicator" id="memory-status"></div>
                </div>
                <div class="metric-value" id="memory-value">0<span class="metric-unit">%</span></div>
                <div class="progress-bar">
                    <div class="progress-fill" id="memory-progress"></div>
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-title">Total Records</div>
                    <div class="status-indicator"></div>
                </div>
                <div class="metric-value" id="records-value">0</div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-title">Queries/Second</div>
                    <div class="status-indicator"></div>
                </div>
                <div class="metric-value" id="qps-value">0</div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-title">Active Tables</div>
                    <div class="status-indicator"></div>
                </div>
                <div class="metric-value" id="tables-value">0</div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-title">Database Size</div>
                    <div class="status-indicator"></div>
                </div>
                <div class="metric-value" id="db-size-value">0<span class="metric-unit">MB</span></div>
            </div>
        </div>

        <div class="services-grid" id="services-grid">
            <!-- Services will be populated dynamically -->
        </div>

        <div class="activity-feed">
            <div class="activity-header">
                🕐 Recent Activity
            </div>
            <div id="activity-list">
                <!-- Activity items will be populated dynamically -->
            </div>
        </div>
    </main>

    <script>
        let ws = null;
        let reconnectTimeout = null;

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = function(event) {
                console.log('WebSocket connected');
                document.getElementById('connection-status').textContent = 'LIVE';
                document.body.classList.remove('offline');

                if (reconnectTimeout) {
                    clearTimeout(reconnectTimeout);
                    reconnectTimeout = null;
                }
            };

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };

            ws.onclose = function(event) {
                console.log('WebSocket disconnected');
                document.getElementById('connection-status').textContent = 'OFFLINE';
                document.body.classList.add('offline');

                // Attempt to reconnect after 3 seconds
                reconnectTimeout = setTimeout(connectWebSocket, 3000);
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }

        function updateDashboard(data) {
            if (data.type === 'metrics_update') {
                // Update system metrics
                const systemMetrics = data.system_metrics;
                updateMetric('cpu', systemMetrics.cpu_percent);
                updateMetric('memory', systemMetrics.memory_percent);

                // Update database metrics
                const dbMetrics = data.database_metrics;
                document.getElementById('records-value').textContent = dbMetrics.total_records.toLocaleString();
                document.getElementById('qps-value').textContent = dbMetrics.queries_per_second.toFixed(1);
                document.getElementById('tables-value').textContent = dbMetrics.total_tables;
                document.getElementById('db-size-value').innerHTML = dbMetrics.database_size_mb.toFixed(1) + '<span class="metric-unit">MB</span>';

                // Update services
                updateServices(data.service_status);

                // Update activity
                updateActivity(data.recent_activity);
            }
        }

        function updateMetric(name, value) {
            const valueElement = document.getElementById(name + '-value');
            const progressElement = document.getElementById(name + '-progress');
            const statusElement = document.getElementById(name + '-status');

            valueElement.innerHTML = Math.round(value) + '<span class="metric-unit">%</span>';
            progressElement.style.width = value + '%';

            // Update status indicator color
            if (value > 80) {
                statusElement.className = 'status-indicator error';
            } else if (value > 60) {
                statusElement.className = 'status-indicator warning';
            } else {
                statusElement.className = 'status-indicator';
            }
        }

        function updateServices(services) {
            const grid = document.getElementById('services-grid');
            grid.innerHTML = '';

            services.forEach(service => {
                const serviceCard = document.createElement('div');
                serviceCard.className = 'service-card';

                const statusClass = service.status === 'running' ? '' :
                                  service.status === 'error' ? 'error' : 'warning';

                const uptime = service.uptime_seconds > 0 ? formatUptime(service.uptime_seconds) : 'Not running';

                serviceCard.innerHTML = `
                    <div class="status-indicator ${statusClass}"></div>
                    <div class="service-info">
                        <h3>${service.name}</h3>
                        <div class="service-details">
                            Port ${service.port} • ${uptime}
                        </div>
                    </div>
                `;

                grid.appendChild(serviceCard);
            });
        }

        function updateActivity(activities) {
            const list = document.getElementById('activity-list');
            list.innerHTML = '';

            activities.forEach(activity => {
                const item = document.createElement('div');
                item.className = 'activity-item';

                const time = new Date(activity.timestamp).toLocaleTimeString();

                item.innerHTML = `
                    <div class="activity-time">${time}</div>
                    <div class="activity-text">
                        <strong>${activity.action}</strong> ${activity.resource}
                        ${activity.user ? 'by ' + activity.user : ''}
                    </div>
                `;

                list.appendChild(item);
            });
        }

        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);

            if (hours > 0) {
                return `${hours}h ${minutes}m`;
            } else {
                return `${minutes}m`;
            }
        }

        // Initialize dashboard
        connectWebSocket();
    </script>
</body>
</html>
    """
    return dashboard_html

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await dashboard_service.add_websocket(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_service.remove_websocket(websocket)

@app.get("/api/metrics")
async def get_metrics():
    """Get current dashboard metrics as JSON"""
    system_metrics = dashboard_service.get_system_metrics()
    database_metrics = dashboard_service.get_database_metrics()
    service_status = dashboard_service.get_service_status()
    recent_activity = dashboard_service.get_recent_activity()

    return {
        "system_metrics": asdict(system_metrics),
        "database_metrics": asdict(database_metrics),
        "service_status": [asdict(s) for s in service_status],
        "recent_activity": [asdict(a) for a in recent_activity]
    }

@app.post("/api/activity")
async def log_activity_endpoint(action: str, resource: str, user_id: str = None, details: str = None):
    """Log system activity"""
    dashboard_service.log_activity(action, resource, user_id, details)
    return {"status": "logged"}

# Background task to broadcast metrics periodically
async def periodic_metrics_broadcast():
    """Periodically broadcast metrics to connected clients"""
    while True:
        await dashboard_service.broadcast_metrics()
        await asyncio.sleep(2)  # Update every 2 seconds

@app.on_event("startup")
async def startup_event():
    """Start background tasks when the application starts"""
    asyncio.create_task(periodic_metrics_broadcast())
    logger.info("🏠 DBBasic Dashboard started on port 8007")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8007)