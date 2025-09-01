#!/usr/bin/env python3
"""
Technical Indicators Utility with Caching
Professional implementation using pandas_ta with real Binance data and LRU caching
"""

import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Dict, List, Optional, Tuple, Union, Any
from functools import lru_cache, wraps
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import hashlib
import json
from threading import Lock
import time

from config.config_manager import get_config

logger = logging.getLogger(__name__)


@dataclass
class PivotPoint:
    """Pivot point data structure"""
    index: int
    price: float
    timestamp: datetime
    pivot_type: str  # 'high' or 'low'
    strength: int  # Number of bars on each side


@dataclass
class IndicatorResult:
    """Container for indicator calculation results"""
    values: Union[pd.Series, pd.DataFrame]
    timestamp: datetime
    symbol: str
    timeframe: str
    cache_key: str


class IndicatorCache:
    """Thread-safe LRU cache for indicator calculations"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = Lock()
    
    def _generate_key(self, symbol: str, timeframe: str, indicator: str, 
                     params: Dict[str, Any], data_hash: str) -> str:
        """Generate cache key from parameters"""
        key_data = {
            'symbol': symbol,
            'timeframe': timeframe,
            'indicator': indicator,
            'params': params,
            'data_hash': data_hash
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired"""
        return time.time() - timestamp > self.ttl_seconds
    
    def _evict_lru(self):
        """Evict least recently used items if cache is full"""
        if len(self._cache) >= self.max_size:
            # Find oldest access time
            oldest_key = min(self._access_times.keys(), 
                           key=lambda k: self._access_times[k])
            del self._cache[oldest_key]
            del self._access_times[oldest_key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if exists and not expired"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not self._is_expired(entry['timestamp']):
                    self._access_times[key] = time.time()
                    return entry['data']
                else:
                    # Remove expired entry
                    del self._cache[key]
                    del self._access_times[key]
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set cached value"""
        with self._lock:
            self._evict_lru()
            self._cache[key] = {
                'data': value,
                'timestamp': time.time()
            }
            self._access_times[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cached values"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            current_time = time.time()
            expired_count = sum(1 for entry in self._cache.values() 
                              if self._is_expired(entry['timestamp']))
            
            return {
                'total_entries': len(self._cache),
                'expired_entries': expired_count,
                'active_entries': len(self._cache) - expired_count,
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds,
                'memory_usage_mb': len(str(self._cache)) / (1024 * 1024)
            }


class TechnicalIndicators:
    """
    Professional Technical Indicators utility with caching
    Uses pandas_ta for calculations with real Binance OHLCV data
    """
    
    def __init__(self, enable_caching: bool = True, cache_size: int = 1000, 
                 cache_ttl: int = 300):
        self.config = get_config()
        self.enable_caching = enable_caching and self.config.enable_caching
        self.cache = IndicatorCache(cache_size, cache_ttl) if self.enable_caching else None
        
        logger.info(f"🔧 TechnicalIndicators initialized with caching: {self.enable_caching}")
    
    def _validate_ohlcv_data(self, data: pd.DataFrame) -> bool:
        """Validate OHLCV data structure and completeness"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        if not isinstance(data, pd.DataFrame):
            logger.error("Data must be a pandas DataFrame")
            return False
        
        if data.empty:
            logger.error("Data cannot be empty")
            return False
        
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False
        
        # Check for NaN values in critical columns
        critical_columns = ['high', 'low', 'close']
        for col in critical_columns:
            if data[col].isna().any():
                logger.warning(f"NaN values found in {col} column")
        
        # Validate price relationships
        invalid_hlc = (data['high'] < data['low']) | (data['close'] > data['high']) | (data['close'] < data['low'])
        if invalid_hlc.any():
            logger.warning(f"Invalid OHLC relationships found in {invalid_hlc.sum()} rows")
        
        return True
    
    def _get_data_hash(self, data: pd.DataFrame) -> str:
        """Generate hash of OHLCV data for caching"""
        # Use last few rows and basic stats for hash to detect data changes
        if len(data) > 10:
            sample_data = data.tail(10)
        else:
            sample_data = data
        
        hash_data = {
            'length': len(data),
            'last_close': float(data['close'].iloc[-1]) if len(data) > 0 else 0,
            'last_timestamp': str(data.index[-1]) if len(data) > 0 else '',
            'checksum': float(sample_data[['open', 'high', 'low', 'close']].sum().sum())
        }
        
        return hashlib.md5(json.dumps(hash_data, sort_keys=True).encode()).hexdigest()
    
    def _get_cached_or_calculate(self, symbol: str, timeframe: str, indicator: str,
                                params: Dict[str, Any], data: pd.DataFrame,
                                calculation_func) -> IndicatorResult:
        """Get cached result or calculate new one"""
        if not self.enable_caching:
            result = calculation_func(data, **params)
            return IndicatorResult(
                values=result,
                timestamp=datetime.now(),
                symbol=symbol,
                timeframe=timeframe,
                cache_key=""
            )
        
        # Generate cache key
        data_hash = self._get_data_hash(data)
        cache_key = self.cache._generate_key(symbol, timeframe, indicator, params, data_hash)
        
        # Try to get from cache
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"📋 Cache hit for {indicator} on {symbol}")
            return cached_result
        
        # Calculate new result
        logger.debug(f"🔄 Calculating {indicator} for {symbol}")
        result = calculation_func(data, **params)
        
        # Cache the result
        indicator_result = IndicatorResult(
            values=result,
            timestamp=datetime.now(),
            symbol=symbol,
            timeframe=timeframe,
            cache_key=cache_key
        )
        
        self.cache.set(cache_key, indicator_result)
        return indicator_result
    
    def calculate_atr(self, data: pd.DataFrame, symbol: str = "UNKNOWN", 
                     timeframe: str = "1h", period: int = 50) -> IndicatorResult:
        """
        Calculate Average True Range using pandas_ta
        
        Args:
            data: OHLCV DataFrame with real Binance data
            symbol: Trading symbol for caching
            timeframe: Timeframe for caching
            period: ATR calculation period
            
        Returns:
            IndicatorResult with ATR values
        """
        if not self._validate_ohlcv_data(data):
            raise ValueError("Invalid OHLCV data provided")
        
        if period <= 0 or period > len(data):
            raise ValueError(f"Invalid ATR period: {period}. Must be > 0 and <= {len(data)}")
        
        def _calculate_atr(df: pd.DataFrame, period: int) -> pd.Series:
            """Internal ATR calculation using pandas_ta"""
            try:
                # Use pandas_ta for ATR calculation
                atr_values = ta.atr(high=df['high'], low=df['low'], close=df['close'], length=period)
                
                if atr_values is None or atr_values.empty:
                    logger.warning("pandas_ta ATR calculation returned empty result")
                    # Fallback manual calculation
                    tr1 = df['high'] - df['low']
                    tr2 = abs(df['high'] - df['close'].shift(1))
                    tr3 = abs(df['low'] - df['close'].shift(1))
                    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                    atr_values = true_range.rolling(window=period).mean()
                
                return atr_values
                
            except Exception as e:
                logger.error(f"Error calculating ATR: {e}")
                raise
        
        params = {'period': period}
        return self._get_cached_or_calculate(
            symbol, timeframe, 'atr', params, data, 
            lambda df, period: _calculate_atr(df, period)
        )
    
    def detect_pivot_highs(self, data: pd.DataFrame, symbol: str = "UNKNOWN",
                          timeframe: str = "1h", length: int = 10) -> IndicatorResult:
        """
        Detect pivot highs in price data
        
        Args:
            data: OHLCV DataFrame with real Binance data
            symbol: Trading symbol for caching
            timeframe: Timeframe for caching
            length: Number of bars on each side for pivot detection
            
        Returns:
            IndicatorResult with pivot high points
        """
        if not self._validate_ohlcv_data(data):
            raise ValueError("Invalid OHLCV data provided")
        
        if length <= 0 or length * 2 + 1 > len(data):
            raise ValueError(f"Invalid pivot length: {length}")
        
        def _detect_pivot_highs(df: pd.DataFrame, length: int) -> pd.Series:
            """Internal pivot high detection"""
            try:
                high_series = df['high'].copy()
                pivot_highs = pd.Series(index=df.index, dtype=float)
                
                for i in range(length, len(high_series) - length):
                    current_high = high_series.iloc[i]
                    
                    # Check if current high is higher than surrounding bars
                    left_side = high_series.iloc[i-length:i]
                    right_side = high_series.iloc[i+1:i+length+1]
                    
                    if (current_high > left_side.max()) and (current_high > right_side.max()):
                        pivot_highs.iloc[i] = current_high
                
                return pivot_highs
                
            except Exception as e:
                logger.error(f"Error detecting pivot highs: {e}")
                raise
        
        params = {'length': length}
        return self._get_cached_or_calculate(
            symbol, timeframe, 'pivot_highs', params, data,
            lambda df, length: _detect_pivot_highs(df, length)
        )
    
    def detect_pivot_lows(self, data: pd.DataFrame, symbol: str = "UNKNOWN",
                         timeframe: str = "1h", length: int = 10) -> IndicatorResult:
        """
        Detect pivot lows in price data
        
        Args:
            data: OHLCV DataFrame with real Binance data
            symbol: Trading symbol for caching
            timeframe: Timeframe for caching
            length: Number of bars on each side for pivot detection
            
        Returns:
            IndicatorResult with pivot low points
        """
        if not self._validate_ohlcv_data(data):
            raise ValueError("Invalid OHLCV data provided")
        
        if length <= 0 or length * 2 + 1 > len(data):
            raise ValueError(f"Invalid pivot length: {length}")
        
        def _detect_pivot_lows(df: pd.DataFrame, length: int) -> pd.Series:
            """Internal pivot low detection"""
            try:
                low_series = df['low'].copy()
                pivot_lows = pd.Series(index=df.index, dtype=float)
                
                for i in range(length, len(low_series) - length):
                    current_low = low_series.iloc[i]
                    
                    # Check if current low is lower than surrounding bars
                    left_side = low_series.iloc[i-length:i]
                    right_side = low_series.iloc[i+1:i+length+1]
                    
                    if (current_low < left_side.min()) and (current_low < right_side.min()):
                        pivot_lows.iloc[i] = current_low
                
                return pivot_lows
                
            except Exception as e:
                logger.error(f"Error detecting pivot lows: {e}")
                raise
        
        params = {'length': length}
        return self._get_cached_or_calculate(
            symbol, timeframe, 'pivot_lows', params, data,
            lambda df, length: _detect_pivot_lows(df, length)
        )
    
    def get_pivot_points(self, data: pd.DataFrame, symbol: str = "UNKNOWN",
                        timeframe: str = "1h", length: int = 10) -> List[PivotPoint]:
        """
        Get structured pivot points (both highs and lows)
        
        Args:
            data: OHLCV DataFrame with real Binance data
            symbol: Trading symbol
            timeframe: Timeframe
            length: Pivot detection length
            
        Returns:
            List of PivotPoint objects
        """
        pivot_highs = self.detect_pivot_highs(data, symbol, timeframe, length)
        pivot_lows = self.detect_pivot_lows(data, symbol, timeframe, length)
        
        pivot_points = []
        
        # Process pivot highs
        for idx, price in pivot_highs.values.dropna().items():
            if pd.notna(price):
                pivot_points.append(PivotPoint(
                    index=data.index.get_loc(idx),
                    price=float(price),
                    timestamp=idx if isinstance(idx, datetime) else datetime.now(),
                    pivot_type='high',
                    strength=length
                ))
        
        # Process pivot lows
        for idx, price in pivot_lows.values.dropna().items():
            if pd.notna(price):
                pivot_points.append(PivotPoint(
                    index=data.index.get_loc(idx),
                    price=float(price),
                    timestamp=idx if isinstance(idx, datetime) else datetime.now(),
                    pivot_type='low',
                    strength=length
                ))
        
        # Sort by index
        pivot_points.sort(key=lambda x: x.index)
        
        return pivot_points
    
    def calculate_rsi(self, data: pd.DataFrame, symbol: str = "UNKNOWN",
                     timeframe: str = "1h", period: int = 14) -> IndicatorResult:
        """
        Calculate RSI using pandas_ta
        
        Args:
            data: OHLCV DataFrame
            symbol: Trading symbol
            timeframe: Timeframe
            period: RSI period
            
        Returns:
            IndicatorResult with RSI values
        """
        if not self._validate_ohlcv_data(data):
            raise ValueError("Invalid OHLCV data provided")
        
        def _calculate_rsi(df: pd.DataFrame, period: int) -> pd.Series:
            """Internal RSI calculation"""
            try:
                rsi_values = ta.rsi(close=df['close'], length=period)
                if rsi_values is None:
                    raise ValueError("RSI calculation failed")
                return rsi_values
            except Exception as e:
                logger.error(f"Error calculating RSI: {e}")
                raise
        
        params = {'period': period}
        return self._get_cached_or_calculate(
            symbol, timeframe, 'rsi', params, data,
            lambda df, period: _calculate_rsi(df, period)
        )
    
    def calculate_ema(self, data: pd.DataFrame, symbol: str = "UNKNOWN",
                     timeframe: str = "1h", period: int = 20) -> IndicatorResult:
        """
        Calculate EMA using pandas_ta
        
        Args:
            data: OHLCV DataFrame
            symbol: Trading symbol
            timeframe: Timeframe
            period: EMA period
            
        Returns:
            IndicatorResult with EMA values
        """
        if not self._validate_ohlcv_data(data):
            raise ValueError("Invalid OHLCV data provided")
        
        def _calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
            """Internal EMA calculation"""
            try:
                ema_values = ta.ema(close=df['close'], length=period)
                if ema_values is None:
                    raise ValueError("EMA calculation failed")
                return ema_values
            except Exception as e:
                logger.error(f"Error calculating EMA: {e}")
                raise
        
        params = {'period': period}
        return self._get_cached_or_calculate(
            symbol, timeframe, 'ema', params, data,
            lambda df, period: _calculate_ema(df, period)
        )
    
    def safe_divide(self, numerator: Union[float, pd.Series], 
                   denominator: Union[float, pd.Series], 
                   default: float = 0.0) -> Union[float, pd.Series]:
        """
        Safe division with zero handling
        
        Args:
            numerator: Numerator value(s)
            denominator: Denominator value(s)
            default: Default value when division by zero
            
        Returns:
            Division result with safe zero handling
        """
        epsilon = 1e-10
        
        if isinstance(denominator, pd.Series):
            # Handle pandas Series
            result = numerator / (denominator + epsilon)
            result = result.fillna(default)
            return result
        else:
            # Handle scalar values
            if abs(denominator) < epsilon:
                return default
            return numerator / denominator
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        if not self.enable_caching or not self.cache:
            return {'caching_enabled': False}
        
        stats = self.cache.get_stats()
        stats['caching_enabled'] = True
        return stats
    
    def clear_cache(self) -> None:
        """Clear all cached indicators"""
        if self.enable_caching and self.cache:
            self.cache.clear()
            logger.info("🗑️ Indicator cache cleared")
    
    def batch_calculate_indicators(self, data: pd.DataFrame, symbol: str,
                                  timeframe: str, indicators: List[str],
                                  params: Dict[str, Dict[str, Any]] = None) -> Dict[str, IndicatorResult]:
        """
        Calculate multiple indicators in batch for efficiency
        
        Args:
            data: OHLCV DataFrame
            symbol: Trading symbol
            timeframe: Timeframe
            indicators: List of indicator names to calculate
            params: Parameters for each indicator
            
        Returns:
            Dictionary of indicator results
        """
        if params is None:
            params = {}
        
        results = {}
        
        for indicator in indicators:
            try:
                indicator_params = params.get(indicator, {})
                
                if indicator == 'atr':
                    period = indicator_params.get('period', self.config.atr_period)
                    results[indicator] = self.calculate_atr(data, symbol, timeframe, period)
                
                elif indicator == 'pivot_highs':
                    length = indicator_params.get('length', self.config.swing_length)
                    results[indicator] = self.detect_pivot_highs(data, symbol, timeframe, length)
                
                elif indicator == 'pivot_lows':
                    length = indicator_params.get('length', self.config.swing_length)
                    results[indicator] = self.detect_pivot_lows(data, symbol, timeframe, length)
                
                elif indicator == 'rsi':
                    period = indicator_params.get('period', 14)
                    results[indicator] = self.calculate_rsi(data, symbol, timeframe, period)
                
                elif indicator == 'ema':
                    period = indicator_params.get('period', 20)
                    results[indicator] = self.calculate_ema(data, symbol, timeframe, period)
                
                else:
                    logger.warning(f"Unknown indicator: {indicator}")
                    
            except Exception as e:
                logger.error(f"Error calculating {indicator} for {symbol}: {e}")
                continue
        
        return results


# Global instance for easy access
_technical_indicators = None


def get_technical_indicators() -> TechnicalIndicators:
    """Get global TechnicalIndicators instance"""
    global _technical_indicators
    if _technical_indicators is None:
        config = get_config()
        _technical_indicators = TechnicalIndicators(
            enable_caching=config.enable_caching,
            cache_size=config.cache_size_mb * 10,  # Approximate entries per MB
            cache_ttl=config.cache_ttl_seconds
        )
    return _technical_indicators


# Convenience functions for direct access
def calculate_atr(data: pd.DataFrame, symbol: str = "UNKNOWN", 
                 timeframe: str = "1h", period: int = None) -> IndicatorResult:
    """Convenience function for ATR calculation"""
    indicators = get_technical_indicators()
    if period is None:
        period = indicators.config.atr_period
    return indicators.calculate_atr(data, symbol, timeframe, period)


def detect_pivot_highs(data: pd.DataFrame, symbol: str = "UNKNOWN",
                      timeframe: str = "1h", length: int = None) -> IndicatorResult:
    """Convenience function for pivot high detection"""
    indicators = get_technical_indicators()
    if length is None:
        length = indicators.config.swing_length
    return indicators.detect_pivot_highs(data, symbol, timeframe, length)


def detect_pivot_lows(data: pd.DataFrame, symbol: str = "UNKNOWN",
                     timeframe: str = "1h", length: int = None) -> IndicatorResult:
    """Convenience function for pivot low detection"""
    indicators = get_technical_indicators()
    if length is None:
        length = indicators.config.swing_length
    return indicators.detect_pivot_lows(data, symbol, timeframe, length)