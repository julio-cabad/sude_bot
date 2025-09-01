#!/usr/bin/env python3
"""
SMC Configuration Manager
Centralized configuration management system with hot-reload capability for multi-symbol SMC system
"""

import json
import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from dotenv import load_dotenv
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class SMCConfig:
    """Centralized SMC Configuration with multi-symbol support"""
    
    # Core settings - Support for 20-40 cryptocurrency pairs
    symbols: List[str] = field(default_factory=lambda: [
        "BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "XRPUSDT",
        "SOLUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "MATICUSDT",
        "LINKUSDT", "LTCUSDT", "UNIUSDT", "ATOMUSDT", "FTMUSDT",
        "NEARUSDT", "ALGOUSDT", "VETUSDT", "ICPUSDT", "FILUSDT"
    ])
    timeframe: str = "1h"
    
    # Trading parameters
    swing_length: int = 10
    history_limit: int = 20
    box_width: float = 2.5
    atr_period: int = 50
    atr_multiplier: float = 2.0
    overlap_threshold_multiplier: float = 2.0
    
    # Performance settings - Optimized for 20-40 symbols
    max_memory_mb: int = 500
    max_symbols: int = 40
    max_zones_per_symbol: int = 15
    max_swings_per_symbol: int = 50
    batch_size: int = 10
    max_workers: int = 8
    update_frequency_seconds: int = 60
    
    # Cache settings - Enhanced for multi-symbol performance
    enable_caching: bool = True
    cache_size_mb: int = 100
    cache_ttl_seconds: int = 300
    cache_strategy: str = "lru"  # lru, fifo, ttl
    
    # Visualization
    supply_color: str = "#EDEDED"
    supply_outline_color: str = "#FFFFFF"
    demand_color: str = "#00FFFF"
    demand_outline_color: str = "#FFFFFF"
    poi_color: str = "#FFFFFF"
    zigzag_color: str = "#000000"
    zone_transparency: int = 70
    show_zigzag: bool = False
    show_price_action_labels: bool = True
    show_poi_lines: bool = True
    
    # API settings
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 5
    max_candles_per_request: int = 1500
    
    # System settings
    enable_logging: bool = True
    log_level: str = "INFO"
    debug_mode: bool = False
    enable_profiling: bool = False
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate symbols
        if not self.symbols:
            errors.append("At least one symbol must be configured")
        
        if len(self.symbols) > self.max_symbols:
            errors.append(f"Too many symbols: {len(self.symbols)} > {self.max_symbols}")
        
        # Validate trading parameters
        if not (1 <= self.swing_length <= 50):
            errors.append("Swing length must be between 1 and 50")
        
        if not (1.0 <= self.box_width <= 10.0):
            errors.append("Box width must be between 1.0 and 10.0")
        
        if not (5 <= self.history_limit <= 100):
            errors.append("History limit must be between 5 and 100")
        
        # Validate performance settings
        if self.max_memory_mb < 50:
            errors.append("Max memory must be at least 50MB")
        
        if self.batch_size > len(self.symbols) and len(self.symbols) > 0:
            errors.append("Batch size cannot exceed number of symbols")
        
        # Validate timeframe
        valid_timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        if self.timeframe not in valid_timeframes:
            errors.append(f"Invalid timeframe: {self.timeframe}. Must be one of {valid_timeframes}")
        
        return errors
    
    def get_multi_symbol_config(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for all symbols"""
        return {
            symbol: self.get_symbol_config(symbol)
            for symbol in self.symbols
        }
    
    def is_symbol_enabled(self, symbol: str) -> bool:
        """Check if a symbol is enabled"""
        return symbol in self.symbols
    
    def get_symbol_config(self, symbol: str) -> Dict[str, Any]:
        """Get configuration for a specific symbol"""
        return {
            "symbol": symbol,
            "timeframe": self.timeframe,
            "swing_length": self.swing_length,
            "history_limit": self.history_limit,
            "box_width": self.box_width,
            "atr_period": self.atr_period,
            "enabled": symbol in self.symbols
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "symbols": self.symbols,
            "timeframe": self.timeframe,
            "trading": {
                "swing_length": self.swing_length,
                "history_limit": self.history_limit,
                "box_width": self.box_width,
                "atr_period": self.atr_period,
                "atr_multiplier": self.atr_multiplier,
                "overlap_threshold_multiplier": self.overlap_threshold_multiplier
            },
            "performance": {
                "max_memory_mb": self.max_memory_mb,
                "max_symbols": self.max_symbols,
                "max_zones_per_symbol": self.max_zones_per_symbol,
                "max_swings_per_symbol": self.max_swings_per_symbol,
                "batch_size": self.batch_size,
                "max_workers": self.max_workers,
                "update_frequency_seconds": self.update_frequency_seconds,
                "enable_caching": self.enable_caching,
                "cache_size_mb": self.cache_size_mb,
                "cache_ttl_seconds": self.cache_ttl_seconds
            },
            "visualization": {
                "supply_color": self.supply_color,
                "supply_outline_color": self.supply_outline_color,
                "demand_color": self.demand_color,
                "demand_outline_color": self.demand_outline_color,
                "poi_color": self.poi_color,
                "zigzag_color": self.zigzag_color,
                "zone_transparency": self.zone_transparency,
                "show_zigzag": self.show_zigzag,
                "show_price_action_labels": self.show_price_action_labels,
                "show_poi_lines": self.show_poi_lines
            },
            "api": {
                "timeout_seconds": self.timeout_seconds,
                "max_retries": self.max_retries,
                "retry_delay_seconds": self.retry_delay_seconds,
                "max_candles_per_request": self.max_candles_per_request
            },
            "system": {
                "enable_logging": self.enable_logging,
                "log_level": self.log_level,
                "debug_mode": self.debug_mode,
                "enable_profiling": self.enable_profiling
            }
        }


class ConfigFileWatcher(FileSystemEventHandler):
    """File system watcher for configuration hot-reload"""
    
    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager
        self.last_modified = 0
        self.debounce_seconds = 1.0  # Prevent multiple rapid reloads
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        # Check if it's our config file
        if event.src_path == str(self.config_manager.config_file):
            current_time = time.time()
            if current_time - self.last_modified > self.debounce_seconds:
                self.last_modified = current_time
                logger.info(f"🔄 Configuration file changed: {event.src_path}")
                try:
                    self.config_manager.reload_config()
                    logger.info("✅ Configuration hot-reloaded successfully")
                except Exception as e:
                    logger.error(f"❌ Failed to hot-reload configuration: {e}")


class ConfigManager:
    """Configuration Manager for SMC System with hot-reload capability"""
    
    def __init__(self, config_file: str = "config/smc_config.json", enable_hot_reload: bool = True):
        self.config_file = Path(config_file)
        self._config: Optional[SMCConfig] = None
        self._watchers: List[Callable[[SMCConfig], None]] = []
        self._file_observer: Optional[Observer] = None
        self._hot_reload_enabled = enable_hot_reload
        self._lock = threading.Lock()  # Thread safety for hot-reload
    
    def load_config(self) -> SMCConfig:
        """Load configuration from file and environment with thread safety"""
        with self._lock:
            config = SMCConfig()
            
            # Load from JSON file if exists
            if self.config_file.exists():
                try:
                    with open(self.config_file, 'r') as f:
                        data = json.load(f)
                    config = self._dict_to_config(data)
                    logger.info(f"✅ Configuration loaded from {self.config_file}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load config file: {e}. Using defaults.")
            else:
                logger.info(f"📝 Config file not found, creating default: {self.config_file}")
                self.save_config(config)
            
            # Override with environment variables
            config = self._load_from_env(config)
            
            # Validate configuration
            errors = config.validate()
            if errors:
                logger.error("❌ Configuration validation failed:")
                for error in errors:
                    logger.error(f"   - {error}")
                raise ValueError(f"Invalid configuration: {errors}")
            
            self._config = config
            
            # Setup hot-reload if enabled
            if self._hot_reload_enabled and self._file_observer is None:
                self._setup_hot_reload()
            
            logger.info(f"🎯 Configuration validated successfully for {len(config.symbols)} symbols")
            return config
    
    def _dict_to_config(self, data: Dict[str, Any]) -> SMCConfig:
        """Convert dictionary to SMCConfig"""
        config = SMCConfig()
        
        # Core settings
        config.symbols = data.get("symbols", config.symbols)
        config.timeframe = data.get("timeframe", config.timeframe)
        
        # Trading settings
        trading = data.get("trading", {})
        config.swing_length = trading.get("swing_length", config.swing_length)
        config.history_limit = trading.get("history_limit", config.history_limit)
        config.box_width = trading.get("box_width", config.box_width)
        config.atr_period = trading.get("atr_period", config.atr_period)
        config.atr_multiplier = trading.get("atr_multiplier", config.atr_multiplier)
        config.overlap_threshold_multiplier = trading.get("overlap_threshold_multiplier", config.overlap_threshold_multiplier)
        
        # Performance settings
        performance = data.get("performance", {})
        config.max_memory_mb = performance.get("max_memory_mb", config.max_memory_mb)
        config.max_symbols = performance.get("max_symbols", config.max_symbols)
        config.max_zones_per_symbol = performance.get("max_zones_per_symbol", config.max_zones_per_symbol)
        config.max_swings_per_symbol = performance.get("max_swings_per_symbol", config.max_swings_per_symbol)
        config.batch_size = performance.get("batch_size", config.batch_size)
        config.max_workers = performance.get("max_workers", config.max_workers)
        config.update_frequency_seconds = performance.get("update_frequency_seconds", config.update_frequency_seconds)
        config.enable_caching = performance.get("enable_caching", config.enable_caching)
        config.cache_size_mb = performance.get("cache_size_mb", config.cache_size_mb)
        config.cache_ttl_seconds = performance.get("cache_ttl_seconds", config.cache_ttl_seconds)
        config.cache_strategy = performance.get("cache_strategy", config.cache_strategy)
        
        # Visualization settings
        visualization = data.get("visualization", {})
        config.supply_color = visualization.get("supply_color", config.supply_color)
        config.supply_outline_color = visualization.get("supply_outline_color", config.supply_outline_color)
        config.demand_color = visualization.get("demand_color", config.demand_color)
        config.demand_outline_color = visualization.get("demand_outline_color", config.demand_outline_color)
        config.poi_color = visualization.get("poi_color", config.poi_color)
        config.zigzag_color = visualization.get("zigzag_color", config.zigzag_color)
        config.zone_transparency = visualization.get("zone_transparency", config.zone_transparency)
        config.show_zigzag = visualization.get("show_zigzag", config.show_zigzag)
        config.show_price_action_labels = visualization.get("show_price_action_labels", config.show_price_action_labels)
        config.show_poi_lines = visualization.get("show_poi_lines", config.show_poi_lines)
        
        # API settings
        api = data.get("api", {})
        config.timeout_seconds = api.get("timeout_seconds", config.timeout_seconds)
        config.max_retries = api.get("max_retries", config.max_retries)
        config.retry_delay_seconds = api.get("retry_delay_seconds", config.retry_delay_seconds)
        config.max_candles_per_request = api.get("max_candles_per_request", config.max_candles_per_request)
        
        # System settings
        system = data.get("system", {})
        config.enable_logging = system.get("enable_logging", config.enable_logging)
        config.log_level = system.get("log_level", config.log_level)
        config.debug_mode = system.get("debug_mode", config.debug_mode)
        config.enable_profiling = system.get("enable_profiling", config.enable_profiling)
        
        return config
    
    def _load_from_env(self, config: SMCConfig) -> SMCConfig:
        """Load configuration overrides from environment variables"""
        
        # Symbols from environment
        symbols_env = os.getenv('SMC_SYMBOLS')
        if symbols_env:
            config.symbols = [s.strip() for s in symbols_env.split(',')]
        
        # Timeframe
        timeframe_env = os.getenv('SMC_TIMEFRAME')
        if timeframe_env:
            config.timeframe = timeframe_env
        
        # Trading parameters
        swing_length_env = os.getenv('SMC_SWING_LENGTH')
        if swing_length_env:
            config.swing_length = int(swing_length_env)
        
        box_width_env = os.getenv('SMC_BOX_WIDTH')
        if box_width_env:
            config.box_width = float(box_width_env)
        
        history_limit_env = os.getenv('SMC_HISTORY_LIMIT')
        if history_limit_env:
            config.history_limit = int(history_limit_env)
        
        # Performance parameters
        max_memory_env = os.getenv('SMC_MAX_MEMORY_MB')
        if max_memory_env:
            config.max_memory_mb = int(max_memory_env)
        
        # Debug mode
        debug_env = os.getenv('SMC_DEBUG_MODE')
        if debug_env:
            config.debug_mode = debug_env.lower() in ['true', '1', 'yes']
        
        # Auto-adjust batch size if needed
        if config.batch_size > len(config.symbols) and len(config.symbols) > 0:
            config.batch_size = min(config.batch_size, len(config.symbols))
            logger.info(f"🔧 Auto-adjusted batch size to {config.batch_size} for {len(config.symbols)} symbols")
        
        return config
    
    def _setup_hot_reload(self) -> None:
        """Setup file system watcher for hot-reload"""
        try:
            self._file_observer = Observer()
            event_handler = ConfigFileWatcher(self)
            
            # Watch the directory containing the config file
            watch_path = self.config_file.parent
            self._file_observer.schedule(event_handler, str(watch_path), recursive=False)
            self._file_observer.start()
            
            logger.info(f"🔍 Hot-reload enabled for {self.config_file}")
        except ImportError:
            logger.warning("⚠️ watchdog not installed, hot-reload disabled")
            self._hot_reload_enabled = False
        except Exception as e:
            logger.error(f"❌ Failed to setup hot-reload: {e}")
            self._hot_reload_enabled = False
    
    def save_config(self, config: SMCConfig = None) -> None:
        """Save configuration to file"""
        if config is None:
            config = self._config
        
        if config is None:
            raise ValueError("No configuration to save")
        
        # Create config directory if it doesn't exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON file
        with open(self.config_file, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
        
        logger.info(f"💾 Configuration saved to {self.config_file}")
    
    def get_config(self) -> SMCConfig:
        """Get current configuration"""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> SMCConfig:
        """Reload configuration from file with hot-reload support"""
        logger.info("🔄 Reloading configuration...")
        old_config = self._config
        config = self.load_config()
        
        # Check for significant changes
        if old_config:
            changes = self._detect_config_changes(old_config, config)
            if changes:
                logger.info(f"📊 Configuration changes detected: {changes}")
        
        # Notify watchers
        for watcher in self._watchers:
            try:
                watcher(config)
            except Exception as e:
                logger.error(f"Error in config watcher: {e}")
        
        return config
    
    def _detect_config_changes(self, old_config: SMCConfig, new_config: SMCConfig) -> List[str]:
        """Detect significant changes between configurations"""
        changes = []
        
        # Check symbol changes
        old_symbols = set(old_config.symbols)
        new_symbols = set(new_config.symbols)
        
        added_symbols = new_symbols - old_symbols
        removed_symbols = old_symbols - new_symbols
        
        if added_symbols:
            changes.append(f"Added symbols: {list(added_symbols)}")
        if removed_symbols:
            changes.append(f"Removed symbols: {list(removed_symbols)}")
        
        # Check parameter changes
        if old_config.swing_length != new_config.swing_length:
            changes.append(f"Swing length: {old_config.swing_length} → {new_config.swing_length}")
        
        if old_config.timeframe != new_config.timeframe:
            changes.append(f"Timeframe: {old_config.timeframe} → {new_config.timeframe}")
        
        if old_config.max_symbols != new_config.max_symbols:
            changes.append(f"Max symbols: {old_config.max_symbols} → {new_config.max_symbols}")
        
        return changes
    
    def add_watcher(self, callback: Callable[[SMCConfig], None]) -> None:
        """Add configuration change watcher"""
        self._watchers.append(callback)
    
    def remove_watcher(self, callback: Callable[[SMCConfig], None]) -> None:
        """Remove configuration change watcher"""
        if callback in self._watchers:
            self._watchers.remove(callback)
    
    def update_symbols(self, symbols: List[str]) -> None:
        """Update symbols and save configuration with validation"""
        with self._lock:
            if self._config is None:
                self.load_config()
            
            # Validate symbol count
            if len(symbols) > self._config.max_symbols:
                raise ValueError(f"Too many symbols: {len(symbols)} > {self._config.max_symbols}")
            
            old_symbols = self._config.symbols.copy()
            self._config.symbols = symbols
            
            errors = self._config.validate()
            if errors:
                # Rollback on validation error
                self._config.symbols = old_symbols
                raise ValueError(f"Invalid symbols configuration: {errors}")
            
            self.save_config()
            logger.info(f"📊 Symbols updated: {len(symbols)} symbols configured")
    
    def add_symbol(self, symbol: str) -> None:
        """Add a single symbol to configuration"""
        if self._config is None:
            self.load_config()
        
        if symbol not in self._config.symbols:
            new_symbols = self._config.symbols + [symbol]
            self.update_symbols(new_symbols)
    
    def remove_symbol(self, symbol: str) -> None:
        """Remove a single symbol from configuration"""
        if self._config is None:
            self.load_config()
        
        if symbol in self._config.symbols:
            new_symbols = [s for s in self._config.symbols if s != symbol]
            self.update_symbols(new_symbols)
    
    def get_symbol_batch(self, batch_size: Optional[int] = None) -> List[List[str]]:
        """Get symbols divided into batches for processing"""
        if self._config is None:
            self.load_config()
        
        batch_size = batch_size or self._config.batch_size
        symbols = self._config.symbols
        
        return [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
    
    def stop_hot_reload(self) -> None:
        """Stop the hot-reload file watcher"""
        if self._file_observer:
            self._file_observer.stop()
            self._file_observer.join()
            self._file_observer = None
            logger.info("🛑 Hot-reload stopped")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_hot_reload()


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> SMCConfig:
    """Get global configuration instance"""
    return config_manager.get_config()


def reload_config() -> SMCConfig:
    """Reload global configuration"""
    return config_manager.reload_config()


# Example usage and testing
if __name__ == "__main__":
    # Test configuration manager
    print("🧪 Testing SMC Configuration Manager...")
    print("=" * 50)
    
    try:
        # Load configuration
        config = config_manager.load_config()
        
        print(f"✅ Configuration loaded successfully")
        print(f"📊 Symbols: {config.symbols}")
        print(f"⏰ Timeframe: {config.timeframe}")
        print(f"🎯 Swing Length: {config.swing_length}")
        print(f"📦 Box Width: {config.box_width}")
        print(f"💾 Memory Limit: {config.max_memory_mb}MB")
        print(f"🚀 Caching: {'Enabled' if config.enable_caching else 'Disabled'}")
        
        # Test symbol configuration
        print(f"\n📈 BTC Configuration:")
        btc_config = config.get_symbol_config("BTCUSDT")
        for key, value in btc_config.items():
            print(f"   {key}: {value}")
        
        # Test validation
        print(f"\n🔍 Validation:")
        errors = config.validate()
        if errors:
            print("❌ Validation errors:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("✅ Configuration is valid")
        
        # Test save/reload
        print(f"\n💾 Testing save/reload...")
        config_manager.save_config()
        reloaded_config = config_manager.reload_config()
        print(f"✅ Save/reload successful")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()