#!/usr/bin/env python3
"""
🚀🎯 LAUNCH TACTICAL - LANZADOR TÁCTICO ⚔️🚀
Lanzador simple para el sistema táctico ordenado
Created by TITANES DEL CÓDIGO - LANZADORES TÁCTICOS
"""

import os
import sys
from pathlib import Path

# Añadir path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_env_file():
    """🔧 CARGA ARCHIVO .env"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        return True
    return False

def check_credentials():
    """🔑 VERIFICA CREDENCIALES"""
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Credenciales de Binance no encontradas")
        print("💡 Ejecuta: python backtesting/setup_env.py")
        return False
    
    print(f"✅ Credenciales verificadas: {api_key[:8]}...{api_key[-4:]}")
    return True

def main():
    """🚀 LANZADOR PRINCIPAL"""
    
    print("🚀🎯⚔️ TACTICAL LAUNCHER ⚔️🎯🚀")
    print("🎯 Lanzando sistema táctico ordenado...")
    print("=" * 50)
    
    # Cargar .env
    if load_env_file():
        print("✅ Archivo .env cargado")
    
    # Verificar credenciales
    if not check_credentials():
        return 1
    
    # Lanzar sistema táctico
    try:
        print("\n🎯 Iniciando Tactical Market Destroyer...")
        
        from backtesting.tactical_market_destroyer import TacticalMarketDestroyer
        
        destroyer = TacticalMarketDestroyer()
        
        if destroyer.start_tactical_destruction():
            print("\n🏆 SISTEMA TÁCTICO ACTIVO!")
            print("🎯 Modo: PRECISIÓN MÁXIMA")
            print("📊 Filtros: ACTIVADOS")
            print("🔔 Alertas: ESPACIADAS")
            print("💡 Presiona Ctrl+C para detener\n")
            
            # Mantener activo
            while True:
                import time
                time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema táctico...")
        destroyer.stop_tactical_destruction()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    print("\n🏆 MISIÓN TÁCTICA COMPLETADA!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)