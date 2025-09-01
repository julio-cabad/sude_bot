# Clase Zone (supply/demand)
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class ZoneType(Enum):
    """Enum for zone types based on Pine Script box_type parameter"""
    SUPPLY = 1      # Equivalent to box_type == 1 in Pine Script
    DEMAND = -1     # Equivalent to box_type == -1 in Pine Script


@dataclass
class Zone:
    """
    Represents a Supply or Demand zone based on Pine Script f_supply_demand function.
    
    Equivalent to Pine Script box creation with:
    - box_top/box_bottom for zone boundaries
    - poi for Point of Interest at zone center
    - atr_buffer for zone width calculation
    """
    
    # Core zone properties
    zone_id: str
    zone_type: ZoneType
    
    # Price levels (equivalent to Pine Script box_top/box_bottom)
    top: float
    bottom: float
    poi: float  # Point of Interest - center of zone (top + bottom) / 2
    
    # Time boundaries (equivalent to Pine Script box_left/box_right)
    left_time: datetime     # When zone was created (swing point time)
    right_time: datetime    # Current time or extension
    left_bar_index: int     # Bar index when zone was created
    right_bar_index: int    # Current bar index
    
    # Zone characteristics
    atr_buffer: float       # ATR-based buffer used for zone width
    swing_price: float      # Original swing high/low price that created the zone
    
    # Zone status
    is_active: bool = True
    is_broken: bool = False
    break_time: Optional[datetime] = None
    break_bar_index: Optional[int] = None
    break_price: Optional[float] = None
    
    # Visual properties (from Pine Script visual settings)
    text_label: str = ""    # "SUPPLY" or "DEMAND"
    
    def __post_init__(self):
        """Initialize zone after creation"""
        if not self.zone_id:
            self.zone_id = str(uuid.uuid4())
        
        # Set default text label based on zone type
        if not self.text_label:
            self.text_label = "SUPPLY" if self.zone_type == ZoneType.SUPPLY else "DEMAND"
    
    @classmethod
    def create_supply_zone(
        cls,
        swing_price: float,
        swing_time: datetime,
        swing_bar_index: int,
        atr_buffer: float,
        current_time: datetime,
        current_bar_index: int
    ) -> 'Zone':
        """
        Create a supply zone from a swing high.
        Equivalent to Pine Script: box_type == 1 logic in f_supply_demand
        """
        # Pine Script logic: box_top := array.get(value_array, 0)
        #                   box_bottom := box_top - atr_buffer
        top = swing_price
        bottom = swing_price - atr_buffer
        poi = (top + bottom) / 2
        
        return cls(
            zone_id="",  # Will be generated in __post_init__
            zone_type=ZoneType.SUPPLY,
            top=top,
            bottom=bottom,
            poi=poi,
            left_time=swing_time,
            right_time=current_time,
            left_bar_index=swing_bar_index,
            right_bar_index=current_bar_index,
            atr_buffer=atr_buffer,
            swing_price=swing_price,
            text_label="SUPPLY"
        )
    
    @classmethod
    def create_demand_zone(
        cls,
        swing_price: float,
        swing_time: datetime,
        swing_bar_index: int,
        atr_buffer: float,
        current_time: datetime,
        current_bar_index: int
    ) -> 'Zone':
        """
        Create a demand zone from a swing low.
        Equivalent to Pine Script: box_type == -1 logic in f_supply_demand
        """
        # Pine Script logic: box_bottom := array.get(value_array, 0)
        #                   box_top := box_bottom + atr_buffer
        bottom = swing_price
        top = swing_price + atr_buffer
        poi = (top + bottom) / 2
        
        return cls(
            zone_id="",  # Will be generated in __post_init__
            zone_type=ZoneType.DEMAND,
            top=top,
            bottom=bottom,
            poi=poi,
            left_time=swing_time,
            right_time=current_time,
            left_bar_index=swing_bar_index,
            right_bar_index=current_bar_index,
            atr_buffer=atr_buffer,
            swing_price=swing_price,
            text_label="DEMAND"
        )
    
    def mark_as_broken(self, break_price: float, break_time: datetime, break_bar_index: int):
        """
        Mark zone as broken when price breaks through.
        Equivalent to Pine Script f_sd_to_bos function logic
        """
        self.is_broken = True
        self.is_active = False
        self.break_price = break_price
        self.break_time = break_time
        self.break_bar_index = break_bar_index
    
    def update_right_boundary(self, new_time: datetime, new_bar_index: int):
        """Update the right boundary of the zone (extension)"""
        self.right_time = new_time
        self.right_bar_index = new_bar_index
    
    def is_price_in_zone(self, price: float) -> bool:
        """Check if a price is within the zone boundaries"""
        return self.bottom <= price <= self.top
    
    def get_zone_height(self) -> float:
        """Get the height of the zone"""
        return self.top - self.bottom
    
    def get_zone_midpoint(self) -> float:
        """Get the midpoint of the zone (same as POI)"""
        return self.poi
    
    def __str__(self) -> str:
        status = "BROKEN" if self.is_broken else "ACTIVE"
        return f"{self.zone_type.name} Zone [{status}]: {self.bottom:.4f} - {self.top:.4f} (POI: {self.poi:.4f})"