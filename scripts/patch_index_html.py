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
"""

import pathlib

import streamlit

INDEX_PATH = pathlib.Path(streamlit.__file__).parent / "static" / "index.html"

OG_TAGS = """<title>HuntJob Chile</title>
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://huntjob.cumsille.me/">
    <meta property="og:title" content="HuntJob Chile — Plataforma Inteligente de Empleos">
    <meta property="og:description" content="Busca ofertas en todos los portales de empleo de Chile y genera tu CV optimizado con IA.">
    <meta property="og:image" content="https://raw.githubusercontent.com/alecumsille/huntjob_chile/main/assets/icon.png">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="HuntJob Chile — Plataforma Inteligente de Empleos">
    <meta name="twitter:description" content="Busca ofertas en todos los portales de empleo de Chile y genera tu CV optimizado con IA.">
    <meta name="twitter:image" content="https://raw.githubusercontent.com/alecumsille/huntjob_chile/main/assets/icon.png">"""

MARCA = "<title>Streamlit</title>"


def main() -> None:
    html = INDEX_PATH.read_text(encoding="utf-8")
    if MARCA not in html:
        raise RuntimeError(
            f"No se encontró '{MARCA}' en {INDEX_PATH} — el template de "
            "Streamlit puede haber cambiado en esta versión, revisar antes "
            "de seguir con el build."
        )
    html = html.replace(MARCA, OG_TAGS)
    INDEX_PATH.write_text(html, encoding="utf-8")
    print(f"OK: Open Graph parchado en {INDEX_PATH}")


if __name__ == "__main__":
    main()
