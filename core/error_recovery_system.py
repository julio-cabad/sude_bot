#!/usr/bin/env python3
"""
🔥⚔️ ERROR RECOVERY SYSTEM - SISTEMA DE RECUPERACIÓN SUPREMO ⚔️🔥
Sistema de manejo de errores que haría llorar a Hades
Created by TITANES DEL CÓDIGO - BESTIAS SUPREMAS
"""

import os
import sys
import time
import json
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue
from collections import defaultdict, deque
import pickle

# Nuestros módulos épicos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.zone_alert import EcuadorTimeUtils


class ErrorSeverity(Enum):
    """🚨 SEVERIDAD DE ERRORES ÉPICA 🚨"""
    LOW = "LOW"           # Errores menores, continuar
    MEDIUM = "MEDIUM"     # Errores moderados, retry
    HIGH = "HIGH"         # Errores graves, cooldown
    CRITICAL = "CRITICAL" # Errores críticos, stop system


class ErrorType(Enum):
    """🔥 TIPOS DE ERRORES ÉPICOS 🔥"""
    API_ERROR = "API_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    DATA_ERROR = "DATA_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class RecoveryAction(Enum):
    """⚔️ ACCIONES DE RECUPERACIÓN ÉPICAS ⚔️"""
    RETRY = "RETRY"
    BACKOFF = "BACKOFF"
    COOLDOWN = "COOLDOWN"
    RESTART_COMPONENT = "RESTART_COMPONENT"
    RESTART_SYSTEM = "RESTART_SYSTEM"
    IGNORE = "IGNORE"
    STOP = "STOP"


@dataclass
class ErrorInfo:
    """📊 INFORMACIÓN DE ERROR ÉPICA 📊"""
    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    timestamp: datetime
    component: str
    symbol: Optional[str] = None
    traceback_info: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    recovery_attempts: int = 0
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario para logging"""
        return {
            'error_id': self.error_id,
            'error_type': self.error_type.value,
            'severity': self.severity.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'component': self.component,
            'symbol': self.symbol,
            'traceback_info': self.traceback_info,
            'context': self.context,
            'recovery_attempts': self.recovery_attempts,
            'resolved': self.resolved
        }


@dataclass
class RecoveryStrategy:
    """🏛️ ESTRATEGIA DE RECUPERACIÓN ÉPICA 🏛️"""
    error_type: ErrorType
    severity: ErrorSeverity
    action: RecoveryAction
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    cooldown_duration: int = 300  # 5 minutos
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcula delay con exponential backoff"""
        if self.action == RecoveryAction.BACKOFF:
            delay = self.base_delay * (self.backoff_multiplier ** attempt)
            return min(delay, self.max_delay)
        return self.base_delay


class ErrorClassifier:
    """🎯 CLASIFICADOR DE ERRORES ÉPICO 🎯"""
    
    # Patrones de clasificación de errores
    ERROR_PATTERNS = {
        # API Errors
        ErrorType.API_ERROR: [
            "api", "endpoint", "invalid request", "bad request", 
            "unauthorized", "forbidden", "not found"
        ],
        
        # Network Errors
        ErrorType.NETWORK_ERROR: [
            "connection", "timeout", "network", "dns", "socket",
            "unreachable", "connection refused", "connection reset"
        ],
        
        # Rate Limit Errors
        ErrorType.RATE_LIMIT_ERROR: [
            "rate limit", "too many requests", "429", "quota exceeded",
            "throttled", "rate exceeded"
        ],
        
        # Data Errors
        ErrorType.DATA_ERROR: [
            "json", "parse", "decode", "invalid data", "malformed",
            "missing field", "type error", "value error"
        ],
        
        # Processing Errors
        ErrorType.PROCESSING_ERROR: [
            "calculation", "algorithm", "processing", "computation",
            "division by zero", "index error", "key error"
        ],
        
        # Configuration Errors
        ErrorType.CONFIGURATION_ERROR: [
            "config", "setting", "parameter", "missing config",
            "invalid config", "configuration"
        ],
        
        # System Errors
        ErrorType.SYSTEM_ERROR: [
            "memory", "disk", "cpu", "resource", "system",
            "permission", "file not found", "access denied"
        ]
    }
    
    @classmethod
    def classify_error(cls, error: Exception, context: Dict = None) -> tuple[ErrorType, ErrorSeverity]:
        """
        🎯 CLASIFICA ERROR Y DETERMINA SEVERIDAD
        Args:
            error: Excepción a clasificar
            context: Contexto adicional
        Returns:
            Tuple de (ErrorType, ErrorSeverity)
        """
        error_message = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Clasificar por tipo
        error_type = ErrorType.UNKNOWN_ERROR
        for etype, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern in error_message or pattern in error_type_name:
                    error_type = etype
                    break
            if error_type != ErrorType.UNKNOWN_ERROR:
                break
        
        # Determinar severidad
        severity = cls._determine_severity(error, error_type, context)
        
        return error_type, severity
    
    @classmethod
    def _determine_severity(cls, error: Exception, error_type: ErrorType, context: Dict = None) -> ErrorSeverity:
        """Determina la severidad del error"""
        error_message = str(error).lower()
        
        # Errores críticos
        if any(word in error_message for word in ["critical", "fatal", "system", "memory"]):
            return ErrorSeverity.CRITICAL
        
        # Errores por tipo
        severity_map = {
            ErrorType.RATE_LIMIT_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.NETWORK_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.API_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.DATA_ERROR: ErrorSeverity.LOW,
            ErrorType.PROCESSING_ERROR: ErrorSeverity.LOW,
            ErrorType.CONFIGURATION_ERROR: ErrorSeverity.HIGH,
            ErrorType.SYSTEM_ERROR: ErrorSeverity.CRITICAL,
            ErrorType.UNKNOWN_ERROR: ErrorSeverity.MEDIUM
        }
        
        return severity_map.get(error_type, ErrorSeverity.MEDIUM)


class ErrorRecoverySystem:
    """🔥⚔️ SISTEMA DE RECUPERACIÓN DE ERRORES SUPREMO ⚔️🔥"""
    
    def __init__(self, 
                 log_dir: str = "logs",
                 max_error_history: int = 1000,
                 enable_persistence: bool = True):
        
        print("🔥⚔️🏛️ INITIALIZING EPIC ERROR RECOVERY SYSTEM 🏛️⚔️🔥")
        print("🎯 HADES Y LOS DIOSES DEL INFRAMUNDO APPROVED!")
        
        self.log_dir = log_dir
        self.max_error_history = max_error_history
        self.enable_persistence = enable_persistence
        
        # Asegurar directorio de logs
        self._ensure_log_dir()
        
        # Configurar logging épico
        self._setup_logging()
        
        # Estrategias de recuperación por defecto
        self.recovery_strategies = self._create_default_strategies()
        
        # Historial de errores
        self.error_history: deque = deque(maxlen=max_error_history)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.component_errors: Dict[str, List[ErrorInfo]] = defaultdict(list)
        
        # Estado de componentes
        self.component_states: Dict[str, Dict] = defaultdict(dict)
        self.cooldown_until: Dict[str, datetime] = {}
        
        # Callbacks épicos
        self.error_callbacks: List[Callable] = []
        self.recovery_callbacks: List[Callable] = []
        
        # Threading
        self.error_queue = queue.Queue()
        self.processing_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # Estadísticas
        self.stats = {
            'total_errors': 0,
            'resolved_errors': 0,
            'failed_recoveries': 0,
            'system_restarts': 0
        }
        
        print("✅ Error Recovery System initialized successfully!")
        print(f"📁 Log directory: {self.log_dir}")
        print(f"📊 Max error history: {max_error_history}")
        print(f"💾 Persistence: {'ENABLED' if enable_persistence else 'DISABLED'}")
    
    def _ensure_log_dir(self):
        """Asegura que el directorio de logs existe"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _setup_logging(self):
        """Configura el sistema de logging épico"""
        log_file = os.path.join(self.log_dir, f"error_recovery_{datetime.now().strftime('%Y%m%d')}.log")
        
        # Configurar logger
        self.logger = logging.getLogger('ErrorRecoverySystem')
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicar handlers
        if not self.logger.handlers:
            # Handler para archivo
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Handler para consola
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formato épico
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def _create_default_strategies(self) -> Dict[tuple, RecoveryStrategy]:
        """Crea estrategias de recuperación por defecto"""
        strategies = {}
        
        # Rate Limit Errors - Backoff agresivo
        strategies[(ErrorType.RATE_LIMIT_ERROR, ErrorSeverity.MEDIUM)] = RecoveryStrategy(
            error_type=ErrorType.RATE_LIMIT_ERROR,
            severity=ErrorSeverity.MEDIUM,
            action=RecoveryAction.BACKOFF,
            max_attempts=5,
            base_delay=60.0,
            max_delay=300.0,
            backoff_multiplier=1.5
        )
        
        # Network Errors - Retry con backoff
        strategies[(ErrorType.NETWORK_ERROR, ErrorSeverity.MEDIUM)] = RecoveryStrategy(
            error_type=ErrorType.NETWORK_ERROR,
            severity=ErrorSeverity.MEDIUM,
            action=RecoveryAction.RETRY,
            max_attempts=3,
            base_delay=5.0,
            max_delay=30.0,
            backoff_multiplier=2.0
        )
        
        # API Errors - Retry limitado
        strategies[(ErrorType.API_ERROR, ErrorSeverity.MEDIUM)] = RecoveryStrategy(
            error_type=ErrorType.API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            action=RecoveryAction.RETRY,
            max_attempts=2,
            base_delay=10.0,
            max_delay=60.0
        )
        
        # Data Errors - Ignorar o retry
        strategies[(ErrorType.DATA_ERROR, ErrorSeverity.LOW)] = RecoveryStrategy(
            error_type=ErrorType.DATA_ERROR,
            severity=ErrorSeverity.LOW,
            action=RecoveryAction.IGNORE,
            max_attempts=1
        )
        
        # Processing Errors - Retry
        strategies[(ErrorType.PROCESSING_ERROR, ErrorSeverity.LOW)] = RecoveryStrategy(
            error_type=ErrorType.PROCESSING_ERROR,
            severity=ErrorSeverity.LOW,
            action=RecoveryAction.RETRY,
            max_attempts=2,
            base_delay=1.0
        )
        
        # Configuration Errors - Stop
        strategies[(ErrorType.CONFIGURATION_ERROR, ErrorSeverity.HIGH)] = RecoveryStrategy(
            error_type=ErrorType.CONFIGURATION_ERROR,
            severity=ErrorSeverity.HIGH,
            action=RecoveryAction.STOP,
            max_attempts=1
        )
        
        # System Errors - Restart
        strategies[(ErrorType.SYSTEM_ERROR, ErrorSeverity.CRITICAL)] = RecoveryStrategy(
            error_type=ErrorType.SYSTEM_ERROR,
            severity=ErrorSeverity.CRITICAL,
            action=RecoveryAction.RESTART_SYSTEM,
            max_attempts=1
        )
        
        # Unknown Errors - Retry conservador
        strategies[(ErrorType.UNKNOWN_ERROR, ErrorSeverity.MEDIUM)] = RecoveryStrategy(
            error_type=ErrorType.UNKNOWN_ERROR,
            severity=ErrorSeverity.MEDIUM,
            action=RecoveryAction.RETRY,
            max_attempts=2,
            base_delay=5.0
        )
        
        return strategies
    
    def start(self):
        """🚀 INICIA EL SISTEMA DE RECUPERACIÓN"""
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(
                target=self._process_errors,
                name="ErrorRecoveryProcessor",
                daemon=True
            )
            self.processing_thread.start()
            self.logger.info("🚀 Error Recovery System STARTED!")
    
    def stop(self):
        """🛑 DETIENE EL SISTEMA DE RECUPERACIÓN"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        self.logger.info("🛑 Error Recovery System STOPPED!")
    
    def handle_error(self, 
                    error: Exception,
                    component: str,
                    symbol: Optional[str] = None,
                    context: Dict = None) -> bool:
        """
        🚨 MANEJA UN ERROR ÉPICO
        Args:
            error: Excepción ocurrida
            component: Componente donde ocurrió
            symbol: Símbolo relacionado (opcional)
            context: Contexto adicional
        Returns:
            True si se puede continuar, False si debe parar
        """
        try:
            # Clasificar error
            error_type, severity = ErrorClassifier.classify_error(error, context)
            
            # Crear info de error
            error_info = ErrorInfo(
                error_id=f"ERR_{int(time.time())}_{hash(str(error)) % 10000}",
                error_type=error_type,
                severity=severity,
                message=str(error),
                timestamp=EcuadorTimeUtils.now(),
                component=component,
                symbol=symbol,
                traceback_info=traceback.format_exc(),
                context=context or {}
            )
            
            # Añadir a queue para procesamiento
            self.error_queue.put(error_info)
            
            # Log inmediato
            self.logger.error(f"🚨 Error in {component}: {error}")
            
            # Verificar si el componente está en cooldown
            if self._is_component_in_cooldown(component):
                self.logger.warning(f"⏰ Component {component} is in cooldown")
                return False
            
            # Determinar si puede continuar basado en severidad
            return severity != ErrorSeverity.CRITICAL
            
        except Exception as e:
            self.logger.critical(f"❌ Error handling error: {e}")
            return False
    
    def _process_errors(self):
        """⚔️ PROCESA ERRORES EN BACKGROUND"""
        while self.is_running:
            try:
                # Obtener error con timeout
                error_info = self.error_queue.get(timeout=1.0)
                
                # Procesar error
                self._process_single_error(error_info)
                
                # Marcar como procesado
                self.error_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"❌ Error processing error: {e}")
    
    def _process_single_error(self, error_info: ErrorInfo):
        """🏛️ PROCESA UN ERROR INDIVIDUAL"""
        try:
            # Añadir al historial
            self.error_history.append(error_info)
            self.error_counts[error_info.error_type.value] += 1
            self.component_errors[error_info.component].append(error_info)
            self.stats['total_errors'] += 1
            
            # Obtener estrategia de recuperación
            strategy = self._get_recovery_strategy(error_info.error_type, error_info.severity)
            
            if strategy:
                # Ejecutar recuperación
                success = self._execute_recovery(error_info, strategy)
                
                if success:
                    error_info.resolved = True
                    self.stats['resolved_errors'] += 1
                    self.logger.info(f"✅ Error {error_info.error_id} resolved")
                else:
                    self.stats['failed_recoveries'] += 1
                    self.logger.warning(f"⚠️ Failed to resolve error {error_info.error_id}")
            
            # Llamar callbacks
            self._call_error_callbacks(error_info)
            
            # Persistir si está habilitado
            if self.enable_persistence:
                self._persist_error(error_info)
            
        except Exception as e:
            self.logger.error(f"❌ Error processing single error: {e}")
    
    def _get_recovery_strategy(self, error_type: ErrorType, severity: ErrorSeverity) -> Optional[RecoveryStrategy]:
        """Obtiene estrategia de recuperación"""
        return self.recovery_strategies.get((error_type, severity))
    
    def _execute_recovery(self, error_info: ErrorInfo, strategy: RecoveryStrategy) -> bool:
        """
        ⚔️ EJECUTA ESTRATEGIA DE RECUPERACIÓN
        Args:
            error_info: Información del error
            strategy: Estrategia a ejecutar
        Returns:
            True si la recuperación fue exitosa
        """
        try:
            self.logger.info(f"🔧 Executing recovery for {error_info.error_id}: {strategy.action.value}")
            
            if strategy.action == RecoveryAction.RETRY:
                return self._handle_retry(error_info, strategy)
            
            elif strategy.action == RecoveryAction.BACKOFF:
                return self._handle_backoff(error_info, strategy)
            
            elif strategy.action == RecoveryAction.COOLDOWN:
                return self._handle_cooldown(error_info, strategy)
            
            elif strategy.action == RecoveryAction.RESTART_COMPONENT:
                return self._handle_restart_component(error_info, strategy)
            
            elif strategy.action == RecoveryAction.RESTART_SYSTEM:
                return self._handle_restart_system(error_info, strategy)
            
            elif strategy.action == RecoveryAction.IGNORE:
                return self._handle_ignore(error_info, strategy)
            
            elif strategy.action == RecoveryAction.STOP:
                return self._handle_stop(error_info, strategy)
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error executing recovery: {e}")
            return False
    
    def _handle_retry(self, error_info: ErrorInfo, strategy: RecoveryStrategy) -> bool:
        """Maneja retry con backoff"""
        if error_info.recovery_attempts >= strategy.max_attempts:
            self.logger.warning(f"⚠️ Max retry attempts reached for {error_info.error_id}")
            return False
        
        # Calcular delay
        delay = strategy.calculate_delay(error_info.recovery_attempts)
        
        self.logger.info(f"🔄 Retry {error_info.recovery_attempts + 1}/{strategy.max_attempts} in {delay}s")
        
        # Incrementar intentos
        error_info.recovery_attempts += 1
        
        # En un sistema real, aquí se reintentaría la operación
        # Por ahora simulamos éxito después de algunos intentos
        return error_info.recovery_attempts >= 2
    
    def _handle_backoff(self, error_info: ErrorInfo, strategy: RecoveryStrategy) -> bool:
        """Maneja backoff exponencial"""
        delay = strategy.calculate_delay(error_info.recovery_attempts)
        
        self.logger.info(f"⏰ Backing off for {delay}s due to {error_info.error_type.value}")
        
        # Marcar componente en cooldown temporal
        cooldown_until = EcuadorTimeUtils.now() + timedelta(seconds=delay)
        self.cooldown_until[error_info.component] = cooldown_until
        
        return True
    
    def _handle_cooldown(self, error_info: ErrorInfo, strategy: RecoveryStrategy) -> bool:
        """Maneja cooldown del componente"""
        cooldown_until = EcuadorTimeUtils.now() + timedelta(seconds=strategy.cooldown_duration)
        self.cooldown_until[error_info.component] = cooldown_until
        
        self.logger.warning(f"❄️ Component {error_info.component} in cooldown until {cooldown_until}")
        return True
    
    def _handle_restart_component(self, error_info: ErrorInfo, strategy: RecoveryStrategy) -> bool:
        """Maneja restart de componente"""
        self.logger.warning(f"🔄 Restarting component {error_info.component}")
        
        # Llamar callbacks de recovery
        self._call_recovery_callbacks(error_info, RecoveryAction.RESTART_COMPONENT)
        
        return True
    
    def _handle_restart_system(self, error_info: ErrorInfo, strategy: RecoveryStrategy) -> bool:
        """Maneja restart del sistema"""
        self.logger.critical(f"🚨 System restart required due to {error_info.error_id}")
        
        self.stats['system_restarts'] += 1
        
        # Llamar callbacks de recovery
        self._call_recovery_callbacks(error_info, RecoveryAction.RESTART_SYSTEM)
        
        return True
    
    def _handle_ignore(self, error_info: ErrorInfo, strategy: RecoveryStrategy) -> bool:
        """Maneja ignorar error"""
        self.logger.info(f"🤷 Ignoring error {error_info.error_id}")
        return True
    
    def _handle_stop(self, error_info: ErrorInfo, strategy: RecoveryStrategy) -> bool:
        """Maneja parar sistema"""
        self.logger.critical(f"🛑 Stopping system due to {error_info.error_id}")
        
        # Llamar callbacks de recovery
        self._call_recovery_callbacks(error_info, RecoveryAction.STOP)
        
        return False
    
    def _is_component_in_cooldown(self, component: str) -> bool:
        """Verifica si un componente está en cooldown"""
        if component not in self.cooldown_until:
            return False
        
        return EcuadorTimeUtils.now() < self.cooldown_until[component]
    
    def _persist_error(self, error_info: ErrorInfo):
        """Persiste error en archivo"""
        try:
            date_str = error_info.timestamp.strftime("%Y-%m-%d")
            error_file = os.path.join(self.log_dir, f"errors_{date_str}.json")
            
            # Leer errores existentes
            errors = []
            if os.path.exists(error_file):
                try:
                    with open(error_file, 'r') as f:
                        errors = json.load(f)
                except:
                    errors = []
            
            # Añadir nuevo error
            errors.append(error_info.to_dict())
            
            # Guardar
            with open(error_file, 'w') as f:
                json.dump(errors, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"❌ Error persisting error: {e}")
    
    # Callbacks épicos
    def add_error_callback(self, callback: Callable[[ErrorInfo], None]):
        """➕ Añade callback para errores"""
        self.error_callbacks.append(callback)
    
    def add_recovery_callback(self, callback: Callable[[ErrorInfo, RecoveryAction], None]):
        """➕ Añade callback para recuperación"""
        self.recovery_callbacks.append(callback)
    
    def _call_error_callbacks(self, error_info: ErrorInfo):
        """📞 Llama callbacks de error"""
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.error(f"❌ Error in error callback: {e}")
    
    def _call_recovery_callbacks(self, error_info: ErrorInfo, action: RecoveryAction):
        """📞 Llama callbacks de recuperación"""
        for callback in self.recovery_callbacks:
            try:
                callback(error_info, action)
            except Exception as e:
                self.logger.error(f"❌ Error in recovery callback: {e}")
    
    # Métodos de información y estadísticas
    def get_error_stats(self) -> Dict:
        """📊 OBTIENE ESTADÍSTICAS DE ERRORES"""
        return {
            'total_errors': self.stats['total_errors'],
            'resolved_errors': self.stats['resolved_errors'],
            'failed_recoveries': self.stats['failed_recoveries'],
            'system_restarts': self.stats['system_restarts'],
            'resolution_rate': (self.stats['resolved_errors'] / max(self.stats['total_errors'], 1)) * 100,
            'error_types': dict(self.error_counts),
            'components_in_cooldown': len([c for c, until in self.cooldown_until.items() 
                                         if EcuadorTimeUtils.now() < until]),
            'recent_errors': len([e for e in self.error_history 
                                if e.timestamp > EcuadorTimeUtils.now() - timedelta(hours=1)])
        }
    
    def get_component_health(self, component: str) -> Dict:
        """🏥 OBTIENE SALUD DE COMPONENTE"""
        component_errors = self.component_errors.get(component, [])
        recent_errors = [e for e in component_errors 
                        if e.timestamp > EcuadorTimeUtils.now() - timedelta(hours=1)]
        
        return {
            'component': component,
            'total_errors': len(component_errors),
            'recent_errors': len(recent_errors),
            'in_cooldown': self._is_component_in_cooldown(component),
            'cooldown_until': self.cooldown_until.get(component, None),
            'last_error': component_errors[-1].timestamp.isoformat() if component_errors else None,
            'error_rate': len(recent_errors) / max(1, 1)  # errores por hora
        }
    
    def clear_component_cooldown(self, component: str) -> bool:
        """🧹 LIMPIA COOLDOWN DE COMPONENTE"""
        if component in self.cooldown_until:
            del self.cooldown_until[component]
            self.logger.info(f"🧹 Cleared cooldown for component {component}")
            return True
        return False


def main():
    """🔥 FUNCIÓN PRINCIPAL PARA TESTING 🔥"""
    print("🔥⚔️🏛️ TESTING EPIC ERROR RECOVERY SYSTEM 🏛️⚔️🔥")
    
    # Crear sistema de recuperación
    recovery_system = ErrorRecoverySystem()
    recovery_system.start()
    
    # Callbacks de prueba
    def on_error(error_info: ErrorInfo):
        print(f"🎯 CALLBACK: Error detected - {error_info.error_type.value}")
    
    def on_recovery(error_info: ErrorInfo, action: RecoveryAction):
        print(f"🔧 CALLBACK: Recovery action - {action.value} for {error_info.error_id}")
    
    recovery_system.add_error_callback(on_error)
    recovery_system.add_recovery_callback(on_recovery)
    
    # Simular diferentes tipos de errores
    test_errors = [
        (ConnectionError("Connection timeout"), "NetworkComponent"),
        (ValueError("Invalid JSON data"), "DataProcessor"),
        (Exception("Rate limit exceeded"), "APIClient"),
        (MemoryError("Out of memory"), "SystemCore"),
        (KeyError("Missing configuration"), "ConfigManager")
    ]
    
    print("\n🧪 Testing different error types...")
    for error, component in test_errors:
        print(f"\n🚨 Simulating error in {component}: {error}")
        
        can_continue = recovery_system.handle_error(
            error=error,
            component=component,
            context={'test': True}
        )
        
        print(f"   Can continue: {can_continue}")
        time.sleep(1)
    
    # Esperar procesamiento
    time.sleep(3)
    
    # Mostrar estadísticas
    print(f"\n📊 ERROR STATS:")
    stats = recovery_system.get_error_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Mostrar salud de componentes
    print(f"\n🏥 COMPONENT HEALTH:")
    for component in ["NetworkComponent", "DataProcessor", "APIClient"]:
        health = recovery_system.get_component_health(component)
        print(f"   {component}: {health['total_errors']} errors, cooldown: {health['in_cooldown']}")
    
    # Detener sistema
    recovery_system.stop()
    
    print("\n🏆 EPIC ERROR RECOVERY SYSTEM TEST COMPLETE! 🏆")


if __name__ == "__main__":
    main()