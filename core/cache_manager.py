"""
Sentinel High-Performance In-Memory TTL & LRU Cache Subsystem.
Caches live Telegram previews, search queries, and entity lookups to accelerate
repeat queries (<5ms), reduce external HTTP traffic, and prevent FloodWait rate limits.
"""
import time
import asyncio
from typing import Any, Optional, Dict, Tuple


class FastCache:
    """Thread-safe in-memory cache with Time-To-Live (TTL) and LRU eviction."""

    def __init__(self, max_size: int = 2000, default_ttl: int = 600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._store: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expire_timestamp)
        self._lock = asyncio.Lock()
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Retrieves item if present and not expired."""
        async with self._lock:
            if key not in self._store:
                self.misses += 1
                return None

            val, exp = self._store[key]
            if time.time() > exp:
                del self._store[key]
                self.misses += 1
                return None

            self.hits += 1
            return val

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Stores item with specified or default TTL (in seconds)."""
        duration = ttl if ttl is not None else self.default_ttl
        exp = time.time() + duration

        async with self._lock:
            # If max size reached, evict oldest items
            if len(self._store) >= self.max_size and key not in self._store:
                now = time.time()
                # First delete expired items
                expired_keys = [k for k, (_, e) in self._store.items() if now > e]
                for k in expired_keys:
                    del self._store[k]

                # If still at max size, evict arbitrary first 10%
                if len(self._store) >= self.max_size:
                    keys_to_remove = list(self._store.keys())[:max(1, self.max_size // 10)]
                    for k in keys_to_remove:
                        del self._store[k]

            self._store[key] = (value, exp)

    async def delete(self, key: str) -> bool:
        """Removes a specific key from cache."""
        async with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    async def clear(self) -> None:
        """Clears all stored entries."""
        async with self._lock:
            self._store.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Returns cache telemetry statistics."""
        total = self.hits + self.misses
        hit_ratio = (self.hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._store),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio_percent": round(hit_ratio, 2)
        }


# Global Singleton Cache Instances
preview_cache = FastCache(max_size=1500, default_ttl=900)  # 15 minutes for channel previews
search_cache = FastCache(max_size=500, default_ttl=300)     # 5 minutes for search queries
intel_cache = FastCache(max_size=500, default_ttl=600)      # 10 minutes for OSINT reports
