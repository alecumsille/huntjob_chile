"""
Módulo de extracción de datos de contacto (email de RRHH y LinkedIn)
desde la descripción de ofertas laborales.
"""

import re

EMAIL_REGEX = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
LINKEDIN_REGEX = r"https?://(?:www\.)?linkedin\.com/(?:in|company|jobs)/[A-Za-z0-9_-]+"


def extraer_datos_contacto(texto_oferta: str) -> dict:
    """
    Escanea la descripción completa de una oferta para extraer:
    - emails: lista de correos válidos encontrados
    - linkedin: lista de enlaces de LinkedIn encontrados
    """
    if not texto_oferta:
        return {"emails": [], "linkedin": []}

    # Extraer emails ignorando correos genéricos de portales
    todos_emails = re.findall(EMAIL_REGEX, texto_oferta)
    emails_filtrados = [
        email for email in set(todos_emails)
        if not any(dominio in email.lower() for dominio in ["computrabajo", "chiletrabajos", "getonbrd", "sentry", "example"])
    ]

    # Extraer enlaces de LinkedIn
    todos_linkedin = re.findall(LINKEDIN_REGEX, texto_oferta)
    linkedin_filtrados = list(set(todos_linkedin))

    return {
        "emails": emails_filtrados,
        "linkedin": linkedin_filtrados,
    }
