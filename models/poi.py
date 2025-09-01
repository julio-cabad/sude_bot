#!/usr/bin/env python3
"""
POI (Point of Interest) Data Model
Professional data structure for Points of Interest in Smart Money Concepts
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any
import uuid


class POIType(Enum):
    """Types of Points of Interest"""
    SUPPLY_POI = "SUPPLY_POI"       # POI at supply zone center
    DEMAND_POI = "DEMAND_POI"       # POI at demand zone center
    FIBONACCI_POI = "FIBONACCI_POI" # Fibonacci retracement level
    PIVOT_POI = "PIVOT_POI"         # Pivot point level
    CUSTOM_POI = "CUSTOM_POI"       # Custom defined POI


class POIStrength(Enum):
    """Strength levels for POI"""
    VERY_STRONG = "very_strong"     # High confidence, multiple confirmations
    STRONG = "strong"               # Good confidence, some confirmations
    MEDIUM = "medium"               # Moderate confidence
    WEAK = "weak"                   # Low confidence
    UNTESTED = "untested"           # New POI, not yet tested


class POIStatus(Enum):
    """Status of POI"""
    ACTIVE = "active"               # POI is active and valid
    TESTED = "tested"               # Price has reached POI level
    BROKEN = "broken"               # POI level has been broken
    INVALIDATED = "invalidated"     # POI is no longer valid
    PENDING = "pending"             # POI is pending confirmation


@dataclass
class POI:
    """
    Point of Interest (POI) data structure
    Represents critical price levels calculated from supply/demand zones
    """
    
    # Core POI properties
    poi_id: str
    price: float                    # POI price level
    timestamp: datetime             # When POI was identified
    zone_id: str                    # Associated zone ID
    poi_type: POIType              # Type of POI
    
    # POI characteristics
    strength: POIStrength = POIStrength.MEDIUM
    status: POIStatus = POIStatus.ACTIVE
    confidence_score: float = 50.0  # Confidence percentage (0-100)
    
    # Market context
    symbol: str = ""                # Trading symbol
    timeframe: str = "1h"          # Timeframe where POI was identified
    
    # Calculation details
    calculation_method: str = "center"  # Method used to calculate POI
    secondary_levels: List[float] = field(default_factory=list)  # Additional POI levels
    fibonacci_levels: Dict[str, float] = field(default_factory=dict)  # Fib levels if applicable
    
    # Testing and validation
    times_tested: int = 0           # How many times price reached this POI
    times_respected: int = 0        # How many times POI acted as support/resistance
    last_test_time: Optional[datetime] = None
    last_test_price: Optional[float] = None
    
    # Performance metrics
    max_distance_reached: float = 0.0  # Maximum distance price moved from POI
    avg_reaction_strength: float = 0.0  # Average reaction strength when tested
    
    # Metadata and tracking
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Initialize POI after creation"""
        if not self.poi_id:
            self.poi_id = str(uuid.uuid4())
        
        # Ensure price precision
        self.price = round(self.price, 8)
        
        # Validate confidence score
        self.confidence_score = max(0.0, min(100.0, self.confidence_score))
    
    @classmethod
    def create_supply_poi(
        cls,
        price: float,
        zone_id: str,
        symbol: str,
        confidence: float = 50.0,
        calculation_method: str = "center"
    ) -> 'POI':
        """
        Create a supply POI from zone data
        
        Args:
            price: POI price level
            zone_id: Associated supply zone ID
            symbol: Trading symbol
            confidence: Confidence score (0-100)
            calculation_method: Method used for calculation
            
        Returns:
            POI object for supply zone
        """
        return cls(
            poi_id="",  # Will be generated in __post_init__
            price=price,
            timestamp=datetime.now(),
            zone_id=zone_id,
            poi_type=POIType.SUPPLY_POI,
            strength=cls._determine_strength_from_confidence(confidence),
            confidence_score=confidence,
            symbol=symbol,
            calculation_method=calculation_method
        )
    
    @classmethod
    def create_demand_poi(
        cls,
        price: float,
        zone_id: str,
        symbol: str,
        confidence: float = 50.0,
        calculation_method: str = "center"
    ) -> 'POI':
        """
        Create a demand POI from zone data
        
        Args:
            price: POI price level
            zone_id: Associated demand zone ID
            symbol: Trading symbol
            confidence: Confidence score (0-100)
            calculation_method: Method used for calculation
            
        Returns:
            POI object for demand zone
        """
        return cls(
            poi_id="",  # Will be generated in __post_init__
            price=price,
            timestamp=datetime.now(),
            zone_id=zone_id,
            poi_type=POIType.DEMAND_POI,
            strength=cls._determine_strength_from_confidence(confidence),
            confidence_score=confidence,
            symbol=symbol,
            calculation_method=calculation_method
        )
    
    @staticmethod
    def _determine_strength_from_confidence(confidence: float) -> POIStrength:
        """Determine POI strength based on confidence score"""
        if confidence >= 80:
            return POIStrength.VERY_STRONG
        elif confidence >= 60:
            return POIStrength.STRONG
        elif confidence >= 40:
            return POIStrength.MEDIUM
        else:
            return POIStrength.WEAK
    
    def test_poi(self, test_price: float, reaction_strength: float = 0.0) -> None:
        """
        Record a test of this POI level
        
        Args:
            test_price: Price at which POI was tested
            reaction_strength: Strength of market reaction (0-100)
        """
        self.times_tested += 1
        self.last_test_time = datetime.now()
        self.last_test_price = test_price
        self.last_updated = datetime.now()
        
        # Calculate distance from POI
        distance = abs(test_price - self.price)
        if distance > self.max_distance_reached:
            self.max_distance_reached = distance
        
        # Update average reaction strength
        if reaction_strength > 0:
            total_reaction = (self.avg_reaction_strength * (self.times_tested - 1)) + reaction_strength
            self.avg_reaction_strength = total_reaction / self.times_tested
        
        # Update status
        if self.status == POIStatus.ACTIVE:
            self.status = POIStatus.TESTED
    
    def mark_respected(self) -> None:
        """Mark POI as respected (acted as support/resistance)"""
        self.times_respected += 1
        self.last_updated = datetime.now()
        
        # Increase confidence slightly when respected
        confidence_boost = min(5.0, 100.0 - self.confidence_score)
        self.confidence_score += confidence_boost
        
        # Update strength if confidence improved significantly
        new_strength = self._determine_strength_from_confidence(self.confidence_score)
        if new_strength.value != self.strength.value:
            self.strength = new_strength
    
    def mark_broken(self, break_price: float) -> None:
        """
        Mark POI as broken
        
        Args:
            break_price: Price at which POI was broken
        """
        self.status = POIStatus.BROKEN
        self.last_test_price = break_price
        self.last_test_time = datetime.now()
        self.last_updated = datetime.now()
        
        # Record break in metadata
        self.metadata['break_price'] = break_price
        self.metadata['break_time'] = datetime.now().isoformat()
    
    def update_confidence(self, new_confidence: float) -> None:
        """
        Update POI confidence score
        
        Args:
            new_confidence: New confidence score (0-100)
        """
        self.confidence_score = max(0.0, min(100.0, new_confidence))
        self.strength = self._determine_strength_from_confidence(self.confidence_score)
        self.last_updated = datetime.now()
    
    def get_success_rate(self) -> float:
        """
        Calculate POI success rate (times respected / times tested)
        
        Returns:
            Success rate as percentage (0-100)
        """
        if self.times_tested == 0:
            return 0.0
        
        return (self.times_respected / self.times_tested) * 100
    
    def is_near_price(self, current_price: float, tolerance_pct: float = 0.5) -> bool:
        """
        Check if current price is near this POI
        
        Args:
            current_price: Current market price
            tolerance_pct: Tolerance as percentage of price
            
        Returns:
            True if price is within tolerance of POI
        """
        tolerance = current_price * (tolerance_pct / 100)
        return abs(current_price - self.price) <= tolerance
    
    def get_distance_from_price(self, current_price: float) -> Dict[str, float]:
        """
        Get distance metrics from current price
        
        Args:
            current_price: Current market price
            
        Returns:
            Dictionary with distance metrics
        """
        absolute_distance = abs(current_price - self.price)
        percentage_distance = (absolute_distance / current_price) * 100
        
        return {
            'absolute_distance': absolute_distance,
            'percentage_distance': percentage_distance,
            'direction': 'above' if self.price > current_price else 'below'
        }
    
    def add_secondary_level(self, price: float, level_type: str = "support") -> None:
        """
        Add a secondary POI level
        
        Args:
            price: Secondary level price
            level_type: Type of secondary level
        """
        if price not in self.secondary_levels:
            self.secondary_levels.append(round(price, 8))
            self.secondary_levels.sort()
            
            # Store level type in metadata
            if 'secondary_level_types' not in self.metadata:
                self.metadata['secondary_level_types'] = {}
            self.metadata['secondary_level_types'][str(price)] = level_type
            
            self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert POI to dictionary representation"""
        return {
            'poi_id': self.poi_id,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'zone_id': self.zone_id,
            'poi_type': self.poi_type.value,
            'strength': self.strength.value,
            'status': self.status.value,
            'confidence_score': self.confidence_score,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'calculation_method': self.calculation_method,
            'secondary_levels': self.secondary_levels,
            'fibonacci_levels': self.fibonacci_levels,
            'times_tested': self.times_tested,
            'times_respected': self.times_respected,
            'success_rate': self.get_success_rate(),
            'last_test_time': self.last_test_time.isoformat() if self.last_test_time else None,
            'last_test_price': self.last_test_price,
            'max_distance_reached': self.max_distance_reached,
            'avg_reaction_strength': self.avg_reaction_strength,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'POI':
        """Create POI from dictionary representation"""
        # Parse datetime fields
        timestamp = datetime.fromisoformat(data['timestamp'])
        created_at = datetime.fromisoformat(data['created_at'])
        last_updated = datetime.fromisoformat(data['last_updated'])
        
        last_test_time = None
        if data.get('last_test_time'):
            last_test_time = datetime.fromisoformat(data['last_test_time'])
        
        return cls(
            poi_id=data['poi_id'],
            price=data['price'],
            timestamp=timestamp,
            zone_id=data['zone_id'],
            poi_type=POIType(data['poi_type']),
            strength=POIStrength(data['strength']),
            status=POIStatus(data['status']),
            confidence_score=data['confidence_score'],
            symbol=data['symbol'],
            timeframe=data.get('timeframe', '1h'),
            calculation_method=data.get('calculation_method', 'center'),
            secondary_levels=data.get('secondary_levels', []),
            fibonacci_levels=data.get('fibonacci_levels', {}),
            times_tested=data.get('times_tested', 0),
            times_respected=data.get('times_respected', 0),
            last_test_time=last_test_time,
            last_test_price=data.get('last_test_price'),
            max_distance_reached=data.get('max_distance_reached', 0.0),
            avg_reaction_strength=data.get('avg_reaction_strength', 0.0),
            metadata=data.get('metadata', {}),
            created_at=created_at,
            last_updated=last_updated
        )
    
    def __str__(self) -> str:
        """String representation of POI"""
        status_emoji = {
            POIStatus.ACTIVE: "🎯",
            POIStatus.TESTED: "✅",
            POIStatus.BROKEN: "❌",
            POIStatus.INVALIDATED: "⚠️",
            POIStatus.PENDING: "⏳"
        }
        
        strength_emoji = {
            POIStrength.VERY_STRONG: "💪💪",
            POIStrength.STRONG: "💪",
            POIStrength.MEDIUM: "👍",
            POIStrength.WEAK: "👎",
            POIStrength.UNTESTED: "❓"
        }
        
        emoji = status_emoji.get(self.status, "🎯")
        strength = strength_emoji.get(self.strength, "👍")
        
        return (f"{emoji} {self.poi_type.value} POI: ${self.price:.4f} "
                f"{strength} ({self.confidence_score:.1f}% confidence)")
    
    def __repr__(self) -> str:
        """Detailed representation of POI"""
        return (f"POI(id={self.poi_id[:8]}, price={self.price:.4f}, "
                f"type={self.poi_type.value}, strength={self.strength.value}, "
                f"status={self.status.value})")