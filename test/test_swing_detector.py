#!/usr/bin/env python3
"""
Comprehensive test suite for Swing Detection with REAL Binance data
Tests swing detection, classification, and multi-symbol support with actual market data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from core.swing_detector import (
    SwingDetector, MultiSymbolSwingDetector, SwingPoint, SwingType, SwingLabel,
    get_multi_swing_detector
)
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


def test_single_symbol_swing_detection():
    """Test swing detection with real Binance data for single symbol"""
    print("\n🧪 Testing Single Symbol Swing Detection with Real Data...")
    print("=" * 70)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return None
    
    try:
        symbol = "BTCUSDT"
        swing_length = 10
        
        print(f"🎯 Testing swing detection for {symbol} (length={swing_length})")
        
        # Create swing detector
        detector = SwingDetector(symbol=symbol, swing_length=swing_length, timeframe="1h")
        
        # Initialize with real data
        print(f"🔧 Initializing detector...")
        start_time = time.time()
        
        if not detector.initialize():
            print("❌ Failed to initialize swing detector")
            return None
        
        init_time = time.time() - start_time
        print(f"✅ Detector initialized in {init_time:.2f}s")
        
        # Get initial swing detection results
        print(f"\n📊 Initial Swing Detection Results:")
        
        # Get recent swings
        recent_swings = detector.get_recent_swings(count=10)
        print(f"   Recent swings detected: {len(recent_swings)}")
        
        if recent_swings:
            print(f"   Swing breakdown:")
            highs = [s for s in recent_swings if s.swing_type == SwingType.HIGH]
            lows = [s for s in recent_swings if s.swing_type == SwingType.LOW]
            print(f"      Highs: {len(highs)}")
            print(f"      Lows: {len(lows)}")
            
            # Show last few swings with details
            print(f"\n   Last 5 swings:")
            for i, swing in enumerate(recent_swings[-5:]):
                print(f"      {i+1}. {swing.swing_type.value.upper()} {swing.label.value} at ${swing.price:.2f}")
                print(f"         Time: {swing.timestamp.strftime('%Y-%m-%d %H:%M')}")
                print(f"         Confirmed: {swing.confirmed}")
                if swing.volume:
                    print(f"         Volume: {swing.volume:,.0f}")
        
        # Test market structure analysis
        print(f"\n📈 Market Structure Analysis:")
        structure = detector.get_swing_structure()
        
        print(f"   Trend: {structure['trend']}")
        print(f"   Structure: {structure['structure']}")
        print(f"   Total swings: {structure['swing_count']}")
        print(f"   Highs: {structure['highs_count']}")
        print(f"   Lows: {structure['lows_count']}")
        
        if structure['last_high']:
            last_high = structure['last_high']
            print(f"   Last High: ${last_high.price:.2f} ({last_high.label.value})")
        
        if structure['last_low']:
            last_low = structure['last_low']
            print(f"   Last Low: ${last_low.price:.2f} ({last_low.label.value})")
        
        # Test real-time update
        print(f"\n🔄 Testing real-time swing update...")
        
        for i in range(3):
            print(f"   Update {i+1}...")
            update_start = time.time()
            
            new_swings = detector.update_with_new_candle()
            update_time = (time.time() - update_start) * 1000
            
            print(f"      New swings detected: {len(new_swings)}")
            print(f"      Update time: {update_time:.2f}ms")
            
            for swing in new_swings:
                print(f"      → {swing.swing_type.value.upper()} {swing.label.value} at ${swing.price:.2f}")
            
            time.sleep(2)  # Wait between updates
        
        # Get performance statistics
        print(f"\n📊 Performance Statistics:")
        stats = detector.get_stats()
        
        print(f"   Total swings detected: {stats.total_swings_detected}")
        print(f"   Highs detected: {stats.highs_detected}")
        print(f"   Lows detected: {stats.lows_detected}")
        print(f"   Confirmed swings: {stats.confirmed_swings}")
        print(f"   HH count: {stats.hh_count}")
        print(f"   HL count: {stats.hl_count}")
        print(f"   LH count: {stats.lh_count}")
        print(f"   LL count: {stats.ll_count}")
        print(f"   Avg detection time: {stats.avg_detection_time_ms:.2f}ms")
        
        return detector
        
    except Exception as e:
        print(f"❌ Error in single symbol swing detection test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_swing_classification_accuracy():
    """Test swing classification accuracy with real market data"""
    print("\n🧪 Testing Swing Classification Accuracy...")
    print("=" * 70)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return
    
    try:
        symbol = "ETHUSDT"
        detector = SwingDetector(symbol=symbol, swing_length=8, timeframe="1h")
        
        print(f"🎯 Testing swing classification for {symbol}")
        
        if not detector.initialize():
            print("❌ Failed to initialize detector")
            return
        
        # Get swings and analyze classification
        recent_swings = detector.get_recent_swings(count=20)
        
        if len(recent_swings) < 4:
            print("⚠️ Insufficient swings for classification analysis")
            return
        
        print(f"📊 Classification Analysis ({len(recent_swings)} swings):")
        
        # Count each label type
        label_counts = {}
        for swing in recent_swings:
            label = swing.label.value
            label_counts[label] = label_counts.get(label, 0) + 1
        
        print(f"   Label distribution:")
        for label, count in label_counts.items():
            percentage = (count / len(recent_swings)) * 100
            print(f"      {label}: {count} ({percentage:.1f}%)")
        
        # Analyze trend consistency
        print(f"\n📈 Trend Analysis:")
        
        # Check for bullish patterns (HH, HL)
        bullish_swings = sum(1 for s in recent_swings if s.label in [SwingLabel.HH, SwingLabel.HL])
        bearish_swings = sum(1 for s in recent_swings if s.label in [SwingLabel.LL, SwingLabel.LH])
        
        print(f"   Bullish signals (HH+HL): {bullish_swings}")
        print(f"   Bearish signals (LL+LH): {bearish_swings}")
        
        if bullish_swings > bearish_swings:
            print(f"   → Trend indication: BULLISH")
        elif bearish_swings > bullish_swings:
            print(f"   → Trend indication: BEARISH")
        else:
            print(f"   → Trend indication: SIDEWAYS")
        
        # Show swing sequence for pattern analysis
        print(f"\n🔄 Recent Swing Sequence:")
        for i, swing in enumerate(recent_swings[-8:]):
            direction = "📈" if swing.swing_type == SwingType.HIGH else "📉"
            print(f"   {i+1}. {direction} {swing.label.value} at ${swing.price:.2f}")
        
        # Test structure validation
        structure = detector.get_swing_structure()
        print(f"\n🏗️ Structure Validation:")
        print(f"   Detected trend: {structure['trend']}")
        print(f"   HH/HL ratio: {structure['hh_hl_ratio']:.2f}")
        print(f"   LL/LH ratio: {structure['ll_lh_ratio']:.2f}")
        
    except Exception as e:
        print(f"❌ Error in swing classification test: {e}")
        import traceback
        traceback.print_exc()


def test_multi_symbol_swing_detection():
    """Test multi-symbol swing detection with real data"""
    print("\n🧪 Testing Multi-Symbol Swing Detection...")
    print("=" * 70)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return None
    
    try:
        config = get_config()
        test_symbols = config.symbols[:3]  # Test with first 3 symbols
        
        print(f"🎯 Testing multi-symbol swing detection with: {test_symbols}")
        
        # Create multi-symbol detector
        multi_detector = MultiSymbolSwingDetector(symbols=test_symbols)
        
        # Initialize all detectors
        print(f"🔧 Initializing detectors for {len(test_symbols)} symbols...")
        start_time = time.time()
        
        if not multi_detector.initialize_all():
            print("❌ Failed to initialize multi-symbol detector")
            return None
        
        init_time = time.time() - start_time
        print(f"✅ All detectors initialized in {init_time:.2f}s")
        print(f"   Average per symbol: {init_time/len(test_symbols):.2f}s")
        
        # Get swing data for all symbols
        print(f"\n📊 Swing Detection Results by Symbol:")
        
        total_swings = 0
        symbol_results = {}
        
        for symbol in test_symbols:
            detector = multi_detector.get_detector(symbol)
            if detector:
                recent_swings = detector.get_recent_swings(count=10)
                structure = detector.get_swing_structure()
                stats = detector.get_stats()
                
                symbol_results[symbol] = {
                    'swings': recent_swings,
                    'structure': structure,
                    'stats': stats
                }
                
                total_swings += len(recent_swings)
                
                print(f"\n   {symbol}:")
                print(f"      Recent swings: {len(recent_swings)}")
                print(f"      Trend: {structure['trend']}")
                print(f"      Total detected: {stats.total_swings_detected}")
                print(f"      Highs/Lows: {stats.highs_detected}/{stats.lows_detected}")
                print(f"      Detection time: {stats.avg_detection_time_ms:.2f}ms")
                
                if structure['last_high'] and structure['last_low']:
                    last_high = structure['last_high']
                    last_low = structure['last_low']
                    print(f"      Last High: ${last_high.price:.2f} ({last_high.label.value})")
                    print(f"      Last Low: ${last_low.price:.2f} ({last_low.label.value})")
        
        print(f"\n📈 Multi-Symbol Summary:")
        print(f"   Total symbols processed: {len(symbol_results)}")
        print(f"   Total swings detected: {total_swings}")
        print(f"   Average swings per symbol: {total_swings/len(symbol_results):.1f}")
        
        # Test concurrent updates
        print(f"\n🔄 Testing concurrent updates...")
        
        for i in range(2):
            print(f"   Update cycle {i+1}...")
            update_start = time.time()
            
            update_results = multi_detector.update_all()
            update_time = time.time() - update_start
            
            total_new_swings = sum(len(swings) for swings in update_results.values())
            
            print(f"      Update time: {update_time:.2f}s")
            print(f"      New swings detected: {total_new_swings}")
            
            for symbol, new_swings in update_results.items():
                if new_swings:
                    print(f"         {symbol}: {len(new_swings)} new swings")
                    for swing in new_swings:
                        print(f"            → {swing.swing_type.value.upper()} {swing.label.value} at ${swing.price:.2f}")
            
            time.sleep(3)
        
        # Get all market structures
        print(f"\n🏗️ Market Structure Analysis:")
        all_structures = multi_detector.get_all_structures()
        
        trend_summary = {}
        for symbol, structure in all_structures.items():
            trend = structure['trend']
            trend_summary[trend] = trend_summary.get(trend, 0) + 1
            print(f"   {symbol}: {trend} ({structure['swing_count']} swings)")
        
        print(f"\n📊 Trend Distribution:")
        for trend, count in trend_summary.items():
            percentage = (count / len(all_structures)) * 100
            print(f"   {trend}: {count} symbols ({percentage:.1f}%)")
        
        return multi_detector
        
    except Exception as e:
        print(f"❌ Error in multi-symbol swing detection test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_performance_and_accuracy():
    """Test performance and accuracy with extended real data"""
    print("\n🧪 Testing Performance and Accuracy...")
    print("=" * 70)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return
    
    try:
        symbol = "ADAUSDT"
        
        # Test different swing lengths
        swing_lengths = [5, 10, 15, 20]
        
        print(f"🎯 Testing performance with different swing lengths for {symbol}")
        
        performance_results = {}
        
        for length in swing_lengths:
            print(f"\n   Testing swing length: {length}")
            
            detector = SwingDetector(symbol=symbol, swing_length=length, timeframe="1h")
            
            # Measure initialization time
            init_start = time.time()
            if not detector.initialize():
                print(f"      ❌ Failed to initialize with length {length}")
                continue
            init_time = time.time() - init_start
            
            # Measure detection time
            detection_start = time.time()
            recent_swings = detector.get_recent_swings(count=20)
            detection_time = time.time() - detection_start
            
            # Get statistics
            stats = detector.get_stats()
            
            performance_results[length] = {
                'init_time': init_time,
                'detection_time': detection_time,
                'swings_detected': len(recent_swings),
                'total_swings': stats.total_swings_detected,
                'avg_detection_ms': stats.avg_detection_time_ms
            }
            
            print(f"      ✅ Init: {init_time:.2f}s, Detection: {detection_time*1000:.2f}ms")
            print(f"      📊 Swings: {len(recent_swings)}, Total: {stats.total_swings_detected}")
        
        # Performance analysis
        print(f"\n📊 Performance Analysis:")
        print(f"   {'Length':<8} {'Init(s)':<8} {'Detect(ms)':<12} {'Swings':<8} {'Total':<8}")
        print(f"   {'-'*50}")
        
        for length, results in performance_results.items():
            print(f"   {length:<8} {results['init_time']:<8.2f} {results['detection_time']*1000:<12.2f} "
                  f"{results['swings_detected']:<8} {results['total_swings']:<8}")
        
        # Find optimal swing length
        if performance_results:
            # Balance between speed and swing detection
            optimal_length = min(performance_results.keys(), 
                               key=lambda x: performance_results[x]['detection_time'])
            
            print(f"\n🎯 Optimal Performance:")
            print(f"   Fastest detection: Length {optimal_length}")
            print(f"   Detection time: {performance_results[optimal_length]['detection_time']*1000:.2f}ms")
            
            # Most swings detected
            most_swings_length = max(performance_results.keys(),
                                   key=lambda x: performance_results[x]['swings_detected'])
            
            print(f"   Most swings detected: Length {most_swings_length}")
            print(f"   Swings count: {performance_results[most_swings_length]['swings_detected']}")
        
    except Exception as e:
        print(f"❌ Error in performance test: {e}")
        import traceback
        traceback.print_exc()


def test_real_market_scenarios():
    """Test swing detection in various real market scenarios"""
    print("\n🧪 Testing Real Market Scenarios...")
    print("=" * 70)
    
    if not check_binance_credentials():
        print("❌ Cannot test with real data - no credentials")
        return
    
    try:
        # Test different market conditions with different symbols
        test_scenarios = [
            ("BTCUSDT", "Large Cap - High Volume"),
            ("ETHUSDT", "Large Cap - High Volatility"),
            ("ADAUSDT", "Mid Cap - Moderate Volume"),
        ]
        
        print(f"🎯 Testing swing detection across different market scenarios")
        
        scenario_results = {}
        
        for symbol, description in test_scenarios:
            print(f"\n📊 Scenario: {symbol} - {description}")
            
            try:
                detector = SwingDetector(symbol=symbol, swing_length=10, timeframe="1h")
                
                if not detector.initialize():
                    print(f"   ❌ Failed to initialize {symbol}")
                    continue
                
                # Get market data analysis
                recent_swings = detector.get_recent_swings(count=15)
                structure = detector.get_swing_structure()
                stats = detector.get_stats()
                
                # Analyze swing characteristics
                if recent_swings:
                    prices = [s.price for s in recent_swings]
                    price_range = max(prices) - min(prices)
                    avg_price = sum(prices) / len(prices)
                    volatility = price_range / avg_price * 100
                    
                    # Count swing types
                    hh_count = sum(1 for s in recent_swings if s.label == SwingLabel.HH)
                    hl_count = sum(1 for s in recent_swings if s.label == SwingLabel.HL)
                    lh_count = sum(1 for s in recent_swings if s.label == SwingLabel.LH)
                    ll_count = sum(1 for s in recent_swings if s.label == SwingLabel.LL)
                    
                    scenario_results[symbol] = {
                        'swings_count': len(recent_swings),
                        'price_range': price_range,
                        'volatility': volatility,
                        'trend': structure['trend'],
                        'hh_count': hh_count,
                        'hl_count': hl_count,
                        'lh_count': lh_count,
                        'll_count': ll_count,
                        'detection_time': stats.avg_detection_time_ms
                    }
                    
                    print(f"   ✅ Analysis complete:")
                    print(f"      Swings detected: {len(recent_swings)}")
                    print(f"      Price range: ${price_range:.2f} ({volatility:.2f}% volatility)")
                    print(f"      Trend: {structure['trend']}")
                    print(f"      Pattern: HH:{hh_count} HL:{hl_count} LH:{lh_count} LL:{ll_count}")
                    print(f"      Detection time: {stats.avg_detection_time_ms:.2f}ms")
                    
                    # Show recent swing pattern
                    print(f"      Recent pattern: ", end="")
                    for swing in recent_swings[-5:]:
                        symbol_char = "📈" if swing.swing_type == SwingType.HIGH else "📉"
                        print(f"{symbol_char}{swing.label.value}", end=" ")
                    print()
                
            except Exception as e:
                print(f"   ❌ Error testing {symbol}: {e}")
                continue
        
        # Compare scenarios
        if len(scenario_results) > 1:
            print(f"\n📈 Scenario Comparison:")
            print(f"   {'Symbol':<10} {'Swings':<8} {'Volatility':<12} {'Trend':<10} {'Speed(ms)':<10}")
            print(f"   {'-'*60}")
            
            for symbol, results in scenario_results.items():
                print(f"   {symbol:<10} {results['swings_count']:<8} {results['volatility']:<12.2f} "
                      f"{results['trend']:<10} {results['detection_time']:<10.2f}")
            
            # Find most/least volatile
            most_volatile = max(scenario_results.keys(), 
                              key=lambda x: scenario_results[x]['volatility'])
            least_volatile = min(scenario_results.keys(),
                               key=lambda x: scenario_results[x]['volatility'])
            
            print(f"\n🎯 Market Insights:")
            print(f"   Most volatile: {most_volatile} ({scenario_results[most_volatile]['volatility']:.2f}%)")
            print(f"   Least volatile: {least_volatile} ({scenario_results[least_volatile]['volatility']:.2f}%)")
            
            # Trend distribution
            trends = [results['trend'] for results in scenario_results.values()]
            trend_counts = {trend: trends.count(trend) for trend in set(trends)}
            
            print(f"   Market sentiment:")
            for trend, count in trend_counts.items():
                print(f"      {trend}: {count} symbols")
        
    except Exception as e:
        print(f"❌ Error in market scenarios test: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all swing detection tests"""
    print("🚀 Swing Detection Testing with Real Binance Data")
    print("=" * 80)
    
    # Test single symbol swing detection
    single_detector = test_single_symbol_swing_detection()
    if not single_detector:
        print("❌ Single symbol test failed")
    
    # Test swing classification accuracy
    test_swing_classification_accuracy()
    
    # Test multi-symbol swing detection
    multi_detector = test_multi_symbol_swing_detection()
    if not multi_detector:
        print("❌ Multi-symbol test failed")
    
    # Test performance and accuracy
    test_performance_and_accuracy()
    
    # Test real market scenarios
    test_real_market_scenarios()
    
    print("\n🎉 All swing detection tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()