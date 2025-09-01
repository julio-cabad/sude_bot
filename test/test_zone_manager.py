#!/usr/bin/env python3
"""
Comprehensive test suite for Zone Manager System
Tests with REAL Binance data and professional zone management
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

from core.zone_manager import ZoneManager, ZoneCreationConfig, ZoneStrength, get_zone_manager
from core.swing_detector import SwingDetector
from models.zone import Zone, ZoneType
from models.swing import Swing, SwingType, SwingLabel
from bnb.binance import RobotBinance
from config.config_manager import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


def get_real_market_data_with_swings(symbol: str = "BTCUSDT", timeframe: str = "1h", 
                                   limit: int = 300) -> tuple[pd.DataFrame, List[Swing]]:
    """Get real OHLCV data and detect swings for zone creation testing"""
    try:
        print(f"📡 Fetching real {symbol} data from Binance...")
        
        # Initialize Binance robot
        robot = RobotBinance(symbol, timeframe)
        
        # Get candlestick data
        df = robot.candlestick(limit=limit)
        
        if df.empty:
            raise ValueError(f"No data received for {symbol}")
        
        print(f"✅ Fetched {len(df)} candles for {symbol}")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")
        print(f"   Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        
        # Detect swings using SwingDetector
        print(f"🔄 Detecting swings in market data...")
        swing_detector = SwingDetector(symbol)
        swings = swing_detector.detect_swings(df)
        
        print(f"✅ Detected {len(swings)} swings")
        
        return df, swings
        
    except Exception as e:
        print(f"❌ Error fetching market data: {e}")
        raise


def create_test_swing(swing_type: SwingType, price: float, timestamp: datetime = None) -> Swing:
    """Create a test swing for zone creation"""
    if timestamp is None:
        timestamp = datetime.now()
    
    return Swing(
        swing_type=swing_type,
        price=price,
        timestamp=timestamp,
        bar_index=100,
        swing_length=10,
        label=SwingLabel.HH if swing_type == SwingType.HIGH else SwingLabel.HL
    )


def test_basic_zone_creation():
    """Test basic supply and demand zone creation"""
    print("\\n🧪 Testing Basic Zone Creation...")
    print("=" * 60)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return None
    
    try:
        # Get real market data and swings
        symbol = "BTCUSDT"
        ohlcv_data, real_swings = get_real_market_data_with_swings(symbol, "1h", 200)
        
        # Create zone manager with default config
        config = ZoneCreationConfig(
            atr_multiplier=2.0,
            enable_overlap_check=True,
            min_swing_strength="medium"
        )
        
        zone_manager = get_zone_manager(symbol, config)
        
        print(f"\\n📊 Testing Supply Zone Creation...")
        
        # Find swing highs from real data
        swing_highs = [s for s in real_swings if s.swing_type == SwingType.HIGH]
        
        if swing_highs:
            # Test supply zone creation with real swing
            swing_high = swing_highs[0]
            print(f"   Using real swing high at ${swing_high.price:.2f}")
            
            supply_zone = zone_manager.create_supply_zone(swing_high, ohlcv_data)
            
            if supply_zone:
                print(f"   ✅ Supply zone created successfully")
                print(f"      Zone ID: {supply_zone.zone_id}")
                print(f"      Price range: ${supply_zone.bottom:.2f} - ${supply_zone.top:.2f}")
                print(f"      POI: ${supply_zone.poi:.2f}")
                print(f"      ATR buffer: ${supply_zone.atr_buffer:.2f}")
                print(f"      Zone height: ${supply_zone.get_zone_height():.2f}")
            else:
                print(f"   ⚠️ Supply zone creation was rejected (validation failed)")
        
        print(f"\\n📊 Testing Demand Zone Creation...")
        
        # Find swing lows from real data
        swing_lows = [s for s in real_swings if s.swing_type == SwingType.LOW]
        
        if swing_lows:
            # Test demand zone creation with real swing
            swing_low = swing_lows[0]
            print(f"   Using real swing low at ${swing_low.price:.2f}")
            
            demand_zone = zone_manager.create_demand_zone(swing_low, ohlcv_data)
            
            if demand_zone:
                print(f"   ✅ Demand zone created successfully")
                print(f"      Zone ID: {demand_zone.zone_id}")
                print(f"      Price range: ${demand_zone.bottom:.2f} - ${demand_zone.top:.2f}")
                print(f"      POI: ${demand_zone.poi:.2f}")
                print(f"      ATR buffer: ${demand_zone.atr_buffer:.2f}")
                print(f"      Zone height: ${demand_zone.get_zone_height():.2f}")
            else:
                print(f"   ⚠️ Demand zone creation was rejected (validation failed)")
        
        # Test zone retrieval
        print(f"\\n📊 Testing Zone Retrieval...")
        active_zones = zone_manager.get_active_zones()
        print(f"   Active zones: {len(active_zones)}")
        
        supply_zones = zone_manager.get_active_zones(ZoneType.SUPPLY)
        demand_zones = zone_manager.get_active_zones(ZoneType.DEMAND)
        
        print(f"   Supply zones: {len(supply_zones)}")
        print(f"   Demand zones: {len(demand_zones)}")
        
        # Get zone manager statistics
        stats = zone_manager.get_stats()
        print(f"\\n📈 Zone Manager Statistics:")
        print(f"   Total zones created: {stats.total_zones_created}")
        print(f"   Supply zones: {stats.supply_zones_created}")
        print(f"   Demand zones: {stats.demand_zones_created}")
        print(f"   Active zones: {stats.active_zones}")
        print(f"   Avg creation time: {stats.avg_creation_time_ms:.2f}ms")
        print(f"   Overlap rejections: {stats.overlap_rejections}")
        print(f"   Strength rejections: {stats.strength_rejections}")
        
        return zone_manager
        
    except Exception as e:
        print(f"❌ Error in basic zone creation test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_batch_zone_processing():
    """Test batch processing of multiple swings"""
    print("\\n🧪 Testing Batch Zone Processing...")
    print("=" * 60)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return
    
    try:
        # Get real market data and swings
        symbol = "ETHUSDT"
        ohlcv_data, real_swings = get_real_market_data_with_swings(symbol, "1h", 300)
        
        # Create zone manager
        zone_manager = get_zone_manager(symbol)
        
        print(f"🚀 Batch processing {len(real_swings)} real swings...")
        
        # Batch process all swings
        start_time = time.time()
        results = zone_manager.batch_process_swings(real_swings, ohlcv_data)
        processing_time = time.time() - start_time
        
        # Analyze results
        total_zones_created = sum(len(zones) for zones in results.values())
        
        print(f"✅ Batch processing completed in {processing_time:.3f}s")
        print(f"   Swings processed: {len(results)}")
        print(f"   Zones created: {total_zones_created}")
        print(f"   Processing rate: {len(real_swings)/processing_time:.0f} swings/second")
        
        # Show breakdown by swing type
        supply_zones = 0
        demand_zones = 0
        
        for swing_id, zones in results.items():
            for zone in zones:
                if zone.zone_type == ZoneType.SUPPLY:
                    supply_zones += 1
                else:
                    demand_zones += 1
        
        print(f"   Supply zones created: {supply_zones}")
        print(f"   Demand zones created: {demand_zones}")
        
        # Test active zones retrieval
        active_zones = zone_manager.get_active_zones()
        print(f"   Active zones after batch: {len(active_zones)}")
        
        # Show some example zones
        if active_zones:
            print(f"\\n📊 Example Created Zones:")
            for i, zone in enumerate(active_zones[:3]):
                print(f"   {i+1}. {zone.zone_type.name} Zone: ${zone.bottom:.2f}-${zone.top:.2f} (POI: ${zone.poi:.2f})")
        
    except Exception as e:
        print(f"❌ Error in batch processing test: {e}")
        import traceback
        traceback.print_exc()


def test_zone_break_detection():
    """Test zone break detection with real price movements"""
    print("\\n🧪 Testing Zone Break Detection...")
    print("=" * 60)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return
    
    try:
        # Get real market data
        symbol = "BTCUSDT"
        ohlcv_data, real_swings = get_real_market_data_with_swings(symbol, "1h", 150)
        
        # Create zone manager and some zones
        zone_manager = get_zone_manager(symbol)
        
        # Create zones from first half of swings
        first_half_swings = real_swings[:len(real_swings)//2]
        zone_manager.batch_process_swings(first_half_swings, ohlcv_data)
        
        initial_zones = zone_manager.get_active_zones()
        print(f"📊 Created {len(initial_zones)} zones for break testing")
        
        if not initial_zones:
            print("⚠️ No zones created for break testing")
            return
        
        # Test zone breaks with subsequent price data
        print(f"\\n🔍 Testing zone breaks with real price movements...")
        
        # Use second half of data for break testing
        second_half_data = ohlcv_data.iloc[len(ohlcv_data)//2:]
        
        total_breaks = 0
        
        for i, (timestamp, candle) in enumerate(second_half_data.iterrows()):
            current_price = float(candle['close'])
            current_time = timestamp
            current_bar_index = len(ohlcv_data)//2 + i
            
            # Check for zone breaks
            broken_zones = zone_manager.check_zone_breaks(
                current_price, current_time, current_bar_index
            )
            
            if broken_zones:
                total_breaks += len(broken_zones)
                print(f"   💥 {len(broken_zones)} zones broken at ${current_price:.2f} on {timestamp.strftime('%Y-%m-%d %H:%M')}")
                
                for zone in broken_zones:
                    print(f"      - {zone.zone_type.name} zone ${zone.bottom:.2f}-${zone.top:.2f} broken")
        
        # Final statistics
        remaining_zones = zone_manager.get_active_zones()
        broken_zones = zone_manager.get_broken_zones()
        
        print(f"\\n📊 Zone Break Results:")
        print(f"   Initial zones: {len(initial_zones)}")
        print(f"   Total breaks detected: {total_breaks}")
        print(f"   Remaining active zones: {len(remaining_zones)}")
        print(f"   Broken zones recorded: {len(broken_zones)}")
        
        # Show some broken zones
        if broken_zones:
            print(f"\\n💥 Recent Broken Zones:")
            for i, zone in enumerate(broken_zones[:3]):
                break_time_str = zone.break_time.strftime('%Y-%m-%d %H:%M') if zone.break_time else "Unknown"
                print(f"   {i+1}. {zone.zone_type.name} at ${zone.poi:.2f} broken at ${zone.break_price:.2f} on {break_time_str}")
        
    except Exception as e:
        print(f"❌ Error in zone break detection test: {e}")
        import traceback
        traceback.print_exc()


def test_zone_overlap_handling():
    """Test zone overlap detection and resolution"""
    print("\\n🧪 Testing Zone Overlap Handling...")
    print("=" * 60)
    
    try:
        # Create zone manager with overlap checking enabled
        symbol = "BTCUSDT"
        config = ZoneCreationConfig(
            atr_multiplier=1.5,
            enable_overlap_check=True,
            overlap_resolution="keep_strongest"
        )
        
        zone_manager = get_zone_manager(symbol, config)
        
        # Create realistic test data with sufficient history for ATR calculation
        current_time = datetime.now()
        dates = pd.date_range(start=current_time - timedelta(hours=50), end=current_time, freq='1H')
        np.random.seed(42)  # For reproducible results
        
        # Generate realistic OHLCV data
        base_price = 50000
        ohlcv_data = []
        
        for i in range(len(dates)):
            # Random walk with some volatility
            price_change = np.random.normal(0, 200)  # $200 average volatility
            base_price += price_change
            base_price = max(base_price, 45000)  # Floor price
            base_price = min(base_price, 55000)  # Ceiling price
            
            # Generate OHLC around the base price
            volatility = np.random.uniform(100, 500)
            open_price = base_price + np.random.uniform(-volatility/2, volatility/2)
            close_price = base_price + np.random.uniform(-volatility/2, volatility/2)
            high_price = max(open_price, close_price) + np.random.uniform(0, volatility/2)
            low_price = min(open_price, close_price) - np.random.uniform(0, volatility/2)
            volume = np.random.uniform(800, 1200)
            
            ohlcv_data.append([open_price, high_price, low_price, close_price, volume])
        
        test_data = pd.DataFrame(ohlcv_data, columns=['open', 'high', 'low', 'close', 'volume'], index=dates)
        
        print(f"📊 Testing overlapping zone creation...")
        
        # Create overlapping swings
        swing1 = create_test_swing(SwingType.HIGH, 50200, current_time - timedelta(hours=2))
        # Add custom strength attribute for testing
        swing1.strength = "strong"
        
        swing2 = create_test_swing(SwingType.HIGH, 50250, current_time - timedelta(hours=1))  # Overlapping
        swing2.strength = "medium"
        
        swing3 = create_test_swing(SwingType.HIGH, 50180, current_time)  # Also overlapping
        swing3.strength = "very_strong"
        
        # Create zones and test overlap handling
        zone1 = zone_manager.create_supply_zone(swing1, test_data)
        print(f"   Zone 1 created: {zone1 is not None} (Strong swing)")
        
        zone2 = zone_manager.create_supply_zone(swing2, test_data)
        print(f"   Zone 2 created: {zone2 is not None} (Medium swing, should be rejected)")
        
        zone3 = zone_manager.create_supply_zone(swing3, test_data)
        print(f"   Zone 3 created: {zone3 is not None} (Very Strong swing, should replace Zone 1)")
        
        # Check final active zones
        active_zones = zone_manager.get_active_zones()
        print(f"\\n📊 Final active zones: {len(active_zones)}")
        
        for i, zone in enumerate(active_zones):
            print(f"   {i+1}. {zone.zone_type.name} Zone: ${zone.bottom:.2f}-${zone.top:.2f}")
        
        # Test different overlap resolution strategies
        print(f"\\n🔧 Testing different overlap resolution strategies...")
        
        strategies = ["keep_strongest", "keep_newest", "merge"]
        
        for strategy in strategies:
            print(f"\\n   Testing '{strategy}' strategy:")
            
            # Create new zone manager with different strategy
            test_config = ZoneCreationConfig(
                atr_multiplier=1.5,
                enable_overlap_check=True,
                overlap_resolution=strategy
            )
            
            test_manager = get_zone_manager(f"{symbol}_test", test_config)
            
            # Create overlapping zones
            zone_a = test_manager.create_supply_zone(swing1, test_data)
            zone_b = test_manager.create_supply_zone(swing2, test_data)
            
            final_zones = test_manager.get_active_zones()
            print(f"      Final zones with {strategy}: {len(final_zones)}")
        
        # Get overlap statistics
        stats = zone_manager.get_stats()
        print(f"\\n📈 Overlap Handling Statistics:")
        print(f"   Total zones created: {stats.total_zones_created}")
        print(f"   Overlap rejections: {stats.overlap_rejections}")
        print(f"   Strength rejections: {stats.strength_rejections}")
        
    except Exception as e:
        print(f"❌ Error in overlap handling test: {e}")
        import traceback
        traceback.print_exc()


def test_zone_queries_and_analysis():
    """Test zone querying and analysis functions"""
    print("\\n🧪 Testing Zone Queries and Analysis...")
    print("=" * 60)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return
    
    try:
        # Get real market data
        symbol = "ADAUSDT"
        ohlcv_data, real_swings = get_real_market_data_with_swings(symbol, "1h", 200)
        
        # Create zone manager and populate with zones
        zone_manager = get_zone_manager(symbol)
        zone_manager.batch_process_swings(real_swings, ohlcv_data)
        
        current_price = float(ohlcv_data['close'].iloc[-1])
        print(f"📊 Current {symbol} price: ${current_price:.4f}")
        
        # Test nearest zones query
        print(f"\\n🎯 Testing nearest zones query...")
        nearest_zones = zone_manager.get_nearest_zones(current_price, count=3)
        
        print(f"   Nearest supply zones (above current price):")
        for i, zone in enumerate(nearest_zones['supply']):
            distance = zone.bottom - current_price
            print(f"      {i+1}. ${zone.bottom:.4f}-${zone.top:.4f} (distance: +${distance:.4f})")
        
        print(f"   Nearest demand zones (below current price):")
        for i, zone in enumerate(nearest_zones['demand']):
            distance = current_price - zone.top
            print(f"      {i+1}. ${zone.bottom:.4f}-${zone.top:.4f} (distance: -${distance:.4f})")
        
        # Test price range query
        print(f"\\n📊 Testing price range query...")
        price_range_min = current_price * 0.95  # 5% below
        price_range_max = current_price * 1.05  # 5% above
        
        zones_in_range = zone_manager.get_zones_by_price_range(price_range_min, price_range_max)
        print(f"   Zones in ±5% range (${price_range_min:.4f} - ${price_range_max:.4f}): {len(zones_in_range)}")
        
        for i, zone in enumerate(zones_in_range):
            print(f"      {i+1}. {zone.zone_type.name}: ${zone.bottom:.4f}-${zone.top:.4f} (POI: ${zone.poi:.4f})")
        
        # Test zone statistics
        print(f"\\n📈 Zone Analysis Statistics:")
        all_active = zone_manager.get_active_zones()
        
        if all_active:
            # Calculate zone distribution
            supply_count = len([z for z in all_active if z.zone_type == ZoneType.SUPPLY])
            demand_count = len([z for z in all_active if z.zone_type == ZoneType.DEMAND])
            
            # Calculate average zone sizes
            zone_heights = [z.get_zone_height() for z in all_active]
            avg_height = np.mean(zone_heights) if zone_heights else 0
            
            # Calculate price coverage
            all_tops = [z.top for z in all_active]
            all_bottoms = [z.bottom for z in all_active]
            price_coverage = (max(all_tops) - min(all_bottoms)) if all_tops and all_bottoms else 0
            
            print(f"   Total active zones: {len(all_active)}")
            print(f"   Supply zones: {supply_count}")
            print(f"   Demand zones: {demand_count}")
            print(f"   Average zone height: ${avg_height:.4f}")
            print(f"   Total price coverage: ${price_coverage:.4f}")
            print(f"   Coverage as % of current price: {(price_coverage/current_price)*100:.1f}%")
        
        # Test zone cleanup
        print(f"\\n🧹 Testing zone cleanup...")
        initial_count = len(zone_manager.get_active_zones())
        
        # Cleanup zones older than 1 hour (very aggressive for testing)
        cleaned_count = zone_manager.cleanup_expired_zones(max_age_hours=1.0)
        
        final_count = len(zone_manager.get_active_zones())
        
        print(f"   Zones before cleanup: {initial_count}")
        print(f"   Zones cleaned up: {cleaned_count}")
        print(f"   Zones after cleanup: {final_count}")
        
    except Exception as e:
        print(f"❌ Error in zone queries test: {e}")
        import traceback
        traceback.print_exc()


def test_zone_manager_performance():
    """Test zone manager performance with large datasets"""
    print("\\n🧪 Testing Zone Manager Performance...")
    print("=" * 60)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return
    
    try:
        # Get large dataset
        symbol = "BTCUSDT"
        ohlcv_data, real_swings = get_real_market_data_with_swings(symbol, "1h", 500)
        
        print(f"🚀 Performance test with {len(real_swings)} swings and {len(ohlcv_data)} candles...")
        
        # Test different configurations
        configs = [
            ("Default", ZoneCreationConfig()),
            ("No Overlap Check", ZoneCreationConfig(enable_overlap_check=False)),
            ("High ATR", ZoneCreationConfig(atr_multiplier=3.0)),
            ("Strict Strength", ZoneCreationConfig(min_swing_strength="strong"))
        ]
        
        for config_name, config in configs:
            print(f"\\n📊 Testing {config_name} configuration:")
            
            zone_manager = get_zone_manager(f"{symbol}_{config_name.lower().replace(' ', '_')}", config)
            
            # Performance test
            start_time = time.time()
            results = zone_manager.batch_process_swings(real_swings, ohlcv_data)
            processing_time = time.time() - start_time
            
            # Analyze results
            total_zones = sum(len(zones) for zones in results.values())
            active_zones = len(zone_manager.get_active_zones())
            
            stats = zone_manager.get_stats()
            
            print(f"   Processing time: {processing_time:.3f}s")
            print(f"   Zones created: {total_zones}")
            print(f"   Active zones: {active_zones}")
            print(f"   Processing rate: {len(real_swings)/processing_time:.0f} swings/s")
            print(f"   Avg creation time: {stats.avg_creation_time_ms:.2f}ms")
            print(f"   Overlap rejections: {stats.overlap_rejections}")
            print(f"   Strength rejections: {stats.strength_rejections}")
        
        # Memory usage estimation
        print(f"\\n💾 Memory Usage Estimation:")
        zone_manager = get_zone_manager(symbol)
        zone_manager.batch_process_swings(real_swings[:100], ohlcv_data)  # Create some zones
        
        active_zones = zone_manager.get_active_zones()
        estimated_memory_per_zone = 1.0  # KB per zone (rough estimate)
        total_memory_kb = len(active_zones) * estimated_memory_per_zone
        
        print(f"   Active zones: {len(active_zones)}")
        print(f"   Estimated memory per zone: {estimated_memory_per_zone:.1f}KB")
        print(f"   Total estimated memory: {total_memory_kb:.1f}KB")
        
    except Exception as e:
        print(f"❌ Error in performance test: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all zone manager tests"""
    print("🚀 Zone Manager System Testing with Real Binance Data")
    print("=" * 70)
    
    # Test basic zone creation
    zone_manager = test_basic_zone_creation()
    if not zone_manager:
        print("❌ Basic zone creation test failed")
    
    # Test batch processing
    test_batch_zone_processing()
    
    # Test zone break detection
    test_zone_break_detection()
    
    # Test overlap handling
    test_zone_overlap_handling()
    
    # Test zone queries and analysis
    test_zone_queries_and_analysis()
    
    # Test performance
    test_zone_manager_performance()
    
    print("\\n🎉 All zone manager tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()