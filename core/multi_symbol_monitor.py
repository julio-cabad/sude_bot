#!/usr/bin/env python3
"""
🔥⚔️ MULTI SYMBOL MONITOR - MONITOR MULTI-SÍMBOLO SUPREMO ⚔️🔥
Sistema de monitoreo paralelo que haría llorar a los dioses del Olimpo
Created by TITANES DEL CÓDIGO - BESTIAS SUPREMAS
"""

import os
import sys
import time
import threading
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import queue
import traceback
from collections import defaultdict

# Nuestros módulos épicos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.realtime_zone_monitor import RealTimeZoneMonitor, MonitoringState, MonitoringSession
from core.timeframe_adapter import TimeframeAdapter
from core.alert_engine import AlertEngine, EpicAlert
from models.zone_alert import ZoneAlert, EcuadorTimeUtils, AlertPriority


@dataclass
class SymbolState:
    """📊 ESTADO DE SÍMBOLO INDIVIDUAL ÉPICO 📊"""
    symbol: str
    is_active: bool = True
    last_check: Optional[datetime] = None
    last_zone_time: Optional[datetime] = None
    total_checks: int = 0
    zones_detected: int = 0
    alerts_sent: int = 0
    consecutive_errors: int = 0
    errors: List[str] = field(default_factory=list)
    processing_time_avg: float = 0.0
    
    def update_processing_time(self, processing_time: float):
        """Actualiza tiempo promedio de procesamiento"""
        if self.total_checks == 0:
            self.processing_time_avg = processing_time
        else:
            # Media móvil simple
            self.processing_time_avg = (self.processing_time_avg * 0.8) + (processing_time * 0.2)


class MultiSymbolMonitor:
    """🔥⚔️ MONITOR MULTI-SÍMBOLO SUPREMO ⚔️🔥"""
    
    def __init__(self,
                 timeframe: str = "1h",
                 enable_alerts: bool = True,
                 enable_sound: bool = True,
                 max_workers: int = 4,
                 max_errors_per_symbol: int = 5,
                 error_cooldown_minutes: int = 5):
        
        print("🔥⚔️🏛️ INITIALIZING EPIC MULTI SYMBOL MONITOR 🏛️⚔️🔥")
        print("🎯 ZEUS Y LOS DIOSES DEL OLIMPO APPROVED!")
        
        # Configuración
        self.timeframe = timeframe
        self.enable_alerts = enable_alerts
        self.enable_sound = enable_sound
        self.max_workers = max_workers
        self.max_errors_per_symbol = max_errors_per_symbol
        self.error_cooldown_minutes = error_cooldown_minutes
        
        # Componentes épicos
        self.timeframe_adapter = TimeframeAdapter()
        self.alert_engine = AlertEngine(enable_sound=enable_sound) if enable_alerts else None
        
        # Validar timeframe
        if not self.timeframe_adapter.validate_timeframe(timeframe):
            raise ValueError(f"❌ Invalid timeframe: {timeframe}")
        
        self.timeframe_info = self.timeframe_adapter.parse_timeframe(timeframe)
        
        # Estado del monitor
        self.state = MonitoringState.STOPPED
        self.symbol_states: Dict[str, SymbolState] = {}
        
        # Threading y concurrencia
        self.executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.symbol_lock = threading.RLock()  # Para acceso thread-safe a symbol_states
        
        # Queues para comunicación entre threads
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # Sesión y estadísticas
        self.current_session: Optional[MonitoringSession] = None
        self.total_sessions = 0
        
        # Callbacks épicos
        self.zone_detected_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        self.state_change_callbacks: List[Callable] = []
        self.symbol_added_callbacks: List[Callable] = []
        self.symbol_removed_callbacks: List[Callable] = []
        
        print("✅ Multi Symbol Monitor initialized successfully!")
        print(f"📊 Timeframe: {self.timeframe_info.display_name}")
        print(f"⚡ Max Workers: {max_workers}")
        print(f"🔊 Alerts: {'ENABLED' if enable_alerts else 'DISABLED'}")
        print(f"🎵 Sound: {'ENABLED' if enable_sound else 'DISABLED'}")
    
    def add_symbol(self, symbol: str) -> bool:
        """
        ➕ AÑADE SÍMBOLO PARA MONITORING PARALELO
        Args:
            symbol: Símbolo a monitorear
        Returns:
            True si se añadió correctamente
        """
        try:
            symbol = symbol.upper().strip()
            
            if not symbol:
                raise ValueError("❌ Symbol cannot be empty")
            
            with self.symbol_lock:
                if symbol in self.symbol_states:
                    print(f"⚠️ Symbol {symbol} already being monitored")
                    return False
                
                # Crear estado del símbolo
                self.symbol_states[symbol] = SymbolState(symbol=symbol)
                
                print(f"✅ Added symbol: {symbol}")
                
                # Actualizar sesión si está activa
                if self.current_session:
                    self.current_session.symbols = set(self.symbol_states.keys())
                
                # Llamar callbacks
                self._call_symbol_added_callbacks(symbol)
                
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
            
            with self.symbol_lock:
                if symbol not in self.symbol_states:
                    print(f"⚠️ Symbol {symbol} not being monitored")
                    return False
                
                # Desactivar símbolo (para que los workers en curso terminen)
                self.symbol_states[symbol].is_active = False
                
                # Remover después de un breve delay para permitir cleanup
                def delayed_removal():
                    time.sleep(1.0)
                    with self.symbol_lock:
                        if symbol in self.symbol_states:
                            del self.symbol_states[symbol]
                            print(f"✅ Removed symbol: {symbol}")
                            
                            # Actualizar sesión si está activa
                            if self.current_session:
                                self.current_session.symbols = set(self.symbol_states.keys())
                            
                            # Llamar callbacks
                            self._call_symbol_removed_callbacks(symbol)
                
                # Ejecutar removal en background
                removal_thread = threading.Thread(target=delayed_removal, daemon=True)
                removal_thread.start()
                
                return True
                
        except Exception as e:
            print(f"❌ Error removing symbol {symbol}: {e}")
            return False
    
    def get_monitored_symbols(self) -> List[str]:
        """📋 OBTIENE LISTA DE SÍMBOLOS MONITOREADOS"""
        with self.symbol_lock:
            return sorted([symbol for symbol, state in self.symbol_states.items() if state.is_active])
    
    def get_symbol_state(self, symbol: str) -> Optional[SymbolState]:
        """📊 OBTIENE ESTADO DE UN SÍMBOLO"""
        with self.symbol_lock:
            return self.symbol_states.get(symbol.upper())
    
    def start_monitoring(self) -> bool:
        """
        🚀 INICIA EL MONITORING MULTI-SÍMBOLO ÉPICO
        Returns:
            True si se inició correctamente
        """
        try:
            if self.state == MonitoringState.RUNNING:
                print("⚠️ Monitoring already running")
                return False
            
            active_symbols = self.get_monitored_symbols()
            if not active_symbols:
                print("❌ No symbols to monitor. Add symbols first.")
                return False
            
            print("🚀 Starting epic multi-symbol monitoring...")
            
            # Cambiar estado
            self._change_state(MonitoringState.STARTING)
            
            # Crear nueva sesión
            self.current_session = MonitoringSession(
                session_id=f"MULTI_SESSION_{int(time.time())}",
                symbols=set(active_symbols),
                timeframe=self.timeframe,
                start_time=EcuadorTimeUtils.now(),
                state=MonitoringState.STARTING
            )
            
            self.total_sessions += 1
            
            # Iniciar alert engine si está habilitado
            if self.alert_engine:
                self.alert_engine.start()
            
            # Crear thread pool executor
            self.executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="ZoneWorker"
            )
            
            # Reset stop event
            self.stop_event.clear()
            
            # Crear y iniciar thread de coordinación
            self.monitoring_thread = threading.Thread(
                target=self._coordination_loop,
                name="MultiSymbolCoordinator",
                daemon=True
            )
            
            self.monitoring_thread.start()
            
            # Cambiar a running
            self._change_state(MonitoringState.RUNNING)
            
            print("✅ Multi-symbol monitoring started successfully!")
            print(f"📊 Symbols: {active_symbols}")
            print(f"⚡ Workers: {self.max_workers}")
            print(f"⏰ Timeframe: {self.timeframe_info.display_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting multi-symbol monitoring: {e}")
            self._change_state(MonitoringState.ERROR)
            return False
    
    def stop_monitoring(self, timeout: float = 15.0) -> bool:
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
            
            print("🛑 Stopping multi-symbol monitoring...")
            
            # Cambiar estado
            self._change_state(MonitoringState.STOPPING)
            
            # Señalar parada
            self.stop_event.set()
            
            # Esperar thread de coordinación
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=timeout/2)
            
            # Shutdown executor
            if self.executor:
                print("⚡ Shutting down worker threads...")
                self.executor.shutdown(wait=True)
                self.executor = None
            
            # Detener alert engine
            if self.alert_engine:
                self.alert_engine.stop()
            
            # Finalizar sesión
            if self.current_session:
                self.current_session.state = MonitoringState.STOPPED
                runtime = EcuadorTimeUtils.now() - self.current_session.start_time
                
                # Calcular estadísticas totales
                total_checks = sum(state.total_checks for state in self.symbol_states.values())
                total_zones = sum(state.zones_detected for state in self.symbol_states.values())
                total_alerts = sum(state.alerts_sent for state in self.symbol_states.values())
                
                print(f"📊 Multi-symbol session completed:")
                print(f"   Duration: {runtime}")
                print(f"   Symbols: {len(self.symbol_states)}")
                print(f"   Total Checks: {total_checks}")
                print(f"   Total Zones: {total_zones}")
                print(f"   Total Alerts: {total_alerts}")
            
            # Cambiar estado final
            self._change_state(MonitoringState.STOPPED)
            
            print("✅ Multi-symbol monitoring stopped successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping multi-symbol monitoring: {e}")
            self._change_state(MonitoringState.ERROR)
            return False
    
    def _coordination_loop(self):
        """⚔️ LOOP DE COORDINACIÓN PRINCIPAL - EL CEREBRO ÉPICO"""
        print("⚔️ Starting epic coordination loop...")
        
        # Calcular sleep duration
        sleep_duration = self.timeframe_adapter.get_sleep_duration(self.timeframe_info)
        print(f"⏰ Check interval: {sleep_duration:.1f} seconds")
        
        while not self.stop_event.is_set():
            try:
                # Verificar si debemos parar
                if self.state != MonitoringState.RUNNING:
                    break
                
                # Obtener símbolos activos
                active_symbols = []
                with self.symbol_lock:
                    active_symbols = [
                        symbol for symbol, state in self.symbol_states.items() 
                        if state.is_active and self._should_process_symbol(state)
                    ]
                
                if not active_symbols:
                    time.sleep(1.0)
                    continue
                
                # Enviar tareas a workers
                futures = []
                for symbol in active_symbols:
                    if self.stop_event.is_set():
                        break
                    
                    future = self.executor.submit(self._process_symbol_parallel, symbol)
                    futures.append((symbol, future))
                
                # Recoger resultados
                for symbol, future in futures:
                    if self.stop_event.is_set():
                        break
                    
                    try:
                        # Timeout por símbolo para evitar bloqueos
                        result = future.result(timeout=sleep_duration * 0.8)
                        self._handle_symbol_result(symbol, result)
                        
                    except concurrent.futures.TimeoutError:
                        print(f"⚠️ Timeout processing {symbol}")
                        self._handle_symbol_error(symbol, Exception("Processing timeout"))
                        
                    except Exception as e:
                        print(f"❌ Error in future for {symbol}: {e}")
                        self._handle_symbol_error(symbol, e)
                
                # Actualizar estadísticas de sesión
                if self.current_session:
                    with self.symbol_lock:
                        self.current_session.total_checks = sum(
                            state.total_checks for state in self.symbol_states.values()
                        )
                        self.current_session.zones_detected = sum(
                            state.zones_detected for state in self.symbol_states.values()
                        )
                        self.current_session.alerts_sent = sum(
                            state.alerts_sent for state in self.symbol_states.values()
                        )
                        self.current_session.last_check = EcuadorTimeUtils.now()
                
                # Sleep hasta próximo ciclo
                if not self.stop_event.is_set():
                    self.stop_event.wait(timeout=sleep_duration)
                
            except Exception as e:
                print(f"❌ Critical error in coordination loop: {e}")
                traceback.print_exc()
                
                # Sleep antes de reintentar
                time.sleep(5.0)
        
        print("⚔️ Coordination loop ended")
    
    def _process_symbol_parallel(self, symbol: str) -> Dict[str, Any]:
        """
        🏛️ PROCESA UN SÍMBOLO EN PARALELO
        Args:
            symbol: Símbolo a procesar
        Returns:
            Resultado del procesamiento
        """
        start_time = time.time()
        result = {
            'symbol': symbol,
            'success': False,
            'zones_detected': [],
            'error': None,
            'processing_time': 0.0
        }
        
        try:
            print(f"🔍 Processing {symbol} on {self.timeframe} (Worker: {threading.current_thread().name})")
            
            # Verificar si el símbolo sigue activo
            with self.symbol_lock:
                if symbol not in self.symbol_states or not self.symbol_states[symbol].is_active:
                    result['error'] = "Symbol no longer active"
                    return result
            
            # Detección real con ImplacableZonesDetector
            zones_detected = self._detect_zones_with_implacable_detector(symbol)
            
            result['zones_detected'] = zones_detected
            result['success'] = True
            
            # Actualizar estado del símbolo
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            
            with self.symbol_lock:
                if symbol in self.symbol_states:
                    state = self.symbol_states[symbol]
                    state.last_check = EcuadorTimeUtils.now()
                    state.total_checks += 1
                    state.consecutive_errors = 0  # Reset errores
                    state.update_processing_time(processing_time)
                    
                    if zones_detected:
                        state.zones_detected += len(zones_detected)
                        state.last_zone_time = EcuadorTimeUtils.now()
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            result['processing_time'] = time.time() - start_time
            return result
    
    def _detect_zones_with_implacable_detector(self, symbol: str) -> List[Dict]:
        """
        🔥 DETECCIÓN REAL CON IMPLACABLE ZONES DETECTOR
        Args:
            symbol: Símbolo a procesar
        Returns:
            Lista de zonas detectadas reales
        """
        try:
            # Importar el detector real
            from demo.implacable_zones_detector import ImplacableZonesDetector
            
            # Crear detector para este símbolo
            detector = ImplacableZonesDetector(symbol=symbol, timeframe=self.timeframe)
            
            # Ejecutar detección completa
            success = detector.run_implacable_detection()
            
            if not success:
                print(f"❌ Error en detección para {symbol}")
                return []
            
            # Obtener zonas detectadas
            zones_data = detector.export_implacable_json()
            
            if not zones_data:
                return []
            
            # Convertir a formato esperado por nuestro sistema
            detected_zones = []
            
            # Procesar zonas de supply
            for zone in zones_data.get('supply_zones', []):
                zone_dict = {
                    'type': 'SUPPLY',
                    'poi': zone['poi'],
                    'top': zone['top'],
                    'bottom': zone['bottom'],
                    'distance_pct': float(zone['distance_percentage'].replace('%', '').replace('+', '')),
                    'formation_candles_ago': self._calculate_candles_ago(zone['formation_date']),
                    'strength': zone['strength'],
                    'volume': zone['volume'],
                    'zone_name': zone['name'],
                    'swings_in_zone': zone['swings_in_zone'],
                    'current_price': zones_data['current_price'],
                    'detection_method': 'implacable_real_data'
                }
                detected_zones.append(zone_dict)
            
            # Procesar zonas de demand
            for zone in zones_data.get('demand_zones', []):
                zone_dict = {
                    'type': 'DEMAND',
                    'poi': zone['poi'],
                    'top': zone['top'],
                    'bottom': zone['bottom'],
                    'distance_pct': float(zone['distance_percentage'].replace('%', '').replace('+', '')),
                    'formation_candles_ago': self._calculate_candles_ago(zone['formation_date']),
                    'strength': zone['strength'],
                    'volume': zone['volume'],
                    'zone_name': zone['name'],
                    'swings_in_zone': zone['swings_in_zone'],
                    'current_price': zones_data['current_price'],
                    'detection_method': 'implacable_real_data'
                }
                detected_zones.append(zone_dict)
            
            print(f"🔥 Detectadas {len(detected_zones)} zonas reales para {symbol}")
            return detected_zones
            
        except Exception as e:
            print(f"❌ Error en detección real para {symbol}: {e}")
            return []
    
    def _calculate_candles_ago(self, formation_date: str) -> int:
        """
        📅 CALCULA CUÁNTAS VELAS ATRÁS SE FORMÓ LA ZONA
        Args:
            formation_date: Fecha de formación en string
        Returns:
            Número aproximado de velas atrás
        """
        try:
            from datetime import datetime
            
            # Parsear fecha de formación
            formation_dt = datetime.strptime(formation_date, '%Y-%m-%d %H:%M:%S')
            current_dt = datetime.now()
            
            # Calcular diferencia en minutos
            time_diff = current_dt - formation_dt
            minutes_diff = time_diff.total_seconds() / 60
            
            # Convertir a velas según timeframe
            timeframe_minutes = {
                '1m': 1,
                '3m': 3,
                '5m': 5,
                '15m': 15,
                '30m': 30,
                '1h': 60,
                '4h': 240,
                '1d': 1440
            }
            
            tf_minutes = timeframe_minutes.get(self.timeframe, 60)
            candles_ago = int(minutes_diff / tf_minutes)
            
            return max(1, candles_ago)  # Mínimo 1 vela
            
        except Exception as e:
            print(f"❌ Error calculando velas atrás: {e}")
            return 10  # Valor por defecto
    
    def _should_process_symbol(self, state: SymbolState) -> bool:
        """
        🤔 DETERMINA SI DEBE PROCESAR UN SÍMBOLO
        Args:
            state: Estado del símbolo
        Returns:
            True si debe procesarse
        """
        # No procesar si tiene demasiados errores consecutivos
        if state.consecutive_errors >= self.max_errors_per_symbol:
            # Verificar si ha pasado el cooldown
            if state.last_check:
                cooldown_end = state.last_check + timedelta(minutes=self.error_cooldown_minutes)
                if EcuadorTimeUtils.now() < cooldown_end:
                    return False
                else:
                    # Reset errores después del cooldown
                    state.consecutive_errors = 0
        
        return True
    
    def _handle_symbol_result(self, symbol: str, result: Dict[str, Any]):
        """
        🏛️ MANEJA RESULTADO DE PROCESAMIENTO DE SÍMBOLO
        Args:
            symbol: Símbolo procesado
            result: Resultado del procesamiento
        """
        try:
            if result['success']:
                zones_detected = result.get('zones_detected', [])
                
                if zones_detected:
                    print(f"🚨 {len(zones_detected)} new zones detected for {symbol}!")
                    
                    # Procesar cada zona
                    for zone_data in zones_detected:
                        self._handle_new_zone(symbol, zone_data)
            else:
                error_msg = result.get('error', 'Unknown error')
                self._handle_symbol_error(symbol, Exception(error_msg))
                
        except Exception as e:
            print(f"❌ Error handling result for {symbol}: {e}")
    
    def _handle_symbol_error(self, symbol: str, error: Exception):
        """
        ❌ MANEJA ERROR DE SÍMBOLO
        Args:
            symbol: Símbolo con error
            error: Excepción ocurrida
        """
        try:
            error_msg = f"Error processing {symbol}: {error}"
            print(f"❌ {error_msg}")
            
            # Actualizar estado del símbolo
            with self.symbol_lock:
                if symbol in self.symbol_states:
                    state = self.symbol_states[symbol]
                    state.consecutive_errors += 1
                    state.errors.append(error_msg)
                    
                    # Mantener solo los últimos 10 errores
                    if len(state.errors) > 10:
                        state.errors = state.errors[-10:]
            
            # Llamar callbacks de error
            self._call_error_callbacks(symbol, error)
            
        except Exception as e:
            print(f"❌ Error handling symbol error: {e}")
    
    def _handle_new_zone(self, symbol: str, zone_data: Dict):
        """
        🏛️ MANEJA UNA NUEVA ZONA DETECTADA
        Args:
            symbol: Símbolo de la zona
            zone_data: Datos de la zona
        """
        try:
            print(f"🏛️ Processing new zone for {symbol}: {zone_data.get('type', 'UNKNOWN')}")
            
            # Actualizar contador de alertas del símbolo
            with self.symbol_lock:
                if symbol in self.symbol_states:
                    self.symbol_states[symbol].alerts_sent += 1
            
            # Llamar callbacks de zona detectada
            self._call_zone_detected_callbacks(symbol, zone_data)
            
            # Enviar alerta si está habilitado
            if self.alert_engine:
                alert = self.alert_engine.create_zone_alert(symbol, zone_data)
                self.alert_engine.send_alert(alert)
            
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
        
        print(f"🔄 Multi-symbol state changed: {old_state.value} -> {new_state.value}")
        
        # Actualizar sesión si existe
        if self.current_session:
            self.current_session.state = new_state
        
        # Llamar callbacks de cambio de estado
        self._call_state_change_callbacks(old_state, new_state)
    
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
    
    def add_symbol_added_callback(self, callback: Callable[[str], None]):
        """➕ Añade callback para símbolo añadido"""
        self.symbol_added_callbacks.append(callback)
    
    def add_symbol_removed_callback(self, callback: Callable[[str], None]):
        """➕ Añade callback para símbolo removido"""
        self.symbol_removed_callbacks.append(callback)
    
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
    
    def _call_symbol_added_callbacks(self, symbol: str):
        """📞 Llama callbacks de símbolo añadido"""
        for callback in self.symbol_added_callbacks:
            try:
                callback(symbol)
            except Exception as e:
                print(f"❌ Error in symbol added callback: {e}")
    
    def _call_symbol_removed_callbacks(self, symbol: str):
        """📞 Llama callbacks de símbolo removido"""
        for callback in self.symbol_removed_callbacks:
            try:
                callback(symbol)
            except Exception as e:
                print(f"❌ Error in symbol removed callback: {e}")
    
    # Métodos de información y estadísticas
    def get_status(self) -> Dict:
        """📊 OBTIENE STATUS COMPLETO DEL MONITOR MULTI-SÍMBOLO"""
        with self.symbol_lock:
            symbol_stats = {}
            for symbol, state in self.symbol_states.items():
                symbol_stats[symbol] = {
                    'is_active': state.is_active,
                    'last_check': state.last_check.isoformat() if state.last_check else None,
                    'total_checks': state.total_checks,
                    'zones_detected': state.zones_detected,
                    'alerts_sent': state.alerts_sent,
                    'consecutive_errors': state.consecutive_errors,
                    'processing_time_avg': round(state.processing_time_avg, 3),
                    'error_count': len(state.errors)
                }
        
        status = {
            "state": self.state.value,
            "timeframe": self.timeframe,
            "max_workers": self.max_workers,
            "active_symbols": len([s for s in self.symbol_states.values() if s.is_active]),
            "total_symbols": len(self.symbol_states),
            "total_sessions": self.total_sessions,
            "symbol_stats": symbol_stats,
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
                "last_check": self.current_session.last_check.isoformat() if self.current_session.last_check else None
            }
        
        return status
    
    def is_running(self) -> bool:
        """🔍 Verifica si está corriendo"""
        return self.state == MonitoringState.RUNNING
    
    def is_monitoring_symbol(self, symbol: str) -> bool:
        """🔍 Verifica si está monitoreando un símbolo"""
        with self.symbol_lock:
            state = self.symbol_states.get(symbol.upper())
            return state is not None and state.is_active


def main():
    """🔥 FUNCIÓN PRINCIPAL PARA TESTING 🔥"""
    print("🔥⚔️🏛️ TESTING EPIC MULTI SYMBOL MONITOR 🏛️⚔️🔥")
    
    # Crear monitor multi-símbolo
    monitor = MultiSymbolMonitor(
        timeframe="1h",
        enable_alerts=True,
        enable_sound=False,  # Deshabilitado para testing
        max_workers=3
    )
    
    # Añadir callbacks de prueba
    def on_zone_detected(symbol: str, zone_data: Dict):
        print(f"🎯 CALLBACK: Zone detected for {symbol}")
    
    def on_error(symbol: str, error: Exception):
        print(f"⚠️ CALLBACK: Error for {symbol}: {error}")
    
    def on_state_change(old_state: MonitoringState, new_state: MonitoringState):
        print(f"🔄 CALLBACK: State changed {old_state.value} -> {new_state.value}")
    
    def on_symbol_added(symbol: str):
        print(f"➕ CALLBACK: Symbol added {symbol}")
    
    def on_symbol_removed(symbol: str):
        print(f"➖ CALLBACK: Symbol removed {symbol}")
    
    monitor.add_zone_detected_callback(on_zone_detected)
    monitor.add_error_callback(on_error)
    monitor.add_state_change_callback(on_state_change)
    monitor.add_symbol_added_callback(on_symbol_added)
    monitor.add_symbol_removed_callback(on_symbol_removed)
    
    # Añadir múltiples símbolos
    symbols = ["ETHUSDT", "BTCUSDT", "ADAUSDT", "SOLUSDT"]
    for symbol in symbols:
        monitor.add_symbol(symbol)
    
    # Mostrar status inicial
    print(f"\n📊 Initial Status:")
    status = monitor.get_status()
    print(f"   Active symbols: {status['active_symbols']}")
    print(f"   Max workers: {status['max_workers']}")
    
    # Iniciar monitoring
    if monitor.start_monitoring():
        print("✅ Multi-symbol monitoring started successfully!")
        
        # Correr por un tiempo
        try:
            print("⏰ Running for 45 seconds...")
            time.sleep(45)
            
            # Mostrar status durante ejecución
            print(f"\n📊 Runtime Status:")
            status = monitor.get_status()
            print(f"   State: {status['state']}")
            print(f"   Active symbols: {status['active_symbols']}")
            
            if status['current_session']:
                session = status['current_session']
                print(f"   Session checks: {session['total_checks']}")
                print(f"   Session zones: {session['zones_detected']}")
            
            # Mostrar stats por símbolo
            print(f"\n📊 Symbol Stats:")
            for symbol, stats in status['symbol_stats'].items():
                print(f"   {symbol}: checks={stats['total_checks']}, zones={stats['zones_detected']}, avg_time={stats['processing_time_avg']}s")
            
            # Test remover símbolo durante ejecución
            print("\n🧪 Testing symbol removal during runtime...")
            monitor.remove_symbol("ADAUSDT")
            time.sleep(5)
            
            # Test añadir símbolo durante ejecución
            print("\n🧪 Testing symbol addition during runtime...")
            monitor.add_symbol("DOTUSDT")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
        
        # Detener monitoring
        monitor.stop_monitoring()
    
    print("\n🏆 EPIC MULTI SYMBOL MONITOR TEST COMPLETE! 🏆")


if __name__ == "__main__":
    main()