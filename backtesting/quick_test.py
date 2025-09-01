#!/usr/bin/env python3
"""
🧪⚔️ QUICK TEST - PRUEBA RÁPIDA DEL SISTEMA ⚔️🧪
Verificación rápida de que todo funciona antes de la batalla
Created by TITANES DEL CÓDIGO - TESTERS SUPREMOS
"""

import os
import sys
from pathlib import Path

# Añadir path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CARGAR ARCHIVO .env SI EXISTE
def load_env_file():
    """🔧 CARGA ARCHIVO .env"""
    env_file = Path(".env")
    if env_file.exists():
        print("🔧 Cargando archivo .env...")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Archivo .env cargado!")
    else:
        print("⚠️ Archivo .env no encontrado")

# Cargar .env al inicio
load_env_file()

def test_credentials():
    """🔑 PRUEBA CREDENCIALES"""
    print("🔑 Verificando credenciales...")
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Credenciales no encontradas")
        return False
    
    print(f"✅ API Key: {api_key[:8]}...{api_key[-4:]}")
    return True

def test_imports():
    """📦 PRUEBA IMPORTS"""
    print("\n📦 Verificando imports...")
    
    try:
        from backtesting.implacable_zones_detector import ImplacableZonesDetector
        print("✅ ImplacableZonesDetector")
        
        from core.multi_symbol_monitor import MultiSymbolMonitor
        print("✅ MultiSymbolMonitor")
        
        from core.alert_engine import AlertEngine
        print("✅ AlertEngine")
        
        from backtesting.epic_market_destroyer import EpicMarketDestroyer
        print("✅ EpicMarketDestroyer")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en imports: {e}")
        return False

def test_binance_connection():
    """📡 PRUEBA CONEXIÓN BINANCE"""
    print("\n📡 Probando conexión con Binance...")
    
    try:
        from bnb.binance import RobotBinance
        
        robot = RobotBinance("BTCUSDT", "1m")
        data = robot.candlestick(limit=5)
        
        if data.empty:
            raise Exception("No data received")
        
        current_price = data['close'].iloc[-1]
        print(f"✅ Conexión exitosa! BTC: ${current_price:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_zone_detection():
    """🏛️ PRUEBA DETECCIÓN DE ZONAS"""
    print("\n🏛️ Probando detección de zonas...")
    
    try:
        from backtesting.implacable_zones_detector import ImplacableZonesDetector
        
        detector = ImplacableZonesDetector("BTCUSDT", "1m")
        
        # Solo probar fetch de datos
        success = detector.fetch_extended_data(limit=100)
        
        if success:
            print("✅ Detección de zonas funcional!")
            return True
        else:
            print("❌ Error en detección de zonas")
            return False
        
    except Exception as e:
        print(f"❌ Error en detección: {e}")
        return False

def main():
    """🔥 FUNCIÓN PRINCIPAL DE PRUEBA 🔥"""
    
    print("🧪⚔️🏛️ QUICK TEST - VERIFICACIÓN RÁPIDA 🏛️⚔️🧪")
    print("🎯 Verificando que tu arma destructora esté lista")
    print("=" * 60)
    
    tests = [
        ("Credenciales", test_credentials),
        ("Imports", test_imports),
        ("Conexión Binance", test_binance_connection),
        ("Detección de Zonas", test_zone_detection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'─'*20} {test_name} {'─'*20}")
        
        try:
            success = test_func()
            if success:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 RESULTADO: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("🏆 ¡TODAS LAS PRUEBAS PASARON!")
        print("🔥 Tu arma destructora está lista para la batalla!")
        print("🚀 Ejecuta: python backtesting/run_market_destroyer.py")
    else:
        print("⚠️ Algunas pruebas fallaron")
        print("💡 Revisa la configuración antes de continuar")
    
    print("=" * 60)

if __name__ == "__main__":
    main()