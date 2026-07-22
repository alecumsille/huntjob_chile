"""
Gestión del perfil de usuario. Con cuenta real (Supabase), el perfil
vive en Postgres por user_id (ver core/db.py) — nunca en disco. En
modo invitado (sin cuenta) vive solo en st.session_state, que es
privado por navegador/pestaña y se pierde al cerrar sesión: nunca se
escribe a un archivo compartido en el servidor, que era la fuga de
datos entre visitantes que tenía la versión anterior.
"""

import streamlit as st

VALORES_POR_DEFECTO = {
    "nombre": "",
    "email": "",
    "telefono": "",
    "linkedin": "",
    "anos_experiencia": 0,
    "seniority": "Junior",
    "stack_principal": "",
    "logros_y_experiencia": "",
}

NIVELES_SENIORITY = ["Junior", "Semi Senior", "Senior", "Lead"]


def cargar_perfil(contexto_usuario: dict | None) -> dict:
    """
    contexto_usuario = {"user_id": ..., "access_token": ...} para una
    cuenta real, o None en modo invitado.
    """
    if contexto_usuario and contexto_usuario.get("user_id"):
        from core.db import obtener_perfil
        return obtener_perfil(contexto_usuario["user_id"], contexto_usuario["access_token"])

    perfil = dict(VALORES_POR_DEFECTO)
    perfil.update(st.session_state.get("perfil_invitado", {}))
    return perfil


def guardar_perfil(contexto_usuario: dict | None, datos: dict) -> None:
    if contexto_usuario and contexto_usuario.get("user_id"):
        from core.db import guardar_perfil_db
        guardar_perfil_db(contexto_usuario["user_id"], contexto_usuario["access_token"], datos)
        return

    st.session_state["perfil_invitado"] = datos


def formatear_perfil(perfil: dict) -> str:
    """
    Serializa el perfil como texto plano para incluir en prompts de IA.
    Fuente única para motor_ia.py y app.py — evita duplicar el formato
    en tres lugares distintos.
    """
    return (
        f"Años de experiencia: {perfil.get('anos_experiencia', 0)}\n"
        f"Nivel: {perfil.get('seniority', '')}\n"
        f"Stack principal: {perfil.get('stack_principal', '')}\n"
        f"Logros y experiencia: {perfil.get('logros_y_experiencia', '')}"
    )
