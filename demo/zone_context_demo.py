#!/usr/bin/env python3
"""
🔥⚔️ ZONE CONTEXT DEMO - PODER DEL CONOCIMIENTO ⚔️🔥
Demo que muestra cómo funciona el análisis de zona anterior
Created by FEROZ GUERRERO DEL CÓDIGO - KNOWLEDGE IS POWER
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from demo.realtime_zone_tracker import RealTimeZoneTracker

def simulate_multiple_zone_detection():
    """
    🎯 SIMULA DETECCIÓN DE MÚLTIPLES ZONAS CON CONTEXTO
    """
    print("🔥⚔️🏛️ ZONE CONTEXT DEMO - KNOWLEDGE IS POWER 🏛️⚔️🔥")
    print("=" * 80)
    print("🎯 SIMULANDO DETECCIÓN DE MÚLTIPLES ZONAS CON CONTEXTO ANTERIOR")
    print("⚔️ DEMOSTRANDO EL PODER DEL CONOCIMIENTO TÁCTICO")
    print("=" * 80)
    
    # Crear tracker
    tracker = RealTimeZoneTracker("BTCUSDT", "1h")
    
    # Simular zonas detectadas secuencialmente
    print("\\n🎬 SIMULACIÓN: Detectando zonas en secuencia...")
    
    # ZONA 1: DEMAND (Primera zona)
    zone1 = {
        'type': 'DEMAND',
        'poi': 65000.0,
        'top': 65300.0,
        'bottom': 64700.0,
        'swing_price': 64700.0,
        'swing_time': datetime.now() - timedelta(hours=48),
        'swing_strength': 8,
        'formation_time': datetime.now() - timedelta(hours=47),
        'distance_pct': -2.5,
        'atr_used': 600.0,
        'zone_height': 600.0,
        'formation_candles_ago': 48
    }
    
    # ZONA 2: SUPPLY (Después de la demand)
    zone2 = {
        'type': 'SUPPLY',
        'poi': 67500.0,
        'top': 67800.0,
        'bottom': 67200.0,
        'swing_price': 67800.0,
        'swing_time': datetime.now() - timedelta(hours=24),
        'swing_strength': 9,
        'formation_time': datetime.now() - timedelta(hours=23),
        'distance_pct': +1.2,
        'atr_used': 600.0,
        'zone_height': 600.0,
        'formation_candles_ago': 24
    }
    
    # ZONA 3: DEMAND (Nueva zona después de supply)
    zone3 = {
        'type': 'DEMAND',
        'poi': 66200.0,
        'top': 66500.0,
        'bottom': 65900.0,
        'swing_price': 65900.0,
        'swing_time': datetime.now() - timedelta(hours=6),
        'swing_strength': 10,
        'formation_time': datetime.now() - timedelta(hours=5),
        'distance_pct': -0.8,
        'atr_used': 600.0,
        'zone_height': 600.0,
        'formation_candles_ago': 6
    }
    
    # Simular datos de mercado
    import pandas as pd
    dates = pd.date_range(start=datetime.now() - timedelta(hours=100), 
                         end=datetime.now(), freq='H')
    tracker.market_data = pd.DataFrame({
        'close': [66700.0] * len(dates),
        'high': [67000.0] * len(dates),
        'low': [66400.0] * len(dates)
    }, index=dates)
    
    # DEMOSTRACIÓN 1: Primera zona (sin contexto anterior)
    print("\\n" + "="*80)
    print("🎬 ESCENARIO 1: PRIMERA ZONA DETECTADA")
    print("="*80)
    
    tracker.zone_formation_history = [zone1]
    tracker.display_latest_zone_alert(zone1)
    
    # DEMOSTRACIÓN 2: Segunda zona (con contexto de demand anterior)
    print("\\n" + "="*80)
    print("🎬 ESCENARIO 2: SUPPLY DESPUÉS DE DEMAND - ESTRUCTURA ALCISTA")
    print("="*80)
    
    tracker.zone_formation_history = [zone1, zone2]
    tracker.display_latest_zone_alert(zone2)
    
    # DEMOSTRACIÓN 3: Tercera zona (con contexto de supply anterior)
    print("\\n" + "="*80)
    print("🎬 ESCENARIO 3: DEMAND DESPUÉS DE SUPPLY - POSIBLE REVERSIÓN")
    print("="*80)
    
    tracker.zone_formation_history = [zone1, zone2, zone3]
    tracker.display_latest_zone_alert(zone3)
    
    # DEMOSTRACIÓN 4: Análisis de estructura completa
    print("\\n" + "="*80)
    print("🎬 ANÁLISIS FINAL: ESTRUCTURA COMPLETA DEL MERCADO")
    print("="*80)
    
    print("\\n🧠 RESUMEN DE CONOCIMIENTO TÁCTICO:")
    print("-" * 60)
    print("📊 SECUENCIA DE ZONAS DETECTADAS:")
    print("   1️⃣ DEMAND at $65,000 (48h atrás) - Soporte inicial")
    print("   2️⃣ SUPPLY at $67,500 (24h atrás) - Resistencia alcista (+$2,500)")
    print("   3️⃣ DEMAND at $66,200 (6h atrás) - Nuevo soporte (+$1,200 desde inicial)")
    
    print("\\n⚔️ INTERPRETACIÓN ESTRATÉGICA:")
    print("   🔺 Estructura ALCISTA confirmada (Higher Highs & Higher Lows)")
    print("   📈 Rango de trading: $2,500 entre zonas extremas")
    print("   🎯 Zona actual: Soporte más alto - Fortaleza alcista")
    print("   ⚖️ Ratio Risk/Reward favorable para posiciones largas")
    
    print("\\n🏛️ VENTAJA TÁCTICA SUPREMA:")
    print("   💡 Conocimiento de zona anterior = Contexto completo")
    print("   🎯 Estructura de mercado = Dirección probable")
    print("   ⚔️ Niveles clave = Puntos de entrada/salida precisos")
    print("   🔥 Análisis completo = Decisiones informadas")
    
    print("\\n🏆 DEMO COMPLETO - EL CONOCIMIENTO ES PODER! 🏆")


if __name__ == "__main__":
    simulate_multiple_zone_detection()