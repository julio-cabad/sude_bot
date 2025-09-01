#!/usr/bin/env python3
"""
🧪⚔️ TESTS PARA REAL TIME ZONE MONITOR - PRUEBAS ÉPICAS ⚔️🧪
Tests que harían llorar a Leonidas y sus 300
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

from core.realtime_zone_monitor import (
    RealTimeZoneMonitor, 
    MonitoringState, 
    MonitoringSession
)


class TestMonitoringSession(unittest.TestCase):
    """🏛️ TESTS PARA MONITORING SESSION 🏛️"""
    
    def test_monitoring_session_creation(self):
        """🧪 Test creación de sesión de monitoring"""
        from models.zone_alert import EcuadorTimeUtils
        
        session = MonitoringSession(
            session_id="TEST_SESSION",
            symbols={"ETHUSDT", "BTCUSDT"},
            timeframe="1h",
            start_time=EcuadorTimeUtils.now(),
            state=MonitoringState.STARTING
        )
        
        self.assertEqual(session.session_id, "TEST_SESSION")
        self.assertEqual(session.symbols, {"ETHUSDT", "BTCUSDT"})
        self.assertEqual(session.timeframe, "1h")
        self.assertEqual(session.state, MonitoringState.STARTING)
        self.assertEqual(session.total_checks, 0)
        self.assertEqual(session.zones_detected, 0)
        self.assertEqual(session.alerts_sent, 0)
        self.assertIsInstance(session.errors, list)
        self.assertEqual(len(session.errors), 0)


class TestRealTimeZoneMonitor(unittest.TestCase):
    """🏛️ TESTS ÉPICOS PARA REAL TIME ZONE MONITOR 🏛️"""
    
    def setUp(self):
        """🚀 Setup para cada test"""
        # Crear monitor con alertas deshabilitadas para testing
        self.monitor = RealTimeZoneMonitor(
            timeframe="1h",
            enable_alerts=False,
            enable_sound=False
        )
    
    def tearDown(self):
        """🧹 Cleanup después de cada test"""
        if self.monitor.is_running():
            self.monitor.stop_monitoring()
    
    def test_initialization(self):
        """🧪 Test inicialización del monitor"""
        self.assertIsInstance(self.monitor, RealTimeZoneMonitor)
        self.assertEqual(self.monitor.timeframe, "1h")
        self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
        self.assertEqual(len(self.monitor.symbols), 0)
        self.assertIsNone(self.monitor.current_session)
        self.assertEqual(self.monitor.total_sessions, 0)
    
    def test_invalid_timeframe(self):
        """🧪 Test inicialización con timeframe inválido"""
        with self.assertRaises(ValueError):
            RealTimeZoneMonitor(timeframe="invalid_tf")
    
    def test_add_symbol(self):
        """🧪 Test añadir símbolos"""
        # Añadir símbolo válido
        result = self.monitor.add_symbol("ETHUSDT")
        self.assertTrue(result)
        self.assertIn("ETHUSDT", self.monitor.symbols)
        
        # Añadir símbolo duplicado
        result = self.monitor.add_symbol("ETHUSDT")
        self.assertFalse(result)
        self.assertEqual(len(self.monitor.symbols), 1)
        
        # Añadir símbolo con espacios y minúsculas
        result = self.monitor.add_symbol("  btcusdt  ")
        self.assertTrue(result)
        self.assertIn("BTCUSDT", self.monitor.symbols)
        
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
        self.assertNotIn("ETHUSDT", self.monitor.symbols)
        self.assertIn("BTCUSDT", self.monitor.symbols)
        
        # Remover símbolo inexistente
        result = self.monitor.remove_symbol("ADAUSDT")
        self.assertFalse(result)
        
        # Remover con espacios y minúsculas
        result = self.monitor.remove_symbol("  btcusdt  ")
        self.assertTrue(result)
        self.assertEqual(len(self.monitor.symbols), 0)
    
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
    
    def test_start_monitoring_no_symbols(self):
        """🧪 Test iniciar monitoring sin símbolos"""
        result = self.monitor.start_monitoring()
        self.assertFalse(result)
        self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
    
    def test_start_monitoring_success(self):
        """🧪 Test iniciar monitoring exitosamente"""
        # Añadir símbolos
        self.monitor.add_symbol("ETHUSDT")
        
        # Mock del alert engine para evitar dependencias
        with patch.object(self.monitor, 'alert_engine', None):
            result = self.monitor.start_monitoring()
            
            self.assertTrue(result)
            self.assertEqual(self.monitor.state, MonitoringState.RUNNING)
            self.assertIsNotNone(self.monitor.current_session)
            self.assertEqual(self.monitor.total_sessions, 1)
            
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
        
        with patch.object(self.monitor, 'alert_engine', None):
            # Iniciar monitoring
            self.monitor.start_monitoring()
            self.assertEqual(self.monitor.state, MonitoringState.RUNNING)
            
            # Detener monitoring
            result = self.monitor.stop_monitoring(timeout=2.0)
            self.assertTrue(result)
            self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
            
            # Verificar que el thread se detuvo
            if self.monitor.monitoring_thread:
                self.assertFalse(self.monitor.monitoring_thread.is_alive())
    
    def test_stop_monitoring_already_stopped(self):
        """🧪 Test detener monitoring cuando ya está detenido"""
        result = self.monitor.stop_monitoring()
        self.assertTrue(result)
        self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
    
    def test_pause_resume_monitoring(self):
        """🧪 Test pausar y reanudar monitoring"""
        self.monitor.add_symbol("ETHUSDT")
        
        with patch.object(self.monitor, 'alert_engine', None):
            # Iniciar monitoring
            self.monitor.start_monitoring()
            self.assertEqual(self.monitor.state, MonitoringState.RUNNING)
            
            # Pausar
            result = self.monitor.pause_monitoring()
            self.assertTrue(result)
            self.assertEqual(self.monitor.state, MonitoringState.PAUSED)
            
            # Reanudar
            result = self.monitor.resume_monitoring()
            self.assertTrue(result)
            self.assertEqual(self.monitor.state, MonitoringState.RUNNING)
            
            # Intentar pausar cuando no está corriendo
            self.monitor.stop_monitoring()
            result = self.monitor.pause_monitoring()
            self.assertFalse(result)
    
    def test_callbacks(self):
        """🧪 Test callbacks del monitor"""
        zone_callback = Mock()
        error_callback = Mock()
        state_callback = Mock()
        
        # Añadir callbacks
        self.monitor.add_zone_detected_callback(zone_callback)
        self.monitor.add_error_callback(error_callback)
        self.monitor.add_state_change_callback(state_callback)
        
        # Verificar que se añadieron
        self.assertIn(zone_callback, self.monitor.zone_detected_callbacks)
        self.assertIn(error_callback, self.monitor.error_callbacks)
        self.assertIn(state_callback, self.monitor.state_change_callbacks)
        
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
    
    def test_get_status(self):
        """🧪 Test obtener status del monitor"""
        # Status inicial
        status = self.monitor.get_status()
        
        self.assertIsInstance(status, dict)
        self.assertEqual(status["state"], MonitoringState.STOPPED.value)
        self.assertEqual(status["timeframe"], "1h")
        self.assertEqual(status["symbols"], [])
        self.assertEqual(status["total_sessions"], 0)
        self.assertIsNone(status["current_session"])
        
        # Añadir símbolos y iniciar
        self.monitor.add_symbol("ETHUSDT")
        
        with patch.object(self.monitor, 'alert_engine', None):
            self.monitor.start_monitoring()
            
            status = self.monitor.get_status()
            self.assertEqual(status["state"], MonitoringState.RUNNING.value)
            self.assertEqual(status["symbols"], ["ETHUSDT"])
            self.assertEqual(status["total_sessions"], 1)
            self.assertIsNotNone(status["current_session"])
            
            # Verificar estructura de sesión actual
            session = status["current_session"]
            self.assertIn("session_id", session)
            self.assertIn("start_time", session)
            self.assertIn("runtime", session)
            self.assertIn("total_checks", session)
            self.assertIn("zones_detected", session)
            self.assertIn("alerts_sent", session)
    
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
    
    @patch('core.realtime_zone_monitor.time.sleep')
    def test_monitoring_loop_basic(self, mock_sleep):
        """🧪 Test básico del loop de monitoring"""
        self.monitor.add_symbol("ETHUSDT")
        
        # Mock del método _process_symbol para evitar dependencias
        with patch.object(self.monitor, '_process_symbol') as mock_process:
            with patch.object(self.monitor, 'alert_engine', None):
                self.monitor.start_monitoring()
                
                # Esperar un poco para que el loop ejecute
                time.sleep(0.1)
                
                # Detener
                self.monitor.stop_monitoring()
                
                # Verificar que se llamó _process_symbol
                mock_process.assert_called()
    
    def test_handle_new_zone(self):
        """🧪 Test manejo de nueva zona"""
        zone_callback = Mock()
        self.monitor.add_zone_detected_callback(zone_callback)
        
        test_zone_data = {
            "type": "DEMAND",
            "poi": 1000.0,
            "top": 1010.0,
            "bottom": 990.0
        }
        
        # Test sin alert engine
        self.monitor._handle_new_zone("ETHUSDT", test_zone_data)
        zone_callback.assert_called_once_with("ETHUSDT", test_zone_data)
        
        # Test con sesión activa
        from models.zone_alert import EcuadorTimeUtils
        self.monitor.current_session = MonitoringSession(
            session_id="TEST",
            symbols={"ETHUSDT"},
            timeframe="1h",
            start_time=EcuadorTimeUtils.now(),
            state=MonitoringState.RUNNING
        )
        
        initial_alerts = self.monitor.current_session.alerts_sent
        self.monitor._handle_new_zone("ETHUSDT", test_zone_data)
        
        # Sin alert engine, no debería incrementar alertas
        self.assertEqual(self.monitor.current_session.alerts_sent, initial_alerts)


class TestMonitoringIntegration(unittest.TestCase):
    """🏛️ TESTS DE INTEGRACIÓN ÉPICOS 🏛️"""
    
    def setUp(self):
        """🚀 Setup para tests de integración"""
        self.monitor = RealTimeZoneMonitor(
            timeframe="1h",
            enable_alerts=False,
            enable_sound=False
        )
    
    def tearDown(self):
        """🧹 Cleanup después de cada test"""
        if self.monitor.is_running():
            self.monitor.stop_monitoring()
    
    def test_full_monitoring_cycle(self):
        """🧪 Test ciclo completo de monitoring"""
        # Configurar callbacks
        zone_detected_count = 0
        state_changes = []
        
        def on_zone_detected(symbol, zone_data):
            nonlocal zone_detected_count
            zone_detected_count += 1
        
        def on_state_change(old_state, new_state):
            state_changes.append((old_state, new_state))
        
        self.monitor.add_zone_detected_callback(on_zone_detected)
        self.monitor.add_state_change_callback(on_state_change)
        
        # Añadir símbolos
        self.monitor.add_symbol("ETHUSDT")
        self.monitor.add_symbol("BTCUSDT")
        
        # Verificar estado inicial
        self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
        self.assertEqual(len(self.monitor.symbols), 2)
        
        # Iniciar monitoring
        with patch.object(self.monitor, 'alert_engine', None):
            result = self.monitor.start_monitoring()
            self.assertTrue(result)
            self.assertEqual(self.monitor.state, MonitoringState.RUNNING)
            
            # Esperar un poco
            time.sleep(0.1)
            
            # Verificar que hay una sesión activa
            self.assertIsNotNone(self.monitor.current_session)
            self.assertEqual(self.monitor.current_session.symbols, {"ETHUSDT", "BTCUSDT"})
            
            # Detener monitoring
            result = self.monitor.stop_monitoring()
            self.assertTrue(result)
            self.assertEqual(self.monitor.state, MonitoringState.STOPPED)
        
        # Verificar cambios de estado
        self.assertTrue(len(state_changes) >= 2)  # Al menos STOPPED->STARTING->RUNNING y RUNNING->STOPPED
    
    @patch('core.realtime_zone_monitor.time.sleep')
    def test_error_handling_in_monitoring(self, mock_sleep):
        """🧪 Test manejo de errores en monitoring"""
        error_count = 0
        
        def on_error(symbol, error):
            nonlocal error_count
            error_count += 1
        
        self.monitor.add_error_callback(on_error)
        self.monitor.add_symbol("ETHUSDT")
        
        # Mock _process_symbol para que lance excepción
        with patch.object(self.monitor, '_process_symbol', side_effect=Exception("Test error")):
            with patch.object(self.monitor, 'alert_engine', None):
                self.monitor.start_monitoring()
                
                # Esperar un poco para que procese
                time.sleep(0.1)
                
                self.monitor.stop_monitoring()
        
        # Verificar que se manejó el error
        self.assertTrue(error_count > 0)


if __name__ == "__main__":
    print("🧪⚔️🏛️ RUNNING EPIC REAL TIME ZONE MONITOR TESTS 🏛️⚔️🧪")
    
    # Ejecutar tests
    unittest.main(verbosity=2)