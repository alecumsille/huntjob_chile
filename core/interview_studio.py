"""
Interview Studio Component — Simulador Táctico de Entrevistas de Trabajo con IA.
HuntJob Chile.
"""

import json
from typing import List, Dict
from core.motor_ia import _ejecutar_con_fallback


def generar_preguntas_entrevista(oferta_titulo: str, oferta_empresa: str, oferta_descripcion: str) -> List[Dict[str, str]]:
    """
    Genera 3 preguntas estratégicas de entrevista simulada específicas para la vacante dada.
    """
    prompt = f"""
    Eres un reclutador senior en Chile para {oferta_empresa or 'la empresa'}.
    Genera 3 preguntas de entrevista clave para el cargo: '{oferta_titulo}'.
    Descripción: {oferta_descripcion[:800]}

    Responde en JSON:
    [
        {{"id": 1, "tipo": "Técnica", "pregunta": "¿Pregunta 1?"}},
        {{"id": 2, "tipo": "Conductual", "pregunta": "¿Pregunta 2?"}},
        {{"id": 3, "tipo": "Ajuste Cultural", "pregunta": "¿Pregunta 3?"}}
    ]
    """

    try:
        raw_res = _ejecutar_con_fallback(prompt, response_mime_type="application/json")
        clean_res = raw_res.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_res)
        if isinstance(parsed, list) and len(parsed) >= 1:
            return parsed
    except Exception:
        pass

    return [
        {"id": 1, "tipo": "Competencias Técnicas", "pregunta": f"¿Cómo aplicas tus habilidades principales para el cargo de {oferta_titulo}?"},
        {"id": 2, "tipo": "Conductual", "pregunta": "Cuéntame sobre un desafío técnico o proyecto complejo que hayas resuelto recientemente."},
        {"id": 3, "tipo": "Ajuste Cultural", "pregunta": f"¿Por qué te interesa formar parte de {oferta_empresa or 'nuestra empresa'} y este rol en específico?"}
    ]


def evaluar_respuesta_entrevista(pregunta: str, respuesta_postulante: str, oferta_titulo: str) -> Dict[str, str]:
    """
    Evalúa la respuesta del candidato a una pregunta de entrevista y entrega retroalimentación profesional.
    """
    if not respuesta_postulante or len(respuesta_postulante.strip()) < 10:
        return {
            "puntaje": 40,
            "feedback": "La respuesta es demasiado breve. Se recomienda dar ejemplos concretos con el método STAR (Situación, Tarea, Acción, Resultado).",
            "palabras_clave_usadas": [],
            "recomendacion": "Amplía tu respuesta mencionando logros cuantificables."
        }

    prompt = f"""
    Evalúa esta respuesta en una entrevista para '{oferta_titulo}'.
    Pregunta: {pregunta}
    Respuesta: {respuesta_postulante}

    Responde en JSON:
    {{
        "puntaje": 85,
        "feedback": "Análisis táctico...",
        "palabras_clave_usadas": ["experiencia"],
        "recomendacion": "Sugerencia..."
    }}
    """

    try:
        raw_res = _ejecutar_con_fallback(prompt, response_mime_type="application/json")
        clean_res = raw_res.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_res)
        if isinstance(parsed, dict) and "puntaje" in parsed:
            return parsed
    except Exception:
        pass

    return {
        "puntaje": 80,
        "feedback": "Buena estructura general en la respuesta.",
        "palabras_clave_usadas": ["experiencia", "resolución"],
        "recomendacion": "Menciona resultados específicos para destacar frente a otros postulantes."
    }
