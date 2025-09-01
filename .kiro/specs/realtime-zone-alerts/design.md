# Design Document

## Overview

The Real-Time Zone Alert System is designed as a lightweight, efficient monitoring layer that leverages our existing ImplacableZonesDetector to provide immediate notifications when new SMC zones are formed. The system uses a comparison-based approach to detect changes and adapts automatically to any timeframe configuration.

## Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Zone Monitor  │───▶│  Zone Comparator │───▶│  Alert Manager  │
│                 │    │                  │    │                 │
│ - Timeframe     │    │ - New vs Old     │    │ - Visual Alerts │
│ - Multi-symbol  │    │ - Change Detection│    │ - Formatting    │
│ - Continuous    │    │ - Deduplication  │    │ - Timestamps    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ImplacableZones  │    │   Zone Storage   │    │   Console UI    │
│   Detector      │    │                  │    │                 │
│                 │    │ - Previous Zones │    │ - Color Coding  │
│ - Existing SMC  │    │ - Current Zones  │    │ - Clear Format  │
│ - Multi-crypto  │    │ - Timestamps     │    │ - Real-time     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

1. **Monitor Loop**: Runs continuously based on timeframe
2. **Zone Detection**: Uses existing ImplacableZonesDetector
3. **Comparison**: Compares new zones with previously stored zones
4. **Alert Generation**: Creates alerts for genuinely new zones
5. **Display**: Shows formatted alerts with zone details

## Components and Interfaces

### 1. RealTimeZoneMonitor

**Purpose**: Main orchestrator that manages the monitoring loop and coordinates all components.

**Key Methods**:
- `start_monitoring(symbols: List[str], timeframe: str)`: Begins continuous monitoring
- `stop_monitoring()`: Gracefully stops the monitoring process
- `add_symbol(symbol: str)`: Dynamically adds a symbol to monitor
- `remove_symbol(symbol: str)`: Removes a symbol from monitoring

**Configuration**:
- Timeframe adaptation (1m, 5m, 1h, etc.)
- Symbol list management
- Error handling and recovery

### 2. ZoneComparator

**Purpose**: Compares current zones with previously detected zones to identify new formations.

**Key Methods**:
- `compare_zones(current_zones: Dict, previous_zones: Dict) -> List[Zone]`: Returns new zones
- `is_zone_new(zone: Zone, existing_zones: List[Zone]) -> bool`: Checks if zone is genuinely new
- `get_zone_signature(zone: Zone) -> str`: Creates unique identifier for zones

**Comparison Logic**:
- Zone uniqueness based on POI price and formation time
- Tolerance for minor price variations (±0.1%)
- Time-based deduplication to prevent duplicate alerts

### 3. ZoneStorage

**Purpose**: Manages persistent storage of zone data for comparison purposes.

**Key Methods**:
- `store_zones(symbol: str, zones: Dict)`: Saves current zones for symbol
- `get_previous_zones(symbol: str) -> Dict`: Retrieves last known zones
- `cleanup_old_data(max_age_hours: int)`: Removes outdated zone data

**Storage Strategy**:
- In-memory storage for current session
- File-based persistence for session recovery
- Automatic cleanup of old data

### 4. AlertManager

**Purpose**: Handles alert generation, formatting, and display.

**Key Methods**:
- `generate_alert(new_zones: List[Zone], symbol: str)`: Creates formatted alert
- `display_alert(alert: Alert)`: Shows alert in console with proper formatting
- `format_zone_info(zone: Zone) -> str`: Formats zone details for display

**Alert Features**:
- Color-coded alerts (red for supply, green for demand)
- Timestamp conversion to local timezone
- Clear zone information display
- Multiple zone handling (show up to 2 most recent)

## Data Models

### Alert Data Structure

```python
@dataclass
class ZoneAlert:
    symbol: str
    timeframe: str
    new_zones: List[Zone]
    detection_time: datetime
    alert_id: str
    
@dataclass
class MonitoringSession:
    symbols: List[str]
    timeframe: str
    start_time: datetime
    last_check: Dict[str, datetime]
    zone_history: Dict[str, Dict]
```

### Zone Comparison Model

```python
@dataclass
class ZoneComparison:
    symbol: str
    previous_count: int
    current_count: int
    new_zones: List[Zone]
    removed_zones: List[Zone]
    comparison_time: datetime
```

## Error Handling

### API Error Management
- **Connection Failures**: Retry with exponential backoff
- **Rate Limiting**: Automatic delay adjustment
- **Invalid Data**: Skip current cycle, log error, continue monitoring

### System Error Recovery
- **Memory Issues**: Automatic cleanup of old data
- **Configuration Errors**: Validation with clear error messages
- **Crash Recovery**: Session state persistence for restart

### Monitoring Continuity
- **Symbol Failures**: Continue monitoring other symbols
- **Timeframe Issues**: Validate and adjust automatically
- **Alert Failures**: Log errors but continue detection

## Testing Strategy

### Unit Tests
- Zone comparison logic with various scenarios
- Alert formatting and display functions
- Storage operations and data persistence
- Timeframe adaptation and validation

### Integration Tests
- End-to-end monitoring workflow
- Multi-symbol monitoring scenarios
- Error recovery and system resilience
- Performance under continuous operation

### Performance Tests
- Memory usage during extended monitoring
- API rate limiting compliance
- Response time for zone detection
- System stability over 24+ hour periods

## Performance Considerations

### Memory Management
- Circular buffer for zone history (max 100 zones per symbol)
- Automatic cleanup of zones older than 24 hours
- Efficient data structures for fast comparison

### API Optimization
- Reuse existing ImplacableZonesDetector (no additional API calls)
- Intelligent caching to minimize redundant operations
- Rate limiting compliance with configurable delays

### Real-Time Requirements
- Target: Detection within 30 seconds of zone formation
- Maximum delay: 1 timeframe interval
- Alert display: Immediate upon detection

## Configuration Options

### Monitoring Settings
```python
MONITOR_CONFIG = {
    'default_symbols': ['BTCUSDT', 'ETHUSDT'],
    'default_timeframe': '5m',
    'max_zones_per_symbol': 100,
    'cleanup_interval_hours': 24,
    'alert_display_duration': 10,
    'comparison_tolerance_pct': 0.1
}
```

### Alert Customization
- Color schemes for different zone types
- Alert sound options (future enhancement)
- Custom formatting templates
- Timezone configuration for timestamps