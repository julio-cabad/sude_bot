#!/usr/bin/env python3
"""
🔧⚔️ SETUP ENV - CONFIGURADOR RÁPIDO DE CREDENCIALES ⚔️🔧
Configuración ultra-rápida para la batalla
Created by TITANES DEL CÓDIGO - CONFIGURADORES SUPREMOS
"""

import os
from pathlib import Path

def check_env_file():
    """🔍 VERIFICA ARCHIVO .env"""
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ Archivo .env encontrado!")
        
        # Leer y mostrar credenciales (parcialmente)
        with open(env_file, 'r') as f:
            content = f.read()
            
        if 'BINANCE_API_KEY' in content and 'BINANCE_API_SECRET' in content:
            print("✅ Credenciales de Binance encontradas en .env")
            
            # Cargar en variables de entorno
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
            
            # Verificar que se cargaron
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')
            
            if api_key and api_secret:
                print(f"✅ API Key cargada: {api_key[:8]}...{api_key[-4:]}")
                print(f"✅ Secret cargada: ***...{api_secret[-4:]}")
                return True
            else:
                print("❌ Error cargando credenciales desde .env")
                return False
        else:
            print("❌ Credenciales de Binance no encontradas en .env")
            return False
    else:
        print("❌ Archivo .env no encontrado")
        return False

def create_env_file():
    """🔧 CREA ARCHIVO .env RÁPIDAMENTE"""
    
    print("\n🔧 CREANDO ARCHIVO .env...")
    print("💡 Necesitas tus credenciales de Binance API")
    
    api_key = input("🔑 Ingresa tu BINANCE_API_KEY: ").strip()
    if not api_key:
        print("❌ API Key no puede estar vacía")
        return False
    
    api_secret = input("🔐 Ingresa tu BINANCE_API_SECRET: ").strip()
    if not api_secret:
        print("❌ API Secret no puede estar vacía")
        return False
    
    # Crear archivo .env
    env_content = f"""# Credenciales de Binance API
BINANCE_API_KEY={api_key}
BINANCE_API_SECRET={api_secret}
"""
    
    with open(".env", 'w') as f:
        f.write(env_content)
    
    print("✅ Archivo .env creado exitosamente!")
    print(f"✅ API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"✅ Secret: ***...{api_secret[-4:]}")
    
    return True

def main():
    """🔥 FUNCIÓN PRINCIPAL 🔥"""
    
    print("🔧⚔️🏛️ SETUP ENV - CONFIGURADOR RÁPIDO 🏛️⚔️🔧")
    print("🎯 Preparando credenciales para la batalla")
    print("=" * 60)
    
    # Verificar si ya existe
    if check_env_file():
        print("\n🏆 ¡CREDENCIALES LISTAS!")
        print("🚀 Puedes ejecutar: python backtesting/quick_test.py")
        return
    
    # Si no existe, crear
    print("\n💡 Vamos a configurar tus credenciales...")
    
    if create_env_file():
        print("\n🏆 ¡CONFIGURACIÓN COMPLETADA!")
        print("🚀 Ahora ejecuta: python backtesting/quick_test.py")
    else:
        print("\n❌ Error en la configuración")
        print("💡 Intenta nuevamente")

if __name__ == "__main__":
    main()