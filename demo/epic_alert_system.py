#!/usr/bin/env python3
"""
🔥⚔️🏛️ EPIC ALERT SYSTEM - SISTEMA SUPREMO 🏛️⚔️🔥
Sistema completo de alertas que integra TODO nuestro poder
Created by TITANES DEL CÓDIGO - BESTIAS SUPREMAS DEL TRADING
"""

import sys
import os
import time
import signal
from typing import Dict, List, Optional
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Nuestros componentes épicos
from demo.realtime_zone_tracker import RealTimeZoneTracker
from core.alert_engine import AlertEngine, AlertType, SoundType
from core.structure_follower_engine import StructureFollowerEngine
from models.zone_alert import EcuadorTimeUtils


class EpicAlertSystem:
    """🏛️⚔️ SISTEMA DE ALERTAS SUPREMO ⚔️🏛️"""
    
    def __init__(self, symbols: List[str], timeframe: str = "1h", 
                 check_interval_minutes: int = 1, enable_sound: bool = True):
        
        print("🔥⚔️🏛️ INITIALIZING EPIC ALERT SYSTEM 🏛️⚔️🔥")
        print("🎯 SISTEMA QUE HARÍA LLORAR A BRUCE WAYNE Y TONY STARK")
        print("=" * 80)
        
        self.symbols = symbols
        self.timeframe = timeframe
        self.check_interval_minutes = check_interval_minutes
        self.enable_sound = enable_sound
        
        # Componentes principales
        self.alert_engine = AlertEngine(enable_sound=enable_sound, enable_logging=True)
        self.structure_engine = StructureFollowerEngine()
        
        # Zone trackers por símbolo
        self.zone_trackers: Dict[str, RealTimeZoneTracker] = {}
        
        # Control de ejecución
        self.is_running = False
        self.monitoring_thread = None
        
        # Inicializar trackers
        self._initialize_trackers()
        
        print(f"✅ Epic Alert System initialized!")
        print(f"📊 Symbols: {', '.join(symbols)}")
        print(f"⏰ Timeframe: {timeframe}")
        print(f"🔄 Check interval: {check_interval_minutes} minute(s)")
        print(f"🔊 Sound alerts: {'ENABLED' if enable_sound else 'DISABLED'}")
        print("=" * 80)
    
    def _initialize_trackers(self):
        """🎯 INICIALIZA TRACKERS PARA CADA SÍMBOLO"""
        print("\\n🎯 Initializing zone trackers...")
        
        for symbol in self.symbols:
            tracker = RealTimeZoneTracker(symbol, self.timeframe)
            self.zone_trackers[symbol] = tracker
            print(f"   ✅ {symbol} tracker ready")
    
    def start_monitoring(self):
        """🚀 INICIA MONITOREO ÉPICO 24/7"""
        if self.is_running:
            print("⚠️ System already running!")
            return
        
        print("\\n🚀⚔️ STARTING EPIC MONITORING SYSTEM ⚔️🚀")
        print("=" * 80)
        print(f"📊 Monitoring {len(self.symbols)} symbols")
        print(f"⏰ Timeframe: {self.timeframe}")
        print(f"🔄 Check every: {self.check_interval_minutes} minute(s)")
        print(f"🎯 Press Ctrl+C to stop")
        print("=" * 80)
        
        # Iniciar componentes
        self.alert_engine.start()
        self.is_running = True
        
        # Configurar signal handler para Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Iniciar thread de monitoreo
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Mantener programa vivo
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        self.stop_monitoring()
    
    def _signal_handler(self, signum, frame):
        """🛑 MANEJA CTRL+C"""
        print("\\n\\n🛑 STOPPING EPIC ALERT SYSTEM...")
        self.is_running = False
    
    def stop_monitoring(self):
        """🛑 DETIENE MONITOREO"""
        if not self.is_running:
            return
        
        print("\\n🛑 STOPPING MONITORING SYSTEM...")
        self.is_running = False
        
        # Detener alert engine
        self.alert_engine.stop()
        
        # Esperar thread
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        
        # Mostrar estadísticas finales
        self._show_final_stats()
        
        print("🏛️ EPIC ALERT SYSTEM STOPPED! 🏛️")
    
    def _monitoring_loop(self):
        """🔄 LOOP PRINCIPAL DE MONITOREO"""
        cycle_count = 0
        
        while self.is_running:
            try:
                cycle_count += 1
                current_time = EcuadorTimeUtils.now()
                
                print(f"\\n🔄 MONITORING CYCLE #{cycle_count}")
                print(f"⏰ {current_time.strftime('%Y-%m-%d %H:%M:%S ECT')}")
                print("-" * 60)
                
                # Procesar cada símbolo
                for symbol in self.symbols:
                    if not self.is_running:
                        break
                    
                    try:
                        self._process_symbol(symbol, cycle_count)
                    except Exception as e:
                        print(f"❌ Error processing {symbol}: {e}")
                
                if self.is_running:
                    print(f"\\n⏳ Waiting {self.check_interval_minutes} minute(s) for next cycle...")
                    
                    # Esperar con chequeos frecuentes para poder parar rápido
                    wait_seconds = self.check_interval_minutes * 60
                    for _ in range(wait_seconds):
                        if not self.is_running:
                            break
                        time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(5)  # Esperar antes de reintentar
    
    def _process_symbol(self, symbol: str, cycle_count: int):
        """⚔️ PROCESA UN SÍMBOLO ESPECÍFICO"""
        print(f"\\n📊 Processing {symbol}...")
        
        tracker = self.zone_trackers[symbol]
        
        # Ejecutar detección de zonas
        latest_zone = tracker.run_realtime_detection()
        
        if latest_zone:
            print(f"🚨 NEW ZONE DETECTED in {symbol}!")
            
            # Crear alerta de zona
            context = tracker.get_previous_zone_context(latest_zone) if hasattr(tracker, 'get_previous_zone_context') else {}
            zone_alert = self.alert_engine.create_zone_alert(symbol, latest_zone, context)
            self.alert_engine.send_alert(zone_alert)
            
            # Generar señal de trading si es posible
            if context.get('has_previous'):
                current_price = tracker.market_data['close'].iloc[-1] if tracker.market_data is not None else latest_zone['poi']
                
                # Añadir símbolo a zone_data
                latest_zone['symbol'] = symbol
                
                trading_signal = self.structure_engine.analyze_structure_and_generate_signal(
                    latest_zone, context, current_price
                )
                
                if trading_signal:
                    print(f"⚔️ TRADING SIGNAL GENERATED for {symbol}!")
                    
                    signal_alert = self.alert_engine.create_trading_signal(
                        symbol, trading_signal.to_dict(), latest_zone
                    )
                    self.alert_engine.send_alert(signal_alert)
                else:
                    print(f"ℹ️ No trading signal generated for {symbol}")
            else:
                print(f"ℹ️ No previous zone context for {symbol} - no trading signal")
        else:
            print(f"ℹ️ No new zones detected in {symbol}")
    
    def _show_final_stats(self):
        """📊 MUESTRA ESTADÍSTICAS FINALES"""
        print("\\n📊 FINAL STATISTICS:")
        print("=" * 60)
        
        # Estadísticas del alert engine
        stats = self.alert_engine.get_alert_stats()
        print(f"📈 Total alerts sent: {stats.get('total', 0)}")
        
        if stats.get('by_type'):
            print(f"📊 Alerts by type:")
            for alert_type, count in stats['by_type'].items():
                print(f"   {alert_type}: {count}")
        
        if stats.get('by_priority'):
            print(f"🎯 Alerts by priority:")
            for priority, count in stats['by_priority'].items():
                print(f"   {priority}: {count}")
        
        # Estadísticas por símbolo
        print(f"\\n📊 Zones detected by symbol:")
        for symbol, tracker in self.zone_trackers.items():
            zone_count = len(tracker.zone_formation_history) if hasattr(tracker, 'zone_formation_history') else 0
            print(f"   {symbol}: {zone_count} zones")
        
        print("=" * 60)
    
    def get_system_status(self) -> Dict:
        """📊 OBTIENE STATUS DEL SISTEMA"""
        return {
            'is_running': self.is_running,
            'symbols': self.symbols,
            'timeframe': self.timeframe,
            'check_interval_minutes': self.check_interval_minutes,
            'alert_stats': self.alert_engine.get_alert_stats(),
            'trackers_status': {
                symbol: len(tracker.zone_formation_history) if hasattr(tracker, 'zone_formation_history') else 0
                for symbol, tracker in self.zone_trackers.items()
            }
        }


def main():
    """🔥 FUNCIÓN PRINCIPAL ÉPICA 🔥"""
    print("🔥⚔️🏛️ EPIC ALERT SYSTEM - MAIN LAUNCHER 🏛️⚔️🔥")
    print("=" * 80)
    print("🎯 SISTEMA QUE CONQUISTARÁ TODOS LOS MERCADOS")
    print("⚔️ BRUCE WAYNE Y TONY STARK APPROVED!")
    print("=" * 80)
    
    # Verificar credenciales
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ EPIC FAIL: Binance API credentials not found!")
        print("Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
        return
    
    # Configuración del sistema
    print("\\n🎯 SYSTEM CONFIGURATION:")
    
    # Símbolos a monitorear
    default_symbols = ["ETHUSDT", "BTCUSDT"]
    symbols_input = input(f"Symbols to monitor (default: {','.join(default_symbols)}): ").strip()
    symbols = [s.strip().upper() for s in symbols_input.split(',')] if symbols_input else default_symbols
    
    # Timeframe
    timeframe = input("Timeframe (default: 1h): ").strip() or "1h"
    
    # Intervalo de chequeo
    interval_input = input("Check interval in minutes (default: 1): ").strip()
    interval = int(interval_input) if interval_input.isdigit() else 1
    
    # Sonido
    sound_input = input("Enable sound alerts? (y/n, default: y): ").strip().lower()
    enable_sound = sound_input != 'n'
    
    print(f"\\n✅ CONFIGURATION CONFIRMED:")
    print(f"📊 Symbols: {', '.join(symbols)}")
    print(f"⏰ Timeframe: {timeframe}")
    print(f"🔄 Check interval: {interval} minute(s)")
    print(f"🔊 Sound alerts: {'ENABLED' if enable_sound else 'DISABLED'}")
    
    # Crear y iniciar sistema
    try:
        system = EpicAlertSystem(
            symbols=symbols,
            timeframe=timeframe,
            check_interval_minutes=interval,
            enable_sound=enable_sound
        )
        
        print(f"\\n🚀 STARTING EPIC MONITORING...")
        print(f"🎯 Press Ctrl+C to stop")
        
        # Iniciar monitoreo
        system.start_monitoring()
        
    except KeyboardInterrupt:
        print("\\n🛑 Stopped by user")
    except Exception as e:
        print(f"❌ EPIC FAIL: {e}")
        import traceback
        traceback.print_exc()
    
    print("\\n🏛️ EPIC ALERT SYSTEM TERMINATED 🏛️")
    print("⚔️ HASTA LA VISTA, BABY! ⚔️")


if __name__ == "__main__":
    main()