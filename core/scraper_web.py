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

            # Extraer sueldo o valores por defecto
            elemento_sueldo = tarjeta.select_one("p.fs16 span.salario") or tarjeta.select_one("span.tag_salary")
            texto_sueldo = elemento_sueldo.get_text(strip=True) if elemento_sueldo else ""
            if not texto_sueldo or "convenir" in texto_sueldo.lower():
                sueldo = "No especifica sueldo"
            else:
                sueldo = texto_sueldo

            # Extraer jornada o tipo de contrato si viene indicado
            elemento_jornada = tarjeta.select_one("span.tag_jornada") or tarjeta.select_one("p.fs13 .i_time")
            jornada = elemento_jornada.get_text(strip=True) if elemento_jornada else "No especifica horario"

            titulo = elemento_titulo.get_text(strip=True)
            link = elemento_titulo.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://www.computrabajo.cl{link}"

            empresa_val = elemento_empresa.get_text(strip=True) if elemento_empresa else ""
            ubicacion_val = elemento_ubicacion.get_text(strip=True) if elemento_ubicacion else ""

            resultados.append({
                "titulo": titulo,
                "empresa": empresa_val if empresa_val else "No especifica empresa",
                "ubicacion": ubicacion_val if ubicacion_val else "No especifica ubicación",
                "modalidad": "Remoto" if es_remoto else "Presencial / Híbrido",
                "sueldo": sueldo,
                "jornada": jornada,
                "publicado": elemento_publicado.get_text(strip=True) if elemento_publicado else "Reciente",
                "link": link,
            })

    return resultados


def buscar_chiletrabajos(palabra_clave: str, cantidad_paginas: int = 1) -> list[dict]:
    """
    Busca ofertas reales en ChileTrabajos para la palabra clave dada.
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
            empresa = "No especifica empresa"
            if elemento_empresa_ubicacion is not None:
                texto_meta = elemento_empresa_ubicacion.get_text(strip=True)
                empresa = texto_meta.split(",")[0].strip() or "No especifica empresa"

            # Chiletrabajos indica la modalidad o sueldo en tags secundarios
            elemento_extra = tarjeta.select_one("span.salary") or tarjeta.select_one("span.type")
            texto_extra = elemento_extra.get_text(strip=True) if elemento_extra else ""
            
            sueldo = "No especifica sueldo"
            if "$" in texto_extra or "CLP" in texto_extra or any(c.isdigit() for c in texto_extra):
                sueldo = texto_extra
            
            link = elemento_titulo.get("href", "")
            if link and not link.startswith("http"):
                link = f"https://www.chiletrabajos.cl{link}"

            ubicacion_val = elemento_ubicacion.get_text(strip=True) if elemento_ubicacion else ""

            resultados.append({
                "titulo": elemento_titulo.get_text(strip=True),
                "empresa": empresa if empresa else "No especifica empresa",
                "ubicacion": ubicacion_val if ubicacion_val else "No especifica ubicación",
                "modalidad": "No especifica modalidad",
                "sueldo": sueldo,
                "jornada": "No especifica horario",
                "publicado": metas[1].get_text(strip=True) if len(metas) > 1 else "Reciente",
                "link": link,
            })

    return resultados


def buscar_getonbrd(palabra_clave: str, cantidad_paginas: int = 1) -> list[dict]:
    """
    Busca empleos en Getonbrd usando su API pública REST oficial.
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
            es_remoto = attr.get("remote", False)
            modalidad = "Remoto" if es_remoto else "Presencial / Híbrido"

            paises = attr.get("countries") or []
            ubicacion = ", ".join(paises) if paises else "No especifica ubicación"

            # Parsear sueldo si GetOnBrd lo expone en min_salary/max_salary
            min_sal = attr.get("min_salary")
            max_sal = attr.get("max_salary")
            if min_sal and max_sal:
                sueldo = f"${min_sal:,} - ${max_sal:,} USD".replace(",", ".")
            else:
                sueldo = "No especifica sueldo"

            link = item.get("links", {}).get("public_url", "")

            publicado = "Reciente"
            timestamp = attr.get("published_at")
            if timestamp:
                publicado = datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y")

            resultados.append({
                "titulo": titulo,
                "empresa": "No especifica empresa",
                "ubicacion": ubicacion,
                "modalidad": modalidad,
                "sueldo": sueldo,
                "jornada": "Full-Time",
                "publicado": publicado,
                "link": link,
            })

    return resultados

