#!/usr/bin/env python3
"""
🧪⚔️ TESTS PARA MULTI SYMBOL MONITOR - PRUEBAS ÉPICAS ⚔️🧪
Tests que harían llorar a Zeus y los dioses del Olimpo
Created by TITANES DEL CÓDIGO - BESTIAS SUPREMAS
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Añadir path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.multi_symbol_monitor import (
    MultiSymbolMonitor,
    SymbolState,
    MonitoringState
)


class TestSymbolState(unittest.TestCase):
    """🏛️ TESTS PARA SYMBOL STATE 🏛️"""
    
    def test_symbol_state_creation(self):
        """🧪 Test creación de estado de símbolo"""
        state = SymbolState(symbol="ETHUSDT")
        
        self.assertEqual(state.symbol, "ETHUSDT")
        self.assertTrue(state.is_active)
        self.assertIsNone(state.last_check)
        self.assertIsNone(state.last_zone_time)
        self.assertEqual(state.total_checks, 0)
        self.assertEqual(state.zones_detected, 0)
        self.assertEqual(state.alerts_sent, 0)
        self.assertEqual(state.consecutive_errors, 0)
        self.assertIsInstance(state.errors, list)
        self.assertEqual(len(state.errors), 0)
        self.assertEqual(state.processing_time_avg, 0.0)
    
    def test_update_processing_time(self):
        """🧪 Test actualización de tiempo de procesamiento"""
        state = SymbolState(symbol="ETHUSDT")
        
        # Primera actualización
        state.update_processing_time(1.0)
        self.assertEqual(state.processing_time_avg, 1.0)
        
        # Segunda actualización (media móvil)
        state.total_checks = 1  # Simular que ya hay checks
        state.update_processing_time(2.0)
        expected = (1.0 * 0.8) + (2.0 * 0.2)  # 0.8 + 0.4 = 1.2
        self.assertEqual(state.processing_time_avg, expected)


class TestMultiSymbolMonitor(unittest.TestCase):
    """🏛️ TESTS ÉPICOS PARA MULTI SYMBOL MONITOR 🏛️"""
    
    def setUp(self):
        """🚀 Setup para cada test"""
        # Crear monitor con alertas deshabilitadas para testing
        self.monitor = MultiSymbolMonitor(
            timeframe="1h",
            enable_alerts=False,
            enable_sound=False,
            max_workers=2
        )
    
    def tearDown(self):
        """🧹 Cleanup después de cada test"""
        if self.monitor.is_running():
            self.monitor.stop_monitoring()
    
    def test_initialization(self):
        """🧪 Test inicialización del monitor"""
        self.assertIsInstance(self.monitor, MultiSymbolMonitor)
        self.assertEqual(self.monitor.timeframe, "1h")
        self.assertEqual(self.monitor.max_workers, 2)
        self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
        self.assertEqual(len(self.monitor.symbol_states), 0)
        self.assertIsNone(self.monitor.current_session)
        self.assertEqual(self.monitor.total_sessions, 0)
    
    def test_invalid_timeframe(self):
        """🧪 Test inicialización con timeframe inválido"""
        with self.assertRaises(ValueError):
            MultiSymbolMonitor(timeframe="invalid_tf")
    
    def test_add_symbol(self):
        """🧪 Test añadir símbolos"""
        # Añadir símbolo válido
        result = self.monitor.add_symbol("ETHUSDT")
        self.assertTrue(result)
        self.assertIn("ETHUSDT", self.monitor.symbol_states)
        self.assertTrue(self.monitor.symbol_states["ETHUSDT"].is_active)
        
        # Añadir símbolo duplicado
        result = self.monitor.add_symbol("ETHUSDT")
        self.assertFalse(result)
        self.assertEqual(len(self.monitor.symbol_states), 1)
        
        # Añadir símbolo con espacios y minúsculas
        result = self.monitor.add_symbol("  btcusdt  ")
        self.assertTrue(result)
        self.assertIn("BTCUSDT", self.monitor.symbol_states)
        
        # Añadir símbolo vacío
        result = self.monitor.add_symbol("")
        self.assertFalse(result)
    
    def test_remove_symbol(self):
        """🧪 Test remover símbolos"""
        # Añadir símbolos primero
        self.monitor.add_symbol("ETHUSDT")
        self.monitor.add_symbol("BTCUSDT")
        
        # Remover símbolo existente
        result = self.monitor.remove_symbol("ETHUSDT")
        self.assertTrue(result)
        
        # Verificar que se marcó como inactivo inmediatamente
        self.assertFalse(self.monitor.symbol_states["ETHUSDT"].is_active)
        
        # Esperar a que se remueva completamente
        time.sleep(1.5)
        self.assertNotIn("ETHUSDT", self.monitor.symbol_states)
        
        # Remover símbolo inexistente
        result = self.monitor.remove_symbol("ADAUSDT")
        self.assertFalse(result)
    
    def test_get_monitored_symbols(self):
        """🧪 Test obtener símbolos monitoreados"""
        # Lista vacía inicialmente
        symbols = self.monitor.get_monitored_symbols()
        self.assertEqual(symbols, [])
        
        # Añadir símbolos
        self.monitor.add_symbol("ETHUSDT")
        self.monitor.add_symbol("BTCUSDT")
        self.monitor.add_symbol("ADAUSDT")
        
        symbols = self.monitor.get_monitored_symbols()
        self.assertEqual(len(symbols), 3)
        self.assertEqual(symbols, sorted(symbols))  # Debe estar ordenado
        self.assertIn("ETHUSDT", symbols)
        self.assertIn("BTCUSDT", symbols)
        self.assertIn("ADAUSDT", symbols)
        
        # Desactivar un símbolo
        self.monitor.symbol_states["BTCUSDT"].is_active = False
        symbols = self.monitor.get_monitored_symbols()
        self.assertEqual(len(symbols), 2)
        self.assertNotIn("BTCUSDT", symbols)
    
    def test_get_symbol_state(self):
        """🧪 Test obtener estado de símbolo"""
        # Símbolo inexistente
        state = self.monitor.get_symbol_state("ETHUSDT")
        self.assertIsNone(state)
        
        # Añadir símbolo
        self.monitor.add_symbol("ETHUSDT")
        state = self.monitor.get_symbol_state("ETHUSDT")
        self.assertIsNotNone(state)
        self.assertIsInstance(state, SymbolState)
        self.assertEqual(state.symbol, "ETHUSDT")
        
        # Test case insensitive
        state = self.monitor.get_symbol_state("ethusdt")
        self.assertIsNotNone(state)
        self.assertEqual(state.symbol, "ETHUSDT")
    
    def test_start_monitoring_no_symbols(self):
        """🧪 Test iniciar monitoring sin símbolos"""
        result = self.monitor.start_monitoring()
        self.assertFalse(result)
        self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
    
    def test_start_monitoring_success(self):
        """🧪 Test iniciar monitoring exitosamente"""
        # Añadir símbolos
        self.monitor.add_symbol("ETHUSDT")
        self.monitor.add_symbol("BTCUSDT")
        
        # Mock del alert engine para evitar dependencias
        with patch.object(self.monitor, 'alert_engine', None):
            result = self.monitor.start_monitoring()
            
            self.assertTrue(result)
            self.assertEqual(self.monitor.state, MonitoringState.RUNNING)
            self.assertIsNotNone(self.monitor.current_session)
            self.assertEqual(self.monitor.total_sessions, 1)
            
            # Verificar que el executor está activo
            self.assertIsNotNone(self.monitor.executor)
            
            # Verificar que el thread está corriendo
            self.assertIsNotNone(self.monitor.monitoring_thread)
            self.assertTrue(self.monitor.monitoring_thread.is_alive())
    
    def test_start_monitoring_already_running(self):
        """🧪 Test iniciar monitoring cuando ya está corriendo"""
        self.monitor.add_symbol("ETHUSDT")
        
        with patch.object(self.monitor, 'alert_engine', None):
            # Iniciar primera vez
            result1 = self.monitor.start_monitoring()
            self.assertTrue(result1)
            
            # Intentar iniciar segunda vez
            result2 = self.monitor.start_monitoring()
            self.assertFalse(result2)
    
    def test_stop_monitoring(self):
        """🧪 Test detener monitoring"""
        self.monitor.add_symbol("ETHUSDT")
        self.monitor.add_symbol("BTCUSDT")
        
        with patch.object(self.monitor, 'alert_engine', None):
            # Iniciar monitoring
            self.monitor.start_monitoring()
            self.assertEqual(self.monitor.state, MonitoringState.RUNNING)
            
            # Detener monitoring
            result = self.monitor.stop_monitoring(timeout=5.0)
            self.assertTrue(result)
            self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
            
            # Verificar que el executor se cerró
            self.assertIsNone(self.monitor.executor)
    
    def test_stop_monitoring_already_stopped(self):
        """🧪 Test detener monitoring cuando ya está detenido"""
        result = self.monitor.stop_monitoring()
        self.assertTrue(result)
        self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
    
    def test_callbacks(self):
        """🧪 Test callbacks del monitor"""
        zone_callback = Mock()
        error_callback = Mock()
        state_callback = Mock()
        symbol_added_callback = Mock()
        symbol_removed_callback = Mock()
        
        # Añadir callbacks
        self.monitor.add_zone_detected_callback(zone_callback)
        self.monitor.add_error_callback(error_callback)
        self.monitor.add_state_change_callback(state_callback)
        self.monitor.add_symbol_added_callback(symbol_added_callback)
        self.monitor.add_symbol_removed_callback(symbol_removed_callback)
        
        # Verificar que se añadieron
        self.assertIn(zone_callback, self.monitor.zone_detected_callbacks)
        self.assertIn(error_callback, self.monitor.error_callbacks)
        self.assertIn(state_callback, self.monitor.state_change_callbacks)
        self.assertIn(symbol_added_callback, self.monitor.symbol_added_callbacks)
        self.assertIn(symbol_removed_callback, self.monitor.symbol_removed_callbacks)
        
        # Test callback de zona detectada
        test_zone_data = {"type": "DEMAND", "poi": 1000.0}
        self.monitor._call_zone_detected_callbacks("ETHUSDT", test_zone_data)
        zone_callback.assert_called_once_with("ETHUSDT", test_zone_data)
        
        # Test callback de error
        test_error = Exception("Test error")
        self.monitor._call_error_callbacks("ETHUSDT", test_error)
        error_callback.assert_called_once_with("ETHUSDT", test_error)
        
        # Test callback de cambio de estado
        self.monitor._call_state_change_callbacks(MonitoringState.STOPPED, MonitoringState.RUNNING)
        state_callback.assert_called_once_with(MonitoringState.STOPPED, MonitoringState.RUNNING)
        
        # Test callback de símbolo añadido
        self.monitor._call_symbol_added_callbacks("ETHUSDT")
        symbol_added_callback.assert_called_once_with("ETHUSDT")
        
        # Test callback de símbolo removido
        self.monitor._call_symbol_removed_callbacks("ETHUSDT")
        symbol_removed_callback.assert_called_once_with("ETHUSDT")
    
    def test_get_status(self):
        """🧪 Test obtener status del monitor"""
        # Status inicial
        status = self.monitor.get_status()
        
        self.assertIsInstance(status, dict)
        self.assertEqual(status["state"], MonitoringState.STOPPED.value)
        self.assertEqual(status["timeframe"], "1h")
        self.assertEqual(status["max_workers"], 2)
        self.assertEqual(status["active_symbols"], 0)
        self.assertEqual(status["total_symbols"], 0)
        self.assertEqual(status["total_sessions"], 0)
        self.assertIsNone(status["current_session"])
        
        # Añadir símbolos
        self.monitor.add_symbol("ETHUSDT")
        self.monitor.add_symbol("BTCUSDT")
        
        status = self.monitor.get_status()
        self.assertEqual(status["active_symbols"], 2)
        self.assertEqual(status["total_symbols"], 2)
        self.assertIn("symbol_stats", status)
        self.assertIn("ETHUSDT", status["symbol_stats"])
        self.assertIn("BTCUSDT", status["symbol_stats"])
        
        # Verificar estructura de stats de símbolo
        eth_stats = status["symbol_stats"]["ETHUSDT"]
        self.assertIn("is_active", eth_stats)
        self.assertIn("total_checks", eth_stats)
        self.assertIn("zones_detected", eth_stats)
        self.assertIn("alerts_sent", eth_stats)
        self.assertIn("consecutive_errors", eth_stats)
        self.assertIn("processing_time_avg", eth_stats)
    
    def test_is_running(self):
        """🧪 Test verificar si está corriendo"""
        self.assertFalse(self.monitor.is_running())
        
        self.monitor.add_symbol("ETHUSDT")
        
        with patch.object(self.monitor, 'alert_engine', None):
            self.monitor.start_monitoring()
            self.assertTrue(self.monitor.is_running())
            
            self.monitor.stop_monitoring()
            self.assertFalse(self.monitor.is_running())
    
    def test_is_monitoring_symbol(self):
        """🧪 Test verificar si está monitoreando símbolo"""
        self.assertFalse(self.monitor.is_monitoring_symbol("ETHUSDT"))
        
        self.monitor.add_symbol("ETHUSDT")
        self.assertTrue(self.monitor.is_monitoring_symbol("ETHUSDT"))
        self.assertTrue(self.monitor.is_monitoring_symbol("ethusdt"))  # Case insensitive
        self.assertFalse(self.monitor.is_monitoring_symbol("BTCUSDT"))
        
        # Desactivar símbolo
        self.monitor.symbol_states["ETHUSDT"].is_active = False
        self.assertFalse(self.monitor.is_monitoring_symbol("ETHUSDT"))
    
    def test_should_process_symbol(self):
        """🧪 Test lógica de si debe procesar símbolo"""
        from models.zone_alert import EcuadorTimeUtils
        from datetime import timedelta
        
        # Crear estado de símbolo
        state = SymbolState(symbol="ETHUSDT")
        
        # Debe procesar normalmente
        self.assertTrue(self.monitor._should_process_symbol(state))
        
        # Con muchos errores consecutivos
        state.consecutive_errors = self.monitor.max_errors_per_symbol
        state.last_check = EcuadorTimeUtils.now()
        self.assertFalse(self.monitor._should_process_symbol(state))
        
        # Después del cooldown
        state.last_check = EcuadorTimeUtils.now() - timedelta(minutes=self.monitor.error_cooldown_minutes + 1)
        self.assertTrue(self.monitor._should_process_symbol(state))
        # Debe haber reseteado los errores
        self.assertEqual(state.consecutive_errors, 0)
    
    def test_process_symbol_parallel(self):
        """🧪 Test procesamiento paralelo de símbolo"""
        # Añadir símbolo
        self.monitor.add_symbol("ETHUSDT")
        
        # Mock de detección de zonas
        with patch.object(self.monitor, '_simulate_zone_detection_parallel', return_value=[]):
            result = self.monitor._process_symbol_parallel("ETHUSDT")
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['symbol'], "ETHUSDT")
            self.assertTrue(result['success'])
            self.assertEqual(result['zones_detected'], [])
            self.assertIsNone(result['error'])
            self.assertGreater(result['processing_time'], 0)
            
            # Verificar que se actualizó el estado
            state = self.monitor.get_symbol_state("ETHUSDT")
            self.assertEqual(state.total_checks, 1)
            self.assertEqual(state.consecutive_errors, 0)
    
    def test_process_symbol_parallel_error(self):
        """🧪 Test procesamiento paralelo con error"""
        # Añadir símbolo
        self.monitor.add_symbol("ETHUSDT")
        
        # Mock que lance excepción
        with patch.object(self.monitor, '_simulate_zone_detection_parallel', side_effect=Exception("Test error")):
            result = self.monitor._process_symbol_parallel("ETHUSDT")
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['symbol'], "ETHUSDT")
            self.assertFalse(result['success'])
            self.assertIsNotNone(result['error'])
            self.assertEqual(result['error'], "Test error")
    
    def test_handle_symbol_result(self):
        """🧪 Test manejo de resultado de símbolo"""
        # Añadir símbolo
        self.monitor.add_symbol("ETHUSDT")
        
        # Test resultado exitoso sin zonas
        result = {
            'symbol': 'ETHUSDT',
            'success': True,
            'zones_detected': [],
            'error': None
        }
        
        # No debería lanzar excepción
        self.monitor._handle_symbol_result("ETHUSDT", result)
        
        # Test resultado exitoso con zonas
        zone_data = {"type": "DEMAND", "poi": 1000.0}
        result['zones_detected'] = [zone_data]
        
        with patch.object(self.monitor, '_handle_new_zone') as mock_handle_zone:
            self.monitor._handle_symbol_result("ETHUSDT", result)
            mock_handle_zone.assert_called_once_with("ETHUSDT", zone_data)
        
        # Test resultado con error
        result = {
            'symbol': 'ETHUSDT',
            'success': False,
            'error': 'Test error'
        }
        
        with patch.object(self.monitor, '_handle_symbol_error') as mock_handle_error:
            self.monitor._handle_symbol_result("ETHUSDT", result)
            mock_handle_error.assert_called_once()
    
    def test_handle_symbol_error(self):
        """🧪 Test manejo de error de símbolo"""
        # Añadir símbolo
        self.monitor.add_symbol("ETHUSDT")
        
        error = Exception("Test error")
        
        # Verificar estado inicial
        state = self.monitor.get_symbol_state("ETHUSDT")
        initial_errors = state.consecutive_errors
        
        # Manejar error
        self.monitor._handle_symbol_error("ETHUSDT", error)
        
        # Verificar que se actualizó el estado
        state = self.monitor.get_symbol_state("ETHUSDT")
        self.assertEqual(state.consecutive_errors, initial_errors + 1)
        self.assertTrue(len(state.errors) > 0)
        self.assertIn("Test error", state.errors[-1])
    
    def test_handle_new_zone(self):
        """🧪 Test manejo de nueva zona"""
        # Añadir símbolo
        self.monitor.add_symbol("ETHUSDT")
        
        zone_data = {
            "type": "DEMAND",
            "poi": 1000.0,
            "top": 1010.0,
            "bottom": 990.0
        }
        
        # Verificar estado inicial
        state = self.monitor.get_symbol_state("ETHUSDT")
        initial_alerts = state.alerts_sent
        
        # Manejar nueva zona
        self.monitor._handle_new_zone("ETHUSDT", zone_data)
        
        # Verificar que se actualizó el contador de alertas
        state = self.monitor.get_symbol_state("ETHUSDT")
        self.assertEqual(state.alerts_sent, initial_alerts + 1)


class TestMultiSymbolIntegration(unittest.TestCase):
    """🏛️ TESTS DE INTEGRACIÓN ÉPICOS 🏛️"""
    
    def setUp(self):
        """🚀 Setup para tests de integración"""
        self.monitor = MultiSymbolMonitor(
            timeframe="1h",
            enable_alerts=False,
            enable_sound=False,
            max_workers=2
        )
    
    def tearDown(self):
        """🧹 Cleanup después de cada test"""
        if self.monitor.is_running():
            self.monitor.stop_monitoring()
    
    def test_full_multi_symbol_cycle(self):
        """🧪 Test ciclo completo multi-símbolo"""
        # Configurar callbacks
        zone_detected_count = 0
        state_changes = []
        symbols_added = []
        symbols_removed = []
        
        def on_zone_detected(symbol, zone_data):
            nonlocal zone_detected_count
            zone_detected_count += 1
        
        def on_state_change(old_state, new_state):
            state_changes.append((old_state, new_state))
        
        def on_symbol_added(symbol):
            symbols_added.append(symbol)
        
        def on_symbol_removed(symbol):
            symbols_removed.append(symbol)
        
        self.monitor.add_zone_detected_callback(on_zone_detected)
        self.monitor.add_state_change_callback(on_state_change)
        self.monitor.add_symbol_added_callback(on_symbol_added)
        self.monitor.add_symbol_removed_callback(on_symbol_removed)
        
        # Añadir múltiples símbolos
        symbols = ["ETHUSDT", "BTCUSDT", "ADAUSDT"]
        for symbol in symbols:
            self.monitor.add_symbol(symbol)
        
        # Verificar callbacks de símbolos añadidos
        self.assertEqual(len(symbols_added), 3)
        
        # Verificar estado inicial
        self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
        self.assertEqual(len(self.monitor.symbol_states), 3)
        
        # Iniciar monitoring
        with patch.object(self.monitor, 'alert_engine', None):
            result = self.monitor.start_monitoring()
            self.assertTrue(result)
            self.assertEqual(self.monitor.state, MonitoringState.RUNNING)
            
            # Esperar un poco para que procese
            time.sleep(0.2)
            
            # Verificar que hay una sesión activa
            self.assertIsNotNone(self.monitor.current_session)
            self.assertEqual(len(self.monitor.current_session.symbols), 3)
            
            # Test remover símbolo durante ejecución
            self.monitor.remove_symbol("ADAUSDT")
            time.sleep(1.5)  # Esperar removal completo
            
            # Verificar removal
            self.assertEqual(len(symbols_removed), 1)
            self.assertEqual(symbols_removed[0], "ADAUSDT")
            
            # Detener monitoring
            result = self.monitor.stop_monitoring()
            self.assertTrue(result)
            self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
        
        # Verificar cambios de estado
        self.assertTrue(len(state_changes) >= 2)
    
    @patch('core.multi_symbol_monitor.time.sleep')
    def test_parallel_processing(self, mock_sleep):
        """🧪 Test procesamiento paralelo real"""
        # Añadir múltiples símbolos
        symbols = ["ETHUSDT", "BTCUSDT", "ADAUSDT", "SOLUSDT"]
        for symbol in symbols:
            self.monitor.add_symbol(symbol)
        
        # Mock del método de procesamiento para simular trabajo
        processing_times = {}
        
        def mock_process_symbol(symbol):
            start_time = time.time()
            time.sleep(0.01)  # Simular trabajo real
            processing_times[symbol] = time.time() - start_time
            return {
                'symbol': symbol,
                'success': True,
                'zones_detected': [],
                'error': None,
                'processing_time': processing_times[symbol]
            }
        
        with patch.object(self.monitor, '_process_symbol_parallel', side_effect=mock_process_symbol):
            with patch.object(self.monitor, 'alert_engine', None):
                self.monitor.start_monitoring()
                
                # Esperar un poco para que procese
                time.sleep(0.1)
                
                self.monitor.stop_monitoring()
        
        # Verificar que se procesaron símbolos
        status = self.monitor.get_status()
        total_checks = sum(
            stats['total_checks'] 
            for stats in status['symbol_stats'].values()
        )
        self.assertGreater(total_checks, 0)


if __name__ == "__main__":
    print("🧪⚔️🏛️ RUNNING EPIC MULTI SYMBOL MONITOR TESTS 🏛️⚔️🧪")
    
    # Ejecutar tests
    unittest.main(verbosity=2)