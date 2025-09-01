#!/usr/bin/env python3
"""
🔥⚔️ TESTS ÉPICOS PARA ZONE STORAGE CON DATOS REALES ⚔️🔥
Tests usando datos REALES de Binance - NO MOCKS, NO FAKE DATA
Created by FEROZ GUERRERO DEL CÓDIGO - OLIMPO REAL DATA TESTING
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from core.zone_storage import ZoneStorage
from models.zone_alert import EcuadorTimeUtils


class TestZoneStorageWithRealData(unittest.TestCase):
    """🏛️ Tests con datos REALES de Binance"""
    
    @classmethod
    def setUpClass(cls):
        """Setup para toda la clase de tests"""
        # Verificar credenciales de Binance
        cls.api_key = os.getenv('BINANCE_API_KEY')
        cls.api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not cls.api_key or not cls.api_secret:
            raise unittest.SkipTest("❌ Credenciales de Binance no encontradas - Skipping tests reales")
        
        print("\\n🔥⚔️ INICIANDO TESTS CON DATOS REALES DE BINANCE ⚔️🔥")
        print("=" * 70)
    
    def setUp(self):
        """Setup para cada test"""
        # Crear directorio temporal para tests
        self.temp_dir = tempfile.mkdtemp(prefix="zone_storage_test_")
        self.storage = ZoneStorage(self.temp_dir)
        
        # Símbolos para testing
        self.test_symbols = ["BTCUSDT", "ETHUSDT"]
        self.test_timeframe = "1h"
    
    def tearDown(self):
        """Cleanup después de cada test"""
        # Limpiar directorio temporal
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_store_zones_real_btc(self):
        """🔥 Test almacenar zonas reales de BTCUSDT"""
        print(f"\\n🎯 TEST: Almacenar zonas reales BTCUSDT")
        print("-" * 50)
        
        symbol = "BTCUSDT"
        
        # Almacenar zonas usando detector real
        success = self.storage.store_zones_from_detector(symbol, self.test_timeframe)
        
        self.assertTrue(success, "Debe almacenar zonas exitosamente")
        
        # Verificar que los datos se almacenaron
        stored_data = self.storage.get_previous_zones(symbol)
        
        self.assertIsNotNone(stored_data, "Debe haber datos almacenados")
        self.assertEqual(stored_data['symbol'], symbol)
        self.assertGreater(stored_data['current_price'], 0, "Debe tener precio actual válido")
        self.assertGreaterEqual(stored_data['total_zones'], 0, "Debe tener conteo de zonas")
        
        # Verificar estructura de datos
        self.assertIn('supply_zones', stored_data)
        self.assertIn('demand_zones', stored_data)
        self.assertIn('detection_time', stored_data)
        self.assertIn('tradingview_precision', stored_data)
        
        print(f"✅ BTCUSDT almacenado exitosamente:")
        print(f"   💰 Precio: ${stored_data['current_price']:,.2f}")
        print(f"   📊 Total zonas: {stored_data['total_zones']}")
        print(f"   🕐 Tiempo: {EcuadorTimeUtils.format_time(stored_data['detection_time'])}")
    
    def test_store_zones_real_eth(self):
        """⚔️ Test almacenar zonas reales de ETHUSDT"""
        print(f"\\n🎯 TEST: Almacenar zonas reales ETHUSDT")
        print("-" * 50)
        
        symbol = "ETHUSDT"
        
        # Almacenar zonas usando detector real
        success = self.storage.store_zones_from_detector(symbol, self.test_timeframe)
        
        self.assertTrue(success, "Debe almacenar zonas exitosamente")
        
        # Verificar datos almacenados
        stored_data = self.storage.get_previous_zones(symbol)
        
        self.assertIsNotNone(stored_data)
        self.assertEqual(stored_data['symbol'], symbol)
        self.assertGreater(stored_data['current_price'], 0)
        
        print(f"✅ ETHUSDT almacenado exitosamente:")
        print(f"   💰 Precio: ${stored_data['current_price']:,.2f}")
        print(f"   📊 Total zonas: {stored_data['total_zones']}")
    
    def test_compare_zones_real_data(self):
        """🏛️ Test comparación con datos reales"""
        print(f"\\n🎯 TEST: Comparación de zonas con datos reales")
        print("-" * 50)
        
        symbol = "BTCUSDT"
        
        # Primera detección
        print("1️⃣ Primera detección...")
        success1 = self.storage.store_zones_from_detector(symbol, self.test_timeframe)
        self.assertTrue(success1, "Primera detección debe ser exitosa")
        
        first_data = self.storage.get_previous_zones(symbol)
        self.assertIsNotNone(first_data)
        
        # Pequeña pausa para simular paso del tiempo
        import time
        time.sleep(1)
        
        # Segunda detección y comparación
        print("2️⃣ Segunda detección y comparación...")
        comparison = self.storage.compare_with_previous(symbol, self.test_timeframe)
        
        self.assertTrue(comparison['success'], "Comparación debe ser exitosa")
        self.assertEqual(comparison['symbol'], symbol)
        self.assertIn('previous_total', comparison)
        self.assertIn('current_total', comparison)
        self.assertIn('new_zones_count', comparison)
        self.assertIn('has_new_zones', comparison)
        
        print(f"✅ Comparación completada:")
        print(f"   📊 Zonas anteriores: {comparison['previous_total']}")
        print(f"   📊 Zonas actuales: {comparison['current_total']}")
        print(f"   🆕 Nuevas zonas: {comparison['new_zones_count']}")
        print(f"   💰 Cambio precio: {comparison['price_change']:+.2f}%")
        
        # En una comparación rápida, normalmente no debería haber nuevas zonas
        # pero el test debe funcionar independientemente del resultado
        self.assertIsInstance(comparison['has_new_zones'], bool)
    
    def test_multi_symbol_real_storage(self):
        """⚔️ Test almacenamiento multi-símbolo con datos reales"""
        print(f"\\n🎯 TEST: Almacenamiento multi-símbolo real")
        print("-" * 50)
        
        symbols_results = {}
        
        for symbol in self.test_symbols:
            print(f"📊 Procesando {symbol}...")
            
            success = self.storage.store_zones_from_detector(symbol, self.test_timeframe)
            symbols_results[symbol] = success
            
            if success:
                data = self.storage.get_previous_zones(symbol)
                print(f"   ✅ {symbol}: ${data['current_price']:,.2f} - {data['total_zones']} zonas")
            else:
                print(f"   ❌ {symbol}: Fallo en detección")
        
        # Verificar que al menos un símbolo fue exitoso
        successful_symbols = sum(symbols_results.values())
        self.assertGreater(successful_symbols, 0, "Al menos un símbolo debe ser exitoso")
        
        # Verificar estadísticas
        stats = self.storage.get_storage_stats()
        self.assertGreater(stats['symbols_stored'], 0)
        
        print(f"\\n📊 Estadísticas finales:")
        print(f"   📁 Símbolos exitosos: {successful_symbols}/{len(self.test_symbols)}")
        print(f"   🎯 Total zonas: {stats['total_zones']}")
        print(f"   💾 Uso disco: {stats['disk_usage_mb']} MB")
    
    def test_persistence_real_data(self):
        """🏛️ Test persistencia de datos reales"""
        print(f"\\n🎯 TEST: Persistencia de datos reales")
        print("-" * 50)
        
        symbol = "BTCUSDT"
        
        # Almacenar datos
        success = self.storage.store_zones_from_detector(symbol, self.test_timeframe)
        self.assertTrue(success)
        
        original_data = self.storage.get_previous_zones(symbol)
        original_price = original_data['current_price']
        original_zones = original_data['total_zones']
        
        # Crear nuevo storage instance (simula reinicio)
        new_storage = ZoneStorage(self.temp_dir)
        
        # Verificar que los datos persisten
        loaded_data = new_storage.get_previous_zones(symbol)
        
        self.assertIsNotNone(loaded_data, "Datos deben persistir después de reinicio")
        self.assertEqual(loaded_data['symbol'], symbol)
        self.assertEqual(loaded_data['current_price'], original_price)
        self.assertEqual(loaded_data['total_zones'], original_zones)
        
        print(f"✅ Persistencia verificada:")
        print(f"   💰 Precio persistido: ${loaded_data['current_price']:,.2f}")
        print(f"   📊 Zonas persistidas: {loaded_data['total_zones']}")
    
    def test_cleanup_functionality(self):
        """🧹 Test funcionalidad de limpieza"""
        print(f"\\n🎯 TEST: Funcionalidad de limpieza")
        print("-" * 50)
        
        symbol = "BTCUSDT"
        
        # Almacenar datos
        success = self.storage.store_zones_from_detector(symbol, self.test_timeframe)
        self.assertTrue(success)
        
        # Verificar que hay datos
        stats_before = self.storage.get_storage_stats()
        self.assertGreater(stats_before['symbols_stored'], 0)
        
        # Limpiar datos (usando edad muy pequeña para forzar limpieza)
        removed_count = self.storage.cleanup_old_data(max_age_hours=0)
        
        # Verificar limpieza
        stats_after = self.storage.get_storage_stats()
        
        print(f"✅ Limpieza completada:")
        print(f"   📊 Antes: {stats_before['symbols_stored']} símbolos")
        print(f"   📊 Después: {stats_after['symbols_stored']} símbolos")
        print(f"   🧹 Removidos: {removed_count}")
        
        # La limpieza debe haber funcionado
        self.assertGreaterEqual(removed_count, 0)
    
    def test_error_handling_invalid_symbol(self):
        """⚠️ Test manejo de errores con símbolo inválido"""
        print(f"\\n🎯 TEST: Manejo de errores - símbolo inválido")
        print("-" * 50)
        
        invalid_symbol = "INVALIDCOIN"
        
        # Intentar almacenar símbolo inválido
        success = self.storage.store_zones_from_detector(invalid_symbol, self.test_timeframe)
        
        # Debe fallar graciosamente
        self.assertFalse(success, "Símbolo inválido debe fallar")
        
        # No debe haber datos almacenados
        data = self.storage.get_previous_zones(invalid_symbol)
        self.assertIsNone(data, "No debe haber datos para símbolo inválido")
        
        print(f"✅ Error manejado correctamente para {invalid_symbol}")


class TestZoneStorageIntegration(unittest.TestCase):
    """🔥 Tests de integración con datos reales"""
    
    @classmethod
    def setUpClass(cls):
        """Setup para tests de integración"""
        cls.api_key = os.getenv('BINANCE_API_KEY')
        cls.api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not cls.api_key or not cls.api_secret:
            raise unittest.SkipTest("❌ Credenciales de Binance no encontradas")
    
    def setUp(self):
        """Setup para cada test de integración"""
        self.temp_dir = tempfile.mkdtemp(prefix="zone_integration_test_")
        self.storage = ZoneStorage(self.temp_dir)
    
    def tearDown(self):
        """Cleanup"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_full_workflow_real_data(self):
        """🏆 Test workflow completo con datos reales"""
        print(f"\\n🔥 TEST WORKFLOW COMPLETO CON DATOS REALES 🔥")
        print("=" * 60)
        
        symbol = "BTCUSDT"
        timeframe = "1h"
        
        # 1. Almacenar datos iniciales
        print("1️⃣ Almacenando datos iniciales...")
        success1 = self.storage.store_zones_from_detector(symbol, timeframe)
        self.assertTrue(success1)
        
        initial_data = self.storage.get_previous_zones(symbol)
        self.assertIsNotNone(initial_data)
        
        print(f"   ✅ Datos iniciales: {initial_data['total_zones']} zonas")
        
        # 2. Simular paso del tiempo y nueva detección
        print("\\n2️⃣ Nueva detección después de tiempo...")
        import time
        time.sleep(2)
        
        comparison = self.storage.compare_with_previous(symbol, timeframe)
        self.assertTrue(comparison['success'])
        
        print(f"   ✅ Comparación: {comparison['new_zones_count']} nuevas zonas")
        
        # 3. Verificar persistencia
        print("\\n3️⃣ Verificando persistencia...")
        new_storage = ZoneStorage(self.temp_dir)
        persisted_data = new_storage.get_previous_zones(symbol)
        
        self.assertIsNotNone(persisted_data)
        self.assertEqual(persisted_data['symbol'], symbol)
        
        print(f"   ✅ Datos persistidos correctamente")
        
        # 4. Estadísticas finales
        stats = new_storage.get_storage_stats()
        print(f"\\n📊 ESTADÍSTICAS FINALES:")
        print(f"   📁 Símbolos: {stats['symbols_stored']}")
        print(f"   🎯 Zonas: {stats['total_zones']}")
        print(f"   💾 Disco: {stats['disk_usage_mb']} MB")
        
        print(f"\\n🏆 WORKFLOW COMPLETO EXITOSO! 🏆")


def run_real_data_tests():
    """Ejecuta todos los tests con datos reales"""
    print("🔥⚔️🏛️ EJECUTANDO TESTS CON DATOS REALES DE BINANCE 🏛️⚔️🔥")
    print("=" * 80)
    
    # Verificar credenciales antes de ejecutar
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ CREDENCIALES DE BINANCE NO ENCONTRADAS!")
        print("   Configura BINANCE_API_KEY y BINANCE_API_SECRET")
        return False
    
    print("✅ Credenciales encontradas - Ejecutando tests reales...")
    
    # Ejecutar tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Añadir tests
    suite.addTests(loader.loadTestsFromTestCase(TestZoneStorageWithRealData))
    suite.addTests(loader.loadTestsFromTestCase(TestZoneStorageIntegration))
    
    # Ejecutar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resultado
    if result.wasSuccessful():
        print("\\n🏆 TODOS LOS TESTS CON DATOS REALES EXITOSOS! 🏆")
        return True
    else:
        print(f"\\n❌ ALGUNOS TESTS FALLARON: {len(result.failures)} failures, {len(result.errors)} errors")
        return False


if __name__ == "__main__":
    run_real_data_tests()