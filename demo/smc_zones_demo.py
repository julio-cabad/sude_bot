#!/usr/bin/env python3
"""
🔥 SMART MONEY CONCEPTS - EPIC ZONES DEMO 🔥
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
from core.zone_manager import ZoneManager
from core.poi_calculator import POICalculator, POICalculationConfig, POICalculationMethod
from utils.overlap_checker import OverlapChecker
from models.zone import Zone, ZoneType
from models.swing import Swing, SwingType
from models.poi import POI, POIType
from bnb.binance import RobotBinance
from config.config_manager import get_config

# Setup epic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - 🔥 %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SMCZonesDemo:
    """
    🏛️ EPIC Smart Money Concepts Zones Demo
    Demonstrates the power of our SPARTAN-level SMC system with real market data
    """
    
    def __init__(self, symbol: str = "BTCUSDT", timeframe: str = "1h"):
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        
        print(f"🔥⚔️ INITIALIZING SMC ZONES DEMO FOR {self.symbol} ⚔️🔥")
        print("=" * 80)
        
        # Initialize our EPIC components
        self.swing_detector = SwingDetector(symbol)
        
        self.zone_manager = ZoneManager(symbol)
        
        self.poi_calculator = POICalculator(
            symbol,
            POICalculationConfig(
                method=POICalculationMethod.DYNAMIC,
                enable_dynamic_adjustment=True
            )
        )
        
        self.overlap_checker = OverlapChecker(symbol)
        
        # Market data
        self.market_data: Optional[pd.DataFrame] = None
        self.zones: List[Zone] = []
        self.swings: List[Swing] = []
        self.pois: List[POI] = []
        
        print(f"✅ SMC Components initialized for {self.symbol}")
        print(f"🎯 Ready to detect EPIC Supply/Demand zones!")
    
    def fetch_market_data(self, limit: int = 500) -> bool:
        """
        Fetch real market data from Binance like a SPARTAN warrior
        """
        try:
            print(f"\\n📡 FETCHING REAL {self.symbol} DATA FROM BINANCE...")
            print("-" * 60)
            
            # Initialize Binance robot
            robot = RobotBinance(self.symbol, self.timeframe)
            
            # Get epic candlestick data
            self.market_data = robot.candlestick(limit=limit)
            
            if self.market_data.empty:
                raise ValueError(f"No data received for {self.symbol}")
            
            # Display market info like a TITAN
            print(f"✅ EPIC SUCCESS! Fetched {len(self.market_data)} candles")
            print(f"📅 Date range: {self.market_data.index[0]} to {self.market_data.index[-1]}")
            print(f"💰 Price range: ${self.market_data['low'].min():,.2f} - ${self.market_data['high'].max():,.2f}")
            print(f"📈 Current price: ${self.market_data['close'].iloc[-1]:,.2f}")
            print(f"📊 Volume range: {self.market_data['volume'].min():,.0f} - {self.market_data['volume'].max():,.0f}")
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in fetching market data: {e}")
            return False
    
    def detect_swings(self) -> bool:
        """
        Detect swing points like a SPARTAN detecting enemy movements
        """
        try:
            print(f"\\n⚔️ DETECTING SWING POINTS WITH SPARTAN PRECISION...")
            print("-" * 60)
            
            start_time = time.time()
            
            # Detect swings with our EPIC detector
            self.swings = self.swing_detector.detect_swings(self.market_data)
            
            detection_time = time.time() - start_time
            
            if not self.swings:
                print("⚠️ No swings detected - market might be too flat")
                return False
            
            # Analyze swing results like a TITAN
            high_swings = [s for s in self.swings if s.swing_type == SwingType.HIGH]
            low_swings = [s for s in self.swings if s.swing_type == SwingType.LOW]
            recent_swings = sorted(self.swings, key=lambda s: s.timestamp)[-5:]
            
            for i, swing in enumerate(recent_swings):
                swing_emoji = "🔺" if swing.swing_type == SwingType.HIGH else "🔻"
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in swing detection: {e}")
            return False
    
    def create_zones(self) -> bool:
        """
        Create Supply/Demand zones like a SPARTAN building fortifications
        """
        try:
            print(f"\\n🏛️ CREATING SUPPLY/DEMAND ZONES WITH TITAN POWER...")
            print("-" * 60)
            
            start_time = time.time()
            
            # Create zones from swings
            self.zones = []
            
            for swing in self.swings:
                try:
                    if swing.swing_type == SwingType.HIGH:
                        # Create supply zone
                        zone = self.zone_manager.create_supply_zone(
                            swing, self.market_data
                        )
                    else:
                        # Create demand zone
                        zone = self.zone_manager.create_demand_zone(
                            swing, self.market_data
                        )
                    
                    if zone:
                        self.zones.append(zone)
                        
                except Exception as e:
                    logger.debug(f"Error creating zone from swing: {e}")
                    continue
            
            creation_time = time.time() - start_time
            
            if not self.zones:
                print("⚠️ No zones created - might need different parameters")
                return False
            
            # Filter overlapping zones like a SPARTAN strategist
            print(f"🔍 FILTERING OVERLAPPING ZONES...")
            
            original_count = len(self.zones)
            self.zones = self.overlap_checker.resolve_overlaps(
                self.zones, 
                resolution_strategy="keep_strongest"
            )
            
            # Analyze zone results like a TITAN
            supply_zones = [z for z in self.zones if z.zone_type == ZoneType.SUPPLY]
            demand_zones = [z for z in self.zones if z.zone_type == ZoneType.DEMAND]
            
            print(f"🎯 EPIC ZONE CREATION COMPLETE!")
            print(f"   ⏱️  Creation time: {creation_time:.3f}s")
            print(f"   📊 Original zones: {original_count}")
            print(f"   🔧 Filtered zones: {len(self.zones)}")
            print(f"   🔺 Supply zones: {len(supply_zones)}")
            print(f"   🔻 Demand zones: {len(demand_zones)}")
            
            # Show zone details like a GLADIATOR
            print(f"\\n🏛️ ZONE ANALYSIS:")
            
            current_price = float(self.market_data['close'].iloc[-1])
            
            print(f"\\n🔺 SUPPLY ZONES (Resistance):")
            for i, zone in enumerate(supply_zones[:5]):  # Top 5
                distance_pct = ((zone.bottom - current_price) / current_price) * 100
                print(f"   {i+1}. ${zone.bottom:,.2f} - ${zone.top:,.2f}")
                print(f"      📏 Distance: {distance_pct:+.2f}% from current price")
                print(f"      📊 Height: ${zone.top - zone.bottom:,.2f}")
                print(f"      🎯 POI: ${zone.poi:,.2f}")
            
            print(f"\\n🔻 DEMAND ZONES (Support):")
            for i, zone in enumerate(demand_zones[:5]):  # Top 5
                distance_pct = ((zone.top - current_price) / current_price) * 100
                print(f"   {i+1}. ${zone.bottom:,.2f} - ${zone.top:,.2f}")
                print(f"      📏 Distance: {distance_pct:+.2f}% from current price")
                print(f"      📊 Height: ${zone.top - zone.bottom:,.2f}")
                print(f"      🎯 POI: ${zone.poi:,.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in zone creation: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def calculate_pois(self) -> bool:
        """
        Calculate Points of Interest like a SPARTAN calculating battle positions
        """
        try:
            print(f"\\n🎯 CALCULATING POINTS OF INTEREST WITH DIVINE PRECISION...")
            print("-" * 60)
            
            start_time = time.time()
            
            # Calculate POIs for all zones
            self.pois = self.poi_calculator.update_poi_levels(self.zones, self.market_data)
            
            calculation_time = time.time() - start_time
            
            if not self.pois:
                print("⚠️ No POIs calculated")
                return False
            
            # Analyze POI results like a TITAN
            supply_pois = [p for p in self.pois if p.poi_type == POIType.SUPPLY_POI]
            demand_pois = [p for p in self.pois if p.poi_type == POIType.DEMAND_POI]
        
            
            # Show POI details like a GLADIATOR
            current_price = float(self.market_data['close'].iloc[-1])
            
            # Get nearest POIs
            nearest_pois = self.poi_calculator.get_nearest_poi_levels(current_price, max_distance_pct=10.0)
            
            for i, poi in enumerate(nearest_pois['above'][:5]):
                distance = poi.get_distance_from_price(current_price)
            print(f"\\n🔻 SUPPORT POIs (Below current price):")
            for i, poi in enumerate(nearest_pois['below'][:5]):
                distance = poi.get_distance_from_price(current_price)
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in POI calculation: {e}")
            return False
    
    def create_epic_chart(self, save_path: str = "demo/smc_zones_chart.png") -> bool:
        """
        Create an EPIC chart visualization worthy of the GODS
        """
        try:
            print(f"\\n🎨 CREATING EPIC CHART VISUALIZATION...")
            print("-" * 60)
            
            # Create figure with TITAN-sized dimensions
            fig, ax = plt.subplots(figsize=(20, 12))
            fig.patch.set_facecolor('black')
            ax.set_facecolor('black')
            
            # Plot candlestick data like a SPARTAN
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
            
            # Plot EPIC Supply Zones
            supply_zones = [z for z in self.zones if z.zone_type == ZoneType.SUPPLY]
            for zone in supply_zones:
                # Find zone position on chart
                zone_start = 0
                zone_end = len(dates) - 1
                
                # Create supply zone rectangle
                zone_rect = patches.Rectangle(
                    (zone_start, zone.bottom), 
                    zone_end - zone_start, 
                    zone.top - zone.bottom,
                    linewidth=2, 
                    edgecolor='#ff6b6b', 
                    facecolor='#ff6b6b', 
                    alpha=0.3,
                    label='Supply Zone'
                )
                ax.add_patch(zone_rect)
                
                # Add POI line
                ax.axhline(y=zone.poi, color='#ff6b6b', linestyle='--', linewidth=2, alpha=0.8)
            
            # Plot EPIC Demand Zones
            demand_zones = [z for z in self.zones if z.zone_type == ZoneType.DEMAND]
            for zone in demand_zones:
                # Find zone position on chart
                zone_start = 0
                zone_end = len(dates) - 1
                
                # Create demand zone rectangle
                zone_rect = patches.Rectangle(
                    (zone_start, zone.bottom), 
                    zone_end - zone_start, 
                    zone.top - zone.bottom,
                    linewidth=2, 
                    edgecolor='#4ecdc4', 
                    facecolor='#4ecdc4', 
                    alpha=0.3,
                    label='Demand Zone'
                )
                ax.add_patch(zone_rect)
                
                # Add POI line
                ax.axhline(y=zone.poi, color='#4ecdc4', linestyle='--', linewidth=2, alpha=0.8)
            
            # Plot EPIC Swing Points
            for swing in self.swings:
                # Find swing position on chart
                swing_idx = None
                for i, date in enumerate(dates):
                    if abs((date - swing.timestamp).total_seconds()) < 3600:  # Within 1 hour
                        swing_idx = i
                        break
                
                if swing_idx is not None:
                    if swing.swing_type == SwingType.HIGH:
                        ax.scatter(swing_idx, swing.price, color='#ff6b6b', s=100, marker='^', 
                                 edgecolors='white', linewidth=2, zorder=5)
                    else:
                        ax.scatter(swing_idx, swing.price, color='#4ecdc4', s=100, marker='v', 
                                 edgecolors='white', linewidth=2, zorder=5)
            
            # EPIC styling worthy of the GODS
            ax.set_title(f'🔥 SMART MONEY CONCEPTS - {self.symbol} ZONES 🔥\\n'
                        f'⚔️ SPARTAN-LEVEL SUPPLY/DEMAND ANALYSIS ⚔️', 
                        fontsize=20, color='white', fontweight='bold', pad=20)
            
            ax.set_xlabel('Time', fontsize=14, color='white')
            ax.set_ylabel('Price (USDT)', fontsize=14, color='white')
            
            # Style the axes like a TITAN
            ax.tick_params(colors='white', labelsize=12)
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            
            # Add current price line
            current_price = float(self.market_data['close'].iloc[-1])
            ax.axhline(y=current_price, color='yellow', linestyle='-', linewidth=3, 
                      label=f'Current Price: ${current_price:,.2f}')
            
            # Add EPIC legend
            legend_elements = [
                patches.Patch(color='#ff6b6b', alpha=0.5, label='Supply Zones (Resistance)'),
                patches.Patch(color='#4ecdc4', alpha=0.5, label='Demand Zones (Support)'),
                plt.Line2D([0], [0], color='yellow', linewidth=3, label=f'Current Price: ${current_price:,.2f}'),
                plt.Line2D([0], [0], color='#ff6b6b', linestyle='--', label='Supply POI'),
                plt.Line2D([0], [0], color='#4ecdc4', linestyle='--', label='Demand POI')
            ]
            
            ax.legend(handles=legend_elements, loc='upper left', fontsize=12, 
                     facecolor='black', edgecolor='white', labelcolor='white')
            
            # Add EPIC statistics box
            stats_text = f"""📊 EPIC SMC STATISTICS:
🔺 Supply Zones: {len(supply_zones)}
🔻 Demand Zones: {len(demand_zones)}
⚔️ Total Swings: {len(self.swings)}
🎯 Total POIs: {len(self.pois)}
📈 Price Range: ${self.market_data['low'].min():,.0f} - ${self.market_data['high'].max():,.0f}
⏰ Timeframe: {self.timeframe}"""
            
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=11,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='black', 
                   edgecolor='white', alpha=0.8), color='white')
            
            # Set x-axis labels to show dates
            num_ticks = min(10, len(dates))
            tick_indices = np.linspace(0, len(dates)-1, num_ticks, dtype=int)
            ax.set_xticks(tick_indices)
            ax.set_xticklabels([dates[i].strftime('%m-%d %H:%M') for i in tick_indices], 
                              rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Save the EPIC chart
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='black')
            
            print(f"🎨 EPIC CHART CREATED!")
            print(f"   💾 Saved to: {save_path}")
            print(f"   📊 Resolution: 300 DPI")
            print(f"   🎯 Zones plotted: {len(self.zones)}")
            print(f"   ⚔️ Swings plotted: {len(self.swings)}")
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in chart creation: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_epic_demo(self) -> bool:
        """
        Run the complete EPIC SMC Zones Demo worthy of the TITANS
        """
        try:
            print(f"\\n🔥⚔️ STARTING EPIC SMC ZONES DEMO ⚔️🔥")
            print("🏛️ PREPARE TO WITNESS THE POWER OF THE SPARTAN GODS! 🏛️")
            print("=" * 80)
            
            demo_start_time = time.time()
            
            # Step 1: Fetch market data like a SPARTAN scout
            if not self.fetch_market_data():
                return False
            
            # Step 2: Detect swings like a SPARTAN warrior
            if not self.detect_swings():
                return False
            
            # Step 3: Create zones like a SPARTAN strategist
            if not self.create_zones():
                return False
            
            # Step 4: Calculate POIs like a SPARTAN mathematician
            if not self.calculate_pois():
                return False
            
            # Step 5: Create EPIC visualization
            if not self.create_epic_chart():
                return False
            
            demo_time = time.time() - demo_start_time
            
            # EPIC FINAL SUMMARY
            print(f"\\n🏆 EPIC SMC ZONES DEMO COMPLETE! 🏆")
            print("=" * 80)
            print(f"⏱️  Total demo time: {demo_time:.3f}s")
            print(f"📊 Market data: {len(self.market_data)} candles")
            print(f"⚔️ Swings detected: {len(self.swings)}")
            print(f"🏛️ Zones created: {len(self.zones)}")
            print(f"🎯 POIs calculated: {len(self.pois)}")
            
            current_price = float(self.market_data['close'].iloc[-1])
            
            # Show key levels
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
            
            print(f"\\n🔥 THE TITANS THEMSELVES WOULD BE PROUD! 🔥")
            print(f"⚔️ SPARTAN CODE QUALITY: LEGENDARY ⚔️")
            print("🏛️ READY FOR CRYPTO DOMINATION! 🏛️")
            
            return True
            
        except Exception as e:
            print(f"❌ EPIC FAIL in demo execution: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """
    Main function to run the EPIC SMC Zones Demo
    """
    print("🔥⚔️🏛️ SMART MONEY CONCEPTS - ZONES DEMO 🏛️⚔️🔥")
    print("=" * 80)
    print("🎯 Created by the SPARTAN GODS of Code")
    print("⚔️ Powered by Real Binance Data")
    print("🏛️ Worthy of the TITANS themselves!")
    print("=" * 80)
    
    # Check credentials
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ EPIC FAIL: Binance API credentials not found!")
        print("🔧 Set BINANCE_API_KEY and BINANCE_API_SECRET in .env file")
        return
    
    # Create and run EPIC demo
    demo = SMCZonesDemo("BTCUSDT", "1h")
    
    success = demo.run_epic_demo()
    
    if success:
        print(f"\\n🎉 DEMO COMPLETED SUCCESSFULLY! 🎉")
        print(f"📊 Check the generated chart: demo/smc_zones_chart.png")
    else:
        print(f"\\n💥 DEMO FAILED - But even SPARTANS face setbacks!")
    
    print("\\n🔥 MAY THE GODS OF CODE BE WITH YOU! 🔥")


if __name__ == "__main__":
    main()