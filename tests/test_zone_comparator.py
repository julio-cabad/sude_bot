#!/usr/bin/env python3
"""
🔥⚔️ ZONE COMPARATOR TESTS - IMPLACABLE VALIDATION ⚔️🔥
Unit tests for zone comparison system
Created by KRATOS - COMPARISON TESTING WARRIOR
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.zone_comparator import ZoneComparator, ZoneSignature, create_zone_comparator, quick_zone_comparison
from models.zone import Zone, ZoneType


class TestZoneComparator(unittest.TestCase):
    """🎯 Test suite for zone comparator system"""
    
    def setUp(self):
        """Set up test data"""
        self.comparator = ZoneComparator(
            price_tolerance=0.001,  # 0.1%
            time_tolerance_minutes=60,
            min_zone_age_minutes=0  # Disable age filtering for tests
        )
        
        self.test_time = datetime.now()
        
        # Test zone data
        self.current_zones = {
            'supply': [
                {
                    'name': 'supply_new',
                    'poi': 67500.0,
                    'top': 67600.0,
                    'bottom': 67400.0,
                    'formation_date': '2024-01-01 12:00:00',
                    'strength': 2.0,
                    'volume': 1000000
                },
                {
                    'name': 'supply_existing',
                    'poi': 68000.0,
                    'top': 68100.0,
                    'bottom': 67900.0,
                    'formation_date': '2024-01-01 10:00:00',
                    'strength': 1.5,
                    'volume': 800000
                }
            ],
            'demand': [
                {
                    'name': 'demand_new',
                    'poi': 66500.0,
                    'top': 66600.0,
                    'bottom': 66400.0,
                    'formation_date': '2024-01-01 11:30:00',
                    'strength': 1.8,
                    'volume': 1200000
                }
            ]
        }
        
        self.previous_zones = {
            'supply': [
                {
                    'name': 'supply_existing',
                    'poi': 68000.0,  # Same as current (should match)
                    'top': 68100.0,
                    'bottom': 67900.0,
                    'formation_date': '2024-01-01 10:00:00',
                    'strength': 1.5,
                    'volume': 800000
                },
                {
                    'name': 'supply_removed',
                    'poi': 69000.0,  # Not in current (should be removed)
                    'top': 69100.0,
                    'bottom': 68900.0,
                    'formation_date': '2024-01-01 09:00:00',
                    'strength': 1.0,
                    'volume': 500000
                }
            ],
            'demand': []
        }
    
    def test_zone_signature_creation(self):
        """Test zone signature creation and matching"""
        print("🎯 Testing zone signature creation...")
        
        # Create test zone using correct constructor
        zone = Zone(
            zone_id="test_zone",
            zone_type=ZoneType.SUPPLY,
            top=67600.0,
            bottom=67400.0,
            poi=67500.0,
            left_time=self.test_time,
            right_time=self.test_time,
            left_bar_index=0,
            right_bar_index=0,
            atr_buffer=200.0,
            swing_price=67500.0
        )
        
        # Create signature
        signature = self.comparator._create_zone_signature(zone)
        
        self.assertEqual(signature.poi_price, 67500.0)
        self.assertEqual(signature.zone_type, 'SUPPLY')
        self.assertEqual(signature.formation_time, self.test_time)
        
        print("   ✅ Zone signature creation: PASSED")
    
    def test_zone_signature_matching(self):
        """Test zone signature matching logic"""
        print("🎯 Testing zone signature matching...")
        
        # Create similar signatures (should match)
        sig1 = ZoneSignature(67500.0, 'SUPPLY', self.test_time)
        sig2 = ZoneSignature(67505.0, 'SUPPLY', self.test_time + timedelta(minutes=30))  # Within tolerance
        
        self.assertTrue(sig1.matches(sig2))
        
        # Create different signatures (should not match)
        sig3 = ZoneSignature(68000.0, 'SUPPLY', self.test_time)  # Different price
        sig4 = ZoneSignature(67500.0, 'DEMAND', self.test_time)  # Different type
        
        self.assertFalse(sig1.matches(sig3))
        self.assertFalse(sig1.matches(sig4))
        
        print("   ✅ Zone signature matching: PASSED")
    
    def test_zone_extraction_from_data(self):
        """Test extracting Zone objects from data dictionary"""
        print("🎯 Testing zone extraction...")
        
        zones = self.comparator._extract_zones_from_data(self.current_zones)
        
        # Should extract 3 zones total (2 supply + 1 demand)
        self.assertEqual(len(zones), 3)
        
        # Check zone types
        supply_zones = [z for z in zones if z.zone_type == ZoneType.SUPPLY]
        demand_zones = [z for z in zones if z.zone_type == ZoneType.DEMAND]
        
        self.assertEqual(len(supply_zones), 2)
        self.assertEqual(len(demand_zones), 1)
        
        # Check zone properties
        first_zone = zones[0]
        self.assertIsInstance(first_zone.poi, float)
        self.assertIsInstance(first_zone.top, float)
        self.assertIsInstance(first_zone.bottom, float)
        
        print("   ✅ Zone extraction: PASSED")
    
    def test_zone_comparison_basic(self):
        """Test basic zone comparison functionality"""
        print("🎯 Testing basic zone comparison...")
        
        comparison = self.comparator.compare_zones(
            self.current_zones, 
            self.previous_zones, 
            "BTCUSDT", 
            "1h"
        )
        
        # Check comparison structure
        self.assertEqual(comparison.symbol, "BTCUSDT")
        self.assertEqual(comparison.timeframe, "1h")
        self.assertIsInstance(comparison.comparison_time, datetime)
        
        # Should find new zones
        self.assertGreater(len(comparison.new_zones), 0)
        
        # Should find removed zones
        self.assertGreater(len(comparison.removed_zones), 0)
        
        # Should have changes
        self.assertTrue(comparison.has_changes())
        
        print("   ✅ Basic zone comparison: PASSED")
    
    def test_new_zone_detection(self):
        """Test detection of new zones"""
        print("🎯 Testing new zone detection...")
        
        comparison = self.comparator.compare_zones(
            self.current_zones, 
            self.previous_zones, 
            "BTCUSDT", 
            "1h"
        )
        
        # Should detect 2 new zones (supply_new and demand_new)
        self.assertEqual(len(comparison.new_zones), 2)
        
        # Check new zone types
        new_zone_pois = [zone.poi for zone in comparison.new_zones]
        self.assertIn(67500.0, new_zone_pois)  # supply_new
        self.assertIn(66500.0, new_zone_pois)  # demand_new
        
        print("   ✅ New zone detection: PASSED")
    
    def test_removed_zone_detection(self):
        """Test detection of removed zones"""
        print("🎯 Testing removed zone detection...")
        
        comparison = self.comparator.compare_zones(
            self.current_zones, 
            self.previous_zones, 
            "BTCUSDT", 
            "1h"
        )
        
        # Should detect 1 removed zone (supply_removed)
        self.assertEqual(len(comparison.removed_zones), 1)
        
        # Check removed zone
        removed_zone = comparison.removed_zones[0]
        self.assertEqual(removed_zone.poi, 69000.0)
        self.assertEqual(removed_zone.zone_type, ZoneType.SUPPLY)
        
        print("   ✅ Removed zone detection: PASSED")
    
    def test_unchanged_zone_detection(self):
        """Test detection of unchanged zones"""
        print("🎯 Testing unchanged zone detection...")
        
        comparison = self.comparator.compare_zones(
            self.current_zones, 
            self.previous_zones, 
            "BTCUSDT", 
            "1h"
        )
        
        # Should detect 1 unchanged zone (supply_existing)
        self.assertEqual(len(comparison.unchanged_zones), 1)
        
        # Check unchanged zone
        unchanged_zone = comparison.unchanged_zones[0]
        self.assertEqual(unchanged_zone.poi, 68000.0)
        self.assertEqual(unchanged_zone.zone_type, ZoneType.SUPPLY)
        
        print("   ✅ Unchanged zone detection: PASSED")
    
    def test_no_previous_zones(self):
        """Test comparison when no previous zones exist"""
        print("🎯 Testing comparison with no previous zones...")
        
        comparison = self.comparator.compare_zones(
            self.current_zones, 
            None,  # No previous zones
            "BTCUSDT", 
            "1h"
        )
        
        # All current zones should be new
        self.assertEqual(len(comparison.new_zones), 3)  # 2 supply + 1 demand
        self.assertEqual(len(comparison.removed_zones), 0)
        self.assertEqual(comparison.previous_count, 0)
        self.assertEqual(comparison.current_count, 3)
        
        print("   ✅ No previous zones handling: PASSED")
    
    def test_empty_current_zones(self):
        """Test comparison when current zones are empty"""
        print("🎯 Testing comparison with empty current zones...")
        
        empty_zones = {'supply': [], 'demand': []}
        
        comparison = self.comparator.compare_zones(
            empty_zones, 
            self.previous_zones, 
            "BTCUSDT", 
            "1h"
        )
        
        # No new zones, all previous should be removed
        self.assertEqual(len(comparison.new_zones), 0)
        self.assertEqual(len(comparison.removed_zones), 2)  # 2 supply zones from previous
        self.assertEqual(comparison.current_count, 0)
        
        print("   ✅ Empty current zones handling: PASSED")
    
    def test_price_tolerance(self):
        """Test price tolerance in zone matching"""
        print("🎯 Testing price tolerance...")
        
        # Create zones with slight price difference
        current_with_tolerance = {
            'supply': [
                {
                    'name': 'supply_tolerance',
                    'poi': 67500.5,  # 0.5 difference (within 0.1% tolerance)
                    'top': 67600.0,
                    'bottom': 67400.0,
                    'formation_date': '2024-01-01 10:00:00',
                    'strength': 1.5
                }
            ],
            'demand': []
        }
        
        previous_tolerance = {
            'supply': [
                {
                    'name': 'supply_base',
                    'poi': 67500.0,  # Base price
                    'top': 67600.0,
                    'bottom': 67400.0,
                    'formation_date': '2024-01-01 10:00:00',
                    'strength': 1.5
                }
            ],
            'demand': []
        }
        
        comparison = self.comparator.compare_zones(
            current_with_tolerance, 
            previous_tolerance, 
            "BTCUSDT", 
            "1h"
        )
        
        # Should match due to tolerance (no new zones)
        self.assertEqual(len(comparison.new_zones), 0)
        self.assertEqual(len(comparison.unchanged_zones), 1)
        
        print("   ✅ Price tolerance: PASSED")
    
    def test_is_zone_new_method(self):
        """Test is_zone_new method"""
        print("🎯 Testing is_zone_new method...")
        
        # Create test zones using correct constructor
        new_zone = Zone(
            zone_id="new_zone",
            zone_type=ZoneType.SUPPLY,
            top=70000.0,
            bottom=69900.0,
            poi=69950.0,
            left_time=self.test_time,
            right_time=self.test_time,
            left_bar_index=0,
            right_bar_index=0,
            atr_buffer=100.0,
            swing_price=69950.0
        )
        
        existing_zone = Zone(
            zone_id="existing_zone",
            zone_type=ZoneType.SUPPLY,
            top=68100.0,
            bottom=67900.0,
            poi=68000.0,
            left_time=self.test_time,
            right_time=self.test_time,
            left_bar_index=0,
            right_bar_index=0,
            atr_buffer=200.0,
            swing_price=68000.0
        )
        
        existing_zones = [existing_zone]
        
        # Test new zone
        self.assertTrue(self.comparator.is_zone_new(new_zone, existing_zones))
        
        # Test existing zone
        self.assertFalse(self.comparator.is_zone_new(existing_zone, existing_zones))
        
        print("   ✅ is_zone_new method: PASSED")
    
    def test_zone_signature_generation(self):
        """Test zone signature generation"""
        print("🎯 Testing zone signature generation...")
        
        zone = Zone(
            zone_id="test_zone",
            zone_type=ZoneType.SUPPLY,
            top=67600.0,
            bottom=67400.0,
            poi=67500.0,
            left_time=self.test_time,
            right_time=self.test_time,
            left_bar_index=0,
            right_bar_index=0,
            atr_buffer=200.0,
            swing_price=67500.0
        )
        
        signature = self.comparator.get_zone_signature(zone)
        
        self.assertIsInstance(signature, str)
        self.assertGreater(len(signature), 0)
        
        # Same zone should produce same signature
        signature2 = self.comparator.get_zone_signature(zone)
        self.assertEqual(signature, signature2)
        
        print("   ✅ Zone signature generation: PASSED")
    
    def test_comparison_stats(self):
        """Test comparison statistics generation"""
        print("🎯 Testing comparison statistics...")
        
        comparison = self.comparator.compare_zones(
            self.current_zones, 
            self.previous_zones, 
            "BTCUSDT", 
            "1h"
        )
        
        stats = self.comparator.get_comparison_stats(comparison)
        
        # Check stats structure
        required_fields = [
            'total_new_zones', 'new_supply_zones', 'new_demand_zones',
            'total_removed_zones', 'removed_supply_zones', 'removed_demand_zones',
            'unchanged_zones', 'net_zone_change', 'comparison_time',
            'has_significant_changes'
        ]
        
        for field in required_fields:
            self.assertIn(field, stats)
        
        # Check values
        self.assertGreaterEqual(stats['total_new_zones'], 0)
        self.assertGreaterEqual(stats['total_removed_zones'], 0)
        self.assertTrue(stats['has_significant_changes'])  # Should have changes
        
        print("   ✅ Comparison statistics: PASSED")
    
    def test_tolerance_adjustment(self):
        """Test tolerance adjustment"""
        print("🎯 Testing tolerance adjustment...")
        
        # Test initial tolerance
        self.assertEqual(self.comparator.price_tolerance, 0.001)
        
        # Adjust tolerance
        self.comparator.set_tolerance(price_tolerance=0.002, time_tolerance_minutes=120)
        
        self.assertEqual(self.comparator.price_tolerance, 0.002)
        self.assertEqual(self.comparator.time_tolerance_minutes, 120)
        
        print("   ✅ Tolerance adjustment: PASSED")
    
    def test_zone_age_filtering(self):
        """Test zone age filtering"""
        print("🎯 Testing zone age filtering...")
        
        # Create comparator with age filtering
        age_comparator = ZoneComparator(min_zone_age_minutes=60)  # 1 hour minimum
        
        # Create zones with different ages
        old_time = datetime.now() - timedelta(hours=2)  # 2 hours ago (should pass)
        new_time = datetime.now() - timedelta(minutes=30)  # 30 minutes ago (should be filtered)
        
        zones = [
            Zone(
                zone_id="old_zone",
                zone_type=ZoneType.SUPPLY,
                top=67600.0,
                bottom=67400.0,
                poi=67500.0,
                left_time=old_time,
                right_time=old_time,
                left_bar_index=0,
                right_bar_index=0,
                atr_buffer=200.0,
                swing_price=67500.0
            ),
            Zone(
                zone_id="new_zone",
                zone_type=ZoneType.SUPPLY,
                top=68600.0,
                bottom=68400.0,
                poi=68500.0,
                left_time=new_time,
                right_time=new_time,
                left_bar_index=0,
                right_bar_index=0,
                atr_buffer=200.0,
                swing_price=68500.0
            )
        ]
        
        filtered_zones = age_comparator._filter_zones_by_age(zones)
        
        # Should only keep the old zone
        self.assertEqual(len(filtered_zones), 1)
        self.assertEqual(filtered_zones[0].left_time, old_time)
        
        print("   ✅ Zone age filtering: PASSED")
    
    def test_factory_function(self):
        """Test factory function"""
        print("🎯 Testing factory function...")
        
        comparator = create_zone_comparator(price_tolerance=0.005)
        
        self.assertIsInstance(comparator, ZoneComparator)
        self.assertEqual(comparator.price_tolerance, 0.005)
        
        print("   ✅ Factory function: PASSED")
    
    def test_quick_comparison_function(self):
        """Test quick comparison utility function"""
        print("🎯 Testing quick comparison function...")
        
        # Test with new zones
        has_new = quick_zone_comparison(self.current_zones, self.previous_zones, "BTCUSDT")
        self.assertTrue(has_new)
        
        # Test with no changes
        has_new_same = quick_zone_comparison(self.current_zones, self.current_zones, "BTCUSDT")
        self.assertFalse(has_new_same)
        
        print("   ✅ Quick comparison function: PASSED")
    
    def test_error_handling(self):
        """Test error handling in comparison"""
        print("🎯 Testing error handling...")
        
        # Test with invalid data
        invalid_zones = {'invalid': 'data'}
        
        comparison = self.comparator.compare_zones(
            invalid_zones, 
            self.previous_zones, 
            "BTCUSDT", 
            "1h"
        )
        
        # Should return valid comparison object even with errors
        self.assertIsInstance(comparison.comparison_time, datetime)
        self.assertEqual(comparison.symbol, "BTCUSDT")
        
        print("   ✅ Error handling: PASSED")


def run_tests():
    """Run all tests"""
    print("🔥⚔️ STARTING ZONE COMPARATOR TESTS ⚔️🔥")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestZoneComparator)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("🏆 ALL COMPARATOR TESTS PASSED - READY FOR BATTLE! 🏆")
    else:
        print("❌ SOME TESTS FAILED - NEED FIXES!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()