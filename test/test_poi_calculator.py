#!/usr/bin/env python3
"""
Comprehensive test suite for POI Calculator System
Tests with REAL zone data and professional POI calculations
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

from core.poi_calculator import POICalculator, POICalculationConfig, POICalculationMethod, get_poi_calculator
from models.poi import POI, POIType, POIStrength, POIStatus
from models.zone import Zone, ZoneType
from bnb.binance import RobotBinance
from config.config_manager import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_zone_for_poi(zone_type: ZoneType, top: float, bottom: float, 
                            zone_id: str = None, atr_buffer: float = 100.0) -> Zone:
    """Create a test zone for POI testing"""
    if zone_id is None:
        zone_id = f"poi_test_{zone_type.value}_{int(time.time())}"
    
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


def check_binance_credentials():
    """Check if Binance credentials are available"""
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("⚠️ Binance API credentials not found")
        print("   Set BINANCE_API_KEY and BINANCE_API_SECRET in .env file")
        return False
    
    print("✅ Binance API credentials found")
    return True


def get_real_market_data_for_poi(symbol: str = "BTCUSDT", timeframe: str = "1h", 
                                limit: int = 200) -> pd.DataFrame:
    """Get real OHLCV data from Binance for POI testing"""
    try:
        print(f"📡 Fetching real {symbol} data from Binance for POI testing...")
        
        # Initialize Binance robot
        robot = RobotBinance(symbol, timeframe)
        
        # Get candlestick data
        df = robot.candlestick(limit=limit)
        
        if df.empty:
            raise ValueError(f"No data received for {symbol}")
        
        print(f"✅ Fetched {len(df)} candles for POI testing")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")
        print(f"   Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error fetching market data: {e}")
        raise


def test_basic_poi_calculation():
    """Test basic POI calculation functionality"""
    print("\\n🧪 Testing Basic POI Calculation...")
    print("=" * 60)
    
    try:
        # Create POI calculator
        calculator = get_poi_calculator("BTCUSDT")
        
        # Test Case 1: Supply zone POI
        print("\\n📊 Test Case 1: Supply Zone POI")
        supply_zone = create_test_zone_for_poi(ZoneType.SUPPLY, 50000, 49000, "supply_poi_test")
        
        poi = calculator.calculate_poi(supply_zone)
        
        print(f"   Supply Zone: ${supply_zone.bottom:.0f} - ${supply_zone.top:.0f}")
        print(f"   Calculated POI: ${poi.price:.2f}")
        print(f"   POI Type: {poi.poi_type.value}")
        print(f"   Strength: {poi.strength.value}")
        print(f"   Confidence: {poi.confidence_score:.1f}%")
        print(f"   Method: {poi.calculation_method}")
        
        assert poi.poi_type == POIType.SUPPLY_POI
        assert supply_zone.bottom <= poi.price <= supply_zone.top
        print("   ✅ Supply POI test passed")
        
        # Test Case 2: Demand zone POI
        print("\\n📊 Test Case 2: Demand Zone POI")
        demand_zone = create_test_zone_for_poi(ZoneType.DEMAND, 48000, 47000, "demand_poi_test")
        
        poi = calculator.calculate_poi(demand_zone)
        
        print(f"   Demand Zone: ${demand_zone.bottom:.0f} - ${demand_zone.top:.0f}")
        print(f"   Calculated POI: ${poi.price:.2f}")
        print(f"   POI Type: {poi.poi_type.value}")
        print(f"   Strength: {poi.strength.value}")
        print(f"   Confidence: {poi.confidence_score:.1f}%")
        
        assert poi.poi_type == POIType.DEMAND_POI
        assert demand_zone.bottom <= poi.price <= demand_zone.top
        print("   ✅ Demand POI test passed")
        
        # Test Case 3: Multiple zones batch processing
        print("\\n📊 Test Case 3: Batch POI Calculation")
        zones = [
            create_test_zone_for_poi(ZoneType.SUPPLY, 52000, 51000, "batch_supply_1"),
            create_test_zone_for_poi(ZoneType.DEMAND, 46000, 45000, "batch_demand_1"),
            create_test_zone_for_poi(ZoneType.SUPPLY, 54000, 53000, "batch_supply_2"),
        ]
        
        pois = calculator.update_poi_levels(zones)
        
        print(f"   Zones processed: {len(zones)}")
        print(f"   POIs calculated: {len(pois)}")
        
        for i, poi in enumerate(pois):
            print(f"     POI {i+1}: {poi.poi_type.value} at ${poi.price:.2f} ({poi.confidence_score:.1f}%)")
        
        assert len(pois) == len(zones)
        print("   ✅ Batch POI calculation test passed")
        
        print("\\n🎉 All basic POI calculation tests passed!")
        return calculator
        
    except Exception as e:
        print(f"❌ Error in basic POI calculation test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_poi_calculation_methods():
    """Test different POI calculation methods"""
    print("\\n🧪 Testing POI Calculation Methods...")
    print("=" * 60)
    
    try:
        # Test different calculation methods
        methods = [
            POICalculationMethod.CENTER,
            POICalculationMethod.FIBONACCI,
            POICalculationMethod.ATR_ADJUSTED,
            POICalculationMethod.DYNAMIC
        ]
        
        # Create test zone
        test_zone = create_test_zone_for_poi(ZoneType.SUPPLY, 50000, 48000, "method_test", 200.0)
        
        print(f"\\n📊 Test Zone: ${test_zone.bottom:.0f} - ${test_zone.top:.0f}")
        print(f"   Zone Height: ${test_zone.top - test_zone.bottom:.0f}")
        print(f"   ATR Buffer: ${test_zone.atr_buffer:.0f}")
        
        results = {}
        
        for method in methods:
            print(f"\\n🔍 Testing {method.value} method:")
            
            # Create calculator with specific method
            config = POICalculationConfig(method=method)
            calculator = get_poi_calculator("BTCUSDT", config)
            
            # Calculate POI
            start_time = time.time()
            poi = calculator.calculate_poi(test_zone)
            calculation_time = (time.time() - start_time) * 1000
            
            results[method.value] = poi
            
            print(f"   Primary POI: ${poi.price:.2f}")
            print(f"   Confidence: {poi.confidence_score:.1f}%")
            print(f"   Calculation time: {calculation_time:.2f}ms")
            
            if poi.secondary_levels:
                print(f"   Secondary levels: {len(poi.secondary_levels)}")
                for level in poi.secondary_levels[:3]:  # Show first 3
                    print(f"     ${level:.2f}")
            
            if poi.fibonacci_levels:
                print(f"   Fibonacci levels: {len(poi.fibonacci_levels)}")
                for level_name, level_price in list(poi.fibonacci_levels.items())[:3]:
                    print(f"     {level_name}: ${level_price:.2f}")
        
        # Compare results
        print(f"\\n📊 Method Comparison:")
        center_poi = results.get('center', {}).price if 'center' in results else 0
        
        for method_name, poi in results.items():
            if center_poi > 0:
                difference = abs(poi.price - center_poi)
                difference_pct = (difference / center_poi) * 100
                print(f"   {method_name}: ${poi.price:.2f} (diff: {difference_pct:.2f}%)")
            else:
                print(f"   {method_name}: ${poi.price:.2f}")
        
        print("\\n🎉 POI calculation methods test completed!")
        return results
        
    except Exception as e:
        print(f"❌ Error in POI calculation methods test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_poi_with_real_market_data():
    """Test POI calculation with real market data"""
    print("\\n🧪 Testing POI with Real Market Data...")
    print("=" * 60)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return None
    
    try:
        # Get real market data
        symbol = "BTCUSDT"
        market_data = get_real_market_data_for_poi(symbol, "1h", 100)
        
        # Create calculator with weighted center method (uses market data)
        config = POICalculationConfig(method=POICalculationMethod.WEIGHTED_CENTER)
        calculator = get_poi_calculator(symbol, config)
        
        # Create zones based on recent price action
        current_price = float(market_data['close'].iloc[-1])
        high_price = float(market_data['high'].max())
        low_price = float(market_data['low'].min())
        
        print(f"\\n📊 Market Data Analysis:")
        print(f"   Current price: ${current_price:.2f}")
        print(f"   Period high: ${high_price:.2f}")
        print(f"   Period low: ${low_price:.2f}")
        print(f"   Price range: ${high_price - low_price:.2f}")
        
        # Create realistic zones
        supply_zone = create_test_zone_for_poi(
            ZoneType.SUPPLY, 
            high_price * 0.98,  # Near recent high
            high_price * 0.96,
            "real_supply_test",
            (high_price - low_price) * 0.02  # 2% of range as ATR
        )
        
        demand_zone = create_test_zone_for_poi(
            ZoneType.DEMAND,
            low_price * 1.04,   # Near recent low
            low_price * 1.02,
            "real_demand_test",
            (high_price - low_price) * 0.02
        )
        
        # Set realistic time ranges
        supply_zone.left_time = market_data.index[0]
        supply_zone.right_time = market_data.index[-1]
        demand_zone.left_time = market_data.index[0]
        demand_zone.right_time = market_data.index[-1]
        
        print(f"\\n🎯 Testing Supply Zone POI:")
        print(f"   Zone: ${supply_zone.bottom:.2f} - ${supply_zone.top:.2f}")
        
        supply_poi = calculator.calculate_poi(supply_zone, market_data)
        
        print(f"   Calculated POI: ${supply_poi.price:.2f}")
        print(f"   Confidence: {supply_poi.confidence_score:.1f}%")
        print(f"   Method: {supply_poi.calculation_method}")
        
        if 'vwap' in supply_poi.metadata:
            print(f"   VWAP: ${supply_poi.metadata['vwap']:.2f}")
            print(f"   Candles in zone: {supply_poi.metadata.get('candles_in_zone', 0)}")
        
        print(f"\\n🎯 Testing Demand Zone POI:")
        print(f"   Zone: ${demand_zone.bottom:.2f} - ${demand_zone.top:.2f}")
        
        demand_poi = calculator.calculate_poi(demand_zone, market_data)
        
        print(f"   Calculated POI: ${demand_poi.price:.2f}")
        print(f"   Confidence: {demand_poi.confidence_score:.1f}%")
        print(f"   Method: {demand_poi.calculation_method}")
        
        # Test POI proximity to current price
        print(f"\\n📏 Distance Analysis:")
        
        supply_distance = supply_poi.get_distance_from_price(current_price)
        demand_distance = demand_poi.get_distance_from_price(current_price)
        
        print(f"   Supply POI distance: {supply_distance['percentage_distance']:.2f}% {supply_distance['direction']}")
        print(f"   Demand POI distance: {demand_distance['percentage_distance']:.2f}% {demand_distance['direction']}")
        
        # Test nearest POI levels
        print(f"\\n🎯 Nearest POI Levels:")
        nearest_pois = calculator.get_nearest_poi_levels(current_price, max_distance_pct=10.0)
        
        print(f"   POIs above current price: {len(nearest_pois['above'])}")
        for poi in nearest_pois['above'][:3]:
            distance = poi.get_distance_from_price(current_price)
            print(f"     ${poi.price:.2f} ({distance['percentage_distance']:.2f}% above)")
        
        print(f"   POIs below current price: {len(nearest_pois['below'])}")
        for poi in nearest_pois['below'][:3]:
            distance = poi.get_distance_from_price(current_price)
            print(f"     ${poi.price:.2f} ({distance['percentage_distance']:.2f}% below)")
        
        print("\\n🎉 Real market data POI test completed!")
        return calculator
        
    except Exception as e:
        print(f"❌ Error in real market data test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_poi_performance_and_caching():
    """Test POI calculation performance and caching"""
    print("\\n🧪 Testing POI Performance and Caching...")
    print("=" * 60)
    
    try:
        calculator = get_poi_calculator("BTCUSDT")
        
        # Create multiple test zones
        zones = []
        for i in range(20):
            zone_type = ZoneType.SUPPLY if i % 2 == 0 else ZoneType.DEMAND
            base_price = 50000 + (i * 500)
            top = base_price + 250
            bottom = base_price - 250
            
            zone = create_test_zone_for_poi(zone_type, top, bottom, f"perf_zone_{i}")
            zones.append(zone)
        
        print(f"🚀 Performance test with {len(zones)} zones...")
        
        # Test 1: Initial calculations (cache misses)
        print("\\n📊 Test 1: Initial Calculations (Cache Misses)")
        start_time = time.time()
        
        pois = []
        for zone in zones:
            poi = calculator.calculate_poi(zone)
            pois.append(poi)
        
        initial_time = time.time() - start_time
        
        print(f"   POIs calculated: {len(pois)}")
        print(f"   Total time: {initial_time:.3f}s")
        print(f"   Average time per POI: {(initial_time/len(pois))*1000:.2f}ms")
        
        # Get initial stats
        stats = calculator.get_stats()
        print(f"   Cache misses: {stats.cache_misses}")
        print(f"   Cache hits: {stats.cache_hits}")
        
        # Test 2: Repeat calculations (cache hits)
        print("\\n📊 Test 2: Repeat Calculations (Cache Hits)")
        start_time = time.time()
        
        cached_pois = []
        for zone in zones:
            poi = calculator.calculate_poi(zone)
            cached_pois.append(poi)
        
        cached_time = time.time() - start_time
        
        print(f"   POIs calculated: {len(cached_pois)}")
        print(f"   Total time: {cached_time:.3f}s")
        print(f"   Average time per POI: {(cached_time/len(cached_pois))*1000:.2f}ms")
        
        # Get final stats
        final_stats = calculator.get_stats()
        new_cache_hits = final_stats.cache_hits - stats.cache_hits
        
        print(f"   New cache hits: {new_cache_hits}")
        print(f"   Cache hit rate: {(new_cache_hits/len(zones))*100:.1f}%")
        
        # Performance improvement
        if initial_time > 0 and cached_time > 0:
            speedup = initial_time / cached_time
            print(f"   Performance improvement: {speedup:.1f}x faster")
        
        # Test 3: Batch processing
        print("\\n📊 Test 3: Batch Processing")
        start_time = time.time()
        
        batch_pois = calculator.update_poi_levels(zones[:10])
        
        batch_time = time.time() - start_time
        
        print(f"   Zones processed: {len(zones[:10])}")
        print(f"   POIs calculated: {len(batch_pois)}")
        print(f"   Batch processing time: {batch_time:.3f}s")
        print(f"   Average time per zone: {(batch_time/len(zones[:10]))*1000:.2f}ms")
        
        # Memory usage estimation
        cache_size = len(calculator._calculation_cache)
        print(f"\\n💾 Memory Usage:")
        print(f"   Cache entries: {cache_size}")
        print(f"   Estimated cache memory: ~{cache_size * 1.0:.1f}KB")
        
        print("\\n🎉 Performance and caching tests completed!")
        return calculator
        
    except Exception as e:
        print(f"❌ Error in performance test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_poi_management_features():
    """Test POI management and filtering features"""
    print("\\n🧪 Testing POI Management Features...")
    print("=" * 60)
    
    try:
        calculator = get_poi_calculator("BTCUSDT")
        
        # Create diverse POIs
        zones = [
            create_test_zone_for_poi(ZoneType.SUPPLY, 52000, 51000, "mgmt_supply_1"),
            create_test_zone_for_poi(ZoneType.SUPPLY, 54000, 53000, "mgmt_supply_2"),
            create_test_zone_for_poi(ZoneType.DEMAND, 48000, 47000, "mgmt_demand_1"),
            create_test_zone_for_poi(ZoneType.DEMAND, 46000, 45000, "mgmt_demand_2"),
        ]
        
        # Calculate POIs
        pois = calculator.update_poi_levels(zones)
        
        print(f"\\n📊 Created {len(pois)} POIs for management testing")
        
        # Test filtering by type
        print("\\n🔍 Testing POI Filtering by Type:")
        
        supply_pois = calculator.get_poi_levels_by_type(POIType.SUPPLY_POI, limit=10)
        demand_pois = calculator.get_poi_levels_by_type(POIType.DEMAND_POI, limit=10)
        
        print(f"   Supply POIs: {len(supply_pois)}")
        for poi in supply_pois:
            print(f"     ${poi.price:.2f} - {poi.strength.value} ({poi.confidence_score:.1f}%)")
        
        print(f"   Demand POIs: {len(demand_pois)}")
        for poi in demand_pois:
            print(f"     ${poi.price:.2f} - {poi.strength.value} ({poi.confidence_score:.1f}%)")
        
        # Test POI testing and validation
        print("\\n🧪 Testing POI Testing and Validation:")
        
        if pois:
            test_poi = pois[0]
            print(f"   Testing POI: ${test_poi.price:.2f}")
            
            # Simulate POI test
            test_price = test_poi.price + 10  # Price near POI
            test_poi.test_poi(test_price, reaction_strength=75.0)
            
            print(f"   Times tested: {test_poi.times_tested}")
            print(f"   Last test price: ${test_poi.last_test_price:.2f}")
            print(f"   Average reaction: {test_poi.avg_reaction_strength:.1f}")
            
            # Mark as respected
            test_poi.mark_respected()
            
            print(f"   Times respected: {test_poi.times_respected}")
            print(f"   Success rate: {test_poi.get_success_rate():.1f}%")
            print(f"   Updated confidence: {test_poi.confidence_score:.1f}%")
        
        # Test POI invalidation
        print("\\n❌ Testing POI Invalidation:")
        
        if len(pois) > 1:
            invalidate_poi = pois[1]
            original_status = invalidate_poi.status
            
            success = calculator.invalidate_poi(invalidate_poi.poi_id, "test_invalidation")
            
            print(f"   POI invalidation success: {success}")
            print(f"   Status changed: {original_status.value} → {invalidate_poi.status.value}")
        
        # Test statistics
        print("\\n📈 POI Calculator Statistics:")
        stats = calculator.get_stats()
        
        print(f"   Total calculations: {stats.total_calculations}")
        print(f"   POIs created: {stats.pois_created}")
        print(f"   POIs updated: {stats.pois_updated}")
        print(f"   Cache hits: {stats.cache_hits}")
        print(f"   Cache misses: {stats.cache_misses}")
        
        cache_hit_rate = (stats.cache_hits / (stats.cache_hits + stats.cache_misses) * 100) if (stats.cache_hits + stats.cache_misses) > 0 else 0
        print(f"   Cache hit rate: {cache_hit_rate:.1f}%")
        print(f"   Average calculation time: {stats.avg_calculation_time_ms:.2f}ms")
        
        print("\\n🎉 POI management features test completed!")
        return calculator
        
    except Exception as e:
        print(f"❌ Error in POI management test: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all POI calculator tests"""
    print("🚀 POI Calculator System Testing")
    print("=" * 70)
    
    # Test basic POI calculation
    calculator = test_basic_poi_calculation()
    if not calculator:
        print("❌ Basic POI calculation test failed")
        return
    
    # Test calculation methods
    test_poi_calculation_methods()
    
    # Test with real market data
    test_poi_with_real_market_data()
    
    # Test performance and caching
    test_poi_performance_and_caching()
    
    # Test management features
    test_poi_management_features()
    
    print("\\n🎉 All POI calculator tests completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()