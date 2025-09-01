# Clase Box para representación visual
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple
import uuid


class BoxType(Enum):
    """Enum for box types based on Pine Script box usage"""
    SUPPLY_ZONE = "SUPPLY_ZONE"      # Supply zone box
    DEMAND_ZONE = "DEMAND_ZONE"      # Demand zone box
    POI_LINE = "POI_LINE"            # POI horizontal line
    BOS_MARKER = "BOS_MARKER"        # Break of Structure marker


class TextAlign(Enum):
    """Text alignment options"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class TextVAlign(Enum):
    """Vertical text alignment options"""
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


@dataclass
class Box:
    """
    Represents a visual box element based on Pine Script box.new() function.
    
    Pine Script equivalent:
    box.new(left, top, right, bottom, border_color, bgcolor, extend, text, 
            text_halign, text_valign, text_color, text_size, xloc)
    """
    
    # Core box properties
    box_id: str
    box_type: BoxType
    
    # Position and dimensions (equivalent to Pine Script left, top, right, bottom)
    left_time: datetime
    top_price: float
    right_time: datetime
    bottom_price: float
    left_bar_index: int
    right_bar_index: int
    
    # Visual properties (from Pine Script box styling)
    border_color: str = "#FFFFFF"     # Border color (hex)
    background_color: str = "#EDEDED" # Background color (hex)
    border_width: int = 1             # Border width
    transparency: int = 70            # Transparency (0-100)
    
    # Text properties (from Pine Script text settings)
    text: str = ""                    # Box text content
    text_color: str = "#FFFFFF"       # Text color (hex)
    text_size: str = "small"          # Text size
    text_halign: TextAlign = TextAlign.CENTER    # Horizontal alignment
    text_valign: TextVAlign = TextVAlign.CENTER  # Vertical alignment
    
    # Extension properties
    extend_right: bool = True         # Extend box to the right
    extend_left: bool = False         # Extend box to the left
    
    # Box status
    is_visible: bool = True
    is_active: bool = True
    
    def __post_init__(self):
        """Initialize box after creation"""
        if not self.box_id:
            self.box_id = str(uuid.uuid4())
    
    @classmethod
    def create_supply_zone_box(
        cls,
        left_time: datetime,
        top_price: float,
        right_time: datetime,
        bottom_price: float,
        left_bar_index: int,
        right_bar_index: int,
        supply_color: str = "#EDEDED",
        outline_color: str = "#FFFFFF"
    ) -> 'Box':
        """
        Create a supply zone box.
        Equivalent to Pine Script supply zone box creation in f_supply_demand
        """
        return cls(
            box_id="",  # Will be generated in __post_init__
            box_type=BoxType.SUPPLY_ZONE,
            left_time=left_time,
            top_price=top_price,
            right_time=right_time,
            bottom_price=bottom_price,
            left_bar_index=left_bar_index,
            right_bar_index=right_bar_index,
            border_color=outline_color,
            background_color=supply_color,
            text="SUPPLY",
            text_halign=TextAlign.CENTER,
            text_valign=TextVAlign.CENTER
        )
    
    @classmethod
    def create_demand_zone_box(
        cls,
        left_time: datetime,
        top_price: float,
        right_time: datetime,
        bottom_price: float,
        left_bar_index: int,
        right_bar_index: int,
        demand_color: str = "#00FFFF",
        outline_color: str = "#FFFFFF"
    ) -> 'Box':
        """
        Create a demand zone box.
        Equivalent to Pine Script demand zone box creation in f_supply_demand
        """
        return cls(
            box_id="",  # Will be generated in __post_init__
            box_type=BoxType.DEMAND_ZONE,
            left_time=left_time,
            top_price=top_price,
            right_time=right_time,
            bottom_price=bottom_price,
            left_bar_index=left_bar_index,
            right_bar_index=right_bar_index,
            border_color=outline_color,
            background_color=demand_color,
            text="DEMAND",
            text_halign=TextAlign.CENTER,
            text_valign=TextVAlign.CENTER
        )
    
    @classmethod
    def create_poi_line(
        cls,
        left_time: datetime,
        poi_price: float,
        right_time: datetime,
        left_bar_index: int,
        right_bar_index: int,
        poi_color: str = "#FFFFFF"
    ) -> 'Box':
        """
        Create a POI horizontal line.
        Equivalent to Pine Script POI line creation in f_supply_demand
        """
        return cls(
            box_id="",  # Will be generated in __post_init__
            box_type=BoxType.POI_LINE,
            left_time=left_time,
            top_price=poi_price,
            right_time=right_time,
            bottom_price=poi_price,  # Same as top for horizontal line
            left_bar_index=left_bar_index,
            right_bar_index=right_bar_index,
            border_color=poi_color,
            background_color=poi_color,
            transparency=90,
            text="POI",
            text_halign=TextAlign.LEFT,
            text_valign=TextVAlign.CENTER
        )
    
    @classmethod
    def create_bos_marker(
        cls,
        left_time: datetime,
        bos_price: float,
        right_time: datetime,
        left_bar_index: int,
        right_bar_index: int
    ) -> 'Box':
        """
        Create a Break of Structure marker.
        Equivalent to Pine Script BOS creation in f_sd_to_bos
        """
        return cls(
            box_id="",  # Will be generated in __post_init__
            box_type=BoxType.BOS_MARKER,
            left_time=left_time,
            top_price=bos_price,
            right_time=right_time,
            bottom_price=bos_price,  # Same as top for horizontal line
            left_bar_index=left_bar_index,
            right_bar_index=right_bar_index,
            border_color="#FF0000",  # Red for BOS
            background_color="#FF0000",
            transparency=50,
            text="BOS",
            text_halign=TextAlign.CENTER,
            text_valign=TextVAlign.CENTER,
            extend_right=False  # BOS markers don't extend
        )
    
    def update_right_boundary(self, new_time: datetime, new_bar_index: int):
        """Update the right boundary of the box (for extension)"""
        self.right_time = new_time
        self.right_bar_index = new_bar_index
    
    def set_visibility(self, visible: bool):
        """Set box visibility"""
        self.is_visible = visible
    
    def set_text(self, text: str):
        """Update box text"""
        self.text = text
    
    def set_colors(self, border_color: str, background_color: str):
        """Update box colors"""
        self.border_color = border_color
        self.background_color = background_color
    
    def get_width_in_bars(self) -> int:
        """Get box width in number of bars"""
        return self.right_bar_index - self.left_bar_index
    
    def get_height(self) -> float:
        """Get box height in price units"""
        return abs(self.top_price - self.bottom_price)
    
    def get_center_price(self) -> float:
        """Get center price of the box"""
        return (self.top_price + self.bottom_price) / 2
    
    def is_price_in_box(self, price: float) -> bool:
        """Check if a price is within the box boundaries"""
        return min(self.top_price, self.bottom_price) <= price <= max(self.top_price, self.bottom_price)
    
    def get_box_coordinates(self) -> Tuple[datetime, float, datetime, float]:
        """Get box coordinates as tuple (left_time, top_price, right_time, bottom_price)"""
        return (self.left_time, self.top_price, self.right_time, self.bottom_price)
    
    def __str__(self) -> str:
        status = "VISIBLE" if self.is_visible else "HIDDEN"
        return f"{self.box_type.value} [{status}]: {self.bottom_price:.4f} - {self.top_price:.4f} | {self.text}"