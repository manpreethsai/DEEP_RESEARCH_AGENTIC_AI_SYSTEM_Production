"""
Cache management utility for the Deep Research Production System.
Provides in-memory and file-based caching with TTL support.
"""

import time
import json
import hashlib
import logging
from typing import Any, Optional, Dict
from pathlib import Path
import pickle

from ..config.settings import config

logger = logging.getLogger(__name__)


class CacheManager:
    """Cache manager for storing and retrieving cached data."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize cache manager."""
        self.cache_dir = Path(cache_dir) if cache_dir else config.cache_path
        self.cache_dir.mkdir(exist_ok=True)
        
        # In-memory cache
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.max_memory_size = 1000  # Maximum number of items in memory
        
        logger.info(f"Cache manager initialized with directory: {self.cache_dir}")
    
    def _generate_key(self, data: str) -> str:
        """Generate cache key from data."""
        return hashlib.md5(data.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{key}.cache"
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set cache value with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        cache_data = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
        
        # Store in memory
        if len(self.memory_cache) >= self.max_memory_size:
            # Remove oldest item
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]['timestamp'])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = cache_data
        
        # Store on disk
        try:
            cache_path = self._get_cache_path(key)
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            logger.warning(f"Failed to write cache to disk: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        # Check memory cache first
        if key in self.memory_cache:
            cache_data = self.memory_cache[key]
            if time.time() - cache_data['timestamp'] < cache_data['ttl']:
                return cache_data['value']
            else:
                # Expired, remove from memory
                del self.memory_cache[key]
        
        # Check disk cache
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # Check if expired
                if time.time() - cache_data['timestamp'] < cache_data['ttl']:
                    # Add to memory cache
                    if len(self.memory_cache) < self.max_memory_size:
                        self.memory_cache[key] = cache_data
                    return cache_data['value']
                else:
                    # Expired, remove from disk
                    cache_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to read cache from disk: {e}")
        
        return None
    
    def delete(self, key: str) -> None:
        """Delete cache entry."""
        # Remove from memory
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Remove from disk
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
    
    def clear(self) -> None:
        """Clear all cache entries."""
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
        
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        memory_size = len(self.memory_cache)
        disk_size = len(list(self.cache_dir.glob("*.cache")))
        
        return {
            'memory_entries': memory_size,
            'disk_entries': disk_size,
            'total_entries': memory_size + disk_size,
            'max_memory_size': self.max_memory_size
        }
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries. Returns number of cleaned entries."""
        cleaned = 0
        current_time = time.time()
        
        # Clean memory cache
        expired_keys = [
            key for key, data in self.memory_cache.items()
            if current_time - data['timestamp'] >= data['ttl']
        ]
        for key in expired_keys:
            del self.memory_cache[key]
            cleaned += 1
        
        # Clean disk cache
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                if current_time - cache_data['timestamp'] >= cache_data['ttl']:
                    cache_file.unlink()
                    cleaned += 1
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
                cache_file.unlink()  # Remove corrupted file
                cleaned += 1
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired cache entries")
        
        return cleaned


# Global cache manager instance
cache_manager = CacheManager() 