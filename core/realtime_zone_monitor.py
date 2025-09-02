#!/usr/bin/env python3
"""
🔥⚔️ REAL TIME ZONE MONITOR - MONITOR SUPREMO DE ZONAS ⚔️🔥
Sistema de monitoreo que haría llorar a Leonidas y sus 300
Created by TITANES DEL CÓDIGO - BESTIAS SUPREMAS
"""

import os
import sys
import time
import threading
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass
from enum import Enum
import traceback

# Nuestros módulos épicos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.timeframe_adapter import TimeframeAdapter, TimeframeInfo
from core.alert_engine import AlertEngine, EpicAlert, AlertType
from models.zone_alert import ZoneAlert, EcuadorTimeUtils, AlertPriority


class MonitoringState(Enum):
    """🚨 ESTADOS DE MONITORING ÉPICOS 🚨"""
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


@dataclass
class MonitoringSession:
    """📊 SESIÓN DE MONITORING ÉPICA 📊"""
    session_id: str
    symbols: Set[str]
    timeframe: str
    start_time: datetime
    state: MonitoringState
    total_checks: int = 0
    zones_detected: int = 0
    alerts_sent: int = 0
    last_check: Optional[datetime] = None
    last_zone_time: Optional[datetime] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class RealTimeZoneMonitor:
    """🔥⚔️ MONITOR DE ZONAS EN TIEMPO REAL SUPREMO ⚔️🔥"""
    
    def __init__(self, 
                 timeframe: str = "1h",
                 enable_alerts: bool = True,
                 enable_sound: bool = True,
                 max_errors: int = 10):
        
        print("🔥⚔️🏛️ INITIALIZING EPIC REAL TIME ZONE MONITOR 🏛️⚔️🔥")
        print("🎯 LEONIDAS Y SUS 300 APPROVED!")
        
        # Configuración
        self.timeframe = timeframe
        self.enable_alerts = enable_alerts
        self.enable_sound = enable_sound
        self.max_errors = max_errors
        
        # Componentes épicos
        self.timeframe_adapter = TimeframeAdapter()
        self.alert_engine = AlertEngine(enable_sound=enable_sound) if enable_alerts else None
        
        # Validar timeframe
        if not self.timeframe_adapter.validate_timeframe(timeframe):
            raise ValueError(f"❌ Invalid timeframe: {timeframe}")
        
        self.timeframe_info = self.timeframe_adapter.parse_timeframe(timeframe)
        
        # Estado del monitor
        self.state = MonitoringState.STOPPED
        self.symbols: Set[str] = set()
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Sesión actual
        self.current_session: Optional[MonitoringSession] = None
        
        # Callbacks épicos
        self.zone_detected_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        self.state_change_callbacks: List[Callable] = []
        
        # Estadísticas
        self.total_sessions = 0
        self.total_runtime = timedelta()
        
        # Manejo de señales para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("✅ Real Time Zone Monitor initialized successfully!")
        print(f"📊 Timeframe: {self.timeframe_info.display_name}")
        print(f"🔊 Alerts: {'ENABLED' if enable_alerts else 'DISABLED'}")
        print(f"🎵 Sound: {'ENABLED' if enable_sound else 'DISABLED'}")
    
    def add_symbol(self, symbol: str) -> bool:
        """
        ➕ AÑADE SÍMBOLO PARA MONITORING
        Args:
            symbol: Símbolo a monitorear (ej: "ETHUSDT")
        Returns:
            True si se añadió correctamente
        """
        try:
            symbol = symbol.upper().strip()
            
            if not symbol:
                raise ValueError("❌ Symbol cannot be empty")
            
            if symbol in self.symbols:
                print(f"⚠️ Symbol {symbol} already being monitored")
                return False
            
            self.symbols.add(symbol)
            print(f"✅ Added symbol: {symbol}")
            
            # Actualizar sesión si está activa
            if self.current_session:
                self.current_session.symbols = self.symbols.copy()
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding symbol {symbol}: {e}")
            return False
    
    def remove_symbol(self, symbol: str) -> bool:
        """
        ➖ REMUEVE SÍMBOLO DEL MONITORING
        Args:
            symbol: Símbolo a remover
        Returns:
            True si se removió correctamente
        """
        try:
            symbol = symbol.upper().strip()
            
            if symbol not in self.symbols:
                print(f"⚠️ Symbol {symbol} not being monitored")
                return False
            
            self.symbols.remove(symbol)
            print(f"✅ Removed symbol: {symbol}")
            
            # Actualizar sesión si está activa
            if self.current_session:
                self.current_session.symbols = self.symbols.copy()
            
            return True
            
        except Exception as e:
            print(f"❌ Error removing symbol {symbol}: {e}")
            return False
    
    def get_monitored_symbols(self) -> List[str]:
        """📋 OBTIENE LISTA DE SÍMBOLOS MONITOREADOS"""
        return sorted(list(self.symbols))
    
    def start_monitoring(self) -> bool:
        """
        🚀 INICIA EL MONITORING ÉPICO
        Returns:
            True si se inició correctamente
        """
        try:
            if self.state == MonitoringState.RUNNING:
                print("⚠️ Monitoring already running")
                return False
            
            if not self.symbols:
                print("❌ No symbols to monitor. Add symbols first.")
                return False
            
            print("🚀 Starting epic monitoring...")
            
            # Cambiar estado
            self._change_state(MonitoringState.STARTING)
            
            # Crear nueva sesión
            self.current_session = MonitoringSession(
                session_id=f"SESSION_{int(time.time())}",
                symbols=self.symbols.copy(),
                timeframe=self.timeframe,
                start_time=EcuadorTimeUtils.now(),
                state=MonitoringState.STARTING
            )
            
            self.total_sessions += 1
            
            # Iniciar alert engine si está habilitado
            if self.alert_engine:
                self.alert_engine.start()
            
            # Reset stop event
            self.stop_event.clear()
            
            # Crear y iniciar thread de monitoring
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="ZoneMonitoringThread",
                daemon=True
            )
            
            self.monitoring_thread.start()
            
            # Cambiar a running
            self._change_state(MonitoringState.RUNNING)
            
            print("✅ Monitoring started successfully!")
            print(f"📊 Symbols: {list(self.symbols)}")
            print(f"⏰ Timeframe: {self.timeframe_info.display_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting monitoring: {e}")
            self._change_state(MonitoringState.ERROR)
            return False
    
    def stop_monitoring(self, timeout: float = 10.0) -> bool:
        """
        🛑 DETIENE EL MONITORING CON CLEANUP GRACEFUL
        Args:
            timeout: Timeout para esperar el shutdown
        Returns:
            True si se detuvo correctamente
        """
        try:
            if self.state == MonitoringState.STOPPED:
                print("⚠️ Monitoring already stopped")
                return True
            
            print("🛑 Stopping monitoring...")
            
            # Cambiar estado
            self._change_state(MonitoringState.STOPPING)
            
            # Señalar parada
            self.stop_event.set()
            
            # Esperar thread de monitoring
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=timeout)
                
                if self.monitoring_thread.is_alive():
                    print("⚠️ Monitoring thread did not stop gracefully")
            
            # Detener alert engine
            if self.alert_engine:
                self.alert_engine.stop()
            
            # Finalizar sesión
            if self.current_session:
                self.current_session.state = MonitoringState.STOPPED
                runtime = EcuadorTimeUtils.now() - self.current_session.start_time
                self.total_runtime += runtime
                
                print(f"📊 Session completed:")
                print(f"   Duration: {runtime}")
                print(f"   Checks: {self.current_session.total_checks}")
                print(f"   Zones: {self.current_session.zones_detected}")
                print(f"   Alerts: {self.current_session.alerts_sent}")
            
            # Cambiar estado final
            self._change_state(MonitoringState.STOPPED)
            
            print("✅ Monitoring stopped successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping monitoring: {e}")
            self._change_state(MonitoringState.ERROR)
            return False
    
    def pause_monitoring(self) -> bool:
        """⏸️ PAUSA EL MONITORING"""
        if self.state == MonitoringState.RUNNING:
            self._change_state(MonitoringState.PAUSED)
            print("⏸️ Monitoring paused")
            return True
        return False
    
    def resume_monitoring(self) -> bool:
        """▶️ REANUDA EL MONITORING"""
        if self.state == MonitoringState.PAUSED:
            self._change_state(MonitoringState.RUNNING)
            print("▶️ Monitoring resumed")
            return True
        return False
    
    def _monitoring_loop(self):
        """⚔️ LOOP PRINCIPAL DE MONITORING - EL CORAZÓN ÉPICO"""
        print("⚔️ Starting epic monitoring loop...")
        
        # Calcular sleep duration
        sleep_duration = self.timeframe_adapter.get_sleep_duration(self.timeframe_info)
        print(f"⏰ Check interval: {sleep_duration:.1f} seconds")
        
        consecutive_errors = 0
        
        while not self.stop_event.is_set():
            try:
                # Verificar si estamos pausados
                if self.state == MonitoringState.PAUSED:
                    time.sleep(1.0)
                    continue
                
                # Verificar si debemos parar
                if self.state != MonitoringState.RUNNING:
                    break
                
                # Procesar cada símbolo
                for symbol in list(self.symbols):  # Copia para evitar modificaciones concurrentes
                    if self.stop_event.is_set():
                        break
                    
                    try:
                        self._process_symbol(symbol)
                        consecutive_errors = 0  # Reset contador de errores
                        
                    except Exception as e:
                        consecutive_errors += 1
                        error_msg = f"Error processing {symbol}: {e}"
                        print(f"❌ {error_msg}")
                        
                        # Añadir a errores de sesión
                        if self.current_session:
                            self.current_session.errors.append(error_msg)
                        
                        # Llamar callbacks de error
                        self._call_error_callbacks(symbol, e)
                        
                        # Si hay demasiados errores consecutivos, parar
                        if consecutive_errors >= self.max_errors:
                            print(f"❌ Too many consecutive errors ({consecutive_errors}). Stopping monitoring.")
                            self.stop_event.set()
                            break
                
                # Actualizar estadísticas de sesión
                if self.current_session:
                    self.current_session.total_checks += 1
                    self.current_session.last_check = EcuadorTimeUtils.now()
                
                # Sleep hasta próximo check
                if not self.stop_event.is_set():
                    self.stop_event.wait(timeout=sleep_duration)
                
            except Exception as e:
                print(f"❌ Critical error in monitoring loop: {e}")
                traceback.print_exc()
                
                consecutive_errors += 1
                if consecutive_errors >= self.max_errors:
                    print("❌ Too many critical errors. Stopping monitoring.")
                    break
                
                # Sleep antes de reintentar
                time.sleep(5.0)
        
        print("⚔️ Monitoring loop ended")
    
    def _process_symbol(self, symbol: str):
        """
        🏛️ PROCESA UN SÍMBOLO INDIVIDUAL
        Args:
            symbol: Símbolo a procesar
        """
        try:
            # Aquí iría la lógica de detección de zonas
            # Por ahora simulamos con un placeholder
            
            print(f"🔍 Checking {symbol} on {self.timeframe}...")
            
            # TODO: Integrar con ImplacableZonesDetector
            # detector = ImplacableZonesDetector()
            # zones = detector.detect_zones(symbol, self.timeframe)
            
            # Simulación temporal
            zones_detected = self._simulate_zone_detection(symbol)
            
            if zones_detected:
                
                # Actualizar estadísticas
                if self.current_session:
                    self.current_session.zones_detected += len(zones_detected)
                    self.current_session.last_zone_time = EcuadorTimeUtils.now()
                
                # Procesar cada zona
                for zone_data in zones_detected:
                    self._handle_new_zone(symbol, zone_data)
            
        except Exception as e:
            raise Exception(f"Failed to process {symbol}: {e}")
    
    def _simulate_zone_detection(self, symbol: str) -> List[Dict]:
        """
        🎭 SIMULACIÓN TEMPORAL DE DETECCIÓN DE ZONAS
        Args:
            symbol: Símbolo a simular
        Returns:
            Lista de zonas detectadas (vacía en simulación)
        """
        # Por ahora retornamos lista vacía
        # En implementación real, aquí iría la detección real
        return []
    
    def _handle_new_zone(self, symbol: str, zone_data: Dict):
        """
        🏛️ MANEJA UNA NUEVA ZONA DETECTADA
        Args:
            symbol: Símbolo de la zona
            zone_data: Datos de la zona
        """
        try:
            
            # Llamar callbacks de zona detectada
            self._call_zone_detected_callbacks(symbol, zone_data)
            
            # Enviar alerta si está habilitado
            if self.alert_engine:
                alert = self.alert_engine.create_zone_alert(symbol, zone_data)
                self.alert_engine.send_alert(alert)
                
                # Actualizar contador de alertas
                if self.current_session:
                    self.current_session.alerts_sent += 1
            
        except Exception as e:
            print(f"❌ Error handling new zone: {e}")
    
    def _change_state(self, new_state: MonitoringState):
        """
        🔄 CAMBIA EL ESTADO DEL MONITOR
        Args:
            new_state: Nuevo estado
        """
        old_state = self.state
        self.state = new_state
        
        print(f"🔄 State changed: {old_state.value} -> {new_state.value}")
        
        # Actualizar sesión si existe
        if self.current_session:
            self.current_session.state = new_state
        
        # Llamar callbacks de cambio de estado
        self._call_state_change_callbacks(old_state, new_state)
    
    def _signal_handler(self, signum, frame):
        """🛡️ MANEJA SEÑALES DEL SISTEMA PARA SHUTDOWN GRACEFUL"""
        print(f"\n🛡️ Received signal {signum}. Initiating graceful shutdown...")
        self.stop_monitoring()
    
    # Callbacks épicos
    def add_zone_detected_callback(self, callback: Callable[[str, Dict], None]):
        """➕ Añade callback para zona detectada"""
        self.zone_detected_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str, Exception], None]):
        """➕ Añade callback para errores"""
        self.error_callbacks.append(callback)
    
    def add_state_change_callback(self, callback: Callable[[MonitoringState, MonitoringState], None]):
        """➕ Añade callback para cambios de estado"""
        self.state_change_callbacks.append(callback)
    
    def _call_zone_detected_callbacks(self, symbol: str, zone_data: Dict):
        """📞 Llama callbacks de zona detectada"""
        for callback in self.zone_detected_callbacks:
            try:
                callback(symbol, zone_data)
            except Exception as e:
                print(f"❌ Error in zone detected callback: {e}")
    
    def _call_error_callbacks(self, symbol: str, error: Exception):
        """📞 Llama callbacks de error"""
        for callback in self.error_callbacks:
            try:
                callback(symbol, error)
            except Exception as e:
                print(f"❌ Error in error callback: {e}")
    
    def _call_state_change_callbacks(self, old_state: MonitoringState, new_state: MonitoringState):
        """📞 Llama callbacks de cambio de estado"""
        for callback in self.state_change_callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                print(f"❌ Error in state change callback: {e}")
    
    # Métodos de información y estadísticas
    def get_status(self) -> Dict:
        """📊 OBTIENE STATUS COMPLETO DEL MONITOR"""
        status = {
            "state": self.state.value,
            "timeframe": self.timeframe,
            "symbols": list(self.symbols),
            "total_sessions": self.total_sessions,
            "total_runtime": str(self.total_runtime),
            "current_session": None
        }
        
        if self.current_session:
            runtime = EcuadorTimeUtils.now() - self.current_session.start_time
            status["current_session"] = {
                "session_id": self.current_session.session_id,
                "start_time": self.current_session.start_time.isoformat(),
                "runtime": str(runtime),
                "total_checks": self.current_session.total_checks,
                "zones_detected": self.current_session.zones_detected,
                "alerts_sent": self.current_session.alerts_sent,
                "last_check": self.current_session.last_check.isoformat() if self.current_session.last_check else None,
                "errors": len(self.current_session.errors)
            }
        
        return status
    
    def is_running(self) -> bool:
        """🔍 Verifica si está corriendo"""
        return self.state == MonitoringState.RUNNING
    
    def is_monitoring_symbol(self, symbol: str) -> bool:
        """🔍 Verifica si está monitoreando un símbolo"""
        return symbol.upper() in self.symbols


def main():
    """🔥 FUNCIÓN PRINCIPAL PARA TESTING 🔥"""
    print("🔥⚔️🏛️ TESTING EPIC REAL TIME ZONE MONITOR 🏛️⚔️🔥")
    
    # Crear monitor
    monitor = RealTimeZoneMonitor(
        timeframe="1h",
        enable_alerts=True,
        enable_sound=False  # Deshabilitado para testing
    )
    
    # Añadir callbacks de prueba
    def on_zone_detected(symbol: str, zone_data: Dict):
        print(f"🎯 CALLBACK: Zone detected for {symbol}")
    
    def on_error(symbol: str, error: Exception):
        print(f"⚠️ CALLBACK: Error for {symbol}: {error}")
    
    def on_state_change(old_state: MonitoringState, new_state: MonitoringState):
        print(f"🔄 CALLBACK: State changed {old_state.value} -> {new_state.value}")
    
    monitor.add_zone_detected_callback(on_zone_detected)
    monitor.add_error_callback(on_error)
    monitor.add_state_change_callback(on_state_change)
    
    # Añadir símbolos
    monitor.add_symbol("ETHUSDT")
    monitor.add_symbol("BTCUSDT")
    
    # Mostrar status inicial
    print(f"\n📊 Initial Status: {monitor.get_status()}")
    
    # Iniciar monitoring
    if monitor.start_monitoring():
        print("✅ Monitoring started successfully!")
        
        # Correr por un tiempo
        try:
            print("⏰ Running for 30 seconds...")
            time.sleep(30)
            
            # Mostrar status durante ejecución
            print(f"\n📊 Runtime Status: {monitor.get_status()}")
            
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
        
        # Detener monitoring
        monitor.stop_monitoring()
    
    print("\n🏆 EPIC REAL TIME ZONE MONITOR TEST COMPLETE! 🏆")


if __name__ == "__main__":
    main()