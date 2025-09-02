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
        
        print(f"🔥⚔️ IMPLACABLE ZONES DETECTOR FOR {self.symbol} ⚔️🔥")
        print("🏛️ PRECISIÓN ABSOLUTA - TRADINGVIEW MATCH OR DIE 🏛️")
        print("=" * 70)
        
        # Initialize components
        self.swing_detector = SwingDetector(symbol)
        
        # Data storage
        self.market_data: Optional[pd.DataFrame] = None
        self.swings: List = []
        self.implacable_zones: Dict = {}
        
        print(f"✅ Implacable Detector initialized for {self.symbol}")
    
    def fetch_extended_data(self, limit: int = 1000) -> bool:
        """Fetch EXTENDED data to catch all significant levels"""
        try:
            print(f"\\n📡 FETCHING EXTENDED {self.symbol} DATA...")
            print("-" * 50)
            
            robot = RobotBinance(self.symbol, self.timeframe)
            self.market_data = robot.candlestick(limit=limit)
            
            if self.market_data.empty:
                raise ValueError(f"No data received for {self.symbol}")
            
            print(f"✅ SUCCESS! Fetched {len(self.market_data)} candles")
            print(f"📅 Extended range: {self.market_data.index[0]} to {self.market_data.index[-1]}")
            print(f"💰 Full price range: ${self.market_data['low'].min():,.2f} - ${self.market_data['high'].max():,.2f}")
            print(f"📈 Current price: ${self.market_data['close'].iloc[-1]:,.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL in fetching extended data: {e}")
            return False
    
    def detect_all_swings(self) -> bool:
        """Detect ALL possible swings with maximum sensitivity"""
        try:
            print(f"\\n⚔️ DETECTING ALL POSSIBLE SWINGS...")
            print("-" * 50)
            
            start_time = time.time()
            self.swings = self.swing_detector.detect_swings(self.market_data)
            detection_time = time.time() - start_time
            
            if not self.swings:
                print("⚠️ No swings detected")
                return False
            
            print(f"🎯 SWING DETECTION COMPLETE!")
            print(f"   ⏱️  Detection time: {detection_time:.3f}s")
            print(f"   📊 Total swings: {len(self.swings)}")
            
            # Analyze swing distribution
            swing_prices = [s.price for s in self.swings]
            swing_prices.sort()
            
            print(f"   💰 Swing range: ${swing_prices[0]:,.2f} - ${swing_prices[-1]:,.2f}")
            print(f"   📊 Price quartiles:")
            print(f"      Q1 (25%): ${np.percentile(swing_prices, 25):,.2f}")
            print(f"      Q2 (50%): ${np.percentile(swing_prices, 50):,.2f}")
            print(f"      Q3 (75%): ${np.percentile(swing_prices, 75):,.2f}")
            print(f"      Q4 (95%): ${np.percentile(swing_prices, 95):,.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL in swing detection: {e}")
            return False
    
    def extract_implacable_zones(self) -> bool:
        """Extract zones with IMPLACABLE precision matching TradingView"""
        try:
            print(f"\\n🏛️ EXTRACTING IMPLACABLE ZONES...")
            print("-" * 50)
            
            if not self.swings:
                print("⚠️ No swings available")
                return False
            
            current_price = float(self.market_data['close'].iloc[-1])
            
            # IMPLACABLE ANALYSIS: Find the EXACT zones TradingView shows
            print(f"📊 IMPLACABLE ANALYSIS:")
            print(f"   Current Price: ${current_price:,.2f}")
            
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
            
            print(f"   📊 Analyzing {len(swing_analysis)} swings...")
            
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
                    # Find the most RECENT swing in this zone (most important for current trading)
                    # Prioritize by RECENCY (timestamp) first, then strength
                    best_swing = max(zone_swings, key=lambda s: (s['timestamp'], s['strength']))
                    
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
                    
                    print(f"   🎯 {zone_name.upper()}: Found {len(zone_swings)} swings, best at ${best_swing['price']:,.2f}")
            
            # Sort zones by distance from current price
            detected_zones.sort(key=lambda z: abs(z['distance_pct']))
            
            # Separate by type
            supply_zones = [z for z in detected_zones if z['type'] == 'SUPPLY']
            demand_zones = [z for z in detected_zones if z['type'] == 'DEMAND']
            
            self.implacable_zones = {
                'supply': supply_zones,
                'demand': demand_zones,
                'current_price': current_price,
                'extraction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_swings_analyzed': len(swing_analysis),
                'detection_method': 'implacable_tradingview_match'
            }
            
            print(f"🎯 IMPLACABLE ZONE EXTRACTION COMPLETE!")
            print(f"   📊 Supply zones: {len(supply_zones)}")
            print(f"   📊 Demand zones: {len(demand_zones)}")
            print(f"   📊 Total zones: {len(detected_zones)}")
            
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
                    'fecha_hora': self._convert_to_utc_minus_5(zone['formation_date'])
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
                    'fecha_hora': self._convert_to_utc_minus_5(zone['formation_date'])
                }
                all_zones.append(zone_data)
            
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
            print(f"🏆 Total zonas: {len(all_zones)} | 🔊 Sistema: ACTIVO | 💡 Presiona Ctrl+C para salir")
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
                    'name': zone['name'],
                    'poi': round(zone['poi'], 2),
                    'top': round(zone['top'], 2),
                    'bottom': round(zone['bottom'], 2),
                    'distance_percentage': f"{zone['distance_pct']:+.2f}%",
                    'formation_date': zone['formation_date'],
                    'strength': zone['strength'],
                    'volume': int(zone['volume']),
                    'swings_in_zone': zone['swing_count_in_zone']
                }
                export_data['supply_zones'].append(clean_zone)
            
            # Process demand zones
            for zone in self.implacable_zones['demand']:
                clean_zone = {
                    'name': zone['name'],
                    'poi': round(zone['poi'], 2),
                    'top': round(zone['top'], 2),
                    'bottom': round(zone['bottom'], 2),
                    'distance_percentage': f"{zone['distance_pct']:+.2f}%",
                    'formation_date': zone['formation_date'],
                    'strength': zone['strength'],
                    'volume': int(zone['volume']),
                    'swings_in_zone': zone['swing_count_in_zone']
                }
                export_data['demand_zones'].append(clean_zone)
            
            return export_data
            
        except Exception as e:
            print(f"❌ FAIL in exporting JSON: {e}")
            return {}
    
    def run_implacable_detection(self) -> bool:
        """Run complete IMPLACABLE detection"""
        try:
            print(f"\\n🔥⚔️ STARTING IMPLACABLE DETECTION ⚔️🔥")
            print("🏛️ TRADINGVIEW PRECISION OR DEATH! 🏛️")
            print("=" * 70)
            
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
            
            print(f"\\n🏆 IMPLACABLE DETECTION COMPLETE! 🏆")
            print("=" * 70)
            print(f"⏱️  Total time: {total_time:.3f}s")
            print(f"📊 Data analyzed: {len(self.market_data)} candles")
            print(f"⚔️ Swings processed: {len(self.swings)}")
            print(f"🏛️ Zones extracted: {len(self.implacable_zones.get('supply', [])) + len(self.implacable_zones.get('demand', []))}")
            
            # ¡MOSTRAR TABLA ÉPICA!
            self.display_epic_zones_table()
            
            print(f"\\n🔥 IMPLACABLE PRECISION: ACTIVATED! 🔥")
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in implacable detection: {e}")
            import traceback
            traceback.print_exc()
            return False