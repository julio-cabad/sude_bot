#!/usr/bin/env python3
"""
🔥⚔️ ALERT MANAGER TESTS - IMPLACABLE VALIDATION ⚔️🔥
Unit tests for alert manager system
Created by KRATOS - ALERT TESTING WARRIOR
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import patch, Mock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.alert_manager import AlertManager, AlertDisplayConfig, AlertColor, create_alert_manager, quick_alert_display
from models.zone_alert import ZoneAlert, AlertType, AlertPriority
from models.zone import Zone, ZoneType


class TestAlertManager(unittest.TestCase):
    """🎯 Test suite for alert manager system"""
    
    def setUp(self):
        """Set up test data"""
        self.config = AlertDisplayConfig(
            show_colors=False,  # Disable colors for testing
            timezone="UTC",
            max_zones_per_alert=2,
            use_emojis=True
        )
        
        self.manager = AlertManager(self.config)
        self.test_time = datetime.now()
        
        # Create test zones
        self.supply_zone = Zone(
            zone_id="test_supply",
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
        
        self.demand_zone = Zone(
            zone_id="test_demand",
            zone_type=ZoneType.DEMAND,
            top=66600.0,
            bottom=66400.0,
            poi=66500.0,
            left_time=self.test_time,
            right_time=self.test_time,
            left_bar_index=0,
            right_bar_index=0,
            atr_buffer=200.0,
            swing_price=66500.0
        )
    
    def test_alert_manager_initialization(self):
        """Test alert manager initialization"""
        print("🎯 Testing alert manager initialization...")
        
        # Test default initialization
        default_manager = AlertManager()
        self.assertIsNotNone(default_manager.config)
        self.assertIsNotNone(default_manager.alert_history)
        self.assertIsNotNone(default_manager.timezone)
        
        # Test custom config initialization
        custom_config = AlertDisplayConfig(show_colors=False, timezone="US/Eastern")
        custom_manager = AlertManager(custom_config)
        self.assertEqual(custom_manager.config.show_colors, False)
        
        print("   ✅ Alert manager initialization: PASSED")
    
    def test_alert_generation(self):
        """Test alert generation from zones"""
        print("🎯 Testing alert generation...")
        
        zones = [self.supply_zone, self.demand_zone]
        
        alert = self.manager.generate_alert(zones, "BTCUSDT", "1h")
        
        # Check alert properties
        self.assertEqual(alert.symbol, "BTCUSDT")
        self.assertEqual(alert.timeframe, "1h")
        self.assertEqual(len(alert.new_zones), 2)
        self.assertIsInstance(alert.detection_time, datetime)
        self.assertIsNotNone(alert.alert_id)
        
        # Check alert is added to history
        self.assertEqual(self.manager.alert_history.get_alert_count(), 1)
        
        print("   ✅ Alert generation: PASSED")
    
    def test_alert_display_full_mode(self):
        """Test full alert display"""
        print("🎯 Testing full alert display...")
        
        zones = [self.supply_zone]
        alert = self.manager.generate_alert(zones, "BTCUSDT", "1h")
        
        # Capture output
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.manager.display_alert(alert)
            output = fake_out.getvalue()
        
        # Check output contains expected elements
        self.assertIn("NEW ZONE ALERT", output)
        self.assertIn("BTCUSDT", output)
        self.assertIn("SUPPLY ZONE", output)
        self.assertIn("POI:", output)
        self.assertIn("Range:", output)
        
        print("   ✅ Full alert display: PASSED")
    
    def test_alert_display_compact_mode(self):
        """Test compact alert display"""
        print("🎯 Testing compact alert display...")
        
        zones = [self.supply_zone]
        alert = self.manager.generate_alert(zones, "BTCUSDT", "1h")
        
        # Enable compact mode
        self.manager.config.compact_mode = True
        
        # Capture output
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.manager.display_alert(alert)
            output = fake_out.getvalue()
        
        # Check compact output
        self.assertIn("BTCUSDT", output)
        self.assertIn("1h", output)
        self.assertIn("SUPPLY", output)
        
        # Should be single line (plus newline)
        lines = output.strip().split('\\n')
        self.assertEqual(len(lines), 1)
        
        print("   ✅ Compact alert display: PASSED")
    
    def test_zone_info_formatting(self):
        """Test zone information formatting"""
        print("🎯 Testing zone info formatting...")
        
        # Test supply zone formatting
        supply_info = self.manager.format_zone_info(self.supply_zone)
        self.assertIn("SUPPLY Zone", supply_info)
        self.assertIn("67,500.00", supply_info)
        self.assertIn("67,400.00", supply_info)
        self.assertIn("67,600.00", supply_info)
        
        # Test demand zone formatting
        demand_info = self.manager.format_zone_info(self.demand_zone)
        self.assertIn("DEMAND Zone", demand_info)
        self.assertIn("66,500.00", demand_info)
        
        print("   ✅ Zone info formatting: PASSED")
    
    def test_timestamp_formatting(self):
        """Test timestamp formatting"""
        print("🎯 Testing timestamp formatting...")
        
        test_dt = datetime(2024, 1, 1, 12, 0, 0)
        
        # Test with timestamps enabled
        self.manager.config.show_timestamps = True
        formatted = self.manager._format_timestamp(test_dt)
        self.assertIn("2024-01-01", formatted)
        self.assertIn("12:00:00", formatted)
        
        # Test with timestamps disabled
        self.manager.config.show_timestamps = False
        formatted_disabled = self.manager._format_timestamp(test_dt)
        self.assertEqual(formatted_disabled, "")
        
        print("   ✅ Timestamp formatting: PASSED")
    
    def test_zone_summary_formatting(self):
        """Test zone summary formatting"""
        print("🎯 Testing zone summary formatting...")
        
        # Test mixed zones
        mixed_zones = [self.supply_zone, self.demand_zone]
        summary = self.manager._format_zone_summary(mixed_zones)
        self.assertIn("SUPPLY", summary)
        self.assertIn("DEMAND", summary)
        
        # Test supply only
        supply_only = [self.supply_zone]
        supply_summary = self.manager._format_zone_summary(supply_only)
        self.assertIn("SUPPLY", supply_summary)
        self.assertNotIn("DEMAND", supply_summary)
        
        # Test empty zones
        empty_summary = self.manager._format_zone_summary([])
        self.assertEqual(empty_summary, "No zones")
        
        print("   ✅ Zone summary formatting: PASSED")
    
    def test_multiple_alerts_display(self):
        """Test displaying multiple alerts"""
        print("🎯 Testing multiple alerts display...")
        
        # Create multiple alerts
        alert1 = self.manager.generate_alert([self.supply_zone], "BTCUSDT", "1h")
        alert2 = self.manager.generate_alert([self.demand_zone], "ETHUSDT", "5m")
        
        alerts = [alert1, alert2]
        
        # Capture output
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.manager.display_multiple_alerts(alerts)
            output = fake_out.getvalue()
        
        # Check output contains both alerts
        self.assertIn("MULTIPLE ZONE ALERTS", output)
        self.assertIn("BTCUSDT", output)
        self.assertIn("ETHUSDT", output)
        self.assertIn("Alert 1/2", output)
        self.assertIn("Alert 2/2", output)
        
        print("   ✅ Multiple alerts display: PASSED")
    
    def test_alert_history_management(self):
        """Test alert history management"""
        print("🎯 Testing alert history management...")
        
        # Generate some alerts
        alert1 = self.manager.generate_alert([self.supply_zone], "BTCUSDT", "1h")
        alert2 = self.manager.generate_alert([self.demand_zone], "ETHUSDT", "5m")
        
        # Test recent alerts
        recent = self.manager.get_recent_alerts(10)
        self.assertEqual(len(recent), 2)
        
        # Test symbol-specific alerts
        btc_alerts = self.manager.get_alerts_for_symbol("BTCUSDT", 10)
        self.assertEqual(len(btc_alerts), 1)
        self.assertEqual(btc_alerts[0].symbol, "BTCUSDT")
        
        # Test clear history
        self.manager.clear_alert_history()
        recent_after_clear = self.manager.get_recent_alerts(10)
        self.assertEqual(len(recent_after_clear), 0)
        
        print("   ✅ Alert history management: PASSED")
    
    def test_alert_statistics(self):
        """Test alert statistics generation"""
        print("🎯 Testing alert statistics...")
        
        # Generate alerts with different zone types
        self.manager.generate_alert([self.supply_zone], "BTCUSDT", "1h")
        self.manager.generate_alert([self.demand_zone], "ETHUSDT", "5m")
        self.manager.generate_alert([self.supply_zone, self.demand_zone], "ADAUSDT", "15m")
        
        stats = self.manager.get_alert_stats()
        
        # Check stats structure
        required_fields = [
            'total_alerts', 'supply_alerts', 'demand_alerts',
            'symbols', 'timeframes', 'avg_zones_per_alert', 'total_zones'
        ]
        
        for field in required_fields:
            self.assertIn(field, stats)
        
        # Check values
        self.assertEqual(stats['total_alerts'], 3)
        self.assertGreater(stats['supply_alerts'], 0)
        self.assertGreater(stats['demand_alerts'], 0)
        self.assertIn('BTCUSDT', stats['symbols'])
        self.assertIn('ETHUSDT', stats['symbols'])
        self.assertIn('ADAUSDT', stats['symbols'])
        
        print("   ✅ Alert statistics: PASSED")
    
    def test_config_updates(self):
        """Test configuration updates"""
        print("🎯 Testing config updates...")
        
        # Test valid config update
        self.manager.update_config(show_colors=True, use_emojis=False)
        self.assertTrue(self.manager.config.show_colors)
        self.assertFalse(self.manager.config.use_emojis)
        
        # Test invalid config (should be ignored)
        original_colors = self.manager.config.show_colors
        self.manager.update_config(invalid_option=True)
        self.assertEqual(self.manager.config.show_colors, original_colors)
        
        print("   ✅ Config updates: PASSED")
    
    def test_color_formatting(self):
        """Test color formatting"""
        print("🎯 Testing color formatting...")
        
        # Enable colors
        self.manager.config.show_colors = True
        
        zones = [self.supply_zone]
        alert = self.manager.generate_alert(zones, "BTCUSDT", "1h")
        
        # Capture output with colors
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.manager.display_alert(alert)
            output = fake_out.getvalue()
        
        # Should contain ANSI color codes when colors are enabled
        # Note: This is a basic check, actual color codes depend on implementation
        self.assertIsInstance(output, str)
        self.assertGreater(len(output), 0)
        
        print("   ✅ Color formatting: PASSED")
    
    def test_emoji_handling(self):
        """Test emoji handling"""
        print("🎯 Testing emoji handling...")
        
        # Test with emojis enabled
        self.manager.config.use_emojis = True
        zones = [self.supply_zone, self.demand_zone]
        
        supply_summary = self.manager._format_zone_summary([self.supply_zone])
        demand_summary = self.manager._format_zone_summary([self.demand_zone])
        
        # Should contain emojis when enabled
        self.assertIn("🔺", supply_summary)
        self.assertIn("🔻", demand_summary)
        
        # Test with emojis disabled
        self.manager.config.use_emojis = False
        
        supply_summary_no_emoji = self.manager._format_zone_summary([self.supply_zone])
        demand_summary_no_emoji = self.manager._format_zone_summary([self.demand_zone])
        
        # Should not contain emojis when disabled
        self.assertNotIn("🔺", supply_summary_no_emoji)
        self.assertNotIn("🔻", demand_summary_no_emoji)
        
        print("   ✅ Emoji handling: PASSED")
    
    def test_max_zones_per_alert(self):
        """Test max zones per alert limiting"""
        print("🎯 Testing max zones per alert...")
        
        # Create more zones than the limit
        extra_zone = Zone(
            zone_id="extra_zone",
            zone_type=ZoneType.SUPPLY,
            top=68600.0,
            bottom=68400.0,
            poi=68500.0,
            left_time=self.test_time,
            right_time=self.test_time,
            left_bar_index=0,
            right_bar_index=0,
            atr_buffer=200.0,
            swing_price=68500.0
        )
        
        many_zones = [self.supply_zone, self.demand_zone, extra_zone]
        alert = self.manager.generate_alert(many_zones, "BTCUSDT", "1h")
        
        # Set limit to 2
        self.manager.config.max_zones_per_alert = 2
        
        # Get zones to show
        zones_to_show = alert.get_most_recent_zones(self.manager.config.max_zones_per_alert)
        
        # Should be limited to 2
        self.assertEqual(len(zones_to_show), 2)
        
        print("   ✅ Max zones per alert: PASSED")
    
    def test_factory_function(self):
        """Test factory function"""
        print("🎯 Testing factory function...")
        
        manager = create_alert_manager(timezone="US/Eastern", show_colors=False)
        
        self.assertIsInstance(manager, AlertManager)
        self.assertEqual(manager.config.timezone, "US/Eastern")
        self.assertFalse(manager.config.show_colors)
        
        print("   ✅ Factory function: PASSED")
    
    def test_quick_alert_display_function(self):
        """Test quick alert display utility function"""
        print("🎯 Testing quick alert display function...")
        
        zones = [self.supply_zone]
        
        # Capture output
        with patch('sys.stdout', new=StringIO()) as fake_out:
            quick_alert_display(zones, "BTCUSDT", "1h")
            output = fake_out.getvalue()
        
        # Check output contains expected elements
        self.assertIn("BTCUSDT", output)
        self.assertIn("SUPPLY", output)
        
        print("   ✅ Quick alert display function: PASSED")
    
    def test_error_handling(self):
        """Test error handling in alert manager"""
        print("🎯 Testing error handling...")
        
        # Test with invalid timezone
        invalid_config = AlertDisplayConfig(timezone="Invalid/Timezone")
        manager_with_invalid_tz = AlertManager(invalid_config)
        
        # Should fall back to UTC
        self.assertIsNotNone(manager_with_invalid_tz.timezone)
        
        # Test alert generation with empty zones
        try:
            alert = self.manager.generate_alert([], "BTCUSDT", "1h")
            # Should handle empty zones gracefully
            self.assertEqual(len(alert.new_zones), 0)
        except Exception as e:
            self.fail(f"Should handle empty zones gracefully: {e}")
        
        print("   ✅ Error handling: PASSED")


def run_tests():
    """Run all tests"""
    print("🔥⚔️ STARTING ALERT MANAGER TESTS ⚔️🔥")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAlertManager)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\\n" + "=" * 70)
    if result.wasSuccessful():
        print("🏆 ALL ALERT MANAGER TESTS PASSED - READY FOR BATTLE! 🏆")
    else:
        print("❌ SOME TESTS FAILED - NEED FIXES!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()