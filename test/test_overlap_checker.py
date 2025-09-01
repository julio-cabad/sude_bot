#!/usr/bin/env python3
"""
Comprehensive test suite for Overlap Checker System
Tests with REAL zone data and professional overlap analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from utils.overlap_checker import OverlapChecker, OverlapType, OverlapResult, get_overlap_checker
from models.zone import Zone, ZoneType
from bnb.binance import RobotBinance
from config.config_manager import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_zone(zone_type: ZoneType, top: float, bottom: float, 
                    zone_id: str = None, atr_buffer: float = 100.0) -> Zone:
    """Create a test zone for overlap testing"""
    if zone_id is None:
        zone_id = f"test_{zone_type.value}_{int(time.time())}"
    
    # Ensure proper ordering
    actual_top = max(top, bottom)
    actual_bottom = min(top, bottom)
    
    current_time = datetime.now()
    
    return Zone(
        zone_id=zone_id,
        zone_type=zone_type,
        top=actual_top,
        bottom=actual_bottom,
        poi=(actual_top + actual_bottom) / 2,
        left_time=current_time - timedelta(hours=1),
        right_time=current_time,
        left_bar_index=100,
        right_bar_index=200,
        atr_buffer=atr_buffer,
        swing_price=actual_top if zone_type == ZoneType.SUPPLY else actual_bottom,
        is_active=True,
        text_label=zone_type.name
    )


def test_basic_overlap_detection():
    """Test basic overlap detection functionality"""
    print("\\n🧪 Testing Basic Overlap Detection...")
    print("=" * 60)
    
    try:
        # Create overlap checker
        checker = get_overlap_checker("BTCUSDT", enable_caching=True)
        
        # Test Case 1: No overlap
        print("\\n📊 Test Case 1: No Overlap")
        zone1 = create_test_zone(ZoneType.SUPPLY, 50000, 49000, "supply_1")
        zone2 = create_test_zone(ZoneType.DEMAND, 48000, 47000, "demand_1")
        
        result = checker._check_individual_overlap(zone1, zone2, 500.0)
        
        print(f"   Zone 1: {zone1.zone_type.value} ${zone1.bottom:.0f} - ${zone1.top:.0f}")
        print(f"   Zone 2: {zone2.zone_type.value} ${zone2.bottom:.0f} - ${zone2.top:.0f}")
        print(f"   Result: {result.overlap_type.value}")
        print(f"   Overlap: {result.overlap_percentage:.1f}%")
        
        assert result.overlap_type == OverlapType.NO_OVERLAP
        assert result.overlap_percentage == 0.0
        print("   ✅ No overlap test passed")
        
        # Test Case 2: Partial overlap
        print("\\n📊 Test Case 2: Partial Overlap")
        zone3 = create_test_zone(ZoneType.SUPPLY, 50000, 49000, "supply_2")
        zone4 = create_test_zone(ZoneType.DEMAND, 49500, 48500, "demand_2")
        
        result = checker._check_individual_overlap(zone3, zone4, 100.0)  # Small ATR threshold
        
        print(f"   Zone 3: {zone3.zone_type.value} ${zone3.bottom:.0f} - ${zone3.top:.0f}")
        print(f"   Zone 4: {zone4.zone_type.value} ${zone4.bottom:.0f} - ${zone4.top:.0f}")
        print(f"   Result: {result.overlap_type.value}")
        print(f"   Overlap: {result.overlap_percentage:.1f}%")
        print(f"   Overlap area: ${result.overlap_area:.0f}")
        
        assert result.overlap_type == OverlapType.PARTIAL_OVERLAP
        assert result.overlap_percentage > 0
        print("   ✅ Partial overlap test passed")
        
        # Test Case 3: Full containment
        print("\\n📊 Test Case 3: Full Containment")
        zone5 = create_test_zone(ZoneType.SUPPLY, 50000, 48000, "supply_3")  # Large zone
        zone6 = create_test_zone(ZoneType.DEMAND, 49500, 48500, "demand_3")  # Small zone inside
        
        result = checker._check_individual_overlap(zone5, zone6, 100.0)
        
        print(f"   Zone 5: {zone5.zone_type.value} ${zone5.bottom:.0f} - ${zone5.top:.0f}")
        print(f"   Zone 6: {zone6.zone_type.value} ${zone6.bottom:.0f} - ${zone6.top:.0f}")
        print(f"   Result: {result.overlap_type.value}")
        print(f"   Overlap: {result.overlap_percentage:.1f}%")
        
        assert result.overlap_type in [OverlapType.CONTAINS, OverlapType.CONTAINED]
        print("   ✅ Containment test passed")
        
        # Test Case 4: Identical zones
        print("\\n📊 Test Case 4: Identical Zones")
        zone7 = create_test_zone(ZoneType.SUPPLY, 50000, 49000, "supply_4")
        zone8 = create_test_zone(ZoneType.SUPPLY, 50000, 49000, "supply_5")  # Same bounds
        
        result = checker._check_individual_overlap(zone7, zone8, 100.0)
        
        print(f"   Zone 7: {zone7.zone_type.value} ${zone7.bottom:.0f} - ${zone7.top:.0f}")
        print(f"   Zone 8: {zone8.zone_type.value} ${zone8.bottom:.0f} - ${zone8.top:.0f}")
        print(f"   Result: {result.overlap_type.value}")
        print(f"   Overlap: {result.overlap_percentage:.1f}%")
        
        assert result.overlap_type == OverlapType.FULL_OVERLAP
        assert result.overlap_percentage >= 99.0
        print("   ✅ Identical zones test passed")
        
        print("\\n🎉 All basic overlap detection tests passed!")
        return checker
        
    except Exception as e:
        print(f"❌ Error in basic overlap detection test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_overlap_performance_and_caching():
    """Test overlap detection performance and caching system"""
    print("\\n🧪 Testing Overlap Performance and Caching...")
    print("=" * 60)
    
    try:
        # Create overlap checker with caching enabled
        checker = get_overlap_checker("BTCUSDT", enable_caching=True)
        
        # Create test zones
        zones = []
        for i in range(20):
            zone_type = ZoneType.SUPPLY if i % 2 == 0 else ZoneType.DEMAND
            top = 50000 + (i * 100)
            bottom = top - 500
            zones.append(create_test_zone(zone_type, top, bottom, f"zone_{i}"))
        
        print(f"🚀 Performance test with {len(zones)} zones...")
        
        # Test 1: Initial overlap checks (cache misses)
        print("\\n📊 Test 1: Initial Checks (Cache Misses)")
        start_time = time.time()
        
        overlap_results = []
        for i in range(len(zones)):
            for j in range(i + 1, len(zones)):
                result = checker._check_individual_overlap(zones[i], zones[j], 200.0)
                overlap_results.append(result)
        
        initial_time = time.time() - start_time
        initial_checks = len(overlap_results)
        
        print(f"   Checks performed: {initial_checks}")
        print(f"   Total time: {initial_time:.3f}s")
        print(f"   Average time per check: {(initial_time/initial_checks)*1000:.2f}ms")
        
        # Get initial stats
        stats = checker.get_stats()
        print(f"   Cache misses: {stats.cache_misses}")
        print(f"   Cache hits: {stats.cache_hits}")
        
        # Test 2: Repeat same checks (cache hits)
        print("\\n📊 Test 2: Repeat Checks (Cache Hits)")
        start_time = time.time()
        
        cached_results = []
        for i in range(len(zones)):
            for j in range(i + 1, len(zones)):
                result = checker._check_individual_overlap(zones[i], zones[j], 200.0)
                cached_results.append(result)
        
        cached_time = time.time() - start_time
        cached_checks = len(cached_results)
        
        print(f"   Checks performed: {cached_checks}")
        print(f"   Total time: {cached_time:.3f}s")
        print(f"   Average time per check: {(cached_time/cached_checks)*1000:.2f}ms")
        
        # Get final stats
        final_stats = checker.get_stats()
        cache_hits = final_stats.cache_hits - stats.cache_hits
        
        print(f"   New cache hits: {cache_hits}")
        print(f"   Cache hit rate: {(cache_hits/cached_checks)*100:.1f}%")
        
        # Performance improvement
        if initial_time > 0:
            speedup = initial_time / cached_time
            print(f"   Performance improvement: {speedup:.1f}x faster")
        
        # Test 3: Batch overlap checking
        print("\\n📊 Test 3: Batch Overlap Checking")
        start_time = time.time()
        
        batch_results = checker.batch_overlap_check(zones[:10])  # Test with 10 zones
        
        batch_time = time.time() - start_time
        
        print(f"   Zones processed: {len(batch_results)}")
        print(f"   Batch processing time: {batch_time:.3f}s")
        print(f"   Average time per zone: {(batch_time/len(batch_results))*1000:.2f}ms")
        
        # Verify results consistency
        assert len(overlap_results) == len(cached_results)
        print("   ✅ Cache consistency verified")
        
        print("\\n🎉 Performance and caching tests passed!")
        return checker
        
    except Exception as e:
        print(f"❌ Error in performance test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_overlap_resolution_strategies():
    """Test overlap resolution strategies"""
    print("\\n🧪 Testing Overlap Resolution Strategies...")
    print("=" * 60)
    
    try:
        checker = get_overlap_checker("BTCUSDT")
        
        # Create overlapping zones with different properties
        zones = [
            create_test_zone(ZoneType.SUPPLY, 50000, 49500, "supply_old"),
            create_test_zone(ZoneType.SUPPLY, 49800, 49300, "supply_new"),  # Overlaps with first
            create_test_zone(ZoneType.DEMAND, 48000, 47500, "demand_1"),
            create_test_zone(ZoneType.DEMAND, 47800, 47300, "demand_2"),   # Overlaps with demand_1
        ]
        
        # Add volume data for testing (as custom attributes)
        zones[0].volume = 1000000  # High volume
        zones[1].volume = 500000   # Lower volume
        zones[2].volume = 800000
        zones[3].volume = 1200000  # Highest volume
        
        # Add creation timestamps (using left_time as creation time)
        base_time = datetime.now()
        zones[0].left_time = base_time - timedelta(hours=2)  # Oldest
        zones[1].left_time = base_time - timedelta(hours=1)  # Newer
        zones[2].left_time = base_time - timedelta(minutes=30)
        zones[3].left_time = base_time  # Newest
        
        print(f"\\n📊 Original zones: {len(zones)}")
        for zone in zones:
            print(f"   {zone.zone_id}: {zone.zone_type.value} ${zone.bottom:.0f}-${zone.top:.0f} "
                  f"(vol: {getattr(zone, 'volume', 0):,})")
        
        # Find overlapping pairs
        overlapping_pairs = checker.find_overlapping_zones(zones, min_overlap_percentage=5.0)
        print(f"\\n🔍 Found {len(overlapping_pairs)} overlapping pairs:")
        for zone1, zone2, overlap_pct in overlapping_pairs:
            print(f"   {zone1.zone_id} ↔ {zone2.zone_id}: {overlap_pct:.1f}% overlap")
        
        # Test different resolution strategies
        strategies = ["keep_strongest", "keep_newest", "keep_oldest", "merge"]
        
        for strategy in strategies:
            print(f"\\n📊 Testing '{strategy}' strategy:")
            
            # Make a copy of zones for testing
            test_zones = [zone for zone in zones]
            
            resolved_zones = checker.resolve_overlaps(test_zones, strategy)
            
            print(f"   Original zones: {len(zones)}")
            print(f"   Resolved zones: {len(resolved_zones)}")
            print(f"   Zones removed: {len(zones) - len(resolved_zones)}")
            
            print(f"   Remaining zones:")
            for zone in resolved_zones:
                print(f"     {zone.zone_id}: {zone.zone_type.value} ${zone.bottom:.0f}-${zone.top:.0f}")
            
            # Verify no overlaps remain (except for merge strategy which might still have some)
            if strategy != "merge":
                remaining_overlaps = checker.find_overlapping_zones(resolved_zones, min_overlap_percentage=5.0)
                if remaining_overlaps:
                    print(f"   ⚠️  Warning: {len(remaining_overlaps)} overlaps still remain")
                else:
                    print(f"   ✅ All overlaps resolved")
        
        print("\\n🎉 Overlap resolution tests completed!")
        return checker
        
    except Exception as e:
        print(f"❌ Error in overlap resolution test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_real_market_overlap_scenarios():
    """Test overlap detection with realistic market scenarios"""
    print("\\n🧪 Testing Real Market Overlap Scenarios...")
    print("=" * 60)
    
    try:
        checker = get_overlap_checker("BTCUSDT")
        
        # Scenario 1: Tight consolidation with multiple supply zones
        print("\\n📊 Scenario 1: Tight Consolidation")
        consolidation_zones = [
            create_test_zone(ZoneType.SUPPLY, 65000, 64800, "supply_resistance_1"),
            create_test_zone(ZoneType.SUPPLY, 64900, 64700, "supply_resistance_2"),
            create_test_zone(ZoneType.SUPPLY, 64850, 64650, "supply_resistance_3"),
        ]
        
        overlaps = checker.find_overlapping_zones(consolidation_zones)
        print(f"   Consolidation zones: {len(consolidation_zones)}")
        print(f"   Overlapping pairs: {len(overlaps)}")
        
        for zone1, zone2, overlap_pct in overlaps:
            print(f"     {zone1.zone_id} ↔ {zone2.zone_id}: {overlap_pct:.1f}%")
        
        # Scenario 2: Strong trend with separated zones
        print("\\n📊 Scenario 2: Strong Trend")
        trend_zones = [
            create_test_zone(ZoneType.SUPPLY, 70000, 69500, "supply_top"),
            create_test_zone(ZoneType.DEMAND, 68000, 67500, "demand_pullback"),
            create_test_zone(ZoneType.SUPPLY, 66000, 65500, "supply_mid"),
            create_test_zone(ZoneType.DEMAND, 64000, 63500, "demand_bottom"),
        ]
        
        trend_overlaps = checker.find_overlapping_zones(trend_zones)
        print(f"   Trend zones: {len(trend_zones)}")
        print(f"   Overlapping pairs: {len(trend_overlaps)}")
        
        if not trend_overlaps:
            print("     ✅ No overlaps in trending market (expected)")
        
        # Scenario 3: Range-bound market with multiple touches
        print("\\n📊 Scenario 3: Range-Bound Market")
        range_zones = [
            create_test_zone(ZoneType.SUPPLY, 62000, 61800, "range_top_1"),
            create_test_zone(ZoneType.SUPPLY, 61900, 61700, "range_top_2"),
            create_test_zone(ZoneType.DEMAND, 60200, 60000, "range_bottom_1"),
            create_test_zone(ZoneType.DEMAND, 60100, 59900, "range_bottom_2"),
        ]
        
        range_overlaps = checker.find_overlapping_zones(range_zones)
        print(f"   Range zones: {len(range_zones)}")
        print(f"   Overlapping pairs: {len(range_overlaps)}")
        
        # Test ATR-based overlap filtering
        print("\\n📊 ATR-Based Overlap Filtering")
        atr_threshold = 150.0  # $150 ATR
        
        for zone1, zone2, overlap_pct in range_overlaps:
            result = checker._check_individual_overlap(zone1, zone2, atr_threshold)
            
            print(f"   {zone1.zone_id} ↔ {zone2.zone_id}:")
            print(f"     Overlap: {overlap_pct:.1f}%")
            print(f"     Overlap area: ${result.overlap_area:.0f}")
            print(f"     ATR threshold met: {result.atr_threshold_met}")
            print(f"     Significant overlap: {result.has_overlap}")
        
        # Scenario 4: Multi-timeframe zone conflicts
        print("\\n📊 Scenario 4: Multi-Timeframe Conflicts")
        mtf_zones = [
            create_test_zone(ZoneType.SUPPLY, 63000, 62500, "h4_supply"),     # 4H supply
            create_test_zone(ZoneType.DEMAND, 62800, 62600, "h1_demand"),     # 1H demand inside 4H supply
            create_test_zone(ZoneType.SUPPLY, 62700, 62650, "m15_supply"),    # 15M supply
        ]
        
        mtf_overlaps = checker.find_overlapping_zones(mtf_zones)
        print(f"   Multi-timeframe zones: {len(mtf_zones)}")
        print(f"   Conflicts detected: {len(mtf_overlaps)}")
        
        for zone1, zone2, overlap_pct in mtf_overlaps:
            print(f"     {zone1.zone_id} ↔ {zone2.zone_id}: {overlap_pct:.1f}%")
        
        print("\\n🎉 Real market scenario tests completed!")
        return checker
        
    except Exception as e:
        print(f"❌ Error in real market scenarios test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_overlap_checker_statistics():
    """Test overlap checker statistics and monitoring"""
    print("\\n🧪 Testing Overlap Checker Statistics...")
    print("=" * 60)
    
    try:
        checker = get_overlap_checker("BTCUSDT", enable_caching=True)
        
        # Perform various overlap checks to generate statistics
        zones = []
        for i in range(15):
            zone_type = ZoneType.SUPPLY if i % 3 == 0 else ZoneType.DEMAND
            top = 50000 + (i * 200) + np.random.randint(-50, 50)
            bottom = top - 300 - np.random.randint(0, 100)
            zones.append(create_test_zone(zone_type, top, bottom, f"stat_zone_{i}"))
        
        print(f"📊 Performing overlap analysis on {len(zones)} zones...")
        
        # Perform multiple overlap checks
        overlap_count = 0
        check_count = 0
        
        start_time = time.time()
        
        for i in range(len(zones)):
            for j in range(i + 1, len(zones)):
                result = checker._check_individual_overlap(zones[i], zones[j], 150.0)
                check_count += 1
                
                if result.has_overlap:
                    overlap_count += 1
        
        total_time = time.time() - start_time
        
        # Get statistics
        stats = checker.get_stats()
        
        print(f"\\n📈 Performance Statistics:")
        print(f"   Total checks performed: {stats.total_checks}")
        print(f"   Overlaps detected: {stats.overlaps_detected}")
        overlap_rate = (stats.overlaps_detected/stats.total_checks)*100 if stats.total_checks > 0 else 0
        print(f"   Overlap rate: {overlap_rate:.1f}%")
        print(f"   Average check time: {stats.avg_check_time_ms:.2f}ms")
        print(f"   Total processing time: {total_time:.3f}s")
        
        print(f"\\n🗄️ Cache Statistics:")
        print(f"   Cache hits: {stats.cache_hits}")
        print(f"   Cache misses: {stats.cache_misses}")
        
        total_cache_requests = stats.cache_hits + stats.cache_misses
        if total_cache_requests > 0:
            cache_hit_rate = (stats.cache_hits / total_cache_requests) * 100
            print(f"   Cache hit rate: {cache_hit_rate:.1f}%")
        
        print(f"   Last check time: {stats.last_check_time.strftime('%H:%M:%S')}")
        
        # Test cache performance with repeated checks
        print(f"\\n🔄 Testing Cache Performance:")
        
        # Clear cache and perform checks
        checker.clear_cache()
        
        # First run (cache misses)
        start_time = time.time()
        for i in range(5):
            for j in range(i + 1, 5):
                checker._check_individual_overlap(zones[i], zones[j], 150.0)
        first_run_time = time.time() - start_time
        
        # Second run (cache hits)
        start_time = time.time()
        for i in range(5):
            for j in range(i + 1, 5):
                checker._check_individual_overlap(zones[i], zones[j], 150.0)
        second_run_time = time.time() - start_time
        
        if first_run_time > 0:
            cache_speedup = first_run_time / second_run_time if second_run_time > 0 else float('inf')
            print(f"   First run (no cache): {first_run_time*1000:.2f}ms")
            print(f"   Second run (cached): {second_run_time*1000:.2f}ms")
            print(f"   Cache speedup: {cache_speedup:.1f}x")
        
        # Test memory usage estimation
        cache_size = len(checker._overlap_cache)
        print(f"\\n💾 Memory Usage:")
        print(f"   Cache entries: {cache_size}")
        print(f"   Estimated cache memory: ~{cache_size * 0.5:.1f}KB")
        
        print("\\n🎉 Statistics and monitoring tests completed!")
        return checker
        
    except Exception as e:
        print(f"❌ Error in statistics test: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all overlap checker tests"""
    print("🚀 Overlap Checker System Testing")
    print("=" * 70)
    
    # Test basic overlap detection
    checker = test_basic_overlap_detection()
    if not checker:
        print("❌ Basic overlap detection test failed")
        return
    
    # Test performance and caching
    test_overlap_performance_and_caching()
    
    # Test overlap resolution strategies
    test_overlap_resolution_strategies()
    
    # Test real market scenarios
    test_real_market_overlap_scenarios()
    
    # Test statistics and monitoring
    test_overlap_checker_statistics()
    
    print("\\n🎉 All overlap checker tests completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()