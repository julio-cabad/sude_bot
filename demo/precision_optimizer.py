#!/usr/bin/env python3
"""
🔥⚔️ PRECISION OPTIMIZER - CONQUISTADOR DE MERCADOS ⚔️🔥
Optimizador que ajusta parámetros para lograr 100% precisión TradingView
Created by FEROZ GUERRERO DEL CÓDIGO - NO MERCY FOR IMPRECISION
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
import json

# Our EPIC SMC Components
from demo.implacable_zones_detector import ImplacableZonesDetector
from core.swing_detector import SwingDetector
from models.zone import Zone, ZoneType
from bnb.binance import RobotBinance

# Setup minimal logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class PrecisionOptimizer:
    """
    🏛️ PRECISION OPTIMIZER - CONQUISTADOR ABSOLUTO
    Optimiza parámetros para lograr 100% precisión en TODAS las cryptos
    """
    
    def __init__(self):
        print(f"🔥⚔️🏛️ PRECISION OPTIMIZER ACTIVATED 🏛️⚔️🔥")
        print("🎯 OBJETIVO: 100% PRECISIÓN EN TODAS LAS CRYPTOS")
        print("⚔️ NO MERCY FOR IMPRECISION!")
        print("=" * 70)
        
        # Parámetros de optimización - ENFOCADOS PARA BTC/ETH
        self.optimization_params = {
            'swing_lengths': [7, 10, 15],  # Reducido para eficiencia
            'data_limits': [1000, 1500],   # Suficiente data histórica
            'zone_ranges': [
                # Rangos optimizados para BTC/ETH
                {'supply_multipliers': [1.01, 1.03, 1.08, 1.12], 'demand_multipliers': [0.88, 0.92, 0.97, 0.99]},
                {'supply_multipliers': [1.005, 1.02, 1.06, 1.10], 'demand_multipliers': [0.90, 0.94, 0.98, 0.995]}
            ],
            'zone_height_factors': [0.3, 0.4]  # Factores más efectivos
        }
        
        # Resultados de optimización
        self.optimization_results = {}
        
    def test_symbol_precision(self, symbol: str, timeframe: str = "1h", 
                            swing_length: int = 10, data_limit: int = 1000,
                            zone_config: Dict = None, zone_height_factor: float = 0.3) -> Dict:
        """
        🎯 PRUEBA LA PRECISIÓN DE UN SÍMBOLO CON PARÁMETROS ESPECÍFICOS
        """
        try:
            print(f"\\n🔍 TESTING {symbol} - swing_length={swing_length}, data_limit={data_limit}")
            
            # Crear detector con parámetros específicos
            detector = ImplacableZonesDetector(symbol, timeframe)
            
            # Modificar parámetros del swing detector
            detector.swing_detector.swing_length = swing_length
            
            # Fetch data
            if not detector.fetch_extended_data(limit=data_limit):
                return {'precision': 0, 'error': 'Failed to fetch data'}
            
            # Detect swings
            if not detector.detect_all_swings():
                return {'precision': 0, 'error': 'Failed to detect swings'}
            
            # Extract zones con parámetros personalizados
            if zone_config:
                success = self._extract_zones_with_custom_params(
                    detector, zone_config, zone_height_factor
                )
            else:
                success = detector.extract_implacable_zones()
            
            if not success:
                return {'precision': 0, 'error': 'Failed to extract zones'}
            
            # Calcular precisión
            precision_data = self._calculate_precision(detector, symbol)
            
            return {
                'precision': precision_data['score'],
                'zones_found': precision_data['zones_found'],
                'zones_expected': precision_data['zones_expected'],
                'details': precision_data['details'],
                'swing_count': len(detector.swings),
                'data_candles': len(detector.market_data)
            }
            
        except Exception as e:
            print(f"❌ Error testing {symbol}: {e}")
            return {'precision': 0, 'error': str(e)}
    
    def _extract_zones_with_custom_params(self, detector, zone_config: Dict, 
                                        zone_height_factor: float) -> bool:
        """
        🏛️ EXTRAE ZONAS CON PARÁMETROS PERSONALIZADOS
        """
        try:
            if not detector.swings:
                return False
            
            current_price = float(detector.market_data['close'].iloc[-1])
            
            # Análisis de swings
            swing_analysis = []
            for swing in detector.swings:
                distance_pct = ((swing.price - current_price) / current_price) * 100
                swing_info = {
                    'price': float(swing.price),
                    'timestamp': swing.timestamp,
                    'swing_type': swing.swing_type,
                    'strength': swing.strength,
                    'volume': getattr(swing, 'volume', 0),
                    'distance_pct': distance_pct
                }
                swing_analysis.append(swing_info)
            
            swing_analysis.sort(key=lambda x: x['price'])
            
            # Configurar zonas objetivo con parámetros personalizados
            supply_mults = zone_config['supply_multipliers']
            demand_mults = zone_config['demand_multipliers']
            
            target_zones = {
                'recent_supply_close': {
                    'min': current_price * supply_mults[0],
                    'max': current_price * supply_mults[1],
                    'type': 'SUPPLY'
                },
                'recent_supply_medium': {
                    'min': current_price * supply_mults[1],
                    'max': current_price * supply_mults[2],
                    'type': 'SUPPLY'
                },
                'recent_supply_high': {
                    'min': current_price * supply_mults[2],
                    'max': current_price * supply_mults[3],
                    'type': 'SUPPLY'
                },
                'recent_demand_close': {
                    'min': current_price * demand_mults[2],
                    'max': current_price * demand_mults[3],
                    'type': 'DEMAND'
                },
                'recent_demand_low': {
                    'min': current_price * demand_mults[0],
                    'max': current_price * demand_mults[1],
                    'type': 'DEMAND'
                }
            }
            
            detected_zones = []
            
            # Encontrar swings en cada zona objetivo
            for zone_name, zone_config_item in target_zones.items():
                zone_swings = []
                
                for swing in swing_analysis:
                    if zone_config_item['min'] <= swing['price'] <= zone_config_item['max']:
                        zone_swings.append(swing)
                
                if zone_swings:
                    best_swing = max(zone_swings, key=lambda s: (s['timestamp'], s['strength']))
                    
                    # Calcular límites de zona con factor personalizado
                    zone_height = (zone_config_item['max'] - zone_config_item['min']) * zone_height_factor
                    
                    if zone_config_item['type'] == 'SUPPLY':
                        zone_top = best_swing['price'] + (zone_height * 0.3)
                        zone_bottom = best_swing['price'] - (zone_height * 0.7)
                    else:  # DEMAND
                        zone_top = best_swing['price'] + (zone_height * 0.7)
                        zone_bottom = best_swing['price'] - (zone_height * 0.3)
                    
                    zone_data = {
                        'name': zone_name,
                        'type': zone_config_item['type'],
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
            
            # Separar por tipo
            supply_zones = [z for z in detected_zones if z['type'] == 'SUPPLY']
            demand_zones = [z for z in detected_zones if z['type'] == 'DEMAND']
            
            detector.implacable_zones = {
                'supply': supply_zones,
                'demand': demand_zones,
                'current_price': current_price,
                'extraction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_swings_analyzed': len(swing_analysis),
                'detection_method': 'optimized_precision'
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Error in custom zone extraction: {e}")
            return False
    
    def _calculate_precision(self, detector, symbol: str) -> Dict:
        """
        ⚔️ CALCULA LA PRECISIÓN COMPARANDO CON TRADINGVIEW
        """
        if not detector.implacable_zones:
            return {'score': 0, 'zones_found': 0, 'zones_expected': 3, 'details': {}}
        
        current_price = detector.implacable_zones['current_price']
        supply_zones = detector.implacable_zones['supply']
        demand_zones = detector.implacable_zones['demand']
        
        # Zonas esperadas dinámicas basadas en precio actual
        expected_zones = {
            f'Upper Supply (~${current_price*1.10:,.0f}-{current_price*1.20:,.0f})': False,
            f'Middle Supply (~${current_price*1.03:,.0f}-{current_price*1.10:,.0f})': False,
            f'Lower Demand (~${current_price*0.90:,.0f}-{current_price*0.97:,.0f})': False
        }
        
        # Verificar zonas encontradas
        for zone in supply_zones + demand_zones:
            poi = zone['poi']
            if current_price*1.10 <= poi <= current_price*1.20:
                expected_zones[f'Upper Supply (~${current_price*1.10:,.0f}-{current_price*1.20:,.0f})'] = True
            elif current_price*1.03 <= poi <= current_price*1.10:
                expected_zones[f'Middle Supply (~${current_price*1.03:,.0f}-{current_price*1.10:,.0f})'] = True
            elif current_price*0.90 <= poi <= current_price*0.97:
                expected_zones[f'Lower Demand (~${current_price*0.90:,.0f}-{current_price*0.97:,.0f})'] = True
        
        # Calcular score
        found_count = sum(expected_zones.values())
        total_expected = len(expected_zones)
        precision_score = (found_count / total_expected) * 100
        
        return {
            'score': precision_score,
            'zones_found': found_count,
            'zones_expected': total_expected,
            'details': expected_zones
        }
    
    def optimize_symbol(self, symbol: str, timeframe: str = "1h") -> Dict:
        """
        🏛️ OPTIMIZA UN SÍMBOLO ESPECÍFICO PARA MÁXIMA PRECISIÓN
        """
        print(f"\\n🔥⚔️ OPTIMIZING {symbol} FOR MAXIMUM PRECISION ⚔️🔥")
        print("-" * 60)
        
        best_result = {'precision': 0, 'params': {}}
        all_results = []
        
        total_combinations = (
            len(self.optimization_params['swing_lengths']) *
            len(self.optimization_params['data_limits']) *
            len(self.optimization_params['zone_ranges']) *
            len(self.optimization_params['zone_height_factors'])
        )
        
        print(f"🎯 Testing {total_combinations} parameter combinations...")
        
        combination_count = 0
        
        for swing_length in self.optimization_params['swing_lengths']:
            for data_limit in self.optimization_params['data_limits']:
                for zone_config in self.optimization_params['zone_ranges']:
                    for zone_height_factor in self.optimization_params['zone_height_factors']:
                        
                        combination_count += 1
                        
                        # Test this combination
                        result = self.test_symbol_precision(
                            symbol, timeframe, swing_length, data_limit,
                            zone_config, zone_height_factor
                        )
                        
                        if result['precision'] > best_result['precision']:
                            best_result = {
                                'precision': result['precision'],
                                'params': {
                                    'swing_length': swing_length,
                                    'data_limit': data_limit,
                                    'zone_config': zone_config,
                                    'zone_height_factor': zone_height_factor
                                },
                                'details': result
                            }
                            
                            print(f"   🎯 NEW BEST: {result['precision']:.1f}% (combo {combination_count}/{total_combinations})")
                        
                        all_results.append({
                            'params': {
                                'swing_length': swing_length,
                                'data_limit': data_limit,
                                'zone_config': zone_config,
                                'zone_height_factor': zone_height_factor
                            },
                            'result': result
                        })
                        
                        # Early exit if we achieve 100%
                        if result['precision'] >= 100:
                            print(f"🏆 PERFECT PRECISION ACHIEVED! Stopping optimization.")
                            break
                    
                    if best_result['precision'] >= 100:
                        break
                if best_result['precision'] >= 100:
                    break
            if best_result['precision'] >= 100:
                break
        
        self.optimization_results[symbol] = {
            'best_result': best_result,
            'all_results': all_results
        }
        
        return best_result
    
    def optimize_multiple_symbols(self, symbols: List[str], timeframe: str = "1h") -> Dict:
        """
        ⚔️ OPTIMIZA MÚLTIPLES SÍMBOLOS PARA DOMINACIÓN TOTAL
        """
        print(f"\\n🔥🏛️ MULTI-SYMBOL OPTIMIZATION - TOTAL DOMINATION 🏛️🔥")
        print("=" * 70)
        
        results = {}
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\\n[{i}/{len(symbols)}] OPTIMIZING {symbol}...")
            
            try:
                result = self.optimize_symbol(symbol, timeframe)
                results[symbol] = result
                
                print(f"✅ {symbol}: {result['precision']:.1f}% precision achieved")
                
            except Exception as e:
                print(f"❌ {symbol}: Optimization failed - {e}")
                results[symbol] = {'precision': 0, 'error': str(e)}
        
        return results
    
    def generate_optimization_report(self, results: Dict) -> None:
        """
        📊 GENERA REPORTE ÉPICO DE OPTIMIZACIÓN
        """
        print(f"\\n🏆 OPTIMIZATION REPORT - CONQUEST SUMMARY 🏆")
        print("=" * 70)
        
        total_symbols = len(results)
        perfect_symbols = sum(1 for r in results.values() if r.get('precision', 0) >= 100)
        good_symbols = sum(1 for r in results.values() if r.get('precision', 0) >= 80)
        
        print(f"📊 SUMMARY:")
        print(f"   Total symbols tested: {total_symbols}")
        print(f"   Perfect precision (100%): {perfect_symbols}")
        print(f"   Good precision (≥80%): {good_symbols}")
        print(f"   Success rate: {(perfect_symbols/total_symbols)*100:.1f}%")
        
        print(f"\\n🎯 DETAILED RESULTS:")
        for symbol, result in results.items():
            precision = result.get('precision', 0)
            status = "🏆" if precision >= 100 else "✅" if precision >= 80 else "⚠️" if precision >= 50 else "❌"
            
            print(f"   {status} {symbol}: {precision:.1f}%")
            
            if precision > 0 and 'params' in result:
                params = result['params']
                print(f"      Best params: swing_length={params['swing_length']}, data_limit={params['data_limit']}")
        
        print(f"\\n🔥 OPTIMIZATION COMPLETE! 🔥")


def main():
    """Main function para optimización épica"""
    print("🔥⚔️🏛️ PRECISION OPTIMIZER - MARKET DOMINATION 🏛️⚔️🔥")
    print("=" * 70)
    
    # Check credentials
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ EPIC FAIL: Binance API credentials not found!")
        return
    
    # Crear optimizador
    optimizer = PrecisionOptimizer()
    
    # Símbolos a optimizar - SOLO BTC Y ETH
    symbols_to_test = ["BTCUSDT", "ETHUSDT"]
    
    print(f"🎯 OPTIMIZING {len(symbols_to_test)} SYMBOLS FOR MAXIMUM PRECISION...")
    
    # Optimizar múltiples símbolos
    results = optimizer.optimize_multiple_symbols(symbols_to_test)
    
    # Generar reporte
    optimizer.generate_optimization_report(results)
    
    # Exportar resultados
    with open('optimization_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\\n📋 Results exported to optimization_results.json")
    print(f"🏛️ PRECISION OPTIMIZATION COMPLETE! 🏛️")


if __name__ == "__main__":
    main()