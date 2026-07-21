import base64
import os
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from core.scraper_web import extraer_texto_url, ErrorScraping
from core.motor_ia import generar_texto, analizar_match, sugerir_respuesta, ErrorIA
from core.generador_pdf import generar_pdf, sanear_nombre_archivo
from core.portales import PORTALES, buscar_en_todos
from core.perfil import cargar_perfil, guardar_perfil, NIVELES_SENIORITY, formatear_perfil
from core.db import guardar_historial, obtener_historial_reciente

st.set_page_config(page_title="HuntJob Chile", page_icon="assets/icon.png", layout="wide")


def _logo_b64() -> str:
    """Lee el logo y lo devuelve en base64 para embeber en HTML."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
    with open(ruta, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _chile_b64() -> str:
    """Lee la bandera chilena y la devuelve en base64."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "chile.png")
    with open(ruta, "rb") as f:
        return base64.b64encode(f.read()).decode()


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
if not st.session_state.get("autenticado"):
    st.markdown(
        """
        <style>
        .auth-card {
            background-color: #FFFDFE;
            border: 1px solid #FCEEF3;
            border-radius: 16px;
            padding: 30px;
            max-width: 480px;
            margin: 40px auto;
            box-shadow: 0 10px 30px rgba(200, 127, 160, 0.15);
            text-align: center;
        }
        .auth-title {
            font-family: 'Quicksand', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: #C87FA0;
            margin-bottom: 8px;
        }
        .auth-sub {
            font-family: 'Nunito', sans-serif;
            color: #666;
            font-size: 0.95rem;
            margin-bottom: 24px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        f"""
        <div class="auth-card">
            <img src="data:image/png;base64,{_logo_b64()}" width="80" style="margin-bottom: 10px;">
            <div class="auth-title">HuntJob Chile</div>
            <div class="auth-sub">Inicia sesión o crea tu perfil con tu cuenta preferida</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown("### Selecciona tu método de ingreso:")
        
        # SVGs oficiales de Google, GitHub y Facebook
        SVG_GOOGLE = '<svg width="18" height="18" viewBox="0 0 24 24" style="vertical-align:middle; margin-right:8px;"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>'
        SVG_GITHUB = '<svg width="18" height="18" viewBox="0 0 24 24" fill="#333" style="vertical-align:middle; margin-right:8px;"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>'
        SVG_FACEBOOK = '<svg width="18" height="18" viewBox="0 0 24 24" fill="#1877F2" style="vertical-align:middle; margin-right:8px;"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>'

        btn_g = st.button("Continuar con Google", use_container_width=True)
        btn_gh = st.button("Continuar con GitHub", use_container_width=True)
        btn_fb = st.button("Continuar con Facebook", use_container_width=True)

        if btn_g:
            st.session_state.autenticado = True
            st.session_state.proveedor_auth = "Google"
            st.session_state.usuario_nombre = "Usuario Google"
            st.rerun()
            
        if btn_gh:
            st.session_state.autenticado = True
            st.session_state.proveedor_auth = "GitHub"
            st.session_state.usuario_nombre = "Usuario GitHub"
            st.rerun()
            
        if btn_fb:
            st.session_state.autenticado = True
            st.session_state.proveedor_auth = "Facebook"
            st.session_state.usuario_nombre = "Usuario Facebook"
            st.rerun()
            
        if clave_requerida:
            st.markdown("---")
            clave_ingresada = st.text_input("O ingresa con la clave de acceso directa:", type="password")
            if clave_ingresada:
                if clave_ingresada == clave_requerida:
                    st.session_state.autenticado = True
                    st.session_state.proveedor_auth = "Clave Directa"
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
    /* --- Eliminar borde del sidebar radio --- */
    [data-testid="stSidebar"] [role="radiogroup"] label div:first-child {{
        border-color: {paleta_actual['sidebar_primario']} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

components.html(
    f"""
    <style>
      body {{
        margin: 0;
        padding: 0;
        background-color: {paleta_actual['fondo']};
        overflow: hidden;
      }}
      @keyframes hj-float {{
        0%, 100% {{ transform: translateY(0px); }}
        50%       {{ transform: translateY(-5px); }}
      }}
      @keyframes hj-search {{
        0%   {{ transform: translateY(0px) rotate(0deg); }}
        25%  {{ transform: translateY(-4px) rotate(-8deg); }}
        75%  {{ transform: translateY(-4px) rotate(8deg); }}
        100% {{ transform: translateY(0px) rotate(0deg); }}
      }}
      .wrap {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 6px 4px;
        box-sizing: border-box;
      }}
      .left {{
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 1;
        min-width: 0;
      }}
      .logo {{
        width: 56px;
        height: 56px;
        flex-shrink: 0;
        animation: hj-float 3.6s ease-in-out infinite;
        filter: drop-shadow(0 4px 8px rgba(200,127,160,0.25));
        cursor: default;
      }}
      .logo:hover {{
        animation: hj-search 1.2s ease-in-out infinite;
      }}
      .texto-box {{
        min-width: 0;
      }}
      .titulo {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {paleta_actual['primario']};
        margin: 0;
        line-height: 1.1;
        letter-spacing: -0.5px;
        font-family: 'Quicksand', sans-serif;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }}
      .caption {{
        font-size: 0.82rem;
        color: #777;
        margin: 3px 0 0 0;
        font-family: 'Nunito', sans-serif;
        line-height: 1.2;
      }}
      .flag {{
        width: 90px;
        height: auto;
        flex-shrink: 0;
        mix-blend-mode: multiply;
        filter: drop-shadow(0 2px 6px rgba(180,0,0,0.15));
        margin-left: 10px;
      }}
      @media (max-width: 520px) {{
        .logo {{
          width: 44px;
          height: 44px;
        }}
        .titulo {{
          font-size: 1.4rem;
        }}
        .caption {{
          font-size: 0.75rem;
        }}
        .flag {{
          width: 65px;
        }}
      }}
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@700&family=Nunito:wght@400&display=swap" rel="stylesheet">
    <div class="wrap">
      <div class="left">
        <img class="logo" src="data:image/png;base64,{_logo_b64()}" alt="HuntJob Chile">
        <div class="texto-box">
          <p class="titulo">HuntJob Chile</p>
          <p class="caption">Motor de postulaciones &mdash; extrae ofertas, analiza con IA y genera tu PDF.</p>
        </div>
      </div>
      <img class="flag" src="data:image/png;base64,{_chile_b64()}" alt="Chile">
    </div>
    """,
    height=85,
    scrolling=False,
)

CARPETA_SALIDA = "salidas_pdf"
os.makedirs(CARPETA_SALIDA, exist_ok=True)

with st.sidebar:
    proveedor = st.session_state.get("proveedor_auth", "Sesión Activa")
    st.markdown(f"**Cuenta:** {proveedor}")
    if st.button("Cerrar Sesión", icon=":material/logout:"):
        st.session_state.autenticado = False
        st.rerun()
    st.divider()
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
            "Tu perfil aún no está completo — los documentos se firmarán como \"Candidato/a\". "
            "Ve a \"Mi Perfil\" para completarlo.",
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
                    st.error(f"Error en la IA: {e}", icon=":material/error:")
                    st.stop()

    with st.container(border=True):
        puesto_objetivo = st.text_input(
            "Puesto detectado (editable)",
            value=st.session_state.puesto_detectado,
        )
        col_mercado, col_estilo = st.columns(2)
        with col_mercado:
            mercado_destino = st.selectbox(
                "Mercado objetivo", ["Chile", "Alemania / Europa", "UK", "USA", "Remoto Global"]
            )
        with col_estilo:
            estilo_pdf = st.selectbox(
                "Estilo visual del PDF", ["Pastel", "Ejecutivo / Marino", "Minimalista Oscuro", "Esmeralda / Tech"]
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
                        f"Redacta un Curriculum Vitae Completo y Profesional en español, optimizado para pasar filtros ATS, "
                        f"diseñado para el puesto de {puesto_objetivo} en {mercado_destino}.\n"
                        f"Usa exclusivamente el stack, experiencia y logros reales del candidato descritos en su perfil.\n"
                        f"Estructura el CV estrictamente con las siguientes secciones limpias:\n\n"
                        f"PERFIL PROFESIONAL\n"
                        f"(Un extracto potente de 4 a 5 líneas enfocado en {puesto_objetivo} con palabras clave del aviso)\n\n"
                        f"EXPERIENCIA Y LOGROS DESTACADOS\n"
                        f"(Puntos concretos con métricas o resultados basados en la experiencia real del candidato)\n\n"
                        f"COMPETENCIAS TÉCNICAS Y HERRAMIENTAS\n"
                        f"(Listado estructurado del stack tecnológico que calza con el aviso)\n\n"
                        f"NUNCA inventes tecnologías o empresas que no estén en el perfil del candidato.\n\n"
                        f"Perfil del candidato:\n{contexto_perfil}"
                    )
                    nombre_firma = perfil["nombre"] or "Candidato/a"
                    prompt_cover = (
                        f"Escribe ÚNICAMENTE el cuerpo de una Cover Letter en español, directa y sin rodeos, "
                        f"para el puesto de {puesto_objetivo} en {mercado_destino}. Si el perfil tiene "
                        f"logros o experiencia, menciona como máximo uno concreto que calce con esta oferta "
                        f"— si no hay logros cargados, escribe sin inventar ninguno. NUNCA indiques que el "
                        f"candidato domina o usa una tecnología que no esté textualmente en su 'Stack "
                        f"principal', aunque la oferta la pida — en ese caso, puedes mencionar disposición "
                        f"a aprenderla, nunca dominio que no tiene. Firma con el nombre {nombre_firma}. "
                        f"No agregues explicaciones ni ningún texto que no sea la carta en sí.\n\n"
                        f"Perfil del candidato:\n{contexto_perfil}"
                    )

                    cv_adaptado = generar_texto(prompt_cv, st.session_state.texto_extraido)
                    cover_letter_adaptada = generar_texto(prompt_cover, st.session_state.texto_extraido)
                except ErrorIA as e:
                    st.error(f"Error al generar el contenido: {e}", icon=":material/error:")
                    st.stop()

            cargo_limpio = sanear_nombre_archivo(puesto_objetivo)
            nombre_archivo = sanear_nombre_archivo(perfil["nombre"] or "candidato")
            ruta_cv = os.path.join(CARPETA_SALIDA, f"CV_{nombre_archivo}_{cargo_limpio}.pdf")
            ruta_cl = os.path.join(CARPETA_SALIDA, f"CoverLetter_{nombre_archivo}_{cargo_limpio}.pdf")

            try:
                generar_pdf(ruta_cv, cv_adaptado, "CV Profesional", puesto_objetivo, perfil, estilo_nombre=estilo_pdf)
                generar_pdf(ruta_cl, cover_letter_adaptada, "Cover Letter", puesto_objetivo, perfil, estilo_nombre=estilo_pdf)
                
                # Guardar en memoria de base de datos SQLite
                guardar_historial(
                    puesto=puesto_objetivo,
                    empresa="Empresa del aviso",
                    mercado=mercado_destino,
                    url_oferta=url_oferta,
                    cv_texto=cv_adaptado,
                    cover_letter_texto=cover_letter_adaptada,
                    estilo_pdf=estilo_pdf
                )
            except ValueError as e:
                st.error(f"Error al generar el PDF: {e}", icon=":material/error:")
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
                                st.error(f"Error en la IA: {e}", icon=":material/error:")

# -------------------------------------------------------------
# SECCIÓN 3: MI PERFIL
# -------------------------------------------------------------
elif seccion == "Mi Perfil":
    st.subheader("Mi perfil")
    st.caption(
        "Con estos datos la IA compara ofertas con tu perfil y personaliza tu CV y Cover Letter. "
        "Tu nombre ya aparece en la firma de la carta."
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
        "Pega la pregunta tal como aparece en el formulario (con las alternativas si es de selección múltiple). "
        "La respuesta es para que tú la copies — la app nunca envía nada por ti."
    )

    with st.container(border=True):
        pregunta = st.text_area("Pregunta del formulario")
        opciones_texto = st.text_input(
            "Alternativas (separadas por coma, dejar vacío si es respuesta libre)"
        )

        if st.button("Sugerir respuesta", icon=":material/lightbulb:", type="primary"):
            if not pregunta.strip():
                st.error("Primero pega la pregunta del formulario.", icon=":material/error:")
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
                    st.error(f"Error en la IA: {e}", icon=":material/error:")
                    st.stop()

            st.success("Respuesta sugerida", icon=":material/check_circle:")
            st.text_area("Respuesta sugerida (cópiala en el formulario)", value=resultado["respuesta"], height=100)
            st.caption(resultado["justificacion"])

# -------------------------------------------------------------
# SECCIÓN 5: FAQ
# -------------------------------------------------------------
elif seccion == "FAQ":
    st.subheader("Preguntas frecuentes")
    st.caption("Lo esencial sobre HuntJob Chile, en pocas palabras.")

    with st.container(border=True):
        st.markdown("#### ¿Qué es HuntJob Chile?")
        st.write(
            "Una app para postular a trabajos en Chile de forma más rápida y efectiva, "
            "usando inteligencia artificial — sin plantillas genéricas."
        )

    with st.container(border=True):
        st.markdown("#### ¿Qué hace exactamente?")
        st.markdown(
            "- **Genera tu CV y Cover Letter** desde el link de una oferta real — pegas la URL, "
            "la IA la lee y redacta un texto adaptado a ese cargo usando tu perfil (tu stack, tus logros).\n"
            "- **Busca vacantes** en varios portales chilenos al mismo tiempo (Computrabajo, ChileTrabajos).\n"
            "- **Analiza qué tan buen match** eres para cada oferta — con puntaje y explicación, "
            "para no perder tiempo en postulaciones que no calzan.\n"
            "- **Sugiere respuestas para el formulario** de postulación (incluso preguntas de selección múltiple), "
            "para que tú las copies cuando corresponda."
        )

    with st.container(border=True):
        st.markdown("#### ¿Mis datos quedan seguros?")
        st.write(
            "Tu información (nombre, experiencia, logros) se guarda solo en tu cuenta — "
            "nunca en el repositorio de GitHub. La app tampoco envía nada por ti en formularios externos."
        )

    with st.container(border=True):
        st.markdown("#### ¿Funciona en mi computador o en internet?")
        st.write(
            "Las dos: como app de escritorio en Linux (con ícono en el menú de aplicaciones), "
            "o como app web alojada en la nube."
        )

    with st.container(border=True):
        st.markdown("#### ¿Por qué cambian los colores de la app?")
        st.write(
            "Un detalle de diseño: los colores rotan entre 4 paletas pastel según la hora del día. "
            "Es solo visual, no afecta nada en el funcionamiento."
        )
