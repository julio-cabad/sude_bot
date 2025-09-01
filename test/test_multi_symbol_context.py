#!/usr/bin/env python3
"""
Comprehensive test suite for Multi-Symbol Context Management System
Tests with REAL Binance data and multi-symbol processing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from core.smc_context import SMCContext, ContextConfig, ContextStatus
from core.smc_symbol_manager import SMCSymbolManager, ManagerStatus, get_symbol_manager
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


def test_single_context_with_real_data():
    """Test single SMC context with real Binance data"""
    print("\n🧪 Testing Single Context with Real Binance Data...")
    print("=" * 60)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return None
    
    try:
        # Create context configuration
        config = ContextConfig(
            symbol="BTCUSDT",
            timeframe="1h",
            swing_length=10,
            history_limit=15,
            enable_zones=True,
            enable_swings=True,
            enable_pois=True,
            enable_bos=True
        )
        
        print(f"🎯 Creating SMC context for {config.symbol}...")
        
        # Create and initialize context
        context = SMCContext("BTCUSDT", config)
        
        # Add event callbacks
        events_received = []
        
        def event_handler(symbol, event_type, data):
            events_received.append({
                'symbol': symbol,
                'event': event_type,
                'data': data,
                'timestamp': datetime.now()
            })
            print(f"   📢 Event: {symbol} - {event_type}")
        
        context.add_event_callback('zone_created', event_handler)
        context.add_event_callback('swing_detected', event_handler)
        context.add_event_callback('poi_calculated', event_handler)
        context.add_event_callback('bos_detected', event_handler)
        
        # Initialize context
        print(f"🔧 Initializing context...")
        start_time = time.time()
        
        if not context.initialize():
            print("❌ Failed to initialize context")
            return None
        
        init_time = time.time() - start_time
        print(f"✅ Context initialized in {init_time:.2f}s")
        
        # Get initial data
        initial_data = context.get_current_data()
        print(f"\n📊 Initial Context Data:")
        print(f"   Status: {initial_data['status']}")
        print(f"   Current Price: ${initial_data['current_price']:.2f}")
        print(f"   Price Mean: ${initial_data['price_mean']:.2f}")
        print(f"   Zones: {initial_data['zones_count']}")
        print(f"   Swings: {initial_data['swings_count']}")
        print(f"   POIs: {initial_data['pois_count']}")
        
        # Test updates
        print(f"\n🔄 Testing context updates...")
        for i in range(3):
            print(f"   Update {i+1}...")
            update_start = time.time()
            
            success = context.update()
            update_time = (time.time() - update_start) * 1000
            
            if success:
                print(f"   ✅ Update successful in {update_time:.2f}ms")
            else:
                print(f"   ❌ Update failed")
            
            time.sleep(2)  # Wait between updates
        
        # Get final data
        final_data = context.get_current_data()
        print(f"\n📊 Final Context Data:")
        print(f"   Zones: {final_data['zones_count']}")
        print(f"   Swings: {final_data['swings_count']}")
        print(f"   POIs: {final_data['pois_count']}")
        print(f"   BOS: {final_data['bos_count']}")
        
        if final_data['latest_zone']:
            zone = final_data['latest_zone']
            print(f"   Latest Zone: {zone['type']} at ${zone['poi']:.2f}")
        
        if final_data['latest_swing']:
            swing = final_data['latest_swing']
            print(f"   Latest Swing: {swing['type']} at ${swing['price']:.2f}")
        
        # Show events received
        print(f"\n📢 Events Received: {len(events_received)}")
        for event in events_received[-3:]:  # Show last 3 events
            print(f"   {event['event']}: {event['symbol']} at {event['timestamp'].strftime('%H:%M:%S')}")
        
        # Get statistics
        stats = context.get_stats()
        print(f"\n📊 Context Statistics:")
        print(f"   Total Updates: {stats.total_updates}")
        print(f"   Successful: {stats.successful_updates}")
        print(f"   Failed: {stats.failed_updates}")
        print(f"   Zones Created: {stats.zones_created}")
        print(f"   Swings Detected: {stats.swings_detected}")
        print(f"   POIs Calculated: {stats.pois_calculated}")
        print(f"   Memory Usage: {stats.memory_usage_mb:.2f}MB")
        print(f"   Avg Processing: {stats.processing_time_ms:.2f}ms")
        
        # Cleanup
        context.stop()
        
        return context
        
    except Exception as e:
        print(f"❌ Error in single context test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_multi_symbol_manager():
    """Test multi-symbol manager with real data"""
    print("\n🧪 Testing Multi-Symbol Manager...")
    print("=" * 60)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return None
    
    try:
        # Get configuration
        config = get_config()
        
        # Use first 3 symbols for testing
        test_symbols = config.symbols[:3]
        print(f"🎯 Testing with symbols: {test_symbols}")
        
        # Create symbol manager
        manager = SMCSymbolManager(symbols=test_symbols, max_workers=4)
        
        # Add global event callbacks
        global_events = []
        
        def global_event_handler(event_type, data):
            global_events.append({
                'event': event_type,
                'data': data,
                'timestamp': datetime.now()
            })
            print(f"   🌐 Global Event: {event_type}")
        
        manager.add_global_callback('symbol_added', global_event_handler)
        manager.add_global_callback('symbol_removed', global_event_handler)
        manager.add_global_callback('context_error', global_event_handler)
        manager.add_global_callback('manager_status_changed', global_event_handler)
        
        # Initialize manager
        print(f"🚀 Initializing manager...")
        start_time = time.time()
        
        if not manager.initialize():
            print("❌ Failed to initialize manager")
            return None
        
        init_time = time.time() - start_time
        print(f"✅ Manager initialized in {init_time:.2f}s")
        
        # Get initial manager stats
        stats = manager.get_manager_stats()
        print(f"\n📊 Manager Statistics:")
        print(f"   Status: {stats.status.value}")
        print(f"   Total Symbols: {stats.total_symbols}")
        print(f"   Active Symbols: {stats.active_symbols}")
        print(f"   Memory Usage: {stats.total_memory_mb:.2f}MB")
        
        # Get data for all symbols
        print(f"\n📊 Symbol Data:")
        all_data = manager.get_all_symbol_data()
        
        for symbol, data in all_data.items():
            print(f"   {symbol}:")
            print(f"      Status: {data['status']}")
            print(f"      Price: ${data['current_price']:.2f}")
            print(f"      Zones: {data['zones_count']}, Swings: {data['swings_count']}")
            
            if data['latest_zone']:
                zone = data['latest_zone']
                print(f"      Latest Zone: {zone['type']} at ${zone['poi']:.2f}")
        
        # Test adding a new symbol
        print(f"\n➕ Testing symbol addition...")
        new_symbol = "ETHUSDT"
        if new_symbol not in test_symbols:
            success = manager.add_symbol(new_symbol)
            print(f"   Add {new_symbol}: {'✅ Success' if success else '❌ Failed'}")
            
            # Wait for initialization
            time.sleep(3)
            
            # Check new symbol data
            new_data = manager.get_symbol_data(new_symbol)
            if new_data:
                print(f"   {new_symbol} Status: {new_data['status']}")
                print(f"   {new_symbol} Price: ${new_data['current_price']:.2f}")
        
        # Test pause/resume
        print(f"\n⏸️ Testing pause/resume...")
        first_symbol = test_symbols[0]
        
        manager.pause_symbol(first_symbol)
        time.sleep(2)
        
        paused_data = manager.get_symbol_data(first_symbol)
        print(f"   {first_symbol} after pause: {paused_data['status']}")
        
        manager.resume_symbol(first_symbol)
        time.sleep(2)
        
        resumed_data = manager.get_symbol_data(first_symbol)
        print(f"   {first_symbol} after resume: {resumed_data['status']}")
        
        # Let manager run for a bit
        print(f"\n🔄 Running manager for 10 seconds...")
        time.sleep(10)
        
        # Get final statistics
        final_stats = manager.get_manager_stats()
        print(f"\n📊 Final Manager Statistics:")
        print(f"   Total Updates: {final_stats.total_updates}")
        print(f"   Successful: {final_stats.successful_updates}")
        print(f"   Failed: {final_stats.failed_updates}")
        print(f"   Uptime: {final_stats.uptime_seconds:.1f}s")
        print(f"   Avg Processing: {final_stats.avg_processing_time_ms:.2f}ms")
        print(f"   Memory Usage: {final_stats.total_memory_mb:.2f}MB")
        
        # Show performance history
        perf_history = manager.get_performance_history(last_n=3)
        print(f"\n📈 Recent Performance (last 3 cycles):")
        for i, perf in enumerate(perf_history):
            print(f"   Cycle {i+1}: {perf['successful_updates']} success, {perf['failed_updates']} failed, {perf['total_time_seconds']:.2f}s")
        
        # Show global events
        print(f"\n🌐 Global Events: {len(global_events)}")
        for event in global_events:
            print(f"   {event['event']}: {event['timestamp'].strftime('%H:%M:%S')}")
        
        # Test removal
        print(f"\n🗑️ Testing symbol removal...")
        if new_symbol in [ctx.symbol for ctx in manager.get_all_contexts().values()]:
            success = manager.remove_symbol(new_symbol)
            print(f"   Remove {new_symbol}: {'✅ Success' if success else '❌ Failed'}")
        
        # Cleanup
        manager.stop()
        
        return manager
        
    except Exception as e:
        print(f"❌ Error in multi-symbol manager test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_performance_and_scalability():
    """Test performance with multiple symbols"""
    print("\n🧪 Testing Performance and Scalability...")
    print("=" * 60)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return
    
    try:
        config = get_config()
        
        # Test with more symbols (up to 5 for testing)
        test_symbols = config.symbols[:5]
        print(f"🎯 Performance test with {len(test_symbols)} symbols: {test_symbols}")
        
        # Create manager with performance monitoring
        manager = SMCSymbolManager(symbols=test_symbols, max_workers=6)
        
        # Initialize
        print(f"🚀 Initializing performance test...")
        start_time = time.time()
        
        if not manager.initialize():
            print("❌ Performance test initialization failed")
            return
        
        init_time = time.time() - start_time
        print(f"✅ Initialized {len(test_symbols)} symbols in {init_time:.2f}s")
        print(f"   Average per symbol: {init_time/len(test_symbols):.2f}s")
        
        # Monitor performance for 30 seconds
        print(f"\n📊 Monitoring performance for 30 seconds...")
        
        performance_samples = []
        start_monitoring = time.time()
        
        while time.time() - start_monitoring < 30:
            time.sleep(5)  # Sample every 5 seconds
            
            stats = manager.get_manager_stats()
            sample = {
                'timestamp': datetime.now(),
                'active_symbols': stats.active_symbols,
                'total_updates': stats.total_updates,
                'memory_mb': stats.total_memory_mb,
                'avg_processing_ms': stats.avg_processing_time_ms
            }
            performance_samples.append(sample)
            
            print(f"   Sample: {stats.active_symbols} active, {stats.total_memory_mb:.1f}MB, {stats.avg_processing_time_ms:.1f}ms avg")
        
        # Analyze performance
        print(f"\n📈 Performance Analysis:")
        if len(performance_samples) >= 2:
            first_sample = performance_samples[0]
            last_sample = performance_samples[-1]
            
            updates_per_second = (last_sample['total_updates'] - first_sample['total_updates']) / 30
            memory_growth = last_sample['memory_mb'] - first_sample['memory_mb']
            
            print(f"   Updates per second: {updates_per_second:.2f}")
            print(f"   Memory growth: {memory_growth:.2f}MB over 30s")
            print(f"   Average processing time: {last_sample['avg_processing_ms']:.2f}ms")
            print(f"   Memory per symbol: {last_sample['memory_mb']/len(test_symbols):.2f}MB")
            
            # Performance assessment
            if updates_per_second > 0.5 and last_sample['avg_processing_ms'] < 1000:
                print(f"   🚀 Performance: EXCELLENT")
            elif updates_per_second > 0.2 and last_sample['avg_processing_ms'] < 2000:
                print(f"   ✅ Performance: GOOD")
            else:
                print(f"   ⚠️ Performance: NEEDS OPTIMIZATION")
        
        # Test concurrent symbol operations
        print(f"\n🧵 Testing concurrent operations...")
        
        def add_remove_symbol():
            """Add and remove symbol concurrently"""
            test_symbol = "ADAUSDT"
            manager.add_symbol(test_symbol)
            time.sleep(2)
            manager.remove_symbol(test_symbol)
        
        # Start concurrent operations
        threads = []
        for i in range(2):
            thread = threading.Thread(target=add_remove_symbol)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        print(f"   ✅ Concurrent operations completed")
        
        # Final statistics
        final_stats = manager.get_manager_stats()
        print(f"\n📊 Final Performance Statistics:")
        print(f"   Total symbols processed: {final_stats.total_symbols}")
        print(f"   Total updates: {final_stats.total_updates}")
        print(f"   Success rate: {(final_stats.successful_updates/final_stats.total_updates*100):.1f}%")
        print(f"   Memory efficiency: {final_stats.total_memory_mb/final_stats.total_symbols:.2f}MB per symbol")
        
        # Cleanup
        manager.stop()
        
    except Exception as e:
        print(f"❌ Error in performance test: {e}")
        import traceback
        traceback.print_exc()


def test_error_handling_and_recovery():
    """Test error handling and recovery mechanisms"""
    print("\n🧪 Testing Error Handling and Recovery...")
    print("=" * 60)
    
    try:
        # Test with invalid symbol
        print(f"🔍 Testing invalid symbol handling...")
        
        invalid_symbols = ["INVALIDUSDT", "BTCUSDT"]  # Mix valid and invalid
        manager = SMCSymbolManager(symbols=invalid_symbols, max_workers=2)
        
        # This should handle the invalid symbol gracefully
        success = manager.initialize()
        print(f"   Initialize with invalid symbol: {'✅ Handled' if success else '❌ Failed'}")
        
        if success:
            stats = manager.get_manager_stats()
            print(f"   Active symbols: {stats.active_symbols}/{stats.total_symbols}")
            print(f"   Error symbols: {stats.error_symbols}")
        
        # Test context isolation
        print(f"\n🔒 Testing context isolation...")
        
        if success and stats.active_symbols > 0:
            # Get first active context
            contexts = manager.get_all_contexts()
            active_context = None
            
            for context in contexts.values():
                if context.get_stats().status == ContextStatus.ACTIVE:
                    active_context = context
                    break
            
            if active_context:
                symbol = active_context.symbol
                print(f"   Testing isolation with {symbol}...")
                
                # Pause one context
                manager.pause_symbol(symbol)
                
                # Check that other contexts are still active
                time.sleep(2)
                
                all_data = manager.get_all_symbol_data()
                paused_count = sum(1 for data in all_data.values() if data['status'] == 'paused')
                active_count = sum(1 for data in all_data.values() if data['status'] == 'active')
                
                print(f"   Paused: {paused_count}, Active: {active_count}")
                print(f"   Isolation: {'✅ Working' if active_count > 0 else '❌ Failed'}")
                
                # Resume
                manager.resume_symbol(symbol)
        
        # Cleanup
        if success:
            manager.stop()
        
    except Exception as e:
        print(f"❌ Error in error handling test: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all multi-symbol context tests"""
    print("🚀 Multi-Symbol Context Management System Testing")
    print("=" * 70)
    
    # Test single context
    single_context = test_single_context_with_real_data()
    if not single_context:
        print("❌ Single context test failed")
    
    # Test multi-symbol manager
    manager = test_multi_symbol_manager()
    if not manager:
        print("❌ Multi-symbol manager test failed")
    
    # Test performance and scalability
    test_performance_and_scalability()
    
    # Test error handling
    test_error_handling_and_recovery()
    
    print("\n🎉 All multi-symbol context tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()