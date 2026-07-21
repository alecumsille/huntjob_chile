import os
from datetime import datetime

import streamlit as st

from core.scraper_web import extraer_texto_url, ErrorScraping
from core.motor_ia import generar_texto, analizar_match, sugerir_respuesta, ErrorIA
from core.generador_pdf import generar_pdf, sanear_nombre_archivo
from core.portales import PORTALES, buscar_en_todos
from core.perfil import cargar_perfil, guardar_perfil, NIVELES_SENIORITY, formatear_perfil

st.set_page_config(page_title="HuntJob Chile", page_icon="assets/icon.png", layout="wide")


def _clave_configurada() -> str:
    """
    Devuelve la clave de acceso configurada vía st.secrets (solo aplica en
    un despliegue público, ej. Streamlit Community Cloud). En uso local o
    en la app de escritorio no hay secrets.toml, así que esto devuelve ""
    y la app no pide clave — el gate solo existe para el despliegue web.
    """
    try:
        return st.secrets.get("APP_PASSWORD", "")
    except Exception:
        return ""


clave_requerida = _clave_configurada()
if clave_requerida and not st.session_state.get("autenticado"):
    st.title("HuntJob Chile")
    clave_ingresada = st.text_input("Clave de acceso", type="password")
    if clave_ingresada:
        if clave_ingresada == clave_requerida:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave incorrecta.", icon=":material/error:")
    st.stop()

# Rotación horaria de paleta: 4 variantes pastel, una por franja horaria
# (hora % 4). El theme nativo de Streamlit (.streamlit/config.toml) es fijo
# por proceso, así que la única forma de cambiar colores sin reiniciar el
# servidor es inyectar CSS con la paleta de la hora actual.
PALETAS_PASTEL = [
    {"fondo": "#FFFDFE", "fondo_secundario": "#FCEEF3", "primario": "#C87FA0",
     "sidebar_fondo": "#EFF6FC", "sidebar_primario": "#5B9BD5"},  # rosado + celeste
    {"fondo": "#FDFEFC", "fondo_secundario": "#EAF7F0", "primario": "#6FBF95",
     "sidebar_fondo": "#F3F0FA", "sidebar_primario": "#9B8AC4"},  # menta + lavanda
    {"fondo": "#FFFEFC", "fondo_secundario": "#FBF0E6", "primario": "#E0A672",
     "sidebar_fondo": "#EAF3FB", "sidebar_primario": "#6FA8D8"},  # durazno + celeste
    {"fondo": "#FFFDFE", "fondo_secundario": "#F3EEFC", "primario": "#9B8AC4",
     "sidebar_fondo": "#FBF0F5", "sidebar_primario": "#D689A8"},  # lavanda + rosado
]

paleta_actual = PALETAS_PASTEL[datetime.now().hour % len(PALETAS_PASTEL)]
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {paleta_actual['fondo']};
    }}
    [data-testid="stSidebar"] {{
        background-color: {paleta_actual['sidebar_fondo']};
    }}
    div[data-testid="stForm"] {{
        background-color: {paleta_actual['fondo_secundario']};
    }}
    button[kind="primary"] {{
        background-color: {paleta_actual['primario']} !important;
        border-color: {paleta_actual['primario']} !important;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label div:first-child {{
        border-color: {paleta_actual['sidebar_primario']} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("HuntJob Chile")
st.caption("Motor de postulaciones: extracción de oferta, análisis con IA (Gemini) y generación de PDF.")

CARPETA_SALIDA = "salidas_pdf"
os.makedirs(CARPETA_SALIDA, exist_ok=True)

with st.sidebar:
    seccion = st.radio(
        "Panel",
        ["Generador por URL", "Buscador de Vacantes", "Mi Perfil", "Preguntas de Postulación", "FAQ"],
    )
    st.caption("HuntJob Chile")

# -------------------------------------------------------------
# SECCIÓN 1: GENERADOR DIRECTO POR URL
# -------------------------------------------------------------
if seccion == "Generador por URL":
    st.subheader("Generación de CV y Cover Letter desde una oferta puntual")

    perfil = cargar_perfil()
    if not perfil["nombre"]:
        st.warning(
            "No completaste tu perfil todavía — los documentos se van a firmar como \"Candidato/a\". "
            "Anda al tab \"Mi Perfil\" para completarlo.",
            icon=":material/warning:",
        )

    if "texto_extraido" not in st.session_state:
        st.session_state.texto_extraido = ""
    if "puesto_detectado" not in st.session_state:
        st.session_state.puesto_detectado = ""

    with st.container(border=True):
        url_oferta = st.text_input("Link de la oferta de trabajo (Computrabajo, LinkedIn, etc.)")

        if url_oferta and st.button("Leer oferta y detectar cargo", icon=":material/search:"):
            with st.spinner("Extrayendo contenido de la URL..."):
                try:
                    st.session_state.texto_extraido = extraer_texto_url(url_oferta)
                except ErrorScraping as e:
                    st.error(f"No se pudo leer la oferta: {e}", icon=":material/error:")
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
                    st.error(f"Fallo en la capa de IA: {e}", icon=":material/error:")
                    st.stop()

    with st.container(border=True):
        puesto_objetivo = st.text_input(
            "Puesto detectado (editable)",
            value=st.session_state.puesto_detectado,
        )
        mercado_destino = st.selectbox(
            "Mercado objetivo", ["Chile", "Alemania / Europa", "UK", "USA", "Remoto Global"]
        )

        if st.button("Generar CV y Cover Letter", icon=":material/description:", type="primary"):
            if not st.session_state.texto_extraido:
                st.error("Primero extrae el contenido de una oferta con el botón anterior.", icon=":material/error:")
                st.stop()
            if not puesto_objetivo.strip():
                st.error("El campo de puesto objetivo no puede estar vacío.", icon=":material/error:")
                st.stop()

            with st.spinner("Redactando documentos con Gemini..."):
                try:
                    contexto_perfil = formatear_perfil(perfil)
                    prompt_cv = (
                        f"Escribe ÚNICAMENTE el extracto de perfil profesional para un CV, en español, "
                        f"para el puesto de {puesto_objetivo} en {mercado_destino}. Basate en el stack y "
                        f"los logros reales del candidato de abajo — seleccioná solo lo que sea relevante "
                        f"para esta oferta puntual, no listes todo. NUNCA digas que el candidato domina o "
                        f"usa una tecnología que no esté textualmente en su 'Stack principal' de abajo, "
                        f"aunque la oferta la pida — si la oferta pide algo que el candidato no tiene, "
                        f"simplemente no lo menciones como si lo dominara. No inventes nada que no esté en "
                        f"el perfil. Un párrafo de 4 a 6 líneas, listo para pegar directo en un CV real, con "
                        f"las palabras clave técnicas relevantes para pasar filtros ATS. No agregues "
                        f"explicaciones, títulos, análisis de por qué funciona, consejos, ni ningún texto "
                        f"dirigido al candidato — solo el extracto en sí.\n\n"
                        f"Perfil del candidato:\n{contexto_perfil}"
                    )
                    nombre_firma = perfil["nombre"] or "Candidato/a"
                    prompt_cover = (
                        f"Escribe ÚNICAMENTE el cuerpo de una Cover Letter en español, directa y sin rodeos, "
                        f"para el puesto de {puesto_objetivo} en {mercado_destino}. Si el perfil de abajo "
                        f"tiene logros o experiencia cargada, mencioná como máximo uno concreto que calce "
                        f"con esta oferta puntual, en vez de lenguaje genérico de relleno — si no hay logros "
                        f"cargados, escribí sin inventar ninguno. NUNCA digas que el candidato domina o usa "
                        f"una tecnología que no esté textualmente en su 'Stack principal' de abajo, aunque la "
                        f"oferta la pida — en ese caso, podés mencionar disposición a aprenderla, nunca "
                        f"dominio que no tiene. Firma con el nombre {nombre_firma}. No agregues explicaciones, "
                        f"análisis, ni ningún texto que no sea la carta en sí.\n\n"
                        f"Perfil del candidato:\n{contexto_perfil}"
                    )

                    cv_adaptado = generar_texto(prompt_cv, st.session_state.texto_extraido)
                    cover_letter_adaptada = generar_texto(prompt_cover, st.session_state.texto_extraido)
                except ErrorIA as e:
                    st.error(f"Fallo generando el contenido: {e}", icon=":material/error:")
                    st.stop()

            cargo_limpio = sanear_nombre_archivo(puesto_objetivo)
            nombre_archivo = sanear_nombre_archivo(perfil["nombre"] or "candidato")
            ruta_cv = os.path.join(CARPETA_SALIDA, f"CV_{nombre_archivo}_{cargo_limpio}.pdf")
            ruta_cl = os.path.join(CARPETA_SALIDA, f"CoverLetter_{nombre_archivo}_{cargo_limpio}.pdf")

            try:
                generar_pdf(ruta_cv, cv_adaptado, "CV", puesto_objetivo, perfil)
                generar_pdf(ruta_cl, cover_letter_adaptada, "Cover Letter", puesto_objetivo, perfil)
            except ValueError as e:
                st.error(f"Fallo generando el PDF: {e}", icon=":material/error:")
                st.stop()

            st.success("Documentos generados correctamente.", icon=":material/check_circle:")

            with st.container(horizontal=True):
                with open(ruta_cv, "rb") as archivo_cv:
                    st.download_button(
                        "Descargar CV (PDF)",
                        data=archivo_cv.read(),
                        file_name=os.path.basename(ruta_cv),
                        mime="application/pdf",
                        icon=":material/download:",
                    )
                with open(ruta_cl, "rb") as archivo_cl:
                    st.download_button(
                        "Descargar Cover Letter (PDF)",
                        data=archivo_cl.read(),
                        file_name=os.path.basename(ruta_cl),
                        mime="application/pdf",
                        icon=":material/download:",
                    )

# -------------------------------------------------------------
# SECCIÓN 2: BUSCADOR MULTI-PORTAL DE VACANTES REALES
# -------------------------------------------------------------
elif seccion == "Buscador de Vacantes":
    st.subheader("Búsqueda de vacantes reales")

    nombres_portales = [portal["nombre"] for portal in PORTALES.values()]
    id_por_nombre = {portal["nombre"]: portal_id for portal_id, portal in PORTALES.items()}

    if "resultados_busqueda" not in st.session_state:
        st.session_state.resultados_busqueda = []
    if "errores_busqueda" not in st.session_state:
        st.session_state.errores_busqueda = []
    if "matches" not in st.session_state:
        st.session_state.matches = {}

    columna_filtros, columna_resultados = st.columns([1, 3])

    with columna_filtros:
        with st.container(border=True):
            palabra_clave = st.text_input("Palabra clave", value="Python")
            cantidad_paginas = st.slider("Páginas a recorrer", min_value=1, max_value=5, value=1)
            portales_elegidos = st.pills(
                "Portales",
                nombres_portales,
                selection_mode="multi",
                default=nombres_portales,
            )
            portales_marcados = [id_por_nombre[nombre] for nombre in portales_elegidos]
            buscar = st.button("Buscar ofertas", icon=":material/search:", type="primary")

    if buscar:
        if not portales_marcados:
            st.error("Marca al menos un portal para buscar.", icon=":material/error:")
            st.stop()

        with st.spinner(f"Consultando {len(portales_marcados)} portal(es) para '{palabra_clave}'..."):
            resultados, errores = buscar_en_todos(palabra_clave, cantidad_paginas, portales_marcados)

        st.session_state.resultados_busqueda = resultados
        st.session_state.errores_busqueda = errores
        st.session_state.matches = {}

    with columna_resultados:
        for error in st.session_state.errores_busqueda:
            st.warning(f"No se pudo buscar en {error}", icon=":material/warning:")

        if not st.session_state.resultados_busqueda:
            if buscar:
                st.info("No se encontraron ofertas para esa palabra clave en los portales seleccionados.")
        else:
            st.success(f"Se encontraron {len(st.session_state.resultados_busqueda)} vacantes.", icon=":material/check_circle:")
            perfil_para_match = cargar_perfil()

            for indice, oferta in enumerate(st.session_state.resultados_busqueda):
                with st.container(border=True):
                    st.markdown(f"#### {oferta['titulo']}")
                    st.caption(f"{oferta['empresa']} — {oferta['ubicacion']}")
                    with st.container(horizontal=True, vertical_alignment="center"):
                        st.badge(oferta["fuente"], icon=":material/travel_explore:", color="gray")
                        if oferta.get("modalidad"):
                            st.badge(oferta["modalidad"], icon=":material/home_work:", color="blue")
                        if oferta.get("publicado"):
                            st.caption(oferta["publicado"])
                    if oferta["link"]:
                        st.link_button(
                            "Ver oferta", oferta["link"], icon=":material/open_in_new:", key=f"ver_oferta_{indice}"
                        )

                    match = st.session_state.matches.get(oferta["link"])
                    if match:
                        color_score = "green" if match["score"] >= 70 else "yellow" if match["score"] >= 40 else "red"
                        st.badge(f"Match: {match['score']}/100", icon=":material/insights:", color=color_score)
                        st.caption(match["explicacion"])
                    elif oferta["link"] and st.button(
                        "Analizar match", icon=":material/insights:", key=f"match_{indice}"
                    ):
                        with st.spinner("Analizando match con tu perfil..."):
                            try:
                                texto_oferta = extraer_texto_url(oferta["link"])
                                st.session_state.matches[oferta["link"]] = analizar_match(
                                    texto_oferta, perfil_para_match
                                )
                                st.rerun()
                            except ErrorScraping as e:
                                st.error(f"No se pudo leer la oferta: {e}", icon=":material/error:")
                            except ErrorIA as e:
                                st.error(f"Fallo en la capa de IA: {e}", icon=":material/error:")

# -------------------------------------------------------------
# SECCIÓN 3: MI PERFIL
# -------------------------------------------------------------
elif seccion == "Mi Perfil":
    st.subheader("Mi perfil")
    st.caption(
        "Estos datos van a servir para que la IA compare ofertas contra tu "
        "perfil real y genere CVs/Cover Letters mucho más personalizados "
        "en las próximas versiones. Por ahora, el nombre ya se usa para "
        "firmar la Cover Letter."
    )

    perfil_actual = cargar_perfil()

    with st.form("form_perfil"):
        nombre = st.text_input("Nombre completo", value=perfil_actual["nombre"])
        with st.container(horizontal=True):
            email = st.text_input("Email", value=perfil_actual["email"])
            telefono = st.text_input("Teléfono", value=perfil_actual["telefono"])
            linkedin = st.text_input("LinkedIn (url o usuario)", value=perfil_actual["linkedin"])
        anos_experiencia = st.number_input(
            "Años de experiencia", min_value=0, max_value=60, value=perfil_actual["anos_experiencia"]
        )
        seniority_guardado = perfil_actual["seniority"]
        indice_seniority = (
            NIVELES_SENIORITY.index(seniority_guardado) if seniority_guardado in NIVELES_SENIORITY else 0
        )
        seniority = st.selectbox("Nivel", NIVELES_SENIORITY, index=indice_seniority)
        stack_principal = st.text_input(
            "Stack principal (lenguajes, frameworks, herramientas)",
            value=perfil_actual["stack_principal"],
        )
        logros_y_experiencia = st.text_area(
            "Logros y experiencia (proyectos reales, resultados concretos)",
            value=perfil_actual["logros_y_experiencia"],
            height=200,
        )

        if st.form_submit_button("Guardar perfil", icon=":material/save:", type="primary"):
            guardar_perfil({
                "nombre": nombre,
                "email": email,
                "telefono": telefono,
                "linkedin": linkedin,
                "anos_experiencia": anos_experiencia,
                "seniority": seniority,
                "stack_principal": stack_principal,
                "logros_y_experiencia": logros_y_experiencia,
            })
            st.success("Perfil guardado.", icon=":material/check_circle:")

# -------------------------------------------------------------
# SECCIÓN 4: PREGUNTAS DE POSTULACIÓN
# -------------------------------------------------------------
elif seccion == "Preguntas de Postulación":
    st.subheader("Asistente de respuestas para formularios de postulación")
    st.caption(
        "Pegá la pregunta tal cual aparece en el formulario real (y las alternativas, "
        "si es de opción múltiple). La respuesta sugerida es para copiar manualmente — "
        "la app nunca completa ni envía nada en un formulario real."
    )

    with st.container(border=True):
        pregunta = st.text_area("Pregunta del formulario")
        opciones_texto = st.text_input(
            "Alternativas (separadas por coma, dejar vacío si es respuesta libre)"
        )

        if st.button("Sugerir respuesta", icon=":material/lightbulb:", type="primary"):
            if not pregunta.strip():
                st.error("Pegá la pregunta del formulario primero.", icon=":material/error:")
                st.stop()

            opciones = (
                [opcion.strip() for opcion in opciones_texto.split(",") if opcion.strip()]
                if opciones_texto.strip()
                else None
            )

            with st.spinner("Pensando la mejor respuesta..."):
                try:
                    perfil_para_pregunta = cargar_perfil()
                    resultado = sugerir_respuesta(pregunta, perfil_para_pregunta, opciones=opciones)
                except ErrorIA as e:
                    st.error(f"Fallo en la capa de IA: {e}", icon=":material/error:")
                    st.stop()

            st.success("Respuesta sugerida", icon=":material/check_circle:")
            st.text_area("Respuesta (copiá esto al formulario real)", value=resultado["respuesta"], height=100)
            st.caption(resultado["justificacion"])

# -------------------------------------------------------------
# SECCIÓN 5: FAQ
# -------------------------------------------------------------
elif seccion == "FAQ":
    st.subheader("Preguntas frecuentes")
    st.caption("Qué es HuntJob Chile, explicado como si te lo contara en el ascensor.")

    with st.container(border=True):
        st.markdown("#### ¿Qué es HuntJob Chile?")
        st.write(
            "Una app personal (no un producto para vender) que te ayuda a postular a "
            "trabajos en Chile más rápido y con mejor calidad, usando IA de verdad — no "
            "plantillas genéricas."
        )

    with st.container(border=True):
        st.markdown("#### ¿Qué hace exactamente?")
        st.markdown(
            "- **Genera tu CV y Cover Letter** a partir del link de una oferta real — "
            "pegás la URL, la IA lee la oferta y redacta un extracto adaptado a ese "
            "puesto puntual, usando tu perfil real (tu stack, tus logros), no inventado.\n"
            "- **Busca vacantes** en varios portales chilenos a la vez (Computrabajo, "
            "ChileTrabajos) desde un solo lugar.\n"
            "- **Te dice qué tan buen match** es cada oferta contra tu perfil — un score "
            "y por qué, para no perder tiempo postulando a algo que no calza.\n"
            "- **Te ayuda con las preguntas raras del formulario** de postulación "
            "(incluso las de opción múltiple), sugiriendo una respuesta que después vos "
            "copiás manualmente."
        )

    with st.container(border=True):
        st.markdown("#### ¿Mis datos quedan seguros?")
        st.write(
            "Tu perfil (nombre, experiencia, logros) se guarda solo en tu propia máquina "
            "o tu cuenta de Streamlit — nunca se sube al repositorio de GitHub, y la app "
            "nunca completa ni envía nada por su cuenta en un formulario real."
        )

    with st.container(border=True):
        st.markdown("#### ¿Corre en mi computador o en internet?")
        st.write(
            "Las dos formas: instalable como app de escritorio en Linux (con su propio "
            "ícono en el menú de aplicaciones), o como app web si la desplegás en "
            "Streamlit Community Cloud."
        )

    with st.container(border=True):
        st.markdown("#### ¿Por qué cambian los colores de la app?")
        st.write(
            "Un detalle personal: la paleta pastel rota entre 4 variantes según la hora "
            "del día. No cambia nada funcional — es solo para que se sienta viva."
        )
