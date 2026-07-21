"""
Dispatcher de búsqueda multi-portal. Cada portal es independiente: si uno
falla, los demás igual devuelven resultados (el error se reporta aparte,
nunca tumba el batch completo).
"""

from core.scraper_web import (
    buscar_computrabajo,
    buscar_chiletrabajos,
    buscar_getonbrd,
    ErrorScraping,
)

PORTALES = {
    "computrabajo": {
        "nombre": "Computrabajo Chile",
        "url": "https://www.computrabajo.cl",
        "funcion": buscar_computrabajo,
    },
    "chiletrabajos": {
        "nombre": "ChileTrabajos",
        "url": "https://www.chiletrabajos.cl",
        "funcion": buscar_chiletrabajos,
    },
    "getonbrd": {
        "nombre": "Get on Board",
        "url": "https://www.getonbrd.com",
        "funcion": buscar_getonbrd,
    },
}


def buscar_en_portal(portal_id: str, palabra_clave: str, paginas: int = 1) -> tuple[list[dict], str | None]:
    """
    Busca en un solo portal. Devuelve (resultados, error). error es None si
    todo salió bien; si no, resultados es una lista vacía y error trae el
    detalle exacto de qué falló.
    """
    portal = PORTALES.get(portal_id)
    if not portal:
        return [], f"Portal desconocido: {portal_id}"

    try:
        resultados = portal["funcion"](palabra_clave, paginas)
    except ErrorScraping as e:
        return [], str(e)
    except Exception as e:
        return [], f"Error inesperado en {portal['nombre']}: {e}"

    for resultado in resultados:
        resultado["fuente"] = portal["nombre"]

    return resultados, None


def buscar_en_todos(
    palabra_clave: str, paginas: int = 1, portales_seleccionados: list[str] | None = None
) -> tuple[list[dict], list[str]]:
    """
    Busca en varios portales. Un portal que falla no bloquea a los demás:
    devuelve (todos_los_resultados_de_los_portales_que_funcionaron, errores).
    """
    if portales_seleccionados is None:
        portales_seleccionados = list(PORTALES.keys())

    todos = []
    errores = []
    for portal_id in portales_seleccionados:
        resultados, error = buscar_en_portal(portal_id, palabra_clave, paginas)
        if error:
            nombre = PORTALES.get(portal_id, {}).get("nombre", portal_id)
            errores.append(f"{nombre}: {error}")
        todos.extend(resultados)

    return todos, errores
