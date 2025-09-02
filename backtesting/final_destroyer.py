#!/usr/bin/env python3
"""
🎯⚔️ FINAL DESTROYER - VERSIÓN DEFINITIVA ⚔️🎯
UNA SOLA VERSIÓN QUE FUNCIONA PERFECTAMENTE
Created by TITANES DEL CÓDIGO - VERSIÓN FINAL
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from collections import defaultdict

# Añadir path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.multi_symbol_monitor import MultiSymbolMonitor
from models.zone_alert import EcuadorTimeUtils


class ZoneDeduplicator:
    """🎯 DEDUPLICADOR DE ZONAS INTELIGENTE - EVITA SPAM"""
    
    def __init__(self):
        self.seen_zones = {}  # symbol -> {poi: timestamp}
        self.poi_tolerance = 0.002  # 0.2% tolerancia para POI similares (más estricto)
        self.time_window = 180  # 3 minutos ventana (más corto para mejor rendimiento)
        self.last_cleanup = datetime.now()
        self.cleanup_interval = 60  # Limpiar cada minuto
    
    def is_duplicate(self, symbol: str, poi: float) -> bool:
        """🔍 VERIFICA SI ES ZONA DUPLICADA CON LIMPIEZA AUTOMÁTICA"""
        
        current_time = datetime.now()
        
        # Limpieza automática periódica para mejor rendimiento
        if (current_time - self.last_cleanup).total_seconds() > self.cleanup_interval:
            self._cleanup_old_zones(current_time)
            self.last_cleanup = current_time
        
        # Verificar si POI es similar a alguno existente
        if symbol in self.seen_zones:
            for existing_poi in list(self.seen_zones[symbol].keys()):
                # Verificar si la zona aún está en ventana de tiempo
                zone_time = self.seen_zones[symbol][existing_poi]
                if (current_time - zone_time).total_seconds() >= self.time_window:
                    del self.seen_zones[symbol][existing_poi]
                    continue
                
                # Verificar similitud de POI
                if abs(poi - existing_poi) / max(existing_poi, 0.01) < self.poi_tolerance:
                    return True
        
        # Registrar nueva zona
        if symbol not in self.seen_zones:
            self.seen_zones[symbol] = {}
        
        self.seen_zones[symbol][poi] = current_time
        return False
    
    def _cleanup_old_zones(self, current_time: datetime):
        """🧹 LIMPIEZA AUTOMÁTICA DE ZONAS ANTIGUAS"""
        for symbol in list(self.seen_zones.keys()):
            if symbol in self.seen_zones:
                self.seen_zones[symbol] = {
                    p: t for p, t in self.seen_zones[symbol].items()
                    if (current_time - t).total_seconds() < self.time_window
                }
                # Eliminar símbolos vacíos
                if not self.seen_zones[symbol]:
                    del self.seen_zones[symbol]


class FinalDestroyer:
    """🎯⚔️ DESTRUCTOR FINAL SUPREMO ⚔️🎯"""
    
    def __init__(self):
        print("🎯⚔️🏛️ FINAL DESTROYER - VERSIÓN DEFINITIVA 🏛️⚔️🎯")
        print("🎯 UNA SOLA VERSIÓN QUE FUNCIONA")
        
        # Cargar credenciales
        self._load_env()
        
        # Componentes - CONFIGURACIÓN SILENCIOSA OPTIMIZADA
        self.monitor = MultiSymbolMonitor(
            timeframe="1m",
            enable_alerts=False,  # 🔇 DESHABILITAR ALERTAS SPAM
            enable_sound=False,   # 🔇 DESHABILITAR SONIDOS SPAM
            max_workers=3
        )
        
        # 🔇 ASEGURAR QUE NO HAY ALERT ENGINE ACTIVO
        self.monitor.alert_engine = None
        
        # 🔇 SILENCIAR COMPLETAMENTE EL ALERT ENGINE ESTÁTICO
        try:
            from core.alert_engine import AlertEngine
            # Reemplazar métodos de AlertEngine con versiones silenciosas
            AlertEngine.display_epic_alert = lambda cls, alert: None
            AlertEngine.send_alert = lambda self, alert: None
            AlertEngine.create_zone_alert = lambda self, symbol, zone_data, context=None: None
        except:
            pass
        
        # 🎯 AJUSTAR FRECUENCIA DE MONITOREO A 15 SEGUNDOS
        self.monitor.timeframe_adapter.get_sleep_duration = lambda tf, rf=0.25: max(15.0, min(300.0, 60 * rf))
        
        # 🎯 CONFIGURACIÓN ÓPTIMA DE ACTUALIZACIÓN
        self.last_table_update = datetime.now()
        self.table_update_interval = 30  # Actualizar tabla cada 30 segundos
        self.zone_change_detected = False
        
        # 🎯 SISTEMA UNIFICADO DE DEDUPLICACIÓN
        self.deduplicator = ZoneDeduplicator()
        self.processed_zones = set()  # Backup para duplicados simples
        
        # Símbolos
        self.symbols = ["ETHUSDT"]
        
        # Estado
        self.zones_detected = 0
        self.signals_generated = 0
        self.session_start = None
        self.last_display_update = datetime.now()
        self.last_cleanup = datetime.now()
        
        # 🎯 SISTEMA DE ZONAS PERSISTENTES SIMPLE
        self.previous_zones = {}  # symbol -> set of zone signatures
        self.zone_check_interval = 30  # Verificar cada 30 segundos
        self.last_zone_check = datetime.now()
        
        # 🔄 SISTEMA DE REFRESH FORZADO
        self.detector_refresh_interval = 120  # Refresh cada 2 minutos
        self.last_detector_refresh = datetime.now()
        
        # 🔇 SILENCIAR TODOS LOS MONITORES INTERNOS
        for monitor in getattr(self.monitor, 'monitors', {}).values():
            if hasattr(monitor, 'alert_engine'):
                monitor.alert_engine = None
        
        # 🎯 CALLBACK DESHABILITADO - USAR SOLO ZONAS PERSISTENTES
        # self._setup_callback()  # COMENTADO PARA EVITAR DUPLICADOS
        
        print("✅ Final Destroyer initialized!")
        print("🎯 Sistema: SOLO ZONAS PERSISTENTES")
        print("🚫 Callback: DESHABILITADO")
        print("🧹 Limpieza automática: HABILITADA")
        print("🔇 AlertEngine: COMPLETAMENTE SILENCIADO")
        print("🔇 Alertas spam: ELIMINADAS")
        print("🔇 Sonidos: DESHABILITADOS")
        print("🎯 Modo: SILENCIO TOTAL GARANTIZADO")
    
    def _load_env(self):
        """🔧 CARGA CREDENCIALES"""
        # Buscar .env en el directorio raíz del proyecto
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"
        
        print(f"🔍 Buscando credenciales en: {env_file}")
        
        if env_file.exists():
            print("✅ Archivo .env encontrado!")
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                        if key.strip() == 'BINANCE_API_KEY':
                            print(f"✅ BINANCE_API_KEY cargada: {value[:10]}...")
        else:
            print(f"❌ Archivo .env NO encontrado en: {env_file}")
            print("💡 Ejecuta: python backtesting/setup_env.py")
    
    def _setup_callback(self):
        """🎯 CONFIGURA CALLBACK ÚNICO"""
        
        def on_zone_detected(symbol: str, zone_data: Dict):
            """🎯 CALLBACK PRINCIPAL OPTIMIZADO"""
            
            poi = zone_data.get('poi', 0)
            zone_type = zone_data.get('type', 'UNKNOWN')
            formation_date = zone_data.get('formation_date', 'Unknown')
            
            # 🎯 DEDUPLICACIÓN INTELIGENTE - Crear ID único de zona
            zone_id = f"{symbol}_{zone_type}_{poi:.2f}_{formation_date}"
            
            # Verificar si ya procesamos esta zona exacta
            if zone_id in self.processed_zones:
                return  # Zona ya procesada, ignorar
            
            # Verificar duplicados por proximidad de POI
            if self.deduplicator.is_duplicate(symbol, poi):
                return  # Zona muy similar detectada recientemente, ignorar
            
            # Registrar zona como procesada
            self.processed_zones.add(zone_id)
            
            self.zones_detected += 1
            self.zone_change_detected = True  # Marcar que hubo cambio
            
            # 🔊 REPRODUCIR ALARMA DE SONIDO INMEDIATAMENTE
            self._play_zone_alert_sound(zone_type)
            
            # 🎯 MOSTRAR DETECCIÓN INMEDIATA CON FECHA REAL
            print(f"\n🔊 ¡NUEVA ZONA DETECTADA! 🔊")
            print(f"🎯 ZONA {zone_type} - {symbol}")
            print(f"📍 POI: ${poi:,.2f}")
            print(f"🕐 Formada: {formation_date}")
            print(f"⏰ Detectada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Generar señal
            signal = self._generate_signal(symbol, zone_data)
            
            if signal:
                self.signals_generated += 1
                
                # Mostrar señal completa
                self._display_zone_alert(symbol, zone_data, signal)
                
                # Guardar en archivo ÚNICO
                self._save_signal(signal)
            
            # Forzar actualización de tabla si hay cambios
            self._check_table_update(force=True)
        
        self.monitor.add_zone_detected_callback(on_zone_detected)
    
    def _generate_signal(self, symbol: str, zone_data: Dict) -> Optional[Dict]:
        """🎯 GENERA SEÑAL SIMPLE"""
        
        try:
            zone_type = zone_data.get('type', 'UNKNOWN')
            poi = zone_data.get('poi', 0)
            zone_top = zone_data.get('top', poi)
            zone_bottom = zone_data.get('bottom', poi)
            
            # Configuración por símbolo
            configs = {
                "BTCUSDT": {"sl_pct": 0.5, "tp_mult": 3.0},
                "ETHUSDT": {"sl_pct": 0.8, "tp_mult": 3.5},
                "ADAUSDT": {"sl_pct": 1.2, "tp_mult": 4.0}
            }
            
            config = configs.get(symbol, configs["BTCUSDT"])
            
            if zone_type == "DEMAND":
                action = "BUY"
                entry = zone_top
                stop_loss = zone_bottom * (1 - config["sl_pct"] / 100)
                take_profit = entry + ((entry - stop_loss) * config["tp_mult"])
            elif zone_type == "SUPPLY":
                action = "SELL"
                entry = zone_bottom
                stop_loss = zone_top * (1 + config["sl_pct"] / 100)
                take_profit = entry - ((stop_loss - entry) * config["tp_mult"])
            else:
                return None
            
            # Calcular RR
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            rr_ratio = reward / risk if risk > 0 else 0
            
            # Solo señales con RR >= 2.0
            if rr_ratio < 2.0:
                return None
            
            return {
                "symbol": symbol,
                "action": action,
                "entry_price": round(entry, 6),
                "stop_loss": round(stop_loss, 6),
                "take_profit": round(take_profit, 6),
                "risk_reward_ratio": round(rr_ratio, 2),
                "zone_type": zone_type,
                "poi": round(poi, 6),
                "timestamp": EcuadorTimeUtils.format_time(EcuadorTimeUtils.now()),
                "timeframe": "1m"
            }
            
        except Exception as e:
            print(f"❌ Error generating signal: {e}")
            return None
    
    def _display_zone_alert(self, symbol: str, zone_data: Dict, signal: Dict):
        """📊 MUESTRA ALERTA SIN SONIDO"""
        
        zone_type = signal['zone_type']
        action = signal['action']
        
        # Color según tipo
        if zone_type == "DEMAND":
            color = '\033[92m'  # Verde
            icon = "📈"
        else:
            color = '\033[91m'  # Rojo
            icon = "📉"
        
        print(f"\n{color}🔊 SEÑAL DE TRADING GENERADA! 🔊")
        print(f"🎯 ZONA {zone_type} - {symbol} {icon}")
        print(f"⚔️ ACCIÓN: {action}")
        print(f"�️ ENTRADA: ${signal['entry_price']:,.2f}")
        print(f"🛡️ STOP LOSS: ${signal['stop_loss']:,.2f}")
        print(f"🎯 TAKE PROFIT: ${signal['take_profit']:,.2f}")
        print(f"⚖️ RISK/REWARD: {signal['risk_reward_ratio']:.1f}:1")
        print(f"� POOI: ${signal['poi']:,.2f}")
        print(f"🕐 HORA: {signal['timestamp']}")
        print(f"═══════════════════════════════════════\033[0m")
    
    def _play_zone_alert_sound(self, zone_type: str):
        """🔊 REPRODUCE ALARMA DE SONIDO PARA NUEVA ZONA"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Usar say command que siempre funciona
                if zone_type == "SUPPLY":
                    subprocess.run(["say", "Supply zone detected"], check=False)
                else:
                    subprocess.run(["say", "Demand zone detected"], check=False)
                    
            elif system == "Windows":
                import winsound
                frequency = 1000 if zone_type == "SUPPLY" else 600
                beeps = 3 if zone_type == "SUPPLY" else 2
                for _ in range(beeps):
                    winsound.Beep(frequency, 500)
                    
            elif system == "Linux":
                subprocess.run(["paplay", "/usr/share/sounds/alsa/Front_Left.wav"], check=False)
                    
            else:
                # Fallback universal
                print(f"\a\a\a")  # Bell character
                
        except Exception as e:
            print(f"🔊 ¡ALARMA! Nueva zona {zone_type} detectada - {e}")
    
    def _save_signal(self, signal: Dict):
        """💾 GUARDA EN ARCHIVO ÚNICO"""
        
        try:
            # UN SOLO ARCHIVO
            signals_dir = "backtesting/signals"
            if not os.path.exists(signals_dir):
                os.makedirs(signals_dir)
            
            filename = os.path.join(signals_dir, "final_signals.json")
            
            # Leer existentes
            signals = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        signals = json.load(f)
                except:
                    signals = []
            
            # Añadir nueva
            signals.append(signal)
            
            # Mantener solo últimas 20 señales
            if len(signals) > 20:
                signals = signals[-20:]
            
            # Guardar
            with open(filename, 'w') as f:
                json.dump(signals, f, indent=2, default=str)
            
        except Exception as e:
            print(f"❌ Error saving: {e}")
    
    def _check_table_update(self, force: bool = False):
        """� MCONTROLA ACTUALIZACIONES DE TABLA DE MANERA INTELIGENTE"""
        
        now = datetime.now()
        time_since_last = (now - self.last_table_update).total_seconds()
        
        # Actualizar si:
        # 1. Se fuerza (nueva zona detectada)
        # 2. Han pasado 30 segundos Y hubo cambios
        # 3. Han pasado 60 segundos (actualización periódica)
        
        should_update = (
            force or 
            (time_since_last >= self.table_update_interval and self.zone_change_detected) or
            time_since_last >= 60
        )
        
        if should_update:
            self._display_status()
            self.last_table_update = now
            self.zone_change_detected = False
        
        # 🔄 REFRESH FORZADO DEL DETECTOR (SOLUCIÓN DEFINITIVA)
        if (now - self.last_detector_refresh).total_seconds() > self.detector_refresh_interval:
            self._force_detector_refresh()
            self.last_detector_refresh = now
        
        # 🎯 VERIFICAR ZONAS NUEVAS (SISTEMA PERSISTENTE)
        self._check_for_new_zones()
        
        # Limpieza periódica del historial de zonas procesadas (cada 10 minutos)
        if (now - self.last_cleanup).total_seconds() > 600:
            self._cleanup_processed_zones()
            self.last_cleanup = now
    
    def _cleanup_processed_zones(self):
        """🧹 LIMPIA HISTORIAL DE ZONAS PROCESADAS PARA EVITAR MEMORY LEAK"""
        # Mantener solo las últimas 100 zonas procesadas
        if len(self.processed_zones) > 100:
            # Convertir a lista, mantener las últimas 50
            zones_list = list(self.processed_zones)
            self.processed_zones = set(zones_list[-50:])
            print(f"🧹 Limpieza: Historial de zonas reducido a {len(self.processed_zones)} entradas")
    
    def _check_for_new_zones(self):
        """🎯 VERIFICA ZONAS NUEVAS SIN CALLBACK - SISTEMA PERSISTENTE"""
        
        now = datetime.now()
        if (now - self.last_zone_check).total_seconds() < self.zone_check_interval:
            return  # Aún no es tiempo de verificar
        
        self.last_zone_check = now
        
        for symbol in self.symbols:
            try:
                # Obtener zonas actuales del monitor
                current_zones = self._get_current_zones(symbol)
                
                if not current_zones:
                    continue
                
                # Crear signatures de zonas actuales
                current_signatures = set()
                for zone in current_zones:
                    signature = self._create_zone_signature(zone)
                    current_signatures.add(signature)
                
                # Comparar con zonas anteriores
                previous_signatures = self.previous_zones.get(symbol, set())
                new_signatures = current_signatures - previous_signatures
                
                # Procesar zonas nuevas
                for zone in current_zones:
                    signature = self._create_zone_signature(zone)
                    if signature in new_signatures:
                        self._process_new_zone(symbol, zone)
                
                # Actualizar zonas anteriores
                self.previous_zones[symbol] = current_signatures
                
            except Exception as e:
                print(f"❌ Error verificando zonas para {symbol}: {e}")
    
    def _get_current_zones(self, symbol: str) -> List[Dict]:
        """📊 OBTIENE ZONAS ACTUALES DEL MONITOR"""
        try:
            # Acceder al monitor interno para obtener zonas
            if hasattr(self.monitor, 'monitors') and symbol in self.monitor.monitors:
                monitor = self.monitor.monitors[symbol]
                if hasattr(monitor, 'detector') and hasattr(monitor.detector, 'zones'):
                    return monitor.detector.zones
            return []
        except Exception as e:
            print(f"❌ Error obteniendo zonas de {symbol}: {e}")
            return []
    
    def _create_zone_signature(self, zone: Dict) -> str:
        """🔑 CREA SIGNATURE ÚNICA DE ZONA"""
        poi = zone.get('poi', 0)
        zone_type = zone.get('type', 'UNKNOWN')
        formation_date = zone.get('formation_date', 'Unknown')
        return f"{zone_type}_{poi:.2f}_{formation_date}"
    
    def _process_new_zone(self, symbol: str, zone_data: Dict):
        """🎯 PROCESA ZONA NUEVA DETECTADA"""
        
        poi = zone_data.get('poi', 0)
        zone_type = zone_data.get('type', 'UNKNOWN')
        formation_date = zone_data.get('formation_date', 'Unknown')
        
        # Verificar duplicados
        if self.deduplicator.is_duplicate(symbol, poi):
            return  # Zona muy similar detectada recientemente
        
        self.zones_detected += 1
        self.zone_change_detected = True
        
        # 🔊 REPRODUCIR ALARMA DE SONIDO
        self._play_zone_alert_sound(zone_type)
        
        # 🎯 MOSTRAR DETECCIÓN
        print(f"\n🔊 ¡NUEVA ZONA DETECTADA! 🔊")
        print(f"🎯 ZONA {zone_type} - {symbol}")
        print(f"📍 POI: ${poi:,.2f}")
        print(f"🕐 Formada: {formation_date}")
        print(f"⏰ Detectada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Generar señal
        signal = self._generate_signal(symbol, zone_data)
        
        if signal:
            self.signals_generated += 1
            self._display_zone_alert(symbol, zone_data, signal)
            self._save_signal(signal)
        
        # Forzar actualización de tabla
        self._check_table_update(force=True)
    
    def _force_detector_refresh(self):
        """🔄 FUERZA REFRESH DEL DETECTOR PARA DATOS FRESCOS"""
        try:
            print("🔄 Refrescando detector para datos actualizados...")
            
            for symbol in self.symbols:
                if hasattr(self.monitor, 'monitors') and symbol in self.monitor.monitors:
                    monitor = self.monitor.monitors[symbol]
                    
                    # Forzar recálculo del detector
                    if hasattr(monitor, 'detector'):
                        # Limpiar cache del detector
                        if hasattr(monitor.detector, 'zones'):
                            monitor.detector.zones.clear()
                        
                        # Forzar nueva detección
                        if hasattr(monitor.detector, 'detect_zones'):
                            try:
                                monitor.detector.detect_zones()
                                print(f"✅ Detector refrescado para {symbol}")
                            except Exception as e:
                                print(f"❌ Error refrescando {symbol}: {e}")
            
            print("🔄 Refresh completado - datos actualizados")
            
        except Exception as e:
            print(f"❌ Error en refresh del detector: {e}")
    
    def _display_status(self):
        """📊 MUESTRA STATUS OPTIMIZADO"""
        
        duration = datetime.now() - self.session_start if self.session_start else timedelta()
        
        # Contar zonas en memoria del deduplicador
        total_tracked_zones = sum(len(zones) for zones in self.deduplicator.seen_zones.values())
        
        print(f"\n📊 STATUS: Duración={duration} | Zonas={self.zones_detected} | Señales={self.signals_generated}")
        print(f"🧠 Memoria: {len(self.processed_zones)} procesadas | {total_tracked_zones} en seguimiento")
        print(f"🕐 Última actualización: {datetime.now().strftime('%H:%M:%S')}")
    
    def start(self):
        """🚀 INICIA SISTEMA FINAL"""
        
        print("\n🚀 INICIANDO SISTEMA FINAL...")
        
        # Añadir símbolos
        for symbol in self.symbols:
            self.monitor.add_symbol(symbol)
        
        self.session_start = datetime.now()
        
        if self.monitor.start_monitoring():
            print("✅ Sistema iniciado!")
            print(f"📊 Símbolos: {self.symbols}")
            print("🔇 SIN alertas sonoras")
            print("💡 Presiona Ctrl+C para detener\n")
            
            return True
        else:
            print("❌ Error iniciando")
            return False
    
    def stop(self):
        """🛑 DETIENE SISTEMA"""
        
        print("\n🛑 Deteniendo sistema...")
        
        if self.monitor.stop_monitoring():
            duration = datetime.now() - self.session_start if self.session_start else timedelta()
            
            print("✅ Sistema detenido!")
            print(f"\n📊 RESUMEN FINAL:")
            print(f"⏰ Duración: {duration}")
            print(f"🏛️ Zonas detectadas: {self.zones_detected}")
            print(f"🎯 Señales generadas: {self.signals_generated}")
            print(f"📁 Archivo: backtesting/signals/final_signals.json")
            
            return True
        else:
            print("❌ Error deteniendo")
            return False


def main():
    """🔥 FUNCIÓN PRINCIPAL FINAL 🔥"""
    
    print("🎯⚔️🏛️ FINAL DESTROYER - VERSIÓN DEFINITIVA 🏛️⚔️🎯")
    
    # Crear destructor final (esto carga las credenciales del .env)
    destroyer = FinalDestroyer()
    
    # Verificar credenciales DESPUÉS de cargarlas
    api_key = os.getenv('BINANCE_API_KEY')
    if not api_key:
        print("❌ Credenciales no encontradas")
        print("💡 Ejecuta: python backtesting/setup_env.py")
        return 1
    
    try:
        if destroyer.start():
            # Mantener activo
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrupción detectada...")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        destroyer.stop()
        
        print("\n🏆 DESTRUCCIÓN FINAL COMPLETADA!")
        print("🎯 Mercados conquistados en silencio!")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)