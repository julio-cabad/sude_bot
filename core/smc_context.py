#!/usr/bin/env python3
"""
SMC Context Management System
Multi-symbol context management with isolation and dynamic symbol handling
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.config_manager import get_config
from utils.array_ops import get_buffer_manager, CircularBuffer, NumericCircularBuffer
from utils.indicators import get_technical_indicators
from bnb.binance import RobotBinance

logger = logging.getLogger(__name__)


class ContextStatus(Enum):
    """Context status enumeration"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class ContextStats:
    """Statistics for SMC context performance monitoring"""
    symbol: str
    status: ContextStatus
    creation_time: datetime = field(default_factory=datetime.now)
    last_update_time: datetime = field(default_factory=datetime.now)
    total_updates: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    zones_created: int = 0
    swings_detected: int = 0
    pois_calculated: int = 0
    memory_usage_mb: float = 0.0
    processing_time_ms: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class ContextConfig:
    """Configuration for individual SMC context"""
    symbol: str
    timeframe: str = "1h"
    swing_length: int = 10
    history_limit: int = 20
    box_width: float = 2.5
    atr_period: int = 50
    enable_zones: bool = True
    enable_swings: bool = True
    enable_pois: bool = True
    enable_bos: bool = True
    max_memory_mb: float = 10.0
    update_frequency_seconds: int = 60


class SMCContext:
    """
    Individual SMC analysis context for a single symbol
    Provides isolated analysis environment with complete SMC functionality
    """
    
    def __init__(self, symbol: str, config: Optional[ContextConfig] = None):
        self.symbol = symbol.upper()
        self.config = config or ContextConfig(symbol=self.symbol)
        self.global_config = get_config()
        
        # Context state
        self._status = ContextStatus.INITIALIZING
        self._lock = threading.RLock()
        self._stats = ContextStats(symbol=self.symbol, status=self._status)
        
        # Data management
        self.buffer_manager = get_buffer_manager()
        self.indicators = get_technical_indicators()
        self._binance_robot: Optional[RobotBinance] = None
        
        # Buffers for this symbol
        self._price_buffer: Optional[NumericCircularBuffer] = None
        self._zones_buffer: Optional[CircularBuffer] = None
        self._swings_buffer: Optional[CircularBuffer] = None
        self._pois_buffer: Optional[CircularBuffer] = None
        self._bos_buffer: Optional[CircularBuffer] = None
        
        # Analysis components (will be initialized later)
        self._swing_detector = None
        self._zone_manager = None
        self._poi_calculator = None
        self._bos_handler = None
        
        # Event callbacks
        self._event_callbacks: Dict[str, List[Callable]] = {
            'zone_created': [],
            'swing_detected': [],
            'poi_calculated': [],
            'bos_detected': [],
            'error_occurred': []
        }
        
        logger.info(f"🎯 SMCContext created for {self.symbol}")
    
    def initialize(self) -> bool:
        """
        Initialize the SMC context with all components
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            with self._lock:
                logger.info(f"🔧 Initializing SMC context for {self.symbol}...")
                
                # Initialize Binance connection
                self._binance_robot = RobotBinance(self.symbol, self.config.timeframe)
                
                # Initialize buffers
                self._initialize_buffers()
                
                # Load initial data
                if not self._load_initial_data():
                    logger.error(f"❌ Failed to load initial data for {self.symbol}")
                    return False
                
                # Initialize analysis components
                self._initialize_components()
                
                # Update status
                self._status = ContextStatus.ACTIVE
                self._stats.status = self._status
                self._stats.last_update_time = datetime.now()
                
                logger.info(f"✅ SMC context initialized for {self.symbol}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize context for {self.symbol}: {e}")
            self._status = ContextStatus.ERROR
            self._stats.status = self._status
            self._stats.error_count += 1
            self._stats.last_error = str(e)
            return False
    
    def _initialize_buffers(self) -> None:
        """Initialize circular buffers for this symbol"""
        # Price buffer for OHLCV data
        self._price_buffer = self.buffer_manager.get_prices_buffer(
            self.symbol, size=max(100, self.config.atr_period * 2)
        )
        
        # SMC component buffers
        if self.config.enable_zones:
            self._zones_buffer = self.buffer_manager.get_zones_buffer(
                self.symbol, size=self.config.history_limit
            )
        
        if self.config.enable_swings:
            self._swings_buffer = self.buffer_manager.get_swings_buffer(
                self.symbol, size=self.config.history_limit * 2
            )
        
        if self.config.enable_pois:
            self._pois_buffer = self.buffer_manager.get_pois_buffer(
                self.symbol, size=self.config.history_limit
            )
        
        if self.config.enable_bos:
            self._bos_buffer = self.buffer_manager.get_buffer(
                self.symbol, "bos", size=self.config.history_limit
            )
        
        logger.debug(f"📦 Buffers initialized for {self.symbol}")
    
    def _load_initial_data(self) -> bool:
        """Load initial market data from Binance"""
        try:
            logger.info(f"📡 Loading initial data for {self.symbol}...")
            
            # Get historical data from Binance
            initial_data = self._binance_robot.candlestick(limit=200)
            
            if initial_data.empty:
                logger.error(f"❌ No initial data received for {self.symbol}")
                return False
            
            # Populate price buffer with historical data
            for _, candle in initial_data.iterrows():
                self._price_buffer.add_pop(float(candle['close']))
            
            logger.info(f"✅ Loaded {len(initial_data)} candles for {self.symbol}")
            logger.info(f"   Price range: ${initial_data['low'].min():.2f} - ${initial_data['high'].max():.2f}")
            logger.info(f"   Current price: ${initial_data['close'].iloc[-1]:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load initial data for {self.symbol}: {e}")
            return False
    
    def _initialize_components(self) -> None:
        """Initialize SMC analysis components"""
        # Note: These will be implemented in subsequent tasks
        # For now, we create placeholder components
        
        if self.config.enable_swings:
            # self._swing_detector = SwingDetector(self.symbol, self.config.swing_length)
            logger.debug(f"🔄 Swing detector ready for {self.symbol}")
        
        if self.config.enable_zones:
            # self._zone_manager = ZoneManager(self.symbol, self.config)
            logger.debug(f"🏢 Zone manager ready for {self.symbol}")
        
        if self.config.enable_pois:
            # self._poi_calculator = POICalculator(self.symbol)
            logger.debug(f"🎯 POI calculator ready for {self.symbol}")
        
        if self.config.enable_bos:
            # self._bos_handler = BOSHandler(self.symbol)
            logger.debug(f"💥 BOS handler ready for {self.symbol}")
    
    def update(self, new_candle_data: Optional[pd.Series] = None) -> bool:
        """
        Update context with new market data
        
        Args:
            new_candle_data: Optional new candle data, if None will fetch from Binance
            
        Returns:
            True if update successful, False otherwise
        """
        if self._status != ContextStatus.ACTIVE:
            logger.warning(f"⚠️ Context {self.symbol} not active, skipping update")
            return False
        
        start_time = time.time()
        
        try:
            with self._lock:
                # Get new data
                if new_candle_data is None:
                    # Fetch latest candle from Binance
                    latest_data = self._binance_robot.candlestick(limit=1)
                    if latest_data.empty:
                        logger.warning(f"⚠️ No new data for {self.symbol}")
                        return False
                    new_candle_data = latest_data.iloc[-1]
                
                # Update price buffer
                new_price = float(new_candle_data['close'])
                self._price_buffer.add_pop(new_price)
                
                # Process SMC analysis
                self._process_smc_analysis(new_candle_data)
                
                # Update statistics
                processing_time = (time.time() - start_time) * 1000
                self._update_stats(processing_time, success=True)
                
                logger.debug(f"✅ Updated {self.symbol} in {processing_time:.2f}ms")
                return True
                
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self._update_stats(processing_time, success=False, error=str(e))
            logger.error(f"❌ Failed to update {self.symbol}: {e}")
            return False
    
    def _process_smc_analysis(self, candle_data: pd.Series) -> None:
        """Process SMC analysis for new candle data"""
        try:
            # Get current price data for analysis
            if self._price_buffer.size() < self.config.swing_length * 2:
                logger.debug(f"📊 Insufficient data for analysis: {self._price_buffer.size()} candles")
                return
            
            # Convert buffer to DataFrame for analysis
            price_history = self._price_buffer.to_array()
            
            # Create OHLCV-like structure (simplified for now)
            # In real implementation, we'd maintain full OHLCV data
            current_price = float(candle_data['close'])
            
            # Simulate SMC analysis (will be replaced with real components)
            self._simulate_swing_detection(current_price)
            self._simulate_zone_creation(current_price)
            self._simulate_poi_calculation(current_price)
            self._simulate_bos_detection(current_price)
            
        except Exception as e:
            logger.error(f"❌ SMC analysis failed for {self.symbol}: {e}")
            raise
    
    def _simulate_swing_detection(self, current_price: float) -> None:
        """Simulate swing detection (placeholder)"""
        if not self.config.enable_swings or not self._swings_buffer:
            return
        
        # Simple swing detection simulation
        if self._price_buffer.size() >= 20:
            price_mean = self._price_buffer.mean()
            price_std = self._price_buffer.std()
            
            # Detect potential swing if price deviates significantly
            if abs(current_price - price_mean) > price_std * 1.5:
                swing_type = "high" if current_price > price_mean else "low"
                
                swing_data = {
                    'type': swing_type,
                    'price': current_price,
                    'timestamp': datetime.now(),
                    'strength': self.config.swing_length,
                    'confirmed': True
                }
                
                self._swings_buffer.add_pop(swing_data)
                self._stats.swings_detected += 1
                
                # Trigger callbacks
                self._trigger_event('swing_detected', swing_data)
                
                logger.debug(f"📈 Swing {swing_type} detected for {self.symbol} at ${current_price:.2f}")
    
    def _simulate_zone_creation(self, current_price: float) -> None:
        """Simulate zone creation (placeholder)"""
        if not self.config.enable_zones or not self._zones_buffer:
            return
        
        # Simple zone creation simulation based on swings
        if self._swings_buffer and self._swings_buffer.size() > 0:
            latest_swing = self._swings_buffer.peek(-1)
            
            # Create zone around swing point
            if latest_swing and abs(latest_swing['price'] - current_price) > current_price * 0.01:
                zone_type = "supply" if latest_swing['type'] == "high" else "demand"
                atr_estimate = self._price_buffer.std() if self._price_buffer.size() > 1 else current_price * 0.01
                
                zone_data = {
                    'type': zone_type,
                    'top': latest_swing['price'] + atr_estimate,
                    'bottom': latest_swing['price'] - atr_estimate,
                    'poi': latest_swing['price'],
                    'timestamp': datetime.now(),
                    'atr': atr_estimate,
                    'active': True
                }
                
                self._zones_buffer.add_pop(zone_data)
                self._stats.zones_created += 1
                
                # Trigger callbacks
                self._trigger_event('zone_created', zone_data)
                
                logger.debug(f"🏢 {zone_type.title()} zone created for {self.symbol} at ${latest_swing['price']:.2f}")
    
    def _simulate_poi_calculation(self, current_price: float) -> None:
        """Simulate POI calculation (placeholder)"""
        if not self.config.enable_pois or not self._pois_buffer:
            return
        
        # Simple POI calculation based on zones
        if self._zones_buffer and self._zones_buffer.size() > 0:
            latest_zone = self._zones_buffer.peek(-1)
            
            if latest_zone:
                poi_data = {
                    'price': latest_zone['poi'],
                    'timestamp': datetime.now(),
                    'zone_id': f"zone_{self._zones_buffer.size()}",
                    'type': f"{latest_zone['type']}_poi",
                    'strength': 1.0
                }
                
                self._pois_buffer.add_pop(poi_data)
                self._stats.pois_calculated += 1
                
                # Trigger callbacks
                self._trigger_event('poi_calculated', poi_data)
                
                logger.debug(f"🎯 POI calculated for {self.symbol} at ${poi_data['price']:.2f}")
    
    def _simulate_bos_detection(self, current_price: float) -> None:
        """Simulate BOS detection (placeholder)"""
        if not self.config.enable_bos or not self._bos_buffer:
            return
        
        # Simple BOS detection based on zone breaks
        if self._zones_buffer and self._zones_buffer.size() > 0:
            for zone in self._zones_buffer.to_list():
                if zone['active']:
                    # Check if price breaks zone
                    if (zone['type'] == 'supply' and current_price > zone['top']) or \
                       (zone['type'] == 'demand' and current_price < zone['bottom']):
                        
                        bos_data = {
                            'type': 'bos',
                            'zone_type': zone['type'],
                            'break_price': current_price,
                            'zone_price': zone['poi'],
                            'timestamp': datetime.now(),
                            'strength': 1.0
                        }
                        
                        self._bos_buffer.add_pop(bos_data)
                        zone['active'] = False  # Mark zone as broken
                        
                        # Trigger callbacks
                        self._trigger_event('bos_detected', bos_data)
                        
                        logger.debug(f"💥 BOS detected for {self.symbol}: {zone['type']} broken at ${current_price:.2f}")
    
    def _update_stats(self, processing_time_ms: float, success: bool, error: Optional[str] = None) -> None:
        """Update context statistics"""
        self._stats.total_updates += 1
        self._stats.last_update_time = datetime.now()
        self._stats.processing_time_ms = processing_time_ms
        
        if success:
            self._stats.successful_updates += 1
        else:
            self._stats.failed_updates += 1
            self._stats.error_count += 1
            if error:
                self._stats.last_error = error
    
    def _trigger_event(self, event_type: str, data: Any) -> None:
        """Trigger event callbacks"""
        if event_type in self._event_callbacks:
            for callback in self._event_callbacks[event_type]:
                try:
                    callback(self.symbol, event_type, data)
                except Exception as e:
                    logger.error(f"❌ Event callback error for {self.symbol}: {e}")
    
    def add_event_callback(self, event_type: str, callback: Callable) -> None:
        """Add event callback for specific event type"""
        if event_type in self._event_callbacks:
            self._event_callbacks[event_type].append(callback)
            logger.debug(f"📢 Event callback added for {self.symbol}: {event_type}")
    
    def get_current_data(self) -> Dict[str, Any]:
        """Get current analysis data for this symbol"""
        with self._lock:
            return {
                'symbol': self.symbol,
                'status': self._status.value,
                'current_price': self._price_buffer.peek(-1) if self._price_buffer and self._price_buffer.size() > 0 else None,
                'price_mean': self._price_buffer.mean() if self._price_buffer and self._price_buffer.size() > 0 else None,
                'zones_count': self._zones_buffer.size() if self._zones_buffer else 0,
                'swings_count': self._swings_buffer.size() if self._swings_buffer else 0,
                'pois_count': self._pois_buffer.size() if self._pois_buffer else 0,
                'bos_count': self._bos_buffer.size() if self._bos_buffer else 0,
                'latest_zone': self._zones_buffer.peek(-1) if self._zones_buffer and self._zones_buffer.size() > 0 else None,
                'latest_swing': self._swings_buffer.peek(-1) if self._swings_buffer and self._swings_buffer.size() > 0 else None,
                'stats': self._stats
            }
    
    def pause(self) -> None:
        """Pause context updates"""
        with self._lock:
            if self._status == ContextStatus.ACTIVE:
                self._status = ContextStatus.PAUSED
                self._stats.status = self._status
                logger.info(f"⏸️ Context paused for {self.symbol}")
    
    def resume(self) -> None:
        """Resume context updates"""
        with self._lock:
            if self._status == ContextStatus.PAUSED:
                self._status = ContextStatus.ACTIVE
                self._stats.status = self._status
                logger.info(f"▶️ Context resumed for {self.symbol}")
    
    def stop(self) -> None:
        """Stop context and cleanup resources"""
        with self._lock:
            self._status = ContextStatus.STOPPED
            self._stats.status = self._status
            
            # Cleanup resources
            if self._binance_robot:
                self._binance_robot = None
            
            logger.info(f"🛑 Context stopped for {self.symbol}")
    
    def get_stats(self) -> ContextStats:
        """Get context statistics"""
        with self._lock:
            # Update memory usage
            memory_usage = 0.0
            if self._price_buffer:
                memory_usage += self._price_buffer.get_stats().memory_usage_bytes
            if self._zones_buffer:
                memory_usage += self._zones_buffer.get_stats().memory_usage_bytes
            if self._swings_buffer:
                memory_usage += self._swings_buffer.get_stats().memory_usage_bytes
            if self._pois_buffer:
                memory_usage += self._pois_buffer.get_stats().memory_usage_bytes
            if self._bos_buffer:
                memory_usage += self._bos_buffer.get_stats().memory_usage_bytes
            
            self._stats.memory_usage_mb = memory_usage / (1024 * 1024)
            return self._stats
    
    def __repr__(self) -> str:
        """String representation of context"""
        return f"SMCContext(symbol={self.symbol}, status={self._status.value}, zones={self._zones_buffer.size() if self._zones_buffer else 0})"