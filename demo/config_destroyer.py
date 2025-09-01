#!/usr/bin/env python3
"""
⚙️⚔️ CONFIG DESTROYER - CONFIGURADOR ÉPICO ⚔️⚙️
Configuración rápida del destructor de mercados
Created by TITANES DEL CÓDIGO - MAESTROS DE LA CONFIGURACIÓN
"""

import json
import os
from typing import Dict, List


class EpicDestroyerConfig:
    """⚙️ CONFIGURADOR ÉPICO DEL DESTRUCTOR ⚙️"""
    
    def __init__(self):
        self.config_file = "destroyer_config.json"
        self.default_config = {
            "timeframe": "1m",
            "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
            "max_workers": 3,
            "enable_sound": True,
            "enable_alerts": True,
            "simulation": {
                "zone_probability": 0.15,
                "min_zone_interval_seconds": 30
            },
            "trading_signals": {
                "BTCUSDT": {
                    "risk_reward_min": 2.0,
                    "stop_loss_pct": 0.5,
                    "take_profit_multiplier": 3.0
                },
                "ETHUSDT": {
                    "risk_reward_min": 2.5,
                    "stop_loss_pct": 0.8,
                    "take_profit_multiplier": 3.5
                },
                "ADAUSDT": {
                    "risk_reward_min": 3.0,
                    "stop_loss_pct": 1.2,
                    "take_profit_multiplier": 4.0
                }
            },
            "base_prices": {
                "BTCUSDT": 43000.0,
                "ETHUSDT": 2600.0,
                "ADAUSDT": 0.45
            }
        }
    
    def load_config(self) -> Dict:
        """📥 CARGA CONFIGURACIÓN"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                print(f"✅ Configuración cargada desde {self.config_file}")
                return config
            else:
                print("📋 Usando configuración por defecto")
                return self.default_config.copy()
        except Exception as e:
            print(f"❌ Error cargando configuración: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict):
        """💾 GUARDA CONFIGURACIÓN"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✅ Configuración guardada en {self.config_file}")
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
    
    def interactive_config(self):
        """🎮 CONFIGURACIÓN INTERACTIVA"""
        
        print("⚙️⚔️🏛️ CONFIGURADOR ÉPICO DEL DESTRUCTOR 🏛️⚔️⚙️")
        print("🎯 Configura tu arma asesina de mercados\n")
        
        config = self.load_config()
        
        # Configurar timeframe
        print("⏰ TIMEFRAME:")
        print("1. 1m (recomendado para testing)")
        print("2. 3m")
        print("3. 5m")
        print("4. 15m")
        print("5. 30m")
        print("6. 1h")
        
        tf_choice = input(f"Selecciona timeframe (actual: {config['timeframe']}): ").strip()
        timeframes = {"1": "1m", "2": "3m", "3": "5m", "4": "15m", "5": "30m", "6": "1h"}
        if tf_choice in timeframes:
            config["timeframe"] = timeframes[tf_choice]
            print(f"✅ Timeframe configurado: {config['timeframe']}")
        
        # Configurar símbolos
        print(f"\n📊 SÍMBOLOS ACTUALES: {', '.join(config['symbols'])}")
        change_symbols = input("¿Cambiar símbolos? (y/n): ").strip().lower()
        
        if change_symbols == 'y':
            print("💡 Símbolos disponibles: BTCUSDT, ETHUSDT, ADAUSDT, SOLUSDT, DOTUSDT, LINKUSDT")
            new_symbols = input("Ingresa símbolos separados por coma: ").strip()
            if new_symbols:
                config["symbols"] = [s.strip().upper() for s in new_symbols.split(",")]
                print(f"✅ Símbolos configurados: {', '.join(config['symbols'])}")
        
        # Configurar workers
        print(f"\n⚡ WORKERS ACTUALES: {config['max_workers']}")
        new_workers = input("Nuevo número de workers (recomendado: igual al número de símbolos): ").strip()
        if new_workers.isdigit():
            config["max_workers"] = int(new_workers)
            print(f"✅ Workers configurados: {config['max_workers']}")
        
        # Configurar sonido
        print(f"\n🔊 SONIDO ACTUAL: {'HABILITADO' if config['enable_sound'] else 'DESHABILITADO'}")
        sound_choice = input("¿Habilitar sonido? (y/n): ").strip().lower()
        if sound_choice in ['y', 'n']:
            config["enable_sound"] = sound_choice == 'y'
            print(f"✅ Sonido: {'HABILITADO' if config['enable_sound'] else 'DESHABILITADO'}")
        
        # Configurar probabilidad de simulación
        print(f"\n🎭 PROBABILIDAD DE ZONA (simulación): {config['simulation']['zone_probability']}")
        new_prob = input("Nueva probabilidad (0.1 = 10%, 0.2 = 20%): ").strip()
        try:
            prob = float(new_prob)
            if 0 < prob <= 1:
                config["simulation"]["zone_probability"] = prob
                print(f"✅ Probabilidad configurada: {prob}")
        except:
            pass
        
        # Configurar precios base
        print(f"\n💰 PRECIOS BASE (para simulación realista):")
        for symbol in config["symbols"]:
            if symbol in config["base_prices"]:
                current_price = config["base_prices"][symbol]
                print(f"   {symbol}: ${current_price}")
                new_price = input(f"Nuevo precio para {symbol} (actual: ${current_price}): ").strip()
                try:
                    price = float(new_price)
                    if price > 0:
                        config["base_prices"][symbol] = price
                        print(f"✅ {symbol}: ${price}")
                except:
                    pass
        
        # Guardar configuración
        self.save_config(config)
        
        print("\n🏆 CONFIGURACIÓN COMPLETADA!")
        print("🎯 Tu arma asesina de mercados está lista!")
        
        return config
    
    def display_config(self, config: Dict):
        """📋 MUESTRA CONFIGURACIÓN ACTUAL"""
        
        print("\n⚙️ CONFIGURACIÓN ACTUAL:")
        print("═" * 50)
        print(f"⏰ Timeframe: {config['timeframe']}")
        print(f"📊 Símbolos: {', '.join(config['symbols'])}")
        print(f"⚡ Workers: {config['max_workers']}")
        print(f"🔊 Sonido: {'HABILITADO' if config['enable_sound'] else 'DESHABILITADO'}")
        print(f"🎭 Prob. Zona: {config['simulation']['zone_probability']}")
        
        print(f"\n💰 Precios Base:")
        for symbol, price in config["base_prices"].items():
            if symbol in config["symbols"]:
                print(f"   {symbol}: ${price}")
        
        print(f"\n🎯 Configuración Trading:")
        for symbol in config["symbols"]:
            if symbol in config["trading_signals"]:
                ts = config["trading_signals"][symbol]
                print(f"   {symbol}: RR≥{ts['risk_reward_min']}, SL={ts['stop_loss_pct']}%, TP={ts['take_profit_multiplier']}x")
        
        print("═" * 50)


def main():
    """🔥 FUNCIÓN PRINCIPAL DE CONFIGURACIÓN 🔥"""
    
    configurator = EpicDestroyerConfig()
    
    print("⚙️⚔️🏛️ EPIC DESTROYER CONFIGURATOR 🏛️⚔️⚙️")
    print("🎯 Configura tu arma asesina de mercados\n")
    
    print("1. Configuración interactiva")
    print("2. Ver configuración actual")
    print("3. Usar configuración por defecto")
    
    choice = input("\nSelecciona opción: ").strip()
    
    if choice == "1":
        config = configurator.interactive_config()
        configurator.display_config(config)
    
    elif choice == "2":
        config = configurator.load_config()
        configurator.display_config(config)
    
    elif choice == "3":
        configurator.save_config(configurator.default_config)
        print("✅ Configuración por defecto guardada")
        configurator.display_config(configurator.default_config)
    
    else:
        print("❌ Opción inválida")
    
    print("\n🏆 CONFIGURACIÓN COMPLETADA!")


if __name__ == "__main__":
    main()