"""
Envoltorio de escritorio para HuntJob Chile: levanta el servidor Streamlit
en un subproceso y lo muestra en una ventana nativa (GTK/WebKit) en vez de
una pestaña del navegador. Cerrar la ventana termina el servidor.
"""

import os
import sys
import signal
import subprocess
import time

import webview

PUERTO = 8765
CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))


def _variables_entorno() -> dict:
    """
    Si GEMINI_API_KEY no está exportada en el entorno, la busca en
    ~/.gemini_key (el mismo archivo que ya usan otros proyectos del
    usuario) para que la app de escritorio no requiera configuración
    adicional.
    """
    entorno = os.environ.copy()
    if not entorno.get("GEMINI_API_KEY"):
        ruta_key = os.path.expanduser("~/.gemini_key")
        if os.path.exists(ruta_key):
            with open(ruta_key, "r", encoding="utf-8") as archivo:
                entorno["GEMINI_API_KEY"] = archivo.read().strip()
    return entorno


def _ruta_streamlit() -> str:
    """Usa el streamlit del mismo venv que corre este script, sin depender del PATH."""
    return os.path.join(os.path.dirname(sys.executable), "streamlit")


def main() -> None:
    proceso = subprocess.Popen(
        [
            _ruta_streamlit(), "run", "app.py",
            "--server.headless", "true",
            "--server.port", str(PUERTO),
        ],
        cwd=CARPETA_PROYECTO,
        env=_variables_entorno(),
    )

    def _terminar_streamlit(*_args) -> None:
        # SIGTERM/SIGINT no ejecutan bloques `finally` de Python por sí
        # solos — sin este manejador, cerrar la app abruptamente (no vía
        # la ventana) deja el servidor de Streamlit corriendo huérfano.
        proceso.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _terminar_streamlit)
    signal.signal(signal.SIGINT, _terminar_streamlit)

    try:
        time.sleep(3)
        webview.create_window("HuntJob Chile", f"http://localhost:{PUERTO}", width=1280, height=800)
        webview.start()
    finally:
        proceso.terminate()
        proceso.wait(timeout=5)


if __name__ == "__main__":
    main()
