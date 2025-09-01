#!/usr/bin/env python3
"""
🧪⚔️ TEST REAL DETECTION - PRUEBA DE DETECCIÓN REAL ⚔️🧪
Prueba rápida del sistema con datos reales de Binance
Created by TITANES DEL CÓDIGO - TESTERS SUPREMOS
"""

import os
import sys
import time
from datetime import datetime

# Añadir path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_credentials():
    """🔑 PRUEBA CREDENCIALES DE BINANCE"""
    
    print("🔑 Verificando credenciales de Binance...")
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Credenciales no encontradas")
        print("💡 Verifica tu archivo .env o variables de entorno")
        return False
    
    print(f"✅ API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"✅ Secret: ***...{api_secret[-4:]}")
    
    return True


def test_binance_connection():
    """📡 PRUEBA CONEXIÓN CON BINANCE"""
    
    print("\n📡 Probando conexión con Binance...")
    
    try:
        from bnb.binance import RobotBinance
        
        robot = RobotBinance("BTCUSDT", "1h")
        data = robot.candlestick(limit=5)
        
        if data.empty:
            raise Exception("No data received")
        
        current_price = data['close'].iloc[-1]
        
        print(f"✅ Conexión exitosa!")
        print(f"📊 Datos obtenidos: {len(data)} velas")
        print(f"💰 Precio actual BTC: ${current_price:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


def test_zone_detection():
    """🏛️ PRUEBA DETECCIÓN DE ZONAS"""
    
    print("\n🏛️ Probando detección de zonas...")
    
    try:
        from demo.implacable_zones_detector import ImplacableZonesDetector
        
        print("🔥 Creando detector para BTCUSDT...")
        detector = ImplacableZonesDetector("BTCUSDT", "1h")
        
        print("⚔️ Ejecutando detección...")
        start_time = time.time()
        
        success = detector.run_implacable_detection()
        
        detection_time = time.time() - start_time
        
        if not success:
            print("❌ Detección fallida")
            return False
        
        # Obtener resultados
        zones_data = detector.export_implacable_json()
        
        supply_count = len(zones_data.get('supply_zones', []))
        demand_count = len(zones_data.get('demand_zones', []))
        total_zones = supply_count + demand_count
        
        print(f"✅ Detección exitosa!")
        print(f"⏱️  Tiempo: {detection_time:.2f}s")
        print(f"🔺 Zonas Supply: {supply_count}")
        print(f"🔻 Zonas Demand: {demand_count}")
        print(f"📊 Total zonas: {total_zones}")
        
        if total_zones > 0:
            print(f"\n🎯 PRIMERAS ZONAS DETECTADAS:")
            
            # Mostrar primera zona de supply
            if zones_data.get('supply_zones'):
                zone = zones_data['supply_zones'][0]
                print(f"   🔺 Supply: ${zone['poi']:,.2f} ({zone['distance_percentage']})")
            
            # Mostrar primera zona de demand
            if zones_data.get('demand_zones'):
                zone = zones_data['demand_zones'][0]
                print(f"   🔻 Demand: ${zone['poi']:,.2f} ({zone['distance_percentage']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en detección: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_symbol_monitor():
    """⚡ PRUEBA MONITOR MULTI-SÍMBOLO"""
    
    print("\n⚡ Probando monitor multi-símbolo...")
    
    try:
        from core.multi_symbol_monitor import MultiSymbolMonitor
        
        # Crear monitor con timeframe corto para prueba rápida
        monitor = MultiSymbolMonitor(
            timeframe="1h",  # Usar 1h para prueba más rápida
            enable_alerts=False,
            enable_sound=False,
            max_workers=1
        )
        
        # Añadir solo BTC para prueba
        monitor.add_symbol("BTCUSDT")
        
        print("🚀 Iniciando monitor de prueba...")
        
        if monitor.start_monitoring():
            print("✅ Monitor iniciado!")
            
            # Correr por 10 segundos
            print("⏰ Ejecutando por 10 segundos...")
            time.sleep(10)
            
            # Obtener status
            status = monitor.get_status()
            
            print("🛑 Deteniendo monitor...")
            monitor.stop_monitoring()
            
            print(f"📊 Resultados de prueba:")
            print(f"   Estado: {status['monitor_status']['state']}")
            print(f"   Símbolos activos: {status['active_symbols']}")
            
            if status['current_session']:
                session = status['current_session']
                print(f"   Checks realizados: {session['total_checks']}")
                print(f"   Zonas detectadas: {session['zones_detected']}")
            
            return True
        else:
            print("❌ Error iniciando monitor")
            return False
        
    except Exception as e:
        print(f"❌ Error en monitor: {e}")
        return False


def main():
    """🔥 FUNCIÓN PRINCIPAL DE PRUEBA 🔥"""
    
    print("🧪⚔️🏛️ TEST DE DETECCIÓN REAL 🏛️⚔️🧪")
    print("🎯 Verificando que todo funcione con datos reales")
    print("=" * 60)
    
    tests = [
        ("Credenciales", test_credentials),
        ("Conexión Binance", test_binance_connection),
        ("Detección de Zonas", test_zone_detection),
        ("Monitor Multi-Símbolo", test_multi_symbol_monitor)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE PRUEBAS:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 RESULTADO: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("🏆 ¡TODAS LAS PRUEBAS PASARON!")
        print("🔥 Tu arma asesina de mercados está lista!")
        print("🚀 Ejecuta: python backtesting/run_market_destroyer.py")
    else:
        print("⚠️ Algunas pruebas fallaron")
        print("💡 Revisa la configuración y credenciales")
    
    print("=" * 60)


if __name__ == "__main__":
    main()