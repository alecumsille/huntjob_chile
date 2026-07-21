"""
Módulo de extracción web.
Responsable de: leer una URL de oferta puntual, y buscar vacantes reales
en Computrabajo Chile. Sin datos simulados: si el scraping falla, se
propaga la excepción con contexto claro (no se retorna una lista vacía
disfrazada de "sin resultados").
"""

from datetime import datetime

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


def buscar_computrabajo(palabra_clave: str, cantidad_paginas: int = 1) -> list[dict]:
    """
    Busca ofertas reales en Computrabajo Chile para la palabra clave dada.
    Devuelve una lista de dicts: {titulo, empresa, ubicacion, modalidad,
    publicado, link}.

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
            elemento_empresa = tarjeta.select_one("p.dFlex a")
            # La ubicación real vive en un p.fs16 sin link (el que sí tiene
            # link de empresa es el de arriba). No confundir con p.fs13,
            # que es el tiempo relativo de publicación ("Hace X minutos").
            elemento_ubicacion = tarjeta.select_one("p.fs16 span.mr10")
            elemento_publicado = tarjeta.select_one("p.fs13.fc_aux")
            es_remoto = tarjeta.select_one("div.fs13 .i_home") is not None

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
                "modalidad": "Remoto" if es_remoto else "",
                "publicado": elemento_publicado.get_text(strip=True) if elemento_publicado else "",
                "link": link,
            })

    return resultados


def buscar_chiletrabajos(palabra_clave: str, cantidad_paginas: int = 1) -> list[dict]:
    """
    Busca ofertas reales en ChileTrabajos para la palabra clave dada.

    El formulario de búsqueda del sitio usa nombres de campo numéricos
    heredados ("2" para la palabra clave, "f"="2" fijo) en vez de nombres
    descriptivos — no es un placeholder, se verificó en vivo contra el
    HTML real del formulario en /encuentra-un-empleo.
    """
    resultados = []
    TAMANO_PAGINA = 30

    for pagina in range(1, cantidad_paginas + 1):
        offset = (pagina - 1) * TAMANO_PAGINA
        ruta = "/encuentra-un-empleo" if offset == 0 else f"/encuentra-un-empleo/{offset}"
        url_busqueda = f"https://www.chiletrabajos.cl{ruta}"

        try:
            respuesta = requests.get(
                url_busqueda, params={"2": palabra_clave, "f": "2"}, headers=HEADERS, timeout=TIMEOUT_SEGUNDOS
            )
        except requests.exceptions.RequestException as e:
            raise ErrorScraping(f"Fallo de red buscando en ChileTrabajos (página {pagina}): {e}")

        if respuesta.status_code != 200:
            raise ErrorScraping(
                f"ChileTrabajos respondió HTTP {respuesta.status_code} en la página {pagina}. "
                f"Puede ser bloqueo por rate-limit o cambio de URL."
            )

        soup = BeautifulSoup(respuesta.text, "html.parser")
        tarjetas = soup.select("div.job-item")

        if not tarjetas:
            break

        for tarjeta in tarjetas:
            elemento_titulo = tarjeta.select_one("h2.title a")
            if elemento_titulo is None:
                continue

            metas = tarjeta.select("h3.meta")
            elemento_empresa_ubicacion = metas[0] if metas else None
            elemento_ubicacion = (
                elemento_empresa_ubicacion.select_one("a") if elemento_empresa_ubicacion else None
            )
            empresa = "No especificada"
            if elemento_empresa_ubicacion is not None:
                texto_meta = elemento_empresa_ubicacion.get_text(strip=True)
                empresa = texto_meta.split(",")[0].strip() or "No especificada"

            link = elemento_titulo.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://www.chiletrabajos.cl{link}"

            resultados.append({
                "titulo": elemento_titulo.get_text(strip=True),
                "empresa": empresa,
                "ubicacion": elemento_ubicacion.get_text(strip=True) if elemento_ubicacion else "No especificada",
                "modalidad": "",
                "publicado": metas[1].get_text(strip=True) if len(metas) > 1 else "",
                "link": link,
            })

    return resultados


def buscar_getonbrd(palabra_clave: str, cantidad_paginas: int = 1) -> list[dict]:
    """
    Busca empleos en Getonbrd usando su API pública REST oficial (libre de
    bloqueos WAF/Cloudflare que sí afectan al scraping directo del HTML).
    Devuelve lista de dicts compatibles con el dispatcher.

    IMPORTANTE — limitación real de este endpoint: "company" en attributes
    es solo una referencia JSON:API ({"data": {"id": ..., "type": "company"}}),
    sin nombre embebido. El endpoint de detalle por job (/api/v0/jobs/{id})
    que sí tendría el nombre completo devuelve 401 sin autenticación —
    verificado en vivo. "empresa" queda honestamente "No especificada" en
    vez de inventar un nombre o parsearlo del slug del id.
    """
    resultados = []

    for pagina in range(1, cantidad_paginas + 1):
        url_api = f"https://www.getonbrd.com/api/v0/search/jobs?query={palabra_clave}&page={pagina}&per_page=20"

        try:
            respuesta = requests.get(url_api, headers=HEADERS, timeout=TIMEOUT_SEGUNDOS)
        except requests.exceptions.RequestException as e:
            raise ErrorScraping(f"Fallo de red buscando en Getonbrd (página {pagina}): {e}")

        if respuesta.status_code != 200:
            raise ErrorScraping(f"Getonbrd respondió HTTP {respuesta.status_code} en la página {pagina}.")

        cuerpo = respuesta.json()
        datos = cuerpo.get("data", [])
        if not datos:
            break

        for item in datos:
            attr = item.get("attributes", {})
            titulo = attr.get("title", "")
            modalidad = "Remoto" if attr.get("remote") else "Presencial/Híbrido"

            paises = attr.get("countries") or []
            ubicacion = ", ".join(paises) if paises else "No especificada"

            # El link real vive en item["links"]["public_url"], no en
            # attributes — attr.get("url") siempre devolvía vacío.
            link = item.get("links", {}).get("public_url", "")

            # published_at es un timestamp Unix.
            publicado = ""
            timestamp = attr.get("published_at")
            if timestamp:
                publicado = datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y")

            resultados.append({
                "titulo": titulo,
                "empresa": "No especificada",
                "ubicacion": ubicacion,
                "modalidad": modalidad,
                "publicado": publicado,
                "link": link,
            })

    return resultados

