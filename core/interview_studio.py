"""
Interview Studio Component — Simulador Táctico de Entrevistas de Trabajo con IA.
HuntJob Chile.

Genera preguntas personalizadas para una oferta laboral dada y evalúa la respuesta del postulante
otorgando feedback táctico en 3 dimensiones: Palabras Clave, Tono Profesional y Puntos de Mejora.
"""

from typing import List, Dict
from core.motor_ia import _invocar_gemini_json


def generar_preguntas_entrevista(oferta_titulo: str, oferta_empresa: str, oferta_descripcion: str) -> List[Dict[str, str]]:
    """
    Genera 3 preguntas estratégicas de entrevista simulada específicas para la vacante dada.
    """
    prompt = f"""
    Eres un reclutador senior experto en Selección de Personal en Chile para la empresa {oferta_empresa or 'Chile'}.
    Genera 3 preguntas de entrevista clave para el cargo: '{oferta_titulo}'.
    Descripción de la oferta: {oferta_descripcion[:1000]}

    Responde estrictamente en formato JSON con la siguiente estructura:
    [
        {{
            "id": 1,
            "tipo": "Técnica / Competencias",
            "pregunta": "¿Texto de la pregunta 1?"
        }},
        {{
            "id": 2,
            "tipo": "Conductual / Situacional",
            "pregunta": "¿Texto de la pregunta 2?"
        }},
        {{
            "id": 3,
            "tipo": "Ajuste Cultural / Motivación",
            "pregunta": "¿Texto de la pregunta 3?"
        }}
    ]
    """

    res = _invocar_gemini_json(prompt)
    if isinstance(res, list) and len(res) >= 1:
        return res

    # Fallback predeterminado si falla el JSON de IA
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
            "recomendacion": "Amplía tu respuesta mencionando métricas o logros cuantificables."
        }

    prompt = f"""
    Evalúa la siguiente respuesta de un candidato en una entrevista para el cargo '{oferta_titulo}'.
    Pregunta: {pregunta}
    Respuesta del postulante: {respuesta_postulante}

    Responde en formato JSON con la estructura:
    {{
        "puntaje": 85,
        "feedback": "Análisis táctico de la respuesta...",
        "palabras_clave_usadas": ["palabra1", "palabra2"],
        "recomendacion": "Sugerencia clave para la entrevista real..."
    }}
    """

    res = _invocar_gemini_json(prompt)
    if isinstance(res, dict) and "puntaje" in res:
        return res

    return {
        "puntaje": 80,
        "feedback": "Buena estructura general en la respuesta.",
        "palabras_clave_usadas": ["experiencia", "resolución"],
        "recomendacion": "Menciona resultados específicos para destacar frente a otros postulantes."
    }
