#!/usr/bin/env python3
"""
Hello World - Prueba del proyecto Python con Binance
"""

import pandas as pd
import pandas_ta as ta
from dotenv import load_dotenv
import os
from binance.cm_futures import CMFutures

def main():
    print("🚀 Hello World - Proyecto Python con Binance!")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar pandas
    print(f"✅ Pandas version: {pd.__version__}")
    
    # Crear un DataFrame de ejemplo
    data = {
        'precio': [100, 101, 102, 99, 98, 103, 105],
        'volumen': [1000, 1200, 800, 1500, 900, 1100, 1300]
    }
    df = pd.DataFrame(data)
    print(f"✅ DataFrame creado:\n{df}")
    
    # Probar pandas_ta con un indicador simple
    df['sma_3'] = ta.sma(df['precio'], length=3)
    print(f"✅ SMA calculado:\n{df[['precio', 'sma_3']]}")
    
    # Verificar variables de entorno
    api_key = os.getenv('BINANCE_API_KEY', 'No configurada')
    print(f"✅ API Key status: {'Configurada' if api_key != 'No configurada' else 'No configurada'}")
    
    # Probar conexión básica a Binance (sin autenticación)
    try:
        client = CMFutures()
        server_time = client.time()
        print(f"✅ Conexión a Binance exitosa. Server time: {server_time}")
    except Exception as e:
        print(f"⚠️  Error de conexión a Binance: {e}")
    
    print("=" * 50)
    print("🎉 ¡Todas las librerías funcionan correctamente!")

if __name__ == "__main__":
    main()