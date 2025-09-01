#!/usr/bin/env python3
"""
🔥 TOP 3 ZONES VIEWER - MAGNIFICO GUERRERO DEL CÓDIGO 🔥
Visualizador épico de las 3 últimas zonas por cripto con horario UTC-5
Based on the proven implacable_zones_detector.py logic
Created by KRATOS - DOMINADOR VISUAL DEL OLIMPO
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
import pytz

# Our EPIC SMC Components - Using proven implacable logic
from demo.implacable_zones_detector import ImplacableZonesDetector

# Setup logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class Top3ZonesViewer:
    """
    🏛️ TOP 3 ZONES VIEWER - MAGNIFICO GUERRERO DEL CÓDIGO
    Visualizador épico que muestra las 3 zonas más recientes por cripto
    """
    
    def __init__(self, timeframe: str = "1h"):
        self.timeframe = timeframe
        
        print(f"🔥⚔️ TOP 3 ZONES VIEWER INITIALIZED ⚔️🔥")
        print("🏛️ MAGNIFICO GUERRERO DEL CÓDIGO - VISUAL DOMINATOR 🏛️")
        print("=" * 80)
        
        # 🏆 TOP 3 CRYPTO SYMBOLS - PROVEN WARRIORS
        self.symbols = [
            'BTCUSDT',   # Bitcoin - King of Crypto
            'ETHUSDT',   # Ethereum - Smart Contract Leader  
            'ADAUSDT'    # Cardano - Academic Blockchain
        ]
        
        # Ecuador timezone (UTC-5)
        self.ecuador_tz = pytz.timezone('America/Guayaquil')
        
        print(f"✅ Top 3 Zones Viewer initialized")
        print(f"📊 Symbols: {', '.join(self.symbols)}")
        print(f"⏰ Timeframe: {self.timeframe}")
        print(f"🌍 Timezone: UTC-5 (Ecuador)")
    
    def convert_to_ecuador_time(self, utc_datetime: datetime) -> str:
        """
        Convert UTC datetime to Ecuador time (UTC-5)
        
        Args:
            utc_datetime: UTC datetime object
            
        Returns:
            Formatted Ecuador time string
        """
        try:
            if isinstance(utc_datetime, str):
                utc_datetime = pd.to_datetime(utc_datetime, utc=True)
            
            # Ensure it's UTC aware
            if utc_datetime.tzinfo is None:
                utc_datetime = pytz.utc.localize(utc_datetime)
            elif utc_datetime.tzinfo != pytz.utc:
                utc_datetime = utc_datetime.astimezone(pytz.utc)
            
            # Convert to Ecuador time
            ecuador_time = utc_datetime.astimezone(self.ecuador_tz)
            
            return ecuador_time.strftime("%Y-%m-%d %H:%M:%S ECT")
            
        except Exception as e:
            return f"Error converting time: {e}"
    
    def get_top3_zones_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Get top 3 most recent zones for a symbol using proven implacable logic
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Dictionary with top 3 zones and metadata
        """
        try:
            print(f"🎯 Analyzing {symbol} for TOP 3 zones...")
            
            # Use proven ImplacableZonesDetector
            detector = ImplacableZonesDetector(symbol, self.timeframe)
            
            # Suppress output for clean display
            import io
            import contextlib
            
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                success = detector.run_implacable_detection()
            
            if not success:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'Implacable detection failed',
                    'top3_zones': []
                }
            
            # Export results using proven method
            results = detector.export_implacable_json()
            
            if not results:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'No results exported',
                    'top3_zones': []
                }
            
            # Extract zones
            supply_zones = results.get('supply_zones', [])
            demand_zones = results.get('demand_zones', [])
            all_zones = supply_zones + demand_zones
            
            if not all_zones:
                return {
                    'symbol': symbol,
                    'success': True,
                    'current_price': results.get('current_price', 0),
                    'total_zones_available': 0,
                    'top3_zones': [],
                    'message': 'No zones detected'
                }
            
            # Sort zones by formation time (most recent first)
            sorted_zones = sorted(
                all_zones, 
                key=lambda z: pd.to_datetime(z.get('formation_time', '1970-01-01')), 
                reverse=True
            )
            
            # Get top 3 most recent zones
            top3_zones = sorted_zones[:3]
            
            # Convert times to Ecuador timezone
            for zone in top3_zones:
                # Try multiple time field names
                time_field = None
                for field in ['formation_time', 'timestamp', 'left_time', 'created_at']:
                    if field in zone and zone[field]:
                        time_field = zone[field]
                        break
                
                if time_field:
                    zone['formation_time_ecuador'] = self.convert_to_ecuador_time(time_field)
                else:
                    zone['formation_time_ecuador'] = 'Time not available'
            
            print(f"✅ {symbol}: Found {len(all_zones)} zones, showing TOP 3")
            
            return {
                'symbol': symbol,
                'success': True,
                'current_price': results.get('current_price', 0),
                'total_zones_available': len(all_zones),
                'supply_zones_count': len(supply_zones),
                'demand_zones_count': len(demand_zones),
                'top3_zones': top3_zones,
                'scan_timestamp_ecuador': self.convert_to_ecuador_time(datetime.now())
            }
            
        except Exception as e:
            print(f"❌ {symbol}: Error - {str(e)[:50]}...")
            return {
                'symbol': symbol,
                'success': False,
                'error': str(e),
                'top3_zones': []
            }
    
    def display_top3_zones_summary(self, symbol_results: Dict[str, Any]) -> None:
        """
        Display beautiful summary of TOP 3 zones for a symbol
        
        Args:
            symbol_results: Results dictionary for the symbol
        """
        try:
            symbol = symbol_results['symbol']
            
            print(f"\n🏛️ {symbol} - TOP 3 MOST RECENT ZONES 🏛️")
            print("=" * 70)
            
            if not symbol_results['success']:
                print(f"❌ Error: {symbol_results.get('error', 'Unknown error')}")
                return
            
            current_price = symbol_results.get('current_price', 0)
            total_zones = symbol_results.get('total_zones_available', 0)
            supply_count = symbol_results.get('supply_zones_count', 0)
            demand_count = symbol_results.get('demand_zones_count', 0)
            
            print(f"💰 Current Price: ${current_price:,.2f}")
            print(f"📊 Total Zones Available: {total_zones} ({supply_count}S/{demand_count}D)")
            print(f"⏰ Scan Time: {symbol_results.get('scan_timestamp_ecuador', 'N/A')}")
            
            top3_zones = symbol_results.get('top3_zones', [])
            
            if not top3_zones:
                print(f"⚠️ No zones to display")
                return
            
            print(f"\n🎯 TOP 3 MOST RECENT ZONES:")
            print("-" * 70)
            print(f"{'#':<2} {'Type':<6} {'Price Range':<25} {'Formation Time (ECT)':<25} {'Status':<8}")
            print("-" * 70)
            
            for i, zone in enumerate(top3_zones, 1):
                zone_type = zone.get('type', 'UNKNOWN')
                top_price = zone.get('top', 0)
                bottom_price = zone.get('bottom', 0)
                formation_time = zone.get('formation_time_ecuador', 'N/A')
                strength = zone.get('strength', 0)
                
                # Determine zone type from price position relative to current price
                if zone_type == 'UNKNOWN' and current_price > 0:
                    zone_center = (top_price + bottom_price) / 2
                    if zone_center > current_price:
                        zone_type = 'SUPPLY'
                    else:
                        zone_type = 'DEMAND'
                
                # Format price range and emoji
                if zone_type == 'SUPPLY':
                    price_range = f"${bottom_price:,.2f} - ${top_price:,.2f}"
                    type_emoji = "🔴"
                else:
                    price_range = f"${bottom_price:,.2f} - ${top_price:,.2f}"
                    type_emoji = "🟢"
                
                # Status based on strength
                if strength >= 8:
                    status = "STRONG"
                elif strength >= 5:
                    status = "MEDIUM"
                else:
                    status = "WEAK"
                
                print(f"{i:<2} {type_emoji}{zone_type:<5} {price_range:<25} {formation_time:<25} {status:<8}")
                
                # Additional details
                poi = zone.get('poi', (top_price + bottom_price) / 2)
                print(f"   💎 POI: ${poi:,.2f} | 💪 Strength: {strength}/10")
            
            print("-" * 70)
            
        except Exception as e:
            print(f"❌ Error displaying {symbol} zones: {e}")
    
    def scan_and_display_all_top3(self) -> None:
        """
        Scan all symbols and display TOP 3 zones for each
        """
        try:
            print(f"\n🔥⚔️ STARTING TOP 3 ZONES ANALYSIS ⚔️🔥")
            print(f"🏛️ MAGNIFICO GUERRERO DEL CÓDIGO - VISUAL CONQUEST 🏛️")
            print("=" * 80)
            
            start_time = time.time()
            total_zones_found = 0
            
            for i, symbol in enumerate(self.symbols, 1):
                print(f"\n[{i}/{len(self.symbols)}] ", end="")
                
                # Get TOP 3 zones for symbol
                symbol_results = self.get_top3_zones_for_symbol(symbol)
                
                # Display beautiful summary
                self.display_top3_zones_summary(symbol_results)
                
                if symbol_results['success']:
                    total_zones_found += len(symbol_results.get('top3_zones', []))
                
                # Small delay for rate limiting
                time.sleep(0.5)
            
            # Final summary
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"\n\n🏆 TOP 3 ZONES ANALYSIS COMPLETE! 🏆")
            print("=" * 80)
            print(f"⏱️  Total analysis time: {total_time:.2f}s")
            print(f"📊 Symbols analyzed: {len(self.symbols)}")
            print(f"🎯 Total TOP 3 zones displayed: {total_zones_found}")
            print(f"⚡ Average time per symbol: {total_time/len(self.symbols):.2f}s")
            print(f"🌍 All times shown in Ecuador Time (UTC-5)")
            
        except Exception as e:
            print(f"❌ EPIC FAIL in TOP 3 analysis: {e}")
            import traceback
            traceback.print_exc()


def main():
    """
    🔥 MAIN EXECUTION - DEPLOY THE TOP 3 VISUAL ARMY! 🔥
    """
    try:
        print("🏛️" + "=" * 78 + "🏛️")
        print("🔥" + " " * 25 + "TOP 3 ZONES VIEWER" + " " * 25 + "🔥")
        print("⚔️" + " " * 20 + "MAGNIFICO GUERRERO DEL CÓDIGO" + " " * 20 + "⚔️")
        print("🏛️" + "=" * 78 + "🏛️")
        
        # Initialize TOP 3 viewer
        viewer = Top3ZonesViewer(timeframe="1h")
        
        # Execute TOP 3 zones analysis and display
        viewer.scan_and_display_all_top3()
        
        print(f"\n🏆 VISUAL MISSION ACCOMPLISHED! 🏆")
        print(f"🎯 TOP 3 zones displayed for all symbols")
        print(f"🌍 Times converted to Ecuador timezone (UTC-5)")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ TOP 3 analysis interrupted by user")
    except Exception as e:
        print(f"❌ EPIC FAIL in main execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()