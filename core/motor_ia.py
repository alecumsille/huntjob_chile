"""
Módulo de generación de texto vía Gemini (Google AI). Sin fallback
silencioso entre modelos: si la API falla, se lanza una excepción clara
indicando la causa real (key faltante, error de la API, timeout), en vez
de devolver texto simulado.
"""

import json
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
    """
    Busca la key primero en la variable de entorno GEMINI_API_KEY (uso
    local / app de escritorio), y si no está, en st.secrets (necesario en
    Streamlit Community Cloud, que no inyecta secrets como variables de
    entorno). Se importa streamlit acá adentro para no acoplar este
    módulo a Streamlit cuando no hace falta.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
        except Exception:
            api_key = ""

    if not api_key:
        raise ErrorIA(
            "Falta GEMINI_API_KEY. Consigue una key gratis en "
            "https://aistudio.google.com/apikey y expórtala antes de correr "
            "la app (export GEMINI_API_KEY=tu-key) o configúrala en "
            "st.secrets si corre en Streamlit Community Cloud."
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


def analizar_match(texto_oferta: str, perfil: dict) -> dict:
    """
    Compara el perfil del usuario contra una oferta real y devuelve un
    score 0-100 + explicación breve, vía respuesta JSON estructurada de
    Gemini (más confiable que parsear texto libre con regex). Lanza
    ErrorIA con el detalle exacto si algo falla.
    """
    api_key = _obtener_api_key()

    contexto_perfil = (
        f"Años de experiencia: {perfil.get('anos_experiencia', 0)}\n"
        f"Nivel: {perfil.get('seniority', '')}\n"
        f"Stack principal: {perfil.get('stack_principal', '')}\n"
        f"Logros y experiencia: {perfil.get('logros_y_experiencia', '')}"
    )
    prompt = (
        "Compara el perfil del candidato contra la oferta laboral. Da un score de 0 "
        "a 100 de qué tan buen match es, y una explicación breve (2 a 3 líneas) de "
        "por qué, mencionando fortalezas y posibles brechas (ej. años de experiencia "
        "insuficientes, tecnologías del stack que la oferta pide y el candidato no "
        "menciona).\n\n"
        f"Perfil del candidato:\n{contexto_perfil}\n\n"
        f"Oferta laboral:\n{texto_oferta[:LIMITE_CARACTERES_CONTEXTO]}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "score": {"type": "INTEGER"},
                    "explicacion": {"type": "STRING"},
                },
                "required": ["score", "explicacion"],
            },
        },
    }
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
        texto_generado = cuerpo["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise ErrorIA(f"Gemini respondió sin contenido generado: {cuerpo}")

    try:
        resultado = json.loads(texto_generado)
    except json.JSONDecodeError:
        raise ErrorIA(f"Gemini no devolvió JSON válido: {texto_generado[:200]}")

    if "score" not in resultado or "explicacion" not in resultado:
        raise ErrorIA(f"La respuesta de Gemini no trae score/explicacion: {resultado}")

    return {"score": int(resultado["score"]), "explicacion": str(resultado["explicacion"])}
