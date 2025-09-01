# Smart Money Concepts - Design Document

## Overview

The Smart Money Concepts (SMC) system is designed as a modular, high-performance trading analysis engine that processes real-time market data from Binance to identify institutional trading patterns. The system follows a clean architecture pattern with clear separation of concerns, enabling scalability and maintainability.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Layer    │    │  Business Logic │    │ Presentation    │
│                 │    │                 │    │                 │
│ SimpleBinanceBot│◄──►│   Core Modules  │◄──►│ Visualization   │
│ Market Data     │    │   Models        │    │ Charts/Alerts   │
│ Real-time Feed  │    │   Utils         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Architecture

```
SMC System
├── Data Integration Layer
│   └── SimpleBinanceBot (existing)
├── Core Processing Engine
│   ├── SwingDetector
│   ├── ZoneManager  
│   ├── POICalculator
│   └── BOSHandler
├── Data Models
│   ├── Zone (Supply/Demand)
│   ├── Swing (High/Low)
│   ├── POI (Point of Interest)
│   └── Box (Visual Element)
├── Utilities
│   ├── ArrayOperations
│   ├── OverlapChecker
│   ├── TechnicalIndicators
│   └── DataManager
└── Visualization Engine
    ├── ChartRenderer
    ├── ZigZagRenderer
    ├── LabelManager
    └── StyleManager
```

## Components and Interfaces

### 1. Data Models (`models/`)

#### Zone Class
```python
@dataclass
class Zone:
    zone_type: ZoneType  # SUPPLY or DEMAND
    top: float
    bottom: float
    left_time: datetime
    right_time: datetime
    poi: float
    atr_buffer: float
    is_active: bool
    break_time: Optional[datetime] = None
```

#### Swing Class
```python
@dataclass
class Swing:
    swing_type: SwingType  # HIGH or LOW
    price: float
    timestamp: datetime
    bar_index: int
    label: SwingLabel  # HH, HL, LH, LL
```

#### POI Class
```python
@dataclass
class POI:
    price: float
    timestamp: datetime
    zone_id: str
    poi_type: POIType  # SUPPLY_POI or DEMAND_POI
```

### 2. Core Processing Engine (`core/`)

#### SwingDetector
```python
class SwingDetector:
    def __init__(self, swing_length: int = 10):
        self.swing_length = swing_length
        self.swing_history = CircularBuffer(maxsize=100)
    
    def detect_swings(self, ohlcv_data: pd.DataFrame) -> List[Swing]:
        """Detect pivot highs and lows using configurable swing length"""
        
    def classify_swing(self, current_swing: Swing, previous_swings: List[Swing]) -> SwingLabel:
        """Classify swing as HH, HL, LH, or LL"""
        
    def update_real_time(self, new_candle: dict) -> Optional[Swing]:
        """Process new candle data for swing detection"""
```

#### ZoneManager
```python
class ZoneManager:
    def __init__(self, history_limit: int = 20, box_width: float = 2.5):
        self.active_zones = CircularBuffer(maxsize=history_limit)
        self.box_width = box_width
        self.overlap_checker = OverlapChecker()
    
    def create_supply_zone(self, swing: Swing, atr: float) -> Optional[Zone]:
        """Create supply zone from swing high"""
        
    def create_demand_zone(self, swing: Swing, atr: float) -> Optional[Zone]:
        """Create demand zone from swing low"""
        
    def check_zone_breaks(self, current_price: float) -> List[Zone]:
        """Check if current price breaks any active zones"""
```

#### POICalculator
```python
class POICalculator:
    def calculate_poi(self, zone: Zone) -> float:
        """Calculate Point of Interest at zone center"""
        return (zone.top + zone.bottom) / 2
    
    def update_poi_levels(self, zones: List[Zone]) -> List[POI]:
        """Update all POI levels for active zones"""
```

#### BOSHandler
```python
class BOSHandler:
    def __init__(self):
        self.broken_structures = CircularBuffer(maxsize=50)
    
    def process_zone_break(self, broken_zone: Zone, break_price: float) -> dict:
        """Process zone break and create BOS marker"""
        
    def check_structure_breaks(self, zones: List[Zone], current_price: float) -> List[dict]:
        """Check for structure breaks in real-time"""
```

### 3. Utilities (`utils/`)

#### ArrayOperations
```python
class CircularBuffer:
    """Efficient circular buffer for maintaining fixed-size history"""
    def __init__(self, maxsize: int):
        self.maxsize = maxsize
        self.data = deque(maxlen=maxsize)
    
    def add_pop(self, item):
        """Add new item and remove oldest if at capacity"""
        self.data.appendleft(item)
```

#### OverlapChecker
```python
class OverlapChecker:
    def check_zone_overlap(self, new_zone: Zone, existing_zones: List[Zone], atr_threshold: float) -> bool:
        """Check if new zone overlaps with existing zones within ATR threshold"""
        
    def calculate_overlap_percentage(self, zone1: Zone, zone2: Zone) -> float:
        """Calculate percentage overlap between two zones"""
```

#### TechnicalIndicators
```python
class TechnicalIndicators:
    @staticmethod
    def calculate_atr(ohlcv_data: pd.DataFrame, period: int = 50) -> pd.Series:
        """Calculate Average True Range using pandas_ta"""
        
    @staticmethod
    def detect_pivot_highs(high_series: pd.Series, length: int) -> pd.Series:
        """Detect pivot highs in price series"""
        
    @staticmethod
    def detect_pivot_lows(low_series: pd.Series, length: int) -> pd.Series:
        """Detect pivot lows in price series"""
```

### 4. Visualization Engine (`visualization/`)

#### ChartRenderer
```python
class ChartRenderer:
    def __init__(self, style_manager: StyleManager):
        self.style_manager = style_manager
        
    def render_zones(self, zones: List[Zone]) -> dict:
        """Render supply/demand zones as boxes"""
        
    def render_poi_levels(self, pois: List[POI]) -> dict:
        """Render POI levels as horizontal lines"""
        
    def update_chart_real_time(self, new_data: dict) -> dict:
        """Update chart with new real-time data"""
```

## Data Models

### Core Data Structures

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

class ZoneType(Enum):
    SUPPLY = "SUPPLY"
    DEMAND = "DEMAND"

class SwingType(Enum):
    HIGH = "HIGH"
    LOW = "LOW"

class SwingLabel(Enum):
    HH = "HH"  # Higher High
    HL = "HL"  # Higher Low
    LH = "LH"  # Lower High
    LL = "LL"  # Lower Low

class POIType(Enum):
    SUPPLY_POI = "SUPPLY_POI"
    DEMAND_POI = "DEMAND_POI"
```

### Data Flow

```
Binance API → SimpleBinanceBot → OHLCV DataFrame → SwingDetector → ZoneManager → POICalculator → BOSHandler → Visualization
```

## Error Handling

### Error Categories and Strategies

1. **Data Errors**
   - Invalid OHLCV data: Skip invalid candles, log warning
   - Missing data points: Interpolate or skip based on gap size
   - API rate limits: Implement exponential backoff

2. **Calculation Errors**
   - Division by zero: Use safe division with epsilon
   - Invalid swing detection: Fallback to previous valid state
   - Zone overlap conflicts: Use ATR-based resolution

3. **System Errors**
   - Memory overflow: Implement data rotation
   - Performance degradation: Use profiling and optimization
   - Connection failures: Automatic reconnection with circuit breaker

### Error Recovery Mechanisms

```python
class ErrorHandler:
    def __init__(self):
        self.retry_count = 0
        self.max_retries = 3
        self.backoff_factor = 2
    
    def handle_api_error(self, error: Exception) -> bool:
        """Handle API errors with exponential backoff"""
        
    def handle_calculation_error(self, error: Exception, fallback_data: dict) -> dict:
        """Handle calculation errors with fallback mechanisms"""
```

## Testing Strategy

### Unit Testing
- Test each component in isolation
- Mock Binance API responses for consistent testing
- Validate mathematical calculations with known datasets
- Test error handling scenarios

### Integration Testing
- Test data flow between components
- Validate real-time processing with simulated market data
- Test performance under load
- Validate memory management

### Performance Testing
- Benchmark processing speed with large datasets
- Memory usage profiling
- Real-time latency measurements
- Stress testing with high-frequency data

## Performance Considerations

### Optimization Strategies

1. **Data Processing**
   - Use vectorized pandas operations
   - Implement efficient circular buffers
   - Cache frequently accessed calculations
   - Use numpy for mathematical operations

2. **Memory Management**
   - Limit historical data retention
   - Implement data compression for storage
   - Use generators for large dataset processing
   - Regular garbage collection optimization

3. **Real-time Processing**
   - Asynchronous data processing
   - Event-driven architecture
   - Efficient data structures (deque, numpy arrays)
   - Minimal object creation in hot paths

### Performance Targets
- Process new candle data: < 100ms
- Memory usage: < 500MB for 24h operation
- Historical analysis: < 5 seconds for 1000 candles
- Zone detection: < 50ms per swing point

## Security Considerations

### API Security
- Secure storage of Binance API credentials
- Rate limiting compliance
- Connection encryption (HTTPS/WSS)
- API key rotation support

### Data Integrity
- Input validation for all market data
- Checksum verification for critical calculations
- Audit logging for trading decisions
- Backup and recovery procedures

## Deployment Architecture

### Production Environment
```
┌─────────────────┐
│   Load Balancer │
└─────────┬───────┘
          │
┌─────────▼───────┐
│  SMC Application│
│  - Core Engine  │
│  - Data Manager │
│  - Visualization│
└─────────┬───────┘
          │
┌─────────▼───────┐
│  Binance API    │
│  - Market Data  │
│  - Real-time    │
└─────────────────┘
```

### Monitoring and Logging
- Application performance monitoring
- Real-time error tracking
- Trading signal logging
- System health dashboards
- Alert mechanisms for critical failures