# SMC Configuration Management System

## Overview

The SMC Configuration Management System provides centralized configuration for the Smart Money Concepts trading system with support for 20-40 cryptocurrency pairs, hot-reload capability, and comprehensive validation.

## Features

- **Multi-Symbol Support**: Configure up to 40 cryptocurrency pairs simultaneously
- **Hot-Reload**: Automatic configuration reloading when files change
- **Environment Variables**: Override configuration via environment variables
- **Validation**: Comprehensive parameter validation with error reporting
- **Thread Safety**: Safe for concurrent access in multi-threaded environments
- **Batch Processing**: Automatic symbol batching for optimal performance

## Configuration Files

### Main Configuration File: `smc_config.json`

```json
{
  "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", ...],
  "timeframe": "1h",
  "trading": {
    "swing_length": 10,
    "history_limit": 20,
    "box_width": 2.5,
    "atr_period": 50,
    "atr_multiplier": 2.0,
    "overlap_threshold_multiplier": 2.0
  },
  "performance": {
    "max_memory_mb": 500,
    "max_symbols": 40,
    "max_zones_per_symbol": 15,
    "max_swings_per_symbol": 50,
    "batch_size": 10,
    "max_workers": 8,
    "update_frequency_seconds": 60,
    "enable_caching": true,
    "cache_size_mb": 100,
    "cache_ttl_seconds": 300,
    "cache_strategy": "lru"
  },
  "visualization": {
    "supply_color": "#EDEDED",
    "demand_color": "#00FFFF",
    "poi_color": "#FFFFFF",
    "zone_transparency": 70,
    "show_zigzag": false,
    "show_price_action_labels": true,
    "show_poi_lines": true
  },
  "api": {
    "timeout_seconds": 30,
    "max_retries": 3,
    "retry_delay_seconds": 5,
    "max_candles_per_request": 1500
  },
  "system": {
    "enable_logging": true,
    "log_level": "INFO",
    "debug_mode": false,
    "enable_profiling": false
  }
}
```

### Environment Variables: `.env.smc`

```bash
# Core Symbol Configuration
SMC_SYMBOLS=BTCUSDT,ETHUSDT,ADAUSDT,BNBUSDT,XRPUSDT

# Trading Parameters
SMC_SWING_LENGTH=10
SMC_BOX_WIDTH=2.5
SMC_HISTORY_LIMIT=20

# Performance Settings
SMC_MAX_SYMBOLS=40
SMC_MAX_MEMORY_MB=500
SMC_BATCH_SIZE=10

# System Settings
SMC_DEBUG_MODE=false
SMC_LOG_LEVEL=INFO
```

## Usage

### Basic Usage

```python
from config.config_manager import ConfigManager, get_config

# Get global configuration
config = get_config()
print(f"Configured symbols: {config.symbols}")

# Or create a specific config manager
config_manager = ConfigManager()
config = config_manager.load_config()
```

### Hot-Reload Setup

```python
from config.config_manager import ConfigManager

# Enable hot-reload (default)
config_manager = ConfigManager(enable_hot_reload=True)

# Add watcher for configuration changes
def on_config_change(new_config):
    print(f"Configuration updated: {len(new_config.symbols)} symbols")

config_manager.add_watcher(on_config_change)
```

### Symbol Management

```python
# Add symbols
config_manager.add_symbol("NEWUSDT")

# Remove symbols
config_manager.remove_symbol("OLDUSDT")

# Update multiple symbols
config_manager.update_symbols(["BTCUSDT", "ETHUSDT", "ADAUSDT"])

# Get symbol batches for processing
batches = config_manager.get_symbol_batch()
for batch in batches:
    process_symbols(batch)
```

### Configuration Validation

```python
config = config_manager.get_config()
errors = config.validate()

if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration is valid")
```

## Configuration Parameters

### Core Settings

- **symbols**: List of cryptocurrency pairs (max 40)
- **timeframe**: Trading timeframe (1m, 5m, 15m, 1h, 4h, 1d)

### Trading Parameters

- **swing_length**: Pivot detection length (1-50)
- **history_limit**: Maximum zones/swings to keep (5-100)
- **box_width**: Zone width multiplier (1.0-10.0)
- **atr_period**: ATR calculation period
- **atr_multiplier**: ATR multiplier for zone sizing

### Performance Settings

- **max_memory_mb**: Maximum memory usage (min 50MB)
- **max_symbols**: Maximum symbols to process (max 40)
- **batch_size**: Symbols per processing batch
- **max_workers**: Maximum worker threads
- **enable_caching**: Enable performance caching
- **cache_strategy**: Cache strategy (lru, fifo, ttl)

### Visualization Settings

- **supply_color**: Supply zone color (hex)
- **demand_color**: Demand zone color (hex)
- **zone_transparency**: Zone transparency (0-100)
- **show_zigzag**: Enable ZigZag display
- **show_poi_lines**: Show POI level lines

## Environment Variable Overrides

Environment variables take precedence over JSON configuration:

| Environment Variable | JSON Path | Description |
|---------------------|-----------|-------------|
| SMC_SYMBOLS | symbols | Comma-separated symbol list |
| SMC_TIMEFRAME | timeframe | Trading timeframe |
| SMC_SWING_LENGTH | trading.swing_length | Swing detection length |
| SMC_BOX_WIDTH | trading.box_width | Zone width multiplier |
| SMC_MAX_SYMBOLS | performance.max_symbols | Maximum symbols |
| SMC_MAX_MEMORY_MB | performance.max_memory_mb | Memory limit |
| SMC_DEBUG_MODE | system.debug_mode | Debug mode flag |

## Validation Rules

### Symbol Configuration
- Minimum 1 symbol required
- Maximum 40 symbols allowed
- All symbols must be valid Binance pairs

### Trading Parameters
- Swing length: 1-50
- Box width: 1.0-10.0
- History limit: 5-100
- ATR period: 5-200

### Performance Limits
- Memory: minimum 50MB
- Batch size: cannot exceed symbol count
- Workers: 1-16 threads

## Hot-Reload Behavior

The system monitors the configuration file for changes and automatically reloads:

1. **File Change Detection**: Uses watchdog to monitor file system
2. **Debouncing**: Prevents multiple rapid reloads (1-second debounce)
3. **Validation**: New configuration is validated before applying
4. **Notifications**: Registered watchers are notified of changes
5. **Error Handling**: Invalid configurations are rejected with logging

## Error Handling

### Configuration Errors
- Invalid parameters are rejected with detailed error messages
- System falls back to previous valid configuration on reload errors
- Environment variable parsing errors are logged but don't stop loading

### File System Errors
- Missing configuration files trigger creation of defaults
- File permission errors are logged with fallback to defaults
- Hot-reload failures don't affect current configuration

## Testing

Run the configuration test suite:

```bash
python test_config_system.py
```

Tests include:
- Basic configuration loading
- Multi-symbol support
- Validation rules
- Hot-reload functionality
- Environment variable overrides

## Best Practices

1. **Symbol Management**: Start with fewer symbols and scale up gradually
2. **Memory Monitoring**: Monitor memory usage with large symbol sets
3. **Batch Sizing**: Adjust batch size based on system performance
4. **Hot-Reload**: Use watchers for critical configuration changes
5. **Validation**: Always validate configuration after manual edits
6. **Environment Variables**: Use for deployment-specific overrides
7. **Backup**: Keep backup copies of working configurations

## Troubleshooting

### Common Issues

1. **"Too many symbols" error**: Reduce symbol count or increase max_symbols
2. **"Batch size cannot exceed symbols"**: Reduce batch_size or add more symbols
3. **Hot-reload not working**: Check file permissions and watchdog installation
4. **Memory errors**: Reduce cache_size_mb or max_memory_mb
5. **Validation failures**: Check parameter ranges in error messages

### Debug Mode

Enable debug mode for detailed logging:

```bash
export SMC_DEBUG_MODE=true
```

Or in configuration:
```json
{
  "system": {
    "debug_mode": true,
    "log_level": "DEBUG"
  }
}
```