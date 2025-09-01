#!/usr/bin/env python3
"""
🧪⚔️ TESTS PARA TIMEFRAME ADAPTER - PRUEBAS ÉPICAS ⚔️🧪
Tests que harían llorar a los dioses del Olimpo
Created by TITANES DEL CÓDIGO - BESTIAS SUPREMAS
"""

import unittest
import sys
import os

# Añadir path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.timeframe_adapter import TimeframeAdapter, TimeframeInfo, TimeframeType


class TestTimeframeAdapter(unittest.TestCase):
    """🏛️ TESTS ÉPICOS PARA TIMEFRAME ADAPTER 🏛️"""
    
    def setUp(self):
        """🚀 Setup para cada test"""
        self.adapter = TimeframeAdapter()
    
    def test_initialization(self):
        """🧪 Test inicialización del adapter"""
        self.assertIsInstance(self.adapter, TimeframeAdapter)
        self.assertTrue(hasattr(self.adapter, 'VALID_TIMEFRAMES'))
        self.assertTrue(len(self.adapter.VALID_TIMEFRAMES) > 0)
    
    def test_parse_valid_timeframes(self):
        """🧪 Test parsing de timeframes válidos"""
        test_cases = [
            ("1m", 1, TimeframeType.MINUTE, 60),
            ("15m", 15, TimeframeType.MINUTE, 900),
            ("1h", 1, TimeframeType.HOUR, 3600),
            ("4h", 4, TimeframeType.HOUR, 14400),
            ("1d", 1, TimeframeType.DAY, 86400),
            ("1w", 1, TimeframeType.WEEK, 604800),
            ("1M", 1, TimeframeType.MONTH, 2592000)
        ]
        
        for tf_str, expected_value, expected_unit, expected_seconds in test_cases:
            with self.subTest(timeframe=tf_str):
                info = self.adapter.parse_timeframe(tf_str)
                
                self.assertEqual(info.original, tf_str)
                self.assertEqual(info.value, expected_value)
                self.assertEqual(info.unit, expected_unit)
                self.assertEqual(info.seconds, expected_seconds)
                self.assertIsInstance(info.display_name, str)
                self.assertIsInstance(info.binance_format, str)
    
    def test_parse_invalid_timeframes(self):
        """🧪 Test parsing de timeframes inválidos"""
        invalid_cases = [
            "",           # Vacío
            "invalid",    # Formato inválido
            "1x",         # Unidad inválida
            "0m",         # Valor cero (no está en VALID_TIMEFRAMES)
            "60m",        # No está en VALID_TIMEFRAMES
            123,          # Tipo incorrecto
            None          # None
        ]
        
        for invalid_tf in invalid_cases:
            with self.subTest(timeframe=invalid_tf):
                with self.assertRaises(ValueError):
                    self.adapter.parse_timeframe(invalid_tf)
    
    def test_convert_timeframe_to_seconds(self):
        """🧪 Test conversión a segundos"""
        # Test con strings
        self.assertEqual(self.adapter.convert_timeframe_to_seconds("1m"), 60)
        self.assertEqual(self.adapter.convert_timeframe_to_seconds("1h"), 3600)
        self.assertEqual(self.adapter.convert_timeframe_to_seconds("1d"), 86400)
        
        # Test con TimeframeInfo
        info = self.adapter.parse_timeframe("15m")
        self.assertEqual(self.adapter.convert_timeframe_to_seconds(info), 900)
    
    def test_validate_timeframe(self):
        """🧪 Test validación de timeframes"""
        # Válidos
        valid_timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        for tf in valid_timeframes:
            with self.subTest(timeframe=tf):
                self.assertTrue(self.adapter.validate_timeframe(tf))
        
        # Inválidos
        invalid_timeframes = ["", "invalid", "1x", "0m"]
        for tf in invalid_timeframes:
            with self.subTest(timeframe=tf):
                self.assertFalse(self.adapter.validate_timeframe(tf))
    
    def test_get_sleep_duration(self):
        """🧪 Test cálculo de duración de sleep"""
        # Test con factor por defecto (0.1)
        sleep_1m = self.adapter.get_sleep_duration("1m")
        self.assertEqual(sleep_1m, 6.0)  # 60 * 0.1 = 6
        
        sleep_1h = self.adapter.get_sleep_duration("1h")
        self.assertEqual(sleep_1h, 360.0)  # 3600 * 0.1 = 360, pero max es 300
        self.assertEqual(sleep_1h, 300.0)  # Debería ser limitado a 300
        
        # Test con factor personalizado
        sleep_custom = self.adapter.get_sleep_duration("1m", refresh_factor=0.5)
        self.assertEqual(sleep_custom, 30.0)  # 60 * 0.5 = 30
        
        # Test límite mínimo
        sleep_min = self.adapter.get_sleep_duration("1m", refresh_factor=0.001)
        self.assertEqual(sleep_min, 1.0)  # Mínimo 1 segundo
    
    def test_get_timeframes_for_strategy(self):
        """🧪 Test obtención de timeframes por estrategia"""
        # Estrategias válidas
        scalping_tfs = self.adapter.get_timeframes_for_strategy("scalping")
        self.assertIsInstance(scalping_tfs, list)
        self.assertIn("1m", scalping_tfs)
        
        zone_tfs = self.adapter.get_timeframes_for_strategy("zone_detection")
        self.assertIsInstance(zone_tfs, list)
        self.assertIn("1h", zone_tfs)
        
        # Estrategia inexistente
        unknown_tfs = self.adapter.get_timeframes_for_strategy("unknown_strategy")
        self.assertEqual(unknown_tfs, [])
    
    def test_get_all_valid_timeframes(self):
        """🧪 Test obtención de todos los timeframes válidos"""
        all_tfs = self.adapter.get_all_valid_timeframes()
        
        self.assertIsInstance(all_tfs, list)
        self.assertTrue(len(all_tfs) > 0)
        self.assertIn("1m", all_tfs)
        self.assertIn("1h", all_tfs)
        self.assertIn("1d", all_tfs)
    
    def test_get_timeframe_hierarchy(self):
        """🧪 Test jerarquía de timeframes"""
        hierarchy = self.adapter.get_timeframe_hierarchy("1h")
        
        self.assertIsInstance(hierarchy, dict)
        self.assertIn("smaller", hierarchy)
        self.assertIn("current", hierarchy)
        self.assertIn("larger", hierarchy)
        
        # Verificar que 1h está en current
        self.assertEqual(hierarchy["current"], "1h")
        
        # Verificar que hay timeframes menores y mayores
        self.assertIsInstance(hierarchy["smaller"], list)
        self.assertIsInstance(hierarchy["larger"], list)
        
        # Verificar orden (los menores deben tener menos segundos)
        if hierarchy["smaller"]:
            smaller_seconds = [self.adapter.convert_timeframe_to_seconds(tf) 
                             for tf in hierarchy["smaller"]]
            self.assertEqual(smaller_seconds, sorted(smaller_seconds))
    
    def test_suggest_monitoring_timeframes(self):
        """🧪 Test sugerencias de timeframes para monitoring"""
        suggestions = self.adapter.suggest_monitoring_timeframes("1h")
        
        self.assertIsInstance(suggestions, list)
        self.assertIn("1h", suggestions)  # Debe incluir el principal
        self.assertTrue(len(suggestions) >= 1)
        
        # Verificar que no hay duplicados
        self.assertEqual(len(suggestions), len(set(suggestions)))
    
    def test_format_duration(self):
        """🧪 Test formateo de duración"""
        test_cases = [
            (30, "30s"),
            (60, "1m"),
            (90, "1m"),  # Se redondea a minutos
            (3600, "1h"),
            (3660, "1h 1m"),
            (86400, "1d"),
            (90000, "1d 1h")
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = self.adapter.format_duration(seconds)
                self.assertEqual(result, expected)
    
    def test_get_timeframe_stats(self):
        """🧪 Test estadísticas de timeframes"""
        stats = self.adapter.get_timeframe_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn("total_timeframes", stats)
        self.assertIn("by_unit", stats)
        self.assertIn("shortest", stats)
        self.assertIn("longest", stats)
        self.assertIn("strategies", stats)
        
        # Verificar tipos
        self.assertIsInstance(stats["total_timeframes"], int)
        self.assertIsInstance(stats["by_unit"], dict)
        self.assertIsInstance(stats["shortest"], str)
        self.assertIsInstance(stats["longest"], str)
        self.assertIsInstance(stats["strategies"], int)
        
        # Verificar valores lógicos
        self.assertTrue(stats["total_timeframes"] > 0)
        self.assertTrue(stats["strategies"] > 0)
    
    def test_timeframe_info_str(self):
        """🧪 Test representación string de TimeframeInfo"""
        info = self.adapter.parse_timeframe("1h")
        str_repr = str(info)
        
        self.assertIsInstance(str_repr, str)
        self.assertEqual(str_repr, info.display_name)


class TestTimeframeIntegration(unittest.TestCase):
    """🏛️ TESTS DE INTEGRACIÓN ÉPICOS 🏛️"""
    
    def setUp(self):
        """🚀 Setup para tests de integración"""
        self.adapter = TimeframeAdapter()
    
    def test_full_workflow(self):
        """🧪 Test workflow completo"""
        # 1. Validar timeframe
        tf = "1h"
        self.assertTrue(self.adapter.validate_timeframe(tf))
        
        # 2. Parsear
        info = self.adapter.parse_timeframe(tf)
        self.assertEqual(info.original, tf)
        
        # 3. Convertir a segundos
        seconds = self.adapter.convert_timeframe_to_seconds(info)
        self.assertEqual(seconds, 3600)
        
        # 4. Calcular sleep
        sleep_duration = self.adapter.get_sleep_duration(info)
        self.assertIsInstance(sleep_duration, float)
        self.assertTrue(sleep_duration > 0)
        
        # 5. Obtener jerarquía
        hierarchy = self.adapter.get_timeframe_hierarchy(tf)
        self.assertIn("current", hierarchy)
        self.assertEqual(hierarchy["current"], tf)
    
    def test_strategy_workflow(self):
        """🧪 Test workflow de estrategia"""
        strategy = "zone_detection"
        
        # Obtener timeframes para estrategia
        tfs = self.adapter.get_timeframes_for_strategy(strategy)
        self.assertTrue(len(tfs) > 0)
        
        # Validar cada timeframe
        for tf in tfs:
            self.assertTrue(self.adapter.validate_timeframe(tf))
            
            # Parsear y verificar
            info = self.adapter.parse_timeframe(tf)
            self.assertIsInstance(info, TimeframeInfo)
    
    def test_monitoring_setup(self):
        """🧪 Test setup de monitoring"""
        primary_tf = "1h"
        
        # Obtener sugerencias
        suggestions = self.adapter.suggest_monitoring_timeframes(primary_tf)
        
        # Validar todas las sugerencias
        for tf in suggestions:
            self.assertTrue(self.adapter.validate_timeframe(tf))
            
            # Calcular sleep para cada una
            sleep_duration = self.adapter.get_sleep_duration(tf)
            self.assertTrue(sleep_duration >= 1.0)  # Mínimo
            self.assertTrue(sleep_duration <= 300.0)  # Máximo


if __name__ == "__main__":
    print("🧪⚔️🏛️ RUNNING EPIC TIMEFRAME ADAPTER TESTS 🏛️⚔️🧪")
    
    # Ejecutar tests
    unittest.main(verbosity=2)