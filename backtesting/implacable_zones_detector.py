#!/usr/bin/env python3
"""
🔥 IMPLACABLE ZONES DETECTOR - PRECISIÓN ABSOLUTA 🔥
Detector que debe coincidir EXACTAMENTE con TradingView
Created by KRATOS - IMPLACABLE PRECISION WARRIOR
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Any, Optional, Tuple

# Our EPIC SMC Components
from core.swing_detector import SwingDetector
from models.zone import Zone, ZoneType
from models.swing import SwingType
from bnb.binance import RobotBinance
from config.config_manager import get_config

# Setup minimal logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class ImplacableZonesDetector:
    """
    🏛️ IMPLACABLE ZONES DETECTOR - PRECISIÓN ABSOLUTA
    Debe coincidir EXACTAMENTE con TradingView o FALLAR
    """
    
    def __init__(self, symbol: str = "BTCUSDT", timeframe: str = "1h"):
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        
        # Initialize components
        self.swing_detector = SwingDetector(symbol)
        
        # Data storage
        self.market_data: Optional[pd.DataFrame] = None
        self.swings: List = []
        self.implacable_zones: Dict = {}
        
        # 🎯 SISTEMA DE ZONAS PERSISTENTES
        self.persistent_zones: Dict = {
            'supply': [],  # Zonas SUPPLY activas
            'demand': []   # Zonas DEMAND activas
        }
        self.zone_id_counter = 0  # Para IDs únicos
        
    
    def fetch_extended_data(self, limit: int = 1000) -> bool:
        """Fetch EXTENDED data to catch all significant levels"""
        try:
            
            robot = RobotBinance(self.symbol, self.timeframe)
            self.market_data = robot.candlestick(limit=limit)
            
            if self.market_data.empty:
                raise ValueError(f"No data received for {self.symbol}")
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL in fetching extended data: {e}")
            return False
    
    def detect_all_swings(self) -> bool:
        """Detect ALL possible swings with maximum sensitivity"""
        try:
            
            start_time = time.time()
            self.swings = self.swing_detector.detect_swings(self.market_data)
            detection_time = time.time() - start_time
            
            if not self.swings:
                print("⚠️ No swings detected")
                return False
            
            
            # Analyze swing distribution
            swing_prices = [s.price for s in self.swings]
            swing_prices.sort()
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL in swing detection: {e}")
            return False
    
    def extract_implacable_zones(self) -> bool:
        """Extract zones with IMPLACABLE precision matching TradingView"""
        try:            
            if not self.swings:
                print("⚠️ No swings available")
                return False
            
            current_price = float(self.market_data['close'].iloc[-1])
            
            # Get ALL swing data with detailed analysis
            swing_analysis = []
            for swing in self.swings:
                distance_pct = ((swing.price - current_price) / current_price) * 100
                
                # Analyze market context around this swing
                swing_time = swing.timestamp
                
                # Find the candle data around this swing
                swing_candle_data = None
                for i, (timestamp, row) in enumerate(self.market_data.iterrows()):
                    if abs((timestamp - swing_time).total_seconds()) < 3600:  # Within 1 hour
                        swing_candle_data = {
                            'index': i,
                            'timestamp': timestamp,
                            'open': row['open'],
                            'high': row['high'],
                            'low': row['low'],
                            'close': row['close'],
                            'volume': row['volume']
                        }
                        break
                
                swing_info = {
                    'price': float(swing.price),
                    'timestamp': swing.timestamp,
                    'swing_type': swing.swing_type,
                    'strength': swing.strength,
                    'volume': getattr(swing, 'volume', 0),
                    'distance_pct': distance_pct,
                    'candle_data': swing_candle_data
                }
                swing_analysis.append(swing_info)
            
            # Sort by price for systematic analysis
            swing_analysis.sort(key=lambda x: x['price'])
            
            # IMPLACABLE ZONE IDENTIFICATION
            # DYNAMIC zone calculation based on current price and market structure
            current_price = self.market_data['close'].iloc[-1]
            price_high = self.market_data['high'].max()
            price_low = self.market_data['low'].min()
            price_range = price_high - price_low
            
            # Calculate dynamic zones based on RECENT market structure - FOCUS ON LATEST ZONES
            target_zones = {
                'recent_supply_close': {
                    'min': current_price * 1.001,  # Very close supply zones (0.1% above)
                    'max': current_price * 1.03,   # Up to 3% above current price
                    'type': 'SUPPLY'
                },
                'recent_supply_medium': {
                    'min': current_price * 1.03,   # Medium supply zones (3-8% above)
                    'max': current_price * 1.08, 
                    'type': 'SUPPLY'
                },
                'recent_supply_high': {
                    'min': current_price * 1.08,   # Higher supply zones (8-15% above)
                    'max': current_price * 1.15, 
                    'type': 'SUPPLY'
                },
                'recent_demand_close': {
                    'min': current_price * 0.97,   # Close demand zones (3% below)
                    'max': current_price * 0.999,  # Just below current price
                    'type': 'DEMAND'
                },
                'recent_demand_low': {
                    'min': current_price * 0.85,   # Lower demand zones (15% below)
                    'max': current_price * 0.97, 
                    'type': 'DEMAND'
                }
            }
            
            detected_zones = []
            
            # Find swings in each target zone
            for zone_name, zone_config in target_zones.items():
                zone_swings = []
                
                for swing in swing_analysis:
                    if zone_config['min'] <= swing['price'] <= zone_config['max']:
                        zone_swings.append(swing)
                
                if zone_swings:
                    # Find the STRONGEST swing in this zone (más estable)
                    # Prioritize by STRENGTH first, then recency for stability
                    best_swing = max(zone_swings, key=lambda s: (s['strength'], s['timestamp']))
                    
                    # Calculate zone boundaries
                    zone_height = (zone_config['max'] - zone_config['min']) * 0.3  # 30% of target range
                    
                    if zone_config['type'] == 'SUPPLY':
                        zone_top = best_swing['price'] + (zone_height * 0.3)
                        zone_bottom = best_swing['price'] - (zone_height * 0.7)
                    else:  # DEMAND
                        zone_top = best_swing['price'] + (zone_height * 0.7)
                        zone_bottom = best_swing['price'] - (zone_height * 0.3)
                    
                    zone_data = {
                        'name': zone_name,
                        'type': zone_config['type'],
                        'poi': best_swing['price'],
                        'top': zone_top,
                        'bottom': zone_bottom,
                        'distance_pct': best_swing['distance_pct'],
                        'formation_date': best_swing['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        'strength': best_swing['strength'],
                        'volume': best_swing['volume'],
                        'swing_count_in_zone': len(zone_swings)
                    }
                    
                    detected_zones.append(zone_data)
                    
                    # Silencioso
            
            # 🎯 USAR SISTEMA DE ZONAS PERSISTENTES UNIFICADO
            
            print(f"🔍 Detectadas {len(detected_zones)} zonas nuevas")
            
            # 1. Actualizar zonas persistentes con callback integrado
            callback = getattr(self, '_zone_callback', None)
            self.update_persistent_zones(detected_zones, current_price, callback)
            
            # 2. Obtener zonas persistentes para mostrar
            persistent_data = self.get_persistent_zones_for_display()
            
            print(f"📊 Zonas persistentes activas: {persistent_data['total_persistent_zones']}")
            
            # 3. Asignar a implacable_zones para compatibilidad
            self.implacable_zones = {
                'supply': persistent_data['supply'],
                'demand': persistent_data['demand'],
                'current_price': current_price,
                'extraction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_swings_analyzed': len(swing_analysis),
                'detection_method': 'persistent_zones_system',
                'total_persistent_zones': persistent_data['total_persistent_zones']
            }
        
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL in implacable zone extraction: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def display_epic_zones_table(self):
        """🏆⚔️ TABLA ÉPICA DE ZONAS - FORMATO SUPREMO ⚔️🏆"""
        try:
            if not self.implacable_zones:
                print("❌ No hay zonas para mostrar")
                return
            
            current_price = self.implacable_zones['current_price']
            
            # Combinar todas las zonas
            all_zones = []
            
            # Procesar zonas SUPPLY
            for zone in self.implacable_zones['supply']:
                zone_data = {
                    'symbol': self.symbol,
                    'zona': zone['type'],
                    'recomendacion': 'SELL',
                    'rango': f"${zone['bottom']:.2f} - ${zone['top']:.2f}",
                    'precio_actual': f"${current_price:.2f}",
                    'fecha_hora': self._convert_to_utc_minus_5(zone.get('first_detected', zone.get('formation_date', '')))
                }
                all_zones.append(zone_data)
            
            # Procesar zonas DEMAND
            for zone in self.implacable_zones['demand']:
                zone_data = {
                    'symbol': self.symbol,
                    'zona': zone['type'],
                    'recomendacion': 'BUY',
                    'rango': f"${zone['bottom']:.2f} - ${zone['top']:.2f}",
                    'precio_actual': f"${current_price:.2f}",
                    'fecha_hora': self._convert_to_utc_minus_5(zone.get('first_detected', zone.get('formation_date', '')))
                }
                all_zones.append(zone_data)
            
            # Ordenar por fecha (más recientes primero)
            all_zones.sort(key=lambda x: x['fecha_hora'], reverse=True)
            
            # Mostrar tabla épica
            print("\n🏆⚔️🏛️ TABLA SUPREMA DE ZONAS IMPLACABLES 🏛️⚔️🏆")
            print("═" * 100)
            print(f"🕐 Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC-5")
            print("═" * 100)
            print("SÍMBOLO   ZONA     RECOMENDACIÓN  RANGO                    PRECIO ACTUAL    FECHA HORA")
            print("─" * 100)
            
            for zone in all_zones:
                symbol = zone['symbol'][:8].ljust(8)
                zona = zone['zona'][:8].ljust(8)
                recom = zone['recomendacion'][:12].ljust(12)
                rango = zone['rango'][:22].ljust(22)
                precio = zone['precio_actual'][:14].ljust(14)
                fecha = zone['fecha_hora']
                
                # Color según recomendación
                if zone['recomendacion'] == 'BUY':
                    color = '\033[92m'  # Verde
                    reset = '\033[0m'
                elif zone['recomendacion'] == 'SELL':
                    color = '\033[91m'  # Rojo
                    reset = '\033[0m'
                else:
                    color = ''
                    reset = ''
                
                print(f"{color}{symbol} {zona} {recom}  {rango} {precio} {fecha}{reset}")
            
            print("─" * 100)
            print("═" * 100)
            
        except Exception as e:
            print(f"❌ Error mostrando tabla épica: {e}")
    
    def _convert_to_utc_minus_5(self, date_str: str) -> str:
        """🕐 CONVIERTE FECHA A UTC-5 FORMATO YYYY-MM-DD HH:MM"""
        try:
            # Parsear fecha original
            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            
            # Convertir a UTC-5 (restar 5 horas)
            dt_utc_minus_5 = dt - timedelta(hours=5)
            
            # Formatear como YYYY-MM-DD HH:MM
            return dt_utc_minus_5.strftime('%Y-%m-%d %H:%M')
            
        except Exception as e:
            print(f"❌ Error convirtiendo fecha: {e}")
            return date_str

    def export_implacable_json(self) -> Dict:
        """Export implacable zones as clean JSON"""
        try:
            if not self.implacable_zones:
                return {}
            
            export_data = {
                'symbol': self.symbol,
                'timeframe': self.timeframe,
                'current_price': self.implacable_zones['current_price'],
                'extraction_timestamp': self.implacable_zones['extraction_time'],
                'detection_method': self.implacable_zones['detection_method'],
                'supply_zones': [],
                'demand_zones': []
            }
            
            # Process supply zones
            for zone in self.implacable_zones['supply']:
                clean_zone = {
                    'name': zone.get('name', f"supply_zone_{zone.get('id', 'unknown')}"),
                    'poi': round(zone['poi'], 2),
                    'top': round(zone['top'], 2),
                    'bottom': round(zone['bottom'], 2),
                    'distance_percentage': f"{zone['distance_pct']:+.2f}%",
                    'formation_date': zone['formation_date'],
                    'strength': zone['strength'],
                    'volume': int(zone.get('volume', 0)),
                    'swings_in_zone': zone.get('swing_count_in_zone', zone.get('swing_count', 1))
                }
                export_data['supply_zones'].append(clean_zone)
            
            # Process demand zones
            for zone in self.implacable_zones['demand']:
                clean_zone = {
                    'name': zone.get('name', f"demand_zone_{zone.get('id', 'unknown')}"),
                    'poi': round(zone['poi'], 2),
                    'top': round(zone['top'], 2),
                    'bottom': round(zone['bottom'], 2),
                    'distance_percentage': f"{zone['distance_pct']:+.2f}%",
                    'formation_date': zone['formation_date'],
                    'strength': zone['strength'],
                    'volume': int(zone.get('volume', 0)),
                    'swings_in_zone': zone.get('swing_count_in_zone', zone.get('swing_count', 1))
                }
                export_data['demand_zones'].append(clean_zone)
            
            return export_data
            
        except Exception as e:
            print(f"❌ FAIL in exporting JSON: {e}")
            return {}
    
    def run_implacable_detection(self) -> bool:
        """Run complete IMPLACABLE detection"""
        try:
            
            start_time = time.time()
            
            # Fetch extended data
            if not self.fetch_extended_data():
                return False
            
            # Detect all swings
            if not self.detect_all_swings():
                return False
            
            # Extract implacable zones
            if not self.extract_implacable_zones():
                return False
            
            total_time = time.time() - start_time
            
            # ¡MOSTRAR TABLA ÉPICA!
            self.display_epic_zones_table()
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in implacable detection: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # 🎯 SISTEMA DE ZONAS PERSISTENTES
    
    def is_zone_invalidated(self, zone: Dict, current_price: float) -> bool:
        """🔍 Verifica si una zona ha sido invalidada por el precio"""
        try:
            if zone['type'] == 'DEMAND':
                # Zona DEMAND invalidada si precio rompe por debajo
                return current_price < zone['bottom']
            elif zone['type'] == 'SUPPLY':
                # Zona SUPPLY invalidada si precio rompe por encima  
                return current_price > zone['top']
            return False
        except Exception as e:
            print(f"❌ Error checking zone invalidation: {e}")
            return True  # Si hay error, considerar invalidada por seguridad
    
    def add_persistent_zone(self, zone_data: Dict, current_price: float) -> bool:
        """🎯 Agrega una nueva zona al sistema persistente"""
        try:
            # Verificar si ya existe una zona similar
            zone_type = zone_data['type'].lower()
            existing_zones = self.persistent_zones[zone_type]
            
            # Tolerancia para considerar zonas similares (2% del precio)
            tolerance = current_price * 0.02
            
            for existing_zone in existing_zones:
                poi_diff = abs(existing_zone['poi'] - zone_data['poi'])
                if poi_diff < tolerance:
                    # Zona similar ya existe, no agregar duplicado
                    return False
            
            # 🎯 USAR FECHA REAL DE FORMACIÓN, NO DATETIME.NOW()
            formation_timestamp = zone_data.get('formation_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # Crear nueva zona persistente
            new_zone = {
                'id': self.zone_id_counter,
                'name': zone_data.get('name', f"{zone_data['type'].lower()}_zone_{self.zone_id_counter}"),  # 🎯 AGREGAR NAME
                'type': zone_data['type'],
                'poi': zone_data['poi'],
                'top': zone_data['top'],
                'bottom': zone_data['bottom'],
                'strength': zone_data['strength'],
                'first_detected': formation_timestamp,  # 🎯 FECHA REAL DEL SWING
                'formation_date': formation_timestamp,  # Misma fecha para consistencia
                'distance_pct': zone_data['distance_pct'],
                'volume': zone_data['volume'],
                'swing_count_in_zone': zone_data.get('swing_count_in_zone', 1),  # 🎯 CORREGIR NOMBRE
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Agregar a zonas persistentes
            self.persistent_zones[zone_type].append(new_zone)
            self.zone_id_counter += 1
            
            print(f"✅ Nueva zona {zone_data['type']}: POI=${zone_data['poi']:,.2f} formada en {formation_timestamp}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding persistent zone: {e}")
            return False
    
    def cleanup_invalidated_zones(self, current_price: float) -> int:
        """🧹 Limpia zonas invalidadas y retorna cuántas se eliminaron"""
        try:
            removed_count = 0
            
            for zone_type in ['supply', 'demand']:
                valid_zones = []
                
                for zone in self.persistent_zones[zone_type]:
                    if not self.is_zone_invalidated(zone, current_price):
                        valid_zones.append(zone)
                    else:
                        removed_count += 1
                        print(f"🗑️ Zona {zone['type']} invalidada: POI=${zone['poi']:,.2f}")
                
                self.persistent_zones[zone_type] = valid_zones
            
            return removed_count
            
        except Exception as e:
            print(f"❌ Error cleaning invalidated zones: {e}")
            return 0
    
    def update_persistent_zones(self, newly_detected_zones: List[Dict], current_price: float, callback=None):
        """🔄 Actualiza el sistema de zonas persistentes"""
        try:
            # 1. Limpiar zonas invalidadas
            removed = self.cleanup_invalidated_zones(current_price)
            
            # 2. Agregar nuevas zonas detectadas
            added_zones = []
            for zone in newly_detected_zones:
                if self.add_persistent_zone(zone, current_price):
                    added_zones.append(zone)
            
            # 3. Actualizar distancias de zonas existentes
            self.update_zone_distances(current_price)
            
            # 4. 🎯 LLAMAR CALLBACK SOLO PARA ZONAS REALMENTE NUEVAS
            if callback and added_zones:
                for new_zone in added_zones:
                    # Obtener la zona persistente completa (con fecha real)
                    zone_type = new_zone['type'].lower()
                    persistent_zone = None
                    
                    # Buscar la zona recién agregada
                    for pz in self.persistent_zones[zone_type]:
                        if abs(pz['poi'] - new_zone['poi']) < current_price * 0.01:
                            persistent_zone = pz
                            break
                    
                    if persistent_zone:
                        # 🎯 CALLBACK CON ZONA VÁLIDA Y FECHA REAL
                        callback(self.symbol, persistent_zone)
            
        except Exception as e:
            print(f"❌ Error updating persistent zones: {e}")
    
    def update_zone_distances(self, current_price: float):
        """📏 Actualiza las distancias de todas las zonas persistentes"""
        try:
            for zone_type in ['supply', 'demand']:
                for zone in self.persistent_zones[zone_type]:
                    distance_pct = ((zone['poi'] - current_price) / current_price) * 100
                    zone['distance_pct'] = distance_pct
        except Exception as e:
            print(f"❌ Error updating zone distances: {e}")
    
    def get_persistent_zones_for_display(self) -> Dict:
        """📊 Obtiene zonas persistentes formateadas para mostrar"""
        try:
            # Ordenar por distancia (más cercanas primero)
            supply_zones = sorted(
                self.persistent_zones['supply'], 
                key=lambda z: abs(z['distance_pct'])
            )[:3]  # Máximo 3 supply
            
            demand_zones = sorted(
                self.persistent_zones['demand'], 
                key=lambda z: abs(z['distance_pct'])
            )[:3]  # Máximo 3 demand
            
            return {
                'supply': supply_zones,
                'demand': demand_zones,
                'current_price': self.market_data.iloc[-1]['close'] if self.market_data is not None else 0,
                'total_persistent_zones': len(supply_zones) + len(demand_zones)
            }
            
        except Exception as e:
            print(f"❌ Error getting persistent zones: {e}")
            return {'supply': [], 'demand': [], 'current_price': 0, 'total_persistent_zones': 0}
    
    def set_zone_callback(self, callback):
        """🎯 Registra callback para zonas nuevas válidas"""
        self._zone_callback = callback