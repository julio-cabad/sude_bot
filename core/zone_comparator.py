#!/usr/bin/env python3
"""
🔥⚔️ ZONE COMPARATOR - IMPLACABLE ZONE DETECTION ⚔️🔥
Compares current zones with previous zones to detect new formations
Created by KRATOS - COMPARISON WARRIOR
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import logging
from dataclasses import dataclass
import hashlib

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.zone import Zone, ZoneType
from models.zone_alert import ZoneComparison

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ZoneSignature:
    """
    🎯 ZONE SIGNATURE - Unique zone identifier
    Used for comparing zones across different detections
    """
    poi_price: float
    zone_type: str
    formation_time: Optional[datetime]
    price_tolerance: float = 0.001  # 0.1% tolerance
    time_tolerance_minutes: int = 60  # 1 hour tolerance
    
    def matches(self, other: 'ZoneSignature') -> bool:
        """Check if this signature matches another"""
        # Check zone type
        if self.zone_type != other.zone_type:
            return False
        
        # Check POI price with tolerance
        price_diff_pct = abs(self.poi_price - other.poi_price) / self.poi_price
        if price_diff_pct > self.price_tolerance:
            return False
        
        # Check formation time if both have it
        if self.formation_time and other.formation_time:
            time_diff = abs((self.formation_time - other.formation_time).total_seconds())
            if time_diff > (self.time_tolerance_minutes * 60):
                return False
        
        return True
    
    def to_hash(self) -> str:
        """Generate hash for quick comparison"""
        # Round POI to reduce precision for comparison
        rounded_poi = round(self.poi_price, 2)
        time_str = self.formation_time.strftime('%Y-%m-%d %H') if self.formation_time else 'unknown'
        
        signature_str = f"{self.zone_type}_{rounded_poi}_{time_str}"
        return hashlib.md5(signature_str.encode()).hexdigest()[:8]


class ZoneComparator:
    """
    🔍 ZONE COMPARATOR - Implacable zone comparison engine
    Detects new zones by comparing current vs previous zone data
    """
    
    def __init__(self, price_tolerance: float = 0.001, 
                 time_tolerance_minutes: int = 60,
                 min_zone_age_minutes: int = 5):
        """
        Initialize zone comparator
        
        Args:
            price_tolerance: Price tolerance for zone matching (0.1% default)
            time_tolerance_minutes: Time tolerance for zone matching (60 min default)
            min_zone_age_minutes: Minimum age for a zone to be considered stable
        """
        self.price_tolerance = price_tolerance
        self.time_tolerance_minutes = time_tolerance_minutes
        self.min_zone_age_minutes = min_zone_age_minutes
        
        logger.info(f"🔍 ZoneComparator initialized:")
        logger.info(f"   Price tolerance: {price_tolerance*100:.1f}%")
        logger.info(f"   Time tolerance: {time_tolerance_minutes} minutes")
        logger.info(f"   Min zone age: {min_zone_age_minutes} minutes")
    
    def compare_zones(self, current_zones: Dict, previous_zones: Optional[Dict], 
                     symbol: str, timeframe: str) -> ZoneComparison:
        """
        Compare current zones with previous zones
        
        Args:
            current_zones: Current zone data from ImplacableZonesDetector
            previous_zones: Previous zone data (can be None)
            symbol: Trading symbol
            timeframe: Timeframe being monitored
            
        Returns:
            ZoneComparison: Comparison results with new zones identified
        """
        try:
            comparison_time = datetime.now()
            
            # Extract zones from data
            current_zone_list = self._extract_zones_from_data(current_zones)
            previous_zone_list = self._extract_zones_from_data(previous_zones) if previous_zones else []
            
            logger.debug(f"🔍 Comparing zones for {symbol}:")
            logger.debug(f"   Current zones: {len(current_zone_list)}")
            logger.debug(f"   Previous zones: {len(previous_zone_list)}")
            
            # Create zone signatures for comparison
            current_signatures = [self._create_zone_signature(zone) for zone in current_zone_list]
            previous_signatures = [self._create_zone_signature(zone) for zone in previous_zone_list]
            
            # Find new zones
            new_zones = self._find_new_zones(current_zone_list, current_signatures, previous_signatures)
            
            # Find removed zones (zones that were there before but not now)
            removed_zones = self._find_removed_zones(previous_zone_list, previous_signatures, current_signatures)
            
            # Find unchanged zones
            unchanged_zones = self._find_unchanged_zones(current_zone_list, current_signatures, previous_signatures)
            
            # Filter new zones by age (only include stable zones)
            stable_new_zones = self._filter_zones_by_age(new_zones)
            
            # Create comparison result
            comparison = ZoneComparison(
                symbol=symbol,
                timeframe=timeframe,
                comparison_time=comparison_time,
                previous_count=len(previous_zone_list),
                current_count=len(current_zone_list),
                new_zones=stable_new_zones,
                removed_zones=removed_zones,
                unchanged_zones=unchanged_zones
            )
            
            logger.debug(f"🎯 Comparison complete for {symbol}:")
            logger.debug(f"   New zones: {len(stable_new_zones)}")
            logger.debug(f"   Removed zones: {len(removed_zones)}")
            logger.debug(f"   Unchanged zones: {len(unchanged_zones)}")
            
            return comparison
            
        except Exception as e:
            logger.error(f"❌ Failed to compare zones for {symbol}: {e}")
            # Return empty comparison on error
            return ZoneComparison(
                symbol=symbol,
                timeframe=timeframe,
                comparison_time=datetime.now(),
                previous_count=0,
                current_count=0,
                new_zones=[]
            )
    
    def _extract_zones_from_data(self, zones_data: Optional[Dict]) -> List[Zone]:
        """Extract Zone objects from zone data dictionary"""
        if not zones_data:
            return []
        
        zones = []
        
        try:
            # Extract supply zones
            supply_zones = zones_data.get('supply', [])
            for zone_data in supply_zones:
                zone = self._create_zone_from_data(zone_data, ZoneType.SUPPLY)
                if zone:
                    zones.append(zone)
            
            # Extract demand zones
            demand_zones = zones_data.get('demand', [])
            for zone_data in demand_zones:
                zone = self._create_zone_from_data(zone_data, ZoneType.DEMAND)
                if zone:
                    zones.append(zone)
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract zones from data: {e}")
        
        return zones
    
    def _create_zone_from_data(self, zone_data: Dict, zone_type: ZoneType) -> Optional[Zone]:
        """Create Zone object from zone data dictionary"""
        try:
            # Parse formation date
            formation_date = datetime.now()
            if 'formation_date' in zone_data:
                try:
                    formation_date = datetime.strptime(zone_data['formation_date'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Try alternative format
                    try:
                        formation_date = datetime.fromisoformat(zone_data['formation_date'])
                    except ValueError:
                        logger.warning(f"⚠️ Could not parse formation date: {zone_data['formation_date']}")
            
            # Extract zone properties
            top = float(zone_data.get('top', zone_data.get('poi', 0)))
            bottom = float(zone_data.get('bottom', zone_data.get('poi', 0)))
            poi = float(zone_data.get('poi', 0))
            
            # Calculate ATR buffer from zone height
            atr_buffer = abs(top - bottom)
            
            # Create Zone object using the correct constructor
            zone = Zone(
                zone_id="",  # Will be auto-generated
                zone_type=zone_type,
                top=top,
                bottom=bottom,
                poi=poi,
                left_time=formation_date,
                right_time=formation_date,
                left_bar_index=0,  # Default value
                right_bar_index=0,  # Default value
                atr_buffer=atr_buffer,
                swing_price=poi,  # Use POI as swing price
                is_active=True,
                is_broken=False
            )
            
            return zone
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to create zone from data: {e}")
            return None
    
    def _create_zone_signature(self, zone: Zone) -> ZoneSignature:
        """Create signature for a zone"""
        return ZoneSignature(
            poi_price=float(zone.poi),
            zone_type=zone.zone_type.name,  # Use .name instead of .value
            formation_time=zone.left_time,  # Use left_time instead of timestamp
            price_tolerance=self.price_tolerance,
            time_tolerance_minutes=self.time_tolerance_minutes
        )
    
    def _find_new_zones(self, current_zones: List[Zone], 
                       current_signatures: List[ZoneSignature],
                       previous_signatures: List[ZoneSignature]) -> List[Zone]:
        """Find zones that are new (not in previous detection)"""
        new_zones = []
        
        for i, current_sig in enumerate(current_signatures):
            is_new = True
            
            # Check if this zone matches any previous zone
            for prev_sig in previous_signatures:
                if current_sig.matches(prev_sig):
                    is_new = False
                    break
            
            if is_new:
                new_zones.append(current_zones[i])
        
        return new_zones
    
    def _find_removed_zones(self, previous_zones: List[Zone],
                           previous_signatures: List[ZoneSignature],
                           current_signatures: List[ZoneSignature]) -> List[Zone]:
        """Find zones that were removed (were there before but not now)"""
        removed_zones = []
        
        for i, prev_sig in enumerate(previous_signatures):
            is_removed = True
            
            # Check if this zone still exists in current detection
            for current_sig in current_signatures:
                if prev_sig.matches(current_sig):
                    is_removed = False
                    break
            
            if is_removed:
                removed_zones.append(previous_zones[i])
        
        return removed_zones
    
    def _find_unchanged_zones(self, current_zones: List[Zone],
                             current_signatures: List[ZoneSignature],
                             previous_signatures: List[ZoneSignature]) -> List[Zone]:
        """Find zones that remain unchanged"""
        unchanged_zones = []
        
        for i, current_sig in enumerate(current_signatures):
            # Check if this zone matches any previous zone
            for prev_sig in previous_signatures:
                if current_sig.matches(prev_sig):
                    unchanged_zones.append(current_zones[i])
                    break
        
        return unchanged_zones
    
    def _filter_zones_by_age(self, zones: List[Zone]) -> List[Zone]:
        """Filter zones by minimum age to ensure stability"""
        if self.min_zone_age_minutes <= 0:
            return zones
        
        stable_zones = []
        min_age = timedelta(minutes=self.min_zone_age_minutes)
        current_time = datetime.now()
        
        for zone in zones:
            if zone.left_time:  # Use left_time instead of timestamp
                age = current_time - zone.left_time
                if age >= min_age:
                    stable_zones.append(zone)
                else:
                    logger.debug(f"🕐 Zone too young, skipping: {zone.poi} (age: {age.total_seconds():.0f}s)")
            else:
                # If no timestamp, assume it's stable
                stable_zones.append(zone)
        
        return stable_zones
    
    def is_zone_new(self, zone: Zone, existing_zones: List[Zone]) -> bool:
        """
        Check if a zone is new compared to existing zones
        
        Args:
            zone: Zone to check
            existing_zones: List of existing zones
            
        Returns:
            bool: True if zone is new
        """
        try:
            zone_signature = self._create_zone_signature(zone)
            
            for existing_zone in existing_zones:
                existing_signature = self._create_zone_signature(existing_zone)
                if zone_signature.matches(existing_signature):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to check if zone is new: {e}")
            return False
    
    def get_zone_signature(self, zone: Zone) -> str:
        """
        Get unique signature string for a zone
        
        Args:
            zone: Zone object
            
        Returns:
            str: Unique signature string
        """
        try:
            signature = self._create_zone_signature(zone)
            return signature.to_hash()
        except Exception as e:
            logger.error(f"❌ Failed to get zone signature: {e}")
            return "unknown"
    
    def get_comparison_stats(self, comparison: ZoneComparison) -> Dict:
        """Get detailed statistics from a comparison"""
        try:
            new_supply_count = sum(1 for zone in comparison.new_zones if zone.zone_type == ZoneType.SUPPLY)
            new_demand_count = sum(1 for zone in comparison.new_zones if zone.zone_type == ZoneType.DEMAND)
            
            removed_supply_count = sum(1 for zone in comparison.removed_zones if zone.zone_type == ZoneType.SUPPLY)
            removed_demand_count = sum(1 for zone in comparison.removed_zones if zone.zone_type == ZoneType.DEMAND)
            
            return {
                'total_new_zones': len(comparison.new_zones),
                'new_supply_zones': new_supply_count,
                'new_demand_zones': new_demand_count,
                'total_removed_zones': len(comparison.removed_zones),
                'removed_supply_zones': removed_supply_count,
                'removed_demand_zones': removed_demand_count,
                'unchanged_zones': len(comparison.unchanged_zones),
                'net_zone_change': len(comparison.new_zones) - len(comparison.removed_zones),
                'comparison_time': comparison.comparison_time.isoformat(),
                'has_significant_changes': len(comparison.new_zones) > 0 or len(comparison.removed_zones) > 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get comparison stats: {e}")
            return {
                'total_new_zones': 0,
                'new_supply_zones': 0,
                'new_demand_zones': 0,
                'total_removed_zones': 0,
                'removed_supply_zones': 0,
                'removed_demand_zones': 0,
                'unchanged_zones': 0,
                'net_zone_change': 0,
                'comparison_time': datetime.now().isoformat(),
                'has_significant_changes': False
            }
    
    def set_tolerance(self, price_tolerance: Optional[float] = None,
                     time_tolerance_minutes: Optional[int] = None) -> None:
        """Update comparison tolerances"""
        if price_tolerance is not None:
            self.price_tolerance = price_tolerance
            logger.info(f"🔧 Updated price tolerance: {price_tolerance*100:.1f}%")
        
        if time_tolerance_minutes is not None:
            self.time_tolerance_minutes = time_tolerance_minutes
            logger.info(f"🔧 Updated time tolerance: {time_tolerance_minutes} minutes")


# Utility functions
def create_zone_comparator(price_tolerance: float = 0.001) -> ZoneComparator:
    """Factory function to create ZoneComparator with default settings"""
    return ZoneComparator(price_tolerance=price_tolerance)


def quick_zone_comparison(current_zones: Dict, previous_zones: Optional[Dict],
                         symbol: str = "UNKNOWN") -> bool:
    """
    Quick comparison to check if there are any new zones
    
    Returns:
        bool: True if there are new zones
    """
    try:
        comparator = ZoneComparator()
        comparison = comparator.compare_zones(current_zones, previous_zones, symbol, "unknown")
        return len(comparison.new_zones) > 0
    except Exception:
        return False


if __name__ == "__main__":
    # Test the comparator
    print("🔥⚔️ TESTING ZONE COMPARATOR ⚔️🔥")
    print("=" * 60)
    
    # Create test comparator
    comparator = ZoneComparator()
    
    # Test data
    current_zones = {
        'supply': [
            {
                'name': 'supply_1',
                'poi': 67500.0,
                'top': 67600.0,
                'bottom': 67400.0,
                'formation_date': '2024-01-01 12:00:00',
                'strength': 2.0
            }
        ],
        'demand': [
            {
                'name': 'demand_1',
                'poi': 66500.0,
                'top': 66600.0,
                'bottom': 66400.0,
                'formation_date': '2024-01-01 11:00:00',
                'strength': 1.5
            }
        ]
    }
    
    previous_zones = {
        'supply': [],
        'demand': [
            {
                'name': 'demand_old',
                'poi': 66000.0,
                'top': 66100.0,
                'bottom': 65900.0,
                'formation_date': '2024-01-01 10:00:00',
                'strength': 1.0
            }
        ]
    }
    
    # Test comparison
    print("✅ Testing zone comparison...")
    comparison = comparator.compare_zones(current_zones, previous_zones, "BTCUSDT", "1h")
    
    print(f"   New zones found: {len(comparison.new_zones)}")
    print(f"   Removed zones: {len(comparison.removed_zones)}")
    print(f"   Has changes: {comparison.has_changes()}")
    
    # Test stats
    stats = comparator.get_comparison_stats(comparison)
    print(f"   Comparison stats: {stats}")
    
    # Test quick comparison
    has_new = quick_zone_comparison(current_zones, previous_zones)
    print(f"   Quick check - has new zones: {has_new}")
    
    print("\n🏆 ZONE COMPARATOR READY FOR BATTLE! 🏆")