#!/usr/bin/env python3
"""
🔥⚔️ RUN MARKET DESTROYER - EJECUTOR SUPREMO ⚔️🔥
Script principal para ejecutar el destructor de mercados
Created by TITANES DEL CÓDIGO - EJECUTORES SUPREMOS
"""

import os
import sys
import time
import signal
from datetime import datetime

# Añadir path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar el destructor épico
from demo.epic_market_destroyer import EpicMarketDestroyer


def display_epic_banner():
    """🎨 MUESTRA BANNER ÉPICO"""
    
    banner = """
🔥⚔️🏛️═══════════════════════════════════════════════════════════════🏛️⚔️🔥
                    EPIC MARKET DESTROYER v1.0
                   ARMA ASESINA DE MERCADOS
                 
              Creado por: TITANES DEL CÓDIGO
           Aprobado por: Ra, Odin, Zeus y Anu
           
    💀 PREPARANDO DESTRUCCIÓN ÉPICA DE MERCADOS 💀
    
    📊 Símbolos: BTC, ETH, ADA
    ⏰ Timeframe: 1 minuto
    🎯 Objetivo: Detectar zonas y generar señales épicas
    
🔥⚔️🏛️═══════════════════════════════════════════════════════════════🏛️⚔️🔥
    """
    
    print(banner)


def display_instructions():
    """📋 MUESTRA INSTRUCCIONES"""
    
    instructions = """
🎯 INSTRUCCIONES DE USO:

1. 🚀 El sistema monitoreará BTC, ETH y ADA en timeframe de 1 minuto
2. 🏛️ Cuando detecte una nueva zona, mostrará:
   - Tipo de zona (DEMAND/SUPPLY)
   - POI (Point of Interest)
   - Rango de la zona
   - Hora de formación (UTC-5)
   
3. ⚔️ Para cada zona generará señal de trading con:
   - Precio de entrada sugerido
   - Stop Loss calculado
   - Take Profit optimizado
   - Risk/Reward ratio
   - Nivel de confianza
   - Hora de entrada recomendada (UTC-5)
   
4. 💾 Las señales se guardan automáticamente en carpeta 'signals/'
5. 🛑 Presiona Ctrl+C para detener el sistema

🔥 SISTEMA CON DATOS REALES DE BINANCE 🔥
   ⚠️  IMPORTANTE: Usa datos reales de mercado para detección de zonas.

🔥 ¡Que comience la destrucción épica de mercados! 🔥
    """
    
    print(instructions)


def main():
    """🔥 FUNCIÓN PRINCIPAL SUPREMA 🔥"""
    
    # Banner épico
    display_epic_banner()
    
    # Verificar credenciales de Binance
    print("🔑 Verificando credenciales de Binance...")
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ ERROR: Credenciales de Binance no encontradas!")
        print("💡 Configura las variables de entorno:")
        print("   export BINANCE_API_KEY='tu_api_key'")
        print("   export BINANCE_API_SECRET='tu_api_secret'")
        print("\n🔧 O ejecuta el configurador:")
        print("   python setup_binance_credentials.py")
        return 1
    
    print("✅ Credenciales de Binance verificadas!")
    
    # Crear destructor con datos reales
    print("💀 Creando destructor épico con datos REALES de Binance...")
    destroyer = EpicMarketDestroyer()
    
    # Mostrar instrucciones
    display_instructions()
    
    # Esperar confirmación del usuario
    input("📋 Presiona ENTER para iniciar la destrucción épica de mercados...")
    
    try:
        print("\n🚀 INICIANDO SISTEMA...")
        
        # Iniciar destrucción
        if destroyer.start_destruction():
            
            print("✅ Sistema iniciado exitosamente!")
            print("🎯 Monitoreando mercados...")
            print("💡 Presiona Ctrl+C para detener\n")
            
            # Loop principal
            status_counter = 0
            
            while True:
                time.sleep(5)  # Check cada 5 segundos
                status_counter += 1
                
                # Mostrar status cada minuto (12 * 5 segundos = 60 segundos)
                if status_counter % 12 == 0:
                    status = destroyer.get_status()
                    
                    print(f"\n📊 STATUS ÉPICO:")
                    print(f"   ⏰ Duración: {status['session_duration']}")
                    print(f"   🏛️ Zonas detectadas: {status['zones_detected']}")
                    print(f"   🎯 Señales generadas: {status['signals_generated']}")
                    print(f"   📈 Estado: {status['monitor_status']['state']}")
                    print(f"   🔥 Datos: REALES de Binance")
                    print("   💀 Continuando destrucción...\n")
        
        else:
            print("❌ Error iniciando el sistema")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️ INTERRUPCIÓN DETECTADA")
        print("🛑 Iniciando shutdown graceful...")
    
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("🛑 Deteniendo sistema...")
    
    finally:
        # Detener destrucción
        print("🔄 Deteniendo destructor...")
        destroyer.stop_destruction()
        
        # Mostrar estadísticas finales
        final_status = destroyer.get_status()
        
        print("\n🏆 DESTRUCCIÓN COMPLETADA!")
        print("═" * 60)
        print("📊 ESTADÍSTICAS FINALES:")
        print(f"   ⏰ Duración total: {final_status['session_duration']}")
        print(f"   🏛️ Zonas detectadas: {final_status['zones_detected']}")
        print(f"   🎯 Señales generadas: {final_status['signals_generated']}")
        print(f"   🔥 Fuente de datos: Binance API (REAL)")
        print(f"   📁 Señales guardadas en: ./signals/")
        print("═" * 60)
        print("⚔️ Los mercados han sido conquistados!")
        print("🎯 Ra, Odin, Zeus y Anu están orgullosos!")
        print("🔥 ¡Hasta la próxima destrucción épica! 🔥")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)