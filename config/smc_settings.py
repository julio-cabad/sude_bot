#!/usr/bin/env python3
"""
Smart Money Concepts - Centralized Configuration Settings
Professional configuration management for multi-symbol SMC system
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import os
from pathlib import Path


class TimeFrame(Enum):
    """Supported timeframes"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class CacheStrategy(Enum):
    """Cache strategies for performance optimization"""
    LRU = "lru"
    FIFO = "fifo"
    TTL = "ttl"
    NONE = "none"


@dataclass
class SymbolConfig:
    """Configuration for individual symbols"""
    symbol: str
    enabled: bool = True
    swing_length: int = 10
    history_limit: int = 20
    box_width: float = 2.5
    atr_period: int = 50
    
    # Symbol-specific overrides
    custom_settings: Dict = field(default_factory=dict)


@dataclass
class PerformanceConfig:
    """Performance and resource management settings"""
    # Memory management
    max_memory_mb: int = 500
    max_symbols: int = 40
    max_zones_per_symbol: int = 15
    max_swings_per_symbol: int = 50
    max_pois_per_symbol: int = 30
    
    # Processing optimization
    batch_size: int = 10
    max_workers: int = 8
    update_frequency_seconds: int = 60
    
    # Cache settings
    enable_caching: bool = True
    cache_strategy: CacheStrategy = CacheStrategy.LRU
    cache_size_mb: int = 100
    cache_ttl_seconds: int = 300
    
    # Performance thresholds
    max_processing_time_ms: int = 100
    memory_warning_threshold: float = 0.8
    memory_critical_threshold: float = 0.95


@dataclass
class TradingConfig:
    """Trading-specific configuration"""
    # Swing detection
    default_swing_length: int = 10
    min_swing_length: int = 5
    max_swing_length: int = 50
    
    # Zone creation
    default_box_width: float = 2.5
    min_box_width: float = 1.0
    max_box_width: float = 10.0
    default_history_limit: int = 20
    
    # Technical indicators
    atr_period: int = 50
    atr_multiplier: float = 2.0
    
    # Overlap detection
    overlap_threshold_multiplier: float = 2.0
    min_zone_distance_atr: float = 1.0


@dataclass
class VisualizationConfig:
    """Visualization and styling settings"""
    # Colors (hex format)
    supply_color: str = "#EDEDED"
    supply_outline_color: str = "#FFFFFF"
    demand_color: str = "#00FFFF"
    demand_outline_color: str = "#FFFFFF"
    poi_color: str = "#FFFFFF"
    zigzag_color: str = "#000000"
    
    # Transparency (0-100)
    zone_transparency: int = 70
    poi_transparency: int = 90
    
    # Display options
    show_zigzag: bool = False
    show_price_action_labels: bool = True
    show_poi_lines: bool = True
    extend_zones_right: bool = True
    
    # Text settings
    label_size: str = "small"
    label_color: str = "#FFFFFF"


@dataclass
class APIConfig:
    """Binance API configuration"""
    # Connection settings
    base_url: str = "https://fapi.binance.com"
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 5
    
    # Rate limiting
    requests_per_minute: int = 1200
    weight_per_minute: int = 6000
    
    # Data settings
    max_candles_per_request: int = 1500
    default_limit: int = 500


@dataclass
class SMCSettings:
    """Main SMC system configuration"""
    
    # Core settings - Starting with BTC and ADA
    symbols: List[str] = field(default_factory=lambda: [
        "BTCUSDT", "ADAUSDT"
    ])
    
    default_timeframe: TimeFrame = TimeFrame.H1
    enabled_timeframes: List[TimeFrame] = field(default_factory=lambda: [TimeFrame.H1])
    
    # Configuration sections
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    # Symbol-specific configurations
    symbol_configs: Dict[str, SymbolConfig] = field(default_factory=dict)
    
    # System settings
    enable_logging: bool = True
    log_level: str = "INFO"
    log_file: Optional[str] = "smc_system.log"
    
    # Development settings
    debug_mode: bool = False
    enable_profiling: bool = False
    
    def __post_init__(self):
        """Initialize symbol configs if not provided"""
        if not self.symbol_configs:
            for symbol in self.symbols:
                self.symbol_configs[symbol] = SymbolConfig(symbol=symbol)
    
    def get_symbol_config(self, symbol: str) -> SymbolConfig:
        """Get configuration for a specific symbol"""
        return self.symbol_configs.get(symbol, SymbolConfig(symbol=symbol))
    
    def add_symbol(self, symbol: str, config: Optional[SymbolConfig] = None) -> None:
        """Add a new symbol to the configuration"""
        if symbol not in self.symbols:
            self.symbols.append(symbol)
        
        if config is None:
            config = SymbolConfig(symbol=symbol)
        
        self.symbol_configs[symbol] = config
    
    def remove_symbol(self, symbol: str) -> None:
        """Remove a symbol from the configuration"""
        if symbol in self.symbols:
            self.symbols.remove(symbol)
        
        if symbol in self.symbol_configs:
            del self.symbol_configs[symbol]
    
    def get_enabled_symbols(self) -> List[str]:
        """Get list of enabled symbols"""
        return [
            symbol for symbol in self.symbols
            if self.symbol_configs.get(symbol, SymbolConfig(symbol)).enabled
        ]
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate symbol count
        if len(self.symbols) > self.performance.max_symbols:
            errors.append(f"Too many symbols: {len(self.symbols)} > {self.performance.max_symbols}")
        
        # Validate timeframes
        if not self.enabled_timeframes:
            errors.append("At least one timeframe must be enabled")
        
        # Validate performance settings
        if self.performance.max_memory_mb < 100:
            errors.append("Max memory too low: minimum 100MB required")
        
        if self.performance.batch_size > len(self.symbols):
            errors.append("Batch size cannot exceed number of symbols")
        
        # Validate trading settings
        if not (self.trading.min_swing_length <= self.trading.default_swing_length <= self.trading.max_swing_length):
            errors.append("Invalid swing length configuration")
        
        return errors


# Default configuration instance
DEFAULT_SMC_SETTINGS = SMCSettings()


def load_settings_from_env() -> SMCSettings:
    """Load settings from environment variables"""
    settings = SMCSettings()
    
    # Load symbols from environment
    symbols_env = os.getenv('SMC_SYMBOLS')
    if symbols_env:
        settings.symbols = [s.strip() for s in symbols_env.split(',')]
    
    # Load timeframe
    timeframe_env = os.getenv('SMC_TIMEFRAME', 'H1')
    try:
        settings.default_timeframe = TimeFrame(timeframe_env.lower())
    except ValueError:
        pass  # Use default
    
    # Load performance settings
    max_symbols = os.getenv('SMC_MAX_SYMBOLS')
    if max_symbols:
        settings.performance.max_symbols = int(max_symbols)
    
    max_memory = os.getenv('SMC_MAX_MEMORY_MB')
    if max_memory:
        settings.performance.max_memory_mb = int(max_memory)
    
    # Load trading settings
    swing_length = os.getenv('SMC_SWING_LENGTH')
    if swing_length:
        settings.trading.default_swing_length = int(swing_length)
    
    box_width = os.getenv('SMC_BOX_WIDTH')
    if box_width:
        settings.trading.default_box_width = float(box_width)
    
    return settings


def save_settings_to_file(settings: SMCSettings, file_path: str) -> None:
    """Save settings to a JSON file"""
    import json
    from dataclasses import asdict
    
    # Convert dataclass to dict
    settings_dict = asdict(settings)
    
    # Convert enums to strings
    def convert_enums(obj):
        if isinstance(obj, dict):
            return {k: convert_enums(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_enums(item) for item in obj]
        elif hasattr(obj, 'value'):  # Enum
            return obj.value
        return obj
    
    settings_dict = convert_enums(settings_dict)
    
    # Save to file
    with open(file_path, 'w') as f:
        json.dump(settings_dict, f, indent=2)


def load_settings_from_file(file_path: str) -> SMCSettings:
    """Load settings from a JSON file"""
    import json
    
    if not Path(file_path).exists():
        return DEFAULT_SMC_SETTINGS
    
    with open(file_path, 'r') as f:
        settings_dict = json.load(f)
    
    # TODO: Implement proper deserialization from dict to SMCSettings
    # For now, return default settings
    return DEFAULT_SMC_SETTINGS


# Example usage and testing
if __name__ == "__main__":
    # Create default settings
    settings = SMCSettings()
    
    # Add some custom symbols
    settings.add_symbol("BNBUSDT")
    settings.add_symbol("FTMUSDT")
    
    # Validate configuration
    errors = settings.validate_config()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration is valid")
    
    # Print summary
    print(f"\n📊 SMC Configuration Summary:")
    print(f"   Symbols: {len(settings.symbols)} ({len(settings.get_enabled_symbols())} enabled)")
    print(f"   Timeframe: {settings.default_timeframe.value}")
    print(f"   Max Memory: {settings.performance.max_memory_mb}MB")
    print(f"   Swing Length: {settings.trading.default_swing_length}")
    print(f"   Box Width: {settings.trading.default_box_width}")
    print(f"   Caching: {'Enabled' if settings.performance.enable_caching else 'Disabled'}")