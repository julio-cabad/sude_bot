#!/usr/bin/env python3
"""
Zone Manager Core Module
Professional supply/demand zone creation and management with multi-symbol support
Equivalent to Pine Script f_supply_demand with enhanced performance and real Binance data
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
from threading import Lock
from collections import defaultdict
import uuid

from models.zone import Zone, ZoneType
from models.swing import Swing, SwingType
from config.config_manager import get_config
from utils.overlap_checker import get_overlap_checker, OverlapChecker
from utils.indicators import get_technical_indicators
from utils.array_ops import get_buffer_manager

logger = logging.getLogger(__name__)


class ZoneStatus(Enum):
    """Zone status enumeration"""
    ACTIVE = "active"
    BROKEN = "broken"
    EXPIRED = "expired"
    PENDING = "pending"


class ZoneStrength(Enum):
    """Zone strength based on swing strength and volume"""
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class ZoneCreationConfig:
    """Configuration for zone creation"""
    atr_multiplier: float = 2.0
    min_zone_height: float = 0.001  # Minimum zone height as percentage
    max_zone_height: float = 0.05   # Maximum zone height as percentage
    enable_overlap_check: bool = True
    overlap_resolution: str = "keep_strongest"  # keep_strongest, keep_newest, merge
    min_swing_strength: str = "medium"
    require_volume_confirmation: bool = True
    volume_threshold_multiplier: float = 1.2


@dataclass
class ZoneStats:
    """Statistics for zone management"""
    total_zones_created: int = 0
    supply_zones_created: int = 0
    demand_zones_created: int = 0
    zones_broken: int = 0
    zones_expired: int = 0
    active_zones: int = 0
    avg_zone_lifetime_hours: float = 0.0
    avg_creation_time_ms: float = 0.0
    last_zone_created: datetime = field(default_factory=datetime.now)
    overlap_rejections: int = 0
    strength_rejections: int = 0


class ZoneManager:
    """
    Professional zone manager for supply/demand zone creation and management
    Handles multi-symbol operation with performance optimization and real market data
    """
    
    def __init__(self, symbol: str, config: Optional[ZoneCreationConfig] = None):
        self.symbol = symbol.upper()
        self.config = config or ZoneCreationConfig()
        self.global_config = get_config()
        
        # Thread safety
        self._lock = Lock()
        self._stats = ZoneStats()
        
        # Components
        self.overlap_checker = get_overlap_checker(self.symbol, enable_caching=True)
        self.indicators = get_technical_indicators()
        self.buffer_manager = get_buffer_manager()
        
        # Zone storage
        self.history_limit = self.global_config.max_zones_per_symbol
        self._active_zones = self.buffer_manager.get_zones_buffer(self.symbol, size=self.history_limit)
        self._broken_zones = self.buffer_manager.get_buffer(self.symbol, "broken_zones", size=50)
        
        # Zone tracking
        self._zone_creation_times: Dict[str, datetime] = {}
        self._zone_strengths: Dict[str, ZoneStrength] = {}
        
        # Performance tracking
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(minutes=30)
        
        logger.info(f"🔧 ZoneManager initialized for {self.symbol}")
    
    def create_supply_zone(self, swing: Swing, ohlcv_data: pd.DataFrame, 
                          current_time: Optional[datetime] = None,
                          current_bar_index: Optional[int] = None) -> Optional[Zone]:
        """
        Create supply zone from swing high with ATR-based width
        
        Args:
            swing: Swing high that triggered zone creation
            ohlcv_data: OHLCV data for ATR calculation
            current_time: Current timestamp (optional)
            current_bar_index: Current bar index (optional)
            
        Returns:
            Created Zone object or None if rejected
        """
        start_time = time.time()
        
        try:
            with self._lock:
                if swing.swing_type != SwingType.HIGH:
                    logger.warning(f"⚠️ Cannot create supply zone from {swing.swing_type.value} swing")
                    return None
                
                # Set defaults
                if current_time is None:
                    current_time = datetime.now()
                if current_bar_index is None:
                    current_bar_index = len(ohlcv_data) - 1
                
                # Calculate ATR for zone width
                atr_value = self._calculate_atr_for_zone(ohlcv_data, swing.timestamp)
                if atr_value <= 0:
                    logger.warning(f"⚠️ Invalid ATR value: {atr_value}")
                    return None
                
                # Calculate zone boundaries
                atr_buffer = atr_value * self.config.atr_multiplier
                
                # Validate zone height
                if not self._validate_zone_height(swing.price, atr_buffer):
                    logger.debug(f"🔍 Zone height validation failed for swing at ${swing.price:.2f}")
                    self._stats.strength_rejections += 1
                    return None
                
                # Create zone using Zone model factory method
                zone = Zone.create_supply_zone(
                    swing_price=swing.price,
                    swing_time=swing.timestamp,
                    swing_bar_index=getattr(swing, 'bar_index', current_bar_index),
                    atr_buffer=atr_buffer,
                    current_time=current_time,
                    current_bar_index=current_bar_index
                )
                
                # Calculate zone strength
                zone_strength = self._calculate_zone_strength(swing, ohlcv_data, atr_value)
                
                # Validate swing strength requirement
                if not self._validate_swing_strength(zone_strength):
                    logger.debug(f"🔍 Swing strength validation failed: {zone_strength.value}")
                    self._stats.strength_rejections += 1
                    return None
                
                # Check for overlaps if enabled
                if self.config.enable_overlap_check:
                    existing_zones = self.get_active_zones()
                    overlap_result = self.overlap_checker.check_zone_overlap(
                        zone, existing_zones, atr_buffer
                    )
                    
                    if overlap_result.has_overlap:
                        logger.debug(f"🔍 Zone overlap detected: {overlap_result.overlap_percentage:.1f}%")
                        
                        # Handle overlap based on resolution strategy
                        if not self._handle_zone_overlap(zone, existing_zones, overlap_result):
                            self._stats.overlap_rejections += 1
                            return None
                
                # Add zone to active zones
                self._active_zones.add_pop(zone)
                
                # Track zone metadata
                self._zone_creation_times[zone.zone_id] = current_time
                self._zone_strengths[zone.zone_id] = zone_strength
                
                # Update statistics
                creation_time = (time.time() - start_time) * 1000
                self._update_creation_stats(ZoneType.SUPPLY, creation_time)
                
                logger.debug(f"✅ Supply zone created: ${zone.bottom:.2f}-${zone.top:.2f} "
                           f"(strength: {zone_strength.value}) in {creation_time:.2f}ms")
                
                return zone
                
        except Exception as e:
            logger.error(f"❌ Error creating supply zone: {e}")
            return None
    
    def create_demand_zone(self, swing: Swing, ohlcv_data: pd.DataFrame,
                          current_time: Optional[datetime] = None,
                          current_bar_index: Optional[int] = None) -> Optional[Zone]:
        """
        Create demand zone from swing low with ATR-based width
        
        Args:
            swing: Swing low that triggered zone creation
            ohlcv_data: OHLCV data for ATR calculation
            current_time: Current timestamp (optional)
            current_bar_index: Current bar index (optional)
            
        Returns:
            Created Zone object or None if rejected
        """
        start_time = time.time()
        
        try:
            with self._lock:
                if swing.swing_type != SwingType.LOW:
                    logger.warning(f"⚠️ Cannot create demand zone from {swing.swing_type.value} swing")
                    return None
                
                # Set defaults
                if current_time is None:
                    current_time = datetime.now()
                if current_bar_index is None:
                    current_bar_index = len(ohlcv_data) - 1
                
                # Calculate ATR for zone width
                atr_value = self._calculate_atr_for_zone(ohlcv_data, swing.timestamp)
                if atr_value <= 0:
                    logger.warning(f"⚠️ Invalid ATR value: {atr_value}")
                    return None
                
                # Calculate zone boundaries
                atr_buffer = atr_value * self.config.atr_multiplier
                
                # Validate zone height
                if not self._validate_zone_height(swing.price, atr_buffer):
                    logger.debug(f"🔍 Zone height validation failed for swing at ${swing.price:.2f}")
                    self._stats.strength_rejections += 1
                    return None
                
                # Create zone using Zone model factory method
                zone = Zone.create_demand_zone(
                    swing_price=swing.price,
                    swing_time=swing.timestamp,
                    swing_bar_index=getattr(swing, 'bar_index', current_bar_index),
                    atr_buffer=atr_buffer,
                    current_time=current_time,
                    current_bar_index=current_bar_index
                )
                
                # Calculate zone strength
                zone_strength = self._calculate_zone_strength(swing, ohlcv_data, atr_value)
                
                # Validate swing strength requirement
                if not self._validate_swing_strength(zone_strength):
                    logger.debug(f"🔍 Swing strength validation failed: {zone_strength.value}")
                    self._stats.strength_rejections += 1
                    return None
                
                # Check for overlaps if enabled
                if self.config.enable_overlap_check:
                    existing_zones = self.get_active_zones()
                    overlap_result = self.overlap_checker.check_zone_overlap(
                        zone, existing_zones, atr_buffer
                    )
                    
                    if overlap_result.has_overlap:
                        logger.debug(f"🔍 Zone overlap detected: {overlap_result.overlap_percentage:.1f}%")
                        
                        # Handle overlap based on resolution strategy
                        if not self._handle_zone_overlap(zone, existing_zones, overlap_result):
                            self._stats.overlap_rejections += 1
                            return None
                
                # Add zone to active zones
                self._active_zones.add_pop(zone)
                
                # Track zone metadata
                self._zone_creation_times[zone.zone_id] = current_time
                self._zone_strengths[zone.zone_id] = zone_strength
                
                # Update statistics
                creation_time = (time.time() - start_time) * 1000
                self._update_creation_stats(ZoneType.DEMAND, creation_time)
                
                logger.debug(f"✅ Demand zone created: ${zone.bottom:.2f}-${zone.top:.2f} "
                           f"(strength: {zone_strength.value}) in {creation_time:.2f}ms")
                
                return zone
                
        except Exception as e:
            logger.error(f"❌ Error creating demand zone: {e}")
            return None
    
    def check_zone_breaks(self, current_price: float, current_time: datetime,
                         current_bar_index: int) -> List[Zone]:
        """
        Check if current price breaks any active zones
        
        Args:
            current_price: Current market price
            current_time: Current timestamp
            current_bar_index: Current bar index
            
        Returns:
            List of broken zones
        """
        try:
            with self._lock:
                broken_zones = []
                active_zones = self.get_active_zones()
                
                for zone in active_zones:
                    if self._is_zone_broken(zone, current_price):
                        # Mark zone as broken
                        zone.mark_as_broken(current_price, current_time, current_bar_index)
                        
                        # Move to broken zones buffer
                        self._broken_zones.add_pop(zone)
                        
                        # Remove from active zones
                        self._remove_zone_from_active(zone)
                        
                        # Update statistics
                        self._stats.zones_broken += 1
                        
                        broken_zones.append(zone)
                        
                        logger.debug(f"💥 Zone broken: {zone.zone_type.name} at ${zone.poi:.2f} "
                                   f"by price ${current_price:.2f}")
                
                return broken_zones
                
        except Exception as e:
            logger.error(f"❌ Error checking zone breaks: {e}")
            return []
    
    def batch_process_swings(self, swings: List[Swing], ohlcv_data: pd.DataFrame) -> Dict[str, List[Zone]]:
        """
        Batch process multiple swings for efficient zone creation
        
        Args:
            swings: List of swings to process
            ohlcv_data: OHLCV data for calculations
            
        Returns:
            Dictionary mapping swing IDs to created zones
        """
        try:
            results = {}
            current_time = datetime.now()
            current_bar_index = len(ohlcv_data) - 1
            
            # Sort swings by timestamp for chronological processing
            sorted_swings = sorted(swings, key=lambda s: s.timestamp)
            
            for swing in sorted_swings:
                swing_id = getattr(swing, 'swing_id', f"swing_{swing.timestamp}")
                created_zones = []
                
                if swing.swing_type == SwingType.HIGH:
                    zone = self.create_supply_zone(swing, ohlcv_data, current_time, current_bar_index)
                    if zone:
                        created_zones.append(zone)
                
                elif swing.swing_type == SwingType.LOW:
                    zone = self.create_demand_zone(swing, ohlcv_data, current_time, current_bar_index)
                    if zone:
                        created_zones.append(zone)
                
                results[swing_id] = created_zones
            
            logger.debug(f"📊 Batch processed {len(swings)} swings, created {sum(len(zones) for zones in results.values())} zones")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in batch swing processing: {e}")
            return {}
    
    def get_active_zones(self, zone_type: Optional[ZoneType] = None) -> List[Zone]:
        """
        Get list of active zones, optionally filtered by type
        
        Args:
            zone_type: Optional zone type filter
            
        Returns:
            List of active Zone objects
        """
        try:
            all_zones = self._active_zones.to_list()
            active_zones = [zone for zone in all_zones if isinstance(zone, Zone) and zone.is_active]
            
            if zone_type:
                active_zones = [zone for zone in active_zones if zone.zone_type == zone_type]
            
            return active_zones
            
        except Exception as e:
            logger.error(f"❌ Error getting active zones: {e}")
            return []
    
    def get_broken_zones(self, limit: int = 20) -> List[Zone]:
        """
        Get list of recently broken zones
        
        Args:
            limit: Maximum number of zones to return
            
        Returns:
            List of broken Zone objects
        """
        try:
            all_broken = self._broken_zones.to_list()
            broken_zones = [zone for zone in all_broken if isinstance(zone, Zone) and zone.is_broken]
            
            # Sort by break time (most recent first)
            broken_zones.sort(key=lambda z: z.break_time or datetime.min, reverse=True)
            
            return broken_zones[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error getting broken zones: {e}")
            return []
    
    def get_zones_by_price_range(self, min_price: float, max_price: float) -> List[Zone]:
        """
        Get zones within a specific price range
        
        Args:
            min_price: Minimum price level
            max_price: Maximum price level
            
        Returns:
            List of zones within the price range
        """
        try:
            active_zones = self.get_active_zones()
            
            zones_in_range = []
            for zone in active_zones:
                # Check if zone overlaps with price range
                if (zone.bottom <= max_price and zone.top >= min_price):
                    zones_in_range.append(zone)
            
            # Sort by distance from current price range center
            range_center = (min_price + max_price) / 2
            zones_in_range.sort(key=lambda z: abs(z.poi - range_center))
            
            return zones_in_range
            
        except Exception as e:
            logger.error(f"❌ Error getting zones by price range: {e}")
            return []
    
    def get_nearest_zones(self, current_price: float, count: int = 5) -> Dict[str, List[Zone]]:
        """
        Get nearest supply and demand zones to current price
        
        Args:
            current_price: Current market price
            count: Number of zones to return for each type
            
        Returns:
            Dictionary with 'supply' and 'demand' zone lists
        """
        try:
            active_zones = self.get_active_zones()
            
            supply_zones = [z for z in active_zones if z.zone_type == ZoneType.SUPPLY and z.bottom > current_price]
            demand_zones = [z for z in active_zones if z.zone_type == ZoneType.DEMAND and z.top < current_price]
            
            # Sort by distance from current price
            supply_zones.sort(key=lambda z: z.bottom - current_price)
            demand_zones.sort(key=lambda z: current_price - z.top)
            
            return {
                'supply': supply_zones[:count],
                'demand': demand_zones[:count]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting nearest zones: {e}")
            return {'supply': [], 'demand': []}
    
    def cleanup_expired_zones(self, max_age_hours: float = 168.0) -> int:
        """
        Clean up expired zones based on age
        
        Args:
            max_age_hours: Maximum age in hours before zone expires
            
        Returns:
            Number of zones cleaned up
        """
        try:
            with self._lock:
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(hours=max_age_hours)
                
                active_zones = self.get_active_zones()
                expired_count = 0
                
                for zone in active_zones:
                    zone_age = current_time - zone.left_time
                    
                    if zone.left_time < cutoff_time:
                        # Mark as expired
                        zone.is_active = False
                        
                        # Remove from active zones
                        self._remove_zone_from_active(zone)
                        
                        # Clean up metadata
                        if zone.zone_id in self._zone_creation_times:
                            del self._zone_creation_times[zone.zone_id]
                        if zone.zone_id in self._zone_strengths:
                            del self._zone_strengths[zone.zone_id]
                        
                        expired_count += 1
                        self._stats.zones_expired += 1
                
                self._last_cleanup = current_time
                
                if expired_count > 0:
                    logger.info(f"🧹 Cleaned up {expired_count} expired zones for {self.symbol}")
                
                return expired_count
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired zones: {e}")
            return 0
    
    def _calculate_atr_for_zone(self, ohlcv_data: pd.DataFrame, swing_time: datetime) -> float:
        """Calculate ATR value for zone creation"""
        try:
            # Find the swing point in the data
            swing_index = None
            min_time_diff = float('inf')
            
            for i, timestamp in enumerate(ohlcv_data.index):
                time_diff = abs((timestamp - swing_time).total_seconds())
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    swing_index = i
                    
                # If we find exact match or very close, use it
                if time_diff < 3600:  # Within 1 hour
                    break
            
            if swing_index is None:
                swing_index = len(ohlcv_data) - 1
            
            # Calculate ATR up to swing point
            atr_period = min(self.global_config.atr_period, swing_index + 1)
            
            # Ensure minimum ATR period for reliable calculation
            min_atr_period = 14  # Standard ATR period
            if atr_period < min_atr_period:
                atr_period = min(min_atr_period, len(ohlcv_data))
            
            # Final check - need at least 5 periods for basic ATR
            if atr_period < 5:
                atr_period = min(5, len(ohlcv_data))
            
            # Get data up to swing point
            data_subset = ohlcv_data.iloc[:swing_index + 1]
            
            # Calculate ATR
            atr_result = self.indicators.calculate_atr(
                data_subset, self.symbol, "zone_creation", period=atr_period
            )
            
            if len(atr_result.values) > 0 and not atr_result.values.isna().all():
                atr_value = float(atr_result.values.iloc[-1])
                if atr_value > 0:
                    return atr_value
            
            # Fallback: use simple price range calculation
            try:
                recent_data = ohlcv_data.tail(min(20, len(ohlcv_data)))
                if len(recent_data) > 0:
                    price_range = float(recent_data['high'].max() - recent_data['low'].min())
                    # Use 5% of recent price range as ATR estimate
                    fallback_atr = price_range * 0.05
                    if fallback_atr > 0:
                        logger.debug(f"🔄 Using fallback ATR: {fallback_atr:.2f} (range: {price_range:.2f})")
                        return fallback_atr
                
                # If still no valid ATR, use percentage of current price
                if len(ohlcv_data) > 0:
                    current_price = float(ohlcv_data['close'].iloc[-1])
                    fallback_atr = current_price * 0.02  # 2% of current price
                    logger.debug(f"🔄 Using price-based fallback ATR: {fallback_atr:.2f} (2% of ${current_price:.2f})")
                    return fallback_atr
                
                # Symbol-based fallback
                if 'BTC' in self.symbol:
                    return 1000.0  # $1000 for BTC
                elif 'ETH' in self.symbol:
                    return 100.0   # $100 for ETH
                else:
                    return 10.0    # $10 for other cryptos
                    
            except Exception as fallback_error:
                logger.warning(f"⚠️ Fallback ATR calculation failed: {fallback_error}")
                # Symbol-based ultimate fallback
                if 'BTC' in self.symbol:
                    return 1000.0
                elif 'ETH' in self.symbol:
                    return 100.0
                else:
                    return 10.0
                
        except Exception as e:
            logger.error(f"❌ Error calculating ATR for zone: {e}")
            return 0.0
    
    def _validate_zone_height(self, swing_price: float, atr_buffer: float) -> bool:
        """Validate zone height against configuration limits"""
        try:
            zone_height_pct = (atr_buffer / swing_price) * 100
            
            return (self.config.min_zone_height <= zone_height_pct <= self.config.max_zone_height)
            
        except Exception as e:
            logger.error(f"❌ Error validating zone height: {e}")
            return False
    
    def _calculate_zone_strength(self, swing: Swing, ohlcv_data: pd.DataFrame, atr_value: float) -> ZoneStrength:
        """Calculate zone strength based on swing properties and market context"""
        try:
            strength_score = 0
            
            # Swing strength contribution (40% weight)
            swing_strength = getattr(swing, 'strength', None)
            if swing_strength:
                if hasattr(swing_strength, 'value'):
                    strength_name = swing_strength.value
                else:
                    strength_name = str(swing_strength)
                
                strength_mapping = {
                    'weak': 1,
                    'medium': 2,
                    'strong': 3,
                    'very_strong': 4
                }
                strength_score += strength_mapping.get(strength_name, 2) * 10
            else:
                strength_score += 20  # Default medium strength
            
            # Volume confirmation (30% weight)
            if hasattr(swing, 'volume_profile') and swing.volume_profile:
                volume_ratio = swing.volume_profile.get('volume_ratio', 1.0)
                if volume_ratio >= self.config.volume_threshold_multiplier:
                    strength_score += 30
                elif volume_ratio >= 1.0:
                    strength_score += 20
                else:
                    strength_score += 10
            else:
                strength_score += 15  # Default if no volume data
            
            # ATR relationship (20% weight)
            if atr_value > 0:
                # Zones with appropriate ATR sizing get bonus
                strength_score += 20
            
            # Time context (10% weight)
            # Recent swings get slight bonus for relevance
            time_diff = datetime.now() - swing.timestamp
            if time_diff.total_hours() < 24:
                strength_score += 10
            elif time_diff.total_hours() < 72:
                strength_score += 5
            
            # Convert score to strength enum
            if strength_score >= 75:
                return ZoneStrength.VERY_STRONG
            elif strength_score >= 60:
                return ZoneStrength.STRONG
            elif strength_score >= 40:
                return ZoneStrength.MEDIUM
            else:
                return ZoneStrength.WEAK
                
        except Exception as e:
            logger.error(f"❌ Error calculating zone strength: {e}")
            return ZoneStrength.MEDIUM
    
    def _validate_swing_strength(self, zone_strength: ZoneStrength) -> bool:
        """Validate if zone strength meets minimum requirements"""
        try:
            strength_order = {
                ZoneStrength.WEAK: 1,
                ZoneStrength.MEDIUM: 2,
                ZoneStrength.STRONG: 3,
                ZoneStrength.VERY_STRONG: 4
            }
            
            min_strength_order = {
                'weak': 1,
                'medium': 2,
                'strong': 3,
                'very_strong': 4
            }
            
            required_level = min_strength_order.get(self.config.min_swing_strength, 2)
            zone_level = strength_order.get(zone_strength, 2)
            
            return zone_level >= required_level
            
        except Exception as e:
            logger.error(f"❌ Error validating swing strength: {e}")
            return True
    
    def _handle_zone_overlap(self, new_zone: Zone, existing_zones: List[Zone], 
                           overlap_result) -> bool:
        """Handle zone overlap based on resolution strategy"""
        try:
            if self.config.overlap_resolution == "keep_strongest":
                # Compare strengths and keep stronger zone
                new_strength = self._zone_strengths.get(new_zone.zone_id, ZoneStrength.MEDIUM)
                
                for existing_zone in existing_zones:
                    existing_strength = self._zone_strengths.get(existing_zone.zone_id, ZoneStrength.MEDIUM)
                    
                    # If existing zone is stronger or equal, reject new zone
                    if existing_strength.value >= new_strength.value:
                        return False
                
                # New zone is stronger, remove weaker existing zones
                self._remove_overlapping_zones(existing_zones, overlap_result.zones_involved)
                return True
            
            elif self.config.overlap_resolution == "keep_newest":
                # Remove older overlapping zones
                self._remove_overlapping_zones(existing_zones, overlap_result.zones_involved)
                return True
            
            elif self.config.overlap_resolution == "merge":
                # Merge overlapping zones (simplified implementation)
                if overlap_result.zones_involved:
                    # Expand new zone to encompass overlapping zones
                    for zone_id in overlap_result.zones_involved:
                        for existing_zone in existing_zones:
                            if existing_zone.zone_id == zone_id:
                                new_zone.top = max(new_zone.top, existing_zone.top)
                                new_zone.bottom = min(new_zone.bottom, existing_zone.bottom)
                                new_zone.poi = (new_zone.top + new_zone.bottom) / 2
                
                self._remove_overlapping_zones(existing_zones, overlap_result.zones_involved)
                return True
            
            else:
                # Default: reject overlapping zones
                return False
                
        except Exception as e:
            logger.error(f"❌ Error handling zone overlap: {e}")
            return False
    
    def _remove_overlapping_zones(self, existing_zones: List[Zone], zone_ids: List[str]) -> None:
        """Remove zones that overlap with new zone"""
        try:
            for zone_id in zone_ids:
                for zone in existing_zones:
                    if zone.zone_id == zone_id:
                        self._remove_zone_from_active(zone)
                        logger.debug(f"🗑️ Removed overlapping zone: {zone_id}")
                        break
        except Exception as e:
            logger.error(f"❌ Error removing overlapping zones: {e}")
    
    def _remove_zone_from_active(self, zone: Zone) -> None:
        """Remove zone from active zones buffer"""
        try:
            # Remove from buffer (implementation depends on buffer type)
            active_zones = self._active_zones.to_list()
            updated_zones = [z for z in active_zones if z.zone_id != zone.zone_id]
            
            # Clear and repopulate buffer
            self._active_zones.clear()
            for z in updated_zones:
                self._active_zones.add_pop(z)
                
        except Exception as e:
            logger.error(f"❌ Error removing zone from active: {e}")
    
    def _is_zone_broken(self, zone: Zone, current_price: float) -> bool:
        """Check if zone is broken by current price"""
        try:
            if zone.zone_type == ZoneType.SUPPLY:
                # Supply zone broken when price closes above it
                return current_price > zone.top
            else:  # DEMAND zone
                # Demand zone broken when price closes below it
                return current_price < zone.bottom
        except Exception as e:
            logger.error(f"❌ Error checking zone break: {e}")
            return False
    
    def _update_creation_stats(self, zone_type: ZoneType, creation_time_ms: float) -> None:
        """Update zone creation statistics"""
        try:
            self._stats.total_zones_created += 1
            self._stats.avg_creation_time_ms = creation_time_ms
            self._stats.last_zone_created = datetime.now()
            
            if zone_type == ZoneType.SUPPLY:
                self._stats.supply_zones_created += 1
            else:
                self._stats.demand_zones_created += 1
            
            # Update active zones count
            self._stats.active_zones = len(self.get_active_zones())
            
        except Exception as e:
            logger.error(f"❌ Error updating creation stats: {e}")
    
    def update_zone_boundaries(self, zone_id: str, current_time: datetime, 
                              current_bar_index: int) -> bool:
        """
        Update zone right boundary (extension)
        
        Args:
            zone_id: Zone ID to update
            current_time: Current timestamp
            current_bar_index: Current bar index
            
        Returns:
            True if zone was updated, False otherwise
        """
        try:
            active_zones = self.get_active_zones()
            
            for zone in active_zones:
                if zone.zone_id == zone_id:
                    zone.update_right_boundary(current_time, current_bar_index)
                    logger.debug(f"🔄 Updated zone boundary: {zone_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error updating zone boundaries: {e}")
            return False
    
    def get_zone_by_id(self, zone_id: str) -> Optional[Zone]:
        """
        Get zone by ID from active or broken zones
        
        Args:
            zone_id: Zone ID to find
            
        Returns:
            Zone object or None if not found
        """
        try:
            # Check active zones
            for zone in self.get_active_zones():
                if zone.zone_id == zone_id:
                    return zone
            
            # Check broken zones
            for zone in self.get_broken_zones():
                if zone.zone_id == zone_id:
                    return zone
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting zone by ID: {e}")
            return None
    
    def get_zone_statistics_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive zone statistics summary
        
        Returns:
            Dictionary with detailed statistics
        """
        try:
            active_zones = self.get_active_zones()
            broken_zones = self.get_broken_zones()
            
            # Zone type distribution
            supply_active = len([z for z in active_zones if z.zone_type == ZoneType.SUPPLY])
            demand_active = len([z for z in active_zones if z.zone_type == ZoneType.DEMAND])
            
            # Strength distribution
            strength_dist = {}
            for zone in active_zones:
                strength = self._zone_strengths.get(zone.zone_id, ZoneStrength.MEDIUM)
                strength_dist[strength.value] = strength_dist.get(strength.value, 0) + 1
            
            # Age analysis
            current_time = datetime.now()
            zone_ages = []
            for zone in active_zones:
                age_hours = (current_time - zone.left_time).total_seconds() / 3600
                zone_ages.append(age_hours)
            
            avg_age = sum(zone_ages) / len(zone_ages) if zone_ages else 0
            
            return {
                'symbol': self.symbol,
                'active_zones': {
                    'total': len(active_zones),
                    'supply': supply_active,
                    'demand': demand_active
                },
                'broken_zones': len(broken_zones),
                'strength_distribution': strength_dist,
                'average_age_hours': avg_age,
                'creation_stats': {
                    'total_created': self._stats.total_zones_created,
                    'supply_created': self._stats.supply_zones_created,
                    'demand_created': self._stats.demand_zones_created,
                    'avg_creation_time_ms': self._stats.avg_creation_time_ms
                },
                'rejection_stats': {
                    'overlap_rejections': self._stats.overlap_rejections,
                    'strength_rejections': self._stats.strength_rejections
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting zone statistics summary: {e}")
            return {}
    
    def perform_maintenance(self) -> Dict[str, int]:
        """
        Perform routine maintenance tasks
        
        Returns:
            Dictionary with maintenance results
        """
        try:
            results = {
                'expired_zones_cleaned': 0,
                'cache_entries_cleared': 0,
                'memory_optimized': 0
            }
            
            # Clean up expired zones
            if (datetime.now() - self._last_cleanup) > self._cleanup_interval:
                results['expired_zones_cleaned'] = self.cleanup_expired_zones()
            
            # Clear overlap checker cache if it's getting large
            if hasattr(self.overlap_checker, '_overlap_cache'):
                cache_size = len(self.overlap_checker._overlap_cache)
                if cache_size > 500:  # Arbitrary threshold
                    self.overlap_checker.clear_cache()
                    results['cache_entries_cleared'] = cache_size
            
            # Memory optimization (remove old metadata)
            current_time = datetime.now()
            old_creation_times = []
            for zone_id, creation_time in self._zone_creation_times.items():
                if (current_time - creation_time).total_hours() > 168:  # 1 week
                    old_creation_times.append(zone_id)
            
            for zone_id in old_creation_times:
                if zone_id in self._zone_creation_times:
                    del self._zone_creation_times[zone_id]
                if zone_id in self._zone_strengths:
                    del self._zone_strengths[zone_id]
                results['memory_optimized'] += 1
            
            if any(results.values()):
                logger.info(f"🔧 Maintenance completed for {self.symbol}: {results}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error performing maintenance: {e}")
            return {}
        try:
            for zone_id in zone_ids:
                for zone in existing_zones:
                    if zone.zone_id == zone_id:
                        self._remove_zone_from_active(zone)
                        break
                        
        except Exception as e:
            logger.error(f"❌ Error removing overlapping zones: {e}")
    
    def _is_zone_broken(self, zone: Zone, current_price: float) -> bool:
        """Check if zone is broken by current price"""
        try:
            if zone.zone_type == ZoneType.SUPPLY:
                # Supply zone broken when price closes above top
                return current_price > zone.top
            else:  # DEMAND
                # Demand zone broken when price closes below bottom
                return current_price < zone.bottom
                
        except Exception as e:
            logger.error(f"❌ Error checking zone break: {e}")
            return False
    
    def _remove_zone_from_active(self, zone: Zone) -> None:
        """Remove zone from active zones buffer"""
        try:
            # Note: CircularBuffer doesn't have direct remove method
            # This is a limitation we'll work with for now
            # In a production system, we might use a different data structure
            pass
            
        except Exception as e:
            logger.error(f"❌ Error removing zone from active: {e}")
    
    def _update_creation_stats(self, zone_type: ZoneType, creation_time_ms: float) -> None:
        """Update zone creation statistics"""
        self._stats.total_zones_created += 1
        self._stats.avg_creation_time_ms = creation_time_ms
        self._stats.last_zone_created = datetime.now()
        
        if zone_type == ZoneType.SUPPLY:
            self._stats.supply_zones_created += 1
        else:
            self._stats.demand_zones_created += 1
        
        # Update active zones count
        self._stats.active_zones = len(self.get_active_zones())
    
    def get_stats(self) -> ZoneStats:
        """Get zone management statistics"""
        with self._lock:
            # Update active zones count
            self._stats.active_zones = len(self.get_active_zones())
            
            # Calculate average zone lifetime
            if self._zone_creation_times:
                current_time = datetime.now()
                total_lifetime_hours = 0
                count = 0
                
                for zone_id, creation_time in self._zone_creation_times.items():
                    lifetime = (current_time - creation_time).total_seconds() / 3600
                    total_lifetime_hours += lifetime
                    count += 1
                
                if count > 0:
                    self._stats.avg_zone_lifetime_hours = total_lifetime_hours / count
            
            return self._stats
    
    def clear_all_zones(self) -> None:
        """Clear all zones and reset statistics"""
        with self._lock:
            self._active_zones.clear()
            self._broken_zones.clear()
            self._zone_creation_times.clear()
            self._zone_strengths.clear()
            self._stats = ZoneStats()
            logger.info(f"🗑️ Cleared all zones for {self.symbol}")
    
    def __repr__(self) -> str:
        """String representation of zone manager"""
        active_count = len(self.get_active_zones())
        return (f"ZoneManager(symbol={self.symbol}, "
                f"active_zones={active_count}, "
                f"total_created={self._stats.total_zones_created})")


# Factory function for creating zone managers
def get_zone_manager(symbol: str, config: Optional[ZoneCreationConfig] = None) -> ZoneManager:
    """
    Factory function to get zone manager instance
    
    Args:
        symbol: Trading symbol
        config: Optional zone creation configuration
        
    Returns:
        ZoneManager instance
    """
    return ZoneManager(symbol, config)