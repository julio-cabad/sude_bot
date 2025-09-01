#!/usr/bin/env python3
"""
Comprehensive test suite for Array Operations and Circular Buffer system
Tests performance, memory management, and multi-symbol functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import numpy as np
import pandas as pd
import threading
import logging
from datetime import datetime, timedelta
from typing import List, Any

from utils.array_ops import (
    CircularBuffer, NumericCircularBuffer, MultiSymbolBufferManager,
    get_buffer_manager, array_add_pop, array_size, array_get, array_clear,
    create_buffer
)
from config.config_manager import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_circular_buffer():
    """Test basic circular buffer functionality"""
    print("\n🧪 Testing Basic Circular Buffer...")
    print("=" * 50)
    
    try:
        # Create buffer
        buffer = CircularBuffer(maxsize=5, symbol="BTCUSDT", buffer_type="test")
        
        print(f"📦 Created buffer: {buffer}")
        print(f"   Initial size: {buffer.size()}")
        print(f"   Capacity: {buffer.capacity()}")
        print(f"   Is empty: {buffer.is_empty()}")
        print(f"   Is full: {buffer.is_full()}")
        
        # Test adding items
        print("\n🔄 Testing add operations...")
        items_to_add = [10, 20, 30, 40, 50]
        
        for i, item in enumerate(items_to_add):
            popped = buffer.add_pop(item)
            print(f"   Added {item}, popped: {popped}, size: {buffer.size()}")
        
        print(f"   Buffer is full: {buffer.is_full()}")
        print(f"   Buffer contents: {buffer.to_list()}")
        
        # Test overflow (should pop oldest)
        print("\n🔄 Testing overflow behavior...")
        popped = buffer.add_pop(60)
        print(f"   Added 60, popped: {popped}")
        print(f"   Buffer contents: {buffer.to_list()}")
        
        popped = buffer.add_pop(70)
        print(f"   Added 70, popped: {popped}")
        print(f"   Buffer contents: {buffer.to_list()}")
        
        # Test peek operations
        print("\n👀 Testing peek operations...")
        print(f"   Oldest item (index 0): {buffer.peek(0)}")
        print(f"   Newest item (index -1): {buffer.peek(-1)}")
        print(f"   Second item (index 1): {buffer.peek(1)}")
        
        # Test range operations
        print("\n📊 Testing range operations...")
        range_items = buffer.peek_range(1, 4)
        print(f"   Items [1:4]: {range_items}")
        
        # Test conversions
        print("\n🔄 Testing conversions...")
        as_array = buffer.to_array()
        print(f"   As numpy array: {as_array}")
        
        as_series = buffer.to_series()
        print(f"   As pandas series: {as_series.tolist()}")
        
        # Test statistics
        print("\n📊 Testing statistics...")
        stats = buffer.get_stats()
        print(f"   Total operations: {stats.total_operations}")
        print(f"   Add operations: {stats.add_operations}")
        print(f"   Pop operations: {stats.pop_operations}")
        print(f"   Memory usage: {stats.memory_usage_bytes} bytes")
        
        return buffer
        
    except Exception as e:
        print(f"❌ Error in basic buffer test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_numeric_circular_buffer():
    """Test numeric circular buffer with mathematical operations"""
    print("\n🧪 Testing Numeric Circular Buffer...")
    print("=" * 50)
    
    try:
        # Create numeric buffer
        buffer = NumericCircularBuffer(maxsize=10, symbol="ETHUSDT", buffer_type="prices")
        
        print(f"📦 Created numeric buffer: {buffer}")
        
        # Add price data
        prices = [100.5, 101.2, 99.8, 102.1, 98.9, 103.5, 97.2, 104.8, 96.1, 105.9]
        
        print("\n💰 Adding price data...")
        for price in prices:
            buffer.add_pop(price)
            print(f"   Added ${price:.2f} - Mean: ${buffer.mean():.2f}, Std: ${buffer.std():.2f}")
        
        # Test mathematical operations
        print("\n📊 Mathematical operations:")
        print(f"   Mean: ${buffer.mean():.4f}")
        print(f"   Std Dev: ${buffer.std():.4f}")
        print(f"   Min: ${buffer.min():.2f}")
        print(f"   Max: ${buffer.max():.2f}")
        print(f"   Range: ${buffer.range():.2f}")
        print(f"   Sum: ${buffer.sum():.2f}")
        print(f"   Median (50th percentile): ${buffer.percentile(50):.2f}")
        print(f"   95th percentile: ${buffer.percentile(95):.2f}")
        
        # Test overflow with statistics update
        print("\n🔄 Testing overflow with statistics...")
        old_mean = buffer.mean()
        old_std = buffer.std()
        
        buffer.add_pop(110.0)  # Add higher price
        
        new_mean = buffer.mean()
        new_std = buffer.std()
        
        print(f"   Added $110.00")
        print(f"   Mean: ${old_mean:.4f} → ${new_mean:.4f}")
        print(f"   Std: ${old_std:.4f} → ${new_std:.4f}")
        print(f"   Buffer: {[f'${x:.2f}' for x in buffer.to_list()]}")
        
        # Test error handling
        print("\n🔍 Testing error handling...")
        try:
            buffer.add_pop(float('nan'))
            print("   ❌ Should have failed with NaN")
        except ValueError as e:
            print(f"   ✅ Correctly rejected NaN: {e}")
        
        try:
            buffer.add_pop("invalid")
            print("   ❌ Should have failed with string")
        except ValueError as e:
            print(f"   ✅ Correctly rejected string: {e}")
        
        return buffer
        
    except Exception as e:
        print(f"❌ Error in numeric buffer test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_multi_symbol_buffer_manager():
    """Test multi-symbol buffer management"""
    print("\n🧪 Testing Multi-Symbol Buffer Manager...")
    print("=" * 50)
    
    try:
        # Get buffer manager
        manager = get_buffer_manager()
        
        print(f"🔧 Buffer manager initialized")
        
        # Test creating buffers for multiple symbols
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT"]
        buffer_types = ["zones", "swings", "pois"]
        
        print(f"\n📦 Creating buffers for {len(symbols)} symbols...")
        
        created_buffers = {}
        for symbol in symbols:
            created_buffers[symbol] = {}
            
            for buffer_type in buffer_types:
                buffer = manager.get_buffer(symbol, buffer_type, size=20)
                created_buffers[symbol][buffer_type] = buffer
                
                # Add some test data
                for i in range(5):
                    buffer.add_pop(f"{symbol}_{buffer_type}_{i}")
            
            # Create numeric price buffer
            price_buffer = manager.get_prices_buffer(symbol, size=50)
            created_buffers[symbol]["prices"] = price_buffer
            
            # Add price data
            base_price = 100 + hash(symbol) % 1000
            for i in range(10):
                price = base_price + np.random.normal(0, 5)
                price_buffer.add_pop(price)
            
            print(f"   ✅ Created buffers for {symbol}")
        
        # Test buffer retrieval
        print(f"\n🔍 Testing buffer retrieval...")
        btc_zones = manager.get_zones_buffer("BTCUSDT")
        eth_swings = manager.get_swings_buffer("ETHUSDT")
        
        print(f"   BTC zones buffer: {btc_zones.size()} items")
        print(f"   ETH swings buffer: {eth_swings.size()} items")
        
        # Test memory usage
        print(f"\n💾 Testing memory usage...")
        memory_stats = manager.get_memory_usage()
        
        print(f"   Total memory: {memory_stats['total_memory_mb']:.2f} MB")
        print(f"   Memory limit: {memory_stats['memory_limit_mb']:.2f} MB")
        print(f"   Usage: {memory_stats['memory_usage_percent']:.1f}%")
        print(f"   Symbols: {memory_stats['symbol_count']}")
        print(f"   Total buffers: {memory_stats['total_buffer_count']}")
        
        # Test performance stats
        print(f"\n📊 Testing performance stats...")
        perf_stats = manager.get_performance_stats()
        
        print(f"   Total operations: {perf_stats['total_operations']}")
        print(f"   Add operations: {perf_stats['add_operations']}")
        print(f"   Pop operations: {perf_stats['pop_operations']}")
        
        # Test symbol removal
        print(f"\n🗑️ Testing symbol removal...")
        manager.remove_symbol("BNBUSDT")
        
        updated_stats = manager.get_memory_usage()
        print(f"   Symbols after removal: {updated_stats['symbol_count']}")
        print(f"   Buffers after removal: {updated_stats['total_buffer_count']}")
        
        return manager
        
    except Exception as e:
        print(f"❌ Error in multi-symbol manager test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_pine_script_equivalents():
    """Test Pine Script equivalent functions"""
    print("\n🧪 Testing Pine Script Equivalent Functions...")
    print("=" * 50)
    
    try:
        # Create buffer using convenience function
        buffer = create_buffer("TESTUSDT", "test_array", size=8, numeric=False)
        
        print(f"📦 Created buffer using create_buffer()")
        
        # Test array_add_pop (Pine Script equivalent)
        print(f"\n🔄 Testing array_add_pop()...")
        items = ["A", "B", "C", "D", "E", "F", "G", "H"]
        
        for item in items:
            popped = array_add_pop(buffer, item)
            size = array_size(buffer)
            print(f"   array_add_pop({item}) → popped: {popped}, size: {size}")
        
        # Test overflow
        print(f"\n🔄 Testing overflow with array_add_pop()...")
        popped = array_add_pop(buffer, "I")
        print(f"   array_add_pop(I) → popped: {popped}")
        print(f"   Buffer contents: {buffer.to_list()}")
        
        # Test array_get (Pine Script equivalent)
        print(f"\n👀 Testing array_get()...")
        print(f"   array_get(0) [oldest]: {array_get(buffer, 0)}")
        print(f"   array_get(-1) [newest]: {array_get(buffer, -1)}")
        print(f"   array_get(3): {array_get(buffer, 3)}")
        
        # Test array_size
        print(f"\n📏 Testing array_size()...")
        print(f"   array_size(): {array_size(buffer)}")
        
        # Test array_clear
        print(f"\n🗑️ Testing array_clear()...")
        array_clear(buffer)
        print(f"   After clear - size: {array_size(buffer)}")
        print(f"   Is empty: {buffer.is_empty()}")
        
        return buffer
        
    except Exception as e:
        print(f"❌ Error in Pine Script equivalents test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_performance_and_threading():
    """Test performance and thread safety"""
    print("\n🧪 Testing Performance and Threading...")
    print("=" * 50)
    
    try:
        # Performance test
        print(f"⚡ Performance test...")
        buffer = CircularBuffer(maxsize=1000, symbol="PERFTEST", buffer_type="performance")
        
        # Single-threaded performance
        start_time = time.time()
        for i in range(10000):
            buffer.add_pop(i)
        single_thread_time = time.time() - start_time
        
        print(f"   Single-threaded: 10,000 operations in {single_thread_time:.4f}s")
        print(f"   Rate: {10000/single_thread_time:.0f} ops/sec")
        
        # Multi-threaded test
        print(f"\n🧵 Multi-threading test...")
        buffer.clear()
        
        def worker_thread(thread_id: int, operations: int):
            """Worker thread for concurrent testing"""
            for i in range(operations):
                buffer.add_pop(f"T{thread_id}_{i}")
        
        # Create and start threads
        threads = []
        operations_per_thread = 1000
        num_threads = 4
        
        start_time = time.time()
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i, operations_per_thread))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        multi_thread_time = time.time() - start_time
        total_operations = num_threads * operations_per_thread
        
        print(f"   Multi-threaded: {total_operations} operations in {multi_thread_time:.4f}s")
        print(f"   Rate: {total_operations/multi_thread_time:.0f} ops/sec")
        print(f"   Final buffer size: {buffer.size()}")
        print(f"   Thread safety: {'✅ PASS' if buffer.size() <= buffer.capacity() else '❌ FAIL'}")
        
        # Memory performance test
        print(f"\n💾 Memory performance test...")
        large_buffer = NumericCircularBuffer(maxsize=10000, symbol="MEMTEST", buffer_type="memory")
        
        start_time = time.time()
        for i in range(50000):
            large_buffer.add_pop(np.random.random())
        memory_test_time = time.time() - start_time
        
        stats = large_buffer.get_stats()
        print(f"   50,000 numeric operations in {memory_test_time:.4f}s")
        print(f"   Memory usage: {stats.memory_usage_bytes / 1024:.1f} KB")
        print(f"   Mean: {large_buffer.mean():.6f}")
        print(f"   Std: {large_buffer.std():.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in performance test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_world_scenario():
    """Test real-world SMC scenario with multiple data types"""
    print("\n🧪 Testing Real-World SMC Scenario...")
    print("=" * 50)
    
    try:
        manager = get_buffer_manager()
        
        # Simulate SMC system with multiple symbols
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        print(f"🎯 Simulating SMC system with {len(symbols)} symbols...")
        
        for symbol in symbols:
            print(f"\n📊 Processing {symbol}...")
            
            # Create buffers for different SMC components
            zones_buffer = manager.get_zones_buffer(symbol, size=20)
            swings_buffer = manager.get_swings_buffer(symbol, size=50)
            pois_buffer = manager.get_pois_buffer(symbol, size=30)
            prices_buffer = manager.get_prices_buffer(symbol, size=100)
            
            # Simulate price data
            base_price = 100 + hash(symbol) % 10000
            for i in range(50):
                # Add price data
                price = base_price + np.random.normal(0, base_price * 0.02)
                prices_buffer.add_pop(price)
                
                # Simulate zone creation (every 5 candles)
                if i % 5 == 0:
                    zone_data = {
                        'type': 'supply' if i % 10 == 0 else 'demand',
                        'price': price,
                        'timestamp': datetime.now() - timedelta(hours=50-i),
                        'atr': prices_buffer.std() if prices_buffer.size() > 1 else 0
                    }
                    zones_buffer.add_pop(zone_data)
                
                # Simulate swing detection (every 3 candles)
                if i % 3 == 0:
                    swing_data = {
                        'type': 'high' if price > prices_buffer.mean() else 'low',
                        'price': price,
                        'timestamp': datetime.now() - timedelta(hours=50-i),
                        'strength': np.random.randint(1, 5)
                    }
                    swings_buffer.add_pop(swing_data)
                
                # Simulate POI calculation (every 7 candles)
                if i % 7 == 0:
                    poi_data = {
                        'price': price,
                        'timestamp': datetime.now() - timedelta(hours=50-i),
                        'zone_id': f"zone_{i//5}",
                        'type': 'supply_poi' if i % 14 == 0 else 'demand_poi'
                    }
                    pois_buffer.add_pop(poi_data)
            
            # Display results
            print(f"   💰 Prices: {prices_buffer.size()} entries, mean: ${prices_buffer.mean():.2f}")
            print(f"   🏢 Zones: {zones_buffer.size()} entries")
            print(f"   📈 Swings: {swings_buffer.size()} entries")
            print(f"   🎯 POIs: {pois_buffer.size()} entries")
            
            # Show latest entries
            if zones_buffer.size() > 0:
                latest_zone = zones_buffer.peek(-1)
                print(f"   Latest zone: {latest_zone['type']} at ${latest_zone['price']:.2f}")
            
            if swings_buffer.size() > 0:
                latest_swing = swings_buffer.peek(-1)
                print(f"   Latest swing: {latest_swing['type']} at ${latest_swing['price']:.2f}")
        
        # Final system statistics
        print(f"\n📊 Final System Statistics:")
        memory_stats = manager.get_memory_usage()
        perf_stats = manager.get_performance_stats()
        
        print(f"   Total memory usage: {memory_stats['total_memory_mb']:.2f} MB")
        print(f"   Total operations: {perf_stats['total_operations']}")
        print(f"   Symbols managed: {perf_stats['symbols_managed']}")
        print(f"   Total buffers: {perf_stats['total_buffers']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in real-world scenario test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all array operations tests"""
    print("🚀 Array Operations and Circular Buffer Testing")
    print("=" * 60)
    
    # Test basic circular buffer
    basic_buffer = test_basic_circular_buffer()
    if not basic_buffer:
        print("❌ Basic buffer test failed, stopping tests")
        return
    
    # Test numeric circular buffer
    numeric_buffer = test_numeric_circular_buffer()
    if not numeric_buffer:
        print("❌ Numeric buffer test failed")
    
    # Test multi-symbol buffer manager
    manager = test_multi_symbol_buffer_manager()
    if not manager:
        print("❌ Multi-symbol manager test failed")
    
    # Test Pine Script equivalents
    test_pine_script_equivalents()
    
    # Test performance and threading
    test_performance_and_threading()
    
    # Test real-world scenario
    test_real_world_scenario()
    
    print("\n🎉 All array operations tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()