#!/usr/bin/env python3
"""
Cache Manager for SMC System
Professional caching strategies for multi-symbol performance optimization
"""

from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, Union, Callable
import hashlib
import pickle
import threading
import time
from functools import wraps
import pandas as pd


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    
    def __post_init__(self):
        """Calculate size if not provided"""
        if self.size_bytes == 0:
            try:
                self.size_bytes = len(pickle.dumps(self.value))
            except:
                self.size_bytes = 1024  # Default estimate


class CacheStrategy(ABC):
    """Abstract base class for cache strategies"""
    
    @abstractmethod
    def should_evict(self, entry: CacheEntry, max_size: int, current_size: int) -> bool:
        """Determine if entry should be evicted"""
        pass
    
    @abstractmethod
    def get_eviction_priority(self, entry: CacheEntry) -> float:
        """Get eviction priority (higher = evict first)"""
        pass


class LRUStrategy(CacheStrategy):
    """Least Recently Used cache strategy"""
    
    def should_evict(self, entry: CacheEntry, max_size: int, current_size: int) -> bool:
        return current_size > max_size
    
    def get_eviction_priority(self, entry: CacheEntry) -> float:
        # Older last_accessed = higher priority for eviction
        return (datetime.now() - entry.last_accessed).total_seconds()


class TTLStrategy(CacheStrategy):
    """Time To Live cache strategy"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
    
    def should_evict(self, entry: CacheEntry, max_size: int, current_size: int) -> bool:
        age = (datetime.now() - entry.created_at).total_seconds()
        return age > self.ttl_seconds or current_size > max_size
    
    def get_eviction_priority(self, entry: CacheEntry) -> float:
        age = (datetime.now() - entry.created_at).total_seconds()
        return age  # Older entries have higher priority


class SMCCacheManager:
    """
    Professional cache manager for SMC system with multiple strategies
    Optimized for multi-symbol trading data caching
    """
    
    def __init__(
        self,
        max_size_mb: int = 100,
        strategy: CacheStrategy = None,
        enable_stats: bool = True
    ):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.strategy = strategy or LRUStrategy()
        self.enable_stats = enable_stats
        
        # Cache storage
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_size_bytes': 0,
            'entry_count': 0
        }
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _update_stats(self, hit: bool = False, miss: bool = False, eviction: bool = False):
        """Update cache statistics"""
        if not self.enable_stats:
            return
        
        with self._lock:
            if hit:
                self._stats['hits'] += 1
            if miss:
                self._stats['misses'] += 1
            if eviction:
                self._stats['evictions'] += 1
            
            self._stats['total_size_bytes'] = sum(entry.size_bytes for entry in self._cache.values())
            self._stats['entry_count'] = len(self._cache)
    
    def _evict_if_needed(self):
        """Evict entries based on strategy"""
        current_size = sum(entry.size_bytes for entry in self._cache.values())
        
        if current_size <= self.max_size_bytes:
            return
        
        # Get entries sorted by eviction priority
        entries_by_priority = sorted(
            self._cache.items(),
            key=lambda x: self.strategy.get_eviction_priority(x[1]),
            reverse=True
        )
        
        # Evict entries until under limit
        for key, entry in entries_by_priority:
            if current_size <= self.max_size_bytes * 0.8:  # Leave some headroom
                break
            
            if self.strategy.should_evict(entry, self.max_size_bytes, current_size):
                del self._cache[key]
                current_size -= entry.size_bytes
                self._update_stats(eviction=True)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                self._update_stats(hit=True)
                return entry.value
            else:
                self._update_stats(miss=True)
                return None
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache"""
        with self._lock:
            now = datetime.now()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now
            )
            
            self._cache[key] = entry
            self._evict_if_needed()
    
    def invalidate(self, key: str) -> bool:
        """Remove specific key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats = {k: 0 for k in self._stats}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            self._update_stats()
            stats = self._stats.copy()
            
            # Calculate derived metrics
            total_requests = stats['hits'] + stats['misses']
            stats['hit_rate'] = stats['hits'] / total_requests if total_requests > 0 else 0
            stats['size_mb'] = stats['total_size_bytes'] / (1024 * 1024)
            stats['utilization'] = stats['total_size_bytes'] / self.max_size_bytes
            
            return stats


class SMCCacheDecorator:
    """Decorator for caching function results"""
    
    def __init__(
        self,
        cache_manager: SMCCacheManager,
        ttl_seconds: Optional[int] = None,
        key_prefix: str = ""
    ):
        self.cache_manager = cache_manager
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{self.key_prefix}:{func.__name__}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            self.cache_manager.put(cache_key, result)
            
            return result
        
        return wrapper


# Specialized cache managers for SMC components
class IndicatorCacheManager(SMCCacheManager):
    """Specialized cache for technical indicators"""
    
    def cache_atr(self, symbol: str, timeframe: str, period: int, data_hash: str, atr_values: pd.Series):
        """Cache ATR calculation"""
        key = f"atr:{symbol}:{timeframe}:{period}:{data_hash}"
        self.put(key, atr_values)
    
    def get_atr(self, symbol: str, timeframe: str, period: int, data_hash: str) -> Optional[pd.Series]:
        """Get cached ATR calculation"""
        key = f"atr:{symbol}:{timeframe}:{period}:{data_hash}"
        return self.get(key)
    
    def cache_pivots(self, symbol: str, timeframe: str, length: int, data_hash: str, pivots: Dict):
        """Cache pivot calculations"""
        key = f"pivots:{symbol}:{timeframe}:{length}:{data_hash}"
        self.put(key, pivots)
    
    def get_pivots(self, symbol: str, timeframe: str, length: int, data_hash: str) -> Optional[Dict]:
        """Get cached pivot calculations"""
        key = f"pivots:{symbol}:{timeframe}:{length}:{data_hash}"
        return self.get(key)


class ZoneCacheManager(SMCCacheManager):
    """Specialized cache for zone calculations"""
    
    def cache_overlap_check(self, zone_data: str, existing_zones_hash: str, result: bool):
        """Cache zone overlap check result"""
        key = f"overlap:{zone_data}:{existing_zones_hash}"
        self.put(key, result)
    
    def get_overlap_check(self, zone_data: str, existing_zones_hash: str) -> Optional[bool]:
        """Get cached overlap check result"""
        key = f"overlap:{zone_data}:{existing_zones_hash}"
        return self.get(key)


class DataCacheManager(SMCCacheManager):
    """Specialized cache for market data"""
    
    def cache_ohlcv(self, symbol: str, timeframe: str, start_time: str, end_time: str, data: pd.DataFrame):
        """Cache OHLCV data"""
        key = f"ohlcv:{symbol}:{timeframe}:{start_time}:{end_time}"
        self.put(key, data)
    
    def get_ohlcv(self, symbol: str, timeframe: str, start_time: str, end_time: str) -> Optional[pd.DataFrame]:
        """Get cached OHLCV data"""
        key = f"ohlcv:{symbol}:{timeframe}:{start_time}:{end_time}"
        return self.get(key)


# Global cache instances
indicator_cache = IndicatorCacheManager(max_size_mb=50, strategy=LRUStrategy())
zone_cache = ZoneCacheManager(max_size_mb=30, strategy=TTLStrategy(ttl_seconds=300))
data_cache = DataCacheManager(max_size_mb=100, strategy=LRUStrategy())


# Decorator instances for easy use
@SMCCacheDecorator(indicator_cache, key_prefix="indicators")
def cached_atr_calculation(ohlcv_data: pd.DataFrame, period: int) -> pd.Series:
    """Example cached ATR calculation"""
    # This would be implemented in the indicators module
    pass


def get_cache_summary() -> Dict[str, Dict]:
    """Get summary of all cache managers"""
    return {
        'indicator_cache': indicator_cache.get_stats(),
        'zone_cache': zone_cache.get_stats(),
        'data_cache': data_cache.get_stats()
    }


# Example usage and testing
if __name__ == "__main__":
    # Test cache manager
    cache = SMCCacheManager(max_size_mb=1)  # Small cache for testing
    
    # Add some test data
    cache.put("test1", "value1")
    cache.put("test2", "value2")
    cache.put("test3", "value3")
    
    # Test retrieval
    print(f"test1: {cache.get('test1')}")
    print(f"test2: {cache.get('test2')}")
    print(f"nonexistent: {cache.get('nonexistent')}")
    
    # Print stats
    stats = cache.get_stats()
    print(f"\n📊 Cache Statistics:")
    print(f"   Hit Rate: {stats['hit_rate']:.2%}")
    print(f"   Entries: {stats['entry_count']}")
    print(f"   Size: {stats['size_mb']:.2f}MB")
    print(f"   Utilization: {stats['utilization']:.2%}")
    
    # Test cache summary
    print(f"\n📈 All Cache Summary:")
    summary = get_cache_summary()
    for cache_name, cache_stats in summary.items():
        print(f"   {cache_name}: {cache_stats['entry_count']} entries, {cache_stats['size_mb']:.2f}MB")