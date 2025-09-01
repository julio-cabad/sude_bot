#!/usr/bin/env python3
"""
🔥⚔️ ZONE STORAGE TESTS - IMPLACABLE VALIDATION ⚔️🔥
Unit tests for zone storage system
Created by KRATOS - STORAGE TESTING WARRIOR
"""

import unittest
import tempfile
import shutil
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.zone_storage import ZoneStorage, create_zone_storage


class TestZoneStorage(unittest.TestCase):
    """🎯 Test suite for zone storage system"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.storage = ZoneStorage(
            storage_dir=self.test_dir,
            max_memory_symbols=5,
            cleanup_hours=1
        )
        
        # Test data
        self.test_zones_btc = {
            'supply': [
                {
                    'name': 'test_supply_1',
                    'poi': 67500.0,
                    'top': 67600.0,
                    'bottom': 67400.0,
                    'formation_date': '2024-01-01 12:00:00'
                }
            ],
            'demand': [
                {
                    'name': 'test_demand_1',
                    'poi': 66500.0,
                    'top': 66600.0,
                    'bottom': 66400.0,
                    'formation_date': '2024-01-01 11:00:00'
                }
            ],
            'current_price': 67000.0,
            'extraction_time': '2024-01-01 12:00:00',
            'total_swings_analyzed': 50
        }
        
        self.test_zones_eth = {
            'supply': [],
            'demand': [
                {
                    'name': 'test_demand_eth',
                    'poi': 2500.0,
                    'top': 2520.0,
                    'bottom': 2480.0,
                    'formation_date': '2024-01-01 12:30:00'
                }
            ],
            'current_price': 2510.0,
            'extraction_time': '2024-01-01 12:30:00',
            'total_swings_analyzed': 30
        }
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_storage_initialization(self):
        """Test storage system initialization"""
        print("🎯 Testing storage initialization...")
        
        # Check directory creation
        storage_path = Path(self.test_dir)
        self.assertTrue(storage_path.exists())
        self.assertTrue((storage_path / "zones").exists())
        self.assertTrue((storage_path / "metadata").exists())
        self.assertTrue((storage_path / "backups").exists())
        
        # Check initial state
        self.assertEqual(len(self.storage._memory_storage), 0)
        self.assertEqual(len(self.storage._access_times), 0)
        
        print("   ✅ Storage initialization: PASSED")
    
    def test_store_and_retrieve_zones(self):
        """Test basic store and retrieve operations"""
        print("🎯 Testing store and retrieve operations...")
        
        # Store zones
        success = self.storage.store_zones("BTCUSDT", self.test_zones_btc)
        self.assertTrue(success)
        
        # Retrieve zones
        retrieved = self.storage.get_previous_zones("BTCUSDT")
        self.assertIsNotNone(retrieved)
        
        # Check data integrity
        self.assertEqual(retrieved['current_price'], self.test_zones_btc['current_price'])
        self.assertEqual(len(retrieved['supply']), len(self.test_zones_btc['supply']))
        self.assertEqual(len(retrieved['demand']), len(self.test_zones_btc['demand']))
        
        print("   ✅ Store and retrieve: PASSED")
    
    def test_memory_storage(self):
        """Test in-memory storage functionality"""
        print("🎯 Testing memory storage...")
        
        # Store data
        self.storage.store_zones("BTCUSDT", self.test_zones_btc)
        
        # Check memory storage
        self.assertIn("BTCUSDT", self.storage._memory_storage)
        self.assertIn("BTCUSDT", self.storage._access_times)
        
        # Retrieve from memory (should be fast)
        retrieved = self.storage.get_previous_zones("BTCUSDT")
        self.assertIsNotNone(retrieved)
        
        print("   ✅ Memory storage: PASSED")
    
    def test_file_storage(self):
        """Test file-based storage functionality"""
        print("🎯 Testing file storage...")
        
        # Store data
        self.storage.store_zones("BTCUSDT", self.test_zones_btc)
        
        # Check file creation
        zones_file = Path(self.test_dir) / "zones" / "BTCUSDT.json"
        metadata_file = Path(self.test_dir) / "metadata" / "BTCUSDT_meta.json"
        
        self.assertTrue(zones_file.exists())
        self.assertTrue(metadata_file.exists())
        
        # Check file content
        with open(zones_file, 'r') as f:
            file_data = json.load(f)
        
        self.assertEqual(file_data['symbol'], 'BTCUSDT')
        self.assertIn('zones_data', file_data)
        self.assertIn('last_update', file_data)
        self.assertIn('data_hash', file_data)
        
        print("   ✅ File storage: PASSED")
    
    def test_memory_management(self):
        """Test memory usage management"""
        print("🎯 Testing memory management...")
        
        # Store more symbols than max_memory_symbols
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "XRPUSDT", "DOTUSDT", "LINKUSDT"]
        
        for i, symbol in enumerate(symbols):
            test_data = self.test_zones_btc.copy()
            test_data['current_price'] = 1000 + i  # Make each unique
            self.storage.store_zones(symbol, test_data)
        
        # Should only keep max_memory_symbols in memory
        self.assertLessEqual(len(self.storage._memory_storage), self.storage.max_memory_symbols)
        
        # But all should be stored to files
        zones_dir = Path(self.test_dir) / "zones"
        stored_files = list(zones_dir.glob("*.json"))
        self.assertEqual(len(stored_files), len(symbols))
        
        print("   ✅ Memory management: PASSED")
    
    def test_data_validation(self):
        """Test data validation"""
        print("🎯 Testing data validation...")
        
        # Test invalid storage data
        invalid_data = {'invalid': 'data'}
        self.assertFalse(self.storage._validate_storage_data(invalid_data))
        
        # Test valid storage data
        valid_data = {
            'symbol': 'BTCUSDT',
            'zones_data': self.test_zones_btc,
            'last_update': datetime.now().isoformat(),
            'data_hash': 'test_hash'
        }
        self.assertTrue(self.storage._validate_storage_data(valid_data))
        
        print("   ✅ Data validation: PASSED")
    
    def test_data_hash_calculation(self):
        """Test data hash calculation for integrity"""
        print("🎯 Testing data hash calculation...")
        
        # Calculate hash for same data twice
        hash1 = self.storage._calculate_data_hash(self.test_zones_btc)
        hash2 = self.storage._calculate_data_hash(self.test_zones_btc)
        
        # Should be identical
        self.assertEqual(hash1, hash2)
        
        # Different data should have different hash
        modified_data = self.test_zones_btc.copy()
        modified_data['current_price'] = 99999.0
        hash3 = self.storage._calculate_data_hash(modified_data)
        
        self.assertNotEqual(hash1, hash3)
        
        print("   ✅ Data hash calculation: PASSED")
    
    def test_cleanup_old_data(self):
        """Test cleanup of old data"""
        print("🎯 Testing cleanup functionality...")
        
        # Store some data
        self.storage.store_zones("BTCUSDT", self.test_zones_btc)
        self.storage.store_zones("ETHUSDT", self.test_zones_eth)
        
        # Verify data exists
        self.assertTrue(self.storage.has_data_for_symbol("BTCUSDT"))
        self.assertTrue(self.storage.has_data_for_symbol("ETHUSDT"))
        
        # Cleanup with very short age (should remove everything)
        cleaned_count = self.storage.cleanup_old_data(max_age_hours=0)
        
        # Should have cleaned some data
        self.assertGreater(cleaned_count, 0)
        
        print("   ✅ Cleanup functionality: PASSED")
    
    def test_storage_stats(self):
        """Test storage statistics"""
        print("🎯 Testing storage statistics...")
        
        # Store some data
        self.storage.store_zones("BTCUSDT", self.test_zones_btc)
        self.storage.store_zones("ETHUSDT", self.test_zones_eth)
        
        # Get stats
        stats = self.storage.get_storage_stats()
        
        # Check stats structure
        required_fields = [
            'memory_symbols', 'file_symbols', 'max_memory_symbols',
            'total_storage_size_bytes', 'total_storage_size_mb',
            'storage_directory', 'cleanup_hours'
        ]
        
        for field in required_fields:
            self.assertIn(field, stats)
        
        # Check values
        self.assertGreaterEqual(stats['memory_symbols'], 0)
        self.assertGreaterEqual(stats['file_symbols'], 0)
        self.assertEqual(stats['max_memory_symbols'], 5)  # Our test setting
        
        print("   ✅ Storage statistics: PASSED")
    
    def test_symbol_operations(self):
        """Test symbol-related operations"""
        print("🎯 Testing symbol operations...")
        
        # Initially no symbols
        symbols = self.storage.get_all_stored_symbols()
        self.assertEqual(len(symbols), 0)
        
        # Store data for symbols
        self.storage.store_zones("BTCUSDT", self.test_zones_btc)
        self.storage.store_zones("ETHUSDT", self.test_zones_eth)
        
        # Check symbol detection
        self.assertTrue(self.storage.has_data_for_symbol("BTCUSDT"))
        self.assertTrue(self.storage.has_data_for_symbol("ETHUSDT"))
        self.assertFalse(self.storage.has_data_for_symbol("ADAUSDT"))
        
        # Get all symbols
        symbols = self.storage.get_all_stored_symbols()
        self.assertIn("BTCUSDT", symbols)
        self.assertIn("ETHUSDT", symbols)
        self.assertEqual(len(symbols), 2)
        
        print("   ✅ Symbol operations: PASSED")
    
    def test_case_insensitive_symbols(self):
        """Test case-insensitive symbol handling"""
        print("🎯 Testing case-insensitive symbols...")
        
        # Store with lowercase
        self.storage.store_zones("btcusdt", self.test_zones_btc)
        
        # Retrieve with uppercase
        retrieved = self.storage.get_previous_zones("BTCUSDT")
        self.assertIsNotNone(retrieved)
        
        # Check with mixed case
        self.assertTrue(self.storage.has_data_for_symbol("BtcUsDt"))
        
        print("   ✅ Case-insensitive symbols: PASSED")
    
    def test_backup_functionality(self):
        """Test backup file creation"""
        print("🎯 Testing backup functionality...")
        
        # Store initial data
        self.storage.store_zones("BTCUSDT", self.test_zones_btc)
        
        # Store updated data (should create backup)
        updated_data = self.test_zones_btc.copy()
        updated_data['current_price'] = 68000.0
        self.storage.store_zones("BTCUSDT", updated_data)
        
        # Check backup directory
        backup_dir = Path(self.test_dir) / "backups"
        backup_files = list(backup_dir.glob("BTCUSDT_*.json"))
        
        # Should have at least one backup
        self.assertGreater(len(backup_files), 0)
        
        print("   ✅ Backup functionality: PASSED")
    
    def test_factory_function(self):
        """Test factory function"""
        print("🎯 Testing factory function...")
        
        # Create storage using factory
        temp_dir = tempfile.mkdtemp()
        try:
            storage = create_zone_storage(temp_dir)
            self.assertIsInstance(storage, ZoneStorage)
            self.assertEqual(str(storage.storage_dir), temp_dir)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        print("   ✅ Factory function: PASSED")
    
    def test_clear_all_data(self):
        """Test clearing all data"""
        print("🎯 Testing clear all data...")
        
        # Store some data
        self.storage.store_zones("BTCUSDT", self.test_zones_btc)
        self.storage.store_zones("ETHUSDT", self.test_zones_eth)
        
        # Verify data exists
        self.assertGreater(len(self.storage.get_all_stored_symbols()), 0)
        
        # Clear all data
        success = self.storage.clear_all_data()
        self.assertTrue(success)
        
        # Verify data is gone
        self.assertEqual(len(self.storage.get_all_stored_symbols()), 0)
        self.assertEqual(len(self.storage._memory_storage), 0)
        
        print("   ✅ Clear all data: PASSED")


def run_tests():
    """Run all tests"""
    print("🔥⚔️ STARTING ZONE STORAGE TESTS ⚔️🔥")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestZoneStorage)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("🏆 ALL STORAGE TESTS PASSED - READY FOR BATTLE! 🏆")
    else:
        print("❌ SOME TESTS FAILED - NEED FIXES!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()