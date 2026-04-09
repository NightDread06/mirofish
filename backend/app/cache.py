"""
Simple in-memory cache with TTL support for ski dashboard services.
"""

import time
import threading
from typing import Any, Optional


class TTLCache:
    """Thread-safe in-memory cache with time-to-live expiry."""

    def __init__(self, default_ttl: int = 600):
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if present and not expired, else None."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.time() > entry["expires_at"]:
                del self._store[key]
                return None
            return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value with the given TTL (seconds)."""
        ttl = ttl if ttl is not None else self.default_ttl
        with self._lock:
            self._store[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
            }

    def delete(self, key: str) -> None:
        """Remove a single entry."""
        with self._lock:
            self._store.pop(key, None)

    def clear_expired(self) -> int:
        """Remove all expired entries. Returns the number of entries removed."""
        now = time.time()
        with self._lock:
            expired = [k for k, v in self._store.items() if now > v["expires_at"]]
            for k in expired:
                del self._store[k]
        return len(expired)

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


# Module-level singleton cache instances
weather_cache = TTLCache(default_ttl=600)   # 10-minute TTL
webcam_cache = TTLCache(default_ttl=1800)   # 30-minute TTL
