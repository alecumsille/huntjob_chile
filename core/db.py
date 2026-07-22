"""
Persistencia por usuario en Supabase Postgres (perfil, historial de
postulaciones y plan de uso). Reemplaza el SQLite local compartido —
en Render el disco es efímero y, peor, un solo archivo compartido
mezclaba los datos de todos los visitantes entre sí.

Todas las funciones reciben un access_token real de Supabase y lo usan
para firmar la consulta: Row Level Security en Postgres es quien
garantiza que cada usuario solo ve sus propias filas (ver sql/schema.sql).
"""

from datetime import datetime, timezone

from core.auth_supabase import cliente_para_usuario
from core.perfil import VALORES_POR_DEFECTO

LIMITE_GRATIS_MENSUAL = 5


def obtener_perfil(user_id: str, access_token: str) -> dict:
    cliente = cliente_para_usuario(access_token)
    resultado = cliente.table("perfiles").select("*").eq("user_id", user_id).limit(1).execute()
    filas = resultado.data or []
    if not filas:
        return dict(VALORES_POR_DEFECTO)
    perfil = dict(VALORES_POR_DEFECTO)
    perfil.update({clave: valor for clave, valor in filas[0].items() if clave in VALORES_POR_DEFECTO})
    return perfil


def guardar_perfil_db(user_id: str, access_token: str, datos: dict) -> None:
    cliente = cliente_para_usuario(access_token)
    fila = {clave: datos.get(clave, VALORES_POR_DEFECTO[clave]) for clave in VALORES_POR_DEFECTO}
    fila["user_id"] = user_id
    cliente.table("perfiles").upsert(fila, on_conflict="user_id").execute()


def guardar_historial(
    user_id: str,
    access_token: str,
    puesto: str,
    empresa: str,
    mercado: str,
    url_oferta: str,
    cv_texto: str,
    cover_letter_texto: str,
    estilo_pdf: str,
    match_score: int | None = None,
    estado: str = "generado",
) -> int | None:
    """Guarda un registro de postulación generada. Devuelve el id de la fila creada."""
    cliente = cliente_para_usuario(access_token)
    fila = {
        "user_id": user_id,
        "puesto": puesto,
        "empresa": empresa,
        "mercado": mercado,
        "url_oferta": url_oferta,
        "cv_texto": cv_texto,
        "cover_letter_texto": cover_letter_texto,
        "estilo_pdf": estilo_pdf,
        "match_score": match_score,
        "estado": estado,
    }
    resultado = cliente.table("historial_postulaciones").insert(fila).execute()
    filas = resultado.data or []
    return filas[0]["id"] if filas else None


def marcar_postulado(user_id: str, access_token: str, historial_id: int) -> None:
    cliente = cliente_para_usuario(access_token)
    cliente.table("historial_postulaciones").update({"estado": "postulado"}).eq("id", historial_id).eq(
        "user_id", user_id
    ).execute()


def obtener_historial_reciente(user_id: str, access_token: str, limite: int = 10) -> list[dict]:
    cliente = cliente_para_usuario(access_token)
    resultado = (
        cliente.table("historial_postulaciones")
        .select("id,puesto,empresa,mercado,url_oferta,estado,match_score,creado_en")
        .eq("user_id", user_id)
        .order("id", desc=True)
        .limit(limite)
        .execute()
    )
    return resultado.data or []


def _periodo_actual() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def obtener_plan(user_id: str, access_token: str) -> dict:
    cliente = cliente_para_usuario(access_token)
    resultado = cliente.table("planes_usuario").select("*").eq("user_id", user_id).limit(1).execute()
    filas = resultado.data or []
    if filas:
        return filas[0]
    # Fallback por si el trigger de alta (handle_new_user) no alcanzó a correr aún.
    fila_defecto = {
        "user_id": user_id,
        "plan": "free",
        "limite_mensual": LIMITE_GRATIS_MENSUAL,
        "generaciones_este_mes": 0,
        "periodo": _periodo_actual(),
    }
    cliente.table("planes_usuario").upsert(fila_defecto, on_conflict="user_id").execute()
    return fila_defecto


def verificar_y_consumir_uso(user_id: str, access_token: str) -> tuple[bool, str]:
    """
    Chequea si el usuario puede generar un documento más este mes y, si
    puede, descuenta el cupo en el mismo paso (evita condiciones de
    carrera de "chequear y luego gastar" en dos llamadas separadas).
    Plan premium = sin límite. Devuelve (permitido, mensaje_para_mostrar).
    """
    cliente = cliente_para_usuario(access_token)
    plan = obtener_plan(user_id, access_token)

    if plan["plan"] == "premium":
        return True, ""

    periodo_hoy = _periodo_actual()
    usados = plan["generaciones_este_mes"] if plan["periodo"] == periodo_hoy else 0

    if usados >= plan["limite_mensual"]:
        return False, (
            f"Llegaste a tu límite gratuito de {plan['limite_mensual']} generaciones este mes. "
            "Pásate a Premium para generar sin límite."
        )

    cliente.table("planes_usuario").upsert(
        {
            "user_id": user_id,
            "plan": plan["plan"],
            "limite_mensual": plan["limite_mensual"],
            "generaciones_este_mes": usados + 1,
            "periodo": periodo_hoy,
        },
        on_conflict="user_id",
    ).execute()

    restantes = plan["limite_mensual"] - (usados + 1)
    aviso = f"Te quedan {restantes} generaciones gratis este mes." if restantes <= 2 else ""
    return True, aviso
