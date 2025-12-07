from cachetools import TTLCache
import hashlib
import json
from typing import Any, Optional

class DataCache:
    def __init__(self, maxsize: int = 100, ttl: int = 3600):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def _get_key(self, key_data: dict) -> str:
        """Generate a cache key from dictionary data."""
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key_data: dict) -> Optional[Any]:
        """Retrieve data from cache."""
        key = self._get_key(key_data)
        return self.cache.get(key)

    def set(self, key_data: dict, value: Any) -> None:
        """Store data in cache."""
        key = self._get_key(key_data)
        self.cache[key] = value

    def clear(self) -> None:
        """Clear all cached data."""
