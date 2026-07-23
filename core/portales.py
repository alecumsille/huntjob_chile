"""
Dispatcher de búsqueda multi-portal. Cada portal es independiente: si uno
falla, los demás igual devuelven resultados (el error se reporta aparte,
nunca tumba el batch completo).
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from core.scraper_web import (
    buscar_computrabajo,
    buscar_chiletrabajos,
    buscar_getonbrd,
    buscar_linkedin,
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
    "linkedin": {
        "nombre": "LinkedIn Jobs Chile",
        "url": "https://www.linkedin.com/jobs",
        "funcion": buscar_linkedin,
    },
}


def buscar_en_portal(portal_id: str, palabra_clave: str, paginas: int = 1) -> tuple[list[dict], str | None]:
    """
    Busca en un solo portal. Devuelve (resultados, error).
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
    Busca simultáneamente en múltiples portales usando ejecución paralela (ThreadPoolExecutor).
    """
    if portales_seleccionados is None:
        portales_seleccionados = list(PORTALES.keys())

    todos = []
    errores = []

    with ThreadPoolExecutor(max_workers=min(len(portales_seleccionados), 6)) as executor:
        futuros = {
            executor.submit(buscar_en_portal, p_id, palabra_clave, paginas): p_id
            for p_id in portales_seleccionados
        }

        for futuro in as_completed(futuros):
            p_id = futuros[futuro]
            try:
                resultados, error = futuro.result()
                if error:
                    nombre = PORTALES.get(p_id, {}).get("nombre", p_id)
                    errores.append(f"{nombre}: {error}")
                todos.extend(resultados)
            except Exception as e:
                nombre = PORTALES.get(p_id, {}).get("nombre", p_id)
                errores.append(f"{nombre}: Error en hilo de ejecución: {e}")

    return todos, errores
