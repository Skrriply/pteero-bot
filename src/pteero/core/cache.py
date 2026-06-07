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

    def __init__(self, clean_interval: float = 60.0) -> None:
        """Initializes the class.

        Args:
            clean_interval (optional): Minimum time in seconds between cache cleans. Defaults to 60 seconds.
        """
        self._storage: dict[str, CacheEntry] = {}
        self._clean_interval: float = clean_interval
        self._last_clean: float = time.monotonic()

    def set(self, key: str, data: Any, ttl: int) -> None:
        """Stores a value in the cache with a specified time-to-live.

        Args:
            key: The unique identifier for the item.
            data: The data payload to store.
            ttl: Time-to-live in seconds before the item expires.
        """
        self._clean()
        self._storage[key] = CacheEntry(data=data, expires_at=time.monotonic() + ttl)

    def get(self, key: str) -> Any | None:
        """Retrieves a value from the cache if it exists and hasn't expired.

        Args:
            key: The unique identifier for the cached item.

        Returns:
            The cached data if valid, otherwise `None`.
        """
        self._clean()
        entry = self._storage.get(key)

        if not entry:
            return None

        if time.monotonic() < entry["expires_at"]:
            return entry["data"]

        del self._storage[key]
        return None

    def _clean(self) -> None:
        """Removes all expired keys from storage."""
        current_time = time.monotonic()

        if current_time - self._last_clean >= self._clean_interval:
            expired_keys = [
                key
                for key, entry in self._storage.items()
                if current_time >= entry["expires_at"]
            ]

            for key in expired_keys:
                del self._storage[key]

            self._last_clean = current_time
