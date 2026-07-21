import os
import streamlit as st

from core.scraper_web import extraer_texto_url, ErrorScraping
from core.motor_ia import generar_texto, ErrorIA
from core.generador_pdf import generar_pdf, sanear_nombre_archivo
from core.portales import PORTALES, buscar_en_todos

st.set_page_config(page_title="HuntJob Chile", layout="wide")

st.title("HuntJob Chile")
st.caption("Motor de postulaciones: extracción de oferta, análisis con IA (Gemini) y generación de PDF.")

CARPETA_SALIDA = "salidas_pdf"
os.makedirs(CARPETA_SALIDA, exist_ok=True)

seccion = st.sidebar.radio("Panel", ["Generador por URL", "Buscador de Vacantes"])

# -------------------------------------------------------------
# SECCIÓN 1: GENERADOR DIRECTO POR URL
# -------------------------------------------------------------
if seccion == "Generador por URL":
    st.subheader("Generación de CV y Cover Letter desde una oferta puntual")

    url_oferta = st.text_input("Link de la oferta de trabajo (Computrabajo, LinkedIn, etc.):")

    if "texto_extraido" not in st.session_state:
        st.session_state.texto_extraido = ""
    if "puesto_detectado" not in st.session_state:
        st.session_state.puesto_detectado = ""

    if url_oferta and st.button("Leer oferta y detectar cargo"):
        with st.spinner("Extrayendo contenido de la URL..."):
            try:
                st.session_state.texto_extraido = extraer_texto_url(url_oferta)
            except ErrorScraping as e:
                st.error(f"No se pudo leer la oferta: {e}")
                st.stop()

        with st.spinner("Detectando cargo con Gemini..."):
            try:
                prompt_detectar_cargo = (
                    "Extrae únicamente el título exacto del puesto de trabajo de la siguiente oferta. "
                    "No agregues explicaciones, comillas ni texto adicional. Responde solo el nombre del cargo."
                )
                st.session_state.puesto_detectado = generar_texto(
                    prompt_detectar_cargo, st.session_state.texto_extraido
                )
            except ErrorIA as e:
                st.error(f"Fallo en la capa de IA: {e}")
                st.stop()

    puesto_objetivo = st.text_input(
        "Puesto detectado (editable):",
        value=st.session_state.puesto_detectado,
    )
    mercado_destino = st.selectbox(
        "Mercado objetivo:", ["Chile", "Alemania / Europa", "UK", "USA", "Remoto Global"]
    )

    if st.button("Generar CV y Cover Letter"):
        if not st.session_state.texto_extraido:
            st.error("Primero extrae el contenido de una oferta con el botón anterior.")
            st.stop()
        if not puesto_objetivo.strip():
            st.error("El campo de puesto objetivo no puede estar vacío.")
            st.stop()

        with st.spinner("Redactando documentos con Gemini..."):
            try:
                prompt_cv = (
                    f"Actúa como experto en ingeniería de software. Analiza la oferta para {puesto_objetivo} "
                    f"en {mercado_destino}. Genera un extracto de CV optimizado enfocado en Python, "
                    f"arquitectura backend y automatización, sin relleno."
                )
                prompt_cover = (
                    f"Actúa como desarrollador senior en Python. Escribe una Cover Letter directa y sin rodeos "
                    f"para {puesto_objetivo} en {mercado_destino}. Firma con el nombre Ale Cumsille."
                )

                cv_adaptado = generar_texto(prompt_cv, st.session_state.texto_extraido)
                cover_letter_adaptada = generar_texto(prompt_cover, st.session_state.texto_extraido)
            except ErrorIA as e:
                st.error(f"Fallo generando el contenido: {e}")
                st.stop()

        cargo_limpio = sanear_nombre_archivo(puesto_objetivo)
        ruta_cv = os.path.join(CARPETA_SALIDA, f"CV_Ale_Cumsille_{cargo_limpio}.pdf")
        ruta_cl = os.path.join(CARPETA_SALIDA, f"CoverLetter_Ale_Cumsille_{cargo_limpio}.pdf")

        try:
            generar_pdf(ruta_cv, cv_adaptado, f"CV - {puesto_objetivo}")
            generar_pdf(ruta_cl, cover_letter_adaptada, f"Cover Letter - {puesto_objetivo}")
        except ValueError as e:
            st.error(f"Fallo generando el PDF: {e}")
            st.stop()

        st.success("Documentos generados correctamente.")

        columna_izquierda, columna_derecha = st.columns(2)
        with columna_izquierda:
            with open(ruta_cv, "rb") as archivo_cv:
                st.download_button(
                    "Descargar CV (PDF)",
                    data=archivo_cv.read(),
                    file_name=os.path.basename(ruta_cv),
                    mime="application/pdf",
                )
        with columna_derecha:
            with open(ruta_cl, "rb") as archivo_cl:
                st.download_button(
                    "Descargar Cover Letter (PDF)",
                    data=archivo_cl.read(),
                    file_name=os.path.basename(ruta_cl),
                    mime="application/pdf",
                )

# -------------------------------------------------------------
# SECCIÓN 2: BUSCADOR MULTI-PORTAL DE VACANTES REALES
# -------------------------------------------------------------
elif seccion == "Buscador de Vacantes":
    st.subheader("Búsqueda de vacantes reales")

    columna_filtros, columna_resultados = st.columns([1, 3])

    with columna_filtros:
        palabra_clave = st.text_input("Palabra clave:", value="Python")
        cantidad_paginas = st.slider("Páginas a recorrer:", min_value=1, max_value=5, value=1)
        st.caption("Portales:")
        portales_marcados = [
            portal_id
            for portal_id, portal in PORTALES.items()
            if st.checkbox(portal["nombre"], value=True, key=f"portal_{portal_id}")
        ]

    with columna_resultados:
        if st.button("Buscar ofertas"):
            if not portales_marcados:
                st.error("Marca al menos un portal para buscar.")
                st.stop()

            with st.spinner(f"Consultando {len(portales_marcados)} portal(es) para '{palabra_clave}'..."):
                resultados, errores = buscar_en_todos(palabra_clave, cantidad_paginas, portales_marcados)

            for error in errores:
                st.warning(f"No se pudo buscar en {error}")

            if not resultados:
                st.info("No se encontraron ofertas para esa palabra clave en los portales seleccionados.")
            else:
                st.success(f"Se encontraron {len(resultados)} vacantes.")
                for oferta in resultados:
                    st.markdown(f"### {oferta['titulo']}")
                    detalle = f"Fuente: {oferta['fuente']} | Empresa: {oferta['empresa']} | Ubicación: {oferta['ubicacion']}"
                    if oferta.get("modalidad"):
                        detalle += f" | {oferta['modalidad']}"
                    if oferta.get("publicado"):
                        detalle += f" | Publicado: {oferta['publicado']}"
                    st.write(detalle)
                    if oferta["link"]:
                        st.markdown(f"[Ver oferta]({oferta['link']})")
                    st.markdown("---")
