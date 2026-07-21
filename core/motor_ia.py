"""
Módulo de generación de texto vía Gemini (Google AI). Sin fallback
silencioso entre modelos: si la API falla, se lanza una excepción clara
indicando la causa real (key faltante, error de la API, timeout), en vez
de devolver texto simulado.
"""

import os
import requests

URL_API = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
MODELO = "gemini-3.1-flash-lite"
TIMEOUT_SEGUNDOS = 30
LIMITE_CARACTERES_CONTEXTO = 4000


class ErrorIA(Exception):
    """Excepción específica para fallos de la capa de generación de texto."""
    pass


def _obtener_api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ErrorIA(
            "Falta la variable de entorno GEMINI_API_KEY. "
            "Consigue una key gratis en https://aistudio.google.com/apikey "
            "y expórtala antes de correr la app: export GEMINI_API_KEY=tu-key"
        )
    return api_key


def generar_texto(prompt_sistema: str, texto_base: str) -> str:
    """
    Envía un prompt a Gemini y devuelve la respuesta generada. Lanza
    ErrorIA con el detalle exacto si algo falla — no hay reintento
    silencioso con otros modelos.
    """
    api_key = _obtener_api_key()

    prompt_completo = f"{prompt_sistema}\n\nTexto de referencia:\n{texto_base[:LIMITE_CARACTERES_CONTEXTO]}"
    payload = {"contents": [{"parts": [{"text": prompt_completo}]}]}
    url = URL_API.format(modelo=MODELO)

    try:
        respuesta = requests.post(
            url, params={"key": api_key}, json=payload, timeout=TIMEOUT_SEGUNDOS
        )
    except requests.exceptions.Timeout:
        raise ErrorIA(f"Gemini no respondió en {TIMEOUT_SEGUNDOS}s.")
    except requests.exceptions.ConnectionError as e:
        raise ErrorIA(f"Se perdió la conexión con Gemini: {e}")

    if respuesta.status_code != 200:
        raise ErrorIA(f"Gemini devolvió código {respuesta.status_code}: {respuesta.text[:200]}")

    cuerpo = respuesta.json()
    try:
        texto_generado = cuerpo["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        raise ErrorIA(f"Gemini respondió sin contenido generado: {cuerpo}")

    if not texto_generado:
        raise ErrorIA("Gemini respondió con texto vacío. Revisa el prompt.")

    return texto_generado
