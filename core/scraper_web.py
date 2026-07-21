"""
Módulo de extracción web.
Responsable de: leer una URL de oferta puntual, y buscar vacantes reales
en Computrabajo Chile. Sin datos simulados: si el scraping falla, se
propaga la excepción con contexto claro (no se retorna una lista vacía
disfrazada de "sin resultados").
"""

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

TIMEOUT_SEGUNDOS = 10


class ErrorScraping(Exception):
    """Excepción específica para fallos de extracción web, para no confundir
    con errores de red genéricos de requests."""
    pass


def extraer_texto_url(url: str) -> str:
    """
    Descarga una URL de oferta laboral y devuelve el texto plano de la página,
    sin scripts ni estilos. Lanza ErrorScraping con el detalle exacto del fallo
    en vez de devolver un string de error silencioso.
    """
    try:
        respuesta = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.Timeout:
        raise ErrorScraping(f"Timeout ({TIMEOUT_SEGUNDOS}s) al conectar con {url}")
    except requests.exceptions.ConnectionError as e:
        raise ErrorScraping(f"No se pudo establecer conexión con {url}: {e}")
    except requests.exceptions.RequestException as e:
        raise ErrorScraping(f"Error de red al pedir {url}: {e}")

    if respuesta.status_code != 200:
        raise ErrorScraping(f"{url} respondió con código HTTP {respuesta.status_code}")

    soup = BeautifulSoup(respuesta.text, "html.parser")
    for etiqueta in soup(["script", "style", "noscript"]):
        etiqueta.extract()

    texto = soup.get_text(separator=" ", strip=True)
    if not texto:
        raise ErrorScraping(f"La página {url} no devolvió texto extraíble (posible bloqueo o JS puro)")

    return texto


def buscar_ofertas_computrabajo(palabra_clave: str, cantidad_paginas: int = 1) -> list[dict]:
    """
    Busca ofertas reales en Computrabajo Chile para la palabra clave dada.
    Devuelve una lista de dicts: {titulo, empresa, ubicacion, link}.

    IMPORTANTE: Computrabajo cambia su HTML con frecuencia. Si esta función
    empieza a devolver listas vacías de golpe, lo primero es inspeccionar
    el HTML actual del sitio (F12 en el navegador) y actualizar los
    selectores CSS de más abajo — no asumir que "no hay ofertas".
    """
    resultados = []
    palabra_url = palabra_clave.strip().replace(" ", "-")

    for pagina in range(1, cantidad_paginas + 1):
        url_busqueda = f"https://www.computrabajo.cl/trabajo-de-{palabra_url}?p={pagina}"

        try:
            respuesta = requests.get(url_busqueda, headers=HEADERS, timeout=TIMEOUT_SEGUNDOS)
        except requests.exceptions.RequestException as e:
            raise ErrorScraping(f"Fallo de red buscando en Computrabajo (página {pagina}): {e}")

        if respuesta.status_code != 200:
            raise ErrorScraping(
                f"Computrabajo respondió HTTP {respuesta.status_code} en la página {pagina}. "
                f"Puede ser bloqueo por rate-limit o cambio de URL."
            )

        soup = BeautifulSoup(respuesta.text, "html.parser")

        # Selectores actuales de Computrabajo (verificado en su estructura pública de listado).
        # Si cambian el markup, este es el punto exacto a corregir.
        tarjetas = soup.select("article.box_offer")

        if not tarjetas:
            # No es error fatal: puede ser que esta página ya no tenga más resultados.
            break

        for tarjeta in tarjetas:
            elemento_titulo = tarjeta.select_one("h2 a")
            elemento_empresa = tarjeta.select_one("p.dFlex a, span.fs16")
            elemento_ubicacion = tarjeta.select_one("p.fs13, span.fs13")

            if elemento_titulo is None:
                # Tarjeta con estructura inesperada: se salta, pero no rompe todo el batch.
                continue

            titulo = elemento_titulo.get_text(strip=True)
            link = elemento_titulo.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://www.computrabajo.cl{link}"

            resultados.append({
                "titulo": titulo,
                "empresa": elemento_empresa.get_text(strip=True) if elemento_empresa else "No especificada",
                "ubicacion": elemento_ubicacion.get_text(strip=True) if elemento_ubicacion else "No especificada",
                "link": link,
            })

    return resultados
