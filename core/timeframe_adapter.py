#!/usr/bin/env python3
"""
⏰⚔️ TIMEFRAME ADAPTER - ADAPTADOR DE TIEMPO SUPREMO ⚔️⏰
Sistema de manejo de intervalos que haría llorar a Cronos
Created by TITANES DEL CÓDIGO - BESTIAS SUPREMAS
"""

import re
from typing import Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass


class TimeframeType(Enum):
    """⏰ TIPOS DE TIMEFRAMES ÉPICOS ⏰"""
    MINUTE = "m"
    HOUR = "h" 
    DAY = "d"
    WEEK = "w"
    MONTH = "M"


@dataclass
class TimeframeInfo:
    """📊 INFORMACIÓN DE TIMEFRAME ÉPICA 📊"""
    original: str           # Timeframe original (ej: "1h")
    value: int             # Valor numérico (ej: 1)
    unit: TimeframeType    # Tipo de unidad (ej: HOUR)
    seconds: int           # Duración en segundos
    display_name: str      # Nombre para mostrar (ej: "1 Hour")
    binance_format: str    # Formato para Binance API
    
    def __str__(self) -> str:
        return self.display_name


class TimeframeAdapter:
    """⏰⚔️ ADAPTADOR DE TIMEFRAMES SUPREMO ⚔️⏰"""
    
    # Mapeo de timeframes válidos a segundos
    VALID_TIMEFRAMES = {
        # Minutos
        "1m": 60,
        "3m": 180,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        
        # Horas
        "1h": 3600,
        "2h": 7200,
        "4h": 14400,
        "6h": 21600,
        "8h": 28800,
        "12h": 43200,
        
        # Días
        "1d": 86400,
        "3d": 259200,
        
        # Semanas
        "1w": 604800,
        
        # Meses (aproximado)
        "1M": 2592000,  # 30 días
    }
    
    # Nombres para mostrar
    DISPLAY_NAMES = {
        "1m": "1 Minute",
        "3m": "3 Minutes", 
        "5m": "5 Minutes",
        "15m": "15 Minutes",
        "30m": "30 Minutes",
        "1h": "1 Hour",
        "2h": "2 Hours",
        "4h": "4 Hours", 
        "6h": "6 Hours",
        "8h": "8 Hours",
        "12h": "12 Hours",
        "1d": "1 Day",
        "3d": "3 Days",
        "1w": "1 Week",
        "1M": "1 Month"
    }
    
    # Timeframes recomendados para diferentes estrategias
    STRATEGY_TIMEFRAMES = {
        "scalping": ["1m", "3m", "5m"],
        "day_trading": ["5m", "15m", "30m", "1h"],
        "swing_trading": ["1h", "4h", "1d"],
        "position_trading": ["1d", "1w", "1M"],
        "zone_detection": ["15m", "1h", "4h", "1d"]  # Nuestro enfoque épico
    }
    
    def __init__(self):
        print("⏰⚔️🏛️ INITIALIZING EPIC TIMEFRAME ADAPTER 🏛️⚔️⏰")
        print("🎯 CRONOS APPROVED!")
        
        # Compilar regex para parsing
        self.timeframe_pattern = re.compile(r'^(\d+)([mhdwM])$')
        
        print("✅ Timeframe Adapter initialized successfully!")
        print(f"📊 Supported timeframes: {len(self.VALID_TIMEFRAMES)}")
    
    def parse_timeframe(self, timeframe: str) -> TimeframeInfo:
        """
        ⚔️ PARSEA TIMEFRAME COMO UN ESPARTANO
        Args:
            timeframe: String del timeframe (ej: "1h", "15m")
        Returns:
            TimeframeInfo con toda la información épica
        """
        if not isinstance(timeframe, str):
            raise ValueError(f"❌ Timeframe must be string, got {type(timeframe)}")
        
        # Normalizar
        timeframe = timeframe.strip().lower()
        
        # Verificar si es válido
        if timeframe not in self.VALID_TIMEFRAMES:
            raise ValueError(f"❌ Invalid timeframe: {timeframe}. Valid: {list(self.VALID_TIMEFRAMES.keys())}")
        
        # Parsear con regex
        match = self.timeframe_pattern.match(timeframe)
        if not match:
            raise ValueError(f"❌ Invalid timeframe format: {timeframe}")
        
        value_str, unit_str = match.groups()
        value = int(value_str)
        
        # Mapear unidad
        unit_map = {
            'm': TimeframeType.MINUTE,
            'h': TimeframeType.HOUR,
            'd': TimeframeType.DAY,
            'w': TimeframeType.WEEK,
            'M': TimeframeType.MONTH
        }
        
        unit = unit_map.get(unit_str)
        if not unit:
            raise ValueError(f"❌ Invalid timeframe unit: {unit_str}")
        
        # Crear info épica
        return TimeframeInfo(
            original=timeframe,
            value=value,
            unit=unit,
            seconds=self.VALID_TIMEFRAMES[timeframe],
            display_name=self.DISPLAY_NAMES[timeframe],
            binance_format=timeframe.upper()  # Binance usa uppercase
        )
    
    def convert_timeframe_to_seconds(self, timeframe: Union[str, TimeframeInfo]) -> int:
        """
        🕐 CONVIERTE TIMEFRAME A SEGUNDOS
        Args:
            timeframe: String o TimeframeInfo
        Returns:
            Duración en segundos
        """
        if isinstance(timeframe, TimeframeInfo):
            return timeframe.seconds
        
        # Parsear si es string
        tf_info = self.parse_timeframe(timeframe)
        return tf_info.seconds
    
    def validate_timeframe(self, timeframe: str) -> bool:
        """
        ✅ VALIDA SI UN TIMEFRAME ES ÉPICO
        Args:
            timeframe: String del timeframe
        Returns:
            True si es válido, False si no
        """
        try:
            self.parse_timeframe(timeframe)
            return True
        except ValueError:
            return False
    
    def get_sleep_duration(self, timeframe: Union[str, TimeframeInfo], 
                          refresh_factor: float = 0.1) -> float:
        """
        😴 CALCULA DURACIÓN DE SLEEP PARA MONITORING
        Args:
            timeframe: Timeframe a monitorear
            refresh_factor: Factor de refresh (0.1 = 10% del timeframe)
        Returns:
            Segundos para sleep
        """
        seconds = self.convert_timeframe_to_seconds(timeframe)
        
        # Calcular sleep con factor
        sleep_duration = seconds * refresh_factor
        
        # Límites mínimos y máximos
        min_sleep = 1.0    # Mínimo 1 segundo
        max_sleep = 300.0  # Máximo 5 minutos
        
        return max(min_sleep, min(sleep_duration, max_sleep))
    
    def get_timeframes_for_strategy(self, strategy: str) -> List[str]:
        """
        🎯 OBTIENE TIMEFRAMES RECOMENDADOS PARA ESTRATEGIA
        Args:
            strategy: Nombre de la estrategia
        Returns:
            Lista de timeframes recomendados
        """
        return self.STRATEGY_TIMEFRAMES.get(strategy.lower(), [])
    
    def get_all_valid_timeframes(self) -> List[str]:
        """📋 OBTIENE TODOS LOS TIMEFRAMES VÁLIDOS"""
        return list(self.VALID_TIMEFRAMES.keys())
    
    def get_timeframe_hierarchy(self, base_timeframe: str) -> Dict[str, List[str]]:
        """
        🏗️ OBTIENE JERARQUÍA DE TIMEFRAMES
        Args:
            base_timeframe: Timeframe base
        Returns:
            Dict con timeframes menores y mayores
        """
        base_seconds = self.convert_timeframe_to_seconds(base_timeframe)
        
        smaller = []
        larger = []
        
        for tf, seconds in self.VALID_TIMEFRAMES.items():
            if seconds < base_seconds:
                smaller.append(tf)
            elif seconds > base_seconds:
                larger.append(tf)
        
        # Ordenar
        smaller.sort(key=lambda x: self.VALID_TIMEFRAMES[x])
        larger.sort(key=lambda x: self.VALID_TIMEFRAMES[x])
        
        return {
            "smaller": smaller,
            "current": base_timeframe,
            "larger": larger
        }
    
    def suggest_monitoring_timeframes(self, primary_timeframe: str) -> List[str]:
        """
        🎯 SUGIERE TIMEFRAMES PARA MONITORING MULTI-TEMPORAL
        Args:
            primary_timeframe: Timeframe principal
        Returns:
            Lista de timeframes sugeridos para análisis completo
        """
        primary_seconds = self.convert_timeframe_to_seconds(primary_timeframe)
        
        suggestions = [primary_timeframe]  # Incluir el principal
        
        # Buscar timeframe menor (para confirmación)
        for tf, seconds in self.VALID_TIMEFRAMES.items():
            if seconds < primary_seconds and seconds >= primary_seconds * 0.25:
                suggestions.append(tf)
                break
        
        # Buscar timeframe mayor (para contexto)
        for tf, seconds in self.VALID_TIMEFRAMES.items():
            if seconds > primary_seconds and seconds <= primary_seconds * 4:
                suggestions.append(tf)
                break
        
        return list(set(suggestions))  # Remover duplicados
    
    def format_duration(self, seconds: int) -> str:
        """
        📝 FORMATEA DURACIÓN EN FORMATO LEGIBLE
        Args:
            seconds: Duración en segundos
        Returns:
            String formateado (ej: "1h 30m")
        """
        if seconds < 60:
            return f"{seconds}s"
        
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if hours < 24:
            if remaining_minutes > 0:
                return f"{hours}h {remaining_minutes}m"
            return f"{hours}h"
        
        days = hours // 24
        remaining_hours = hours % 24
        
        if remaining_hours > 0:
            return f"{days}d {remaining_hours}h"
        return f"{days}d"
    
    def get_timeframe_stats(self) -> Dict:
        """📊 OBTIENE ESTADÍSTICAS DE TIMEFRAMES"""
        stats = {
            "total_timeframes": len(self.VALID_TIMEFRAMES),
            "by_unit": {},
            "shortest": None,
            "longest": None,
            "strategies": len(self.STRATEGY_TIMEFRAMES)
        }
        
        # Contar por unidad
        for tf in self.VALID_TIMEFRAMES.keys():
            tf_info = self.parse_timeframe(tf)
            unit = tf_info.unit.value
            stats["by_unit"][unit] = stats["by_unit"].get(unit, 0) + 1
        
        # Encontrar más corto y más largo
        sorted_tfs = sorted(self.VALID_TIMEFRAMES.items(), key=lambda x: x[1])
        stats["shortest"] = sorted_tfs[0][0]
        stats["longest"] = sorted_tfs[-1][0]
        
        return stats


def main():
    """🔥 FUNCIÓN PRINCIPAL PARA TESTING 🔥"""
    print("⏰⚔️🏛️ TESTING EPIC TIMEFRAME ADAPTER 🏛️⚔️⏰")
    
    # Crear adapter
    adapter = TimeframeAdapter()
    
    # Test parsing
    test_timeframes = ["1m", "15m", "1h", "4h", "1d"]
    
    print("\n🧪 TESTING TIMEFRAME PARSING:")
    for tf in test_timeframes:
        try:
            info = adapter.parse_timeframe(tf)
            print(f"✅ {tf} -> {info}")
            print(f"   Seconds: {info.seconds}")
            print(f"   Sleep duration: {adapter.get_sleep_duration(tf):.1f}s")
        except Exception as e:
            print(f"❌ {tf} -> Error: {e}")
    
    # Test validación
    print("\n🔍 TESTING VALIDATION:")
    valid_tests = ["1h", "15m", "invalid", "2x", ""]
    for tf in valid_tests:
        is_valid = adapter.validate_timeframe(tf)
        print(f"{'✅' if is_valid else '❌'} {tf}: {is_valid}")
    
    # Test estrategias
    print("\n🎯 TESTING STRATEGY TIMEFRAMES:")
    for strategy in ["scalping", "day_trading", "zone_detection"]:
        tfs = adapter.get_timeframes_for_strategy(strategy)
        print(f"📊 {strategy}: {tfs}")
    
    # Test jerarquía
    print("\n🏗️ TESTING TIMEFRAME HIERARCHY:")
    hierarchy = adapter.get_timeframe_hierarchy("1h")
    print(f"📊 Hierarchy for 1h:")
    print(f"   Smaller: {hierarchy['smaller']}")
    print(f"   Current: {hierarchy['current']}")
    print(f"   Larger: {hierarchy['larger']}")
    
    # Test sugerencias
    print("\n💡 TESTING MONITORING SUGGESTIONS:")
    suggestions = adapter.suggest_monitoring_timeframes("1h")
    print(f"📊 Suggestions for 1h: {suggestions}")
    
    # Test estadísticas
    print("\n📊 TIMEFRAME STATS:")
    stats = adapter.get_timeframe_stats()
    print(f"📈 {stats}")
    
    print("\n🏆 EPIC TIMEFRAME ADAPTER TEST COMPLETE! 🏆")


if __name__ == "__main__":
    main()