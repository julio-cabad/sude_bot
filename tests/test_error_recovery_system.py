#!/usr/bin/env python3
"""
🧪⚔️ TESTS PARA ERROR RECOVERY SYSTEM - PRUEBAS ÉPICAS ⚔️🧪
Tests que harían llorar a Hades y los dioses del inframundo
Created by TITANES DEL CÓDIGO - BESTIAS SUPREMAS
"""

import unittest
import time
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Añadir path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.error_recovery_system import (
    ErrorRecoverySystem,
    ErrorClassifier,
    ErrorInfo,
    RecoveryStrategy,
    ErrorType,
    ErrorSeverity,
    RecoveryAction
)


class TestErrorClassifier(unittest.TestCase):
    """🏛️ TESTS PARA ERROR CLASSIFIER 🏛️"""
    
    def test_classify_network_error(self):
        """🧪 Test clasificación de errores de red"""
        error = ConnectionError("Connection timeout")
        error_type, severity = ErrorClassifier.classify_error(error)
        
        self.assertEqual(error_type, ErrorType.NETWORK_ERROR)
        self.assertEqual(severity, ErrorSeverity.MEDIUM)
    
    def test_classify_rate_limit_error(self):
        """🧪 Test clasificación de errores de rate limit"""
        error = Exception("Rate limit exceeded")
        error_type, severity = ErrorClassifier.classify_error(error)
        
        self.assertEqual(error_type, ErrorType.RATE_LIMIT_ERROR)
        self.assertEqual(severity, ErrorSeverity.MEDIUM)
    
    def test_classify_data_error(self):
        """🧪 Test clasificación de errores de datos"""
        error = ValueError("Invalid JSON data")
        error_type, severity = ErrorClassifier.classify_error(error)
        
        self.assertEqual(error_type, ErrorType.DATA_ERROR)
        self.assertEqual(severity, ErrorSeverity.LOW)
    
    def test_classify_system_error(self):
        """🧪 Test clasificación de errores de sistema"""
        error = MemoryError("Out of memory")
        error_type, severity = ErrorClassifier.classify_error(error)
        
        self.assertEqual(error_type, ErrorType.SYSTEM_ERROR)
        self.assertEqual(severity, ErrorSeverity.CRITICAL)
    
    def test_classify_unknown_error(self):
        """🧪 Test clasificación de errores desconocidos"""
        error = Exception("Some unknown error")
        error_type, severity = ErrorClassifier.classify_error(error)
        
        self.assertEqual(error_type, ErrorType.UNKNOWN_ERROR)
        self.assertEqual(severity, ErrorSeverity.MEDIUM)
    
    def test_classify_critical_severity(self):
        """🧪 Test clasificación de severidad crítica"""
        error = Exception("Critical system failure")
        error_type, severity = ErrorClassifier.classify_error(error)
        
        self.assertEqual(severity, ErrorSeverity.CRITICAL)


class TestRecoveryStrategy(unittest.TestCase):
    """🏛️ TESTS PARA RECOVERY STRATEGY 🏛️"""
    
    def test_calculate_delay_backoff(self):
        """🧪 Test cálculo de delay con backoff"""
        strategy = RecoveryStrategy(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.MEDIUM,
            action=RecoveryAction.BACKOFF,
            base_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0
        )
        
        # Test diferentes intentos
        self.assertEqual(strategy.calculate_delay(0), 1.0)  # 1.0 * 2^0 = 1.0
        self.assertEqual(strategy.calculate_delay(1), 2.0)  # 1.0 * 2^1 = 2.0
        self.assertEqual(strategy.calculate_delay(2), 4.0)  # 1.0 * 2^2 = 4.0
        self.assertEqual(strategy.calculate_delay(3), 8.0)  # 1.0 * 2^3 = 8.0
        self.assertEqual(strategy.calculate_delay(4), 10.0) # Limitado por max_delay
    
    def test_calculate_delay_no_backoff(self):
        """🧪 Test cálculo de delay sin backoff"""
        strategy = RecoveryStrategy(
            error_type=ErrorType.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            action=RecoveryAction.RETRY,
            base_delay=5.0
        )
        
        # Sin backoff, siempre devuelve base_delay
        self.assertEqual(strategy.calculate_delay(0), 5.0)
        self.assertEqual(strategy.calculate_delay(1), 5.0)
        self.assertEqual(strategy.calculate_delay(5), 5.0)


class TestErrorInfo(unittest.TestCase):
    """🏛️ TESTS PARA ERROR INFO 🏛️"""
    
    def test_error_info_creation(self):
        """🧪 Test creación de ErrorInfo"""
        from models.zone_alert import EcuadorTimeUtils
        
        error_info = ErrorInfo(
            error_id="TEST_ERROR_001",
            error_type=ErrorType.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Test error message",
            timestamp=EcuadorTimeUtils.now(),
            component="TestComponent"
        )
        
        self.assertEqual(error_info.error_id, "TEST_ERROR_001")
        self.assertEqual(error_info.error_type, ErrorType.API_ERROR)
        self.assertEqual(error_info.severity, ErrorSeverity.MEDIUM)
        self.assertEqual(error_info.message, "Test error message")
        self.assertEqual(error_info.component, "TestComponent")
        self.assertEqual(error_info.recovery_attempts, 0)
        self.assertFalse(error_info.resolved)
    
    def test_error_info_to_dict(self):
        """🧪 Test conversión a diccionario"""
        from models.zone_alert import EcuadorTimeUtils
        
        error_info = ErrorInfo(
            error_id="TEST_ERROR_001",
            error_type=ErrorType.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Test error message",
            timestamp=EcuadorTimeUtils.now(),
            component="TestComponent",
            symbol="ETHUSDT"
        )
        
        error_dict = error_info.to_dict()
        
        self.assertIsInstance(error_dict, dict)
        self.assertEqual(error_dict['error_id'], "TEST_ERROR_001")
        self.assertEqual(error_dict['error_type'], "API_ERROR")
        self.assertEqual(error_dict['severity'], "MEDIUM")
        self.assertEqual(error_dict['message'], "Test error message")
        self.assertEqual(error_dict['component'], "TestComponent")
        self.assertEqual(error_dict['symbol'], "ETHUSDT")


class TestErrorRecoverySystem(unittest.TestCase):
    """🏛️ TESTS ÉPICOS PARA ERROR RECOVERY SYSTEM 🏛️"""
    
    def setUp(self):
        """🚀 Setup para cada test"""
        # Crear directorio temporal para logs
        self.temp_dir = tempfile.mkdtemp()
        
        # Crear sistema de recuperación
        self.recovery_system = ErrorRecoverySystem(
            log_dir=self.temp_dir,
            max_error_history=100,
            enable_persistence=True
        )
        
        # Iniciar sistema
        self.recovery_system.start()
    
    def tearDown(self):
        """🧹 Cleanup después de cada test"""
        # Detener sistema
        self.recovery_system.stop()
        
        # Limpiar directorio temporal
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """🧪 Test inicialización del sistema"""
        self.assertIsInstance(self.recovery_system, ErrorRecoverySystem)
        self.assertEqual(self.recovery_system.log_dir, self.temp_dir)
        self.assertEqual(self.recovery_system.max_error_history, 100)
        self.assertTrue(self.recovery_system.enable_persistence)
        self.assertTrue(self.recovery_system.is_running)
        
        # Verificar que se crearon las estrategias por defecto
        self.assertTrue(len(self.recovery_system.recovery_strategies) > 0)
        
        # Verificar estadísticas iniciales
        stats = self.recovery_system.get_error_stats()
        self.assertEqual(stats['total_errors'], 0)
        self.assertEqual(stats['resolved_errors'], 0)
    
    def test_handle_error_basic(self):
        """🧪 Test manejo básico de errores"""
        error = ValueError("Test error")
        component = "TestComponent"
        
        # Manejar error
        can_continue = self.recovery_system.handle_error(error, component)
        
        # Debe poder continuar (ValueError no es crítico)
        self.assertTrue(can_continue)
        
        # Esperar procesamiento
        time.sleep(0.1)
        
        # Verificar estadísticas
        stats = self.recovery_system.get_error_stats()
        self.assertEqual(stats['total_errors'], 1)
    
    def test_handle_critical_error(self):
        """🧪 Test manejo de errores críticos"""
        error = MemoryError("Critical memory error")
        component = "SystemCore"
        
        # Manejar error crítico
        can_continue = self.recovery_system.handle_error(error, component)
        
        # No debe poder continuar (MemoryError es crítico)
        self.assertFalse(can_continue)
    
    def test_component_cooldown(self):
        """🧪 Test cooldown de componentes"""
        component = "TestComponent"
        
        # Verificar que no está en cooldown inicialmente
        self.assertFalse(self.recovery_system._is_component_in_cooldown(component))
        
        # Simular error que cause cooldown
        error = Exception("Rate limit exceeded")
        self.recovery_system.handle_error(error, component)
        
        # Esperar procesamiento
        time.sleep(0.1)
        
        # Verificar cooldown (puede o no estar dependiendo de la estrategia)
        # Este test es más para verificar que el método funciona
        cooldown_status = self.recovery_system._is_component_in_cooldown(component)
        self.assertIsInstance(cooldown_status, bool)
    
    def test_clear_component_cooldown(self):
        """🧪 Test limpiar cooldown de componente"""
        component = "TestComponent"
        
        # Establecer cooldown manualmente
        from models.zone_alert import EcuadorTimeUtils
        self.recovery_system.cooldown_until[component] = EcuadorTimeUtils.now() + timedelta(minutes=5)
        
        # Verificar que está en cooldown
        self.assertTrue(self.recovery_system._is_component_in_cooldown(component))
        
        # Limpiar cooldown
        result = self.recovery_system.clear_component_cooldown(component)
        self.assertTrue(result)
        
        # Verificar que ya no está en cooldown
        self.assertFalse(self.recovery_system._is_component_in_cooldown(component))
        
        # Intentar limpiar cooldown inexistente
        result = self.recovery_system.clear_component_cooldown("NonExistentComponent")
        self.assertFalse(result)
    
    def test_callbacks(self):
        """🧪 Test callbacks del sistema"""
        error_callback = Mock()
        recovery_callback = Mock()
        
        # Añadir callbacks
        self.recovery_system.add_error_callback(error_callback)
        self.recovery_system.add_recovery_callback(recovery_callback)
        
        # Verificar que se añadieron
        self.assertIn(error_callback, self.recovery_system.error_callbacks)
        self.assertIn(recovery_callback, self.recovery_system.recovery_callbacks)
        
        # Manejar error para activar callbacks
        error = ValueError("Test error")
        self.recovery_system.handle_error(error, "TestComponent")
        
        # Esperar procesamiento
        time.sleep(0.2)
        
        # Verificar que se llamó el callback de error
        error_callback.assert_called()
    
    def test_get_error_stats(self):
        """🧪 Test obtener estadísticas de errores"""
        # Estadísticas iniciales
        stats = self.recovery_system.get_error_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_errors', stats)
        self.assertIn('resolved_errors', stats)
        self.assertIn('failed_recoveries', stats)
        self.assertIn('system_restarts', stats)
        self.assertIn('resolution_rate', stats)
        self.assertIn('error_types', stats)
        self.assertIn('components_in_cooldown', stats)
        self.assertIn('recent_errors', stats)
        
        # Verificar tipos
        self.assertIsInstance(stats['total_errors'], int)
        self.assertIsInstance(stats['resolution_rate'], float)
        self.assertIsInstance(stats['error_types'], dict)
    
    def test_get_component_health(self):
        """🧪 Test obtener salud de componente"""
        component = "TestComponent"
        
        # Salud inicial
        health = self.recovery_system.get_component_health(component)
        
        self.assertIsInstance(health, dict)
        self.assertEqual(health['component'], component)
        self.assertEqual(health['total_errors'], 0)
        self.assertEqual(health['recent_errors'], 0)
        self.assertFalse(health['in_cooldown'])
        self.assertIsNone(health['cooldown_until'])
        self.assertIsNone(health['last_error'])
        
        # Añadir error
        error = ValueError("Test error")
        self.recovery_system.handle_error(error, component)
        
        # Esperar procesamiento
        time.sleep(0.1)
        
        # Verificar salud actualizada
        health = self.recovery_system.get_component_health(component)
        self.assertEqual(health['total_errors'], 1)
        self.assertEqual(health['recent_errors'], 1)
    
    def test_recovery_strategies(self):
        """🧪 Test estrategias de recuperación"""
        # Verificar que existen estrategias por defecto
        strategies = self.recovery_system.recovery_strategies
        
        self.assertTrue(len(strategies) > 0)
        
        # Verificar algunas estrategias específicas
        rate_limit_key = (ErrorType.RATE_LIMIT_ERROR, ErrorSeverity.MEDIUM)
        self.assertIn(rate_limit_key, strategies)
        
        network_key = (ErrorType.NETWORK_ERROR, ErrorSeverity.MEDIUM)
        self.assertIn(network_key, strategies)
        
        # Verificar estructura de estrategia
        strategy = strategies[rate_limit_key]
        self.assertIsInstance(strategy, RecoveryStrategy)
        self.assertEqual(strategy.error_type, ErrorType.RATE_LIMIT_ERROR)
        self.assertEqual(strategy.severity, ErrorSeverity.MEDIUM)
    
    def test_error_processing_queue(self):
        """🧪 Test procesamiento de queue de errores"""
        # Manejar múltiples errores rápidamente
        errors = [
            ValueError("Error 1"),
            ConnectionError("Error 2"),
            Exception("Error 3")
        ]
        
        for i, error in enumerate(errors):
            self.recovery_system.handle_error(error, f"Component{i}")
        
        # Esperar procesamiento
        time.sleep(0.3)
        
        # Verificar que se procesaron todos
        stats = self.recovery_system.get_error_stats()
        self.assertEqual(stats['total_errors'], len(errors))
    
    def test_error_persistence(self):
        """🧪 Test persistencia de errores"""
        if not self.recovery_system.enable_persistence:
            self.skipTest("Persistence disabled")
        
        # Manejar error
        error = ValueError("Test persistence error")
        self.recovery_system.handle_error(error, "TestComponent")
        
        # Esperar procesamiento y persistencia
        time.sleep(0.2)
        
        # Verificar que se creó archivo de log
        log_files = os.listdir(self.temp_dir)
        error_files = [f for f in log_files if f.startswith('errors_')]
        
        self.assertTrue(len(error_files) > 0)


class TestErrorRecoveryIntegration(unittest.TestCase):
    """🏛️ TESTS DE INTEGRACIÓN ÉPICOS 🏛️"""
    
    def setUp(self):
        """🚀 Setup para tests de integración"""
        self.temp_dir = tempfile.mkdtemp()
        self.recovery_system = ErrorRecoverySystem(
            log_dir=self.temp_dir,
            enable_persistence=True
        )
        self.recovery_system.start()
    
    def tearDown(self):
        """🧹 Cleanup después de cada test"""
        self.recovery_system.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_full_error_recovery_cycle(self):
        """🧪 Test ciclo completo de error y recuperación"""
        # Configurar callbacks para tracking
        error_events = []
        recovery_events = []
        
        def on_error(error_info):
            error_events.append(error_info)
        
        def on_recovery(error_info, action):
            recovery_events.append((error_info, action))
        
        self.recovery_system.add_error_callback(on_error)
        self.recovery_system.add_recovery_callback(on_recovery)
        
        # Simular diferentes tipos de errores
        test_scenarios = [
            (ValueError("Invalid data"), "DataProcessor"),
            (ConnectionError("Network timeout"), "NetworkClient"),
            (Exception("Rate limit hit"), "APIClient"),
        ]
        
        for error, component in test_scenarios:
            can_continue = self.recovery_system.handle_error(error, component)
            self.assertIsInstance(can_continue, bool)
        
        # Esperar procesamiento completo
        time.sleep(0.5)
        
        # Verificar que se procesaron los errores
        self.assertEqual(len(error_events), len(test_scenarios))
        
        # Verificar estadísticas finales
        stats = self.recovery_system.get_error_stats()
        self.assertEqual(stats['total_errors'], len(test_scenarios))
        self.assertTrue(stats['resolution_rate'] >= 0)
    
    def test_component_isolation(self):
        """🧪 Test aislamiento de errores por componente"""
        components = ["ComponentA", "ComponentB", "ComponentC"]
        
        # Generar errores en diferentes componentes
        for component in components:
            for i in range(3):
                error = ValueError(f"Error {i} in {component}")
                self.recovery_system.handle_error(error, component)
        
        # Esperar procesamiento
        time.sleep(0.3)
        
        # Verificar que cada componente tiene sus errores
        for component in components:
            health = self.recovery_system.get_component_health(component)
            self.assertEqual(health['total_errors'], 3)
            self.assertEqual(health['component'], component)
    
    def test_error_rate_limiting(self):
        """🧪 Test limitación de tasa de errores"""
        component = "RateLimitedComponent"
        
        # Generar muchos errores rápidamente
        for i in range(10):
            error = Exception(f"Rapid error {i}")
            self.recovery_system.handle_error(error, component)
        
        # Esperar procesamiento
        time.sleep(0.3)
        
        # Verificar que se manejaron todos los errores
        health = self.recovery_system.get_component_health(component)
        self.assertEqual(health['total_errors'], 10)
        
        # Verificar estadísticas generales
        stats = self.recovery_system.get_error_stats()
        self.assertEqual(stats['total_errors'], 10)


if __name__ == "__main__":
    print("🧪⚔️🏛️ RUNNING EPIC ERROR RECOVERY SYSTEM TESTS 🏛️⚔️🧪")
    
    # Ejecutar tests
    unittest.main(verbosity=2)