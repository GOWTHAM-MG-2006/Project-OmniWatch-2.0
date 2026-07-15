"""
OmniWatch 2.0 — NexusStore
Component: Connection Pool Manager
Layer: 4
Phase: 7
Purpose: Thread-safe connection pooling for ClickHouse and Redis with
         min/max sizing, health checks, and pool statistics
Inputs: Database configuration, environment
Outputs: Pooled connections with health checks
Technology: Python, threading, clickhouse_connect, redis
"""

import logging
import os
import threading
import time
from collections import deque
from typing import Any

from config import config

logger = logging.getLogger(__name__)

try:
    import clickhouse_connect
    HAS_CLICKHOUSE = True
except ImportError:
    HAS_CLICKHOUSE = False

try:
    import redis as _redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class _PoolEntry:
    __slots__ = ("conn", "created_at", "last_used", "healthy")

    def __init__(self, conn: Any):
        self.conn = conn
        self.created_at = time.monotonic()
        self.last_used = time.monotonic()
        self.healthy = True


class ClickHousePool:
    """Thread-safe ClickHouse connection pool with min/max sizing."""

    def __init__(self, host: str = config.CLICKHOUSE_HOST, port: int = config.CLICKHOUSE_PORT,
                 min_size: int = 2, max_size: int = 10,
                 connect_timeout: int = 5, idle_timeout: int = config.CH_IDLE_TIMEOUT):
        self._host = host
        self._port = port
        self._min_size = min_size
        self._max_size = max_size
        self._connect_timeout = connect_timeout
        self._idle_timeout = idle_timeout
        self._pool: deque[_PoolEntry] = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._total_created = 0
        self._total_acquired = 0
        self._total_released = 0
        self._total_errors = 0
        self._init_pool()

    def _create_connection(self) -> Any | None:
        if not HAS_CLICKHOUSE:
            return None
        try:
            client = clickhouse_connect.get_client(
                host=self._host,
                port=self._port,
                connect_timeout=self._connect_timeout,
                send_receive_timeout=config.CH_SEND_RECEIVE_TIMEOUT,
            )
            return client
        except Exception as exc:
            logger.error("Failed to create ClickHouse connection: %s", exc)
            self._total_errors += 1
            return None

    def _init_pool(self) -> None:
        with self._lock:
            for _ in range(self._min_size):
                conn = self._create_connection()
                if conn:
                    self._pool.append(_PoolEntry(conn))
                    self._total_created += 1
            logger.info("ClickHouse pool initialized: %d/%d connections",
                        len(self._pool), self._min_size)

    def acquire(self, timeout: float = 5.0) -> Any | None:
        """Acquire a connection from the pool."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                while self._pool:
                    entry = self._pool.popleft()
                    if entry.healthy and (time.monotonic() - entry.last_used) < self._idle_timeout:
                        entry.last_used = time.monotonic()
                        self._total_acquired += 1
                        return entry.conn
                    # Stale or unhealthy — close and discard
                    self._close_conn(entry.conn)
                # Pool empty — create new if under max
                if self._total_created - self._total_released < self._max_size:
                    conn = self._create_connection()
                    if conn:
                        self._total_created += 1
                        self._total_acquired += 1
                        return conn
            time.sleep(0.05)
        logger.warning("ClickHouse pool acquire timed out after %.1fs", timeout)
        return None

    def release(self, conn: Any) -> None:
        """Release a connection back to the pool."""
        with self._lock:
            entry = _PoolEntry(conn)
            entry.last_used = time.monotonic()
            if len(self._pool) < self._max_size:
                self._pool.append(entry)
            else:
                self._close_conn(conn)
            self._total_released += 1

    def health_check(self) -> dict[str, Any]:
        """Run a health check on pooled connections."""
        healthy = 0
        unhealthy = 0
        with self._lock:
            alive: deque[_PoolEntry] = deque()
            for entry in self._pool:
                try:
                    if hasattr(entry.conn, "command"):
                        entry.conn.command("SELECT 1")
                    entry.healthy = True
                    healthy += 1
                    alive.append(entry)
                except Exception:
                    entry.healthy = False
                    unhealthy += 1
                    self._close_conn(entry.conn)
            self._pool = alive
        return {"healthy": healthy, "unhealthy": unhealthy, "pool_size": len(self._pool)}

    def close_all(self) -> int:
        """Close all connections in the pool."""
        count = 0
        with self._lock:
            while self._pool:
                entry = self._pool.popleft()
                self._close_conn(entry.conn)
                count += 1
        return count

    def get_stats(self) -> dict[str, Any]:
        """Return pool statistics."""
        return {
            "pool_size": len(self._pool),
            "min_size": self._min_size,
            "max_size": self._max_size,
            "total_created": self._total_created,
            "total_acquired": self._total_acquired,
            "total_released": self._total_released,
            "total_errors": self._total_errors,
        }

    @staticmethod
    def _close_conn(conn: Any) -> None:
        try:
            if hasattr(conn, "close"):
                conn.close()
        except Exception:
            pass


class RedisPool:
    """Redis connection pool backed by redis-py's built-in pool or a manual deque."""

    def __init__(self, host: str = config.REDIS_HOST, port: int = config.REDIS_PORT,
                 db: int = 0, max_connections: int = 20,
                 password: str | None = None, idle_timeout: int = config.REDIS_IDLE_TIMEOUT):
        self._host = host
        self._port = port
        self._db = db
        self._max_connections = max_connections
        self._password = password
        self._idle_timeout = idle_timeout
        self._native_pool = None
        self._manual_pool: deque[_PoolEntry] = deque(maxlen=max_connections)
        self._lock = threading.Lock()
        self._total_acquired = 0
        self._total_released = 0
        self._total_errors = 0
        self._init_pool()

    def _init_pool(self) -> None:
        if HAS_REDIS:
            try:
                self._native_pool = _redis.ConnectionPool(
                    host=self._host,
                    port=self._port,
                    db=self._db,
                    password=self._password,
                    max_connections=self._max_connections,
                    socket_connect_timeout=config.REDIS_CONNECT_TIMEOUT,
                    socket_timeout=config.REDIS_SOCKET_TIMEOUT,
                )
                logger.info("Redis native pool initialized (max=%d)", self._max_connections)
                return
            except Exception as exc:
                logger.warning("Redis native pool init failed, using manual pool: %s", exc)
        logger.info("Using manual Redis pool (max=%d)", self._max_connections)

    def _create_connection(self) -> Any | None:
        if HAS_REDIS and self._native_pool:
            try:
                return _redis.Redis(connection_pool=self._native_pool)
            except Exception as exc:
                logger.error("Redis connection creation failed: %s", exc)
                self._total_errors += 1
                return None
        return None

    def acquire(self, timeout: float = 3.0) -> Any | None:
        """Acquire a Redis connection."""
        if self._native_pool:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    conn = self._create_connection()
                    if conn:
                        self._total_acquired += 1
                        return conn
                except Exception:
                    pass
                time.sleep(0.05)
            return None

        # Manual pool fallback
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                while self._manual_pool:
                    entry = self._manual_pool.popleft()
                    if (time.monotonic() - entry.last_used) < self._idle_timeout:
                        entry.last_used = time.monotonic()
                        self._total_acquired += 1
                        return entry.conn
                    self._close_conn(entry.conn)
                total_active = self._total_acquired - self._total_released
                if total_active < self._max_connections:
                    self._total_acquired += 1
                    return None  # Caller should create manually
            time.sleep(0.05)
        return None

    def release(self, conn: Any) -> None:
        """Release a Redis connection back to the pool."""
        if self._native_pool:
            try:
                conn.close()
            except Exception:
                pass
            self._total_released += 1
            return
        with self._lock:
            if len(self._manual_pool) < self._max_connections:
                entry = _PoolEntry(conn)
                entry.last_used = time.monotonic()
                self._manual_pool.append(entry)
            else:
                self._close_conn(conn)
            self._total_released += 1

    def health_check(self) -> dict[str, Any]:
        """Ping all pooled connections."""
        if not HAS_REDIS:
            return {"healthy": 0, "unhealthy": 0, "pool_size": 0, "error": "redis not installed"}
        try:
            test_conn = self.acquire(timeout=config.REDIS_HEALTH_TIMEOUT)
            if test_conn:
                result = test_conn.ping()
                self.release(test_conn)
                return {"healthy": 1 if result else 0, "unhealthy": 0, "pool_size": self._max_connections}
        except Exception as exc:
            return {"healthy": 0, "unhealthy": 1, "pool_size": 0, "error": str(exc)}
        return {"healthy": 0, "unhealthy": 0, "pool_size": 0}

    def get_stats(self) -> dict[str, Any]:
        return {
            "pool_size": len(self._manual_pool) if not self._native_pool else self._max_connections,
            "max_connections": self._max_connections,
            "total_acquired": self._total_acquired,
            "total_released": self._total_released,
            "total_errors": self._total_errors,
            "using_native_pool": self._native_pool is not None,
        }

    @staticmethod
    def _close_conn(conn: Any) -> None:
        try:
            if hasattr(conn, "close"):
                conn.close()
        except Exception:
            pass


class ConnectionPoolManager:
    """Top-level manager that owns a ClickHouse pool and a Redis pool."""

    def __init__(self):
        ch_host = config.CLICKHOUSE_HOST
        ch_port = config.CLICKHOUSE_PORT
        redis_host = config.REDIS_HOST
        redis_port = config.REDIS_PORT
        redis_pw = os.getenv("REDIS_PASSWORD") or None

        self._clickhouse_pool = ClickHousePool(host=ch_host, port=ch_port)
        self._redis_pool = RedisPool(host=redis_host, port=redis_port, password=redis_pw)

    @property
    def clickhouse(self) -> ClickHousePool:
        return self._clickhouse_pool

    @property
    def redis(self) -> RedisPool:
        return self._redis_pool

    def health_check(self, pool_type: str = "all") -> dict[str, Any]:
        """Check health of connection pools."""
        results: dict[str, Any] = {}
        if pool_type in ("all", "clickhouse"):
            results["clickhouse"] = self._clickhouse_pool.health_check()
        if pool_type in ("all", "redis"):
            results["redis"] = self._redis_pool.health_check()
        return results

    def get_pool_stats(self) -> dict[str, Any]:
        """Get combined pool statistics."""
        return {
            "clickhouse": self._clickhouse_pool.get_stats(),
            "redis": self._redis_pool.get_stats(),
        }

    def close_all(self) -> dict[str, int]:
        """Close all connections in both pools."""
        return {
            "clickhouse_closed": self._clickhouse_pool.close_all(),
            "redis_closed": 0,
        }
