#!/usr/bin/env python3
"""
🔥 AGGRESSIVE MULTI-SYMBOL SMC SCANNER 🔥
Escáner masivo AGRESIVO que detecta zonas en TODOS los símbolos
Created by KRATOS - CONQUISTADOR IMPLACABLE DEL OLIMPO
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import json
from typing import List, Dict, Any, Optional, Tuple

# Our EPIC SMC Components
from bnb.binance import RobotBinance
from core.swing_detector import SwingDetector
from core.zone_manager import ZoneManager
from core.poi_calculator import POICalculator
from models.swing import Swing
from models.zone import Zone, ZoneType
from core.swing_detector import SwingPoint

# Setup logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class AggressiveMultiScanner:
    """
    🏛️ AGGRESSIVE MULTI-SYMBOL SMC SCANNER
    Escáner BRUTAL que encuentra zonas en CUALQUIER símbolo
    """
    
    def __init__(self, timeframe: str = "1h"):
        self.timeframe = timeframe
        
        print(f"🔥⚔️ AGGRESSIVE MULTI-SCANNER INITIALIZED ⚔️🔥")
        print("🏛️ CONQUISTADOR IMPLACABLE DEL OLIMPO 🏛️")
        print("=" * 80)
        
        # 🏆 TOP 3 CRYPTO SYMBOLS FOR TESTING - MAXIMUM POWER
        self.symbols = [
            'BTCUSDT',   # Bitcoin - King of Crypto
            'ETHUSDT',   # Ethereum - Smart Contract Leader  
            'ADAUSDT'    # Cardano - Academic Blockchain
        ]
        
        # Components will be created per symbol dynamically
        
        # Results storage
        self.scan_results: Dict[str, Dict] = {}
        self.scan_stats = {
            'total_symbols': len(self.symbols),
            'successful_scans': 0,
            'failed_scans': 0,
            'total_zones_detected': 0,
            'scan_start_time': None,
            'scan_end_time': None,
            'total_scan_time': 0.0
        }
        
        print(f"✅ Aggressive Scanner initialized for {len(self.symbols)} symbols")
        print(f"📊 Symbols: {', '.join(self.symbols)}")
        print(f"⏰ Timeframe: {self.timeframe}")
    
    def aggressive_zone_detection(self, symbol: str) -> Dict[str, Any]:
        """
        AGGRESSIVE zone detection that ALWAYS finds zones
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Dictionary with detected zones and metadata
        """
        try:
            print(f"🎯 AGGRESSIVE SCAN: {symbol}")
            
            # Fetch data using RobotBinance
            robot = RobotBinance(symbol, self.timeframe)
            df = robot.candlestick(limit=500)
            if df is None or df.empty:
                return {'success': False, 'error': 'No data fetched'}
            
            # Create swing detector for this symbol
            swing_detector = SwingDetector(symbol, swing_length=5, timeframe=self.timeframe)
            
            # Initialize and detect swings with AGGRESSIVE settings
            if not swing_detector.initialize():
                return {'success': False, 'error': 'Swing detector initialization failed'}
                
            swings = swing_detector.detect_swings(df)
            
            if not swings:
                return {'success': False, 'error': 'No swings detected'}
            
            # Create zones with AGGRESSIVE parameters
            supply_zones = []
            demand_zones = []
            
            current_price = df['close'].iloc[-1]
            price_range = df['high'].max() - df['low'].min()
            
            # AGGRESSIVE zone creation - find zones from ALL significant swings
            current_time = datetime.now()
            atr_buffer = price_range * 0.005  # 0.5% of price range as buffer
            
            for i, swing in enumerate(swings):
                if swing.swing_type.value == 'high':
                    # Create supply zone from swing high using class method
                    zone = Zone.create_supply_zone(
                        swing_price=swing.price,
                        swing_time=swing.timestamp,
                        swing_bar_index=swing.bar_index,
                        atr_buffer=atr_buffer,
                        current_time=current_time,
                        current_bar_index=len(df) - 1
                    )
                    supply_zones.append(zone)
                
                elif swing.swing_type.value == 'low':
                    # Create demand zone from swing low using class method
                    zone = Zone.create_demand_zone(
                        swing_price=swing.price,
                        swing_time=swing.timestamp,
                        swing_bar_index=swing.bar_index,
                        atr_buffer=atr_buffer,
                        current_time=current_time,
                        current_bar_index=len(df) - 1
                    )
                    demand_zones.append(zone)
            
            # Filter zones - keep only the most recent ones (no strength attribute in Zone)
            supply_zones = supply_zones[:5]  # Keep first 5
            demand_zones = demand_zones[:5]  # Keep first 5
            
            # Calculate POIs for zones using dynamic POI calculator
            all_zones = supply_zones + demand_zones
            pois = []
            
            if all_zones:
                poi_calculator = POICalculator(symbol)
                for zone in all_zones:
                    try:
                        poi = poi_calculator.calculate_poi(zone, market_data=df)
                        if poi:
                            pois.append(poi)
                    except Exception as e:
                        # If POI calculation fails, create a simple POI from zone center
                        simple_poi = {
                            'price': zone.poi,
                            'poi_type': 'center',
                            'strength': 1.0,
                            'timestamp': zone.left_time
                        }
                        pois.append(simple_poi)
            
            # Prepare results
            results = {
                'success': True,
                'symbol': symbol,
                'timeframe': self.timeframe,
                'scan_timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'price_range': {
                    'high': float(df['high'].max()),
                    'low': float(df['low'].min()),
                    'range_pct': float((df['high'].max() - df['low'].min()) / current_price * 100)
                },
                'swings_detected': len(swings),
                'supply_zones': [self._zone_to_dict(zone) for zone in supply_zones],
                'demand_zones': [self._zone_to_dict(zone) for zone in demand_zones],
                'pois': [self._poi_to_dict(poi) for poi in pois],
                'summary': {
                    'supply_zones_count': len(supply_zones),
                    'demand_zones_count': len(demand_zones),
                    'total_zones': len(supply_zones) + len(demand_zones),
                    'total_pois': len(pois),
                    'has_zones': len(supply_zones) + len(demand_zones) > 0
                }
            }
            
            total_zones = len(supply_zones) + len(demand_zones)
            print(f"✅ {symbol}: {total_zones} zones ({len(supply_zones)}S/{len(demand_zones)}D)")
            
            return results
            
        except Exception as e:
            print(f"❌ {symbol}: Error - {str(e)[:50]}...")
            return {
                'success': False,
                'symbol': symbol,
                'error': str(e),
                'scan_timestamp': datetime.now().isoformat()
            }
    
    def _zone_to_dict(self, zone: Zone) -> Dict[str, Any]:
        """Convert Zone object to dictionary"""
        return {
            'zone_id': zone.zone_id,
            'type': zone.zone_type.name,
            'top': float(zone.top),
            'bottom': float(zone.bottom),
            'poi': float(zone.poi),
            'swing_price': float(zone.swing_price),
            'atr_buffer': float(zone.atr_buffer),
            'is_active': bool(zone.is_active),
            'is_broken': bool(zone.is_broken),
            'left_time': zone.left_time.isoformat() if zone.left_time else None,
            'right_time': zone.right_time.isoformat() if zone.right_time else None,
            'left_bar_index': zone.left_bar_index,
            'right_bar_index': zone.right_bar_index,
            'text_label': zone.text_label
        }
    
    def _poi_to_dict(self, poi) -> Dict[str, Any]:
        """Convert POI object to dictionary"""
        try:
            return {
                'price': float(getattr(poi, 'price', 0.0)),
                'poi_type': getattr(poi, 'poi_type', 'unknown'),
                'strength': float(getattr(poi, 'strength', 1.0)),
                'timestamp': getattr(poi, 'timestamp', datetime.now()).isoformat() if hasattr(poi, 'timestamp') else datetime.now().isoformat()
            }
        except Exception as e:
            # Fallback if POI object is different
            return {
                'price': float(poi) if isinstance(poi, (int, float)) else 0.0,
                'poi_type': 'center',
                'strength': 1.0,
                'timestamp': datetime.now().isoformat()
            }
    
    def scan_all_symbols(self) -> Dict[str, Dict]:
        """
        Scan all symbols sequentially with AGGRESSIVE detection
        
        Returns:
            Dictionary with all scan results
        """
        try:
            print(f"\n🔥⚔️ STARTING AGGRESSIVE MASS SCAN ⚔️🔥")
            print(f"🏛️ DEPLOYING BRUTAL WEAPONS ON {len(self.symbols)} TARGETS 🏛️")
            print("=" * 80)
            
            self.scan_stats['scan_start_time'] = datetime.now()
            start_time = time.time()
            
            # Sequential scanning for stability
            for i, symbol in enumerate(self.symbols, 1):
                print(f"\n[{i:2d}/{len(self.symbols)}] ", end="")
                
                results = self.aggressive_zone_detection(symbol)
                self.scan_results[symbol] = results
                
                if results.get('success', False):
                    self.scan_stats['successful_scans'] += 1
                    zones_count = results.get('summary', {}).get('total_zones', 0)
                    self.scan_stats['total_zones_detected'] += zones_count
                else:
                    self.scan_stats['failed_scans'] += 1
                
                # Small delay to avoid rate limits
                time.sleep(0.1)
            
            # Calculate final stats
            end_time = time.time()
            self.scan_stats['scan_end_time'] = datetime.now()
            self.scan_stats['total_scan_time'] = end_time - start_time
            
            print(f"\n\n🏆 AGGRESSIVE MASS SCAN COMPLETE! 🏆")
            print("=" * 80)
            print(f"⏱️  Total scan time: {self.scan_stats['total_scan_time']:.2f}s")
            print(f"✅ Successful scans: {self.scan_stats['successful_scans']}/{self.scan_stats['total_symbols']}")
            print(f"❌ Failed scans: {self.scan_stats['failed_scans']}")
            print(f"🎯 Total zones detected: {self.scan_stats['total_zones_detected']}")
            print(f"⚡ Average time per symbol: {self.scan_stats['total_scan_time']/len(self.symbols):.2f}s")
            
            return self.scan_results
            
        except Exception as e:
            print(f"❌ EPIC FAIL in aggressive scanning: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def display_latest_zones_per_crypto(self, zones_per_crypto: int = 3) -> None:
        """
        🔥 Display the latest zones for each crypto - EPIC VISUALIZATION 🔥
        
        Args:
            zones_per_crypto: Number of latest zones to show per crypto
        """
        try:
            print(f"\n🏛️ LATEST {zones_per_crypto} ZONES PER CRYPTO - EPIC BREAKDOWN 🏛️")
            print("=" * 100)
            
            # Filter successful scans
            successful_scans = {
                symbol: data for symbol, data in self.scan_results.items() 
                if data.get('success', False)
            }
            
            if not successful_scans:
                print("❌ No successful scans to display")
                return
            
            for symbol, data in successful_scans.items():
                print(f"\n🔥⚔️ {symbol} - LATEST ZONES ⚔️🔥")
                print("-" * 80)
                
                current_price = data.get('current_price', 0)
                supply_zones = data.get('supply_zones', [])
                demand_zones = data.get('demand_zones', [])
                
                print(f"💰 Current Price: ${current_price:,.2f}")
                print(f"📊 Total Zones: {len(supply_zones)} Supply + {len(demand_zones)} Demand")
                
                # Show latest supply zones
                if supply_zones:
                    print(f"\n🔴 LATEST {min(zones_per_crypto, len(supply_zones))} SUPPLY ZONES:")
                    print(f"{'#':<3} {'Price Range':<25} {'POI':<15} {'Distance':<12} {'Date':<20}")
                    print("-" * 80)
                    
                    # Sort by creation time (most recent first)
                    sorted_supply = sorted(supply_zones, 
                                         key=lambda z: z.get('left_time', ''), 
                                         reverse=True)[:zones_per_crypto]
                    
                    for i, zone in enumerate(sorted_supply, 1):
                        top = zone.get('top', 0)
                        bottom = zone.get('bottom', 0)
                        poi = zone.get('poi', 0)
                        left_time = zone.get('left_time', '')
                        
                        # Calculate distance from current price
                        distance_pct = ((poi - current_price) / current_price * 100) if current_price > 0 else 0
                        distance_str = f"{distance_pct:+.2f}%"
                        
                        # Format date
                        try:
                            date_obj = datetime.fromisoformat(left_time.replace('Z', '+00:00'))
                            date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                        except:
                            date_str = left_time[:16] if left_time else 'Unknown'
                        
                        price_range = f"${bottom:,.2f} - ${top:,.2f}"
                        poi_str = f"${poi:,.2f}"
                        
                        print(f"{i:<3} {price_range:<25} {poi_str:<15} {distance_str:<12} {date_str:<20}")
                
                # Show latest demand zones
                if demand_zones:
                    print(f"\n🟢 LATEST {min(zones_per_crypto, len(demand_zones))} DEMAND ZONES:")
                    print(f"{'#':<3} {'Price Range':<25} {'POI':<15} {'Distance':<12} {'Date':<20}")
                    print("-" * 80)
                    
                    # Sort by creation time (most recent first)
                    sorted_demand = sorted(demand_zones, 
                                         key=lambda z: z.get('left_time', ''), 
                                         reverse=True)[:zones_per_crypto]
                    
                    for i, zone in enumerate(sorted_demand, 1):
                        top = zone.get('top', 0)
                        bottom = zone.get('bottom', 0)
                        poi = zone.get('poi', 0)
                        left_time = zone.get('left_time', '')
                        
                        # Calculate distance from current price
                        distance_pct = ((poi - current_price) / current_price * 100) if current_price > 0 else 0
                        distance_str = f"{distance_pct:+.2f}%"
                        
                        # Format date
                        try:
                            date_obj = datetime.fromisoformat(left_time.replace('Z', '+00:00'))
                            date_str = date_obj.strftime('%Y-%m-%d %H:%M')
                        except:
                            date_str = left_time[:16] if left_time else 'Unknown'
                        
                        price_range = f"${bottom:,.2f} - ${top:,.2f}"
                        poi_str = f"${poi:,.2f}"
                        
                        print(f"{i:<3} {price_range:<25} {poi_str:<15} {distance_str:<12} {date_str:<20}")
                
                print(f"\n{'='*80}")
            
            print(f"\n🏆 ZONE ANALYSIS COMPLETE! 🏆")
            
        except Exception as e:
            print(f"❌ Error displaying latest zones: {e}")
            import traceback
            traceback.print_exc()

    def display_top_performers(self, top_n: int = 10) -> None:
        """Display top performing symbols by zones detected"""
        try:
            print(f"\n🏛️ TOP {top_n} PERFORMERS BY ZONES DETECTED 🏛️")
            print("=" * 80)
            
            # Filter successful scans and sort by total zones
            successful_scans = {
                symbol: data for symbol, data in self.scan_results.items() 
                if data.get('success', False)
            }
            
            if successful_scans:
                sorted_symbols = sorted(
                    successful_scans.items(),
                    key=lambda x: x[1].get('summary', {}).get('total_zones', 0),
                    reverse=True
                )
                
                print(f"🎯 RANKING:")
                print("-" * 70)
                print(f"{'Rank':<4} {'Symbol':<10} {'Zones':<6} {'Supply':<6} {'Demand':<6} {'POIs':<5}")
                print("-" * 70)
                
                for i, (symbol, data) in enumerate(sorted_symbols[:top_n], 1):
                    summary = data.get('summary', {})
                    supply_count = summary.get('supply_zones_count', 0)
                    demand_count = summary.get('demand_zones_count', 0)
                    total_zones = summary.get('total_zones', 0)
                    total_pois = summary.get('total_pois', 0)
                    
                    print(f"{i:<4} {symbol:<10} {total_zones:<6} {supply_count:<6} {demand_count:<6} {total_pois:<5}")
                
                # Summary statistics
                total_supply = sum(
                    data.get('summary', {}).get('supply_zones_count', 0) 
                    for data in successful_scans.values()
                )
                total_demand = sum(
                    data.get('summary', {}).get('demand_zones_count', 0) 
                    for data in successful_scans.values()
                )
                
                print(f"\n📊 OVERALL STATISTICS:")
                print("-" * 40)
                print(f"🔴 Total Supply zones: {total_supply}")
                print(f"🟢 Total Demand zones: {total_demand}")
                print(f"📈 Supply/Demand ratio: {total_supply/max(total_demand,1):.2f}")
                print(f"⚡ Average zones per symbol: {(total_supply + total_demand)/len(successful_scans):.1f}")
            
            else:
                print("❌ No successful scans to display")
                
        except Exception as e:
            print(f"❌ Error displaying top performers: {e}")
    
    def export_results(self, filename: Optional[str] = None) -> str:
        """Export results to JSON file"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"aggressive_smc_scan_{timestamp}.json"
            
            export_data = {
                'scan_metadata': {
                    'scan_timestamp': datetime.now().isoformat(),
                    'timeframe': self.timeframe,
                    'scanner_version': 'aggressive_1.0.0',
                    'total_symbols_scanned': len(self.symbols),
                    'symbols_list': self.symbols
                },
                'scan_statistics': self.scan_stats,
                'scan_results': self.scan_results
            }
            
            filepath = os.path.join('demo', filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📁 Results exported to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error exporting results: {e}")
            return ""


def main():
    """
    🔥 MAIN EXECUTION - DEPLOY THE AGGRESSIVE ARMY! 🔥
    """
    try:
        print("🏛️" + "=" * 78 + "🏛️")
        print("🔥" + " " * 15 + "AGGRESSIVE MULTI-SYMBOL SMC SCANNER" + " " * 15 + "🔥")
        print("⚔️" + " " * 10 + "CONQUISTADOR IMPLACABLE DEL OLIMPO" + " " * 10 + "⚔️")
        print("🏛️" + "=" * 78 + "🏛️")
        
        # Initialize aggressive scanner
        scanner = AggressiveMultiScanner(timeframe="1h")
        
        # Execute aggressive mass scan
        results = scanner.scan_all_symbols()
        
        if results:
            # Display latest zones per crypto - EPIC VISUALIZATION
            scanner.display_latest_zones_per_crypto(zones_per_crypto=3)
            
            # Display top performers summary
            scanner.display_top_performers(top_n=15)
            
            # Export results
            export_path = scanner.export_results()
            
            print(f"\n🏆 AGGRESSIVE MISSION ACCOMPLISHED! 🏆")
            print(f"📊 Scanned {len(results)} symbols")
            print(f"📁 Results saved to: {export_path}")
            
        else:
            print("❌ No results obtained from aggressive scan")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Aggressive scan interrupted by user")
    except Exception as e:
        print(f"❌ EPIC FAIL in aggressive execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()