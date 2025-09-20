#!/usr/bin/env python3
"""
DBBasic Immutable Event Store
==============================
True event sourcing implementation for DBBasic framework.
All state changes are stored as immutable events that can be replayed.
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import duckdb
import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import logging

from presentation_layer import PresentationLayer
from bootstrap_components import ExtendedBootstrapRenderer
from dbbasic_unified_ui import get_master_layout, SERVICES

# Initialize presentation layer
PresentationLayer.add_renderer('bootstrap', ExtendedBootstrapRenderer())


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Event Models
class Event(BaseModel):
    """Immutable event in the event store"""
    event_id: str = None
    aggregate_id: str
    aggregate_type: str
    event_type: str
    event_version: int
    event_data: Dict[str, Any]
    event_metadata: Dict[str, Any] = {}
    event_timestamp: str = None
    sequence_number: Optional[int] = None

class EventQuery(BaseModel):
    """Query parameters for retrieving events"""
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    event_type: Optional[str] = None
    from_sequence: Optional[int] = None
    to_sequence: Optional[int] = None
    from_timestamp: Optional[str] = None
    to_timestamp: Optional[str] = None
    limit: int = 100

class Snapshot(BaseModel):
    """Snapshot of aggregate state at a point in time"""
    aggregate_id: str
    aggregate_type: str
    snapshot_version: int
    snapshot_data: Dict[str, Any]
    snapshot_timestamp: str = None

class EventStore:
    """
    Immutable Event Store implementation using DuckDB
    """

    def __init__(self, database_path: str = "event_store.db"):
        self.database_path = database_path
        self.conn = duckdb.connect(database_path)
        self._init_tables()
        self.projections: Dict[str, Callable] = {}
        self.event_handlers: List[Callable] = []

    def _init_tables(self):
        """Initialize event store tables"""
        # Events table - immutable, append-only
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                sequence_number BIGINT PRIMARY KEY,
                event_id VARCHAR NOT NULL UNIQUE,
                aggregate_id VARCHAR NOT NULL,
                aggregate_type VARCHAR NOT NULL,
                event_type VARCHAR NOT NULL,
                event_version INTEGER NOT NULL,
                event_data JSON NOT NULL,
                event_metadata JSON,
                event_timestamp TIMESTAMP NOT NULL
            )
        """)

        # Snapshots table - for performance optimization
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                aggregate_id VARCHAR NOT NULL,
                aggregate_type VARCHAR NOT NULL,
                snapshot_version INTEGER NOT NULL,
                snapshot_data JSON NOT NULL,
                snapshot_timestamp TIMESTAMP NOT NULL,

                PRIMARY KEY (aggregate_id, snapshot_version)
            )
        """)

        # Create indexes separately for DuckDB
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_aggregate ON events (aggregate_id, event_version)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON events (aggregate_type, event_type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON events (event_timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_aggregate_snapshot ON snapshots (aggregate_id, snapshot_version DESC)")

        # Projections table - materialized views
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS projections (
                projection_name VARCHAR NOT NULL,
                projection_key VARCHAR NOT NULL,
                projection_data JSON NOT NULL,
                last_sequence BIGINT NOT NULL,
                updated_at TIMESTAMP NOT NULL,

                PRIMARY KEY (projection_name, projection_key)
            )
        """)

        logger.info("✅ Event store tables initialized")

    def append_event(self, event: Event) -> int:
        """
        Append an event to the event store (immutable operation)
        Returns the sequence number of the stored event
        """
        # Generate IDs and timestamps if not provided
        if not event.event_id:
            event.event_id = str(uuid.uuid4())
        if not event.event_timestamp:
            event.event_timestamp = datetime.now(timezone.utc).isoformat()

        # Get next sequence number (atomic operation)
        result = self.conn.execute("""
            SELECT COALESCE(MAX(sequence_number), 0) + 1 as next_seq
            FROM events
        """).fetchone()

        sequence_number = result[0]

        # Get current version for this aggregate
        version_result = self.conn.execute("""
            SELECT COALESCE(MAX(event_version), 0) as current_version
            FROM events
            WHERE aggregate_id = ?
        """, [event.aggregate_id]).fetchone()

        event.event_version = version_result[0] + 1

        # Insert the event (immutable)
        self.conn.execute("""
            INSERT INTO events (
                sequence_number, event_id, aggregate_id, aggregate_type,
                event_type, event_version, event_data, event_metadata, event_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            sequence_number,
            event.event_id,
            event.aggregate_id,
            event.aggregate_type,
            event.event_type,
            event.event_version,
            json.dumps(event.event_data),
            json.dumps(event.event_metadata),
            event.event_timestamp
        ])

        # Notify event handlers
        event.sequence_number = sequence_number
        asyncio.create_task(self._notify_handlers(event))

        # Update projections
        asyncio.create_task(self._update_projections(event))

        logger.info(f"📝 Event stored: {event.event_type} for {event.aggregate_type}:{event.aggregate_id} (seq: {sequence_number})")
        return sequence_number

    async def _notify_handlers(self, event: Event):
        """Notify all registered event handlers"""
        for handler in self.event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

    async def _update_projections(self, event: Event):
        """Update registered projections based on the event"""
        for name, projection_func in self.projections.items():
            try:
                if asyncio.iscoroutinefunction(projection_func):
                    projection_data = await projection_func(event)
                else:
                    projection_data = projection_func(event)

                if projection_data:
                    self._save_projection(name, projection_data, event.sequence_number)
            except Exception as e:
                logger.error(f"Error updating projection {name}: {e}")

    def _save_projection(self, name: str, data: Dict[str, Any], sequence: int):
        """Save projection data"""
        for key, value in data.items():
            self.conn.execute("""
                INSERT OR REPLACE INTO projections
                (projection_name, projection_key, projection_data, last_sequence, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, [
                name, key, json.dumps(value), sequence,
                datetime.now(timezone.utc).isoformat()
            ])

    def get_events(self, query: EventQuery) -> List[Event]:
        """
        Query events from the store
        Events are immutable - this only reads
        """
        sql = "SELECT * FROM events WHERE 1=1"
        params = []

        if query.aggregate_id:
            sql += " AND aggregate_id = ?"
            params.append(query.aggregate_id)

        if query.aggregate_type:
            sql += " AND aggregate_type = ?"
            params.append(query.aggregate_type)

        if query.event_type:
            sql += " AND event_type = ?"
            params.append(query.event_type)

        if query.from_sequence:
            sql += " AND sequence_number >= ?"
            params.append(query.from_sequence)

        if query.to_sequence:
            sql += " AND sequence_number <= ?"
            params.append(query.to_sequence)

        if query.from_timestamp:
            sql += " AND event_timestamp >= ?"
            params.append(query.from_timestamp)

        if query.to_timestamp:
            sql += " AND event_timestamp <= ?"
            params.append(query.to_timestamp)

        sql += f" ORDER BY sequence_number LIMIT {query.limit}"

        results = self.conn.execute(sql, params).fetchall()

        events = []
        for row in results:
            events.append(Event(
                sequence_number=row[0],
                event_id=row[1],
                aggregate_id=row[2],
                aggregate_type=row[3],
                event_type=row[4],
                event_version=row[5],
                event_data=json.loads(row[6]),
                event_metadata=json.loads(row[7]) if row[7] else {},
                event_timestamp=row[8]
            ))

        return events

    def get_aggregate_events(self, aggregate_id: str, from_version: int = 0) -> List[Event]:
        """Get all events for a specific aggregate"""
        query = EventQuery(
            aggregate_id=aggregate_id,
            limit=10000  # Get all events for the aggregate
        )
        events = self.get_events(query)
        return [e for e in events if e.event_version > from_version]

    def rebuild_aggregate(self, aggregate_id: str, aggregate_type: str,
                         reducer: Callable) -> Dict[str, Any]:
        """
        Rebuild aggregate state by replaying all events
        This demonstrates the power of event sourcing
        """
        # Try to get latest snapshot
        snapshot = self.get_latest_snapshot(aggregate_id)

        if snapshot:
            state = snapshot.snapshot_data
            from_version = snapshot.snapshot_version
        else:
            state = {}
            from_version = 0

        # Get events after snapshot
        events = self.get_aggregate_events(aggregate_id, from_version)

        # Replay events through reducer
        for event in events:
            state = reducer(state, event)

        return state

    def save_snapshot(self, snapshot: Snapshot):
        """Save a snapshot for performance optimization"""
        if not snapshot.snapshot_timestamp:
            snapshot.snapshot_timestamp = datetime.now(timezone.utc).isoformat()

        self.conn.execute("""
            INSERT INTO snapshots
            (aggregate_id, aggregate_type, snapshot_version, snapshot_data, snapshot_timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, [
            snapshot.aggregate_id,
            snapshot.aggregate_type,
            snapshot.snapshot_version,
            json.dumps(snapshot.snapshot_data),
            snapshot.snapshot_timestamp
        ])

        logger.info(f"📸 Snapshot saved for {snapshot.aggregate_type}:{snapshot.aggregate_id} at version {snapshot.snapshot_version}")

    def get_latest_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """Get the latest snapshot for an aggregate"""
        result = self.conn.execute("""
            SELECT * FROM snapshots
            WHERE aggregate_id = ?
            ORDER BY snapshot_version DESC
            LIMIT 1
        """, [aggregate_id]).fetchone()

        if result:
            return Snapshot(
                aggregate_id=result[0],
                aggregate_type=result[1],
                snapshot_version=result[2],
                snapshot_data=json.loads(result[3]),
                snapshot_timestamp=result[4]
            )
        return None

    def register_projection(self, name: str, projection_func: Callable):
        """Register a projection function"""
        self.projections[name] = projection_func
        logger.info(f"📊 Registered projection: {name}")

    def register_event_handler(self, handler: Callable):
        """Register an event handler"""
        self.event_handlers.append(handler)
        logger.info(f"🎯 Registered event handler")

    def get_projection(self, name: str, key: str) -> Optional[Dict[str, Any]]:
        """Get projection data"""
        result = self.conn.execute("""
            SELECT projection_data FROM projections
            WHERE projection_name = ? AND projection_key = ?
        """, [name, key]).fetchone()

        if result:
            return json.loads(result[0])
        return None

# FastAPI Application
app = FastAPI(title="DBBasic Event Store")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize event store
event_store = EventStore()

# WebSocket connections
websocket_connections: List[WebSocket] = []

# API Endpoints
@app.post("/events")
async def append_event(event: Event):
    """Append an event to the event store"""
    try:
        sequence_number = event_store.append_event(event)

        # Broadcast to WebSocket clients
        await broadcast_event(event)

        return {
            "status": "success",
            "sequence_number": sequence_number,
            "event_id": event.event_id
        }
    except Exception as e:
        logger.error(f"Error appending event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/events/query")
async def query_events(query: EventQuery):
    """Query events from the store"""
    try:
        events = event_store.get_events(query)
        return {
            "events": [e.dict() for e in events],
            "count": len(events)
        }
    except Exception as e:
        logger.error(f"Error querying events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/aggregates/{aggregate_id}")
async def get_aggregate(aggregate_id: str):
    """Get all events for an aggregate"""
    try:
        events = event_store.get_aggregate_events(aggregate_id)
        return {
            "aggregate_id": aggregate_id,
            "events": [e.dict() for e in events],
            "version": events[-1].event_version if events else 0
        }
    except Exception as e:
        logger.error(f"Error getting aggregate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/snapshots")
async def save_snapshot(snapshot: Snapshot):
    """Save a snapshot"""
    try:
        event_store.save_snapshot(snapshot)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error saving snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projections/{name}/{key}")
async def get_projection(name: str, key: str):
    """Get projection data"""
    try:
        data = event_store.get_projection(name, key)
        if data:
            return data
        raise HTTPException(status_code=404, detail="Projection not found")
    except Exception as e:
        logger.error(f"Error getting projection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time event streaming"""
    await websocket.accept()
    websocket_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)

async def broadcast_event(event: Event):
    """Broadcast event to all WebSocket clients"""
    for connection in websocket_connections:
        try:
            await connection.send_json(event.dict())
        except:
            websocket_connections.remove(connection)

# Web Interface
@app.get("/", response_class=HTMLResponse)
async def get_interface():
    """Serve the event store web interface"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>DBBasic Event Store</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        h1 { color: white; margin-bottom: 2rem; font-size: 2.5rem; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
        .card { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        h2 { color: #2c3e50; margin-bottom: 1rem; font-size: 1.5rem; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.5rem; color: #555; font-weight: 500; }
        input, select, textarea { width: 100%; padding: 0.75rem; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 1rem; }
        input:focus, select:focus, textarea:focus { border-color: #667eea; outline: none; }
        button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 600; }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .event-list { max-height: 400px; overflow-y: auto; border: 2px solid #e0e0e0; border-radius: 8px; padding: 1rem; background: #f9f9f9; }
        .event-item { padding: 0.75rem; margin-bottom: 0.5rem; background: white; border-radius: 8px; border-left: 4px solid #667eea; }
        .event-header { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
        .event-type { font-weight: 600; color: #2c3e50; }
        .event-time { color: #888; font-size: 0.9rem; }
        .event-data { font-family: 'Courier New', monospace; font-size: 0.9rem; color: #555; background: #f5f5f5; padding: 0.5rem; border-radius: 4px; margin-top: 0.5rem; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 12px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .stat-value { font-size: 2rem; font-weight: bold; color: #667eea; }
        .stat-label { color: #888; margin-top: 0.5rem; }
        .status { padding: 0.25rem 0.5rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
        .status.connected { background: #4CAF50; color: white; }
        .status.disconnected { background: #f44336; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🗄️ DBBasic Event Store <span id="status" class="status disconnected">Disconnected</span></h1>

        <div class="grid">
            <div class="card">
                <h2>📝 Append Event</h2>
                <form id="eventForm">
                    <div class="form-group">
                        <label>Aggregate ID</label>
                        <input type="text" id="aggregateId" placeholder="e.g., user-123" required>
                    </div>
                    <div class="form-group">
                        <label>Aggregate Type</label>
                        <input type="text" id="aggregateType" placeholder="e.g., User" required>
                    </div>
                    <div class="form-group">
                        <label>Event Type</label>
                        <input type="text" id="eventType" placeholder="e.g., UserCreated" required>
                    </div>
                    <div class="form-group">
                        <label>Event Data (JSON)</label>
                        <textarea id="eventData" rows="4" placeholder='{"name": "John Doe", "email": "john@example.com"}' required></textarea>
                    </div>
                    <button type="submit">Append Event</button>
                </form>
            </div>

            <div class="card">
                <h2>📊 Recent Events</h2>
                <div id="eventList" class="event-list">
                    <p style="color: #888;">No events yet...</p>
                </div>
            </div>
        </div>

        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-value" id="totalEvents">0</div>
                <div class="stat-label">Total Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="aggregateCount">0</div>
                <div class="stat-label">Aggregates</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="eventsPerSec">0</div>
                <div class="stat-label">Events/sec</div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let eventCount = 0;
        let aggregates = new Set();
        let eventsInLastSecond = 0;

        function connectWebSocket() {
            ws = new WebSocket('ws://localhost:8007/ws');

            ws.onopen = () => {
                document.getElementById('status').textContent = 'Connected';
                document.getElementById('status').className = 'status connected';
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                addEventToList(data);
                updateStats(data);
            };

            ws.onclose = () => {
                document.getElementById('status').textContent = 'Disconnected';
                document.getElementById('status').className = 'status disconnected';
                setTimeout(connectWebSocket, 3000);
            };
        }

        function addEventToList(event) {
            const list = document.getElementById('eventList');
            if (list.querySelector('p')) {
                list.innerHTML = '';
            }

            const eventItem = document.createElement('div');
            eventItem.className = 'event-item';
            eventItem.innerHTML = `
                <div class="event-header">
                    <span class="event-type">${event.event_type}</span>
                    <span class="event-time">${new Date(event.event_timestamp).toLocaleTimeString()}</span>
                </div>
                <div>Aggregate: ${event.aggregate_type}:${event.aggregate_id}</div>
                <div>Version: ${event.event_version} | Sequence: ${event.sequence_number}</div>
                <div class="event-data">${JSON.stringify(event.event_data, null, 2)}</div>
            `;

            list.insertBefore(eventItem, list.firstChild);

            // Keep only last 10 events
            while (list.children.length > 10) {
                list.removeChild(list.lastChild);
            }
        }

        function updateStats(event) {
            eventCount++;
            aggregates.add(event.aggregate_id);
            eventsInLastSecond++;

            document.getElementById('totalEvents').textContent = eventCount;
            document.getElementById('aggregateCount').textContent = aggregates.size;

            setTimeout(() => {
                eventsInLastSecond--;
                document.getElementById('eventsPerSec').textContent = eventsInLastSecond;
            }, 1000);

            document.getElementById('eventsPerSec').textContent = eventsInLastSecond;
        }

        document.getElementById('eventForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const event = {
                aggregate_id: document.getElementById('aggregateId').value,
                aggregate_type: document.getElementById('aggregateType').value,
                event_type: document.getElementById('eventType').value,
                event_data: JSON.parse(document.getElementById('eventData').value)
            };

            try {
                const response = await fetch('/events', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(event)
                });

                if (response.ok) {
                    document.getElementById('eventForm').reset();
                    document.getElementById('eventData').value = '{}';
                } else {
                    alert('Error appending event');
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });

        // Load initial stats
        async function loadStats() {
            try {
                const response = await fetch('/events/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ limit: 1000 })
                });

                if (response.ok) {
                    const data = await response.json();
                    eventCount = data.count;

                    data.events.forEach(event => {
                        aggregates.add(event.aggregate_id);
                        addEventToList(event);
                    });

                    document.getElementById('totalEvents').textContent = eventCount;
                    document.getElementById('aggregateCount').textContent = aggregates.size;
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        connectWebSocket();
        loadStats();
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    logger.info("🚀 Starting DBBasic Event Store on http://localhost:8007")
    uvicorn.run(app, host="0.0.0.0", port=8007)