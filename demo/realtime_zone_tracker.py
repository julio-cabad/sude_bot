#!/usr/bin/env python3
"""
🔥⚔️ REAL-TIME ZONE TRACKER - ÚLTIMA ZONA DETECTOR ⚔️🔥
Detector enfocado en la ÚLTIMA zona que se forma en tiempo real
Created by FEROZ GUERRERO DEL CÓDIGO - VICTORY OR DEATH
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
from bnb.binance import RobotBinance
from config.config_manager import get_config

# Setup minimal logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class RealTimeZoneTracker:
    """
    🏛️ REAL-TIME ZONE TRACKER - ÚLTIMA ZONA HUNTER
    Se enfoca SOLO en detectar la ÚLTIMA zona que se forma
    """
    
    def __init__(self, symbol: str = "BTCUSDT", timeframe: str = "1h"):
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        
        print(f"🔥⚔️ REAL-TIME ZONE TRACKER FOR {self.symbol} ⚔️🔥")
        print("🎯 OBJETIVO: DETECTAR LA ÚLTIMA ZONA FORMADA")
        print("⚔️ ENFOQUE: TIEMPO REAL - NO HISTORIA")
        print("=" * 70)
        
        # Initialize components
        self.swing_detector = SwingDetector(symbol)
        
        # CONFIGURACIÓN OPTIMIZADA PARA TIEMPO REAL
        self.config = {
            'recent_candles_focus': 150,  # Más candles para mejor contexto
            'min_swing_strength': 2,      # Más sensible a swings
            'zone_formation_lookback': 30, # Mayor lookback para zonas
            'price_tolerance_pct': 0.2,   # Más sensible a zonas cercanas
        }
        
        # Data storage
        self.market_data: Optional[pd.DataFrame] = None
        self.recent_swings: List = []
        self.last_detected_zone: Optional[Dict] = None
        self.zone_formation_history: List = []
        
        print(f"✅ Real-Time Zone Tracker initialized")
        print(f"   📊 Focus: Last {self.config['recent_candles_focus']} candles")
        print(f"   🎯 Lookback: {self.config['zone_formation_lookback']} candles for zone formation")
    
    def fetch_recent_data(self, limit: int = 200) -> bool:
        """Fetch RECENT data focused on latest market action"""
        try:
            print(f"\\n📡 FETCHING RECENT {self.symbol} DATA...")
            print("-" * 50)
            
            robot = RobotBinance(self.symbol, self.timeframe)
            self.market_data = robot.candlestick(limit=limit)
            
            if self.market_data.empty:
                raise ValueError(f"No data received for {self.symbol}")
            
            # Focus on RECENT data only
            recent_focus = self.config['recent_candles_focus']
            if len(self.market_data) > recent_focus:
                self.market_data = self.market_data.tail(recent_focus).copy()
            
            current_price = self.market_data['close'].iloc[-1]
            
            print(f"✅ SUCCESS! Focused on {len(self.market_data)} recent candles")
            print(f"📅 Recent range: {self.market_data.index[0]} to {self.market_data.index[-1]}")
            print(f"💰 Recent price range: ${self.market_data['low'].min():,.2f} - ${self.market_data['high'].max():,.2f}")
            print(f"📈 Current price: ${current_price:,.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL in fetching recent data: {e}")
            return False
    
    def detect_recent_swings(self) -> bool:
        """Detect swings in RECENT data only"""
        try:
            print(f"\\n⚔️ DETECTING RECENT SWINGS...")
            print("-" * 50)
            
            start_time = time.time()
            
            # Detect all swings first
            all_swings = self.swing_detector.detect_swings(self.market_data)
            
            if not all_swings:
                print("⚠️ No swings detected in recent data")
                return False
            
            # Filter for SIGNIFICANT recent swings
            min_strength = self.config['min_swing_strength']
            self.recent_swings = [
                swing for swing in all_swings 
                if swing.strength >= min_strength
            ]
            
            # Sort by timestamp (most recent first)
            self.recent_swings.sort(key=lambda s: s.timestamp, reverse=True)
            
            detection_time = time.time() - start_time
            
            print(f"🎯 RECENT SWING DETECTION COMPLETE!")
            print(f"   ⏱️  Detection time: {detection_time:.3f}s")
            print(f"   📊 Total swings found: {len(all_swings)}")
            print(f"   🎯 Significant recent swings: {len(self.recent_swings)}")
            
            if self.recent_swings:
                latest_swing = self.recent_swings[0]
                print(f"   🔥 LATEST SWING: {latest_swing.swing_type.name} at ${latest_swing.price:,.2f}")
                print(f"      📅 Time: {latest_swing.timestamp}")
                print(f"      💪 Strength: {latest_swing.strength}")
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL in recent swing detection: {e}")
            return False
    
    def detect_all_existing_zones(self) -> List[Dict]:
        """
        �️ EDETECTA TODAS LAS ZONAS EXISTENTES EN LOS DATOS RECIENTES
        Esto nos da el contexto completo de zonas ya formadas
        """
        try:
            print(f"\\n🏛️ DETECTING ALL EXISTING ZONES...")
            print("-" * 50)
            
            if not self.recent_swings:
                print("⚠️ No recent swings available")
                return []
            
            current_price = float(self.market_data['close'].iloc[-1])
            current_time = self.market_data.index[-1]
            
            all_zones = []
            
            # Analizar TODOS los swings significativos, no solo el último
            print(f"🎯 ANALYZING ALL {len(self.recent_swings)} SIGNIFICANT SWINGS:")
            
            for i, swing in enumerate(self.recent_swings):
                print(f"   Swing {i+1}: {swing.swing_type.name} at ${swing.price:,.2f} (Strength: {swing.strength})")
                
                # Verificar si este swing puede formar una zona válida
                zone_data = self._analyze_zone_formation(swing, current_price, current_time)
                
                if zone_data:
                    # Verificar que no sea duplicada con zonas ya encontradas
                    is_duplicate = False
                    for existing_zone in all_zones:
                        price_diff_pct = abs((zone_data['poi'] - existing_zone['poi']) / existing_zone['poi']) * 100
                        if (price_diff_pct < 1.0 and zone_data['type'] == existing_zone['type']):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        all_zones.append(zone_data)
                        print(f"      ✅ VALID ZONE: {zone_data['type']} at ${zone_data['poi']:,.2f}")
                    else:
                        print(f"      ⚠️ Duplicate zone, skipping")
                else:
                    print(f"      ❌ No valid zone formed")
            
            # Ordenar zonas por tiempo de formación (más reciente primero)
            all_zones.sort(key=lambda z: z['swing_time'], reverse=True)
            
            print(f"\\n🎯 TOTAL ZONES DETECTED: {len(all_zones)}")
            for i, zone in enumerate(all_zones):
                emoji = "🔺" if zone['type'] == 'SUPPLY' else "🔻"
                
                # Convertir timestamp a UTC-5 (Ecuador)
                from models.zone_alert import utc_to_ecuador, format_ecuador_time
                ecuador_time = utc_to_ecuador(zone['swing_time'])
                formatted_time = ecuador_time.strftime("%Y-%m-%d %H:%M ECT")
                
                print(f"   {i+1}. {emoji} {zone['type']} at ${zone['poi']:.3f}")
                print(f"      📊 Rango: ${zone['bottom']:.3f} - ${zone['top']:.3f}")
                print(f"      📅 Formación: {formatted_time}")
                print(f"      ⏰ Hace: {zone['formation_candles_ago']} velas")
            
            return all_zones
            
        except Exception as e:
            print(f"❌ FAIL in detecting all existing zones: {e}")
            import traceback
            traceback.print_exc()
            return []

    def detect_latest_zone_formation(self) -> Optional[Dict]:
        """
        🎯 DETECTA LA FORMACIÓN DE LA ÚLTIMA ZONA CON CONTEXTO COMPLETO
        Primero detecta todas las zonas existentes, luego identifica la más nueva
        """
        try:
            print(f"\\n🏛️ DETECTING LATEST ZONE FORMATION WITH FULL CONTEXT...")
            print("-" * 50)
            
            # Primero, detectar TODAS las zonas existentes
            all_existing_zones = self.detect_all_existing_zones()
            
            if not all_existing_zones:
                print("ℹ️ No zones detected in recent data")
                return None
            
            # La zona más reciente es la primera en la lista (ordenada por tiempo)
            latest_zone = all_existing_zones[0]
            
            # Verificar si esta zona es NUEVA comparada con nuestro historial
            if self._is_new_zone(latest_zone):
                print(f"\\n🚨 NEW ZONE FORMATION DETECTED!")
                print(f"   Type: {latest_zone['type']}")
                print(f"   POI: ${latest_zone['poi']:,.2f}")
                print(f"   Range: ${latest_zone['bottom']:,.2f} - ${latest_zone['top']:,.2f}")
                print(f"   Distance from current: {latest_zone['distance_pct']:+.2f}%")
                
                # IMPORTANTE: Actualizar historial con TODAS las zonas detectadas
                # Esto asegura que tengamos contexto completo
                for zone in reversed(all_existing_zones):  # Añadir en orden cronológico
                    if not any(abs(zone['poi'] - existing['poi']) < zone['poi'] * 0.01 
                             for existing in self.zone_formation_history):
                        self.zone_formation_history.append(zone)
                
                self.last_detected_zone = latest_zone
                return latest_zone
            else:
                print(f"\\nℹ️ Latest zone already in our records")
                
                # Aún así, actualizar nuestro historial con zonas que no tengamos
                new_zones_added = 0
                for zone in reversed(all_existing_zones):
                    if not any(abs(zone['poi'] - existing['poi']) < zone['poi'] * 0.01 
                             for existing in self.zone_formation_history):
                        self.zone_formation_history.append(zone)
                        new_zones_added += 1
                
                if new_zones_added > 0:
                    print(f"   📊 Added {new_zones_added} existing zones to our records")
                
                return None
            
        except Exception as e:
            print(f"❌ FAIL in latest zone formation detection: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _analyze_zone_formation(self, swing, current_price: float, current_time) -> Optional[Dict]:
        """
        ⚔️ ANALIZA SI UN SWING FORMA UNA ZONA VÁLIDA
        """
        try:
            # Calcular ATR para el ancho de zona
            atr_period = 14
            if len(self.market_data) >= atr_period:
                high_low = self.market_data['high'] - self.market_data['low']
                high_close = abs(self.market_data['high'] - self.market_data['close'].shift(1))
                low_close = abs(self.market_data['low'] - self.market_data['close'].shift(1))
                
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = true_range.rolling(window=atr_period).mean().iloc[-1]
            else:
                # Fallback ATR calculation
                atr = (self.market_data['high'] - self.market_data['low']).mean()
            
            # Verificar que el swing sea lo suficientemente significativo
            swing_distance_pct = abs((swing.price - current_price) / current_price) * 100
            
            # Relajar el criterio - debe estar al menos 0.2% alejado del precio actual
            # Esto permite detectar zonas más cercanas que son válidas
            if swing_distance_pct < 0.2:
                return None
            
            # Crear zona basada en el tipo de swing
            if swing.swing_type.name == 'HIGH':
                # Supply zone
                zone_top = swing.price
                zone_bottom = swing.price - (atr * 0.5)  # Zona más compacta
                zone_type = 'SUPPLY'
            else:
                # Demand zone
                zone_bottom = swing.price
                zone_top = swing.price + (atr * 0.5)  # Zona más compacta
                zone_type = 'DEMAND'
            
            poi = (zone_top + zone_bottom) / 2
            distance_pct = ((poi - current_price) / current_price) * 100
            
            # Verificar que la zona tenga un tamaño mínimo
            zone_height = zone_top - zone_bottom
            min_zone_height = current_price * 0.002  # Mínimo 0.2% del precio
            
            if zone_height < min_zone_height:
                return None
            
            zone_data = {
                'type': zone_type,
                'poi': poi,
                'top': zone_top,
                'bottom': zone_bottom,
                'swing_price': swing.price,
                'swing_time': swing.timestamp,
                'swing_strength': swing.strength,
                'formation_time': current_time,
                'distance_pct': distance_pct,
                'atr_used': atr,
                'zone_height': zone_height,
                'formation_candles_ago': self._calculate_candles_ago(swing.timestamp, current_time)
            }
            
            return zone_data
            
        except Exception as e:
            print(f"❌ Error in zone formation analysis: {e}")
            return None
    
    def _is_new_zone(self, zone_data: Dict) -> bool:
        """
        🎯 VERIFICA SI LA ZONA ES REALMENTE NUEVA
        """
        if not self.zone_formation_history:
            return True
        
        # Verificar contra las últimas 5 zonas detectadas
        recent_zones = self.zone_formation_history[-5:]
        
        for existing_zone in recent_zones:
            # Verificar si es muy similar en precio y tiempo
            price_diff_pct = abs((zone_data['poi'] - existing_zone['poi']) / existing_zone['poi']) * 100
            
            # Si la diferencia de precio es menor al 1% y es del mismo tipo, no es nueva
            if (price_diff_pct < 1.0 and 
                zone_data['type'] == existing_zone['type']):
                return False
        
        return True
    
    def _calculate_candles_ago(self, swing_time, current_time) -> int:
        """Calcula cuántas velas atrás se formó el swing"""
        try:
            # Encontrar el índice del swing time en los datos
            swing_idx = None
            current_idx = len(self.market_data) - 1
            
            for i, timestamp in enumerate(self.market_data.index):
                if abs((timestamp - swing_time).total_seconds()) < 3600:  # Within 1 hour
                    swing_idx = i
                    break
            
            if swing_idx is not None:
                return current_idx - swing_idx
            else:
                return 0
                
        except Exception:
            return 0
    
    def get_previous_zone_context(self, current_zone: Dict) -> Dict:
        """
        🧠 OBTIENE CONTEXTO DE LA ZONA ANTERIOR - CONOCIMIENTO ES PODER
        """
        context = {
            'has_previous': False,
            'previous_zone': None,
            'relationship': None,
            'market_structure': None,
            'tactical_advantage': None
        }
        
        if len(self.zone_formation_history) >= 2:
            # Zona anterior (la penúltima)
            previous_zone = self.zone_formation_history[-2]
            context['has_previous'] = True
            context['previous_zone'] = previous_zone
            
            # Analizar relación entre zonas
            current_poi = current_zone['poi']
            previous_poi = previous_zone['poi']
            
            # Determinar estructura de mercado
            if current_zone['type'] == 'SUPPLY' and previous_zone['type'] == 'DEMAND':
                if current_poi > previous_poi:
                    context['relationship'] = 'BULLISH_STRUCTURE'
                    context['market_structure'] = 'Estructura Alcista - Higher High después de Higher Low'
                    context['tactical_advantage'] = 'Buscar continuación alcista o rechazo en nueva resistencia'
                else:
                    context['relationship'] = 'BEARISH_REVERSAL'
                    context['market_structure'] = 'Posible Reversión Bajista - Lower High'
                    context['tactical_advantage'] = 'Cuidado: posible cambio de tendencia'
                    
            elif current_zone['type'] == 'DEMAND' and previous_zone['type'] == 'SUPPLY':
                if current_poi < previous_poi:
                    context['relationship'] = 'BEARISH_STRUCTURE'
                    context['market_structure'] = 'Estructura Bajista - Lower Low después de Lower High'
                    context['tactical_advantage'] = 'Buscar continuación bajista o rebote en nuevo soporte'
                else:
                    context['relationship'] = 'BULLISH_REVERSAL'
                    context['market_structure'] = 'Posible Reversión Alcista - Higher Low'
                    context['tactical_advantage'] = 'Oportunidad: posible cambio de tendencia alcista'
                    
            elif current_zone['type'] == previous_zone['type']:
                # Mismo tipo de zona
                if current_zone['type'] == 'SUPPLY':
                    if current_poi > previous_poi:
                        context['relationship'] = 'HIGHER_RESISTANCE'
                        context['market_structure'] = 'Resistencia más Alta - Presión alcista'
                        context['tactical_advantage'] = 'Momentum alcista fuerte, cuidado con el rechazo'
                    else:
                        context['relationship'] = 'LOWER_RESISTANCE'
                        context['market_structure'] = 'Resistencia más Baja - Debilidad alcista'
                        context['tactical_advantage'] = 'Posible debilidad, zona crítica'
                else:  # DEMAND
                    if current_poi > previous_poi:
                        context['relationship'] = 'HIGHER_SUPPORT'
                        context['market_structure'] = 'Soporte más Alto - Fortaleza alcista'
                        context['tactical_advantage'] = 'Estructura alcista sólida, buscar rebotes'
                    else:
                        context['relationship'] = 'LOWER_SUPPORT'
                        context['market_structure'] = 'Soporte más Bajo - Presión bajista'
                        context['tactical_advantage'] = 'Momentum bajista, zona crítica de soporte'
        
        return context

    def display_latest_zone_alert(self, zone_data: Dict) -> None:
        """
        🚨 MUESTRA ALERTA DE LA ÚLTIMA ZONA DETECTADA CON CONTEXTO ANTERIOR
        """
        zone_number = len(self.zone_formation_history)
        
        print(f"\\n🚨🔥 NUEVA ZONA #{zone_number} DETECTADA - ALERTA TIEMPO REAL 🔥🚨")
        print("=" * 80)
        
        current_price = self.market_data['close'].iloc[-1]
        
        # Emoji según el tipo
        emoji = "🔺" if zone_data['type'] == 'SUPPLY' else "🔻"
        
        print(f"{emoji} TIPO: {zone_data['type']} ZONE #{zone_number}")
        print(f"💰 POI (Point of Interest): ${zone_data['poi']:.3f}")
        print(f"📊 Rango de Zona: ${zone_data['bottom']:.3f} - ${zone_data['top']:.3f}")
        print(f"📈 Precio Actual: ${current_price:.3f}")
        print(f"📏 Distancia: {zone_data['distance_pct']:+.2f}% del precio actual")
        print(f"⏰ Formación: {zone_data['formation_candles_ago']} velas atrás")
        print(f"💪 Fuerza del Swing: {zone_data['swing_strength']}")
        
        # Convertir tiempo a UTC-5 (Ecuador) con formato mejorado
        from models.zone_alert import utc_to_ecuador
        ecuador_time = utc_to_ecuador(zone_data['swing_time'])
        formatted_time = ecuador_time.strftime("%Y-%m-%d %H:%M ECT")
        print(f"📅 Tiempo de Formación: {formatted_time}")
        
        print(f"🎯 ATR Usado: ${zone_data['atr_used']:.3f}")
        print(f"📊 Timeframe: {self.timeframe}")
        
        # 🧠 ANÁLISIS DE ZONA ANTERIOR - CONOCIMIENTO ES PODER
        context = self.get_previous_zone_context(zone_data)
        
        if context['has_previous']:
            prev_zone = context['previous_zone']
            prev_emoji = "🔺" if prev_zone['type'] == 'SUPPLY' else "🔻"
            
            print(f"\\n🧠 CONTEXTO DE ZONA ANTERIOR - CONOCIMIENTO TÁCTICO:")
            print("-" * 60)
            print(f"{prev_emoji} ZONA ANTERIOR: {prev_zone['type']} at ${prev_zone['poi']:.3f}")
            
            # Convertir tiempo anterior a UTC-5
            prev_ecuador_time = utc_to_ecuador(prev_zone['swing_time'])
            prev_formatted_time = prev_ecuador_time.strftime("%Y-%m-%d %H:%M ECT")
            print(f"   📅 Formada: {prev_formatted_time} ({prev_zone['formation_candles_ago']} velas atrás)")
            print(f"   📊 Rango: ${prev_zone['bottom']:.3f} - ${prev_zone['top']:.3f}")
            
            # Análisis de estructura de mercado
            print(f"\\n⚔️ ANÁLISIS DE ESTRUCTURA DE MERCADO:")
            print(f"   🎯 Relación: {context['relationship']}")
            print(f"   📈 Estructura: {context['market_structure']}")
            print(f"   🏛️ Ventaja Táctica: {context['tactical_advantage']}")
            
            # Cálculo de distancia entre zonas
            distance_between_zones = abs(zone_data['poi'] - prev_zone['poi'])
            distance_pct = (distance_between_zones / prev_zone['poi']) * 100
            print(f"   📏 Distancia entre zonas: ${distance_between_zones:.3f} ({distance_pct:.2f}%)")
            
        else:
            print(f"\\n🧠 CONTEXTO: Esta es la PRIMERA zona detectada en esta sesión")
        
        # Mostrar historial de zonas si hay más de una
        if len(self.zone_formation_history) > 1:
            print(f"\\n📋 HISTORIAL COMPLETO DE ZONAS:")
            print("-" * 60)
            for i, zone in enumerate(self.zone_formation_history[-5:], 1):  # Últimas 5
                zone_num = len(self.zone_formation_history) - 5 + i
                if zone_num > 0:
                    zone_emoji = "🔺" if zone['type'] == 'SUPPLY' else "🔻"
                    status = "🆕 NUEVA" if zone_num == zone_number else "📍"
                    
                    # Convertir tiempo a UTC-5 para historial
                    hist_ecuador_time = utc_to_ecuador(zone['swing_time'])
                    hist_formatted_time = hist_ecuador_time.strftime("%m-%d %H:%M")
                    
                    print(f"   {status} {zone_emoji} Zona #{zone_num}: {zone['type']} at ${zone['poi']:.3f}")
                    print(f"      📊 Rango: ${zone['bottom']:.3f} - ${zone['top']:.3f}")
                    print(f"      📅 {hist_formatted_time} ECT ({zone['formation_candles_ago']} velas atrás)")
        
        # Análisis de trading mejorado
        print(f"\\n📋 ANÁLISIS PARA TRADING:")
        print("-" * 60)
        if zone_data['type'] == 'SUPPLY':
            print(f"   🎯 Zona de RESISTENCIA potencial")
            print(f"   📈 Precio debe romper ${zone_data['top']:,.2f} para invalidar")
            print(f"   🔻 Posible rechazo cerca de ${zone_data['poi']:,.2f}")
            
            if context['has_previous'] and context['previous_zone']['type'] == 'DEMAND':
                prev_poi = context['previous_zone']['poi']
                range_size = zone_data['poi'] - prev_poi
                print(f"   📊 Rango desde último soporte: ${range_size:,.2f}")
                print(f"   🎯 Ratio Risk/Reward desde soporte anterior: {range_size/zone_data['atr_used']:.2f}")
                
        else:  # DEMAND
            print(f"   🎯 Zona de SOPORTE potencial")
            print(f"   📉 Precio debe romper ${zone_data['bottom']:,.2f} para invalidar")
            print(f"   🔺 Posible rebote cerca de ${zone_data['poi']:,.2f}")
            
            if context['has_previous'] and context['previous_zone']['type'] == 'SUPPLY':
                prev_poi = context['previous_zone']['poi']
                range_size = prev_poi - zone_data['poi']
                print(f"   📊 Rango desde última resistencia: ${range_size:,.2f}")
                print(f"   🎯 Ratio Risk/Reward desde resistencia anterior: {range_size/zone_data['atr_used']:.2f}")
        
        # Recomendaciones tácticas basadas en contexto
        if context['has_previous']:
            print(f"\\n⚔️ RECOMENDACIONES TÁCTICAS:")
            print("-" * 60)
            if context['relationship'] in ['BULLISH_STRUCTURE', 'BULLISH_REVERSAL']:
                print(f"   🔺 SESGO ALCISTA: Buscar oportunidades de compra en retrocesos")
                print(f"   🎯 Objetivo: Zona anterior como referencia")
            elif context['relationship'] in ['BEARISH_STRUCTURE', 'BEARISH_REVERSAL']:
                print(f"   🔻 SESGO BAJISTA: Buscar oportunidades de venta en rebotes")
                print(f"   🎯 Objetivo: Zona anterior como referencia")
            else:
                print(f"   ⚖️ MERCADO LATERAL: Operar entre zonas establecidas")
                print(f"   🎯 Estrategia: Range trading entre soportes y resistencias")
        
        print(f"\\n🔥 ALERTA #{zone_number} CON CONTEXTO COMPLETO GENERADA! 🔥")
        print("=" * 80)
    
    def run_realtime_detection(self) -> Optional[Dict]:
        """
        🎯 EJECUTA DETECCIÓN EN TIEMPO REAL
        """
        try:
            print(f"\\n🔥⚔️ STARTING REAL-TIME ZONE DETECTION ⚔️🔥")
            print("🎯 ENFOQUE: ÚLTIMA ZONA FORMADA")
            print("=" * 70)
            
            start_time = time.time()
            
            # Fetch recent data
            if not self.fetch_recent_data():
                return None
            
            # Detect recent swings
            if not self.detect_recent_swings():
                return None
            
            # Detect latest zone formation
            latest_zone = self.detect_latest_zone_formation()
            
            total_time = time.time() - start_time
            
            if latest_zone:
                self.display_latest_zone_alert(latest_zone)
                
                print(f"\\n🏆 REAL-TIME DETECTION SUCCESS! 🏆")
                print("=" * 70)
                print(f"⏱️  Total time: {total_time:.3f}s")
                print(f"📊 Recent candles analyzed: {len(self.market_data)}")
                print(f"⚔️ Recent swings found: {len(self.recent_swings)}")
                print(f"🎯 NEW ZONE DETECTED: {latest_zone['type']} at ${latest_zone['poi']:,.2f}")
                
                return latest_zone
            else:
                print(f"\\nℹ️ NO NEW ZONE FORMATION DETECTED")
                print("=" * 70)
                print(f"⏱️  Total time: {total_time:.3f}s")
                print(f"📊 Recent candles analyzed: {len(self.market_data)}")
                print(f"⚔️ Recent swings found: {len(self.recent_swings)}")
                print(f"🎯 Status: Monitoring for new formations...")
                
                return None
            
        except Exception as e:
            print(f"❌ EPIC FAIL in real-time detection: {e}")
            import traceback
            traceback.print_exc()
            return None


    def run_continuous_monitoring(self, symbol: str, timeframe: str = "5m", 
                                 check_interval_minutes: int = 1) -> None:
        """
        🔄 MONITOREO CONTINUO - DETECTA MÚLTIPLES ZONAS
        """
        print(f"\\n🔄⚔️ STARTING CONTINUOUS MONITORING ⚔️🔄")
        print("=" * 70)
        print(f"📊 Symbol: {symbol}")
        print(f"⏰ Timeframe: {timeframe}")
        print(f"🔄 Check interval: {check_interval_minutes} minute(s)")
        print("🎯 Press Ctrl+C to stop monitoring")
        print("=" * 70)
        
        # Reinitialize for continuous monitoring
        self.__init__(symbol, timeframe)
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                print(f"\\n🔄 MONITORING CYCLE #{cycle_count}")
                print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 50)
                
                # Run detection
                latest_zone = self.run_realtime_detection()
                
                if latest_zone:
                    print(f"🚨 CYCLE #{cycle_count}: NEW ZONE DETECTED!")
                    
                    # Aquí puedes añadir notificaciones adicionales
                    # Como enviar email, webhook, etc.
                    
                else:
                    print(f"ℹ️ CYCLE #{cycle_count}: No new zones - continuing monitoring...")
                
                # Wait for next check
                print(f"\\n⏳ Waiting {check_interval_minutes} minute(s) for next check...")
                time.sleep(check_interval_minutes * 60)
                
        except KeyboardInterrupt:
            print(f"\\n\\n🛑 MONITORING STOPPED BY USER")
            print("=" * 70)
            print(f"📊 Total cycles completed: {cycle_count}")
            print(f"🎯 Total zones detected: {len(self.zone_formation_history)}")
            
            if self.zone_formation_history:
                print(f"\\n📋 ZONES DETECTED DURING SESSION:")
                for i, zone in enumerate(self.zone_formation_history, 1):
                    zone_emoji = "🔺" if zone['type'] == 'SUPPLY' else "🔻"
                    print(f"   {zone_emoji} Zone #{i}: {zone['type']} at ${zone['poi']:,.2f}")
            
            print(f"\\n🏛️ CONTINUOUS MONITORING COMPLETE! 🏛️")


def main():
    """Main function para detección en tiempo real"""
    print("🔥⚔️🏛️ REAL-TIME ZONE TRACKER 🏛️⚔️🔥")
    print("=" * 70)
    print("🎯 OBJETIVO: DETECTAR LA ÚLTIMA ZONA QUE SE FORMA")
    print("⚔️ ENFOQUE: TIEMPO REAL - NO HISTORIA")
    print("🏛️ PRECISIÓN ABSOLUTA EN FORMACIÓN ACTIVA")
    print("=" * 70)
    
    # Check credentials
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ EPIC FAIL: Binance API credentials not found!")
        return
    
    # Opciones de uso
    print("\\n🎯 OPCIONES DE USO:")
    print("1. Test único (actual)")
    print("2. Monitoreo continuo")
    
    choice = input("\\nSelecciona opción (1 o 2): ").strip()
    
    if choice == "2":
        # Monitoreo continuo
        symbol = input("Símbolo (ej: BTCUSDT): ").strip().upper() or "BTCUSDT"
        timeframe = input("Timeframe (ej: 5m, 1h): ").strip() or "5m"
        interval = int(input("Intervalo de chequeo en minutos (ej: 1): ").strip() or "1")
        
        tracker = RealTimeZoneTracker(symbol, timeframe)
        tracker.run_continuous_monitoring(symbol, timeframe, interval)
        
    else:
        # Test único (comportamiento actual)
        symbols_to_test = ["BTCUSDT", "ETHUSDT"]
        
        for symbol in symbols_to_test:
            print(f"\\n🎯 TESTING REAL-TIME DETECTION FOR {symbol}")
            print("=" * 50)
            
            # Crear tracker
            tracker = RealTimeZoneTracker(symbol, "1h")
            
            # Ejecutar detección
            latest_zone = tracker.run_realtime_detection()
            
            if latest_zone:
                print(f"✅ {symbol}: NEW ZONE DETECTED!")
            else:
                print(f"ℹ️ {symbol}: No new zone formation")
            
            print("\\n" + "="*50)
        
        print(f"\\n🔥 REAL-TIME ZONE TRACKING COMPLETE! 🔥")


if __name__ == "__main__":
    main()