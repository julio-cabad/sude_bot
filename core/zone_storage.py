#!/usr/bin/env python3
"""
🔥⚔️ ZONE STORAGE - GUARDIÁN ÉPICO DE LA MEMORIA ⚔️🔥
Sistema de almacenamiento para zonas SMC con datos REALES de Binance
Created by FEROZ GUERRERO DEL CÓDIGO - OLIMPO STORAGE DIVISION
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

from models.zone import Zone
from models.zone_alert import EcuadorTimeUtils, ECUADOR_TZ
from demo.implacable_zones_detector import ImplacableZonesDetector

# Setup logging
logger = logging.getLogger(__name__)


class ZoneStorage:
    """
    🏛️ GUARDIÁN ÉPICO DE ZONAS SMC
    Almacena y gestiona zonas detectadas con datos REALES de Binance
    """
    
    def __init__(self, storage_dir: str = "data/zone_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivos de almacenamiento
        self.zones_file = self.storage_dir / "zones_data.json"
        self.metadata_file = self.storage_dir / "metadata.json"
        self.backup_dir = self.storage_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Cache en memoria para acceso rápido
        self._memory_cache: Dict[str, Dict] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Configuración
        self.max_zones_per_symbol = 100
        self.max_age_hours = 24
        self.cache_ttl_minutes = 15
        
        print(f"🏛️ ZoneStorage inicializado en: {self.storage_dir}")
        print(f"📊 Configuración: max_zones={self.max_zones_per_symbol}, max_age={self.max_age_hours}h")
        
        # Cargar datos existentes
        self._load_existing_data()
    
    def _load_existing_data(self) -> None:
        """Carga datos existentes del almacenamiento"""
        try:
            if self.zones_file.exists():
                with open(self.zones_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Convertir timestamps de vuelta a datetime
                for symbol, symbol_data in data.items():
                    if 'zones' in symbol_data:
                        for zone_data in symbol_data['zones']:
                            if 'detection_time' in zone_data:
                                zone_data['detection_time'] = datetime.fromisoformat(zone_data['detection_time'])
                    
                    self._memory_cache[symbol] = symbol_data
                    self._cache_timestamps[symbol] = EcuadorTimeUtils.now()
                
                print(f"✅ Datos cargados para {len(data)} símbolos")
            else:
                print("📝 No hay datos previos - iniciando almacenamiento limpio")
                
        except Exception as e:
            logger.error(f"Error cargando datos existentes: {e}")
            print(f"⚠️ Error cargando datos: {e}")
    
    def store_zones_from_detector(self, symbol: str, timeframe: str = "1h") -> bool:
        """
        🔥 ALMACENA ZONAS USANDO DETECTOR REAL DE BINANCE
        Usa ImplacableZonesDetector para obtener datos reales
        """
        try:
            print(f"\\n🔥⚔️ DETECTANDO ZONAS REALES PARA {symbol} ⚔️🔥")
            print("-" * 50)
            
            # Usar nuestro detector épico con datos reales
            detector = ImplacableZonesDetector(symbol, timeframe)
            
            # Ejecutar detección completa
            success = detector.run_implacable_detection()
            
            if not success:
                print(f"❌ Fallo en detección para {symbol}")
                return False
            
            # Obtener zonas detectadas
            zones_data = detector.export_implacable_json()
            
            if not zones_data:
                print(f"⚠️ No se obtuvieron datos de zonas para {symbol}")
                return False
            
            # Preparar datos para almacenamiento
            storage_data = {
                'symbol': symbol,
                'timeframe': timeframe,
                'detection_time': EcuadorTimeUtils.now(),
                'current_price': zones_data.get('current_price', 0),
                'supply_zones': zones_data.get('supply_zones', []),
                'demand_zones': zones_data.get('demand_zones', []),
                'total_zones': len(zones_data.get('supply_zones', [])) + len(zones_data.get('demand_zones', [])),
                'tradingview_precision': zones_data.get('tradingview_precision', {}),
                'raw_detector_data': zones_data  # Guardar datos completos
            }
            
            # Almacenar en memoria y disco
            self._store_symbol_data(symbol, storage_data)
            
            print(f"✅ ZONAS REALES ALMACENADAS PARA {symbol}:")
            print(f"   📊 Supply zones: {len(storage_data['supply_zones'])}")
            print(f"   📊 Demand zones: {len(storage_data['demand_zones'])}")
            print(f"   💰 Precio actual: ${storage_data['current_price']:,.2f}")
            print(f"   🕐 Tiempo: {EcuadorTimeUtils.format_time(storage_data['detection_time'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error almacenando zonas para {symbol}: {e}")
            print(f"❌ Error almacenando zonas para {symbol}: {e}")
            return False
    
    def _store_symbol_data(self, symbol: str, data: Dict) -> None:
        """Almacena datos de un símbolo en memoria y disco"""
        try:
            # Actualizar cache en memoria
            self._memory_cache[symbol] = data
            self._cache_timestamps[symbol] = EcuadorTimeUtils.now()
            
            # Guardar en disco
            self._save_to_disk()
            
        except Exception as e:
            logger.error(f"Error almacenando datos para {symbol}: {e}")
            raise
    
    def get_previous_zones(self, symbol: str) -> Optional[Dict]:
        """
        🏛️ OBTIENE ZONAS ANTERIORES PARA COMPARACIÓN
        Returns: Datos de zonas previas o None si no existen
        """
        try:
            # Verificar cache en memoria
            if symbol in self._memory_cache:
                cache_time = self._cache_timestamps.get(symbol)
                if cache_time and (EcuadorTimeUtils.now() - cache_time).total_seconds() < (self.cache_ttl_minutes * 60):
                    print(f"📋 Usando cache para {symbol}")
                    return self._memory_cache[symbol].copy()
            
            # Si no está en cache o está expirado, cargar desde disco
            if self.zones_file.exists():
                with open(self.zones_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if symbol in data:
                    # Convertir timestamps
                    symbol_data = data[symbol].copy()
                    if 'detection_time' in symbol_data:
                        symbol_data['detection_time'] = datetime.fromisoformat(symbol_data['detection_time'])
                    
                    # Actualizar cache
                    self._memory_cache[symbol] = symbol_data
                    self._cache_timestamps[symbol] = EcuadorTimeUtils.now()
                    
                    print(f"💾 Datos cargados desde disco para {symbol}")
                    return symbol_data
            
            print(f"📝 No hay datos previos para {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo zonas previas para {symbol}: {e}")
            print(f"❌ Error obteniendo datos para {symbol}: {e}")
            return None
    
    def compare_with_previous(self, symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
        """
        ⚔️ COMPARA ZONAS ACTUALES CON ANTERIORES USANDO DATOS REALES
        Returns: Diccionario con comparación detallada
        """
        try:
            print(f"\\n🎯 COMPARANDO ZONAS REALES PARA {symbol}")
            print("-" * 40)
            
            # Obtener zonas anteriores
            previous_data = self.get_previous_zones(symbol)
            
            # Detectar zonas actuales con datos reales
            current_success = self.store_zones_from_detector(symbol, timeframe)
            
            if not current_success:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'Failed to detect current zones'
                }
            
            # Obtener datos actuales
            current_data = self._memory_cache.get(symbol)
            
            if not current_data:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'No current data available'
                }
            
            # Realizar comparación
            comparison = self._perform_zone_comparison(previous_data, current_data)
            
            print(f"🎯 COMPARACIÓN COMPLETADA:")
            print(f"   📊 Zonas anteriores: {comparison['previous_total']}")
            print(f"   📊 Zonas actuales: {comparison['current_total']}")
            print(f"   🆕 Nuevas zonas: {comparison['new_zones_count']}")
            print(f"   ❌ Zonas removidas: {comparison['removed_zones_count']}")
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparando zonas para {symbol}: {e}")
            return {
                'symbol': symbol,
                'success': False,
                'error': str(e)
            }
    
    def _perform_zone_comparison(self, previous_data: Optional[Dict], current_data: Dict) -> Dict[str, Any]:
        """Realiza comparación detallada entre zonas"""
        comparison = {
            'symbol': current_data['symbol'],
            'timeframe': current_data['timeframe'],
            'comparison_time': EcuadorTimeUtils.now(),
            'success': True,
            'previous_total': 0,
            'current_total': current_data['total_zones'],
            'new_zones_count': 0,
            'removed_zones_count': 0,
            'new_zones': [],
            'removed_zones': [],
            'price_change': 0,
            'has_new_zones': False
        }
        
        if not previous_data:
            # Primera detección - todas las zonas son nuevas
            comparison['new_zones_count'] = current_data['total_zones']
            comparison['new_zones'] = current_data['supply_zones'] + current_data['demand_zones']
            comparison['has_new_zones'] = comparison['new_zones_count'] > 0
            
            print(f"   🆕 Primera detección - {comparison['new_zones_count']} zonas nuevas")
            return comparison
        
        # Comparación con datos anteriores
        comparison['previous_total'] = previous_data.get('total_zones', 0)
        
        # Calcular cambio de precio
        prev_price = previous_data.get('current_price', 0)
        curr_price = current_data.get('current_price', 0)
        if prev_price > 0:
            comparison['price_change'] = ((curr_price - prev_price) / prev_price) * 100
        
        # Comparar zonas por POI (Point of Interest)
        previous_pois = set()
        current_pois = set()
        
        # Extraer POIs anteriores
        for zone in previous_data.get('supply_zones', []) + previous_data.get('demand_zones', []):
            if 'poi' in zone:
                previous_pois.add(round(zone['poi'], 2))
        
        # Extraer POIs actuales y identificar nuevas
        current_zones_list = current_data.get('supply_zones', []) + current_data.get('demand_zones', [])
        for zone in current_zones_list:
            if 'poi' in zone:
                poi = round(zone['poi'], 2)
                current_pois.add(poi)
                
                # Si el POI no existía antes, es una zona nueva
                if poi not in previous_pois:
                    comparison['new_zones'].append(zone)
        
        # Identificar zonas removidas
        for zone in previous_data.get('supply_zones', []) + previous_data.get('demand_zones', []):
            if 'poi' in zone:
                poi = round(zone['poi'], 2)
                if poi not in current_pois:
                    comparison['removed_zones'].append(zone)
        
        comparison['new_zones_count'] = len(comparison['new_zones'])
        comparison['removed_zones_count'] = len(comparison['removed_zones'])
        comparison['has_new_zones'] = comparison['new_zones_count'] > 0
        
        return comparison
    
    def _save_to_disk(self) -> None:
        """Guarda datos en disco con backup"""
        try:
            # Crear backup si existe archivo anterior
            if self.zones_file.exists():
                backup_name = f"zones_backup_{EcuadorTimeUtils.now().strftime('%Y%m%d_%H%M%S')}.json"
                backup_path = self.backup_dir / backup_name
                
                import shutil
                shutil.copy2(self.zones_file, backup_path)
            
            # Preparar datos para JSON (convertir datetime a string)
            json_data = {}
            for symbol, data in self._memory_cache.items():
                json_data[symbol] = data.copy()
                if 'detection_time' in json_data[symbol]:
                    json_data[symbol]['detection_time'] = json_data[symbol]['detection_time'].isoformat()
            
            # Guardar datos
            with open(self.zones_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            # Actualizar metadata
            metadata = {
                'last_update': EcuadorTimeUtils.now().isoformat(),
                'symbols_count': len(self._memory_cache),
                'total_zones': sum(data.get('total_zones', 0) for data in self._memory_cache.values())
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error guardando en disco: {e}")
            raise
    
    def cleanup_old_data(self, max_age_hours: Optional[int] = None) -> int:
        """
        🧹 LIMPIEZA ÉPICA DE DATOS ANTIGUOS
        Returns: Número de registros eliminados
        """
        if max_age_hours is None:
            max_age_hours = self.max_age_hours
        
        cutoff_time = EcuadorTimeUtils.now() - timedelta(hours=max_age_hours)
        removed_count = 0
        
        try:
            symbols_to_remove = []
            
            for symbol, data in self._memory_cache.items():
                detection_time = data.get('detection_time')
                if detection_time and detection_time < cutoff_time:
                    symbols_to_remove.append(symbol)
            
            for symbol in symbols_to_remove:
                del self._memory_cache[symbol]
                if symbol in self._cache_timestamps:
                    del self._cache_timestamps[symbol]
                removed_count += 1
            
            if removed_count > 0:
                self._save_to_disk()
                print(f"🧹 Limpieza completada: {removed_count} registros antiguos eliminados")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error en limpieza de datos: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del almacenamiento"""
        try:
            total_zones = sum(data.get('total_zones', 0) for data in self._memory_cache.values())
            
            stats = {
                'symbols_stored': len(self._memory_cache),
                'total_zones': total_zones,
                'storage_dir': str(self.storage_dir),
                'cache_size': len(self._memory_cache),
                'last_cleanup': None,
                'disk_usage_mb': 0
            }
            
            # Calcular uso de disco
            if self.zones_file.exists():
                stats['disk_usage_mb'] = round(self.zones_file.stat().st_size / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def clear_all_data(self) -> bool:
        """⚠️ LIMPIA TODOS LOS DATOS - USAR CON PRECAUCIÓN"""
        try:
            self._memory_cache.clear()
            self._cache_timestamps.clear()
            
            if self.zones_file.exists():
                self.zones_file.unlink()
            
            if self.metadata_file.exists():
                self.metadata_file.unlink()
            
            print("🧹 TODOS LOS DATOS ELIMINADOS")
            return True
            
        except Exception as e:
            logger.error(f"Error limpiando datos: {e}")
            return False


def test_zone_storage_with_real_data():
    """
    🔥 TEST ÉPICO CON DATOS REALES DE BINANCE 🔥
    """
    print("🔥⚔️🏛️ TESTING ZONE STORAGE CON DATOS REALES 🏛️⚔️🔥")
    print("=" * 70)
    
    # Verificar credenciales
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ CREDENCIALES DE BINANCE NO ENCONTRADAS!")
        return False
    
    # Crear storage
    storage = ZoneStorage("data/test_zone_storage")
    
    # Test con BTCUSDT real
    symbol = "BTCUSDT"
    timeframe = "1h"
    
    print(f"\\n🎯 TESTING CON {symbol} - DATOS REALES")
    print("-" * 50)
    
    # Primera detección
    print("1️⃣ PRIMERA DETECCIÓN:")
    success1 = storage.store_zones_from_detector(symbol, timeframe)
    
    if not success1:
        print("❌ Fallo en primera detección")
        return False
    
    # Esperar un momento y hacer segunda detección
    print("\\n2️⃣ SEGUNDA DETECCIÓN (para comparar):")
    import time
    time.sleep(2)  # Pequeña pausa
    
    comparison = storage.compare_with_previous(symbol, timeframe)
    
    if comparison['success']:
        print(f"\\n🎯 RESULTADOS DE COMPARACIÓN:")
        print(f"   📊 Zonas anteriores: {comparison['previous_total']}")
        print(f"   📊 Zonas actuales: {comparison['current_total']}")
        print(f"   🆕 Nuevas zonas: {comparison['new_zones_count']}")
        print(f"   💰 Cambio de precio: {comparison['price_change']:+.2f}%")
        print(f"   🕐 Tiempo: {EcuadorTimeUtils.format_time(comparison['comparison_time'])}")
        
        if comparison['has_new_zones']:
            print(f"\\n🚨 ¡NUEVAS ZONAS DETECTADAS!")
            for i, zone in enumerate(comparison['new_zones'][:2], 1):
                print(f"   {i}. {zone.get('name', 'Unknown')} - POI: ${zone.get('poi', 0):,.2f}")
    
    # Estadísticas
    stats = storage.get_storage_stats()
    print(f"\\n📊 ESTADÍSTICAS DEL STORAGE:")
    print(f"   📁 Símbolos almacenados: {stats['symbols_stored']}")
    print(f"   🎯 Total zonas: {stats['total_zones']}")
    print(f"   💾 Uso de disco: {stats['disk_usage_mb']} MB")
    
    print("\\n🏆 TEST CON DATOS REALES COMPLETADO! 🏆")
    return True


if __name__ == "__main__":
    test_zone_storage_with_real_data()