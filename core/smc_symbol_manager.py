#!/usr/bin/env python3
"""
SMC Symbol Manager
Multi-symbol context management system for 20-40 cryptocurrency pairs
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

from config.config_manager import get_config
from core.smc_context import SMCContext, ContextConfig, ContextStatus, ContextStats
from utils.array_ops import get_buffer_manager

logger = logging.getLogger(__name__)


class ManagerStatus(Enum):
    """Manager status enumeration"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ManagerStats:
    """Statistics for SMC Symbol Manager"""
    status: ManagerStatus
    total_symbols: int = 0
    active_symbols: int = 0
    paused_symbols: int = 0
    error_symbols: int = 0
    total_updates: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    total_memory_mb: float = 0.0
    avg_processing_time_ms: float = 0.0
    uptime_seconds: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    last_update_time: datetime = field(default_factory=datetime.now)


class SMCSymbolManager:
    """
    Multi-symbol context management system
    Manages SMC analysis contexts for 20-40 cryptocurrency pairs simultaneously
    """
    
    def __init__(self, symbols: Optional[List[str]] = None, max_workers: Optional[int] = None):
        self.config = get_config()
        self.symbols = symbols or self.config.symbols
        self.max_workers = max_workers or self.config.max_workers
        
        # Manager state
        self._status = ManagerStatus.INITIALIZING
        self._lock = threading.RLock()
        self._stats = ManagerStats(status=self._status)
        
        # Context management
        self._contexts: Dict[str, SMCContext] = {}
        self._context_configs: Dict[str, ContextConfig] = {}
        self._executor: Optional[ThreadPoolExecutor] = None
        
        # Update management
        self._update_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._update_frequency = self.config.update_frequency_seconds
        
        # Event callbacks
        self._global_callbacks: Dict[str, List[Callable]] = {
            'symbol_added': [],
            'symbol_removed': [],
            'context_error': [],
            'manager_status_changed': []
        }
        
        # Performance monitoring
        self._performance_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
        
        logger.info(f"🔧 SMCSymbolManager initialized for {len(self.symbols)} symbols")
    
    def initialize(self) -> bool:
        """
        Initialize the symbol manager and all contexts
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            with self._lock:
                logger.info(f"🚀 Initializing SMC Symbol Manager...")
                logger.info(f"   Symbols: {len(self.symbols)} ({self.symbols[:5]}{'...' if len(self.symbols) > 5 else ''})")
                logger.info(f"   Max workers: {self.max_workers}")
                logger.info(f"   Update frequency: {self._update_frequency}s")
                
                # Initialize thread pool
                self._executor = ThreadPoolExecutor(
                    max_workers=self.max_workers,
                    thread_name_prefix="SMC-Worker"
                )
                
                # Create context configurations
                self._create_context_configs()
                
                # Initialize contexts in parallel
                if not self._initialize_contexts_parallel():
                    logger.error("❌ Failed to initialize contexts")
                    return False
                
                # Start update thread
                self._start_update_thread()
                
                # Update status
                self._status = ManagerStatus.RUNNING
                self._stats.status = self._status
                self._stats.start_time = datetime.now()
                
                # Trigger status change callback
                self._trigger_global_event('manager_status_changed', {
                    'old_status': ManagerStatus.INITIALIZING,
                    'new_status': self._status
                })
                
                logger.info(f"✅ SMC Symbol Manager initialized successfully")
                logger.info(f"   Active contexts: {len([c for c in self._contexts.values() if c.get_stats().status == ContextStatus.ACTIVE])}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize SMC Symbol Manager: {e}")
            self._status = ManagerStatus.ERROR
            self._stats.status = self._status
            return False
    
    def _create_context_configs(self) -> None:
        """Create context configurations for all symbols"""
        for symbol in self.symbols:
            config = ContextConfig(
                symbol=symbol,
                timeframe=self.config.timeframe,
                swing_length=self.config.swing_length,
                history_limit=self.config.history_limit,
                box_width=self.config.box_width,
                atr_period=self.config.atr_period,
                update_frequency_seconds=self._update_frequency
            )
            self._context_configs[symbol] = config
        
        logger.debug(f"📋 Created configurations for {len(self._context_configs)} symbols")
    
    def _initialize_contexts_parallel(self) -> bool:
        """Initialize all contexts in parallel"""
        logger.info(f"🔄 Initializing {len(self.symbols)} contexts in parallel...")
        
        # Submit initialization tasks
        future_to_symbol = {}
        for symbol in self.symbols:
            future = self._executor.submit(self._initialize_single_context, symbol)
            future_to_symbol[future] = symbol
        
        # Collect results
        successful_contexts = 0
        failed_contexts = 0
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                success = future.result(timeout=30)  # 30 second timeout per context
                if success:
                    successful_contexts += 1
                    logger.info(f"✅ Context initialized: {symbol}")
                else:
                    failed_contexts += 1
                    logger.error(f"❌ Context failed: {symbol}")
            except Exception as e:
                failed_contexts += 1
                logger.error(f"❌ Context exception for {symbol}: {e}")
        
        logger.info(f"📊 Context initialization complete:")
        logger.info(f"   Successful: {successful_contexts}")
        logger.info(f"   Failed: {failed_contexts}")
        
        # Consider successful if at least 50% of contexts initialized
        success_rate = successful_contexts / len(self.symbols) if self.symbols else 0
        return success_rate >= 0.5
    
    def _initialize_single_context(self, symbol: str) -> bool:
        """Initialize a single context"""
        try:
            config = self._context_configs[symbol]
            context = SMCContext(symbol, config)
            
            # Add event callbacks
            context.add_event_callback('zone_created', self._on_zone_created)
            context.add_event_callback('swing_detected', self._on_swing_detected)
            context.add_event_callback('poi_calculated', self._on_poi_calculated)
            context.add_event_callback('bos_detected', self._on_bos_detected)
            context.add_event_callback('error_occurred', self._on_context_error)
            
            # Initialize context
            if context.initialize():
                with self._lock:
                    self._contexts[symbol] = context
                return True
            else:
                logger.error(f"❌ Failed to initialize context for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception initializing context for {symbol}: {e}")
            return False
    
    def _start_update_thread(self) -> None:
        """Start the update thread for continuous processing"""
        self._update_thread = threading.Thread(
            target=self._update_loop,
            name="SMC-UpdateLoop",
            daemon=True
        )
        self._update_thread.start()
        logger.info(f"🔄 Update thread started with {self._update_frequency}s frequency")
    
    def _update_loop(self) -> None:
        """Main update loop for processing all contexts"""
        logger.info(f"🔄 SMC update loop started")
        
        while not self._stop_event.is_set():
            try:
                if self._status == ManagerStatus.RUNNING:
                    self._update_all_contexts()
                
                # Wait for next update cycle
                self._stop_event.wait(self._update_frequency)
                
            except Exception as e:
                logger.error(f"❌ Error in update loop: {e}")
                time.sleep(5)  # Brief pause before retrying
    
    def _update_all_contexts(self) -> None:
        """Update all active contexts"""
        start_time = time.time()
        
        # Get active contexts
        active_contexts = [
            (symbol, context) for symbol, context in self._contexts.items()
            if context.get_stats().status == ContextStatus.ACTIVE
        ]
        
        if not active_contexts:
            return
        
        logger.debug(f"🔄 Updating {len(active_contexts)} active contexts...")
        
        # Submit update tasks
        future_to_symbol = {}
        for symbol, context in active_contexts:
            future = self._executor.submit(self._update_single_context, symbol, context)
            future_to_symbol[future] = symbol
        
        # Collect results
        successful_updates = 0
        failed_updates = 0
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                success = future.result(timeout=10)  # 10 second timeout per update
                if success:
                    successful_updates += 1
                else:
                    failed_updates += 1
            except Exception as e:
                failed_updates += 1
                logger.error(f"❌ Update exception for {symbol}: {e}")
        
        # Update manager statistics
        total_time = time.time() - start_time
        self._update_manager_stats(successful_updates, failed_updates, total_time)
        
        logger.debug(f"✅ Update cycle complete: {successful_updates} success, {failed_updates} failed in {total_time:.2f}s")
    
    def _update_single_context(self, symbol: str, context: SMCContext) -> bool:
        """Update a single context"""
        try:
            return context.update()
        except Exception as e:
            logger.error(f"❌ Failed to update context {symbol}: {e}")
            return False
    
    def _update_manager_stats(self, successful: int, failed: int, total_time: float) -> None:
        """Update manager statistics"""
        with self._lock:
            self._stats.total_updates += successful + failed
            self._stats.successful_updates += successful
            self._stats.failed_updates += failed
            self._stats.last_update_time = datetime.now()
            
            # Calculate uptime
            self._stats.uptime_seconds = (datetime.now() - self._stats.start_time).total_seconds()
            
            # Update symbol counts
            self._update_symbol_counts()
            
            # Update memory usage
            self._update_memory_usage()
            
            # Update average processing time
            if successful + failed > 0:
                self._stats.avg_processing_time_ms = (total_time * 1000) / (successful + failed)
            
            # Store performance history
            self._store_performance_data(successful, failed, total_time)
    
    def _update_symbol_counts(self) -> None:
        """Update symbol status counts"""
        self._stats.total_symbols = len(self._contexts)
        self._stats.active_symbols = 0
        self._stats.paused_symbols = 0
        self._stats.error_symbols = 0
        
        for context in self._contexts.values():
            status = context.get_stats().status
            if status == ContextStatus.ACTIVE:
                self._stats.active_symbols += 1
            elif status == ContextStatus.PAUSED:
                self._stats.paused_symbols += 1
            elif status == ContextStatus.ERROR:
                self._stats.error_symbols += 1
    
    def _update_memory_usage(self) -> None:
        """Update total memory usage"""
        total_memory = 0.0
        for context in self._contexts.values():
            total_memory += context.get_stats().memory_usage_mb
        self._stats.total_memory_mb = total_memory
    
    def _store_performance_data(self, successful: int, failed: int, total_time: float) -> None:
        """Store performance data for monitoring"""
        perf_data = {
            'timestamp': datetime.now(),
            'successful_updates': successful,
            'failed_updates': failed,
            'total_time_seconds': total_time,
            'active_symbols': self._stats.active_symbols,
            'memory_usage_mb': self._stats.total_memory_mb
        }
        
        self._performance_history.append(perf_data)
        
        # Limit history size
        if len(self._performance_history) > self._max_history_size:
            self._performance_history = self._performance_history[-self._max_history_size:]
    
    # Event handlers
    def _on_zone_created(self, symbol: str, event_type: str, data: Any) -> None:
        """Handle zone created event"""
        logger.debug(f"🏢 Zone created for {symbol}: {data['type']} at ${data['poi']:.2f}")
    
    def _on_swing_detected(self, symbol: str, event_type: str, data: Any) -> None:
        """Handle swing detected event"""
        logger.debug(f"📈 Swing detected for {symbol}: {data['type']} at ${data['price']:.2f}")
    
    def _on_poi_calculated(self, symbol: str, event_type: str, data: Any) -> None:
        """Handle POI calculated event"""
        logger.debug(f"🎯 POI calculated for {symbol}: {data['type']} at ${data['price']:.2f}")
    
    def _on_bos_detected(self, symbol: str, event_type: str, data: Any) -> None:
        """Handle BOS detected event"""
        logger.info(f"💥 BOS detected for {symbol}: {data['zone_type']} broken at ${data['break_price']:.2f}")
    
    def _on_context_error(self, symbol: str, event_type: str, data: Any) -> None:
        """Handle context error event"""
        logger.error(f"❌ Context error for {symbol}: {data}")
        self._trigger_global_event('context_error', {'symbol': symbol, 'error': data})
    
    def _trigger_global_event(self, event_type: str, data: Any) -> None:
        """Trigger global event callbacks"""
        if event_type in self._global_callbacks:
            for callback in self._global_callbacks[event_type]:
                try:
                    callback(event_type, data)
                except Exception as e:
                    logger.error(f"❌ Global callback error: {e}")
    
    # Public interface methods
    def add_symbol(self, symbol: str, config: Optional[ContextConfig] = None) -> bool:
        """
        Add a new symbol to the manager
        
        Args:
            symbol: Trading symbol to add
            config: Optional context configuration
            
        Returns:
            True if symbol added successfully, False otherwise
        """
        symbol = symbol.upper()
        
        if symbol in self._contexts:
            logger.warning(f"⚠️ Symbol {symbol} already exists")
            return False
        
        try:
            with self._lock:
                # Create config if not provided
                if config is None:
                    config = ContextConfig(
                        symbol=symbol,
                        timeframe=self.config.timeframe,
                        swing_length=self.config.swing_length,
                        history_limit=self.config.history_limit,
                        box_width=self.config.box_width,
                        atr_period=self.config.atr_period
                    )
                
                self._context_configs[symbol] = config
                
                # Initialize context
                if self._initialize_single_context(symbol):
                    self.symbols.append(symbol)
                    self._trigger_global_event('symbol_added', {'symbol': symbol})
                    logger.info(f"✅ Symbol added: {symbol}")
                    return True
                else:
                    logger.error(f"❌ Failed to add symbol: {symbol}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Exception adding symbol {symbol}: {e}")
            return False
    
    def remove_symbol(self, symbol: str) -> bool:
        """
        Remove a symbol from the manager
        
        Args:
            symbol: Trading symbol to remove
            
        Returns:
            True if symbol removed successfully, False otherwise
        """
        symbol = symbol.upper()
        
        if symbol not in self._contexts:
            logger.warning(f"⚠️ Symbol {symbol} not found")
            return False
        
        try:
            with self._lock:
                # Stop context
                context = self._contexts[symbol]
                context.stop()
                
                # Remove from collections
                del self._contexts[symbol]
                del self._context_configs[symbol]
                
                if symbol in self.symbols:
                    self.symbols.remove(symbol)
                
                # Cleanup buffers
                buffer_manager = get_buffer_manager()
                buffer_manager.remove_symbol(symbol)
                
                self._trigger_global_event('symbol_removed', {'symbol': symbol})
                logger.info(f"🗑️ Symbol removed: {symbol}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Exception removing symbol {symbol}: {e}")
            return False
    
    def get_context(self, symbol: str) -> Optional[SMCContext]:
        """Get context for specific symbol"""
        return self._contexts.get(symbol.upper())
    
    def get_all_contexts(self) -> Dict[str, SMCContext]:
        """Get all contexts"""
        with self._lock:
            return self._contexts.copy()
    
    def get_symbol_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current data for specific symbol"""
        context = self.get_context(symbol)
        return context.get_current_data() if context else None
    
    def get_all_symbol_data(self) -> Dict[str, Dict[str, Any]]:
        """Get current data for all symbols"""
        with self._lock:
            return {
                symbol: context.get_current_data()
                for symbol, context in self._contexts.items()
            }
    
    def pause_symbol(self, symbol: str) -> bool:
        """Pause updates for specific symbol"""
        context = self.get_context(symbol)
        if context:
            context.pause()
            logger.info(f"⏸️ Symbol paused: {symbol}")
            return True
        return False
    
    def resume_symbol(self, symbol: str) -> bool:
        """Resume updates for specific symbol"""
        context = self.get_context(symbol)
        if context:
            context.resume()
            logger.info(f"▶️ Symbol resumed: {symbol}")
            return True
        return False
    
    def pause_all(self) -> None:
        """Pause all symbol updates"""
        with self._lock:
            self._status = ManagerStatus.PAUSED
            self._stats.status = self._status
            
            for context in self._contexts.values():
                context.pause()
            
            logger.info(f"⏸️ All symbols paused")
    
    def resume_all(self) -> None:
        """Resume all symbol updates"""
        with self._lock:
            self._status = ManagerStatus.RUNNING
            self._stats.status = self._status
            
            for context in self._contexts.values():
                context.resume()
            
            logger.info(f"▶️ All symbols resumed")
    
    def get_manager_stats(self) -> ManagerStats:
        """Get manager statistics"""
        with self._lock:
            return self._stats
    
    def get_performance_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get performance history"""
        with self._lock:
            if last_n:
                return self._performance_history[-last_n:]
            return self._performance_history.copy()
    
    def add_global_callback(self, event_type: str, callback: Callable) -> None:
        """Add global event callback"""
        if event_type in self._global_callbacks:
            self._global_callbacks[event_type].append(callback)
            logger.debug(f"📢 Global callback added: {event_type}")
    
    def stop(self) -> None:
        """Stop the symbol manager and cleanup resources"""
        logger.info(f"🛑 Stopping SMC Symbol Manager...")
        
        with self._lock:
            self._status = ManagerStatus.STOPPING
            self._stats.status = self._status
        
        # Stop update thread
        self._stop_event.set()
        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=5)
        
        # Stop all contexts
        for context in self._contexts.values():
            context.stop()
        
        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=True)
        
        with self._lock:
            self._status = ManagerStatus.STOPPED
            self._stats.status = self._status
        
        logger.info(f"✅ SMC Symbol Manager stopped")
    
    def __repr__(self) -> str:
        """String representation of manager"""
        return f"SMCSymbolManager(symbols={len(self._contexts)}, status={self._status.value}, active={self._stats.active_symbols})"


# Global manager instance
_symbol_manager = None


def get_symbol_manager() -> SMCSymbolManager:
    """Get global symbol manager instance"""
    global _symbol_manager
    if _symbol_manager is None:
        _symbol_manager = SMCSymbolManager()
    return _symbol_manager