# Script para construir el instalador/ejecutable portable de Windows (.exe)
#
# Para ejecutar en una máquina Windows (o máquina virtual Windows):
# 1. Instalar Python 3.10+
# 2. Abrir PowerShell en la carpeta del proyecto y ejecutar:
#      pip install -r requirements.txt
#      pip install -r requirements-desktop.txt
#      pip install pyinstaller
# 3. Ejecutar este script:
#      python construir_exe_windows.py

import subprocess
import sys
import os

def construir():
    print("Iniciando empaquetado optimizado para Windows...")
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",                # Genera una carpeta ligera con el exe en vez de descomprimir un .exe gigante en RAM
        "--windowed",              # Oculta la consola negra de comandos
        "--name=HuntJob_Chile",
        "--icon=assets/icon.ico",  # Icono oficial (si existe)
        "--add-data=assets;assets",
        "--add-data=core;core",
        "--add-data=app.py;.",
        "--collect-all=streamlit",
        "--collect-all=webview",
        "desktop.py"
    ]

    print(f"Ejecutando comando: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n¡Empaquetado exitoso!")
        print("El programa ejecutable se encuentra en: dist\\HuntJob_Chile\\HuntJob_Chile.exe")
    else:
        print("\nError al construir el ejecutable.")

if __name__ == "__main__":
    construir()
