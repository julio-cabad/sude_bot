#!/usr/bin/env python3
"""
Swing Detection Core Module with Multi-Symbol Support
Professional swing detection using real Binance OHLCV data with caching and performance optimization
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

from config.config_manager import get_config
from utils.indicators import get_technical_indicators, detect_pivot_highs, detect_pivot_lows
from utils.array_ops import get_buffer_manager, CircularBuffer
from bnb.binance import RobotBinance

logger = logging.getLogger(__name__)


class SwingType(Enum):
    """Swing point types"""
    HIGH = "high"
    LOW = "low"


class SwingLabel(Enum):
    """Swing labels for market structure"""
    HH = "HH"  # Higher High
    HL = "HL"  # Higher Low  
    LH = "LH"  # Lower High
    LL = "LL"  # Lower Low
    UNKNOWN = "UNKNOWN"


@dataclass
class SwingPoint:
    """Swing point data structure"""
    swing_type: SwingType
    price: float
    timestamp: datetime
    bar_index: int
    label: SwingLabel
    strength: int
    confirmed: bool = False
    symbol: str = ""
    timeframe: str = ""
    
    # Additional metadata
    volume: Optional[float] = None
    atr_distance: Optional[float] = None
    previous_swing_distance: Optional[float] = None
    
    def __post_init__(self):
        """Post initialization processing"""
        if isinstance(self.swing_type, str):
            self.swing_type = SwingType(self.swing_type)
        if isinstance(self.label, str):
            self.label = SwingLabel(self.label)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'type': self.swing_type.value,
            'price': self.price,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'bar_index': self.bar_index,
            'label': self.label.value,
            'strength': self.strength,
            'confirmed': self.confirmed,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'volume': self.volume,
            'atr_distance': self.atr_distance,
            'previous_swing_distance': self.previous_swing_distance
        }


@dataclass
class SwingDetectionStats:
    """Statistics for swing detection performance"""
    symbol: str
    total_swings_detected: int = 0
    highs_detected: int = 0
    lows_detected: int = 0
    confirmed_swings: int = 0
    hh_count: int = 0
    hl_count: int = 0
    lh_count: int = 0
    ll_count: int = 0
    avg_detection_time_ms: float = 0.0
    last_detection_time: Optional[datetime] = None
    cache_hits: int = 0
    cache_misses: int = 0


class SwingDetector:
    """
    Professional swing detection module with multi-symbol support
    Uses real Binance OHLCV data with intelligent caching and performance optimization
    """
    
    def __init__(self, symbol: str, swing_length: int = 10, timeframe: str = "1h"):
        self.symbol = symbol.upper()
        self.swing_length = swing_length
        self.timeframe = timeframe
        self.config = get_config()
        
        # Components
        self.indicators = get_technical_indicators()
        self.buffer_manager = get_buffer_manager()
        
        # Buffers for swing history
        self.swing_buffer = self.buffer_manager.get_swings_buffer(
            self.symbol, size=self.config.max_swings_per_symbol
        )
        
        # Price data buffer for analysis
        self.price_buffer = self.buffer_manager.get_prices_buffer(
            self.symbol, size=max(200, self.swing_length * 4)
        )
        
        # Internal state
        self._lock = threading.RLock()
        self._stats = SwingDetectionStats(symbol=self.symbol)
        self._last_ohlcv_data: Optional[pd.DataFrame] = None
        self._cached_swings: Dict[str, List[SwingPoint]] = {}
        
        # Binance connection for real data
        self._binance_robot: Optional[RobotBinance] = None
        
        logger.info(f"🔄 SwingDetector initialized for {self.symbol} (length={swing_length})")
    
    def initialize(self) -> bool:
        """
        Initialize swing detector with real Binance data
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info(f"🔧 Initializing SwingDetector for {self.symbol}...")
            
            # Initialize Binance connection
            self._binance_robot = RobotBinance(self.symbol, self.timeframe)
            
            # Load initial historical data
            if not self._load_initial_data():
                logger.error(f"❌ Failed to load initial data for {self.symbol}")
                return False
            
            # Detect initial swings from historical data
            initial_swings = self._detect_swings_from_current_data()
            
            logger.info(f"✅ SwingDetector initialized for {self.symbol}")
            logger.info(f"   Initial swings detected: {len(initial_swings)}")
            logger.info(f"   Highs: {sum(1 for s in initial_swings if s.swing_type == SwingType.HIGH)}")
            logger.info(f"   Lows: {sum(1 for s in initial_swings if s.swing_type == SwingType.LOW)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize SwingDetector for {self.symbol}: {e}")
            return False
    
    def _load_initial_data(self) -> bool:
        """Load initial OHLCV data from Binance"""
        try:
            logger.info(f"📡 Loading initial OHLCV data for {self.symbol}...")
            
            # Get historical data (enough for swing detection)
            historical_data = self._binance_robot.candlestick(limit=500)
            
            if historical_data.empty:
                logger.error(f"❌ No historical data received for {self.symbol}")
                return False
            
            # Store for swing detection
            self._last_ohlcv_data = historical_data
            
            # Populate price buffer
            for _, candle in historical_data.iterrows():
                self.price_buffer.add_pop(float(candle['close']))
            
            logger.info(f"✅ Loaded {len(historical_data)} candles for {self.symbol}")
            logger.info(f"   Date range: {historical_data.index[0]} to {historical_data.index[-1]}")
            logger.info(f"   Price range: ${historical_data['low'].min():.2f} - ${historical_data['high'].max():.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load initial data for {self.symbol}: {e}")
            return False
    
    def detect_swings(self, ohlcv_data: Optional[pd.DataFrame] = None) -> List[SwingPoint]:
        """
        Detect swing points using real Binance OHLCV data
        
        Args:
            ohlcv_data: Optional OHLCV data, if None will use cached data or fetch new
            
        Returns:
            List of detected swing points
        """
        start_time = time.time()
        
        try:
            with self._lock:
                # Use provided data or get from cache/fetch new
                if ohlcv_data is None:
                    if self._last_ohlcv_data is None:
                        logger.warning(f"⚠️ No OHLCV data available for {self.symbol}")
                        return []
                    ohlcv_data = self._last_ohlcv_data
                else:
                    self._last_ohlcv_data = ohlcv_data
                
                # Detect swings
                swings = self._detect_swings_from_data(ohlcv_data)
                
                # Update statistics
                detection_time = (time.time() - start_time) * 1000
                self._update_stats(swings, detection_time)
                
                logger.debug(f"🔄 Detected {len(swings)} swings for {self.symbol} in {detection_time:.2f}ms")
                
                return swings
                
        except Exception as e:
            logger.error(f"❌ Error detecting swings for {self.symbol}: {e}")
            return []
    
    def _detect_swings_from_current_data(self) -> List[SwingPoint]:
        """Detect swings from currently cached data"""
        if self._last_ohlcv_data is not None:
            return self.detect_swings(self._last_ohlcv_data)
        return []
    
    def _detect_swings_from_data(self, ohlcv_data: pd.DataFrame) -> List[SwingPoint]:
        """
        Core swing detection logic using real OHLCV data
        
        Args:
            ohlcv_data: Real Binance OHLCV DataFrame
            
        Returns:
            List of detected swing points
        """
        try:
            if len(ohlcv_data) < self.swing_length * 2 + 1:
                logger.debug(f"📊 Insufficient data for swing detection: {len(ohlcv_data)} candles")
                return []
            
            # Use technical indicators for pivot detection
            pivot_highs_result = self.indicators.detect_pivot_highs(
                ohlcv_data, self.symbol, self.timeframe, length=self.swing_length
            )
            
            pivot_lows_result = self.indicators.detect_pivot_lows(
                ohlcv_data, self.symbol, self.timeframe, length=self.swing_length
            )
            
            # Convert pivot results to swing points
            swings = []
            
            # Process pivot highs
            pivot_highs = pivot_highs_result.values.dropna()
            for timestamp, price in pivot_highs.items():
                if pd.notna(price):
                    bar_index = ohlcv_data.index.get_loc(timestamp)
                    
                    swing = SwingPoint(
                        swing_type=SwingType.HIGH,
                        price=float(price),
                        timestamp=timestamp if isinstance(timestamp, datetime) else datetime.now(),
                        bar_index=bar_index,
                        label=SwingLabel.UNKNOWN,  # Will be classified later
                        strength=self.swing_length,
                        confirmed=True,
                        symbol=self.symbol,
                        timeframe=self.timeframe,
                        volume=float(ohlcv_data.loc[timestamp, 'volume']) if 'volume' in ohlcv_data.columns else None
                    )
                    
                    swings.append(swing)
            
            # Process pivot lows
            pivot_lows = pivot_lows_result.values.dropna()
            for timestamp, price in pivot_lows.items():
                if pd.notna(price):
                    bar_index = ohlcv_data.index.get_loc(timestamp)
                    
                    swing = SwingPoint(
                        swing_type=SwingType.LOW,
                        price=float(price),
                        timestamp=timestamp if isinstance(timestamp, datetime) else datetime.now(),
                        bar_index=bar_index,
                        label=SwingLabel.UNKNOWN,  # Will be classified later
                        strength=self.swing_length,
                        confirmed=True,
                        symbol=self.symbol,
                        timeframe=self.timeframe,
                        volume=float(ohlcv_data.loc[timestamp, 'volume']) if 'volume' in ohlcv_data.columns else None
                    )
                    
                    swings.append(swing)
            
            # Sort swings by timestamp
            swings.sort(key=lambda x: x.bar_index)
            
            # Classify swing labels (HH, HL, LH, LL)
            classified_swings = self._classify_swing_labels(swings)
            
            # Add additional metadata
            self._add_swing_metadata(classified_swings, ohlcv_data)
            
            # Store in buffer
            for swing in classified_swings:
                self.swing_buffer.add_pop(swing)
            
            return classified_swings
            
        except Exception as e:
            logger.error(f"❌ Error in swing detection logic for {self.symbol}: {e}")
            return []
    
    def _classify_swing_labels(self, swings: List[SwingPoint]) -> List[SwingPoint]:
        """
        Classify swings as HH, HL, LH, LL based on market structure
        
        Args:
            swings: List of unclassified swing points
            
        Returns:
            List of classified swing points
        """
        if len(swings) < 2:
            return swings
        
        # Get existing swings from buffer for context
        existing_swings = []
        if self.swing_buffer.size() > 0:
            existing_swings = [swing for swing in self.swing_buffer.to_list() if isinstance(swing, SwingPoint)]
        
        # Combine existing and new swings for classification
        all_swings = existing_swings + swings
        all_swings.sort(key=lambda x: x.bar_index)
        
        # Classify each new swing
        for i, swing in enumerate(swings):
            # Find position in combined list
            swing_index = next((idx for idx, s in enumerate(all_swings) if s is swing), -1)
            
            if swing_index > 0:
                swing.label = self._determine_swing_label(swing, all_swings, swing_index)
            else:
                swing.label = SwingLabel.UNKNOWN
        
        return swings
    
    def _determine_swing_label(self, current_swing: SwingPoint, all_swings: List[SwingPoint], 
                              current_index: int) -> SwingLabel:
        """
        Determine swing label based on previous swings of the same type
        
        Args:
            current_swing: Current swing to classify
            all_swings: All swings in chronological order
            current_index: Index of current swing in all_swings
            
        Returns:
            Appropriate swing label
        """
        try:
            # Find previous swing of the same type
            previous_same_type = None
            
            for i in range(current_index - 1, -1, -1):
                if all_swings[i].swing_type == current_swing.swing_type:
                    previous_same_type = all_swings[i]
                    break
            
            if previous_same_type is None:
                return SwingLabel.UNKNOWN
            
            # Classify based on price comparison
            if current_swing.swing_type == SwingType.HIGH:
                if current_swing.price > previous_same_type.price:
                    return SwingLabel.HH  # Higher High
                else:
                    return SwingLabel.LH  # Lower High
            
            else:  # SwingType.LOW
                if current_swing.price > previous_same_type.price:
                    return SwingLabel.HL  # Higher Low
                else:
                    return SwingLabel.LL  # Lower Low
                    
        except Exception as e:
            logger.error(f"❌ Error determining swing label: {e}")
            return SwingLabel.UNKNOWN
    
    def _add_swing_metadata(self, swings: List[SwingPoint], ohlcv_data: pd.DataFrame) -> None:
        """Add additional metadata to swing points"""
        try:
            # Calculate ATR for distance measurements
            atr_result = self.indicators.calculate_atr(ohlcv_data, self.symbol, self.timeframe)
            current_atr = atr_result.values.iloc[-1] if len(atr_result.values) > 0 else None
            
            for swing in swings:
                # Add ATR distance
                if current_atr:
                    swing.atr_distance = abs(swing.price - ohlcv_data['close'].iloc[-1]) / current_atr
                
                # Add distance to previous swing
                existing_swings = [s for s in self.swing_buffer.to_list() if isinstance(s, SwingPoint)]
                if existing_swings:
                    last_swing = existing_swings[-1]
                    swing.previous_swing_distance = abs(swing.price - last_swing.price)
                    
        except Exception as e:
            logger.error(f"❌ Error adding swing metadata: {e}")
    
    def update_with_new_candle(self, new_candle_data: Optional[pd.Series] = None) -> List[SwingPoint]:
        """
        Update swing detection with new candle data
        
        Args:
            new_candle_data: New candle data, if None will fetch from Binance
            
        Returns:
            List of newly detected swings
        """
        try:
            # Get new candle data
            if new_candle_data is None:
                # Fetch latest candle from Binance
                latest_data = self._binance_robot.candlestick(limit=1)
                if latest_data.empty:
                    logger.debug(f"📊 No new candle data for {self.symbol}")
                    return []
                new_candle_data = latest_data.iloc[-1]
            
            # Update price buffer
            new_price = float(new_candle_data['close'])
            self.price_buffer.add_pop(new_price)
            
            # Get recent data for swing detection
            recent_data = self._binance_robot.candlestick(limit=self.swing_length * 4)
            
            if recent_data.empty:
                return []
            
            # Detect swings with updated data
            new_swings = self.detect_swings(recent_data)
            
            # Filter for truly new swings (not already detected)
            existing_swing_times = set()
            if self.swing_buffer.size() > 0:
                for swing in self.swing_buffer.to_list():
                    if isinstance(swing, SwingPoint):
                        existing_swing_times.add(swing.timestamp)
            
            truly_new_swings = [
                swing for swing in new_swings 
                if swing.timestamp not in existing_swing_times
            ]
            
            if truly_new_swings:
                logger.info(f"🔄 New swings detected for {self.symbol}: {len(truly_new_swings)}")
                for swing in truly_new_swings:
                    logger.info(f"   {swing.swing_type.value.upper()} {swing.label.value} at ${swing.price:.2f}")
            
            return truly_new_swings
            
        except Exception as e:
            logger.error(f"❌ Error updating swings for {self.symbol}: {e}")
            return []
    
    def get_recent_swings(self, count: int = 10) -> List[SwingPoint]:
        """
        Get recent swing points
        
        Args:
            count: Number of recent swings to return
            
        Returns:
            List of recent swing points
        """
        with self._lock:
            if self.swing_buffer.size() == 0:
                return []
            
            recent_swings = []
            buffer_data = self.swing_buffer.to_list()
            
            # Get last 'count' swings
            for swing_data in buffer_data[-count:]:
                if isinstance(swing_data, SwingPoint):
                    recent_swings.append(swing_data)
                elif isinstance(swing_data, dict):
                    # Convert dict to SwingPoint if needed
                    try:
                        swing = SwingPoint(
                            swing_type=SwingType(swing_data.get('type', 'high')),
                            price=swing_data.get('price', 0.0),
                            timestamp=swing_data.get('timestamp', datetime.now()),
                            bar_index=swing_data.get('bar_index', 0),
                            label=SwingLabel(swing_data.get('label', 'UNKNOWN')),
                            strength=swing_data.get('strength', self.swing_length),
                            confirmed=swing_data.get('confirmed', True),
                            symbol=swing_data.get('symbol', self.symbol),
                            timeframe=swing_data.get('timeframe', self.timeframe)
                        )
                        recent_swings.append(swing)
                    except Exception as e:
                        logger.error(f"❌ Error converting swing data: {e}")
            
            return recent_swings
    
    def get_swing_structure(self) -> Dict[str, Any]:
        """
        Get current market structure based on swings
        
        Returns:
            Dictionary with market structure information
        """
        recent_swings = self.get_recent_swings(count=20)
        
        if len(recent_swings) < 4:
            return {
                'trend': 'UNKNOWN',
                'structure': 'INSUFFICIENT_DATA',
                'last_high': None,
                'last_low': None,
                'swing_count': len(recent_swings)
            }
        
        # Separate highs and lows
        highs = [s for s in recent_swings if s.swing_type == SwingType.HIGH]
        lows = [s for s in recent_swings if s.swing_type == SwingType.LOW]
        
        # Determine trend based on recent swing labels
        recent_labels = [s.label for s in recent_swings[-6:]]  # Last 6 swings
        
        hh_hl_count = sum(1 for label in recent_labels if label in [SwingLabel.HH, SwingLabel.HL])
        ll_lh_count = sum(1 for label in recent_labels if label in [SwingLabel.LL, SwingLabel.LH])
        
        if hh_hl_count > ll_lh_count:
            trend = 'BULLISH'
        elif ll_lh_count > hh_hl_count:
            trend = 'BEARISH'
        else:
            trend = 'SIDEWAYS'
        
        return {
            'trend': trend,
            'structure': 'CLEAR',
            'last_high': highs[-1] if highs else None,
            'last_low': lows[-1] if lows else None,
            'swing_count': len(recent_swings),
            'highs_count': len(highs),
            'lows_count': len(lows),
            'hh_hl_ratio': hh_hl_count / len(recent_labels) if recent_labels else 0,
            'll_lh_ratio': ll_lh_count / len(recent_labels) if recent_labels else 0
        }
    
    def _update_stats(self, swings: List[SwingPoint], detection_time_ms: float) -> None:
        """Update detection statistics"""
        self._stats.total_swings_detected += len(swings)
        self._stats.avg_detection_time_ms = detection_time_ms
        self._stats.last_detection_time = datetime.now()
        
        for swing in swings:
            if swing.swing_type == SwingType.HIGH:
                self._stats.highs_detected += 1
            else:
                self._stats.lows_detected += 1
            
            if swing.confirmed:
                self._stats.confirmed_swings += 1
            
            # Count labels
            if swing.label == SwingLabel.HH:
                self._stats.hh_count += 1
            elif swing.label == SwingLabel.HL:
                self._stats.hl_count += 1
            elif swing.label == SwingLabel.LH:
                self._stats.lh_count += 1
            elif swing.label == SwingLabel.LL:
                self._stats.ll_count += 1
    
    def get_stats(self) -> SwingDetectionStats:
        """Get swing detection statistics"""
        with self._lock:
            return self._stats
    
    def clear_cache(self) -> None:
        """Clear cached swing data"""
        with self._lock:
            self._cached_swings.clear()
            logger.debug(f"🗑️ Swing cache cleared for {self.symbol}")
    
    def __repr__(self) -> str:
        """String representation"""
        return f"SwingDetector(symbol={self.symbol}, length={self.swing_length}, swings={self.swing_buffer.size()})"


# Multi-symbol swing detector manager
class MultiSymbolSwingDetector:
    """
    Manager for multiple swing detectors across different symbols
    """
    
    def __init__(self, symbols: Optional[List[str]] = None):
        self.config = get_config()
        self.symbols = symbols or self.config.symbols
        self._detectors: Dict[str, SwingDetector] = {}
        self._lock = threading.RLock()
        
        logger.info(f"🔄 MultiSymbolSwingDetector initialized for {len(self.symbols)} symbols")
    
    def initialize_all(self) -> bool:
        """Initialize all swing detectors"""
        success_count = 0
        
        for symbol in self.symbols:
            try:
                detector = SwingDetector(
                    symbol=symbol,
                    swing_length=self.config.swing_length,
                    timeframe=self.config.timeframe
                )
                
                if detector.initialize():
                    self._detectors[symbol] = detector
                    success_count += 1
                    logger.info(f"✅ SwingDetector initialized for {symbol}")
                else:
                    logger.error(f"❌ Failed to initialize SwingDetector for {symbol}")
                    
            except Exception as e:
                logger.error(f"❌ Exception initializing SwingDetector for {symbol}: {e}")
        
        logger.info(f"📊 Initialized {success_count}/{len(self.symbols)} swing detectors")
        return success_count > 0
    
    def get_detector(self, symbol: str) -> Optional[SwingDetector]:
        """Get swing detector for specific symbol"""
        return self._detectors.get(symbol.upper())
    
    def update_all(self) -> Dict[str, List[SwingPoint]]:
        """Update all swing detectors"""
        results = {}
        
        for symbol, detector in self._detectors.items():
            try:
                new_swings = detector.update_with_new_candle()
                results[symbol] = new_swings
            except Exception as e:
                logger.error(f"❌ Error updating SwingDetector for {symbol}: {e}")
                results[symbol] = []
        
        return results
    
    def get_all_structures(self) -> Dict[str, Dict[str, Any]]:
        """Get market structure for all symbols"""
        structures = {}
        
        for symbol, detector in self._detectors.items():
            try:
                structures[symbol] = detector.get_swing_structure()
            except Exception as e:
                logger.error(f"❌ Error getting structure for {symbol}: {e}")
                structures[symbol] = {'trend': 'ERROR', 'structure': 'ERROR'}
        
        return structures


# Global multi-symbol detector instance
_multi_swing_detector = None


def get_multi_swing_detector() -> MultiSymbolSwingDetector:
    """Get global multi-symbol swing detector instance"""
    global _multi_swing_detector
    if _multi_swing_detector is None:
        _multi_swing_detector = MultiSymbolSwingDetector()
    return _multi_swing_detector