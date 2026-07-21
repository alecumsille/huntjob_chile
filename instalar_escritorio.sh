#!/bin/bash
# Instala HuntJob Chile como app de escritorio en Linux (probado en Linux
# Mint / base Ubuntu-Debian). Deja un lanzador en el menu de aplicaciones
# que abre la app en una ventana nativa (GTK/WebKit) en vez de una pestaña
# del navegador.
#
# pywebview necesita los bindings de GTK del sistema (python3-gi), que no
# se pueden instalar solo con pip - por eso el venv se crea/ajusta con
# --system-site-packages.

set -e
cd "$(dirname "$0")"
CARPETA_PROYECTO="$(pwd)"

echo "Verificando dependencias del sistema (GTK/WebKit)..."
if ! python3 -c "import gi" 2>/dev/null; then
    echo "Faltan bindings de GTK para Python. Instalando (pedira tu password de sudo)..."
    sudo apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1
fi

if [ ! -d venv ]; then
    echo "Creando entorno virtual con acceso a paquetes del sistema..."
    python3 -m venv --system-site-packages venv
elif ! grep -q "include-system-site-packages = true" venv/pyvenv.cfg; then
    echo "Habilitando acceso a paquetes del sistema en el venv existente..."
    sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' venv/pyvenv.cfg
fi

source venv/bin/activate
pip install -q -r requirements.txt
pip install -q -r requirements-desktop.txt

echo "Instalando lanzador en el menu de aplicaciones..."
mkdir -p "$HOME/.local/share/applications"
sed "s|RUTA_PROYECTO|$CARPETA_PROYECTO|g" huntjob-chile.desktop.template > "$HOME/.local/share/applications/huntjob-chile.desktop"
chmod +x "$HOME/.local/share/applications/huntjob-chile.desktop"

echo ""
echo "Listo. Busca \"HuntJob Chile\" en el menu de aplicaciones."
echo "Si GEMINI_API_KEY no esta exportada, la app la busca automaticamente en ~/.gemini_key"
