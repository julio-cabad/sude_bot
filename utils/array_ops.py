#!/usr/bin/env python3
"""
Array Operations Utility with Circular Buffer
High-performance circular buffer implementation for multi-symbol SMC system
Equivalent to Pine Script f_array_add_pop functionality with memory optimization
"""

import numpy as np
import pandas as pd
from typing import Any, List, Optional, Union, Iterator, Tuple, Dict
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
import threading
import logging
from abc import ABC, abstractmethod

from config.config_manager import get_config

logger = logging.getLogger(__name__)


@dataclass
class BufferStats:
    """Statistics for circular buffer performance monitoring"""
    total_operations: int = 0
    add_operations: int = 0
    pop_operations: int = 0
    memory_usage_bytes: int = 0
    max_size: int = 0
    current_size: int = 0
    creation_time: datetime = field(default_factory=datetime.now)
    last_operation_time: datetime = field(default_factory=datetime.now)


class CircularBufferBase(ABC):
    """Abstract base class for circular buffers"""
    
    @abstractmethod
    def add_pop(self, item: Any) -> Optional[Any]:
        """Add item and pop oldest if at capacity"""
        pass
    
    @abstractmethod
    def peek(self, index: int = -1) -> Any:
        """Peek at item without removing it"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all items"""
        pass
    
    @abstractmethod
    def is_full(self) -> bool:
        """Check if buffer is at capacity"""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get current number of items"""
        pass


class CircularBuffer(CircularBufferBase):
    """
    High-performance circular buffer with fixed size
    Equivalent to Pine Script array operations with automatic size management
    """
    
    def __init__(self, maxsize: int, symbol: str = "UNKNOWN", buffer_type: str = "generic"):
        if maxsize <= 0:
            raise ValueError("Buffer size must be positive")
        
        self.maxsize = maxsize
        self.symbol = symbol
        self.buffer_type = buffer_type
        self._data = deque(maxlen=maxsize)
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._stats = BufferStats(max_size=maxsize)
        
        logger.debug(f"🔄 Created CircularBuffer for {symbol} ({buffer_type}): size={maxsize}")
    
    def add_pop(self, item: Any) -> Optional[Any]:
        """
        Add new item and return popped item if buffer was full
        Equivalent to Pine Script f_array_add_pop functionality
        
        Args:
            item: Item to add to buffer
            
        Returns:
            Popped item if buffer was full, None otherwise
        """
        with self._lock:
            popped_item = None
            was_full = len(self._data) >= self.maxsize
            
            if was_full:
                # Buffer is full, will pop oldest item
                popped_item = self._data[0] if self._data else None
                self._stats.pop_operations += 1
            
            # Add new item (deque automatically handles size limit)
            self._data.append(item)
            self._stats.add_operations += 1
            self._stats.total_operations += 1
            self._stats.current_size = len(self._data)
            self._stats.last_operation_time = datetime.now()
            
            return popped_item
    
    def add(self, item: Any) -> None:
        """Add item without returning popped item"""
        self.add_pop(item)
    
    def pop(self) -> Any:
        """Remove and return the most recent item"""
        with self._lock:
            if not self._data:
                raise IndexError("Buffer is empty")
            
            item = self._data.pop()
            self._stats.pop_operations += 1
            self._stats.total_operations += 1
            self._stats.current_size = len(self._data)
            self._stats.last_operation_time = datetime.now()
            
            return item
    
    def popleft(self) -> Any:
        """Remove and return the oldest item"""
        with self._lock:
            if not self._data:
                raise IndexError("Buffer is empty")
            
            item = self._data.popleft()
            self._stats.pop_operations += 1
            self._stats.total_operations += 1
            self._stats.current_size = len(self._data)
            self._stats.last_operation_time = datetime.now()
            
            return item
    
    def peek(self, index: int = -1) -> Any:
        """
        Peek at item without removing it
        
        Args:
            index: Index to peek at (-1 for most recent, 0 for oldest)
            
        Returns:
            Item at specified index
        """
        with self._lock:
            if not self._data:
                raise IndexError("Buffer is empty")
            
            if abs(index) > len(self._data):
                raise IndexError(f"Index {index} out of range for buffer size {len(self._data)}")
            
            return self._data[index]
    
    def peek_range(self, start: int = 0, end: Optional[int] = None) -> List[Any]:
        """Get a range of items without removing them"""
        with self._lock:
            if not self._data:
                return []
            
            if end is None:
                end = len(self._data)
            
            return list(self._data)[start:end]
    
    def to_list(self) -> List[Any]:
        """Convert buffer to list (oldest to newest)"""
        with self._lock:
            return list(self._data)
    
    def to_array(self) -> np.ndarray:
        """Convert buffer to numpy array"""
        with self._lock:
            if not self._data:
                return np.array([])
            
            try:
                return np.array(list(self._data))
            except (ValueError, TypeError) as e:
                logger.warning(f"Cannot convert buffer to numpy array: {e}")
                return np.array(list(self._data), dtype=object)
    
    def to_series(self, index: Optional[pd.Index] = None) -> pd.Series:
        """Convert buffer to pandas Series"""
        with self._lock:
            data = list(self._data)
            if index is not None and len(index) != len(data):
                raise ValueError("Index length must match buffer size")
            
            return pd.Series(data, index=index)
    
    def clear(self) -> None:
        """Clear all items from buffer"""
        with self._lock:
            self._data.clear()
            self._stats.current_size = 0
            self._stats.last_operation_time = datetime.now()
            logger.debug(f"🗑️ Cleared buffer for {self.symbol}")
    
    def is_full(self) -> bool:
        """Check if buffer is at maximum capacity"""
        with self._lock:
            return len(self._data) >= self.maxsize
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        with self._lock:
            return len(self._data) == 0
    
    def size(self) -> int:
        """Get current number of items in buffer"""
        with self._lock:
            return len(self._data)
    
    def capacity(self) -> int:
        """Get maximum capacity of buffer"""
        return self.maxsize
    
    def available_space(self) -> int:
        """Get number of items that can be added before buffer is full"""
        with self._lock:
            return max(0, self.maxsize - len(self._data))
    
    def get_stats(self) -> BufferStats:
        """Get buffer performance statistics"""
        with self._lock:
            stats = BufferStats(
                total_operations=self._stats.total_operations,
                add_operations=self._stats.add_operations,
                pop_operations=self._stats.pop_operations,
                memory_usage_bytes=self._estimate_memory_usage(),
                max_size=self.maxsize,
                current_size=len(self._data),
                creation_time=self._stats.creation_time,
                last_operation_time=self._stats.last_operation_time
            )
            return stats
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes"""
        try:
            import sys
            base_size = sys.getsizeof(self._data)
            items_size = sum(sys.getsizeof(item) for item in self._data)
            return base_size + items_size
        except Exception:
            # Fallback estimation
            return len(self._data) * 64  # Rough estimate: 64 bytes per item
    
    def __len__(self) -> int:
        """Get buffer size"""
        return self.size()
    
    def __iter__(self) -> Iterator[Any]:
        """Iterate over buffer items (oldest to newest)"""
        with self._lock:
            return iter(list(self._data))
    
    def __getitem__(self, index: Union[int, slice]) -> Any:
        """Get item by index or slice"""
        with self._lock:
            return self._data[index]
    
    def __repr__(self) -> str:
        """String representation of buffer"""
        return f"CircularBuffer(symbol={self.symbol}, size={len(self._data)}/{self.maxsize}, type={self.buffer_type})"


class NumericCircularBuffer(CircularBuffer):
    """
    Specialized circular buffer for numeric data with mathematical operations
    Optimized for price data, indicators, and numerical analysis
    """
    
    def __init__(self, maxsize: int, symbol: str = "UNKNOWN", buffer_type: str = "numeric"):
        super().__init__(maxsize, symbol, buffer_type)
        self._sum = 0.0
        self._sum_squares = 0.0
        self._min_value = float('inf')
        self._max_value = float('-inf')
    
    def add_pop(self, item: Union[int, float]) -> Optional[Union[int, float]]:
        """Add numeric item and update statistics"""
        if not isinstance(item, (int, float)) or np.isnan(item):
            raise ValueError(f"Item must be a valid number, got {item}")
        
        with self._lock:
            popped_item = None
            was_full = len(self._data) >= self.maxsize
            
            if was_full and self._data:
                # Update statistics for popped item
                popped_item = self._data[0]
                self._sum -= popped_item
                self._sum_squares -= popped_item ** 2
                
                # Recalculate min/max if necessary
                if popped_item == self._min_value or popped_item == self._max_value:
                    self._recalculate_min_max()
            
            # Add new item
            self._data.append(item)
            self._sum += item
            self._sum_squares += item ** 2
            self._min_value = min(self._min_value, item)
            self._max_value = max(self._max_value, item)
            
            # Update stats
            self._stats.add_operations += 1
            if popped_item is not None:
                self._stats.pop_operations += 1
            self._stats.total_operations += 1
            self._stats.current_size = len(self._data)
            self._stats.last_operation_time = datetime.now()
            
            return popped_item
    
    def _recalculate_min_max(self) -> None:
        """Recalculate min and max values"""
        if not self._data:
            self._min_value = float('inf')
            self._max_value = float('-inf')
        else:
            self._min_value = min(self._data)
            self._max_value = max(self._data)
    
    def mean(self) -> float:
        """Calculate mean of buffer values"""
        with self._lock:
            if not self._data:
                return 0.0
            return self._sum / len(self._data)
    
    def std(self, ddof: int = 1) -> float:
        """Calculate standard deviation of buffer values"""
        with self._lock:
            if len(self._data) <= ddof:
                return 0.0
            
            n = len(self._data)
            variance = (self._sum_squares - (self._sum ** 2) / n) / (n - ddof)
            return np.sqrt(max(0, variance))  # Ensure non-negative
    
    def min(self) -> float:
        """Get minimum value in buffer"""
        with self._lock:
            if not self._data:
                return float('nan')
            return self._min_value
    
    def max(self) -> float:
        """Get maximum value in buffer"""
        with self._lock:
            if not self._data:
                return float('nan')
            return self._max_value
    
    def sum(self) -> float:
        """Get sum of all values in buffer"""
        with self._lock:
            return self._sum
    
    def range(self) -> float:
        """Get range (max - min) of buffer values"""
        with self._lock:
            if not self._data:
                return 0.0
            return self._max_value - self._min_value
    
    def percentile(self, q: float) -> float:
        """Calculate percentile of buffer values"""
        with self._lock:
            if not self._data:
                return float('nan')
            return np.percentile(list(self._data), q)
    
    def clear(self) -> None:
        """Clear buffer and reset statistics"""
        with self._lock:
            super().clear()
            self._sum = 0.0
            self._sum_squares = 0.0
            self._min_value = float('inf')
            self._max_value = float('-inf')


class MultiSymbolBufferManager:
    """
    Manager for multiple circular buffers across different symbols
    Provides centralized buffer management with memory monitoring
    """
    
    def __init__(self, default_size: int = None, enable_monitoring: bool = True):
        self.config = get_config()
        self.default_size = default_size or self.config.max_zones_per_symbol
        self.enable_monitoring = enable_monitoring
        
        self._buffers: Dict[str, Dict[str, CircularBufferBase]] = {}
        self._lock = threading.RLock()
        self._total_memory_limit = self.config.max_memory_mb * 1024 * 1024  # Convert to bytes
        
        logger.info(f"🔧 MultiSymbolBufferManager initialized: default_size={self.default_size}")
    
    def get_buffer(self, symbol: str, buffer_type: str, 
                   size: Optional[int] = None, 
                   numeric: bool = False) -> CircularBufferBase:
        """
        Get or create buffer for symbol and type
        
        Args:
            symbol: Trading symbol
            buffer_type: Type of buffer (zones, swings, pois, etc.)
            size: Buffer size (uses default if None)
            numeric: Whether to use NumericCircularBuffer
            
        Returns:
            CircularBuffer instance
        """
        with self._lock:
            if symbol not in self._buffers:
                self._buffers[symbol] = {}
            
            buffer_key = f"{buffer_type}_{size or self.default_size}"
            
            if buffer_key not in self._buffers[symbol]:
                buffer_size = size or self.default_size
                
                # Check memory limits
                if self.enable_monitoring and not self._check_memory_limit(buffer_size):
                    raise MemoryError(f"Buffer creation would exceed memory limit")
                
                # Create appropriate buffer type
                if numeric:
                    buffer = NumericCircularBuffer(buffer_size, symbol, buffer_type)
                else:
                    buffer = CircularBuffer(buffer_size, symbol, buffer_type)
                
                self._buffers[symbol][buffer_key] = buffer
                logger.debug(f"📦 Created buffer: {symbol}.{buffer_type} (size={buffer_size})")
            
            return self._buffers[symbol][buffer_key]
    
    def get_zones_buffer(self, symbol: str, size: Optional[int] = None) -> CircularBuffer:
        """Get zones buffer for symbol"""
        return self.get_buffer(symbol, "zones", size)
    
    def get_swings_buffer(self, symbol: str, size: Optional[int] = None) -> CircularBuffer:
        """Get swings buffer for symbol"""
        return self.get_buffer(symbol, "swings", size)
    
    def get_pois_buffer(self, symbol: str, size: Optional[int] = None) -> CircularBuffer:
        """Get POIs buffer for symbol"""
        return self.get_buffer(symbol, "pois", size)
    
    def get_prices_buffer(self, symbol: str, size: Optional[int] = None) -> NumericCircularBuffer:
        """Get numeric prices buffer for symbol"""
        return self.get_buffer(symbol, "prices", size, numeric=True)
    
    def remove_symbol(self, symbol: str) -> None:
        """Remove all buffers for a symbol"""
        with self._lock:
            if symbol in self._buffers:
                buffer_count = len(self._buffers[symbol])
                del self._buffers[symbol]
                logger.info(f"🗑️ Removed {buffer_count} buffers for {symbol}")
    
    def clear_all_buffers(self) -> None:
        """Clear all buffers for all symbols"""
        with self._lock:
            total_buffers = sum(len(buffers) for buffers in self._buffers.values())
            for symbol_buffers in self._buffers.values():
                for buffer in symbol_buffers.values():
                    buffer.clear()
            logger.info(f"🗑️ Cleared {total_buffers} buffers")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get detailed memory usage statistics"""
        with self._lock:
            total_memory = 0
            symbol_stats = {}
            
            for symbol, buffers in self._buffers.items():
                symbol_memory = 0
                buffer_stats = {}
                
                for buffer_key, buffer in buffers.items():
                    stats = buffer.get_stats()
                    buffer_memory = stats.memory_usage_bytes
                    symbol_memory += buffer_memory
                    
                    buffer_stats[buffer_key] = {
                        'memory_bytes': buffer_memory,
                        'size': stats.current_size,
                        'capacity': stats.max_size,
                        'operations': stats.total_operations
                    }
                
                total_memory += symbol_memory
                symbol_stats[symbol] = {
                    'total_memory_bytes': symbol_memory,
                    'buffer_count': len(buffers),
                    'buffers': buffer_stats
                }
            
            return {
                'total_memory_bytes': total_memory,
                'total_memory_mb': total_memory / (1024 * 1024),
                'memory_limit_mb': self._total_memory_limit / (1024 * 1024),
                'memory_usage_percent': (total_memory / self._total_memory_limit) * 100,
                'symbol_count': len(self._buffers),
                'total_buffer_count': sum(len(buffers) for buffers in self._buffers.values()),
                'symbols': symbol_stats
            }
    
    def _check_memory_limit(self, new_buffer_size: int) -> bool:
        """Check if creating new buffer would exceed memory limit"""
        if not self.enable_monitoring:
            return True
        
        current_usage = self.get_memory_usage()['total_memory_bytes']
        estimated_new_buffer = new_buffer_size * 64  # Rough estimate
        
        return (current_usage + estimated_new_buffer) < self._total_memory_limit
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all buffers"""
        with self._lock:
            total_operations = 0
            total_add_ops = 0
            total_pop_ops = 0
            
            for buffers in self._buffers.values():
                for buffer in buffers.values():
                    stats = buffer.get_stats()
                    total_operations += stats.total_operations
                    total_add_ops += stats.add_operations
                    total_pop_ops += stats.pop_operations
            
            return {
                'total_operations': total_operations,
                'add_operations': total_add_ops,
                'pop_operations': total_pop_ops,
                'symbols_managed': len(self._buffers),
                'total_buffers': sum(len(buffers) for buffers in self._buffers.values())
            }


# Global buffer manager instance
_buffer_manager = None


def get_buffer_manager() -> MultiSymbolBufferManager:
    """Get global buffer manager instance"""
    global _buffer_manager
    if _buffer_manager is None:
        _buffer_manager = MultiSymbolBufferManager()
    return _buffer_manager


# Convenience functions equivalent to Pine Script array operations
def array_add_pop(buffer: CircularBufferBase, item: Any) -> Optional[Any]:
    """
    Pine Script equivalent: array.add_pop()
    Add item to buffer and return popped item if buffer was full
    """
    return buffer.add_pop(item)


def array_size(buffer: CircularBufferBase) -> int:
    """
    Pine Script equivalent: array.size()
    Get current size of buffer
    """
    return buffer.size()


def array_get(buffer: CircularBufferBase, index: int) -> Any:
    """
    Pine Script equivalent: array.get()
    Get item at index (0 = oldest, -1 = newest)
    """
    return buffer.peek(index)


def array_clear(buffer: CircularBufferBase) -> None:
    """
    Pine Script equivalent: array.clear()
    Clear all items from buffer
    """
    buffer.clear()


def create_buffer(symbol: str, buffer_type: str, size: int, numeric: bool = False) -> CircularBufferBase:
    """
    Create a new circular buffer
    
    Args:
        symbol: Trading symbol
        buffer_type: Type of buffer
        size: Maximum buffer size
        numeric: Whether to create numeric buffer
        
    Returns:
        CircularBuffer instance
    """
    manager = get_buffer_manager()
    return manager.get_buffer(symbol, buffer_type, size, numeric)