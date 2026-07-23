"""
Parser de Archivos de CV y Documentos de Postulantes — HuntJob Chile.
Inspirado en pyresume, stackedcv, simple-resume-parser y orasik/resume-parser.

Soporta análisis de texto extraído de archivos de CV (PDF, DOCX, TXT),
extrayendo datos de contacto (email, teléfono, RUT/DNI, LinkedIn),
experiencia laboral estructurada, educación, idiomas y habilidades.
"""

import re
from core.perfil import VALORES_POR_DEFECTO, COMPETENCIAS_POPULARES, HABILIDADES_BLANDAS_POPULARES, IDIOMAS_POPULARES


def parsear_cv_completo(texto: str) -> dict:
    """
    Parsea un texto completo de CV y devuelve un diccionario compatible
    con la estructura de perfil de HuntJob Chile.
    """
    perfil = dict(VALORES_POR_DEFECTO)
    if not texto or not texto.strip():
        return perfil

    texto_clean = texto.strip()
    texto_lower = texto_clean.lower()

    # 1. Extraer Email
    match_email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", texto_clean)
    if match_email:
        perfil["email"] = match_email.group(0)

    # 2. Extraer Teléfono (formatos chilenos e internacionales)
    match_tel = re.search(r"(\+?56\s?9?\s?\d{4}\s?\d{4}|\+?\d{1,3}[\s-]?\d{3,4}[\s-]?\d{3,4})", texto_clean)
    if match_tel:
        perfil["telefono"] = match_tel.group(0).strip()

    # 3. Extraer LinkedIn URL
    match_linkedin = re.search(r"(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?", texto_clean, re.IGNORECASE)
    if match_linkedin:
        perfil["linkedin"] = match_linkedin.group(0)

    # 4. Extraer Nombre (primera línea o patrón 'Nombre:')
    lineas = [l.strip() for l in texto_clean.split("\n") if l.strip()]
    if lineas:
        primera_linea = lineas[0]
        if len(primera_linea) < 50 and not "@" in primera_linea and not "http" in primera_linea:
            perfil["nombre"] = primera_linea

    # 5. Extraer Competencias Técnicas
    skills_encontradas = []
    for skill in COMPETENCIAS_POPULARES:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, texto_lower):
            skills_encontradas.append(skill)
    perfil["competencias_tecnicas"] = ", ".join(list(dict.fromkeys(skills_encontradas)))

    # 6. Extraer Habilidades Blandas
    blandas_encontradas = []
    for soft in HABILIDADES_BLANDAS_POPULARES:
        palabras = [p.lower() for p in soft.split() if len(p) > 3]
        if any(w in texto_lower for w in palabras):
            blandas_encontradas.append(soft)
    perfil["habilidades_blandas"] = ", ".join(list(dict.fromkeys(blandas_encontradas[:5])))

    # 7. Extraer Idiomas
    idiomas_list = []
    for idioma in IDIOMAS_POPULARES:
        if idioma.lower() in texto_lower:
            nivel = "Avanzado" if "avanzado" in texto_lower or "fluent" in texto_lower else "Intermedio"
            idiomas_list.append({"idioma": idioma, "nivel": nivel})
    perfil["idiomas"] = idiomas_list

    # 8. Determinar Seniority y Años de Experiencia
    if any(k in texto_lower for k in ["lead", "principal", "director", "head of"]):
        perfil["seniority"] = "Lead"
        perfil["anos_experiencia"] = 8
    elif any(k in texto_lower for k in ["senior", "sr.", "sr ", " 5+ años", " 6+ años"]):
        perfil["seniority"] = "Senior"
        perfil["anos_experiencia"] = 5
    elif any(k in texto_lower for k in ["semi senior", "ssr", " 3+ años"]):
        perfil["seniority"] = "Semi Senior"
        perfil["anos_experiencia"] = 3
    else:
        perfil["seniority"] = "Junior"
        perfil["anos_experiencia"] = 1

    return perfil
