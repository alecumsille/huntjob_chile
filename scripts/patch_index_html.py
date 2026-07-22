"""
Streamlit no deja fijar meta tags Open Graph en el HTML que sirve el
servidor: solo expone su template estático (index.html), y todo lo que
el código Python de la app agrega vive dentro del <div id="root"> que
arma React en el navegador — invisible para los bots que arman la
vista previa de un link (WhatsApp, Telegram, Facebook, Slack, etc. leen
el HTML crudo, no ejecutan JavaScript).

Este script parchea el index.html estático de Streamlit al construir la
imagen Docker, así el título y las etiquetas Open Graph ya vienen en el
HTML que se sirve, antes de que corra cualquier JS.

El crawler de Facebook pide el HTML con un header Range (ej. primeros
~1KB) — confirmado con el Sharing Debugger devolviendo código 206.
Si las etiquetas quedan después del bloque de comentario de licencia de
Streamlit (~800 bytes), el crawler nunca llega a leerlas. Por eso se
sacan el comentario de licencia y se ponen las etiquetas lo más arriba
posible en <head>, justo después del charset.
"""

import pathlib
import re

import streamlit

INDEX_PATH = pathlib.Path(streamlit.__file__).parent / "static" / "index.html"

OG_TAGS = """<title>HuntJob Chile</title>
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://huntjob.cumsille.me/">
    <meta property="og:title" content="HuntJob Chile — Plataforma Inteligente de Empleos">
    <meta property="og:description" content="Busca ofertas en todos los portales de empleo de Chile y genera tu CV optimizado con IA.">
    <meta property="og:image" content="https://raw.githubusercontent.com/alecumsille/huntjob_chile/main/assets/icon.png">
    <meta property="fb:app_id" content="1062967339642692">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="HuntJob Chile — Plataforma Inteligente de Empleos">
    <meta name="twitter:description" content="Busca ofertas en todos los portales de empleo de Chile y genera tu CV optimizado con IA.">
    <meta name="twitter:image" content="https://raw.githubusercontent.com/alecumsille/huntjob_chile/main/assets/icon.png">
"""

MARCA_TITLE = "<title>Streamlit</title>"
MARCA_HTML = '<html lang="en">'
HTML_CON_NAMESPACES = '<html lang="es" xmlns:og="http://ogp.me/ns#" xmlns:fb="http://www.facebook.com/2008/fbml">'
MARCA_CHARSET = '<meta charset="UTF-8" />'
COMENTARIO_LICENCIA = re.compile(r"<!--.*?-->\s*", re.DOTALL)


def main() -> None:
    html = INDEX_PATH.read_text(encoding="utf-8")
    for marca in (MARCA_TITLE, MARCA_HTML, MARCA_CHARSET):
        if marca not in html:
            raise RuntimeError(
                f"No se encontró '{marca}' en {INDEX_PATH} — el template de "
                "Streamlit puede haber cambiado en esta versión, revisar antes "
                "de seguir con el build."
            )

    # 1) Sacar el <title> original de su lugar original (se vuelve a poner,
    #    junto con el resto de las etiquetas OG, mas arriba en el paso 3).
    html = html.replace(MARCA_TITLE + "\n", "", 1)
    html = html.replace(MARCA_TITLE, "", 1)

    # 2) Sacar el bloque de comentario de licencia del principio del
    #    archivo — son ~800 bytes que empujan todo el resto del <head>
    #    fuera del rango que pide el crawler de Facebook.
    html = COMENTARIO_LICENCIA.sub("", html, count=1)

    # 3) Insertar las etiquetas OG lo mas arriba posible: justo despues
    #    del charset, antes de cualquier otra cosa.
    html = html.replace(MARCA_CHARSET, MARCA_CHARSET + "\n    " + OG_TAGS, 1)

    # 4) Namespaces og/fb en <html>, requeridos por el validador de
    #    Facebook para reconocer la propiedad fb:app_id.
    html = html.replace(MARCA_HTML, HTML_CON_NAMESPACES)

    INDEX_PATH.write_text(html, encoding="utf-8")
    print(f"OK: Open Graph parchado en {INDEX_PATH}")


if __name__ == "__main__":
    main()
