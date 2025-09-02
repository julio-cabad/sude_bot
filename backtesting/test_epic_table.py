#!/usr/bin/env python3
"""
🏆⚔️ TEST TABLA ÉPICA DE ZONAS ⚔️🏆
Prueba la nueva tabla suprema espartana
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.implacable_zones_detector import ImplacableZonesDetector


def test_epic_table():
    """🔥 PRUEBA LA TABLA ÉPICA 🔥"""
    
    print("🏆⚔️🏛️ TESTING EPIC ZONES TABLE 🏛️⚔️🏆")
    print("=" * 70)
    
    # Símbolos para probar
    symbols = ["ADAUSDT", "BTCUSDT", "ETHUSDT"]
    
    for symbol in symbols:
        print(f"\n🎯 TESTING {symbol}...")
        
        try:
            # Crear detector
            detector = ImplacableZonesDetector(symbol=symbol, timeframe="1h")
            
            # Ejecutar detección completa
            success = detector.run_implacable_detection()
            
            if success:
                print(f"✅ {symbol}: Detección exitosa!")
            else:
                print(f"❌ {symbol}: Error en detección")
                
        except Exception as e:
            print(f"❌ Error con {symbol}: {e}")
        
        print("-" * 50)
    
    print("\n🏆 EPIC TABLE TEST COMPLETE! 🏆")


if __name__ == "__main__":
    test_epic_table()