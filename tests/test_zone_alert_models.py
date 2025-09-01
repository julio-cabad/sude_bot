#!/usr/bin/env python3
"""
🔥⚔️ TESTS ÉPICOS PARA ZONE ALERT MODELS ⚔️🔥
Tests unitarios para los modelos de alertas con timezone Ecuador
Created by FEROZ GUERRERO DEL CÓDIGO - OLIMPO TESTING DIVISION
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from datetime import datetime, timezone, timedelta
from models.zone_alert import (
    ZoneAlert, MonitoringSession, ZoneComparison,
    AlertPriority, AlertStatus, EcuadorTimeUtils,
    ECUADOR_TZ, get_ecuador_time, utc_to_ecuador, format_ecuador_time
)
from models.zone import Zone, ZoneType


class TestEcuadorTimezone(unittest.TestCase):
    """🏛️ Tests para manejo de timezone Ecuador (UTC-5)"""
    
    def test_ecuador_timezone_constant(self):
        """Test que ECUADOR_TZ esté configurado correctamente"""
        expected_offset = timedelta(hours=-5)
        self.assertEqual(ECUADOR_TZ.utcoffset(None), expected_offset)
    
    def test_get_ecuador_time(self):
        """Test obtener hora actual en Ecuador"""
        ecuador_time = get_ecuador_time()
        self.assertEqual(ecuador_time.tzinfo, ECUADOR_TZ)
        self.assertIsInstance(ecuador_time, datetime)
    
    def test_utc_to_ecuador_conversion(self):
        """Test conversión de UTC a Ecuador"""
        # UTC time
        utc_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        # Convert to Ecuador
        ecuador_time = utc_to_ecuador(utc_time)
        
        # Should be 5 hours behind UTC (07:00)
        expected_time = datetime(2024, 1, 15, 7, 0, 0, tzinfo=ECUADOR_TZ)
        self.assertEqual(ecuador_time, expected_time)
    
    def test_utc_to_ecuador_naive_datetime(self):
        """Test conversión de datetime naive (sin timezone) a Ecuador"""
        # Naive datetime (assumed UTC)
        naive_time = datetime(2024, 1, 15, 12, 0, 0)
        
        # Convert to Ecuador
        ecuador_time = utc_to_ecuador(naive_time)
        
        # Should be 5 hours behind (07:00)
        expected_time = datetime(2024, 1, 15, 7, 0, 0, tzinfo=ECUADOR_TZ)
        self.assertEqual(ecuador_time, expected_time)
    
    def test_format_ecuador_time(self):
        """Test formateo de tiempo en Ecuador"""
        test_time = datetime(2024, 1, 15, 14, 30, 45, tzinfo=ECUADOR_TZ)
        formatted = format_ecuador_time(test_time)
        
        expected = "2024-01-15 14:30:45 ECT"
        self.assertEqual(formatted, expected)
    
    def test_format_ecuador_time_with_utc_input(self):
        """Test formateo convirtiendo de UTC a Ecuador"""
        utc_time = datetime(2024, 1, 15, 19, 30, 45, tzinfo=timezone.utc)
        formatted = format_ecuador_time(utc_time)
        
        # UTC 19:30 = Ecuador 14:30
        expected = "2024-01-15 14:30:45 ECT"
        self.assertEqual(formatted, expected)


class TestEcuadorTimeUtils(unittest.TestCase):
    """⚔️ Tests para utilidades de tiempo Ecuador"""
    
    def test_now(self):
        """Test obtener hora actual"""
        now = EcuadorTimeUtils.now()
        self.assertEqual(now.tzinfo, ECUADOR_TZ)
    
    def test_from_utc(self):
        """Test conversión desde UTC"""
        utc_time = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)
        ecuador_time = EcuadorTimeUtils.from_utc(utc_time)
        
        expected = datetime(2024, 1, 15, 15, 0, 0, tzinfo=ECUADOR_TZ)
        self.assertEqual(ecuador_time, expected)
    
    def test_format_time(self):
        """Test formateo de tiempo"""
        test_time = datetime(2024, 1, 15, 10, 15, 30, tzinfo=ECUADOR_TZ)
        formatted = EcuadorTimeUtils.format_time(test_time)
        
        expected = "2024-01-15 10:15:30 ECT"
        self.assertEqual(formatted, expected)
    
    def test_parse_binance_time(self):
        """Test parseo de timestamp de Binance"""
        # Binance timestamp en milliseconds (ejemplo: 1705339200000 = 2024-01-15 12:00:00 UTC)
        binance_timestamp = 1705339200000
        
        ecuador_time = EcuadorTimeUtils.parse_binance_time(binance_timestamp)
        
        # Verificar que el resultado esté en Ecuador timezone
        self.assertEqual(ecuador_time.tzinfo, ECUADOR_TZ)
        
        # Verificar que la conversión sea correcta (UTC - 5 horas)
        utc_time = datetime.fromtimestamp(binance_timestamp / 1000, tz=timezone.utc)
        expected_ecuador = utc_to_ecuador(utc_time)
        self.assertEqual(ecuador_time, expected_ecuador)
    
    def test_time_ago_seconds(self):
        """Test cálculo de tiempo transcurrido - segundos"""
        now = EcuadorTimeUtils.now()
        past_time = now - timedelta(seconds=30)
        
        result = EcuadorTimeUtils.time_ago(past_time)
        self.assertEqual(result, "hace unos segundos")
    
    def test_time_ago_minutes(self):
        """Test cálculo de tiempo transcurrido - minutos"""
        now = EcuadorTimeUtils.now()
        past_time = now - timedelta(minutes=5)
        
        result = EcuadorTimeUtils.time_ago(past_time)
        self.assertEqual(result, "hace 5 minutos")
    
    def test_time_ago_hours(self):
        """Test cálculo de tiempo transcurrido - horas"""
        now = EcuadorTimeUtils.now()
        past_time = now - timedelta(hours=2)
        
        result = EcuadorTimeUtils.time_ago(past_time)
        self.assertEqual(result, "hace 2 horas")
    
    def test_time_ago_days(self):
        """Test cálculo de tiempo transcurrido - días"""
        now = EcuadorTimeUtils.now()
        past_time = now - timedelta(days=3)
        
        result = EcuadorTimeUtils.time_ago(past_time)
        self.assertEqual(result, "hace 3 días")


class TestZoneAlert(unittest.TestCase):
    """🏛️ Tests para ZoneAlert model"""
    
    def setUp(self):
        """Setup para tests"""
        current_time = get_ecuador_time()
        self.test_zone = Zone.create_supply_zone(
            swing_price=67500.0,
            swing_time=current_time,
            swing_bar_index=100,
            atr_buffer=300.0,
            current_time=current_time,
            current_bar_index=100
        )
    
    def test_zone_alert_creation(self):
        """Test creación básica de ZoneAlert"""
        alert = ZoneAlert(
            symbol="BTCUSDT",
            timeframe="5m",
            new_zones=[self.test_zone]
        )
        
        self.assertEqual(alert.symbol, "BTCUSDT")
        self.assertEqual(alert.timeframe, "5m")
        self.assertEqual(len(alert.new_zones), 1)
        self.assertEqual(alert.status, AlertStatus.NEW)
        self.assertEqual(alert.detection_time.tzinfo, ECUADOR_TZ)
        self.assertTrue(len(alert.alert_id) == 8)  # UUID truncado
    
    def test_automatic_message_generation(self):
        """Test generación automática de mensaje"""
        alert = ZoneAlert(
            symbol="BTCUSDT",
            timeframe="5m",
            new_zones=[self.test_zone]
        )
        
        # El POI se calcula automáticamente: (swing_price + (swing_price - atr_buffer)) / 2
        # swing_price=67500, atr_buffer=300 -> top=67500, bottom=67200 -> poi=67350
        expected_message = f"🚨 Nueva zona SUPPLY detectada en BTCUSDT a ${self.test_zone.poi:,.2f}"
        self.assertEqual(alert.message, expected_message)
    
    def test_automatic_priority_calculation(self):
        """Test cálculo automático de prioridad"""
        # 1 zona = MEDIUM
        alert_1 = ZoneAlert(symbol="BTCUSDT", new_zones=[self.test_zone])
        self.assertEqual(alert_1.priority, AlertPriority.MEDIUM)
        
        # 2 zonas = HIGH
        alert_2 = ZoneAlert(symbol="BTCUSDT", new_zones=[self.test_zone, self.test_zone])
        self.assertEqual(alert_2.priority, AlertPriority.HIGH)
        
        # 3+ zonas = CRITICAL
        alert_3 = ZoneAlert(symbol="BTCUSDT", new_zones=[self.test_zone] * 3)
        self.assertEqual(alert_3.priority, AlertPriority.CRITICAL)
    
    def test_timezone_conversion_in_post_init(self):
        """Test conversión automática de timezone en __post_init__"""
        # Crear con UTC time
        utc_time = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)
        
        alert = ZoneAlert(
            symbol="BTCUSDT",
            detection_time=utc_time
        )
        
        # Debe convertirse automáticamente a Ecuador
        expected_ecuador = datetime(2024, 1, 15, 15, 0, 0, tzinfo=ECUADOR_TZ)
        self.assertEqual(alert.detection_time, expected_ecuador)
    
    def test_get_formatted_time(self):
        """Test formateo de tiempo"""
        test_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=ECUADOR_TZ)
        alert = ZoneAlert(symbol="BTCUSDT", detection_time=test_time)
        
        formatted = alert.get_formatted_time()
        expected = "2024-01-15 14:30:00 ECT"
        self.assertEqual(formatted, expected)
    
    def test_get_zone_summary(self):
        """Test resumen de zonas"""
        current_time = get_ecuador_time()
        demand_zone = Zone.create_demand_zone(
            swing_price=66000.0,
            swing_time=current_time,
            swing_bar_index=95,
            atr_buffer=300.0,
            current_time=current_time,
            current_bar_index=95
        )
        
        alert = ZoneAlert(
            symbol="BTCUSDT",
            new_zones=[self.test_zone, demand_zone]
        )
        
        summary = alert.get_zone_summary()
        
        self.assertEqual(summary["total_zones"], 2)
        self.assertEqual(summary["supply_count"], 1)
        self.assertEqual(summary["demand_count"], 1)
        # Los POI se calculan automáticamente, usamos los valores reales
        self.assertEqual(summary["price_range"]["min"], demand_zone.poi)
        self.assertEqual(summary["price_range"]["max"], self.test_zone.poi)
    
    def test_status_management(self):
        """Test manejo de estados de alerta"""
        alert = ZoneAlert(symbol="BTCUSDT")
        
        # Estado inicial
        self.assertEqual(alert.status, AlertStatus.NEW)
        
        # Marcar como mostrada
        alert.mark_as_displayed()
        self.assertEqual(alert.status, AlertStatus.DISPLAYED)
        
        # Marcar como reconocida
        alert.mark_as_acknowledged()
        self.assertEqual(alert.status, AlertStatus.ACKNOWLEDGED)


class TestMonitoringSession(unittest.TestCase):
    """⚔️ Tests para MonitoringSession model"""
    
    def test_monitoring_session_creation(self):
        """Test creación de sesión de monitoreo"""
        symbols = ["BTCUSDT", "ETHUSDT"]
        session = MonitoringSession(
            symbols=symbols,
            timeframe="5m"
        )
        
        self.assertEqual(session.symbols, symbols)
        self.assertEqual(session.timeframe, "5m")
        self.assertEqual(session.start_time.tzinfo, ECUADOR_TZ)
        self.assertTrue(session.active)
        self.assertEqual(session.total_alerts, 0)
        self.assertTrue(len(session.session_id) == 8)
        
        # Verificar que last_check se inicializa para todos los símbolos
        for symbol in symbols:
            self.assertIn(symbol, session.last_check)
    
    def test_add_remove_symbol(self):
        """Test añadir y remover símbolos"""
        session = MonitoringSession(symbols=["BTCUSDT"])
        
        # Añadir símbolo
        session.add_symbol("ETHUSDT")
        self.assertIn("ETHUSDT", session.symbols)
        self.assertIn("ETHUSDT", session.last_check)
        
        # Remover símbolo
        session.remove_symbol("ETHUSDT")
        self.assertNotIn("ETHUSDT", session.symbols)
        self.assertNotIn("ETHUSDT", session.last_check)
    
    def test_update_last_check(self):
        """Test actualización de último chequeo"""
        session = MonitoringSession(symbols=["BTCUSDT"])
        
        original_time = session.last_check["BTCUSDT"]
        
        # Simular paso del tiempo
        import time
        time.sleep(0.01)
        
        session.update_last_check("BTCUSDT")
        new_time = session.last_check["BTCUSDT"]
        
        self.assertGreater(new_time, original_time)
    
    def test_increment_alerts(self):
        """Test incremento de contador de alertas"""
        session = MonitoringSession()
        
        self.assertEqual(session.total_alerts, 0)
        
        session.increment_alerts()
        self.assertEqual(session.total_alerts, 1)
        
        session.increment_alerts()
        self.assertEqual(session.total_alerts, 2)
    
    def test_get_session_duration(self):
        """Test cálculo de duración de sesión"""
        session = MonitoringSession()
        
        duration = session.get_session_duration()
        self.assertIsInstance(duration, timedelta)
        self.assertGreaterEqual(duration.total_seconds(), 0)
    
    def test_stop_session(self):
        """Test detener sesión"""
        session = MonitoringSession()
        self.assertTrue(session.active)
        
        session.stop_session()
        self.assertFalse(session.active)


class TestZoneComparison(unittest.TestCase):
    """🏛️ Tests para ZoneComparison model"""
    
    def setUp(self):
        """Setup para tests"""
        current_time = get_ecuador_time()
        self.test_zone = Zone.create_supply_zone(
            swing_price=67500.0,
            swing_time=current_time,
            swing_bar_index=100,
            atr_buffer=300.0,
            current_time=current_time,
            current_bar_index=100
        )
    
    def test_zone_comparison_creation(self):
        """Test creación de comparación de zonas"""
        comparison = ZoneComparison(
            symbol="BTCUSDT",
            timeframe="5m",
            previous_count=2,
            current_count=3,
            new_zones=[self.test_zone]
        )
        
        self.assertEqual(comparison.symbol, "BTCUSDT")
        self.assertEqual(comparison.timeframe, "5m")
        self.assertEqual(comparison.previous_count, 2)
        self.assertEqual(comparison.current_count, 3)
        self.assertEqual(len(comparison.new_zones), 1)
        self.assertEqual(comparison.comparison_time.tzinfo, ECUADOR_TZ)
    
    def test_has_new_zones_property(self):
        """Test propiedad has_new_zones"""
        # Sin nuevas zonas
        comparison_1 = ZoneComparison(symbol="BTCUSDT")
        self.assertFalse(comparison_1.has_new_zones)
        
        # Con nuevas zonas
        comparison_2 = ZoneComparison(symbol="BTCUSDT", new_zones=[self.test_zone])
        self.assertTrue(comparison_2.has_new_zones)
    
    def test_has_changes_property(self):
        """Test propiedad has_changes"""
        # Sin cambios
        comparison_1 = ZoneComparison(symbol="BTCUSDT")
        self.assertFalse(comparison_1.has_changes)
        
        # Con nuevas zonas
        comparison_2 = ZoneComparison(symbol="BTCUSDT", new_zones=[self.test_zone])
        self.assertTrue(comparison_2.has_changes)
        
        # Con zonas removidas
        comparison_3 = ZoneComparison(symbol="BTCUSDT", removed_zones=[self.test_zone])
        self.assertTrue(comparison_3.has_changes)
    
    def test_get_change_summary(self):
        """Test resumen de cambios"""
        comparison = ZoneComparison(
            symbol="BTCUSDT",
            timeframe="5m",
            previous_count=2,
            current_count=3,
            new_zones=[self.test_zone],
            unchanged_zones=[self.test_zone, self.test_zone]
        )
        
        summary = comparison.get_change_summary()
        
        self.assertEqual(summary["symbol"], "BTCUSDT")
        self.assertEqual(summary["timeframe"], "5m")
        self.assertEqual(summary["changes"]["new_zones"], 1)
        self.assertEqual(summary["changes"]["removed_zones"], 0)
        self.assertEqual(summary["changes"]["unchanged_zones"], 2)
        self.assertEqual(summary["zone_counts"]["previous"], 2)
        self.assertEqual(summary["zone_counts"]["current"], 3)
        self.assertEqual(summary["zone_counts"]["net_change"], 1)


if __name__ == "__main__":
    print("🔥⚔️🏛️ EJECUTANDO TESTS ÉPICOS DE ZONE ALERT MODELS 🏛️⚔️🔥")
    print("=" * 70)
    
    # Ejecutar todos los tests
    unittest.main(verbosity=2)