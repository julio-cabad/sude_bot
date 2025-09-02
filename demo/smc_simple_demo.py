#!/usr/bin/env python3
"""
🔥 SMART MONEY CONCEPTS - SIMPLE EPIC DEMO 🔥
Professional Supply/Demand Zone Detection with Real Binance Data
Created by the SPARTAN GODS of Code - A demonstration worthy of the TITANS!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Any, Optional

# Our EPIC SMC Components
from core.swing_detector import SwingDetector
from core.poi_calculator import POICalculator, POICalculationConfig, POICalculationMethod
from models.zone import Zone, ZoneType
from models.swing import SwingType
from models.poi import POI, POIType
from bnb.binance import RobotBinance
from config.config_manager import get_config

# Setup epic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - 🔥 %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleSMCDemo:
    """
    🏛️ SIMPLE but EPIC Smart Money Concepts Demo
    Shows swing detection and manual zone creation with real market data
    """
    
    def __init__(self, symbol: str = "BTCUSDT", timeframe: str = "1h"):
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        
        print(f"🔥⚔️ INITIALIZING SIMPLE SMC DEMO FOR {self.symbol} ⚔️🔥")
        print("=" * 80)
        
        # Initialize our EPIC components
        self.swing_detector = SwingDetector(symbol)
        self.poi_calculator = POICalculator(
            symbol,
            POICalculationConfig(method=POICalculationMethod.FIBONACCI)
        )
        
        # Data storage
        self.market_data: Optional[pd.DataFrame] = None
        self.swings: List = []
        self.zones: List[Zone] = []
        self.pois: List[POI] = []
        
        print(f"✅ SMC Components initialized for {self.symbol}")
    
    def fetch_market_data(self, limit: int = 300) -> bool:
        """Fetch real market data from Binance"""
        try:
            print(f"\\n📡 FETCHING REAL {self.symbol} DATA FROM BINANCE...")
            print("-" * 60)
            
            robot = RobotBinance(self.symbol, self.timeframe)
            self.market_data = robot.candlestick(limit=limit)
            
            if self.market_data.empty:
                raise ValueError(f"No data received for {self.symbol}")
            
            print(f"✅ EPIC SUCCESS! Fetched {len(self.market_data)} candles")
            print(f"📅 Date range: {self.market_data.index[0]} to {self.market_data.index[-1]}")
            print(f"💰 Price range: ${self.market_data['low'].min():,.2f} - ${self.market_data['high'].max():,.2f}")
            print(f"📈 Current price: ${self.market_data['close'].iloc[-1]:,.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in fetching market data: {e}")
            return False
    
    def detect_swings(self) -> bool:
        """Detect swing points"""
        try:
            print(f"\\n⚔️ DETECTING SWING POINTS WITH SPARTAN PRECISION...")
            print("-" * 60)
            
            start_time = time.time()
            self.swings = self.swing_detector.detect_swings(self.market_data)
            detection_time = time.time() - start_time
            
            if not self.swings:
                print("⚠️ No swings detected")
                return False
            
            high_swings = [s for s in self.swings if s.swing_type == SwingType.HIGH]
            low_swings = [s for s in self.swings if s.swing_type == SwingType.LOW]
            
            # Show recent swings
            print(f"\\n🏛️ RECENT SWING POINTS (Last 5):")
            recent_swings = sorted(self.swings, key=lambda s: s.timestamp)[-5:]
            
            for i, swing in enumerate(recent_swings):
                swing_emoji = "🔺" if swing.swing_type == SwingType.HIGH else "🔻"
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in swing detection: {e}")
            return False
    
    def create_manual_zones(self) -> bool:
        """Create zones manually from swing data"""
        try:
            print(f"\\n🏛️ CREATING MANUAL SUPPLY/DEMAND ZONES...")
            print("-" * 60)
            
            if not self.swings:
                print("⚠️ No swings available for zone creation")
                return False
            
            # Get price statistics for zone sizing
            price_range = self.market_data['high'].max() - self.market_data['low'].min()
            zone_height = price_range * 0.02  # 2% of price range
            
            # Create zones from significant swings
            # Get all swing prices and sort them
            all_prices = [s.price for s in self.swings]
            all_prices.sort()
            
            # Take top 25% as supply zones and bottom 25% as demand zones
            num_zones = min(5, len(all_prices) // 4)
            if num_zones == 0:
                num_zones = min(3, len(all_prices))
            
            high_prices = sorted(all_prices, reverse=True)[:num_zones]
            low_prices = sorted(all_prices)[:num_zones]
            
            # Find swings corresponding to these prices
            high_swings = []
            low_swings = []
            
            for swing in self.swings:
                if swing.price in high_prices:
                    high_swings.append(swing)
                elif swing.price in low_prices:
                    low_swings.append(swing)
            
            # Create supply zones from highest swings
            for i, swing in enumerate(high_swings[:5]):  # Top 5 highs
                zone = Zone(
                    zone_id=f"supply_{i+1}",
                    zone_type=ZoneType.SUPPLY,
                    top=swing.price + (zone_height * 0.3),
                    bottom=swing.price - (zone_height * 0.7),
                    poi=swing.price,
                    left_time=swing.timestamp,
                    right_time=self.market_data.index[-1],
                    left_bar_index=0,
                    right_bar_index=len(self.market_data)-1,
                    atr_buffer=zone_height,
                    swing_price=swing.price,
                    is_active=True,
                    text_label="SUPPLY"
                )
                self.zones.append(zone)
            
            # Create demand zones from lowest swings
            for i, swing in enumerate(low_swings[:5]):  # Bottom 5 lows
                zone = Zone(
                    zone_id=f"demand_{i+1}",
                    zone_type=ZoneType.DEMAND,
                    top=swing.price + (zone_height * 0.7),
                    bottom=swing.price - (zone_height * 0.3),
                    poi=swing.price,
                    left_time=swing.timestamp,
                    right_time=self.market_data.index[-1],
                    left_bar_index=0,
                    right_bar_index=len(self.market_data)-1,
                    atr_buffer=zone_height,
                    swing_price=swing.price,
                    is_active=True,
                    text_label="DEMAND"
                )
                self.zones.append(zone)
            
            supply_zones = [z for z in self.zones if z.zone_type == ZoneType.SUPPLY]
            demand_zones = [z for z in self.zones if z.zone_type == ZoneType.DEMAND]
            
            print(f"🎯 EPIC ZONE CREATION COMPLETE!")
            print(f"   📊 Total zones: {len(self.zones)}")
            print(f"   🔺 Supply zones: {len(supply_zones)}")
            print(f"   🔻 Demand zones: {len(demand_zones)}")
            
            # Show zone details
            current_price = float(self.market_data['close'].iloc[-1])
            
            print(f"\\n🔺 SUPPLY ZONES (Resistance):")
            for i, zone in enumerate(supply_zones):
                distance_pct = ((zone.poi - current_price) / current_price) * 100
                print(f"   {i+1}. ${zone.bottom:,.2f} - ${zone.top:,.2f}")
                print(f"      📏 Distance: {distance_pct:+.2f}% from current price")
                print(f"      🎯 POI: ${zone.poi:,.2f}")
            
            print(f"\\n🔻 DEMAND ZONES (Support):")
            for i, zone in enumerate(demand_zones):
                distance_pct = ((zone.poi - current_price) / current_price) * 100
                print(f"   {i+1}. ${zone.bottom:,.2f} - ${zone.top:,.2f}")
                print(f"      📏 Distance: {distance_pct:+.2f}% from current price")
                print(f"      🎯 POI: ${zone.poi:,.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in zone creation: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def calculate_pois(self) -> bool:
        """Calculate POIs for zones"""
        try:
            print(f"\\n🎯 CALCULATING POINTS OF INTEREST...")
            print("-" * 60)
            
            if not self.zones:
                print("⚠️ No zones available for POI calculation")
                return False
            
            start_time = time.time()
            self.pois = self.poi_calculator.update_poi_levels(self.zones, self.market_data)
            calculation_time = time.time() - start_time
            
            supply_pois = [p for p in self.pois if p.poi_type == POIType.SUPPLY_POI]
            demand_pois = [p for p in self.pois if p.poi_type == POIType.DEMAND_POI]
            
            # Show POI details
            current_price = float(self.market_data['close'].iloc[-1])
            
            print(f"\\n🎯 KEY POI LEVELS:")
            for poi in self.pois[:10]:  # Top 10 POIs
                distance = poi.get_distance_from_price(current_price)
                poi_emoji = "🔺" if poi.poi_type == POIType.SUPPLY_POI else "🔻"
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in POI calculation: {e}")
            return False
    
    def create_epic_chart(self, save_path: str = "demo/simple_smc_chart.png") -> bool:
        """Create epic chart visualization"""
        try:
            print(f"\\n🎨 CREATING EPIC CHART VISUALIZATION...")
            print("-" * 60)
            
            # Create figure
            fig, ax = plt.subplots(figsize=(16, 10))
            fig.patch.set_facecolor('black')
            ax.set_facecolor('black')
            
            # Plot candlestick data
            dates = self.market_data.index
            opens = self.market_data['open']
            highs = self.market_data['high']
            lows = self.market_data['low']
            closes = self.market_data['close']
            
            # Plot price action
            for i in range(len(dates)):
                color = '#00ff00' if closes.iloc[i] >= opens.iloc[i] else '#ff0000'
                
                # High-low line
                ax.plot([i, i], [lows.iloc[i], highs.iloc[i]], color=color, linewidth=1)
                
                # Body
                body_height = abs(closes.iloc[i] - opens.iloc[i])
                body_bottom = min(opens.iloc[i], closes.iloc[i])
                
                rect = patches.Rectangle(
                    (i-0.3, body_bottom), 0.6, body_height,
                    linewidth=1, edgecolor=color, facecolor=color, alpha=0.8
                )
                ax.add_patch(rect)
            
            # Plot Supply Zones
            supply_zones = [z for z in self.zones if z.zone_type == ZoneType.SUPPLY]
            for zone in supply_zones:
                zone_rect = patches.Rectangle(
                    (0, zone.bottom), 
                    len(dates) - 1, 
                    zone.top - zone.bottom,
                    linewidth=2, 
                    edgecolor='#ff6b6b', 
                    facecolor='#ff6b6b', 
                    alpha=0.3
                )
                ax.add_patch(zone_rect)
                ax.axhline(y=zone.poi, color='#ff6b6b', linestyle='--', linewidth=2, alpha=0.8)
            
            # Plot Demand Zones
            demand_zones = [z for z in self.zones if z.zone_type == ZoneType.DEMAND]
            for zone in demand_zones:
                zone_rect = patches.Rectangle(
                    (0, zone.bottom), 
                    len(dates) - 1, 
                    zone.top - zone.bottom,
                    linewidth=2, 
                    edgecolor='#4ecdc4', 
                    facecolor='#4ecdc4', 
                    alpha=0.3
                )
                ax.add_patch(zone_rect)
                ax.axhline(y=zone.poi, color='#4ecdc4', linestyle='--', linewidth=2, alpha=0.8)
            
            # Plot Swing Points
            for swing in self.swings:
                swing_idx = None
                for i, date in enumerate(dates):
                    if abs((date - swing.timestamp).total_seconds()) < 3600:
                        swing_idx = i
                        break
                
                if swing_idx is not None:
                    if swing.swing_type == SwingType.HIGH:
                        ax.scatter(swing_idx, swing.price, color='#ff6b6b', s=80, marker='^', 
                                 edgecolors='white', linewidth=2, zorder=5)
                    else:
                        ax.scatter(swing_idx, swing.price, color='#4ecdc4', s=80, marker='v', 
                                 edgecolors='white', linewidth=2, zorder=5)
            
            # Styling
            ax.set_title(f'🔥 SMART MONEY CONCEPTS - {self.symbol} 🔥\\n'
                        f'⚔️ SPARTAN-LEVEL SUPPLY/DEMAND ANALYSIS ⚔️', 
                        fontsize=18, color='white', fontweight='bold', pad=20)
            
            ax.set_xlabel('Time', fontsize=12, color='white')
            ax.set_ylabel('Price (USDT)', fontsize=12, color='white')
            
            ax.tick_params(colors='white', labelsize=10)
            for spine in ax.spines.values():
                spine.set_color('white')
            
            # Current price line
            current_price = float(self.market_data['close'].iloc[-1])
            ax.axhline(y=current_price, color='yellow', linestyle='-', linewidth=3)
            
            # Legend
            legend_elements = [
                patches.Patch(color='#ff6b6b', alpha=0.5, label='Supply Zones'),
                patches.Patch(color='#4ecdc4', alpha=0.5, label='Demand Zones'),
                plt.Line2D([0], [0], color='yellow', linewidth=3, label=f'Current: ${current_price:,.2f}')
            ]
            
            ax.legend(handles=legend_elements, loc='upper left', fontsize=10, 
                     facecolor='black', edgecolor='white', labelcolor='white')
            
            # Statistics box
            stats_text = f"""📊 SMC STATISTICS:
🔺 Supply Zones: {len(supply_zones)}
🔻 Demand Zones: {len(demand_zones)}
⚔️ Total Swings: {len(self.swings)}
🎯 Total POIs: {len(self.pois)}
⏰ Timeframe: {self.timeframe}"""
            
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='black', 
                   edgecolor='white', alpha=0.8), color='white')
            
            # X-axis labels
            num_ticks = min(8, len(dates))
            tick_indices = np.linspace(0, len(dates)-1, num_ticks, dtype=int)
            ax.set_xticks(tick_indices)
            ax.set_xticklabels([dates[i].strftime('%m-%d %H:%M') for i in tick_indices], 
                              rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Save chart
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='black')
            
            print(f"🎨 EPIC CHART CREATED!")
            print(f"   💾 Saved to: {save_path}")
            print(f"   📊 Zones plotted: {len(self.zones)}")
            print(f"   ⚔️ Swings plotted: {len(self.swings)}")
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in chart creation: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_demo(self) -> bool:
        """Run the complete demo"""
        try:
            print(f"\\n🔥⚔️ STARTING SIMPLE SMC DEMO ⚔️🔥")
            print("🏛️ PREPARE TO WITNESS SPARTAN CODE POWER! 🏛️")
            print("=" * 80)
            
            demo_start_time = time.time()
            
            # Fetch data
            if not self.fetch_market_data():
                return False
            
            # Detect swings
            if not self.detect_swings():
                return False
            
            # Create zones
            if not self.create_manual_zones():
                return False
            
            # Calculate POIs
            if not self.calculate_pois():
                return False
            
            # Create chart
            if not self.create_epic_chart():
                return False
            
            demo_time = time.time() - demo_start_time
            
            # Final summary
            print(f"\\n🏆 SIMPLE SMC DEMO COMPLETE! 🏆")
            print("=" * 80)
            print(f"⏱️  Total demo time: {demo_time:.3f}s")
            print(f"📊 Market data: {len(self.market_data)} candles")
            print(f"⚔️ Swings detected: {len(self.swings)}")
            print(f"🏛️ Zones created: {len(self.zones)}")
            print(f"🎯 POIs calculated: {len(self.pois)}")
            
            current_price = float(self.market_data['close'].iloc[-1])
            supply_zones = [z for z in self.zones if z.zone_type == ZoneType.SUPPLY]
            demand_zones = [z for z in self.zones if z.zone_type == ZoneType.DEMAND]
            
            print(f"\\n🎯 KEY LEVELS FOR {self.symbol}:")
            print(f"💰 Current Price: ${current_price:,.2f}")
            
            if supply_zones:
                nearest_supply = min(supply_zones, key=lambda z: abs(z.poi - current_price))
                distance_pct = ((nearest_supply.poi - current_price) / current_price) * 100
                print(f"🔺 Nearest Resistance: ${nearest_supply.poi:,.2f} ({distance_pct:+.2f}%)")
            
            if demand_zones:
                nearest_demand = min(demand_zones, key=lambda z: abs(z.poi - current_price))
                distance_pct = ((nearest_demand.poi - current_price) / current_price) * 100
                print(f"🔻 Nearest Support: ${nearest_demand.poi:,.2f} ({distance_pct:+.2f}%)")
            
            print(f"\\n🔥 THE TITANS WOULD BE PROUD! 🔥")
            print(f"⚔️ SPARTAN CODE QUALITY: LEGENDARY ⚔️")
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in demo: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function"""
    print("🔥⚔️🏛️ SIMPLE SMC DEMO 🏛️⚔️🔥")
    print("=" * 60)
    print("🎯 Created by the SPARTAN GODS of Code")
    print("⚔️ Powered by Real Binance Data")
    print("=" * 60)
    
    # Check credentials
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ EPIC FAIL: Binance API credentials not found!")
        print("🔧 Set BINANCE_API_KEY and BINANCE_API_SECRET in .env file")
        return
    
    # Run demo
    demo = SimpleSMCDemo("BTCUSDT", "1h")
    success = demo.run_demo()
    
    if success:
        print(f"\\n🎉 DEMO COMPLETED SUCCESSFULLY! 🎉")
        print(f"📊 Check the chart: demo/simple_smc_chart.png")
    else:
        print(f"\\n💥 DEMO FAILED - But SPARTANS never give up!")
    
    print("\\n🔥 MAY THE GODS OF CODE BE WITH YOU! 🔥")


if __name__ == "__main__":
    main()