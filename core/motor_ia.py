"""
Módulo de generación de texto vía Gemini (Google AI) con fallback transparente
hacia Groq (Llama 3.3 70B). Si Gemini falla por cuota (429) o conectividad,
la app intenta automáticamente con Groq si está configurada la GROQ_API_KEY.
"""

import json
import os
import time
import requests

from core.perfil import formatear_perfil

# Configuración Gemini
URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
MODELO_GEMINI = "gemini-2.0-flash-lite"

# Configuración Groq (OpenAI-compatible API)
URL_GROQ = "https://api.groq.com/openai/v1/chat/completions"
MODELO_GROQ = "llama-3.3-70b-versatile"

TIMEOUT_SEGUNDOS = 30
LIMITE_CARACTERES_CONTEXTO = 10000


class ErrorIA(Exception):
    """Excepción específica para fallos de la capa de generación de texto."""
    pass


def _obtener_key(nombre_var: str) -> str:
    """Busca una API key en env vars o en st.secrets si está en Streamlit Cloud."""
    key = os.environ.get(nombre_var, "").strip()
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get(nombre_var, "").strip()
        except Exception:
            key = ""
    return key


def _llamar_gemini(prompt: str, response_mime_type: str | None = None, response_schema: dict | None = None) -> str:
    api_key = _obtener_key("GEMINI_API_KEY")
    if not api_key:
        raise ErrorIA("Falta GEMINI_API_KEY.")

    url = URL_GEMINI.format(modelo=MODELO_GEMINI)
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    gen_config = {}
    if response_mime_type:
        gen_config["responseMimeType"] = response_mime_type
    if response_schema:
        gen_config["responseSchema"] = response_schema
    if gen_config:
        payload["generationConfig"] = gen_config

    try:
        res = requests.post(url, params={"key": api_key}, json=payload, timeout=TIMEOUT_SEGUNDOS)
    except Exception as e:
        raise ErrorIA(f"Conexión con Gemini falló: {e}")

    if res.status_code == 429:
        raise ErrorIA("El servicio de IA superó el límite de consultas por minuto. Espera 1 minuto y vuelve a presionar el botón.")
    if res.status_code != 200:
        raise ErrorIA(f"Servicio de IA no disponible ({res.status_code}). Intenta en un momento.")

    cuerpo = res.json()
    try:
        return cuerpo["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        raise ErrorIA("Gemini respondió sin contenido.")


def _llamar_groq(prompt: str, json_mode: bool = False) -> str:
    api_key = _obtener_key("GROQ_API_KEY")
    if not api_key:
        raise ErrorIA("Falta GROQ_API_KEY.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODELO_GROQ,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        res = requests.post(URL_GROQ, headers=headers, json=payload, timeout=TIMEOUT_SEGUNDOS)
    except Exception as e:
        raise ErrorIA(f"Conexión con Groq falló: {e}")

    if res.status_code != 200:
        raise ErrorIA(f"Groq respondió {res.status_code}: {res.text[:150]}")

    cuerpo = res.json()
    try:
        return cuerpo["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        raise ErrorIA("Groq respondió sin contenido.")


def _ejecutar_con_fallback(prompt: str, response_mime_type: str | None = None, response_schema: dict | None = None) -> str:
    """Intenta primero con Gemini. Si falla (por cuota 429 u otro error) e intenta con Groq."""
    errores = []

    # 1. Intentar Gemini
    try:
        return _llamar_gemini(prompt, response_mime_type, response_schema)
    except ErrorIA as e:
        errores.append(f"Gemini: {e}")

    # 2. Intentar Groq como respaldo si está disponible
    if _obtener_key("GROQ_API_KEY"):
        json_mode = (response_mime_type == "application/json")
        try:
            return _llamar_groq(prompt, json_mode=json_mode)
        except ErrorIA as e:
            errores.append(f"Groq: {e}")

    # Si ninguno funcionó
    if not _obtener_key("GEMINI_API_KEY") and not _obtener_key("GROQ_API_KEY"):
        raise ErrorIA("Falta configurar GEMINI_API_KEY o GROQ_API_KEY en st.secrets.")

    raise ErrorIA(f"No se pudo completar la solicitud con IA. Detalle: {' | '.join(errores)}")


def generar_texto(prompt_sistema: str, texto_base: str) -> str:
    prompt_completo = f"{prompt_sistema}\n\nTexto de referencia:\n{texto_base[:LIMITE_CARACTERES_CONTEXTO]}"
    return _ejecutar_con_fallback(prompt_completo)


def extraer_cargo_y_empresa(texto_oferta: str) -> dict:
    """Detecta el título del puesto y la empresa que publica la oferta en un solo llamado."""
    prompt = (
        "Extrae de la siguiente oferta laboral el título exacto del puesto y el nombre de la "
        "empresa que publica el aviso. Si la empresa no está indicada explícitamente (ej. "
        "'empresa confidencial' o portales que la ocultan), responde \"No especificada\". "
        "Responde ÚNICAMENTE un objeto JSON con las llaves \"cargo\" y \"empresa\".\n\n"
        f"Oferta laboral:\n{texto_oferta[:LIMITE_CARACTERES_CONTEXTO]}"
    )
    schema = {
        "type": "OBJECT",
        "properties": {"cargo": {"type": "STRING"}, "empresa": {"type": "STRING"}},
        "required": ["cargo", "empresa"],
    }
    texto_res = _ejecutar_con_fallback(prompt, response_mime_type="application/json", response_schema=schema)
    try:
        resultado = json.loads(texto_res)
        return {
            "cargo": str(resultado.get("cargo", "")).strip(),
            "empresa": str(resultado.get("empresa", "No especificada")).strip(),
        }
    except Exception as e:
        raise ErrorIA(f"Error procesando detección de cargo/empresa: {e}")


def analizar_match(texto_oferta: str, perfil: dict) -> dict:
    contexto_perfil = formatear_perfil(perfil)
    prompt = (
        "Eres un reclutador experto y auditor de sistemas ATS (Applicant Tracking Systems). "
        "Compara el perfil del candidato contra la oferta laboral. Responde ÚNICAMENTE un objeto JSON válido "
        "con las siguientes llaves:\n"
        "- \"score\": (entero de 0 a 100 indicando la compatibilidad ATS)\n"
        "- \"explicacion\": (string de 2 a 3 líneas con el diagnóstico general)\n"
        "- \"fortalezas\": (lista de 2 a 4 ítems con los puntos fuertes coincidentes)\n"
        "- \"debilidades\": (lista de 2 a 4 brechas reales del candidato frente a la oferta: seniority, "
        "años de experiencia, dominio de un área, etc. — no repitas aquí lo que ya va en palabras_faltantes)\n"
        "- \"palabras_faltantes\": (lista de 2 a 4 términos o herramientas clave que exige la oferta pero no destacan en el perfil)\n"
        "- \"recomendaciones\": (lista de 2 a 3 acciones concretas para subir el puntaje de postulación)\n\n"
        f"Perfil del candidato:\n{contexto_perfil}\n\n"
        f"Oferta laboral:\n{texto_oferta[:LIMITE_CARACTERES_CONTEXTO]}"
    )
    schema = {
        "type": "OBJECT",
        "properties": {
            "score": {"type": "INTEGER"},
            "explicacion": {"type": "STRING"},
            "fortalezas": {"type": "ARRAY", "items": {"type": "STRING"}},
            "debilidades": {"type": "ARRAY", "items": {"type": "STRING"}},
            "palabras_faltantes": {"type": "ARRAY", "items": {"type": "STRING"}},
            "recomendaciones": {"type": "ARRAY", "items": {"type": "STRING"}},
        },
        "required": ["score", "explicacion", "fortalezas", "debilidades", "palabras_faltantes", "recomendaciones"],
    }

    texto_res = _ejecutar_con_fallback(prompt, response_mime_type="application/json", response_schema=schema)
    try:
        resultado = json.loads(texto_res)
        return {
            "score": int(resultado.get("score", 50)),
            "explicacion": str(resultado.get("explicacion", "")),
            "fortalezas": list(resultado.get("fortalezas", [])),
            "debilidades": list(resultado.get("debilidades", [])),
            "palabras_faltantes": list(resultado.get("palabras_faltantes", [])),
            "recomendaciones": list(resultado.get("recomendaciones", [])),
        }
    except Exception as e:
        raise ErrorIA(f"Error procesando respuesta del análisis de match: {e}")


def sugerir_respuesta(pregunta: str, perfil: dict, opciones: list[str] | None = None) -> dict:
    contexto_perfil = formatear_perfil(perfil)
    instruccion_opciones = ""
    if opciones:
        instruccion_opciones = (
            f" Debes elegir EXACTAMENTE una de estas alternativas: {', '.join(opciones)}."
        )

    prompt = (
        "Eres un candidato respondiendo una pregunta de un formulario de postulación. "
        "Responde ÚNICAMENTE un objeto JSON válido con las llaves \"respuesta\" (string corto) "
        f"y \"justificacion\" (string de 1 a 2 líneas).{instruccion_opciones}\n\n"
        f"Perfil del candidato:\n{contexto_perfil}\n\n"
        f"Pregunta:\n{pregunta}"
    )
    schema = {
        "type": "OBJECT",
        "properties": {
            "respuesta": {"type": "STRING"},
            "justificacion": {"type": "STRING"},
        },
        "required": ["respuesta", "justificacion"],
    }

    texto_res = _ejecutar_con_fallback(prompt, response_mime_type="application/json", response_schema=schema)
    try:
        resultado = json.loads(texto_res)
        return {"respuesta": str(resultado["respuesta"]), "justificacion": str(resultado["justificacion"])}
    except Exception as e:
        raise ErrorIA(f"Error procesando sugerencia de respuesta: {e}")
