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
    """🎯 DEDUPLICADOR DE ZONAS - EVITA SPAM"""
    
    def __init__(self):
        self.seen_zones = {}  # symbol -> {poi: timestamp}
        self.poi_tolerance = 0.001  # 0.1% tolerancia para POI similares
        self.time_window = 300  # 5 minutos ventana
    
    def is_duplicate(self, symbol: str, poi: float) -> bool:
        """🔍 VERIFICA SI ES ZONA DUPLICADA"""
        
        current_time = datetime.now()
        
        # Limpiar zonas antiguas
        if symbol in self.seen_zones:
            self.seen_zones[symbol] = {
                p: t for p, t in self.seen_zones[symbol].items()
                if (current_time - t).total_seconds() < self.time_window
            }
        
        # Verificar si POI es similar a alguno existente
        if symbol in self.seen_zones:
            for existing_poi in self.seen_zones[symbol].keys():
                if abs(poi - existing_poi) / existing_poi < self.poi_tolerance:
                    return True
        
        # Registrar nueva zona
        if symbol not in self.seen_zones:
            self.seen_zones[symbol] = {}
        
        self.seen_zones[symbol][poi] = current_time
        return False


class FinalDestroyer:
    """🎯⚔️ DESTRUCTOR FINAL SUPREMO ⚔️🎯"""
    
    def __init__(self):
        print("🎯⚔️🏛️ FINAL DESTROYER - VERSIÓN DEFINITIVA 🏛️⚔️🎯")
        print("🎯 UNA SOLA VERSIÓN QUE FUNCIONA")
        
        # Cargar credenciales
        self._load_env()
        
        # Componentes
        self.monitor = MultiSymbolMonitor(
            timeframe="1m",
            enable_alerts=False,  # DESHABILITAMOS ALERTAS SONORAS
            enable_sound=False,   # SIN SONIDOS
            max_workers=3
        )
        
        self.deduplicator = ZoneDeduplicator()
        
        # Símbolos
        self.symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        # Estado
        self.zones_detected = 0
        self.signals_generated = 0
        self.session_start = None
        self.last_display_update = datetime.now()
        
        # Configurar callback
        self._setup_callback()
        
        print("✅ Final Destroyer initialized!")
        print("🔇 Alertas sonoras: DESHABILITADAS")
        print("🎯 Modo: SILENCIO TÁCTICO")
    
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
            """🎯 CALLBACK PRINCIPAL"""
            
            poi = zone_data.get('poi', 0)
            
            # Verificar duplicados
            if self.deduplicator.is_duplicate(symbol, poi):
                return  # Zona duplicada, ignorar
            
            self.zones_detected += 1
            
            # Generar señal
            signal = self._generate_signal(symbol, zone_data)
            
            if signal:
                self.signals_generated += 1
                
                # Mostrar en consola (SIN SONIDO)
                self._display_zone_alert(symbol, zone_data, signal)
                
                # Guardar en archivo ÚNICO
                self._save_signal(signal)
            
            # Actualizar display cada 30 segundos
            now = datetime.now()
            if (now - self.last_display_update).total_seconds() >= 30:
                self._display_status()
                self.last_display_update = now
        
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
        
        print(f"\n{color}🎯 NUEVA ZONA {zone_type} - {symbol} {icon}")
        print(f"⚔️ ACCIÓN: {action}")
        print(f"💰 ENTRADA: ${signal['entry_price']:,.2f}")
        print(f"🛡️ STOP LOSS: ${signal['stop_loss']:,.2f}")
        print(f"🎯 TAKE PROFIT: ${signal['take_profit']:,.2f}")
        print(f"⚖️ RISK/REWARD: {signal['risk_reward_ratio']:.1f}:1")
        print(f"📍 POI: ${signal['poi']:,.2f}")
        print(f"🕐 HORA: {signal['timestamp']}")
        print(f"═══════════════════════════════════════\033[0m")
    
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
    
    def _display_status(self):
        """📊 MUESTRA STATUS CADA 30 SEGUNDOS"""
        
        duration = datetime.now() - self.session_start if self.session_start else timedelta()
        
        print(f"\n📊 STATUS: Duración={duration} | Zonas={self.zones_detected} | Señales={self.signals_generated}")
    
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