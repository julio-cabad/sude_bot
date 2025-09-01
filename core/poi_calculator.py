#!/usr/bin/env python3
"""
POI (Point of Interest) Calculator Core Module
Professional POI calculation system with advanced caching and multi-symbol support
Calculates critical price levels at zone centers with real-time updates and performance optimization
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any, Set, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
from threading import Lock
from functools import lru_cache
import hashlib
import uuid

from models.zone import Zone, ZoneType
from models.poi import POI, POIType, POIStrength, POIStatus
from config.config_manager import get_config
from utils.array_ops import get_buffer_manager, CircularBuffer
from utils.indicators import get_technical_indicators

logger = logging.getLogger(__name__)


class POICalculationMethod(Enum):
    """Methods for POI calculation"""
    CENTER = "center"           # Simple center point (top + bottom) / 2
    WEIGHTED_CENTER = "weighted_center"  # Volume-weighted center
    FIBONACCI = "fibonacci"     # Fibonacci retracement levels
    ATR_ADJUSTED = "atr_adjusted"  # ATR-adjusted center point
    DYNAMIC = "dynamic"         # Dynamic calculation based on market conditions


@dataclass
class POICalculationConfig:
    """Configuration for POI calculations"""
    method: POICalculationMethod = POICalculationMethod.CENTER
    fibonacci_levels: List[float] = field(default_factory=lambda: [0.236, 0.382, 0.5, 0.618, 0.786])
    atr_adjustment_factor: float = 0.1
    volume_weight_factor: float = 0.3
    enable_dynamic_adjustment: bool = True
    min_zone_height_ratio: float = 0.001  # Minimum zone height as ratio of price
    cache_ttl_seconds: int = 300  # 5 minutes cache TTL


@dataclass
class POICalculationResult:
    """Result of POI calculation"""
    primary_poi: float
    secondary_pois: List[float] = field(default_factory=list)
    fibonacci_levels: Dict[str, float] = field(default_factory=dict)
    confidence_score: float = 0.0
    calculation_method: POICalculationMethod = POICalculationMethod.CENTER
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class POIStats:
    """Statistics for POI calculation performance"""
    total_calculations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_calculation_time_ms: float = 0.0
    pois_created: int = 0
    pois_updated: int = 0
    last_calculation_time: datetime = field(default_factory=datetime.now)


class POICalculator:
    """
    Professional Point of Interest (POI) Calculator
    Calculates critical price levels at zone centers with advanced algorithms and caching
    """
    
    def __init__(self, symbol: str, config: Optional[POICalculationConfig] = None):
        self.symbol = symbol.upper()
        self.config = config or POICalculationConfig()
        self.global_config = get_config()
        
        # Performance optimization
        self._lock = Lock()
        self._stats = POIStats()
        
        # Components
        self.buffer_manager = get_buffer_manager()
        self.indicators = get_technical_indicators()
        
        # Buffers
        self._poi_buffer = self.buffer_manager.get_pois_buffer(self.symbol, size=100)
        self._calculation_cache: Dict[str, Tuple[POICalculationResult, datetime]] = {}
        self._cache_max_size = 500
        
        # Configuration
        self.precision_decimals = 8  # Price precision for crypto
        
        logger.info(f"🎯 POICalculator initialized for {self.symbol}")
    
    def calculate_poi(self, zone: Zone, market_data: Optional[pd.DataFrame] = None) -> POI:
        """
        Calculate Point of Interest for a zone
        
        Args:
            zone: Zone object to calculate POI for
            market_data: Optional market data for advanced calculations
            
        Returns:
            POI object with calculated price level
        """
        start_time = time.time()
        
        try:
            with self._lock:
                # Check cache first
                cache_key = self._generate_cache_key(zone)
                cached_result = self._get_cached_calculation(cache_key)
                
                if cached_result:
                    self._stats.cache_hits += 1
                    calculation_result = cached_result
                else:
                    self._stats.cache_misses += 1
                    # Perform calculation
                    calculation_result = self._perform_poi_calculation(zone, market_data)
                    # Cache the result
                    self._cache_calculation(cache_key, calculation_result)
                
                # Create POI object
                poi = self._create_poi_from_result(zone, calculation_result)
                
                # Store in buffer
                self._poi_buffer.add_pop(poi)
                
                # Update statistics
                calculation_time = (time.time() - start_time) * 1000
                self._update_stats(calculation_time, created=True)
                
                logger.debug(f"🎯 POI calculated for {self.symbol} zone {zone.zone_id}: "
                           f"${poi.price:.4f} in {calculation_time:.2f}ms")
                
                return poi
                
        except Exception as e:
            logger.error(f"❌ Error calculating POI for {self.symbol}: {e}")
            # Return fallback POI
            return self._create_fallback_poi(zone)
    
    def _perform_poi_calculation(self, zone: Zone, market_data: Optional[pd.DataFrame]) -> POICalculationResult:
        """
        Perform the actual POI calculation based on configuration
        
        Args:
            zone: Zone to calculate POI for
            market_data: Optional market data
            
        Returns:
            POICalculationResult with calculated values
        """
        try:
            method = self.config.method
            
            if method == POICalculationMethod.CENTER:
                return self._calculate_center_poi(zone)
            
            elif method == POICalculationMethod.WEIGHTED_CENTER:
                return self._calculate_weighted_center_poi(zone, market_data)
            
            elif method == POICalculationMethod.FIBONACCI:
                return self._calculate_fibonacci_poi(zone)
            
            elif method == POICalculationMethod.ATR_ADJUSTED:
                return self._calculate_atr_adjusted_poi(zone, market_data)
            
            elif method == POICalculationMethod.DYNAMIC:
                return self._calculate_dynamic_poi(zone, market_data)
            
            else:
                # Fallback to center calculation
                return self._calculate_center_poi(zone)
                
        except Exception as e:
            logger.error(f"❌ Error in POI calculation: {e}")
            return self._calculate_center_poi(zone)  # Fallback
    
    def _calculate_center_poi(self, zone: Zone) -> POICalculationResult:
        """Calculate simple center POI"""
        try:
            primary_poi = round((zone.top + zone.bottom) / 2, self.precision_decimals)
            
            # Calculate confidence based on zone height
            zone_height = zone.top - zone.bottom
            current_price = zone.swing_price
            height_ratio = zone_height / current_price if current_price > 0 else 0
            
            # Higher confidence for larger zones relative to price
            confidence = min(height_ratio * 100, 100.0)
            
            return POICalculationResult(
                primary_poi=primary_poi,
                confidence_score=confidence,
                calculation_method=POICalculationMethod.CENTER,
                metadata={
                    'zone_height': zone_height,
                    'height_ratio': height_ratio,
                    'zone_top': zone.top,
                    'zone_bottom': zone.bottom
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error in center POI calculation: {e}")
            return POICalculationResult(primary_poi=zone.poi)
    
    def _calculate_weighted_center_poi(self, zone: Zone, market_data: Optional[pd.DataFrame]) -> POICalculationResult:
        """Calculate volume-weighted center POI"""
        try:
            # Start with center calculation
            center_result = self._calculate_center_poi(zone)
            
            if market_data is None or market_data.empty:
                return center_result
            
            # Find candles within the zone time range
            zone_data = market_data[
                (market_data.index >= zone.left_time) & 
                (market_data.index <= zone.right_time)
            ]
            
            if zone_data.empty:
                return center_result
            
            # Calculate volume-weighted price within zone
            zone_prices = []
            zone_volumes = []
            
            for _, candle in zone_data.iterrows():
                # Check if candle intersects with zone
                candle_high = candle['high']
                candle_low = candle['low']
                candle_volume = candle['volume']
                
                if candle_low <= zone.top and candle_high >= zone.bottom:
                    # Use OHLC4 as representative price
                    ohlc4 = (candle['open'] + candle['high'] + candle['low'] + candle['close']) / 4
                    zone_prices.append(ohlc4)
                    zone_volumes.append(candle_volume)
            
            if not zone_prices:
                return center_result
            
            # Calculate volume-weighted average price (VWAP)
            total_volume = sum(zone_volumes)
            if total_volume > 0:
                vwap = sum(p * v for p, v in zip(zone_prices, zone_volumes)) / total_volume
                
                # Blend with center POI based on weight factor
                weight = self.config.volume_weight_factor
                weighted_poi = (vwap * weight) + (center_result.primary_poi * (1 - weight))
                weighted_poi = round(weighted_poi, self.precision_decimals)
                
                # Update confidence based on volume data quality
                confidence = center_result.confidence_score * (1 + len(zone_prices) * 0.1)
                confidence = min(confidence, 100.0)
                
                return POICalculationResult(
                    primary_poi=weighted_poi,
                    confidence_score=confidence,
                    calculation_method=POICalculationMethod.WEIGHTED_CENTER,
                    metadata={
                        **center_result.metadata,
                        'vwap': vwap,
                        'total_volume': total_volume,
                        'candles_in_zone': len(zone_prices),
                        'weight_factor': weight
                    }
                )
            
            return center_result
            
        except Exception as e:
            logger.error(f"❌ Error in weighted center POI calculation: {e}")
            return self._calculate_center_poi(zone)
    
    def _calculate_fibonacci_poi(self, zone: Zone) -> POICalculationResult:
        """Calculate Fibonacci-based POI levels"""
        try:
            zone_height = zone.top - zone.bottom
            fibonacci_levels = {}
            secondary_pois = []
            
            # Calculate Fibonacci retracement levels
            for level in self.config.fibonacci_levels:
                if zone.zone_type == ZoneType.SUPPLY:
                    # For supply zones, calculate from top down
                    fib_price = zone.top - (zone_height * level)
                else:
                    # For demand zones, calculate from bottom up
                    fib_price = zone.bottom + (zone_height * level)
                
                fib_price = round(fib_price, self.precision_decimals)
                fibonacci_levels[f"fib_{level}"] = fib_price
                secondary_pois.append(fib_price)
            
            # Use 50% retracement as primary POI
            primary_poi = fibonacci_levels.get("fib_0.5", (zone.top + zone.bottom) / 2)
            
            # Calculate confidence based on zone characteristics
            confidence = 75.0  # Fibonacci levels generally have good confidence
            
            return POICalculationResult(
                primary_poi=primary_poi,
                secondary_pois=secondary_pois,
                fibonacci_levels=fibonacci_levels,
                confidence_score=confidence,
                calculation_method=POICalculationMethod.FIBONACCI,
                metadata={
                    'zone_height': zone_height,
                    'fibonacci_count': len(fibonacci_levels),
                    'zone_type': zone.zone_type.name
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error in Fibonacci POI calculation: {e}")
            return self._calculate_center_poi(zone)
    
    def _calculate_atr_adjusted_poi(self, zone: Zone, market_data: Optional[pd.DataFrame]) -> POICalculationResult:
        """Calculate ATR-adjusted POI"""
        try:
            # Start with center calculation
            center_result = self._calculate_center_poi(zone)
            
            if market_data is None or zone.atr_buffer <= 0:
                return center_result
            
            # Adjust POI based on ATR
            atr_adjustment = zone.atr_buffer * self.config.atr_adjustment_factor
            
            if zone.zone_type == ZoneType.SUPPLY:
                # For supply zones, adjust slightly lower (more conservative)
                adjusted_poi = center_result.primary_poi - atr_adjustment
            else:
                # For demand zones, adjust slightly higher (more conservative)
                adjusted_poi = center_result.primary_poi + atr_adjustment
            
            # Ensure adjusted POI stays within zone bounds
            adjusted_poi = max(zone.bottom, min(zone.top, adjusted_poi))
            adjusted_poi = round(adjusted_poi, self.precision_decimals)
            
            # Increase confidence for ATR-adjusted calculations
            confidence = center_result.confidence_score * 1.2
            confidence = min(confidence, 100.0)
            
            return POICalculationResult(
                primary_poi=adjusted_poi,
                confidence_score=confidence,
                calculation_method=POICalculationMethod.ATR_ADJUSTED,
                metadata={
                    **center_result.metadata,
                    'atr_buffer': zone.atr_buffer,
                    'atr_adjustment': atr_adjustment,
                    'original_center': center_result.primary_poi
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error in ATR-adjusted POI calculation: {e}")
            return self._calculate_center_poi(zone)
    
    def _calculate_dynamic_poi(self, zone: Zone, market_data: Optional[pd.DataFrame]) -> POICalculationResult:
        """Calculate dynamic POI based on market conditions"""
        try:
            # Try different methods and choose the best one
            methods_to_try = [
                POICalculationMethod.WEIGHTED_CENTER,
                POICalculationMethod.FIBONACCI,
                POICalculationMethod.ATR_ADJUSTED,
                POICalculationMethod.CENTER
            ]
            
            results = []
            
            for method in methods_to_try:
                try:
                    if method == POICalculationMethod.WEIGHTED_CENTER:
                        result = self._calculate_weighted_center_poi(zone, market_data)
                    elif method == POICalculationMethod.FIBONACCI:
                        result = self._calculate_fibonacci_poi(zone)
                    elif method == POICalculationMethod.ATR_ADJUSTED:
                        result = self._calculate_atr_adjusted_poi(zone, market_data)
                    else:
                        result = self._calculate_center_poi(zone)
                    
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Method {method} failed: {e}")
                    continue
            
            if not results:
                return self._calculate_center_poi(zone)
            
            # Choose result with highest confidence
            best_result = max(results, key=lambda r: r.confidence_score)
            
            # Combine secondary POIs from all methods
            all_secondary_pois = []
            for result in results:
                all_secondary_pois.extend(result.secondary_pois)
            
            # Remove duplicates and sort
            unique_pois = list(set(all_secondary_pois))
            unique_pois.sort()
            
            # Update result
            best_result.calculation_method = POICalculationMethod.DYNAMIC
            best_result.secondary_pois = unique_pois[:10]  # Limit to top 10
            best_result.metadata['methods_tried'] = len(results)
            best_result.metadata['best_method'] = best_result.calculation_method.value
            
            return best_result
            
        except Exception as e:
            logger.error(f"❌ Error in dynamic POI calculation: {e}")
            return self._calculate_center_poi(zone)
    
    def _create_poi_from_result(self, zone: Zone, result: POICalculationResult) -> POI:
        """Create POI object from calculation result"""
        try:
            # Determine POI type based on zone type
            poi_type = POIType.SUPPLY_POI if zone.zone_type == ZoneType.SUPPLY else POIType.DEMAND_POI
            
            # Determine strength based on confidence
            if result.confidence_score >= 80:
                strength = POIStrength.VERY_STRONG
            elif result.confidence_score >= 60:
                strength = POIStrength.STRONG
            elif result.confidence_score >= 40:
                strength = POIStrength.MEDIUM
            else:
                strength = POIStrength.WEAK
            
            # Create POI
            poi = POI(
                poi_id=str(uuid.uuid4()),
                price=result.primary_poi,
                timestamp=datetime.now(),
                zone_id=zone.zone_id,
                poi_type=poi_type,
                strength=strength,
                status=POIStatus.ACTIVE,
                symbol=self.symbol,
                confidence_score=result.confidence_score,
                calculation_method=result.calculation_method.value,
                secondary_levels=result.secondary_pois,
                fibonacci_levels=result.fibonacci_levels,
                metadata=result.metadata,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            return poi
            
        except Exception as e:
            logger.error(f"❌ Error creating POI from result: {e}")
            return self._create_fallback_poi(zone)
    
    def _create_fallback_poi(self, zone: Zone) -> POI:
        """Create fallback POI when calculation fails"""
        poi_type = POIType.SUPPLY_POI if zone.zone_type == ZoneType.SUPPLY else POIType.DEMAND_POI
        
        return POI(
            poi_id=str(uuid.uuid4()),
            price=zone.poi,  # Use zone's built-in POI
            timestamp=datetime.now(),
            zone_id=zone.zone_id,
            poi_type=poi_type,
            strength=POIStrength.WEAK,
            status=POIStatus.ACTIVE,
            symbol=self.symbol,
            confidence_score=25.0,
            calculation_method="fallback",
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
    
    def update_poi_levels(self, zones: List[Zone], market_data: Optional[pd.DataFrame] = None) -> List[POI]:
        """
        Update POI levels for multiple zones
        
        Args:
            zones: List of zones to calculate POIs for
            market_data: Optional market data for calculations
            
        Returns:
            List of calculated POI objects
        """
        try:
            pois = []
            
            for zone in zones:
                if zone.is_active:
                    poi = self.calculate_poi(zone, market_data)
                    pois.append(poi)
            
            logger.debug(f"🎯 Updated {len(pois)} POI levels for {self.symbol}")
            return pois
            
        except Exception as e:
            logger.error(f"❌ Error updating POI levels for {self.symbol}: {e}")
            return []
    
    def get_poi_levels_by_type(self, poi_type: POIType, limit: int = 20) -> List[POI]:
        """
        Get POI levels filtered by type
        
        Args:
            poi_type: Type of POI to filter by
            limit: Maximum number of POIs to return
            
        Returns:
            List of POI objects
        """
        try:
            all_pois = self._poi_buffer.to_list()
            
            # Filter by type and status
            filtered_pois = [
                poi for poi in all_pois 
                if isinstance(poi, POI) and poi.poi_type == poi_type and poi.status == POIStatus.ACTIVE
            ]
            
            # Sort by confidence score (highest first)
            filtered_pois.sort(key=lambda p: p.confidence_score, reverse=True)
            
            return filtered_pois[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error getting POI levels by type: {e}")
            return []
    
    def get_nearest_poi_levels(self, current_price: float, max_distance_pct: float = 5.0) -> Dict[str, List[POI]]:
        """
        Get POI levels near current price
        
        Args:
            current_price: Current market price
            max_distance_pct: Maximum distance as percentage of price
            
        Returns:
            Dictionary with 'above' and 'below' POI lists
        """
        try:
            all_pois = self._poi_buffer.to_list()
            active_pois = [poi for poi in all_pois if isinstance(poi, POI) and poi.status == POIStatus.ACTIVE]
            
            max_distance = current_price * (max_distance_pct / 100)
            
            above_pois = []
            below_pois = []
            
            for poi in active_pois:
                distance = abs(poi.price - current_price)
                
                if distance <= max_distance:
                    if poi.price > current_price:
                        above_pois.append(poi)
                    else:
                        below_pois.append(poi)
            
            # Sort by distance from current price
            above_pois.sort(key=lambda p: p.price)  # Closest above first
            below_pois.sort(key=lambda p: p.price, reverse=True)  # Closest below first
            
            return {
                'above': above_pois[:10],
                'below': below_pois[:10]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting nearest POI levels: {e}")
            return {'above': [], 'below': []}
    
    def invalidate_poi(self, poi_id: str, reason: str = "manual") -> bool:
        """
        Invalidate a POI (mark as inactive)
        
        Args:
            poi_id: ID of POI to invalidate
            reason: Reason for invalidation
            
        Returns:
            True if POI was found and invalidated
        """
        try:
            all_pois = self._poi_buffer.to_list()
            
            for poi in all_pois:
                if isinstance(poi, POI) and poi.poi_id == poi_id:
                    poi.status = POIStatus.INVALIDATED
                    poi.last_updated = datetime.now()
                    poi.metadata['invalidation_reason'] = reason
                    
                    logger.debug(f"🎯 POI {poi_id} invalidated: {reason}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error invalidating POI: {e}")
            return False
    
    def _generate_cache_key(self, zone: Zone) -> str:
        """Generate cache key for zone"""
        try:
            # Create key from zone's key properties
            key_data = f"{zone.zone_id}_{zone.top}_{zone.bottom}_{zone.atr_buffer}_{self.config.method.value}"
            return hashlib.md5(key_data.encode()).hexdigest()[:16]
        except Exception:
            return f"fallback_{time.time()}"
    
    def _get_cached_calculation(self, cache_key: str) -> Optional[POICalculationResult]:
        """Get cached calculation result"""
        try:
            if cache_key in self._calculation_cache:
                result, timestamp = self._calculation_cache[cache_key]
                
                # Check if cache is still valid
                if (datetime.now() - timestamp).total_seconds() < self.config.cache_ttl_seconds:
                    return result
                else:
                    # Remove expired entry
                    del self._calculation_cache[cache_key]
            
            return None
        except Exception:
            return None
    
    def _cache_calculation(self, cache_key: str, result: POICalculationResult) -> None:
        """Cache calculation result"""
        try:
            # Clean up cache if too large
            if len(self._calculation_cache) >= self._cache_max_size:
                self._cleanup_cache()
            
            self._calculation_cache[cache_key] = (result, datetime.now())
        except Exception as e:
            logger.debug(f"Error caching calculation: {e}")
    
    def _cleanup_cache(self) -> None:
        """Clean up expired cache entries"""
        try:
            current_time = datetime.now()
            expired_keys = []
            
            for key, (_, timestamp) in self._calculation_cache.items():
                if (current_time - timestamp).total_seconds() > self.config.cache_ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._calculation_cache[key]
            
            # If still too many, remove oldest
            if len(self._calculation_cache) >= self._cache_max_size:
                sorted_items = sorted(
                    self._calculation_cache.items(),
                    key=lambda x: x[1][1]  # Sort by timestamp
                )
                
                remove_count = len(sorted_items) // 4  # Remove 25%
                for i in range(remove_count):
                    key = sorted_items[i][0]
                    if key in self._calculation_cache:
                        del self._calculation_cache[key]
        except Exception as e:
            logger.debug(f"Error cleaning cache: {e}")
    
    def _update_stats(self, calculation_time_ms: float, created: bool = False, updated: bool = False) -> None:
        """Update calculation statistics"""
        self._stats.total_calculations += 1
        self._stats.avg_calculation_time_ms = calculation_time_ms
        self._stats.last_calculation_time = datetime.now()
        
        if created:
            self._stats.pois_created += 1
        if updated:
            self._stats.pois_updated += 1
    
    def get_stats(self) -> POIStats:
        """Get POI calculation statistics"""
        with self._lock:
            return POIStats(
                total_calculations=self._stats.total_calculations,
                cache_hits=self._stats.cache_hits,
                cache_misses=self._stats.cache_misses,
                avg_calculation_time_ms=self._stats.avg_calculation_time_ms,
                pois_created=self._stats.pois_created,
                pois_updated=self._stats.pois_updated,
                last_calculation_time=self._stats.last_calculation_time
            )
    
    def clear_cache(self) -> None:
        """Clear calculation cache"""
        with self._lock:
            self._calculation_cache.clear()
            logger.info(f"🗑️ Cleared POI calculation cache for {self.symbol}")
    
    def clear_pois(self) -> None:
        """Clear all stored POIs"""
        with self._lock:
            self._poi_buffer.clear()
            logger.info(f"🗑️ Cleared all POIs for {self.symbol}")
    
    def __repr__(self) -> str:
        """String representation of POI calculator"""
        return (f"POICalculator(symbol={self.symbol}, "
                f"method={self.config.method.value}, "
                f"pois={self._poi_buffer.size()}, "
                f"calculations={self._stats.total_calculations})")


# Factory function for creating POI calculators
def get_poi_calculator(symbol: str, config: Optional[POICalculationConfig] = None) -> POICalculator:
    """
    Factory function to get POI calculator instance
    
    Args:
        symbol: Trading symbol
        config: Optional POI calculation configuration
        
    Returns:
        POICalculator instance
    """
    return POICalculator(symbol, config)