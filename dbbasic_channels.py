#!/usr/bin/env python3
"""
DBBasic Channels - Pub/Sub system for service orchestration
Workers watch channels, pick up jobs, process them, and broadcast results
Built on DuckDB for persistence + async for real-time
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict
import duckdb
from enum import Enum

class Channel(Enum):
    """Standard channels for different job types"""
    ORDERS = "orders"
    SHIPPING = "shipping"
    FRAUD = "fraud"
    NOTIFICATIONS = "notifications"
    ANALYTICS = "analytics"
    CUSTOMER = "customer"
    INVENTORY = "inventory"
    PRICING = "pricing"
    ALL = "*"  # Special channel for monitoring everything

class DBBasicChannels:
    """
    Pub/Sub system with channels for service orchestration.
    - Publishers push jobs to channels
    - Subscribers watch channels and process jobs
    - Results broadcast back to interested listeners
    """

    def __init__(self, db_path: str = "dbbasic_channels.duckdb"):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._init_db()

        # In-memory subscriptions (channel -> list of callbacks)
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)

        # Active watchers (channel -> list of async tasks)
        self.watchers: Dict[str, List[asyncio.Task]] = defaultdict(list)

        # Event for new messages
        self.new_message_event = asyncio.Event()

    def _init_db(self):
        """Initialize channel tables"""

        # Messages table - the main pub/sub queue
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id VARCHAR PRIMARY KEY,
                channel VARCHAR NOT NULL,
                message_type VARCHAR NOT NULL,
                payload JSON,
                status VARCHAR DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                processed_by VARCHAR,
                result JSON,
                error VARCHAR,
                ttl_seconds INTEGER DEFAULT 3600
            )
        """)

        # Channel registry
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                name VARCHAR PRIMARY KEY,
                description VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                last_message_at TIMESTAMP,
                active_subscribers INTEGER DEFAULT 0
            )
        """)

        # Subscribers tracking
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id VARCHAR PRIMARY KEY,
                channel VARCHAR NOT NULL,
                subscriber_name VARCHAR NOT NULL,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                messages_processed INTEGER DEFAULT 0,
                last_seen TIMESTAMP
            )
        """)

        # Create indexes for performance
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_channel_status
            ON messages(channel, status, created_at)
        """)

        # Initialize standard channels
        for channel in Channel:
            if channel != Channel.ALL:
                self.conn.execute("""
                    INSERT OR IGNORE INTO channels (name, description)
                    VALUES (?, ?)
                """, [channel.value, f"Channel for {channel.value} related messages"])

    async def publish(self, channel: str, message_type: str, payload: Dict[str, Any],
                     ttl_seconds: int = 3600) -> str:
        """
        Publish a message to a channel.
        Returns message ID.
        """
        message_id = str(uuid.uuid4())

        self.conn.execute("""
            INSERT INTO messages (id, channel, message_type, payload, ttl_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, [message_id, channel, message_type, json.dumps(payload), ttl_seconds])

        # Update channel stats
        self.conn.execute("""
            UPDATE channels
            SET message_count = message_count + 1,
                last_message_at = CURRENT_TIMESTAMP
            WHERE name = ?
        """, [channel])

        # Notify watchers
        self.new_message_event.set()

        # Trigger in-memory subscribers
        await self._trigger_subscribers(channel, {
            'id': message_id,
            'channel': channel,
            'message_type': message_type,
            'payload': payload,
            'timestamp': datetime.now().isoformat()
        })

        print(f"📤 Published to {channel}: {message_type} (ID: {message_id[:8]}...)")
        return message_id

    async def subscribe(self, channel: str, callback: Callable,
                       subscriber_name: Optional[str] = None) -> str:
        """
        Subscribe to a channel with a callback function.
        Returns subscriber ID.
        """
        subscriber_id = str(uuid.uuid4())
        subscriber_name = subscriber_name or f"subscriber_{subscriber_id[:8]}"

        # Register in database
        self.conn.execute("""
            INSERT INTO subscribers (id, channel, subscriber_name)
            VALUES (?, ?, ?)
        """, [subscriber_id, channel, subscriber_name])

        # Add to in-memory subscribers
        self.subscribers[channel].append(callback)

        # Update channel subscriber count
        self.conn.execute("""
            UPDATE channels
            SET active_subscribers = (
                SELECT COUNT(*) FROM subscribers WHERE channel = ?
            )
            WHERE name = ?
        """, [channel, channel])

        print(f"📥 {subscriber_name} subscribed to {channel}")
        return subscriber_id

    async def watch_channel(self, channel: str, worker_name: str,
                           processor: Optional[Callable] = None):
        """
        Watch a channel and process incoming messages.
        This is for workers that pull and process jobs.
        """
        print(f"👁️ {worker_name} watching channel: {channel}")

        while True:
            try:
                # Get next pending message from channel
                result = self.conn.execute("""
                    UPDATE messages
                    SET status = 'processing',
                        processed_by = ?,
                        processed_at = CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT id FROM messages
                        WHERE channel = ?
                        AND status = 'pending'
                        AND (created_at + INTERVAL '1 second' * ttl_seconds) > CURRENT_TIMESTAMP
                        ORDER BY created_at
                        LIMIT 1
                    )
                    RETURNING *
                """, [worker_name, channel]).fetchone()

                if result:
                    message = {
                        'id': result[0],
                        'channel': result[1],
                        'message_type': result[2],
                        'payload': json.loads(result[3]) if result[3] else {}
                    }

                    # Process the message
                    if processor:
                        try:
                            result_data = await processor(message)

                            # Mark as completed
                            self.conn.execute("""
                                UPDATE messages
                                SET status = 'completed',
                                    result = ?
                                WHERE id = ?
                            """, [json.dumps(result_data) if result_data else None, message['id']])

                            # Update subscriber stats
                            self.conn.execute("""
                                UPDATE subscribers
                                SET messages_processed = messages_processed + 1,
                                    last_seen = CURRENT_TIMESTAMP
                                WHERE subscriber_name = ?
                            """, [worker_name])

                            # Broadcast completion
                            await self._broadcast_completion(channel, message, result_data)

                        except Exception as e:
                            # Mark as failed
                            self.conn.execute("""
                                UPDATE messages
                                SET status = 'failed',
                                    error = ?
                                WHERE id = ?
                            """, [str(e), message['id']])

                            print(f"❌ Error processing {message['id']}: {e}")

                else:
                    # No messages, wait for signal
                    await asyncio.wait_for(
                        self.new_message_event.wait(),
                        timeout=1.0
                    )
                    self.new_message_event.clear()

            except asyncio.TimeoutError:
                # Periodic check even without new message signal
                continue
            except Exception as e:
                print(f"❌ Watcher error: {e}")
                await asyncio.sleep(1)

    async def _trigger_subscribers(self, channel: str, message: Dict):
        """Trigger all in-memory subscribers for a channel"""
        # Direct channel subscribers
        for callback in self.subscribers.get(channel, []):
            try:
                await callback(message)
            except Exception as e:
                print(f"❌ Subscriber error: {e}")

        # Wildcard subscribers (monitoring all channels)
        for callback in self.subscribers.get("*", []):
            try:
                await callback(message)
            except Exception as e:
                print(f"❌ Wildcard subscriber error: {e}")

    async def _broadcast_completion(self, channel: str, message: Dict,
                                  result: Any):
        """Broadcast completion to interested listeners"""
        completion_event = {
            'type': 'completion',
            'channel': channel,
            'message_id': message['id'],
            'message_type': message['message_type'],
            'result': result,
            'timestamp': datetime.now().isoformat()
        }

        await self._trigger_subscribers(channel, completion_event)

    def get_channel_stats(self) -> Dict[str, Any]:
        """Get statistics for all channels"""
        stats = self.conn.execute("""
            SELECT
                c.name,
                c.message_count,
                c.active_subscribers,
                COUNT(m.id) FILTER (WHERE m.status = 'pending') as pending,
                COUNT(m.id) FILTER (WHERE m.status = 'processing') as processing,
                COUNT(m.id) FILTER (WHERE m.status = 'completed') as completed,
                COUNT(m.id) FILTER (WHERE m.status = 'failed') as failed
            FROM channels c
            LEFT JOIN messages m ON c.name = m.channel
            GROUP BY c.name, c.message_count, c.active_subscribers
        """).fetchall()

        return {
            row[0]: {
                'total_messages': row[1],
                'active_subscribers': row[2],
                'pending': row[3] or 0,
                'processing': row[4] or 0,
                'completed': row[5] or 0,
                'failed': row[6] or 0
            }
            for row in stats
        }

    async def cleanup_old_messages(self, max_age_seconds: int = 3600):
        """Clean up old processed messages"""
        deleted = self.conn.execute("""
            DELETE FROM messages
            WHERE status IN ('completed', 'failed')
            AND (created_at + INTERVAL '1 second' * ?) < CURRENT_TIMESTAMP
            RETURNING COUNT(*)
        """, [max_age_seconds]).fetchone()

        if deleted and deleted[0] > 0:
            print(f"🧹 Cleaned up {deleted[0]} old messages")


# Example worker processors for different channels
async def process_order(message: Dict) -> Dict:
    """Process order messages"""
    payload = message['payload']
    # Simulate order processing
    await asyncio.sleep(0.01)
    return {
        'order_id': payload.get('order_id'),
        'status': 'processed',
        'total': payload.get('total', 0) * 1.1  # Add tax
    }

async def process_shipping(message: Dict) -> Dict:
    """Process shipping messages"""
    payload = message['payload']
    # Simulate shipping calculation
    await asyncio.sleep(0.01)
    return {
        'tracking_number': f"TRACK{uuid.uuid4().hex[:8].upper()}",
        'carrier': 'UPS',
        'estimated_days': 3
    }

async def process_fraud(message: Dict) -> Dict:
    """Process fraud detection messages"""
    payload = message['payload']
    # Simulate fraud check
    await asyncio.sleep(0.02)
    risk_score = 25 if payload.get('amount', 0) < 1000 else 75
    return {
        'risk_score': risk_score,
        'action': 'approve' if risk_score < 50 else 'review'
    }


# Demo
async def demo_channels():
    """Demonstrate the channel system"""

    channels = DBBasicChannels()

    print("\n🚀 DBBasic Channels Demo\n")

    # Start workers watching different channels
    print("Starting channel watchers...")

    # Order processor
    asyncio.create_task(
        channels.watch_channel(Channel.ORDERS.value, "OrderWorker-1", process_order)
    )

    # Shipping processor
    asyncio.create_task(
        channels.watch_channel(Channel.SHIPPING.value, "ShippingWorker-1", process_shipping)
    )

    # Fraud processor
    asyncio.create_task(
        channels.watch_channel(Channel.FRAUD.value, "FraudWorker-1", process_fraud)
    )

    # Monitor all channels
    async def monitor_callback(message):
        print(f"📊 Monitor: {message.get('channel')} - {message.get('message_type')}")

    await channels.subscribe("*", monitor_callback, "GlobalMonitor")

    # Give workers time to start
    await asyncio.sleep(1)

    # Publish some messages
    print("\nPublishing messages to channels...")

    # Publish order
    await channels.publish(
        Channel.ORDERS.value,
        "new_order",
        {"order_id": "ORD123", "total": 150.00, "customer_id": "CUST456"}
    )

    # Publish shipping request
    await channels.publish(
        Channel.SHIPPING.value,
        "calculate_shipping",
        {"weight": 2.5, "destination": "90210"}
    )

    # Publish fraud check
    await channels.publish(
        Channel.FRAUD.value,
        "check_transaction",
        {"transaction_id": "TXN789", "amount": 2500.00}
    )

    # Wait for processing
    await asyncio.sleep(2)

    # Show stats
    print("\n📊 Channel Statistics:")
    stats = channels.get_channel_stats()
    for channel, data in stats.items():
        if data['total_messages'] > 0:
            print(f"  {channel}: {data}")

    # Keep running for a bit to show real-time processing
    await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(demo_channels())