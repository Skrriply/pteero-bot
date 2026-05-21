import logging
import time
from typing import Any, TypedDict

logger = logging.getLogger(__name__)


class CacheEntry(TypedDict):
    """Represents a single item stored in the cache."""

    data: Any
    expires_at: float


class CacheManager:
    """A lazy in-memory cache manager."""

    def __init__(self) -> None:
        self._storage: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        entry = self._storage.get(key)
        if not entry:
            return None

        if time.monotonic() < entry["expires_at"]:
            return entry["data"]

        del self._storage[key]
        return None

    def set(self, key: str, data: Any, ttl: int) -> None:
        self._storage[key] = CacheEntry(data=data, expires_at=time.monotonic() + ttl)

    def clear(self) -> None:
        self._storage.clear()
