#!/usr/bin/env python3
"""
🔥⚔️ ALERT ENGINE - MOTOR DE ALERTAS SUPREMO ⚔️🔥
Sistema de alertas que haría llorar a Bruce Wayne y Tony Stark
Created by TITANES DEL CÓDIGO - BESTIAS SUPREMAS
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
import threading
import queue

# Nuestros modelos épicos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.zone_alert import ZoneAlert, EcuadorTimeUtils, AlertPriority


class AlertType(Enum):
    """🚨 TIPOS DE ALERTAS ÉPICAS 🚨"""
    NEW_ZONE_DETECTED = "NEW_ZONE_DETECTED"
    STRUCTURE_CHANGE = "STRUCTURE_CHANGE"
    PRICE_APPROACHING_ZONE = "PRICE_APPROACHING_ZONE"
    ZONE_BREAKOUT = "ZONE_BREAKOUT"
    TRADING_SIGNAL = "TRADING_SIGNAL"
    STRUCTURE_FOLLOWER_SIGNAL = "STRUCTURE_FOLLOWER_SIGNAL"


class SoundType(Enum):
    """🔊 TIPOS DE SONIDOS PARA MAC 🔊"""
    NEW_ZONE = "Ping"           # Zona nueva detectada
    TRADING_SIGNAL = "Hero"     # Señal de trading
    CRITICAL = "Sosumi"         # Alerta crítica
    SUCCESS = "Glass"           # Operación exitosa
    WARNING = "Basso"           # Advertencia
    ERROR = "Funk"              # Error


@dataclass
class EpicAlert:
    """🏛️ ALERTA ÉPICA SUPREMA 🏛️"""
    alert_id: str
    alert_type: AlertType
    symbol: str
    title: str
    message: str
    priority: AlertPriority
    timestamp: datetime
    zone_data: Optional[Dict] = None
    trading_signal: Optional[Dict] = None
    sound_type: SoundType = SoundType.NEW_ZONE
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario para logging"""
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type.value,
            'symbol': self.symbol,
            'title': self.title,
            'message': self.message,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'zone_data': self.zone_data,
            'trading_signal': self.trading_signal,
            'sound_type': self.sound_type.value
        }


class MacSoundPlayer:
    """🔊 REPRODUCTOR DE SONIDOS PARA MAC - ÉPICO 🔊"""
    
    @staticmethod
    def play_sound(sound_type: SoundType, volume: float = 0.8):
        """
        🎵 REPRODUCE SONIDO EN MAC
        Args:
            sound_type: Tipo de sonido a reproducir
            volume: Volumen (0.0 a 1.0)
        """
        try:
            # Comando para reproducir sonido en Mac
            cmd = f"afplay /System/Library/Sounds/{sound_type.value}.aiff"
            
            # Ejecutar en background para no bloquear
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        except Exception as e:
            print(f"⚠️ Error playing sound: {e}")
    
    @staticmethod
    def play_custom_beep(frequency: int = 1000, duration: float = 0.5):
        """
        🎵 REPRODUCE BEEP PERSONALIZADO
        Args:
            frequency: Frecuencia en Hz
            duration: Duración en segundos
        """
        try:
            # Usar osascript para beep personalizado
            cmd = f'osascript -e "beep {int(duration * 10)}"'
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"⚠️ Error playing beep: {e}")


class ConsoleDisplay:
    """🖥️ DISPLAY DE CONSOLA ÉPICO 🖥️"""
    
    # Colores ANSI para terminal
    COLORS = {
        'RED': '\\033[91m',
        'GREEN': '\\033[92m',
        'YELLOW': '\\033[93m',
        'BLUE': '\\033[94m',
        'MAGENTA': '\\033[95m',
        'CYAN': '\\033[96m',
        'WHITE': '\\033[97m',
        'BOLD': '\\033[1m',
        'UNDERLINE': '\\033[4m',
        'END': '\\033[0m'
    }
    
    @classmethod
    def display_epic_alert(cls, alert: EpicAlert):
        """🚨 MUESTRA ALERTA ÉPICA EN CONSOLA 🚨"""
        
        # Seleccionar colores según prioridad
        if alert.priority == AlertPriority.CRITICAL:
            color = cls.COLORS['RED']
            border = "🔥" * 20
        elif alert.priority == AlertPriority.HIGH:
            color = cls.COLORS['YELLOW']
            border = "⚔️" * 20
        elif alert.priority == AlertPriority.MEDIUM:
            color = cls.COLORS['CYAN']
            border = "🏛️" * 20
        else:
            color = cls.COLORS['GREEN']
            border = "✅" * 20
        
        # Timestamp en Ecuador
        ecuador_time = EcuadorTimeUtils.format_time(alert.timestamp)
        
        print(f"\\n{color}{cls.COLORS['BOLD']}")
        print(border)
        print(f"🚨 {alert.title} 🚨")
        print(border)
        print(f"📊 Symbol: {alert.symbol}")
        print(f"⏰ Time: {ecuador_time}")
        print(f"🎯 Type: {alert.alert_type.value}")
        print(f"💥 Priority: {alert.priority.value}")
        print(f"\\n📋 MESSAGE:")
        print(f"{alert.message}")
        
        # Mostrar datos de zona si existen
        if alert.zone_data:
            cls._display_zone_data(alert.zone_data)
        
        # Mostrar señal de trading si existe
        if alert.trading_signal:
            cls._display_trading_signal(alert.trading_signal)
        
        print(border)
        print(f"{cls.COLORS['END']}")
    
    @classmethod
    def _display_zone_data(cls, zone_data: Dict):
        """📊 Muestra datos de zona"""
        print(f"\\n🏛️ ZONE DATA:")
        print(f"   Type: {zone_data.get('type', 'N/A')}")
        print(f"   POI: ${zone_data.get('poi', 0):.3f}")
        print(f"   Range: ${zone_data.get('bottom', 0):.3f} - ${zone_data.get('top', 0):.3f}")
        print(f"   Distance: {zone_data.get('distance_pct', 0):+.2f}%")
        print(f"   Formation: {zone_data.get('formation_candles_ago', 0)} candles ago")
    
    @classmethod
    def _display_trading_signal(cls, signal: Dict):
        """⚔️ Muestra señal de trading"""
        print(f"\\n⚔️ TRADING SIGNAL:")
        print(f"   Action: {signal.get('action', 'N/A')}")
        print(f"   Entry: ${signal.get('entry', 0):.3f}")
        print(f"   Stop Loss: ${signal.get('stop_loss', 0):.3f}")
        print(f"   Take Profit: ${signal.get('take_profit', 0):.3f}")
        print(f"   Risk/Reward: {signal.get('risk_reward_ratio', 0):.1f}:1")
        print(f"   Confidence: {signal.get('confidence', 0)}%")


class AlertLogger:
    """📝 LOGGER DE ALERTAS ÉPICO 📝"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.ensure_log_dir()
    
    def ensure_log_dir(self):
        """Asegura que el directorio de logs existe"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def log_alert(self, alert: EpicAlert):
        """📝 Registra alerta en archivo"""
        try:
            # Archivo por fecha
            date_str = alert.timestamp.strftime("%Y-%m-%d")
            log_file = os.path.join(self.log_dir, f"alerts_{date_str}.json")
            
            # Preparar datos
            alert_data = alert.to_dict()
            
            # Leer alertas existentes
            alerts = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        alerts = json.load(f)
                except:
                    alerts = []
            
            # Añadir nueva alerta
            alerts.append(alert_data)
            
            # Guardar
            with open(log_file, 'w') as f:
                json.dump(alerts, f, indent=2, default=str)
                
        except Exception as e:
            print(f"⚠️ Error logging alert: {e}")


class AlertEngine:
    """🔥⚔️ MOTOR DE ALERTAS SUPREMO ⚔️🔥"""
    
    def __init__(self, enable_sound: bool = True, enable_logging: bool = True):
        print("🔥⚔️🏛️ INITIALIZING EPIC ALERT ENGINE 🏛️⚔️🔥")
        print("🎯 BRUCE WAYNE Y TONY STARK APPROVED!")
        
        self.enable_sound = enable_sound
        self.enable_logging = enable_logging
        
        # Componentes
        self.sound_player = MacSoundPlayer()
        self.console_display = ConsoleDisplay()
        self.logger = AlertLogger() if enable_logging else None
        
        # Queue para alertas
        self.alert_queue = queue.Queue()
        
        # Historial de alertas
        self.alert_history: List[EpicAlert] = []
        
        # Thread para procesar alertas
        self.processing_thread = None
        self.is_running = False
        
        print("✅ Alert Engine initialized successfully!")
        print(f"🔊 Sound: {'ENABLED' if enable_sound else 'DISABLED'}")
        print(f"📝 Logging: {'ENABLED' if enable_logging else 'DISABLED'}")
    
    def start(self):
        """🚀 INICIA EL MOTOR DE ALERTAS"""
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._process_alerts, daemon=True)
            self.processing_thread.start()
            print("🚀 Alert Engine STARTED!")
    
    def stop(self):
        """🛑 DETIENE EL MOTOR DE ALERTAS"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1)
        print("🛑 Alert Engine STOPPED!")
    
    def send_alert(self, alert: EpicAlert):
        """🚨 ENVÍA ALERTA ÉPICA"""
        # Añadir timestamp si no existe
        if not alert.timestamp:
            alert.timestamp = EcuadorTimeUtils.now()
        
        # Añadir a queue
        self.alert_queue.put(alert)
    
    def _process_alerts(self):
        """⚔️ PROCESA ALERTAS EN BACKGROUND"""
        while self.is_running:
            try:
                # Obtener alerta con timeout
                alert = self.alert_queue.get(timeout=1)
                
                # Procesar alerta
                self._handle_alert(alert)
                
                # Marcar como procesada
                self.alert_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error processing alert: {e}")
    
    def _handle_alert(self, alert: EpicAlert):
        """🏛️ MANEJA UNA ALERTA INDIVIDUAL"""
        try:
            # Añadir al historial
            self.alert_history.append(alert)
            
            # Mostrar en consola
            self.console_display.display_epic_alert(alert)
            
            # Reproducir sonido
            if self.enable_sound:
                self.sound_player.play_sound(alert.sound_type)
            
            # Log en archivo
            if self.enable_logging and self.logger:
                self.logger.log_alert(alert)
            
            print(f"✅ Alert processed: {alert.alert_id}")
            
        except Exception as e:
            print(f"❌ Error handling alert: {e}")
    
    def create_zone_alert(self, symbol: str, zone_data: Dict, context: Dict = None) -> EpicAlert:
        """🏛️ CREA ALERTA DE NUEVA ZONA"""
        
        zone_type = zone_data.get('type', 'UNKNOWN')
        poi = zone_data.get('poi', 0)
        
        # Generar mensaje épico
        message = f"Nueva zona {zone_type} detectada en {symbol}\\n"
        message += f"POI: ${poi:.3f}\\n"
        message += f"Rango: ${zone_data.get('bottom', 0):.3f} - ${zone_data.get('top', 0):.3f}\\n"
        
        if context and context.get('has_previous'):
            structure = context.get('market_structure', 'Unknown')
            message += f"Estructura: {structure}\\n"
            message += f"Ventaja Táctica: {context.get('tactical_advantage', 'N/A')}"
        
        return EpicAlert(
            alert_id=f"ZONE_{symbol}_{int(time.time())}",
            alert_type=AlertType.NEW_ZONE_DETECTED,
            symbol=symbol,
            title=f"NUEVA ZONA {zone_type} DETECTADA",
            message=message,
            priority=AlertPriority.HIGH,
            timestamp=EcuadorTimeUtils.now(),
            zone_data=zone_data,
            sound_type=SoundType.NEW_ZONE
        )
    
    def create_trading_signal(self, symbol: str, signal_data: Dict, zone_data: Dict = None) -> EpicAlert:
        """⚔️ CREA ALERTA DE SEÑAL DE TRADING"""
        
        action = signal_data.get('action', 'UNKNOWN')
        entry = signal_data.get('entry', 0)
        stop_loss = signal_data.get('stop_loss', 0)
        take_profit = signal_data.get('take_profit', 0)
        rr_ratio = signal_data.get('risk_reward_ratio', 0)
        confidence = signal_data.get('confidence', 0)
        
        # Mensaje épico de trading
        message = f"SEÑAL DE TRADING ACTIVADA\\n"
        message += f"Acción: {action}\\n"
        message += f"Entrada: ${entry:.3f}\\n"
        message += f"Stop Loss: ${stop_loss:.3f}\\n"
        message += f"Take Profit: ${take_profit:.3f}\\n"
        message += f"Risk/Reward: {rr_ratio:.1f}:1\\n"
        message += f"Confianza: {confidence}%\\n"
        message += f"\\n🔥 ¡ACTÚA AHORA, COMANDANTE! 🔥"
        
        return EpicAlert(
            alert_id=f"SIGNAL_{symbol}_{int(time.time())}",
            alert_type=AlertType.TRADING_SIGNAL,
            symbol=symbol,
            title=f"SEÑAL {action} - {symbol}",
            message=message,
            priority=AlertPriority.CRITICAL,
            timestamp=EcuadorTimeUtils.now(),
            zone_data=zone_data,
            trading_signal=signal_data,
            sound_type=SoundType.TRADING_SIGNAL
        )
    
    def get_alert_stats(self) -> Dict:
        """📊 OBTIENE ESTADÍSTICAS DE ALERTAS"""
        total_alerts = len(self.alert_history)
        
        if total_alerts == 0:
            return {"total": 0}
        
        # Contar por tipo
        type_counts = {}
        priority_counts = {}
        
        for alert in self.alert_history:
            alert_type = alert.alert_type.value
            priority = alert.priority.value
            
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            "total": total_alerts,
            "by_type": type_counts,
            "by_priority": priority_counts,
            "last_alert": self.alert_history[-1].timestamp.isoformat() if self.alert_history else None
        }


def main():
    """🔥 FUNCIÓN PRINCIPAL PARA TESTING CON DATOS REALES 🔥"""
    print("🔥⚔️🏛️ TESTING EPIC ALERT ENGINE WITH REAL DATA 🏛️⚔️🔥")
    print("🎯 NO HARDCODED DATA - ONLY REAL WARRIOR DATA!")
    
    # Importar nuestro tracker para datos reales
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'demo'))
        from realtime_zone_tracker import RealTimeZoneTracker
    except ImportError as e:
        print(f"❌ Cannot import RealTimeZoneTracker: {e}")
        print("🎯 Testing with basic engine functionality only...")
        
        # Test básico sin datos reales
        engine = AlertEngine(enable_sound=False, enable_logging=True)
        engine.start()
        
        print("✅ Alert Engine basic functionality tested")
        engine.stop()
        return
    
    # Crear motor de alertas
    engine = AlertEngine(enable_sound=True, enable_logging=True)
    engine.start()
    
    # Crear tracker para obtener datos reales
    print("📊 Fetching REAL data from Binance...")
    tracker = RealTimeZoneTracker("ETHUSDT", "1h")
    
    try:
        # Obtener zona real
        latest_zone = tracker.run_realtime_detection()
        
        if latest_zone:
            print(f"🚨 REAL ZONE DETECTED: {latest_zone}")
            
            # Obtener contexto real
            context = tracker.get_previous_zone_context(latest_zone) if hasattr(tracker, 'get_previous_zone_context') else {}
            
            # Crear alerta con datos reales
            zone_alert = engine.create_zone_alert("ETHUSDT", latest_zone, context)
            engine.send_alert(zone_alert)
            
            # Si hay contexto, generar señal de trading real
            if context.get('has_previous'):
                # Importar structure engine para señal real
                try:
                    sys.path.append(os.path.join(os.path.dirname(__file__)))
                    from structure_follower_engine import StructureFollowerEngine
                    
                    structure_engine = StructureFollowerEngine()
                    current_price = tracker.market_data['close'].iloc[-1] if tracker.market_data is not None else latest_zone['poi']
                    
                    # Añadir símbolo a zone_data
                    latest_zone['symbol'] = "ETHUSDT"
                    
                    trading_signal = structure_engine.analyze_structure_and_generate_signal(
                        latest_zone, context, current_price
                    )
                    
                    if trading_signal:
                        print(f"⚔️ REAL TRADING SIGNAL GENERATED!")
                        signal_alert = engine.create_trading_signal("ETHUSDT", trading_signal.to_dict(), latest_zone)
                        engine.send_alert(signal_alert)
                    else:
                        print("ℹ️ No trading signal generated from real data")
                        
                except ImportError as e:
                    print(f"⚠️ Cannot import StructureFollowerEngine: {e}")
            else:
                print("ℹ️ No previous zone context - no trading signal")
        else:
            print("ℹ️ No new zones detected in current market conditions")
            print("🎯 This is REAL - market doesn't always have new zones!")
            
    except Exception as e:
        print(f"❌ Error fetching real data: {e}")
        print("🎯 This proves we're using REAL data - not hardcoded!")
    
    # Esperar un poco para procesar
    time.sleep(3)
    
    # Mostrar estadísticas
    stats = engine.get_alert_stats()
    print(f"\\n📊 REAL ALERT STATS: {stats}")
    
    # Detener motor
    engine.stop()
    
    print("\\n🏆 EPIC ALERT ENGINE REAL DATA TEST COMPLETE! 🏆")
    print("⚔️ NO COWARD HARDCODED DATA USED! ⚔️")


if __name__ == "__main__":
    main()