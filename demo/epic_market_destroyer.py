#!/usr/bin/env python3
"""
🔥⚔️ EPIC MARKET DESTROYER - ARMA ASESINA DE MERCADOS ⚔️🔥
Sistema que haría llorar a Ra, Odin, Zeus y Anu de admiración
Created by TITANES DEL CÓDIGO - DIOSES DE LA DESTRUCCIÓN DE MERCADOS
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Añadir path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.multi_symbol_monitor import MultiSymbolMonitor
from core.alert_engine import AlertEngine, EpicAlert, AlertType, SoundType
from models.zone_alert import EcuadorTimeUtils, AlertPriority


class TradingSignalGenerator:
    """⚔️ GENERADOR DE SEÑALES DE TRADING ÉPICO ⚔️"""
    
    def __init__(self):
        print("⚔️🏛️ INITIALIZING EPIC TRADING SIGNAL GENERATOR 🏛️⚔️")
        
        # Configuraciones por símbolo
        self.symbol_configs = {
            "BTCUSDT": {
                "risk_reward_min": 2.0,
                "stop_loss_pct": 0.5,  # 0.5% para BTC
                "take_profit_multiplier": 3.0
            },
            "ETHUSDT": {
                "risk_reward_min": 2.5,
                "stop_loss_pct": 0.8,  # 0.8% para ETH
                "take_profit_multiplier": 3.5
            },
            "ADAUSDT": {
                "risk_reward_min": 3.0,
                "stop_loss_pct": 1.2,  # 1.2% para ADA
                "take_profit_multiplier": 4.0
            }
        }
        
        print("✅ Trading Signal Generator initialized!")
    
    def generate_trading_signal(self, symbol: str, zone_data: Dict, current_price: float) -> Dict:
        """
        🎯 GENERA SEÑAL DE TRADING ÉPICA
        Args:
            symbol: Símbolo del activo
            zone_data: Datos de la zona detectada
            current_price: Precio actual
        Returns:
            Señal de trading completa
        """
        try:
            config = self.symbol_configs.get(symbol, self.symbol_configs["BTCUSDT"])
            zone_type = zone_data.get('type', 'UNKNOWN')
            poi = zone_data.get('poi', current_price)
            zone_top = zone_data.get('top', poi)
            zone_bottom = zone_data.get('bottom', poi)
            
            # Determinar dirección de la señal
            if zone_type == "DEMAND":
                action = "BUY"
                entry_price = zone_top  # Entrada en el tope de la zona de demanda
                stop_loss = zone_bottom * (1 - config["stop_loss_pct"] / 100)
                take_profit = entry_price + ((entry_price - stop_loss) * config["take_profit_multiplier"])
            elif zone_type == "SUPPLY":
                action = "SELL"
                entry_price = zone_bottom  # Entrada en el fondo de la zona de supply
                stop_loss = zone_top * (1 + config["stop_loss_pct"] / 100)
                take_profit = entry_price - ((stop_loss - entry_price) * config["take_profit_multiplier"])
            else:
                # Zona neutral - determinar por posición del precio
                if current_price < poi:
                    action = "BUY"
                    entry_price = poi
                    stop_loss = entry_price * (1 - config["stop_loss_pct"] / 100)
                    take_profit = entry_price * (1 + (config["stop_loss_pct"] * config["take_profit_multiplier"]) / 100)
                else:
                    action = "SELL"
                    entry_price = poi
                    stop_loss = entry_price * (1 + config["stop_loss_pct"] / 100)
                    take_profit = entry_price * (1 - (config["stop_loss_pct"] * config["take_profit_multiplier"]) / 100)
            
            # Calcular risk/reward ratio
            if action == "BUY":
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
            else:
                risk = abs(stop_loss - entry_price)
                reward = abs(entry_price - take_profit)
            
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Calcular confianza basada en la calidad de la zona
            confidence = self._calculate_confidence(zone_data, risk_reward_ratio, config)
            
            # Generar timestamp de entrada (ahora + 1 minuto para dar tiempo)
            entry_time = EcuadorTimeUtils.now() + timedelta(minutes=1)
            
            signal = {
                "symbol": symbol,
                "action": action,
                "entry_price": round(entry_price, 6),
                "stop_loss": round(stop_loss, 6),
                "take_profit": round(take_profit, 6),
                "risk_reward_ratio": round(risk_reward_ratio, 2),
                "confidence": confidence,
                "zone_type": zone_type,
                "poi": round(poi, 6),
                "entry_time": entry_time.isoformat(),
                "entry_time_utc5": EcuadorTimeUtils.format_time(entry_time),
                "zone_formation_time": EcuadorTimeUtils.format_time(EcuadorTimeUtils.now()),
                "timeframe": "1m",
                "risk_pct": config["stop_loss_pct"],
                "reward_multiplier": config["take_profit_multiplier"]
            }
            
            return signal
            
        except Exception as e:
            print(f"❌ Error generating trading signal: {e}")
            return {}
    
    def _calculate_confidence(self, zone_data: Dict, rr_ratio: float, config: Dict) -> int:
        """
        🎯 CALCULA CONFIANZA DE LA SEÑAL
        Args:
            zone_data: Datos de la zona
            rr_ratio: Risk/Reward ratio
            config: Configuración del símbolo
        Returns:
            Confianza en porcentaje (0-100)
        """
        confidence = 50  # Base
        
        # Bonus por risk/reward ratio
        if rr_ratio >= config["risk_reward_min"]:
            confidence += 20
        elif rr_ratio >= config["risk_reward_min"] * 0.8:
            confidence += 10
        
        # Bonus por distancia de formación (zonas más recientes son mejores)
        formation_candles = zone_data.get('formation_candles_ago', 10)
        if formation_candles <= 5:
            confidence += 15
        elif formation_candles <= 10:
            confidence += 10
        elif formation_candles <= 20:
            confidence += 5
        
        # Bonus por tipo de zona
        zone_type = zone_data.get('type', 'UNKNOWN')
        if zone_type in ['DEMAND', 'SUPPLY']:
            confidence += 10
        
        # Bonus por fuerza de la zona (si está disponible)
        zone_strength = zone_data.get('strength', 0)
        if zone_strength > 0.8:
            confidence += 10
        elif zone_strength > 0.6:
            confidence += 5
        
        return min(100, max(0, confidence))


class EpicMarketDestroyer:
    """🔥⚔️ DESTRUCTOR ÉPICO DE MERCADOS ⚔️🔥"""
    
    def __init__(self):
        print("🔥⚔️🏛️ INITIALIZING EPIC MARKET DESTROYER 🏛️⚔️🔥")
        print("🎯 RA, ODIN, ZEUS Y ANU APPROVED!")
        print("💀 PREPARANDO ARMA ASESINA DE MERCADOS...")
        
        # Componentes épicos
        self.monitor = MultiSymbolMonitor(
            timeframe="1m",  # 1 minuto para máxima precisión
            enable_alerts=True,
            enable_sound=True,
            max_workers=3  # Un worker por símbolo
        )
        
        self.signal_generator = TradingSignalGenerator()
        
        # Símbolos de la trinidad sagrada
        self.sacred_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        # Estadísticas épicas
        self.zones_detected = 0
        self.signals_generated = 0
        self.session_start = None
        
        # Configurar callbacks
        self._setup_callbacks()
        
        print("✅ Epic Market Destroyer initialized!")
        print("🏛️ Ready to destroy markets like the gods intended!")
    
    def _setup_callbacks(self):
        """⚔️ CONFIGURA CALLBACKS ÉPICOS"""
        
        def on_zone_detected(symbol: str, zone_data: Dict):
            """🚨 Callback cuando se detecta nueva zona"""
            self.zones_detected += 1
            
            print(f"\n🔥⚔️ NUEVA ZONA DETECTADA - {symbol} ⚔️🔥")
            print(f"🏛️ Tipo: {zone_data.get('type', 'UNKNOWN')}")
            print(f"📍 POI: ${zone_data.get('poi', 0):.6f}")
            print(f"📊 Rango: ${zone_data.get('bottom', 0):.6f} - ${zone_data.get('top', 0):.6f}")
            print(f"⏰ Formación: {zone_data.get('formation_candles_ago', 0)} velas atrás")
            print(f"🕐 Hora UTC-5: {EcuadorTimeUtils.format_time(EcuadorTimeUtils.now())}")
            
            # Generar señal de trading
            current_price = zone_data.get('poi', 0)  # Usar POI como precio actual
            signal = self.signal_generator.generate_trading_signal(symbol, zone_data, current_price)
            
            if signal:
                self.signals_generated += 1
                self._display_trading_signal(signal)
                self._save_signal_to_file(signal)
        
        def on_error(symbol: str, error: Exception):
            """❌ Callback para errores"""
            print(f"⚠️ Error en {symbol}: {error}")
        
        def on_state_change(old_state, new_state):
            """🔄 Callback para cambios de estado"""
            print(f"🔄 Estado: {old_state.value} -> {new_state.value}")
        
        # Registrar callbacks
        self.monitor.add_zone_detected_callback(on_zone_detected)
        self.monitor.add_error_callback(on_error)
        self.monitor.add_state_change_callback(on_state_change)
    
    def _display_trading_signal(self, signal: Dict):
        """🎯 MUESTRA SEÑAL DE TRADING ÉPICA"""
        
        print(f"\n{'='*80}")
        print(f"🎯⚔️ SEÑAL DE TRADING ÉPICA - {signal['symbol']} ⚔️🎯")
        print(f"{'='*80}")
        print(f"🔥 ACCIÓN: {signal['action']}")
        print(f"💰 ENTRADA: ${signal['entry_price']:.6f}")
        print(f"🛡️ STOP LOSS: ${signal['stop_loss']:.6f}")
        print(f"🎯 TAKE PROFIT: ${signal['take_profit']:.6f}")
        print(f"⚖️ RISK/REWARD: {signal['risk_reward_ratio']:.2f}:1")
        print(f"🎲 CONFIANZA: {signal['confidence']}%")
        print(f"🏛️ TIPO ZONA: {signal['zone_type']}")
        print(f"📍 POI: ${signal['poi']:.6f}")
        print(f"⏰ HORA FORMACIÓN: {signal['zone_formation_time']}")
        print(f"🕐 HORA ENTRADA: {signal['entry_time_utc5']}")
        print(f"📊 TIMEFRAME: {signal['timeframe']}")
        print(f"⚠️ RIESGO: {signal['risk_pct']}%")
        print(f"🚀 MULTIPLICADOR: {signal['reward_multiplier']}x")
        print(f"{'='*80}")
        
        # Mensaje épico según confianza
        if signal['confidence'] >= 80:
            print("🔥🔥🔥 SEÑAL DE ALTA CONFIANZA - ¡ACTÚA AHORA! 🔥🔥🔥")
        elif signal['confidence'] >= 60:
            print("⚔️⚔️ SEÑAL SÓLIDA - CONSIDERA LA ENTRADA ⚔️⚔️")
        else:
            print("🏛️ SEÑAL MODERADA - PROCEDE CON CAUTELA 🏛️")
        
        print(f"{'='*80}\n")
    
    def _save_signal_to_file(self, signal: Dict):
        """💾 GUARDA SEÑAL EN ARCHIVO"""
        try:
            # Crear directorio si no existe
            signals_dir = "signals"
            if not os.path.exists(signals_dir):
                os.makedirs(signals_dir)
            
            # Archivo por fecha
            date_str = EcuadorTimeUtils.now().strftime("%Y-%m-%d")
            filename = os.path.join(signals_dir, f"trading_signals_{date_str}.json")
            
            # Leer señales existentes
            signals = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        signals = json.load(f)
                except:
                    signals = []
            
            # Añadir nueva señal
            signals.append(signal)
            
            # Guardar
            with open(filename, 'w') as f:
                json.dump(signals, f, indent=2, default=str)
            
            print(f"💾 Señal guardada en: {filename}")
            
        except Exception as e:
            print(f"❌ Error guardando señal: {e}")
    
    def start_destruction(self):
        """🚀 INICIA LA DESTRUCCIÓN ÉPICA DE MERCADOS"""
        
        print("\n🔥⚔️🏛️ INICIANDO DESTRUCCIÓN ÉPICA DE MERCADOS 🏛️⚔️🔥")
        print("💀 Los dioses tiemblan ante nuestro poder...")
        
        # Añadir símbolos sagrados
        for symbol in self.sacred_symbols:
            self.monitor.add_symbol(symbol)
            print(f"⚔️ Símbolo añadido: {symbol}")
        
        # Iniciar monitoring
        self.session_start = EcuadorTimeUtils.now()
        
        if self.monitor.start_monitoring():
            print("✅ Monitoring iniciado exitosamente!")
            print(f"📊 Símbolos: {self.sacred_symbols}")
            print(f"⏰ Timeframe: 1 minuto")
            print(f"🕐 Inicio: {EcuadorTimeUtils.format_time(self.session_start)}")
            print("\n🎯 Esperando detección de zonas...")
            print("💡 Presiona Ctrl+C para detener\n")
            
            return True
        else:
            print("❌ Error iniciando monitoring")
            return False
    
    def stop_destruction(self):
        """🛑 DETIENE LA DESTRUCCIÓN"""
        
        print("\n🛑 Deteniendo destrucción de mercados...")
        
        if self.monitor.stop_monitoring():
            session_end = EcuadorTimeUtils.now()
            duration = session_end - self.session_start if self.session_start else timedelta()
            
            print("✅ Monitoring detenido exitosamente!")
            print(f"\n📊 ESTADÍSTICAS DE LA SESIÓN:")
            print(f"⏰ Duración: {duration}")
            print(f"🏛️ Zonas detectadas: {self.zones_detected}")
            print(f"🎯 Señales generadas: {self.signals_generated}")
            print(f"🕐 Fin: {EcuadorTimeUtils.format_time(session_end)}")
            
            return True
        else:
            print("❌ Error deteniendo monitoring")
            return False
    
    def get_status(self) -> Dict:
        """📊 OBTIENE STATUS ÉPICO"""
        monitor_status = self.monitor.get_status()
        
        duration = timedelta()
        if self.session_start:
            duration = EcuadorTimeUtils.now() - self.session_start
        
        return {
            "session_duration": str(duration),
            "zones_detected": self.zones_detected,
            "signals_generated": self.signals_generated,
            "monitor_status": monitor_status,
            "sacred_symbols": self.sacred_symbols,
            "session_start": self.session_start.isoformat() if self.session_start else None
        }


def main():
    """🔥 FUNCIÓN PRINCIPAL ÉPICA 🔥"""
    
    print("🔥⚔️🏛️ EPIC MARKET DESTROYER - DEMO SUPREMO 🏛️⚔️🔥")
    print("💀 Preparando el arma que haría llorar a los dioses...")
    
    # Crear destructor épico
    destroyer = EpicMarketDestroyer()
    
    try:
        # Iniciar destrucción
        if destroyer.start_destruction():
            
            # Correr indefinidamente hasta Ctrl+C
            while True:
                time.sleep(10)
                
                # Mostrar status cada 10 segundos
                status = destroyer.get_status()
                print(f"📊 Status: Zonas={status['zones_detected']}, Señales={status['signals_generated']}, Duración={status['session_duration']}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupción del usuario detectada...")
    
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
    
    finally:
        # Detener destrucción
        destroyer.stop_destruction()
        
        print("\n🏆 DESTRUCCIÓN COMPLETADA!")
        print("🎯 Los mercados han sido conquistados por los dioses del código!")
        print("⚔️ Ra, Odin, Zeus y Anu están orgullosos!")


if __name__ == "__main__":
    main()