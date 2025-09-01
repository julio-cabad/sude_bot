#!/usr/bin/env python3
"""
🔥⚔️ ALERT MANAGER - IMPLACABLE ALERT SYSTEM ⚔️🔥
Manages alert generation, formatting, and display
Created by KRATOS - ALERT WARRIOR
"""

import sys
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum
import pytz

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.zone_alert import ZoneAlert, AlertType, AlertPriority, AlertHistory
from models.zone import Zone, ZoneType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertColor(Enum):
    """Color codes for terminal output"""
    RED = '\033[91m'      # Supply zones
    GREEN = '\033[92m'    # Demand zones
    YELLOW = '\033[93m'   # Warnings
    BLUE = '\033[94m'     # Info
    PURPLE = '\033[95m'   # Headers
    CYAN = '\033[96m'     # Highlights
    WHITE = '\033[97m'    # Normal text
    BOLD = '\033[1m'      # Bold text
    UNDERLINE = '\033[4m' # Underlined text
    END = '\033[0m'       # Reset color


@dataclass
class AlertDisplayConfig:
    """Configuration for alert display"""
    show_colors: bool = True
    show_timestamps: bool = True
    timezone: str = "UTC"
    max_zones_per_alert: int = 2
    alert_duration_seconds: int = 10
    use_emojis: bool = True
    compact_mode: bool = False


class AlertManager:
    """
    🚨 ALERT MANAGER - Implacable alert generation and display
    Handles creation, formatting, and display of zone alerts
    """
    
    def __init__(self, config: Optional[AlertDisplayConfig] = None):
        """
        Initialize alert manager
        
        Args:
            config: Display configuration (uses defaults if None)
        """
        self.config = config or AlertDisplayConfig()
        self.alert_history = AlertHistory()
        
        # Set up timezone
        try:
            self.timezone = pytz.timezone(self.config.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"⚠️ Unknown timezone: {self.config.timezone}, using UTC")
            self.timezone = pytz.UTC
        
        logger.info(f"🚨 AlertManager initialized:")
        logger.info(f"   Colors: {'ON' if self.config.show_colors else 'OFF'}")
        logger.info(f"   Timezone: {self.config.timezone}")
        logger.info(f"   Max zones per alert: {self.config.max_zones_per_alert}")
        logger.info(f"   Emojis: {'ON' if self.config.use_emojis else 'OFF'}")
    
    def generate_alert(self, new_zones: List[Zone], symbol: str, timeframe: str,
                      detection_time: Optional[datetime] = None) -> ZoneAlert:
        """
        Generate alert from new zones
        
        Args:
            new_zones: List of newly detected zones
            symbol: Trading symbol
            timeframe: Timeframe being monitored
            detection_time: When zones were detected (defaults to now)
            
        Returns:
            ZoneAlert: Generated alert object
        """
        try:
            if detection_time is None:
                detection_time = datetime.now()
            
            # Create alert
            alert = ZoneAlert(
                symbol=symbol.upper(),
                timeframe=timeframe,
                new_zones=new_zones,
                detection_time=detection_time
            )
            
            # Add to history
            self.alert_history.add_alert(alert)
            
            logger.debug(f"🚨 Generated alert for {symbol}: {len(new_zones)} new zones")
            
            return alert
            
        except Exception as e:
            logger.error(f"❌ Failed to generate alert for {symbol}: {e}")
            raise
    
    def display_alert(self, alert: ZoneAlert) -> None:
        """
        Display alert in console with formatting
        
        Args:
            alert: Alert to display
        """
        try:
            # Get zones to display (limit to max_zones_per_alert)
            zones_to_show = alert.get_most_recent_zones(self.config.max_zones_per_alert)
            
            if self.config.compact_mode:
                self._display_compact_alert(alert, zones_to_show)
            else:
                self._display_full_alert(alert, zones_to_show)
            
        except Exception as e:
            logger.error(f"❌ Failed to display alert: {e}")
    
    def _display_full_alert(self, alert: ZoneAlert, zones: List[Zone]) -> None:
        """Display full formatted alert"""
        # Header
        header = self._format_alert_header(alert)
        print(header)
        
        # Zone details
        for i, zone in enumerate(zones, 1):
            zone_info = self._format_zone_info(zone, i)
            print(zone_info)
        
        # Footer
        footer = self._format_alert_footer(alert)
        print(footer)
        print()  # Empty line for separation
    
    def _display_compact_alert(self, alert: ZoneAlert, zones: List[Zone]) -> None:
        """Display compact alert (single line)"""
        timestamp = self._format_timestamp(alert.detection_time)
        zone_summary = self._format_zone_summary(zones)
        
        compact_msg = f"{timestamp} 🚨 {alert.symbol} ({alert.timeframe}): {zone_summary}"
        
        if self.config.show_colors:
            compact_msg = f"{AlertColor.CYAN.value}{compact_msg}{AlertColor.END.value}"
        
        print(compact_msg)
    
    def _format_alert_header(self, alert: ZoneAlert) -> str:
        """Format alert header"""
        emoji = "🚨" if self.config.use_emojis else ""
        timestamp = self._format_timestamp(alert.detection_time)
        
        # Priority indicator
        priority_indicator = ""
        if alert.priority == AlertPriority.HIGH:
            priority_indicator = "🔥" if self.config.use_emojis else "[HIGH]"
        elif alert.priority == AlertPriority.CRITICAL:
            priority_indicator = "⚡" if self.config.use_emojis else "[CRITICAL]"
        
        header = f"{emoji} NEW ZONE ALERT {priority_indicator}"
        
        if self.config.show_colors:
            header = f"{AlertColor.BOLD.value}{AlertColor.PURPLE.value}{header}{AlertColor.END.value}"
        
        # Add symbol and timeframe info
        info_line = f"Symbol: {alert.symbol} | Timeframe: {alert.timeframe} | Time: {timestamp}"
        
        if self.config.show_colors:
            info_line = f"{AlertColor.CYAN.value}{info_line}{AlertColor.END.value}"
        
        separator = "=" * 70
        if self.config.show_colors:
            separator = f"{AlertColor.BLUE.value}{separator}{AlertColor.END.value}"
        
        return f"{separator}\\n{header}\\n{info_line}\\n{separator}"
    
    def _format_zone_info(self, zone: Zone, zone_number: int) -> str:
        """Format individual zone information"""
        # Zone type with emoji and color
        if zone.zone_type == ZoneType.SUPPLY:
            zone_emoji = "🔺" if self.config.use_emojis else ""
            zone_color = AlertColor.RED if self.config.show_colors else None
            zone_type_text = f"{zone_emoji} SUPPLY ZONE"
        else:
            zone_emoji = "🔻" if self.config.use_emojis else ""
            zone_color = AlertColor.GREEN if self.config.show_colors else None
            zone_type_text = f"{zone_emoji} DEMAND ZONE"
        
        # Apply color
        if zone_color and self.config.show_colors:
            zone_type_text = f"{zone_color.value}{AlertColor.BOLD.value}{zone_type_text}{AlertColor.END.value}"
        
        # Zone details
        poi_text = f"POI: ${zone.poi:,.2f}"
        range_text = f"Range: ${zone.bottom:,.2f} - ${zone.top:,.2f}"
        
        # Formation time
        formation_time = ""
        if zone.left_time:
            formation_time = f"Formed: {self._format_timestamp(zone.left_time)}"
        
        # Distance from current price (if available)
        distance_text = ""
        # Note: We'd need current price to calculate this, for now skip
        
        # Combine zone info
        zone_info_parts = [
            f"   {zone_number}. {zone_type_text}",
            f"      {poi_text}",
            f"      {range_text}"
        ]
        
        if formation_time:
            zone_info_parts.append(f"      {formation_time}")
        
        if distance_text:
            zone_info_parts.append(f"      {distance_text}")
        
        return "\\n".join(zone_info_parts)
    
    def _format_zone_summary(self, zones: List[Zone]) -> str:
        """Format zone summary for compact display"""
        if not zones:
            return "No zones"
        
        supply_count = sum(1 for z in zones if z.zone_type == ZoneType.SUPPLY)
        demand_count = sum(1 for z in zones if z.zone_type == ZoneType.DEMAND)
        
        parts = []
        if supply_count > 0:
            emoji = "🔺" if self.config.use_emojis else ""
            parts.append(f"{supply_count} {emoji}SUPPLY")
        
        if demand_count > 0:
            emoji = "🔻" if self.config.use_emojis else ""
            parts.append(f"{demand_count} {emoji}DEMAND")
        
        return " + ".join(parts) if parts else "Unknown zones"
    
    def _format_alert_footer(self, alert: ZoneAlert) -> str:
        """Format alert footer"""
        footer_parts = [
            f"Alert ID: {alert.alert_id[:8]}",
            f"Total new zones: {len(alert.new_zones)}",
            f"Priority: {alert.priority.value}"
        ]
        
        footer = " | ".join(footer_parts)
        
        if self.config.show_colors:
            footer = f"{AlertColor.BLUE.value}{footer}{AlertColor.END.value}"
        
        separator = "=" * 70
        if self.config.show_colors:
            separator = f"{AlertColor.BLUE.value}{separator}{AlertColor.END.value}"
        
        return f"{separator}\\n{footer}"
    
    def _format_timestamp(self, dt: datetime) -> str:
        """Format timestamp for display"""
        if not self.config.show_timestamps:
            return ""
        
        try:
            # Convert to configured timezone
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            
            local_dt = dt.astimezone(self.timezone)
            return local_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to format timestamp: {e}")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def format_zone_info(self, zone: Zone) -> str:
        """
        Format zone information as string
        
        Args:
            zone: Zone to format
            
        Returns:
            str: Formatted zone information
        """
        try:
            zone_type = "SUPPLY" if zone.zone_type == ZoneType.SUPPLY else "DEMAND"
            
            info_parts = [
                f"{zone_type} Zone",
                f"POI: ${zone.poi:,.2f}",
                f"Range: ${zone.bottom:,.2f} - ${zone.top:,.2f}"
            ]
            
            if zone.left_time:
                timestamp = self._format_timestamp(zone.left_time)
                info_parts.append(f"Formed: {timestamp}")
            
            return " | ".join(info_parts)
            
        except Exception as e:
            logger.error(f"❌ Failed to format zone info: {e}")
            return f"Zone: ${zone.poi:,.2f}"
    
    def display_multiple_alerts(self, alerts: List[ZoneAlert]) -> None:
        """Display multiple alerts in sequence"""
        if not alerts:
            return
        
        print(f"\\n{AlertColor.PURPLE.value if self.config.show_colors else ''}🚨 MULTIPLE ZONE ALERTS ({len(alerts)}){AlertColor.END.value if self.config.show_colors else ''}")
        print("=" * 70)
        
        for i, alert in enumerate(alerts, 1):
            print(f"\\n--- Alert {i}/{len(alerts)} ---")
            self.display_alert(alert)
    
    def get_recent_alerts(self, limit: int = 10) -> List[ZoneAlert]:
        """Get recent alerts from history"""
        return self.alert_history.get_recent_alerts(limit)
    
    def get_alerts_for_symbol(self, symbol: str, limit: int = 10) -> List[ZoneAlert]:
        """Get recent alerts for specific symbol"""
        return self.alert_history.get_alerts_for_symbol(symbol, limit)
    
    def clear_alert_history(self) -> None:
        """Clear all alert history"""
        self.alert_history.clear_history()
        logger.info("🗑️ Alert history cleared")
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            recent_alerts = self.alert_history.get_recent_alerts(100)
            
            if not recent_alerts:
                return {
                    'total_alerts': 0,
                    'supply_alerts': 0,
                    'demand_alerts': 0,
                    'symbols': [],
                    'timeframes': [],
                    'avg_zones_per_alert': 0.0
                }
            
            # Count zone types
            supply_alerts = 0
            demand_alerts = 0
            total_zones = 0
            symbols = set()
            timeframes = set()
            
            for alert in recent_alerts:
                symbols.add(alert.symbol)
                timeframes.add(alert.timeframe)
                total_zones += len(alert.new_zones)
                
                for zone in alert.new_zones:
                    if zone.zone_type == ZoneType.SUPPLY:
                        supply_alerts += 1
                    else:
                        demand_alerts += 1
            
            return {
                'total_alerts': len(recent_alerts),
                'supply_alerts': supply_alerts,
                'demand_alerts': demand_alerts,
                'symbols': sorted(list(symbols)),
                'timeframes': sorted(list(timeframes)),
                'avg_zones_per_alert': total_zones / len(recent_alerts) if recent_alerts else 0.0,
                'total_zones': total_zones
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get alert stats: {e}")
            return {}
    
    def update_config(self, **kwargs) -> None:
        """Update display configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"🔧 Updated config: {key} = {value}")
            else:
                logger.warning(f"⚠️ Unknown config option: {key}")


# Utility functions
def create_alert_manager(timezone: str = "UTC", show_colors: bool = True) -> AlertManager:
    """Factory function to create AlertManager with custom settings"""
    config = AlertDisplayConfig(
        timezone=timezone,
        show_colors=show_colors
    )
    return AlertManager(config)


def quick_alert_display(zones: List[Zone], symbol: str, timeframe: str = "1h") -> None:
    """Quick function to display zones as alert"""
    manager = AlertManager()
    alert = manager.generate_alert(zones, symbol, timeframe)
    manager.display_alert(alert)


if __name__ == "__main__":
    # Test the alert manager
    print("🔥⚔️ TESTING ALERT MANAGER ⚔️🔥")
    print("=" * 60)
    
    # Create test alert manager
    manager = AlertManager()
    
    # Create test zones
    from models.zone import Zone
    
    test_zones = [
        Zone(
            zone_id="test_supply",
            zone_type=ZoneType.SUPPLY,
            top=67600.0,
            bottom=67400.0,
            poi=67500.0,
            left_time=datetime.now(),
            right_time=datetime.now(),
            left_bar_index=0,
            right_bar_index=0,
            atr_buffer=200.0,
            swing_price=67500.0
        ),
        Zone(
            zone_id="test_demand",
            zone_type=ZoneType.DEMAND,
            top=66600.0,
            bottom=66400.0,
            poi=66500.0,
            left_time=datetime.now(),
            right_time=datetime.now(),
            left_bar_index=0,
            right_bar_index=0,
            atr_buffer=200.0,
            swing_price=66500.0
        )
    ]
    
    # Test alert generation and display
    print("✅ Testing alert generation and display...")
    alert = manager.generate_alert(test_zones, "BTCUSDT", "1h")
    manager.display_alert(alert)
    
    # Test compact mode
    print("\\n✅ Testing compact mode...")
    manager.config.compact_mode = True
    manager.display_alert(alert)
    
    # Test stats
    stats = manager.get_alert_stats()
    print(f"\\n✅ Alert stats: {stats}")
    
    print("\\n🏆 ALERT MANAGER READY FOR BATTLE! 🏆")