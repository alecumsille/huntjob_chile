"""
Gestión del perfil de usuario. Con cuenta real (Supabase), el perfil
vive en Postgres por user_id (ver core/db.py) — nunca en disco. En
modo invitado (sin cuenta) vive solo en st.session_state, que es
privado por navegador/pestaña y se pierde al cerrar sesión: nunca se
escribe a un archivo compartido en el servidor, que era la fuga de
datos entre visitantes que tenía la versión anterior.

El CV final mezcla dos fuentes: las secciones de este perfil (formación,
competencias, habilidades blandas, idiomas, datos personales) se
renderizan literales en core/generador_pdf.py — la IA nunca las toca.
Solo el resumen profesional y los bullets de experiencia pasan por IA
(ver core/postulacion.py y core/motor_ia.py).
"""

import copy

import streamlit as st

VALORES_POR_DEFECTO = {
    "nombre": "",
    "email": "",
    "telefono": "",
    "linkedin": "",
    "ciudad": "",
    "anos_experiencia": 0,
    "seniority": "Junior",
    "experiencia_laboral": [],
    "formacion_academica": [],
    "idiomas": [],
    "habilidades_blandas": "",
    "competencias_tecnicas": "",
    # Legado: ya no se usan en la generación del CV, se mantienen solo
    # como origen de la migración automática de lectura (ver
    # _migrar_legado). Un usuario nuevo nunca los llena.
    "stack_principal": "",
    "logros_y_experiencia": "",
}

NIVELES_SENIORITY = ["Junior", "Semi Senior", "Senior", "Lead"]
NIVELES_IDIOMA = ["Básico", "Intermedio", "Avanzado", "Nativo"]
TIPOS_FORMACION = ["Carrera", "Curso", "Certificación"]

IDIOMAS_POPULARES = ["Español", "Inglés", "Portugués", "Alemán", "Francés", "Italiano", "Chino Mandarín", "Japonés"]
COMPETENCIAS_POPULARES = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "SQL", "PostgreSQL",
    "Docker", "AWS", "Git / GitHub", "Excel Avanzado", "Power BI", "Scrum / Agile",
    "Java", "C# / .NET", "PHP", "Flutter", "Kubernetes", "Linux / Bash", "HTML/CSS"
]
HABILIDADES_BLANDAS_POPULARES = [
    "Liderazgo de Equipos", "Comunicación Efectiva", "Resolución de Problemas",
    "Trabajo en Equipo", "Adaptabilidad y Flexibilidad", "Pensamiento Crítico",
    "Gestión del Tiempo", "Negociación", "Pensamiento Analítico",
    "Orientación a Resultados", "Autonomía y Proactividad"
]


def lineas_no_vacias(texto: str) -> list[str]:
    """
    Convierte un texto multilínea (una idea por línea, como se cargan
    habilidades y competencias en el formulario) en una lista,
    descartando líneas en blanco. Se usa tanto para renderizar el PDF
    como para el fallback de bullets de experiencia en motor_ia.py.
    """
    return [linea.strip() for linea in (texto or "").split("\n") if linea.strip()]


def _migrar_legado(perfil: dict) -> dict:
    """
    Fallback de lectura (no destructivo): si el usuario tiene datos en
    los campos viejos de texto libre pero nada todavía en los campos
    estructurados nuevos, los precarga como una primera entrada editable
    para que no pierda lo que ya había escrito. No modifica los campos
    viejos ni escribe nada en la base — solo transforma el dict en
    memoria antes de devolverlo.
    """
    perfil = dict(perfil)
    if not perfil.get("experiencia_laboral") and perfil.get("logros_y_experiencia"):
        perfil["experiencia_laboral"] = [{
            "cargo": "",
            "empresa": "",
            "fecha_inicio": "",
            "fecha_fin": "",
            "actualidad": False,
            "funciones": perfil["logros_y_experiencia"],
        }]
    if not perfil.get("competencias_tecnicas") and perfil.get("stack_principal"):
        perfil["competencias_tecnicas"] = perfil["stack_principal"]
    return perfil


def cargar_perfil(contexto_usuario: dict | None) -> dict:
    """
    contexto_usuario = {"user_id": ..., "access_token": ...} para una
    cuenta real, o None en modo invitado.
    """
    if contexto_usuario and contexto_usuario.get("user_id"):
        from core.db import obtener_perfil
        perfil = obtener_perfil(contexto_usuario["user_id"], contexto_usuario["access_token"])
    else:
        perfil = copy.deepcopy(VALORES_POR_DEFECTO)
        perfil.update(st.session_state.get("perfil_invitado", {}))
    return _migrar_legado(perfil)


def guardar_perfil(contexto_usuario: dict | None, datos: dict) -> None:
    if contexto_usuario and contexto_usuario.get("user_id"):
        from core.db import guardar_perfil_db
        guardar_perfil_db(contexto_usuario["user_id"], contexto_usuario["access_token"], datos)
        return

    st.session_state["perfil_invitado"] = datos


def formatear_perfil(perfil: dict) -> str:
    """
    Serializa el perfil como texto plano para incluir en prompts de IA.
    Fuente única para motor_ia.py y postulacion.py — evita duplicar el
    formato en varios lugares. Incluye todos los campos, incluso los
    que en el CV final se renderizan literales (formación, idiomas,
    etc.) — la IA los necesita como contexto de lectura para el
    resumen profesional y el análisis de match ATS, aunque no los
    redacte directamente.
    """
    partes = [
        f"Ciudad: {perfil.get('ciudad', '')}",
        f"Años de experiencia: {perfil.get('anos_experiencia', 0)}",
        f"Nivel: {perfil.get('seniority', '')}",
        f"Competencias técnicas: {', '.join(lineas_no_vacias(perfil.get('competencias_tecnicas', '')))}",
        f"Habilidades blandas: {', '.join(lineas_no_vacias(perfil.get('habilidades_blandas', '')))}",
    ]

    experiencia = perfil.get("experiencia_laboral") or []
    if experiencia:
        partes.append("Experiencia laboral:")
        for trabajo in experiencia:
            rango = trabajo.get("fecha_fin") or ("Actualidad" if trabajo.get("actualidad") else "")
            partes.append(
                f"- {trabajo.get('cargo', '')} en {trabajo.get('empresa', '')} "
                f"({trabajo.get('fecha_inicio', '')} - {rango}): {trabajo.get('funciones', '')}"
            )

    formacion = perfil.get("formacion_academica") or []
    if formacion:
        partes.append("Formación académica:")
        for estudio in formacion:
            partes.append(
                f"- {estudio.get('titulo', '')} en {estudio.get('institucion', '')} "
                f"({estudio.get('fecha_inicio', '')} - {estudio.get('fecha_fin', '')})"
            )

    idiomas = perfil.get("idiomas") or []
    if idiomas:
        partes.append(
            "Idiomas: " + ", ".join(f"{i.get('idioma', '')}: {i.get('nivel', '')}" for i in idiomas)
        )

    return "\n".join(partes)
