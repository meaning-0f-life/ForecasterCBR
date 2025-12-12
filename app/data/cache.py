from cachetools import TTLCache
import hashlib
import json
import os
import time
from typing import Any, Optional

class DataCache:
    def __init__(self, maxsize: int = 100, ttl: int = 3600, cache_dir: str = "cache"):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.cache_dir = os.path.join(os.path.dirname(__file__), cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_key(self, key_data: dict) -> str:
        """Generate a cache key from dictionary data."""
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key_data: dict) -> Optional[Any]:
        """Retrieve data from cache with file persistence."""
        key = self._get_key(key_data)

        # First check in-memory cache
        value = self.cache.get(key)
        if value is not None:
            return value

        # Then check file cache
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Check TTL
                if time.time() - data['timestamp'] < self.cache.ttl:
                    # Store in memory cache too
                    self.cache[key] = data['value']
                    return data['value']
                else:
                    # Expired, remove file
                    os.remove(cache_file)
            except (json.JSONDecodeError, KeyError, OSError):
                # Invalid cache file, remove it
                try:
                    os.remove(cache_file)
                except OSError:
                    pass

        return None

    def set(self, key_data: dict, value: Any) -> None:
        """Store data in cache with file persistence."""
        key = self._get_key(key_data)

        # Store in memory cache
        self.cache[key] = value

        # Store in file cache
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        try:
            cache_data = {
                'timestamp': time.time(),
                'value': value
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
        except OSError as e:
            print(f"Warning: Could not save cache to file {cache_file}: {e}")

    def clear(self) -> None:
        """Clear all cached data."""
