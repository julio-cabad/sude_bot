# Clase Swing (high/low)
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class SwingType(Enum):
    """Enum for swing types based on Pine Script swing detection"""
    HIGH = 1    # Equivalent to swing_type == 1 in Pine Script (pivot high)
    LOW = -1    # Equivalent to swing_type == -1 in Pine Script (pivot low)


class SwingLabel(Enum):
    """
    Enum for swing labels based on Pine Script f_sh_sl_labels function.
    
    Pine Script logic:
    - For swing_type == 1: 'HH' if current >= previous else 'LH'
    - For swing_type == -1: 'HL' if current >= previous else 'LL'
    """
    HH = "HH"  # Higher High
    HL = "HL"  # Higher Low  
    LH = "LH"  # Lower High
    LL = "LL"  # Lower Low


@dataclass
class Swing:
    """
    Represents a swing point (pivot high or low) based on Pine Script swing detection.
    
    Equivalent to Pine Script:
    - swing_high = ta.pivothigh(high, swing_length, swing_length)
    - swing_low = ta.pivotlow(low, swing_length, swing_length)
    """
    
    # Core swing properties
    swing_type: SwingType
    price: float            # The swing high or low price
    timestamp: datetime     # When the swing occurred
    bar_index: int         # Bar index of the swing (equivalent to Pine Script bar_index)
    
    # Swing classification
    label: Optional[SwingLabel] = None  # HH, HL, LH, LL classification
    
    # Technical properties
    swing_length: int = 10  # Length parameter used for pivot detection
    
    # Comparison data for classification
    previous_swing_price: Optional[float] = None
    
    def __post_init__(self):
        """Initialize swing after creation"""
        # Auto-classify if we have previous swing data
        if self.previous_swing_price is not None and self.label is None:
            self.label = self._classify_swing()
    
    def _classify_swing(self) -> SwingLabel:
        """
        Classify swing based on Pine Script f_sh_sl_labels logic.
        
        Pine Script equivalent:
        if swing_type == 1
            label_text := array.get(array, 0) >= array.get(array, 1) ? 'HH' : 'LH'
        else if swing_type == -1
            label_text := array.get(array, 0) >= array.get(array, 1) ? 'HL' : 'LL'
        """
        if self.previous_swing_price is None:
            # First swing, default classification
            return SwingLabel.HH if self.swing_type == SwingType.HIGH else SwingLabel.HL
        
        current_higher = self.price >= self.previous_swing_price
        
        if self.swing_type == SwingType.HIGH:
            return SwingLabel.HH if current_higher else SwingLabel.LH
        else:  # SwingType.LOW
            return SwingLabel.HL if current_higher else SwingLabel.LL
    
    @classmethod
    def create_from_pivot_high(
        cls,
        price: float,
        timestamp: datetime,
        bar_index: int,
        swing_length: int = 10,
        previous_swing_price: Optional[float] = None
    ) -> 'Swing':
        """
        Create a swing from a pivot high detection.
        Equivalent to Pine Script: swing_high = ta.pivothigh(high, swing_length, swing_length)
        """
        return cls(
            swing_type=SwingType.HIGH,
            price=price,
            timestamp=timestamp,
            bar_index=bar_index,
            swing_length=swing_length,
            previous_swing_price=previous_swing_price
        )
    
    @classmethod
    def create_from_pivot_low(
        cls,
        price: float,
        timestamp: datetime,
        bar_index: int,
        swing_length: int = 10,
        previous_swing_price: Optional[float] = None
    ) -> 'Swing':
        """
        Create a swing from a pivot low detection.
        Equivalent to Pine Script: swing_low = ta.pivotlow(low, swing_length, swing_length)
        """
        return cls(
            swing_type=SwingType.LOW,
            price=price,
            timestamp=timestamp,
            bar_index=bar_index,
            swing_length=swing_length,
            previous_swing_price=previous_swing_price
        )
    
    def update_classification(self, previous_swing_price: float):
        """Update swing classification with new previous swing data"""
        self.previous_swing_price = previous_swing_price
        self.label = self._classify_swing()
    
    def is_higher_than(self, other_swing: 'Swing') -> bool:
        """Check if this swing is higher than another swing"""
        return self.price > other_swing.price
    
    def is_lower_than(self, other_swing: 'Swing') -> bool:
        """Check if this swing is lower than another swing"""
        return self.price < other_swing.price
    
    def get_time_difference(self, other_swing: 'Swing') -> float:
        """Get time difference in seconds between swings"""
        return abs((self.timestamp - other_swing.timestamp).total_seconds())
    
    def get_price_difference(self, other_swing: 'Swing') -> float:
        """Get price difference between swings"""
        return abs(self.price - other_swing.price)
    
    def is_bullish_structure(self) -> bool:
        """Check if swing indicates bullish structure (HH or HL)"""
        return self.label in [SwingLabel.HH, SwingLabel.HL] if self.label else False
    
    def is_bearish_structure(self) -> bool:
        """Check if swing indicates bearish structure (LH or LL)"""
        return self.label in [SwingLabel.LH, SwingLabel.LL] if self.label else False
    
    def __str__(self) -> str:
        label_str = f" ({self.label.value})" if self.label else ""
        return f"{self.swing_type.name} Swing{label_str}: {self.price:.4f} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"