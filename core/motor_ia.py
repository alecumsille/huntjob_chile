"""
Módulo de generación de texto vía Ollama local (modelo phi3).
Sin fallback silencioso entre modelos: si phi3 no responde, se lanza
una excepción clara indicando la causa real (servicio caído, modelo
no instalado, timeout), en vez de probar modelos al azar.
"""

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "phi3"
TIMEOUT_SEGUNDOS = 90
LIMITE_CARACTERES_CONTEXTO = 4000


class ErrorOllama(Exception):
    """Excepción específica para fallos de la capa de generación local."""
    pass


def verificar_ollama_activo() -> None:
    """
    Verifica que el servicio Ollama esté corriendo antes de intentar
    generar texto. Lanza ErrorOllama con instrucciones concretas si no.
    """
    try:
        respuesta = requests.get("http://localhost:11434/api/tags", timeout=3)
    except requests.exceptions.ConnectionError:
        raise ErrorOllama(
            "Ollama no está corriendo en localhost:11434. "
            "Ejecuta 'ollama serve' en una terminal aparte."
        )

    if respuesta.status_code != 200:
        raise ErrorOllama(f"Ollama respondió con estado inesperado: {respuesta.status_code}")

    modelos_instalados = [m["name"] for m in respuesta.json().get("models", [])]
    if not any(MODELO in nombre for nombre in modelos_instalados):
        raise ErrorOllama(
            f"El modelo '{MODELO}' no aparece instalado. "
            f"Modelos disponibles: {modelos_instalados or 'ninguno'}. "
            f"Ejecuta 'ollama pull {MODELO}'."
        )


def generar_texto(prompt_sistema: str, texto_base: str) -> str:
    """
    Envía un prompt a Ollama (modelo phi3) y devuelve la respuesta generada.
    Lanza ErrorOllama con el detalle exacto si algo falla — no hay
    reintento silencioso con otros modelos.
    """
    verificar_ollama_activo()

    prompt_completo = f"{prompt_sistema}\n\nTexto de referencia:\n{texto_base[:LIMITE_CARACTERES_CONTEXTO]}"

    payload = {
        "model": MODELO,
        "prompt": prompt_completo,
        "stream": False,
    }

    try:
        respuesta = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.Timeout:
        raise ErrorOllama(f"Ollama no respondió en {TIMEOUT_SEGUNDOS}s. El modelo puede estar sobrecargado.")
    except requests.exceptions.ConnectionError:
        raise ErrorOllama("Se perdió la conexión con Ollama durante la generación.")

    if respuesta.status_code != 200:
        raise ErrorOllama(f"Ollama devolvió código {respuesta.status_code}: {respuesta.text[:200]}")

    cuerpo = respuesta.json()
    texto_generado = cuerpo.get("response", "").strip()

    if not texto_generado:
        raise ErrorOllama("Ollama respondió con texto vacío. Revisa el prompt o el estado del modelo.")

    return texto_generado
