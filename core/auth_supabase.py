"""
Cliente de Supabase para validar sesiones reales de OAuth y ejecutar
consultas a Postgres respetando Row Level Security (RLS) por usuario.

No usamos la Service Role Key en ningún momento: cada consulta se firma
con el access_token del propio usuario autenticado, así que RLS filtra
automáticamente por auth.uid() sin que el backend necesite privilegios
de administrador.
"""

import logging
import os

import streamlit as st
from supabase import create_client, Client

logger = logging.getLogger(__name__)


def _obtener_config(nombre_var: str, valor_defecto: str = "") -> str:
    valor = os.environ.get(nombre_var, "").strip()
    if not valor:
        try:
            valor = st.secrets.get(nombre_var, "").strip()
        except Exception:
            valor = ""
    return valor or valor_defecto


SUPABASE_URL = _obtener_config("SUPABASE_URL", "https://oonkwgfawfyqtrndshhu.supabase.co")
SUPABASE_ANON_KEY = _obtener_config("SUPABASE_ANON_KEY")


@st.cache_resource
def _cliente_base() -> Client:
    if not SUPABASE_ANON_KEY:
        raise RuntimeError("Falta configurar SUPABASE_ANON_KEY en st.secrets o variables de entorno.")
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def obtener_usuario_desde_token(access_token: str) -> dict | None:
    """
    Valida un access_token contra Supabase Auth. Devuelve
    {"id", "email", "proveedor"} si es válido, o None si el token es
    inválido/expiró — nunca confía en el valor a ojo, siempre lo
    verifica contra el servidor de Supabase.
    """
    if not access_token:
        return None
    try:
        respuesta = _cliente_base().auth.get_user(access_token)
    except Exception:
        logger.exception("Fallo al validar access_token contra Supabase Auth")
        return None
    usuario = getattr(respuesta, "user", None)
    if not usuario:
        logger.warning("Supabase respondio sin 'user' para el access_token recibido")
        return None
    proveedor = (usuario.app_metadata or {}).get("provider", "Cuenta")
    return {"id": usuario.id, "email": usuario.email, "proveedor": proveedor.capitalize()}


def cliente_para_usuario(access_token: str) -> Client:
    """
    Cliente de Postgres firmado con el JWT del usuario — todas las
    consultas quedan automáticamente acotadas por las políticas RLS
    (auth.uid() = user_id) definidas en sql/schema.sql.
    """
    cliente = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    cliente.postgrest.auth(access_token)
    return cliente


def cerrar_sesion(access_token: str) -> None:
    try:
        cliente = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        cliente.postgrest.auth(access_token)
        cliente.auth.sign_out()
    except Exception:
        pass
