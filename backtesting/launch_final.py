#!/usr/bin/env python3
"""
🏆🚀 LAUNCH FINAL - LANZADOR FINAL SUPREMO 🚀🏆
Lanzador definitivo del sistema perfeccionado
Created by TITANES DEL CÓDIGO - LANZADORES FINALES
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

def main():
    """🚀 LANZADOR FINAL"""
    
    print("🏆🚀⚔️ FINAL LAUNCHER ⚔️🚀🏆")
    print("🎯 Sistema definitivo con deduplicación absoluta")
    print("=" * 60)
    
    # Cargar .env
    if load_env_file():
        print("✅ Credenciales cargadas")
    
    # Verificar credenciales
    api_key = os.getenv('BINANCE_API_KEY')
    if not api_key:
        print("❌ Credenciales no encontradas")
        print("💡 Ejecuta: python backtesting/setup_env.py")
        return 1
    
    print(f"✅ API Key verificada: {api_key[:8]}...{api_key[-4:]}")
    
    # Lanzar sistema final
    try:
        print("\n🏆 Iniciando Final Market Destroyer...")
        
        from backtesting.final_market_destroyer import FinalMarketDestroyer
        
        destroyer = FinalMarketDestroyer()
        
        if destroyer.start_final_destruction():
            print("\n🏆 SISTEMA FINAL ACTIVO!")
            print("🎯 Características:")
            print("   ✅ Deduplicación absoluta")
            print("   ✅ Una alerta por zona única")
            print("   ✅ Un archivo por día")
            print("   ✅ Sin spam de alertas")
            print("   ✅ Máxima precisión")
            print("\n💡 Presiona Ctrl+C para detener\n")
            
            # Mantener activo
            while True:
                import time
                time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema final...")
        destroyer.stop_final_destruction()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    print("\n🏆 MISIÓN FINAL COMPLETADA!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)