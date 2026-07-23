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
    """Intenta primero con Gemini. Si falla (por cuota 429 u otro error) e intenta con Groq. Aplica Privacy Shield."""
    from core.privacy_shield import anonimizar_datos_sensibles, restaurar_datos_sensibles

    prompt_seguro, mapa_privacidad = anonimizar_datos_sensibles(prompt)
    errores = []
    respuesta_bruta = None

    # 1. Intentar Gemini
    try:
        respuesta_bruta = _llamar_gemini(prompt_seguro, response_mime_type, response_schema)
    except ErrorIA as e:
        errores.append(f"Gemini: {e}")

    # 2. Intentar Groq como respaldo si está disponible
    if respuesta_bruta is None and _obtener_key("GROQ_API_KEY"):
        json_mode = (response_mime_type == "application/json")
        try:
            respuesta_bruta = _llamar_groq(prompt_seguro, json_mode=json_mode)
        except ErrorIA as e:
            errores.append(f"Groq: {e}")

    if respuesta_bruta is not None:
        return restaurar_datos_sensibles(respuesta_bruta, mapa_privacidad)

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
    try:
        texto_res = _ejecutar_con_fallback(prompt, response_mime_type="application/json", response_schema=schema)
        resultado = json.loads(texto_res)
        return {
            "cargo": str(resultado.get("cargo", "")).strip() or "Cargo General",
            "empresa": str(resultado.get("empresa", "No especificada")).strip(),
        }
    except Exception:
        lineas = [l.strip() for l in texto_oferta.split("\n") if l.strip()]
        cargo_linea = lineas[0] if lineas else "Cargo General"
        return {"cargo": cargo_linea[:60], "empresa": "No especificada"}


def analizar_match(texto_oferta: str, perfil: dict) -> dict:
    contexto_perfil = formatear_perfil(perfil)
    prompt = (
        "Eres un reclutador experto y auditor de sistemas ATS (Applicant Tracking Systems). "
        "Compara el perfil del candidato contra la oferta laboral. Responde ÚNICAMENTE un objeto JSON válido "
        "con las siguientes llaves:\n"
        "- \"score\": (entero de 0 a 100 indicando la compatibilidad ATS global)\n"
        "- \"desglose_score\": (objeto con 4 puntajes de 0 a 100: \"hardskills\", \"experiencia\", \"formacion\", \"softskills\")\n"
        "- \"explicacion\": (string de 2 a 3 líneas con el diagnóstico general)\n"
        "- \"fortalezas\": (lista de 2 a 4 ítems con los puntos fuertes coincidentes)\n"
        "- \"debilidades\": (lista de 2 a 4 brechas reales del candidato frente a la oferta: seniority, "
        "años de experiencia, dominio de un área, etc. — no repitas aquí lo que ya va en palabras_faltantes)\n"
        "- \"palabras_faltantes\": (lista de 2 a 4 términos o herramientas clave que exige la oferta pero no destacan en el perfil)\n"
        "- \"recomendaciones\": (lista de 2 a 3 acciones concretas para subir el puntaje de postulación)\n"
        "- \"resumen_fit\": (lista de objetos para comparar 'Postulante vs Requisitos', cada objeto con 'requisito' [string], 'postulante' [string: qué ofrece el candidato], y 'estado' [string: 'Cumplido', 'Parcial' o 'No detectado'])\n"
        "- \"requisitos_destacados\": (lista de los 4 a 8 términos o herramientas clave más importantes que exige la oferta y que el candidato posee)\n\n"
        f"Perfil del candidato:\n{contexto_perfil}\n\n"
        f"Oferta laboral:\n{texto_oferta[:LIMITE_CARACTERES_CONTEXTO]}"
    )
    schema = {
        "type": "OBJECT",
        "properties": {
            "score": {"type": "INTEGER"},
            "desglose_score": {
                "type": "OBJECT",
                "properties": {
                    "hardskills": {"type": "INTEGER"},
                    "experiencia": {"type": "INTEGER"},
                    "formacion": {"type": "INTEGER"},
                    "softskills": {"type": "INTEGER"},
                },
            },
            "explicacion": {"type": "STRING"},
            "fortalezas": {"type": "ARRAY", "items": {"type": "STRING"}},
            "debilidades": {"type": "ARRAY", "items": {"type": "STRING"}},
            "palabras_faltantes": {"type": "ARRAY", "items": {"type": "STRING"}},
            "recomendaciones": {"type": "ARRAY", "items": {"type": "STRING"}},
            "resumen_fit": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "requisito": {"type": "STRING"},
                        "postulante": {"type": "STRING"},
                        "estado": {"type": "STRING"},
                    },
                    "required": ["requisito", "postulante", "estado"],
                },
            },
            "requisitos_destacados": {"type": "ARRAY", "items": {"type": "STRING"}},
        },
        "required": [
            "score",
            "explicacion",
            "fortalezas",
            "debilidades",
            "palabras_faltantes",
            "recomendaciones",
            "resumen_fit",
            "requisitos_destacados",
        ],
    }
    try:
        texto_res = _ejecutar_con_fallback(prompt, response_mime_type="application/json", response_schema=schema)
        resultado = json.loads(texto_res)
        desglose = resultado.get("desglose_score") or {}
        score_global = int(resultado.get("score", 50))
        return {
            "score": score_global,
            "desglose_score": {
                "hardskills": int(desglose.get("hardskills", score_global)),
                "experiencia": int(desglose.get("experiencia", score_global)),
                "formacion": int(desglose.get("formacion", score_global)),
                "softskills": int(desglose.get("softskills", score_global)),
            },
            "explicacion": str(resultado.get("explicacion", "")),
            "fortalezas": list(resultado.get("fortalezas", [])),
            "debilidades": list(resultado.get("debilidades", [])),
            "palabras_faltantes": list(resultado.get("palabras_faltantes", [])),
            "recomendaciones": list(resultado.get("recomendaciones", [])),
            "resumen_fit": list(resultado.get("resumen_fit", [])),
            "requisitos_destacados": list(resultado.get("requisitos_destacados", [])),
        }
    except Exception:
        return {
            "score": 75,
            "desglose_score": {"hardskills": 75, "experiencia": 70, "formacion": 80, "softskills": 75},
            "explicacion": "Análisis preliminar ATS. Configura GEMINI_API_KEY en st.secrets para análisis IA completo.",
            "fortalezas": ["Formación y perfil laboral alineados", "Años de experiencia requeridos"],
            "debilidades": ["Optimizar palabras clave específicas"],
            "palabras_faltantes": ["Términos técnicos específicos del rol"],
            "recomendaciones": ["Alinear términos del CV con la descripción del cargo"],
            "resumen_fit": [
                {"requisito": "Experiencia laboral", "postulante": perfil.get("seniority", "Junior"), "estado": "Cumplido"},
                {"requisito": "Stack técnico principal", "postulante": perfil.get("stack_principal", "Revisar"), "estado": "Parcial"},
            ],
            "requisitos_destacados": [perfil.get("stack_principal", "Conocimientos del área")],
        }


def generar_preguntas_entrevista(texto_oferta: str, perfil: dict) -> list[dict]:
    """
    Genera las 5 preguntas más probables de entrevista (técnicas y conductuales)
    con respuestas modelo estructuradas basadas en la oferta y el perfil del postulante.
    """
    contexto_perfil = formatear_perfil(perfil)
    prompt = (
        "Eres un reclutador senior y evaluador técnico en Chile. A partir de la oferta laboral y el perfil del candidato, "
        "genera las 5 preguntas de entrevista de trabajo más probables que le harán (mezclando preguntas técnicas y conductuales). "
        "Para cada pregunta, redacta una respuesta modelo ideal basada en la experiencia real del candidato.\n\n"
        "Responde ÚNICAMENTE un objeto JSON con la llave \"preguntas\": una lista de 5 objetos, cada uno con:\n"
        "- \"tipo\": (\"Técnica\" o \"Conductual/STAR\")\n"
        "- \"pregunta\": (string)\n"
        "- \"consejo\": (string: recomendación clave para responder)\n"
        "- \"respuesta_modelo\": (string de 2 a 4 líneas)\n\n"
        f"Perfil del candidato:\n{contexto_perfil}\n\n"
        f"Oferta laboral:\n{texto_oferta[:LIMITE_CARACTERES_CONTEXTO]}"
    )
    schema = {
        "type": "OBJECT",
        "properties": {
            "preguntas": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "tipo": {"type": "STRING"},
                        "pregunta": {"type": "STRING"},
                        "consejo": {"type": "STRING"},
                        "respuesta_modelo": {"type": "STRING"},
                    },
                    "required": ["tipo", "pregunta", "consejo", "respuesta_modelo"],
                },
            }
        },
        "required": ["preguntas"],
    }
    try:
        texto_res = _ejecutar_con_fallback(prompt, response_mime_type="application/json", response_schema=schema)
        resultado = json.loads(texto_res)
        return list(resultado.get("preguntas", []))
    except Exception as e:
        raise ErrorIA(f"Error generando preguntas de entrevista: {e}")


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


def pulir_experiencia_laboral(experiencia_laboral: list[dict], puesto_objetivo: str, texto_oferta: str) -> list[list[str]]:
    """
    Por cada trabajo, pide a la IA una versión reordenada/pulida de sus
    'funciones' ya cargadas, priorizando lo relevante para la oferta.
    NUNCA inventa funciones ni experiencias que no estén en el perfil.
    ENVUELVE las palabras/requisitos clave de la oferta que estén presentes en las funciones
    en etiquetas <b> y </b> (por ejemplo, <b>Python</b>, <b>Liderazgo de Equipos</b>) para destacarlas en el CV ATS.
    """
    from core.perfil import lineas_no_vacias

    bullets_originales = [lineas_no_vacias(trabajo.get("funciones", "")) for trabajo in experiencia_laboral]
    trabajos_con_funciones = [
        (indice, trabajo) for indice, trabajo in enumerate(experiencia_laboral) if bullets_originales[indice]
    ]
    if not trabajos_con_funciones:
        return bullets_originales

    bloques = []
    for numero, (indice, trabajo) in enumerate(trabajos_con_funciones, start=1):
        funciones_texto = "\n".join(f"- {f}" for f in bullets_originales[indice])
        bloques.append(f"Trabajo {numero} — {trabajo.get('cargo', '')} en {trabajo.get('empresa', '')}:\n{funciones_texto}")

    prompt = (
        f"Eres un editor experto de currículums ATS. A continuación hay {len(bloques)} trabajos de la experiencia "
        f"laboral real de un candidato que postula a '{puesto_objetivo}'. Para cada uno, reordena y pule "
        "la redacción de sus funciones escritas, dando prioridad a lo más relevante para la oferta laboral. "
        "NUNCA agregues una función, herramienta o logro que no esté en el texto original — solo reordena y pule. "
        "CRÍTICO: En cada función pulida, identifica las palabras clave, herramientas o tecnologías de la oferta "
        "que el candidato efectivamente mencione o posea, y ENVUÉLVELAS EN ETIQUETAS <b> y </b> (ej: <b>Python</b>, "
        "<b>PostgreSQL</b>, <b>Scrum</b>) para destacarlas visualmente en negrita.\n\n"
        "Responde ÚNICAMENTE un objeto JSON con la llave \"bullets_por_trabajo\": una lista de listas de "
        f"strings, en el MISMO ORDEN y con EXACTAMENTE {len(bloques)} elementos (uno por trabajo).\n\n"
        + "\n\n".join(bloques)
        + f"\n\nOferta laboral:\n{texto_oferta[:LIMITE_CARACTERES_CONTEXTO]}"
    )
    schema = {
        "type": "OBJECT",
        "properties": {
            "bullets_por_trabajo": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "STRING"}}},
        },
        "required": ["bullets_por_trabajo"],
    }

    try:
        texto_res = _ejecutar_con_fallback(prompt, response_mime_type="application/json", response_schema=schema)
        resultado = json.loads(texto_res)
        pulido = resultado.get("bullets_por_trabajo", [])
        if len(pulido) != len(bloques):
            raise ValueError("La IA devolvió una cantidad de trabajos distinta a la esperada.")
    except Exception:
        return bullets_originales

    bullets_finales = list(bullets_originales)
    for (indice, _trabajo), bullets_pulidos in zip(trabajos_con_funciones, pulido):
        limpios = [str(b).strip() for b in bullets_pulidos if str(b).strip()]
        bullets_finales[indice] = limpios or bullets_originales[indice]
    return bullets_finales


def optimizar_logro_car(logro_bruto: str, cargo: str = "") -> list[str]:
    """
    Toma una frase simple de experiencia laboral y genera 3 alternativas
    estructuradas bajo la metodología Google CAR (Contexto - Acción - Resultado).
    """
    prompt = (
        f"Eres un consultor experto en redacción de CVs para superar filtros ATS y reclutadores de elite. "
        f"Toma el siguiente logro o tarea de experiencia laboral (Cargo: {cargo or 'General'}) y reescríbelo en 3 "
        f"versiones alternativas de alto impacto usando la metodología Google CAR (Contexto, Acción, Resultado).\n"
        f"Reglas de formato estrictas:\n"
        f"1. Cada alternativa debe incluir un impacto o métrica cuantitativa estimada (ej. 'incrementando un 25%', 'reduciendo tiempos en un 30%').\n"
        f"2. Encierra en etiquetas HTML <b>...</b> las herramientas tecnológicas y palabras clave principales.\n"
        f"3. Responde ÚNICAMENTE un objeto JSON con la llave \"opciones\": una lista de 3 strings.\n\n"
        f"Texto original:\n{logro_bruto}"
    )
    schema = {
        "type": "OBJECT",
        "properties": {"opciones": {"type": "ARRAY", "items": {"type": "STRING"}}},
        "required": ["opciones"],
    }
    try:
        texto_res = _ejecutar_con_fallback(prompt, response_mime_type="application/json", response_schema=schema)
        resultado = json.loads(texto_res)
        return resultado.get("opciones", [])
    except Exception:
        return [
            f"Lideré la optimización de procesos técnicos utilizando <b>{cargo or 'herramientas clave'}</b>, incrementando la eficiencia operativa en un <b>25%</b>.",
            f"Diseñé e implementé soluciones estratégicas con <b>{cargo or 'tecnología del área'}</b>, reduciendo los tiempos de respuesta en un <b>30%</b>.",
            f"Gestioné proyectos clave del área aplicando <b>mejores prácticas</b>, alcanzando un <b>95%</b> de cumplimiento de objetivos.",
        ]


def inyectar_palabras_clave_cv(cv_texto: str, palabras_faltantes: list[str]) -> str:
    """
    Inyecta estratégicamente las palabras clave faltantes en las viñetas del CV.
    """
    if not palabras_faltantes or not cv_texto:
        return cv_texto

    palabras_str = ", ".join(palabras_faltantes)
    prompt = (
        f"Eres un experto optimizador ATS. A continuación se presenta el borrador de un CV y una lista de "
        f"palabras clave/herramientas que el filtro ATS exige ({palabras_str}).\n"
        f"Instrucción: Reescribe el CV incorporando de manera fluida y coherente estas palabras clave en las viñetas "
        f"de experiencia o conocimientos. CRÍTICO: Envuelve cada palabra clave recién incorporada en etiquetas HTML <b> y </b> "
        f"para destacarla en negrita.\n\n"
        f"CV Original:\n{cv_texto}"
    )
    try:
        return _ejecutar_con_fallback(prompt)
    except Exception:
        cv_modificado = cv_texto
        for p in palabras_faltantes[:3]:
            cv_modificado += f"\n- Conocimientos aplicados en <b>{p}</b>."
        return cv_modificado
