#!/usr/bin/env python3
"""
Overlap Checker Utility
Professional zone overlap detection with ATR-based thresholds and performance optimization
Equivalent to Pine Script f_check_overlapping with enhanced caching and multi-symbol support
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
from threading import Lock
from functools import lru_cache
import hashlib

from models.zone import Zone, ZoneType
from config.config_manager import get_config
from utils.indicators import get_technical_indicators

logger = logging.getLogger(__name__)


class OverlapType(Enum):
    """Types of zone overlap"""
    NO_OVERLAP = "no_overlap"
    PARTIAL_OVERLAP = "partial_overlap"
    FULL_OVERLAP = "full_overlap"
    CONTAINED = "contained"
    CONTAINS = "contains"


@dataclass
class OverlapResult:
    """Result of overlap detection"""
    has_overlap: bool
    overlap_type: OverlapType
    overlap_percentage: float
    overlap_area: float
    atr_threshold_met: bool
    zones_involved: List[str] = field(default_factory=list)
    overlap_bounds: Optional[Tuple[float, float]] = None


@dataclass
class OverlapCache:
    """Cache entry for overlap calculations"""
    zone1_hash: str
    zone2_hash: str
    result: OverlapResult
    timestamp: datetime
    ttl_seconds: int = 300  # 5 minutes cache TTL


@dataclass
class OverlapStats:
    """Statistics for overlap detection performance"""
    total_checks: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    overlaps_detected: int = 0
    avg_check_time_ms: float = 0.0
    last_check_time: datetime = field(default_factory=datetime.now)


class OverlapChecker:
    """
    Professional zone overlap detection system
    Detects overlapping supply/demand zones with ATR-based thresholds and performance optimization
    """
    
    def __init__(self, symbol: str, enable_caching: bool = True):
        self.symbol = symbol.upper()
        self.enable_caching = enable_caching
        self.global_config = get_config()
        
        # Performance optimization
        self._lock = Lock()
        self._stats = OverlapStats()
        
        # Caching system
        self._overlap_cache: Dict[str, OverlapCache] = {}
        self._cache_max_size = 1000
        self._cache_ttl_seconds = 300  # 5 minutes
        
        # Components
        self.indicators = get_technical_indicators()
        
        # Configuration
        self.atr_multiplier = getattr(self.global_config, 'atr_multiplier', 1.5)
        self.min_overlap_percentage = 10.0  # Default minimum overlap percentage
        self.overlap_threshold_multiplier = getattr(self.global_config, 'overlap_threshold_multiplier', 2.0)
        self.precision_decimals = 8  # Price precision for crypto
        
        logger.info(f"🔧 OverlapChecker initialized for {self.symbol}")
    
    def check_zone_overlap(self, new_zone: Zone, existing_zones: List[Zone], 
                          atr_threshold: Optional[float] = None) -> OverlapResult:
        """
        Check if new zone overlaps with existing zones within ATR threshold
        
        Args:
            new_zone: New zone to check for overlaps
            existing_zones: List of existing zones to check against
            atr_threshold: ATR threshold for overlap detection (optional)
            
        Returns:
            OverlapResult with detailed overlap information
        """
        start_time = time.time()
        
        try:
            with self._lock:
                # Quick validation
                if not existing_zones:
                    return OverlapResult(
                        has_overlap=False,
                        overlap_type=OverlapType.NO_OVERLAP,
                        overlap_percentage=0.0,
                        overlap_area=0.0,
                        atr_threshold_met=True
                    )
                
                # Use default ATR threshold if not provided
                if atr_threshold is None:
                    atr_threshold = new_zone.atr_buffer * self.atr_multiplier
                
                # Check overlaps with each existing zone
                max_overlap_percentage = 0.0
                strongest_overlap = None
                overlapping_zones = []
                
                for existing_zone in existing_zones:
                    # Skip if same zone type and not configured to check same types
                    check_same_type = True  # Default to checking same type overlaps
                    if (new_zone.zone_type == existing_zone.zone_type and not check_same_type):
                        continue
                    
                    # Check individual overlap
                    overlap_result = self._check_individual_overlap(
                        new_zone, existing_zone, atr_threshold
                    )
                    
                    if overlap_result.has_overlap:
                        overlapping_zones.append(existing_zone.zone_id)
                        
                        if overlap_result.overlap_percentage > max_overlap_percentage:
                            max_overlap_percentage = overlap_result.overlap_percentage
                            strongest_overlap = overlap_result
                
                # Determine final result
                if strongest_overlap:
                    strongest_overlap.zones_involved = overlapping_zones
                    final_result = strongest_overlap
                else:
                    final_result = OverlapResult(
                        has_overlap=False,
                        overlap_type=OverlapType.NO_OVERLAP,
                        overlap_percentage=0.0,
                        overlap_area=0.0,
                        atr_threshold_met=True
                    )
                
                # Update statistics
                check_time = (time.time() - start_time) * 1000
                self._update_stats(final_result.has_overlap, check_time)
                
                logger.debug(f"🔍 Overlap check for {self.symbol}: {final_result.overlap_type.value} "
                           f"({final_result.overlap_percentage:.1f}%) in {check_time:.2f}ms")
                
                return final_result
                
        except Exception as e:
            logger.error(f"❌ Error checking zone overlap for {self.symbol}: {e}")
            return OverlapResult(
                has_overlap=False,
                overlap_type=OverlapType.NO_OVERLAP,
                overlap_percentage=0.0,
                overlap_area=0.0,
                atr_threshold_met=False
            )
    
    def _check_individual_overlap(self, zone1: Zone, zone2: Zone, 
                                 atr_threshold: float) -> OverlapResult:
        """
        Check overlap between two individual zones
        
        Args:
            zone1: First zone
            zone2: Second zone
            atr_threshold: ATR threshold for overlap detection
            
        Returns:
            OverlapResult for the two zones
        """
        try:
            # Check cache first
            if self.enable_caching:
                cached_result = self._get_cached_overlap(zone1, zone2)
                if cached_result:
                    self._stats.cache_hits += 1
                    return cached_result.result
                else:
                    self._stats.cache_misses += 1
            
            # Calculate zone bounds with precision
            zone1_top = round(zone1.top, self.precision_decimals)
            zone1_bottom = round(zone1.bottom, self.precision_decimals)
            zone2_top = round(zone2.top, self.precision_decimals)
            zone2_bottom = round(zone2.bottom, self.precision_decimals)
            
            # Ensure proper ordering (top > bottom)
            if zone1_top < zone1_bottom:
                zone1_top, zone1_bottom = zone1_bottom, zone1_top
            if zone2_top < zone2_bottom:
                zone2_top, zone2_bottom = zone2_bottom, zone2_top
            
            # Calculate overlap bounds
            overlap_top = min(zone1_top, zone2_top)
            overlap_bottom = max(zone1_bottom, zone2_bottom)
            
            # Check if there's any overlap
            if overlap_bottom >= overlap_top:
                # No overlap
                result = OverlapResult(
                    has_overlap=False,
                    overlap_type=OverlapType.NO_OVERLAP,
                    overlap_percentage=0.0,
                    overlap_area=0.0,
                    atr_threshold_met=True,
                    overlap_bounds=None
                )
            else:
                # Calculate overlap metrics
                overlap_height = overlap_top - overlap_bottom
                
                zone1_height = zone1_top - zone1_bottom
                zone2_height = zone2_top - zone2_bottom
                
                # Calculate overlap percentages
                zone1_overlap_pct = (overlap_height / zone1_height * 100) if zone1_height > 0 else 0
                zone2_overlap_pct = (overlap_height / zone2_height * 100) if zone2_height > 0 else 0
                
                # Use the maximum overlap percentage
                overlap_percentage = max(zone1_overlap_pct, zone2_overlap_pct)
                
                # Determine overlap type
                overlap_type = self._classify_overlap_type(
                    zone1_top, zone1_bottom, zone2_top, zone2_bottom, overlap_percentage
                )
                
                # Check ATR threshold
                atr_threshold_met = overlap_height <= atr_threshold
                
                # Determine if overlap is significant
                has_overlap = (overlap_percentage >= self.min_overlap_percentage and 
                             not atr_threshold_met)
                
                result = OverlapResult(
                    has_overlap=has_overlap,
                    overlap_type=overlap_type,
                    overlap_percentage=overlap_percentage,
                    overlap_area=overlap_height,
                    atr_threshold_met=atr_threshold_met,
                    overlap_bounds=(overlap_bottom, overlap_top)
                )
            
            # Cache the result
            if self.enable_caching:
                self._cache_overlap_result(zone1, zone2, result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in individual overlap check: {e}")
            return OverlapResult(
                has_overlap=False,
                overlap_type=OverlapType.NO_OVERLAP,
                overlap_percentage=0.0,
                overlap_area=0.0,
                atr_threshold_met=False
            )
    
    def _classify_overlap_type(self, zone1_top: float, zone1_bottom: float,
                              zone2_top: float, zone2_bottom: float,
                              overlap_percentage: float) -> OverlapType:
        """
        Classify the type of overlap between two zones
        
        Args:
            zone1_top: Top of first zone
            zone1_bottom: Bottom of first zone
            zone2_top: Top of second zone
            zone2_bottom: Bottom of second zone
            overlap_percentage: Calculated overlap percentage
            
        Returns:
            OverlapType classification
        """
        try:
            # Check for full overlap (same bounds) first
            if (abs(zone1_top - zone2_top) < 1e-8 and abs(zone1_bottom - zone2_bottom) < 1e-8):
                return OverlapType.FULL_OVERLAP
            
            # Check for full containment
            if (zone1_bottom >= zone2_bottom and zone1_top <= zone2_top):
                return OverlapType.CONTAINED  # zone1 is contained in zone2
            
            if (zone2_bottom >= zone1_bottom and zone2_top <= zone1_top):
                return OverlapType.CONTAINS  # zone1 contains zone2
            
            # Check overlap percentage thresholds
            if overlap_percentage >= 90.0:
                return OverlapType.FULL_OVERLAP
            elif overlap_percentage > 0.0:
                return OverlapType.PARTIAL_OVERLAP
            else:
                return OverlapType.NO_OVERLAP
                
        except Exception as e:
            logger.error(f"❌ Error classifying overlap type: {e}")
            return OverlapType.NO_OVERLAP
    
    def calculate_overlap_percentage(self, zone1: Zone, zone2: Zone) -> float:
        """
        Calculate percentage overlap between two zones
        
        Args:
            zone1: First zone
            zone2: Second zone
            
        Returns:
            Overlap percentage (0-100)
        """
        try:
            # Use the individual overlap check to get detailed results
            result = self._check_individual_overlap(zone1, zone2, float('inf'))
            return result.overlap_percentage
            
        except Exception as e:
            logger.error(f"❌ Error calculating overlap percentage: {e}")
            return 0.0
    
    def batch_overlap_check(self, zones: List[Zone], 
                           atr_values: Optional[Dict[str, float]] = None) -> Dict[str, List[OverlapResult]]:
        """
        Perform batch overlap checking for multiple zones
        
        Args:
            zones: List of zones to check for overlaps
            atr_values: Optional ATR values per zone
            
        Returns:
            Dictionary mapping zone IDs to their overlap results
        """
        try:
            overlap_results = {}
            
            for i, zone in enumerate(zones):
                zone_overlaps = []
                
                # Get ATR threshold for this zone
                atr_threshold = None
                if atr_values and zone.zone_id in atr_values:
                    atr_threshold = atr_values[zone.zone_id] * self.atr_multiplier
                
                # Check against all other zones
                other_zones = zones[:i] + zones[i+1:]
                
                if other_zones:
                    overlap_result = self.check_zone_overlap(zone, other_zones, atr_threshold)
                    zone_overlaps.append(overlap_result)
                
                overlap_results[zone.zone_id] = zone_overlaps
            
            logger.debug(f"📊 Batch overlap check completed for {len(zones)} zones")
            return overlap_results
            
        except Exception as e:
            logger.error(f"❌ Error in batch overlap check: {e}")
            return {}
    
    def find_overlapping_zones(self, zones: List[Zone], 
                              min_overlap_percentage: Optional[float] = None) -> List[Tuple[Zone, Zone, float]]:
        """
        Find all pairs of overlapping zones
        
        Args:
            zones: List of zones to analyze
            min_overlap_percentage: Minimum overlap percentage to consider
            
        Returns:
            List of tuples (zone1, zone2, overlap_percentage)
        """
        try:
            if min_overlap_percentage is None:
                min_overlap_percentage = self.min_overlap_percentage
            
            overlapping_pairs = []
            
            for i in range(len(zones)):
                for j in range(i + 1, len(zones)):
                    zone1, zone2 = zones[i], zones[j]
                    
                    overlap_result = self._check_individual_overlap(zone1, zone2, float('inf'))
                    
                    if (overlap_result.has_overlap and 
                        overlap_result.overlap_percentage >= min_overlap_percentage):
                        overlapping_pairs.append((zone1, zone2, overlap_result.overlap_percentage))
            
            # Sort by overlap percentage (highest first)
            overlapping_pairs.sort(key=lambda x: x[2], reverse=True)
            
            logger.debug(f"🔍 Found {len(overlapping_pairs)} overlapping zone pairs")
            return overlapping_pairs
            
        except Exception as e:
            logger.error(f"❌ Error finding overlapping zones: {e}")
            return []
    
    def resolve_overlaps(self, zones: List[Zone], 
                        resolution_strategy: str = "keep_strongest") -> List[Zone]:
        """
        Resolve overlapping zones using specified strategy
        
        Args:
            zones: List of zones with potential overlaps
            resolution_strategy: Strategy for resolving overlaps
                - "keep_strongest": Keep zone with highest strength/volume
                - "keep_newest": Keep most recently created zone
                - "keep_oldest": Keep oldest zone
                - "merge": Merge overlapping zones
            
        Returns:
            List of zones with overlaps resolved
        """
        try:
            if not zones:
                return []
            
            # Find overlapping pairs
            overlapping_pairs = self.find_overlapping_zones(zones)
            
            if not overlapping_pairs:
                return zones  # No overlaps to resolve
            
            # Track zones to remove
            zones_to_remove = set()
            
            for zone1, zone2, overlap_pct in overlapping_pairs:
                # Skip if either zone is already marked for removal
                if zone1.zone_id in zones_to_remove or zone2.zone_id in zones_to_remove:
                    continue
                
                if resolution_strategy == "keep_strongest":
                    # Keep zone with higher volume or strength
                    if hasattr(zone1, 'volume') and hasattr(zone2, 'volume'):
                        if zone1.volume < zone2.volume:
                            zones_to_remove.add(zone1.zone_id)
                        else:
                            zones_to_remove.add(zone2.zone_id)
                    else:
                        # Fallback to zone size
                        zone1_size = abs(zone1.top - zone1.bottom)
                        zone2_size = abs(zone2.top - zone2.bottom)
                        if zone1_size < zone2_size:
                            zones_to_remove.add(zone1.zone_id)
                        else:
                            zones_to_remove.add(zone2.zone_id)
                
                elif resolution_strategy == "keep_newest":
                    if zone1.created_at < zone2.created_at:
                        zones_to_remove.add(zone1.zone_id)
                    else:
                        zones_to_remove.add(zone2.zone_id)
                
                elif resolution_strategy == "keep_oldest":
                    if zone1.created_at > zone2.created_at:
                        zones_to_remove.add(zone1.zone_id)
                    else:
                        zones_to_remove.add(zone2.zone_id)
                
                elif resolution_strategy == "merge":
                    # Merge zones (keep zone1, remove zone2, expand zone1 bounds)
                    zone1.top = max(zone1.top, zone2.top)
                    zone1.bottom = min(zone1.bottom, zone2.bottom)
                    zones_to_remove.add(zone2.zone_id)
            
            # Filter out removed zones
            resolved_zones = [zone for zone in zones if zone.zone_id not in zones_to_remove]
            
            logger.info(f"🔧 Resolved {len(zones_to_remove)} overlapping zones using '{resolution_strategy}' strategy")
            return resolved_zones
            
        except Exception as e:
            logger.error(f"❌ Error resolving overlaps: {e}")
            return zones
    
    def _get_cached_overlap(self, zone1: Zone, zone2: Zone) -> Optional[OverlapCache]:
        """Get cached overlap result if available and valid"""
        try:
            cache_key = self._generate_cache_key(zone1, zone2)
            
            if cache_key in self._overlap_cache:
                cached_entry = self._overlap_cache[cache_key]
                
                # Check if cache entry is still valid
                if (datetime.now() - cached_entry.timestamp).total_seconds() < cached_entry.ttl_seconds:
                    return cached_entry
                else:
                    # Remove expired entry
                    del self._overlap_cache[cache_key]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting cached overlap: {e}")
            return None
    
    def _cache_overlap_result(self, zone1: Zone, zone2: Zone, result: OverlapResult) -> None:
        """Cache overlap result for future use"""
        try:
            # Check cache size limit
            if len(self._overlap_cache) >= self._cache_max_size:
                self._cleanup_cache()
            
            cache_key = self._generate_cache_key(zone1, zone2)
            
            cache_entry = OverlapCache(
                zone1_hash=self._generate_zone_hash(zone1),
                zone2_hash=self._generate_zone_hash(zone2),
                result=result,
                timestamp=datetime.now(),
                ttl_seconds=self._cache_ttl_seconds
            )
            
            self._overlap_cache[cache_key] = cache_entry
            
        except Exception as e:
            logger.error(f"❌ Error caching overlap result: {e}")
    
    def _generate_cache_key(self, zone1: Zone, zone2: Zone) -> str:
        """Generate cache key for two zones"""
        try:
            # Create deterministic key regardless of zone order
            hash1 = self._generate_zone_hash(zone1)
            hash2 = self._generate_zone_hash(zone2)
            
            # Sort hashes to ensure consistent key
            if hash1 < hash2:
                return f"{hash1}_{hash2}"
            else:
                return f"{hash2}_{hash1}"
                
        except Exception as e:
            logger.error(f"❌ Error generating cache key: {e}")
            return f"error_{time.time()}"
    
    def _generate_zone_hash(self, zone: Zone) -> str:
        """Generate hash for a zone based on its key properties"""
        try:
            # Create hash from zone's immutable properties
            zone_data = f"{zone.zone_type.value}_{zone.top}_{zone.bottom}_{zone.left_time}_{zone.right_time}"
            return hashlib.md5(zone_data.encode()).hexdigest()[:16]
            
        except Exception as e:
            logger.error(f"❌ Error generating zone hash: {e}")
            return f"error_{time.time()}"
    
    def _cleanup_cache(self) -> None:
        """Clean up expired cache entries"""
        try:
            current_time = datetime.now()
            expired_keys = []
            
            for key, entry in self._overlap_cache.items():
                if (current_time - entry.timestamp).total_seconds() > entry.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._overlap_cache[key]
            
            # If still too many entries, remove oldest ones
            if len(self._overlap_cache) >= self._cache_max_size:
                sorted_entries = sorted(
                    self._overlap_cache.items(),
                    key=lambda x: x[1].timestamp
                )
                
                # Remove oldest 25% of entries
                remove_count = len(sorted_entries) // 4
                for i in range(remove_count):
                    key = sorted_entries[i][0]
                    if key in self._overlap_cache:
                        del self._overlap_cache[key]
            
            logger.debug(f"🧹 Cache cleanup: removed {len(expired_keys)} expired entries")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up cache: {e}")
    
    def _update_stats(self, overlap_detected: bool, check_time_ms: float) -> None:
        """Update overlap detection statistics"""
        self._stats.total_checks += 1
        self._stats.avg_check_time_ms = check_time_ms
        self._stats.last_check_time = datetime.now()
        
        if overlap_detected:
            self._stats.overlaps_detected += 1
    
    def get_stats(self) -> OverlapStats:
        """Get overlap detection statistics"""
        with self._lock:
            # Calculate cache hit rate
            total_cache_requests = self._stats.cache_hits + self._stats.cache_misses
            cache_hit_rate = (self._stats.cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0
            
            # Add cache statistics to stats
            stats_copy = OverlapStats(
                total_checks=self._stats.total_checks,
                cache_hits=self._stats.cache_hits,
                cache_misses=self._stats.cache_misses,
                overlaps_detected=self._stats.overlaps_detected,
                avg_check_time_ms=self._stats.avg_check_time_ms,
                last_check_time=self._stats.last_check_time
            )
            
            return stats_copy
    
    def clear_cache(self) -> None:
        """Clear overlap detection cache"""
        with self._lock:
            self._overlap_cache.clear()
            logger.info(f"🗑️ Cleared overlap detection cache for {self.symbol}")
    
    def __repr__(self) -> str:
        """String representation of overlap checker"""
        return (f"OverlapChecker(symbol={self.symbol}, "
                f"cache_size={len(self._overlap_cache)}, "
                f"checks={self._stats.total_checks})")


# Factory function for creating overlap checkers
def get_overlap_checker(symbol: str, enable_caching: bool = True) -> OverlapChecker:
    """
    Factory function to get overlap checker instance
    
    Args:
        symbol: Trading symbol
        enable_caching: Whether to enable caching
        
    Returns:
        OverlapChecker instance
    """
    return OverlapChecker(symbol, enable_caching)