#!/usr/bin/env python3
"""
🔥⚔️ ZONE ALERT DATA MODELS - ECUADOR TIMEZONE (UTC-5) ⚔️🔥
Modelos de datos para el sistema de alertas en tiempo real
Created by FEROZ GUERRERO DEL CÓDIGO - OLIMPO APPROVED
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid

from models.zone import Zone


class AlertPriority(Enum):
    """Prioridad de las alertas"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(Enum):
    """Estado de las alertas"""
    NEW = "NEW"
    DISPLAYED = "DISPLAYED"
    ACKNOWLEDGED = "ACKNOWLEDGED"


# TIMEZONE ECUADOR (UTC-5) - CONFIGURACIÓN ÉPICA
ECUADOR_TZ = timezone(timedelta(hours=-5))


def get_ecuador_time() -> datetime:
    """
    🏛️ OBTIENE LA HORA ACTUAL EN ECUADOR (UTC-5)
    Returns: datetime object in Ecuador timezone
    """
    return datetime.now(ECUADOR_TZ)


def utc_to_ecuador(utc_time: datetime) -> datetime:
    """
    ⚔️ CONVIERTE UTC A HORA DE ECUADOR (UTC-5)
    Args:
        utc_time: datetime in UTC
    Returns:
        datetime in Ecuador timezone (UTC-5)
    """
    if utc_time.tzinfo is None:
        # Si no tiene timezone, asumimos que es UTC
        utc_time = utc_time.replace(tzinfo=timezone.utc)
    
    return utc_time.astimezone(ECUADOR_TZ)


def format_ecuador_time(dt: datetime) -> str:
    """
    🔥 FORMATEA TIEMPO EN ZONA HORARIA DE ECUADOR
    Args:
        dt: datetime object
    Returns:
        Formatted string in Ecuador timezone
    """
    ecuador_time = utc_to_ecuador(dt) if dt.tzinfo != ECUADOR_TZ else dt
    return ecuador_time.strftime("%Y-%m-%d %H:%M:%S ECT")


@dataclass
class ZoneAlert:
    """
    🏛️ ALERTA DE ZONA ÉPICA - ECUADOR TIMEZONE
    Representa una alerta cuando se detecta una nueva zona
    """
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str = ""
    timeframe: str = ""
    new_zones: List[Zone] = field(default_factory=list)
    detection_time: datetime = field(default_factory=get_ecuador_time)
    priority: AlertPriority = AlertPriority.MEDIUM
    status: AlertStatus = AlertStatus.NEW
    message: str = ""
    
    def __post_init__(self):
        """Post-initialization para validación y configuración"""
        # Asegurar que detection_time esté en Ecuador timezone
        if self.detection_time.tzinfo != ECUADOR_TZ:
            self.detection_time = utc_to_ecuador(self.detection_time)
        
        # Generar mensaje automático si no se proporciona
        if not self.message:
            self.message = self._generate_alert_message()
        
        # Determinar prioridad automáticamente
        if self.priority == AlertPriority.MEDIUM:
            self.priority = self._calculate_priority()
    
    def _generate_alert_message(self) -> str:
        """Genera mensaje automático de alerta"""
        if not self.new_zones:
            return f"🚨 Nueva actividad detectada en {self.symbol}"
        
        zone_count = len(self.new_zones)
        zone_types = [zone.zone_type.name for zone in self.new_zones]
        
        if zone_count == 1:
            zone_type = zone_types[0]
            price = self.new_zones[0].poi
            return f"🚨 Nueva zona {zone_type} detectada en {self.symbol} a ${price:,.2f}"
        else:
            return f"🚨 {zone_count} nuevas zonas detectadas en {self.symbol}"
    
    def _calculate_priority(self) -> AlertPriority:
        """Calcula prioridad basada en las zonas detectadas"""
        if not self.new_zones:
            return AlertPriority.LOW
        
        zone_count = len(self.new_zones)
        
        # Más zonas = mayor prioridad
        if zone_count >= 3:
            return AlertPriority.CRITICAL
        elif zone_count == 2:
            return AlertPriority.HIGH
        else:
            return AlertPriority.MEDIUM
    
    def get_formatted_time(self) -> str:
        """Obtiene tiempo formateado en Ecuador"""
        return format_ecuador_time(self.detection_time)
    
    def get_zone_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de las zonas en la alerta"""
        if not self.new_zones:
            return {}
        
        supply_zones = [z for z in self.new_zones if z.zone_type.name == "SUPPLY"]
        demand_zones = [z for z in self.new_zones if z.zone_type.name == "DEMAND"]
        
        return {
            "total_zones": len(self.new_zones),
            "supply_count": len(supply_zones),
            "demand_count": len(demand_zones),
            "price_range": {
                "min": min(z.poi for z in self.new_zones),
                "max": max(z.poi for z in self.new_zones)
            }
        }
    
    def mark_as_displayed(self):
        """Marca la alerta como mostrada"""
        self.status = AlertStatus.DISPLAYED
    
    def mark_as_acknowledged(self):
        """Marca la alerta como reconocida"""
        self.status = AlertStatus.ACKNOWLEDGED


@dataclass
class MonitoringSession:
    """
    ⚔️ SESIÓN DE MONITOREO ÉPICA
    Rastrea el estado activo del monitoreo
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbols: List[str] = field(default_factory=list)
    timeframe: str = "5m"
    start_time: datetime = field(default_factory=get_ecuador_time)
    last_check: Dict[str, datetime] = field(default_factory=dict)
    zone_history: Dict[str, Dict] = field(default_factory=dict)
    total_alerts: int = 0
    active: bool = True
    
    def __post_init__(self):
        """Post-initialization para configuración"""
        # Asegurar que start_time esté en Ecuador timezone
        if self.start_time.tzinfo != ECUADOR_TZ:
            self.start_time = utc_to_ecuador(self.start_time)
        
        # Inicializar last_check para todos los símbolos
        for symbol in self.symbols:
            if symbol not in self.last_check:
                self.last_check[symbol] = self.start_time
    
    def add_symbol(self, symbol: str):
        """Añade un símbolo al monitoreo"""
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            self.last_check[symbol] = get_ecuador_time()
            self.zone_history[symbol] = {}
    
    def remove_symbol(self, symbol: str):
        """Remueve un símbolo del monitoreo"""
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            self.last_check.pop(symbol, None)
            self.zone_history.pop(symbol, None)
    
    def update_last_check(self, symbol: str):
        """Actualiza el último chequeo para un símbolo"""
        self.last_check[symbol] = get_ecuador_time()
    
    def increment_alerts(self):
        """Incrementa el contador de alertas"""
        self.total_alerts += 1
    
    def get_session_duration(self) -> timedelta:
        """Obtiene la duración de la sesión"""
        return get_ecuador_time() - self.start_time
    
    def get_formatted_start_time(self) -> str:
        """Obtiene tiempo de inicio formateado"""
        return format_ecuador_time(self.start_time)
    
    def stop_session(self):
        """Detiene la sesión de monitoreo"""
        self.active = False


@dataclass
class ZoneComparison:
    """
    🏛️ COMPARACIÓN DE ZONAS ÉPICA
    Resultado de comparar zonas actuales vs anteriores
    """
    symbol: str = ""
    timeframe: str = ""
    comparison_time: datetime = field(default_factory=get_ecuador_time)
    previous_count: int = 0
    current_count: int = 0
    new_zones: List[Zone] = field(default_factory=list)
    removed_zones: List[Zone] = field(default_factory=list)
    unchanged_zones: List[Zone] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization para configuración"""
        # Asegurar que comparison_time esté en Ecuador timezone
        if self.comparison_time.tzinfo != ECUADOR_TZ:
            self.comparison_time = utc_to_ecuador(self.comparison_time)
    
    @property
    def has_new_zones(self) -> bool:
        """Verifica si hay nuevas zonas"""
        return len(self.new_zones) > 0
    
    @property
    def has_changes(self) -> bool:
        """Verifica si hay cambios en las zonas"""
        return len(self.new_zones) > 0 or len(self.removed_zones) > 0
    
    def get_change_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de cambios"""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "comparison_time": self.get_formatted_time(),
            "changes": {
                "new_zones": len(self.new_zones),
                "removed_zones": len(self.removed_zones),
                "unchanged_zones": len(self.unchanged_zones)
            },
            "zone_counts": {
                "previous": self.previous_count,
                "current": self.current_count,
                "net_change": self.current_count - self.previous_count
            }
        }
    
    def get_formatted_time(self) -> str:
        """Obtiene tiempo de comparación formateado"""
        return format_ecuador_time(self.comparison_time)


# UTILIDADES ÉPICAS PARA MANEJO DE TIEMPO
class EcuadorTimeUtils:
    """🔥 UTILIDADES DE TIEMPO PARA ECUADOR (UTC-5) 🔥"""
    
    @staticmethod
    def now() -> datetime:
        """Hora actual en Ecuador"""
        return get_ecuador_time()
    
    @staticmethod
    def from_utc(utc_time: datetime) -> datetime:
        """Convierte de UTC a Ecuador"""
        return utc_to_ecuador(utc_time)
    
    @staticmethod
    def format_time(dt: datetime) -> str:
        """Formatea tiempo en Ecuador"""
        return format_ecuador_time(dt)
    
    @staticmethod
    def parse_binance_time(timestamp: int) -> datetime:
        """
        Convierte timestamp de Binance (ms) a Ecuador time
        Args:
            timestamp: Binance timestamp in milliseconds
        Returns:
            datetime in Ecuador timezone
        """
        utc_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        return utc_to_ecuador(utc_time)
    
    @staticmethod
    def time_ago(dt: datetime) -> str:
        """
        Calcula tiempo transcurrido desde una fecha
        Args:
            dt: datetime object
        Returns:
            Human readable time difference
        """
        now = get_ecuador_time()
        if dt.tzinfo != ECUADOR_TZ:
            dt = utc_to_ecuador(dt)
        
        diff = now - dt
        
        if diff.days > 0:
            return f"hace {diff.days} día{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"hace {hours} hora{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"hace {minutes} minuto{'s' if minutes > 1 else ''}"
        else:
            return "hace unos segundos"


if __name__ == "__main__":
    # 🔥 PRUEBAS ÉPICAS DE LOS MODELOS 🔥
    print("🔥⚔️🏛️ TESTING ZONE ALERT MODELS 🏛️⚔️🔥")
    print("=" * 60)
    
    # Test timezone handling
    print(f"🕐 Hora actual Ecuador: {EcuadorTimeUtils.now()}")
    print(f"🕐 Formateada: {EcuadorTimeUtils.format_time(EcuadorTimeUtils.now())}")
    
    # Test alert creation
    from models.zone import Zone, ZoneType
    test_zone = Zone(
        zone_type=ZoneType.SUPPLY,
        poi=67500.0,
        top=67800.0,
        bottom=67200.0,
        timestamp=EcuadorTimeUtils.now()
    )
    
    alert = ZoneAlert(
        symbol="BTCUSDT",
        timeframe="5m",
        new_zones=[test_zone]
    )
    
    print(f"\\n🚨 Alerta creada:")
    print(f"   ID: {alert.alert_id}")
    print(f"   Mensaje: {alert.message}")
    print(f"   Tiempo: {alert.get_formatted_time()}")
    print(f"   Prioridad: {alert.priority.value}")
    
    # Test monitoring session
    session = MonitoringSession(
        symbols=["BTCUSDT", "ETHUSDT"],
        timeframe="5m"
    )
    
    print(f"\\n⚔️ Sesión de monitoreo:")
    print(f"   ID: {session.session_id}")
    print(f"   Símbolos: {session.symbols}")
    print(f"   Inicio: {session.get_formatted_start_time()}")
    
    print("\\n🏆 MODELOS ÉPICOS CREADOS EXITOSAMENTE! 🏆")