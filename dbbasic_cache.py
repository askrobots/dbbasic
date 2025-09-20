#!/usr/bin/env python3
"""
DBBasic Caching System
Configuration-driven multi-layer caching for high performance applications
"""

import json
import time
import hashlib
import pickle
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import redis
import sqlite3
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    MEMORY = "memory"
    REDIS = "redis"
    SQLITE = "sqlite"
    MULTI_LAYER = "multi_layer"

class CachePolicy(Enum):
    LRU = "lru"          # Least Recently Used
    LFU = "lfu"          # Least Frequently Used
    TTL = "ttl"          # Time To Live
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"

@dataclass
class CacheConfig:
    strategy: CacheStrategy
    policy: CachePolicy
    max_size: int = 1000
    ttl_seconds: int = 3600
    redis_url: str = "redis://localhost:6379"
    sqlite_path: str = "cache.db"
    compression: bool = False
    serialization: str = "json"  # json, pickle

@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: Optional[int]
    size_bytes: int

class MemoryCache:
    """In-memory cache with LRU/LFU policies"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.data: Dict[str, CacheEntry] = {}
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.data:
                return None

            entry = self.data[key]

            # Check TTL
            if entry.ttl_seconds and self._is_expired(entry):
                del self.data[key]
                return None

            # Update access statistics
            entry.last_accessed = datetime.now()
            entry.access_count += 1

            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        with self.lock:
            # Serialize value to calculate size
            serialized = self._serialize(value)
            size_bytes = len(serialized)

            # Check if we need to evict entries
            if len(self.data) >= self.config.max_size:
                self._evict()

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                ttl_seconds=ttl_seconds or self.config.ttl_seconds,
                size_bytes=size_bytes
            )

            self.data[key] = entry
            return True

    def delete(self, key: str) -> bool:
        with self.lock:
            if key in self.data:
                del self.data[key]
                return True
            return False

    def clear(self):
        with self.lock:
            self.data.clear()

    def _evict(self):
        """Evict entries based on cache policy"""
        if not self.data:
            return

        if self.config.policy == CachePolicy.LRU:
            # Remove least recently used
            oldest_key = min(self.data.keys(),
                           key=lambda k: self.data[k].last_accessed)
            del self.data[oldest_key]

        elif self.config.policy == CachePolicy.LFU:
            # Remove least frequently used
            least_used_key = min(self.data.keys(),
                               key=lambda k: self.data[k].access_count)
            del self.data[least_used_key]

        elif self.config.policy == CachePolicy.TTL:
            # Remove expired entries first
            now = datetime.now()
            expired_keys = [
                key for key, entry in self.data.items()
                if entry.ttl_seconds and (now - entry.created_at).seconds > entry.ttl_seconds
            ]
            for key in expired_keys:
                del self.data[key]

            # If still over capacity, fall back to LRU
            if len(self.data) >= self.config.max_size:
                self._evict_lru()

    def _is_expired(self, entry: CacheEntry) -> bool:
        if not entry.ttl_seconds:
            return False
        age = (datetime.now() - entry.created_at).seconds
        return age > entry.ttl_seconds

    def _serialize(self, value: Any) -> bytes:
        if self.config.serialization == "pickle":
            return pickle.dumps(value)
        else:
            return json.dumps(value, default=str).encode('utf-8')

class RedisCache:
    """Redis-based distributed cache"""

    def __init__(self, config: CacheConfig):
        self.config = config
        try:
            import redis
            self.client = redis.from_url(config.redis_url)
            self.client.ping()  # Test connection
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None

        try:
            data = self.client.get(key)
            if data is None:
                return None

            return self._deserialize(data)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        if not self.client:
            return False

        try:
            serialized = self._serialize(value)
            ttl = ttl_seconds or self.config.ttl_seconds

            if ttl:
                return self.client.setex(key, ttl, serialized)
            else:
                return self.client.set(key, serialized)
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            return False

    def delete(self, key: str) -> bool:
        if not self.client:
            return False

        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete failed: {e}")
            return False

    def clear(self):
        if self.client:
            try:
                self.client.flushdb()
            except Exception as e:
                logger.error(f"Redis clear failed: {e}")

    def _serialize(self, value: Any) -> bytes:
        if self.config.serialization == "pickle":
            return pickle.dumps(value)
        else:
            return json.dumps(value, default=str).encode('utf-8')

    def _deserialize(self, data: bytes) -> Any:
        if self.config.serialization == "pickle":
            return pickle.loads(data)
        else:
            return json.loads(data.decode('utf-8'))

class SqliteCache:
    """SQLite-based persistent cache"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.db_path = config.sqlite_path
        self._init_database()

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value BLOB,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER,
                ttl_seconds INTEGER,
                size_bytes INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    def get(self, key: str) -> Optional[Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                'SELECT value, created_at, ttl_seconds, access_count FROM cache_entries WHERE key = ?',
                (key,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            value_data, created_at_str, ttl_seconds, access_count = row
            created_at = datetime.fromisoformat(created_at_str)

            # Check TTL
            if ttl_seconds and (datetime.now() - created_at).seconds > ttl_seconds:
                cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                conn.commit()
                return None

            # Update access statistics
            cursor.execute(
                'UPDATE cache_entries SET last_accessed = ?, access_count = ? WHERE key = ?',
                (datetime.now().isoformat(), access_count + 1, key)
            )
            conn.commit()

            return self._deserialize(value_data)

        except Exception as e:
            logger.error(f"SQLite get failed: {e}")
            return None
        finally:
            conn.close()

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            serialized = self._serialize(value)
            size_bytes = len(serialized)
            now = datetime.now().isoformat()
            ttl = ttl_seconds or self.config.ttl_seconds

            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries
                (key, value, created_at, last_accessed, access_count, ttl_seconds, size_bytes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (key, serialized, now, now, 1, ttl, size_bytes))

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"SQLite set failed: {e}")
            return False
        finally:
            conn.close()

    def delete(self, key: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"SQLite delete failed: {e}")
            return False
        finally:
            conn.close()

    def clear(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute('DELETE FROM cache_entries')
            conn.commit()
        except Exception as e:
            logger.error(f"SQLite clear failed: {e}")
        finally:
            conn.close()

    def _serialize(self, value: Any) -> bytes:
        if self.config.serialization == "pickle":
            return pickle.dumps(value)
        else:
            return json.dumps(value, default=str).encode('utf-8')

    def _deserialize(self, data: bytes) -> Any:
        if self.config.serialization == "pickle":
            return pickle.loads(data)
        else:
            return json.loads(data.decode('utf-8'))

class MultiLayerCache:
    """Multi-layer cache combining memory, Redis, and SQLite"""

    def __init__(self, config: CacheConfig):
        self.config = config

        # L1: Memory cache (fastest)
        memory_config = CacheConfig(
            strategy=CacheStrategy.MEMORY,
            policy=config.policy,
            max_size=min(100, config.max_size // 10),  # 10% of total size
            ttl_seconds=config.ttl_seconds
        )
        self.memory_cache = MemoryCache(memory_config)

        # L2: Redis cache (distributed)
        self.redis_cache = RedisCache(config)

        # L3: SQLite cache (persistent)
        self.sqlite_cache = SqliteCache(config)

    def get(self, key: str) -> Optional[Any]:
        # Try L1 (memory) first
        value = self.memory_cache.get(key)
        if value is not None:
            return value

        # Try L2 (Redis)
        value = self.redis_cache.get(key)
        if value is not None:
            # Promote to L1
            self.memory_cache.set(key, value)
            return value

        # Try L3 (SQLite)
        value = self.sqlite_cache.get(key)
        if value is not None:
            # Promote to L1 and L2
            self.memory_cache.set(key, value)
            self.redis_cache.set(key, value)
            return value

        return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        # Write to all layers
        results = [
            self.memory_cache.set(key, value, ttl_seconds),
            self.redis_cache.set(key, value, ttl_seconds),
            self.sqlite_cache.set(key, value, ttl_seconds)
        ]
        return any(results)  # Success if any layer succeeds

    def delete(self, key: str) -> bool:
        # Delete from all layers
        results = [
            self.memory_cache.delete(key),
            self.redis_cache.delete(key),
            self.sqlite_cache.delete(key)
        ]
        return any(results)

    def clear(self):
        self.memory_cache.clear()
        self.redis_cache.clear()
        self.sqlite_cache.clear()

class CacheManager:
    """Main cache manager with configuration-driven setup"""

    def __init__(self):
        self.caches: Dict[str, Union[MemoryCache, RedisCache, SqliteCache, MultiLayerCache]] = {}
        self.default_config = CacheConfig(
            strategy=CacheStrategy.MEMORY,
            policy=CachePolicy.LRU,
            max_size=1000,
            ttl_seconds=3600
        )

    def configure_cache(self, name: str, config: CacheConfig):
        """Configure a named cache instance"""
        if config.strategy == CacheStrategy.MEMORY:
            self.caches[name] = MemoryCache(config)
        elif config.strategy == CacheStrategy.REDIS:
            self.caches[name] = RedisCache(config)
        elif config.strategy == CacheStrategy.SQLITE:
            self.caches[name] = SqliteCache(config)
        elif config.strategy == CacheStrategy.MULTI_LAYER:
            self.caches[name] = MultiLayerCache(config)

        logger.info(f"🗄️ Configured cache '{name}' with strategy {config.strategy.value}")

    def get_cache(self, name: str = "default"):
        """Get a cache instance by name"""
        if name not in self.caches:
            self.configure_cache(name, self.default_config)
        return self.caches[name]

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments"""
        # Create deterministic key from arguments
        key_parts = [prefix]

        # Add positional arguments
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))

        # Add keyword arguments (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (dict, list)):
                key_parts.append(f"{k}:{json.dumps(v, sort_keys=True)}")
            else:
                key_parts.append(f"{k}:{v}")

        # Create hash to ensure key length limits
        key_string = ":".join(key_parts)
        if len(key_string) > 200:  # Most cache systems have key length limits
            key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
            return f"{prefix}:{key_hash}"

        return key_string

# Global cache manager instance
cache_manager = CacheManager()

def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    return cache_manager

# Decorators for easy caching
def cached(cache_name: str = "default", ttl_seconds: Optional[int] = None,
          key_prefix: str = "func"):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_cache_manager()
            cache = manager.get_cache(cache_name)

            # Generate cache key
            key = manager.cache_key(f"{key_prefix}:{func.__name__}", *args, **kwargs)

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result

        return wrapper
    return decorator

def cached_async(cache_name: str = "default", ttl_seconds: Optional[int] = None,
                key_prefix: str = "async_func"):
    """Decorator to cache async function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = get_cache_manager()
            cache = manager.get_cache(cache_name)

            # Generate cache key
            key = manager.cache_key(f"{key_prefix}:{func.__name__}", *args, **kwargs)

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result

        return wrapper
    return decorator

# Example configuration for different cache types
CACHE_CONFIGURATIONS = {
    "crud_queries": CacheConfig(
        strategy=CacheStrategy.MULTI_LAYER,
        policy=CachePolicy.LRU,
        max_size=5000,
        ttl_seconds=1800,  # 30 minutes
        redis_url="redis://localhost:6379/1"
    ),
    "user_sessions": CacheConfig(
        strategy=CacheStrategy.REDIS,
        policy=CachePolicy.TTL,
        ttl_seconds=3600,  # 1 hour
        redis_url="redis://localhost:6379/2"
    ),
    "api_responses": CacheConfig(
        strategy=CacheStrategy.MEMORY,
        policy=CachePolicy.LRU,
        max_size=1000,
        ttl_seconds=300,  # 5 minutes
    ),
    "analytics": CacheConfig(
        strategy=CacheStrategy.SQLITE,
        policy=CachePolicy.TTL,
        ttl_seconds=86400,  # 24 hours
        sqlite_path="analytics_cache.db"
    )
}

if __name__ == "__main__":
    # Example usage
    manager = get_cache_manager()

    # Configure different cache types
    for name, config in CACHE_CONFIGURATIONS.items():
        manager.configure_cache(name, config)

    # Test caching
    cache = manager.get_cache("crud_queries")

    # Set some test data
    cache.set("user:123", {"name": "John", "email": "john@example.com"})
    cache.set("product:456", {"name": "Widget", "price": 19.99})

    # Retrieve data
    user = cache.get("user:123")
    product = cache.get("product:456")

    print(f"User: {user}")
    print(f"Product: {product}")

    # Test decorator
    @cached(cache_name="api_responses", ttl_seconds=60)
    def expensive_calculation(n):
        time.sleep(1)  # Simulate expensive operation
        return n * n

    # First call will be slow
    start = time.time()
    result1 = expensive_calculation(10)
    elapsed1 = time.time() - start

    # Second call will be fast (cached)
    start = time.time()
    result2 = expensive_calculation(10)
    elapsed2 = time.time() - start

    print(f"First call: {result1} (took {elapsed1:.2f}s)")
    print(f"Second call: {result2} (took {elapsed2:.2f}s)")