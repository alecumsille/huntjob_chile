import base64
import os
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from core.scraper_web import extraer_texto_url, ErrorScraping
from core.motor_ia import extraer_cargo_y_empresa, analizar_match, sugerir_respuesta, ErrorIA
from core.portales import PORTALES, buscar_en_todos
from core.perfil import cargar_perfil, guardar_perfil, NIVELES_SENIORITY
from core.postulacion import generar_documentos
from core.auth_supabase import obtener_usuario_desde_token, cerrar_sesion, SUPABASE_URL
from core.db import guardar_historial, obtener_historial_reciente, marcar_postulado, verificar_y_consumir_uso, obtener_plan
from core.flow_checkout import PAYMENTS_SERVICE_URL

st.set_page_config(page_title="HuntJob Chile", page_icon="assets/icon.png", layout="wide")

# Inyección de metadatos Open Graph directo al <head> nativo del DOM
components.html(
    """
    <script>
    const parentHead = window.parent.document.getElementsByTagName('head')[0];
    
    // Meta OG Image
    let metaOgImg = window.parent.document.querySelector("meta[property='og:image']");
    if (!metaOgImg) {
        metaOgImg = window.parent.document.createElement('meta');
        metaOgImg.setAttribute('property', 'og:image');
        parentHead.appendChild(metaOgImg);
    }
    metaOgImg.setAttribute('content', 'https://raw.githubusercontent.com/alecumsille/huntjob_chile/main/assets/icon.png');

    // Meta OG Title
    let metaOgTitle = window.parent.document.querySelector("meta[property='og:title']");
    if (!metaOgTitle) {
        metaOgTitle = window.parent.document.createElement('meta');
        metaOgTitle.setAttribute('property', 'og:title');
        parentHead.appendChild(metaOgTitle);
    }
    metaOgTitle.setAttribute('content', 'HuntJob Chile — Plataforma Inteligente de Empleos');

    // Meta OG Description
    let metaOgDesc = window.parent.document.querySelector("meta[property='og:description']");
    if (!metaOgDesc) {
        metaOgDesc = window.parent.document.createElement('meta');
        metaOgDesc.setAttribute('property', 'og:description');
        parentHead.appendChild(metaOgDesc);
    }
    metaOgDesc.setAttribute('content', 'Busca ofertas en todos los portales de empleo de Chile y genera tu CV optimizado con IA.');

    // Favicon link
    let favicon = window.parent.document.querySelector("link[rel*='icon']");
    if (!favicon) {
        favicon = window.parent.document.createElement('link');
        favicon.type = 'image/png';
        favicon.rel = 'shortcut icon';
        parentHead.appendChild(favicon);
    }
    favicon.href = 'https://raw.githubusercontent.com/alecumsille/huntjob_chile/main/assets/icon.png';
    </script>
    """,
    height=0,
)


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


def _social_icon_b64(nombre: str) -> str:
    """Devuelve el b64 de los logos PNG oficiales."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", f"{nombre}.png")
    if os.path.exists(ruta):
        with open(ruta, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


def mostrar_faq() -> None:
    """Contenido estático de preguntas frecuentes — público, no requiere sesión."""
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


# Supabase entrega el token en el fragmento de la URL (#access_token=...),
# que el servidor de Streamlit nunca puede leer — solo el navegador. Este
# puente en JS lo copia a un query param (?access_token=...) para que el
# próximo rerun de Python sí lo reciba en st.query_params.
components.html(
    """
    <script>
    const hash = window.parent.location.hash;
    if (hash && hash.includes('access_token')) {
        const params = new URLSearchParams(hash.substring(1));
        const url = new URL(window.parent.location.href);
        url.hash = '';
        url.searchParams.set('access_token', params.get('access_token') || '');
        window.parent.location.replace(url.toString());
    }
    </script>
    """,
    height=0,
)

if not st.session_state.get("autenticado", False):
    token_url = st.query_params.get("access_token")
    if token_url:
        usuario = obtener_usuario_desde_token(token_url)
        if usuario:
            st.session_state["autenticado"] = True
            st.session_state["user_id"] = usuario["id"]
            st.session_state["user_email"] = usuario["email"]
            st.session_state["access_token"] = token_url
            st.session_state["proveedor_auth"] = usuario["proveedor"]
            st.query_params.clear()
            st.rerun()
        else:
            st.query_params.clear()

if not st.session_state.get("autenticado", False):
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 30px 20px; background: #FFFFFF; border-radius: 16px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-top: 40px;">
                <img src="data:image/png;base64,{_logo_b64()}" width="70" style="margin-bottom: 10px;">
                <h2 style="font-family: 'Quicksand', sans-serif; color: #2D3748; margin-bottom: 5px;">HuntJob Chile</h2>
                <p style="color: #64748B; font-size: 0.95rem; margin-bottom: 25px;">Selecciona tu cuenta para ingresar:</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        g_b64 = _social_icon_b64("google")
        gh_b64 = _social_icon_b64("github")
        fb_b64 = _social_icon_b64("facebook")
        supabase_url = SUPABASE_URL
        redirect_target = "https://huntjob.cumsille.me"
        url_google = f"{supabase_url}/auth/v1/authorize?provider=google&redirect_to={redirect_target}"
        url_github = f"{supabase_url}/auth/v1/authorize?provider=github&redirect_to={redirect_target}"
        url_facebook = f"{supabase_url}/auth/v1/authorize?provider=facebook&redirect_to={redirect_target}"

        st.markdown(
            f"""
            <style>
            .social-btn-link {{
                display: flex !important; align-items: center !important; justify-content: center !important;
                gap: 12px !important; width: 100% !important; height: 48px !important; border-radius: 12px !important;
                font-family: 'Inter', sans-serif !important; font-weight: 600 !important; font-size: 0.95rem !important;
                text-decoration: none !important; transition: all 0.2s ease !important; margin-bottom: 12px !important;
                box-sizing: border-box !important;
            }}
            .btn-g-style {{ background: #FFFFFF !important; color: #0F172A !important; border: 1px solid #CBD5E1 !important; }}
            .btn-gh-style {{ background: #1E293B !important; color: #F8FAFC !important; border: 1px solid #1E293B !important; }}
            .btn-fb-style {{ background: #1877F2 !important; color: #FFFFFF !important; border: 1px solid #1877F2 !important; }}
            .icon-img {{ width: 20px !important; height: 20px !important; object-fit: contain !important; }}
            </style>

            <a href="{url_google}" class="social-btn-link btn-g-style" target="_self">
                <img src="data:image/png;base64,{g_b64}" class="icon-img" alt="Google">
                <span>Continuar con Google</span>
            </a>
            <a href="{url_github}" class="social-btn-link btn-gh-style" target="_self">
                <img src="data:image/png;base64,{gh_b64}" class="icon-img" alt="GitHub">
                <span>Continuar con GitHub</span>
            </a>
            <a href="{url_facebook}" class="social-btn-link btn-fb-style" target="_self">
                <img src="data:image/png;base64,{fb_b64}" class="icon-img" alt="Facebook">
                <span>Continuar con Facebook</span>
            </a>
            """,
            unsafe_allow_html=True
        )

        if st.button("Probar sin cuenta (modo invitado)", use_container_width=True, type="secondary"):
            st.session_state["autenticado"] = True
            st.session_state["user_id"] = None
            st.session_state["access_token"] = None
            st.session_state["proveedor_auth"] = "Invitado"
            st.rerun()
        st.caption("En modo invitado tu perfil e historial no se guardan — se pierden al cerrar la pestaña.")

        with st.expander("¿Qué es HuntJob Chile? Ver preguntas frecuentes (FAQ)"):
            mostrar_faq()

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

# Contexto de usuario: None en modo invitado, o {"user_id","access_token"}
# con cuenta real — todas las lecturas/escrituras de datos lo reciben para
# saber si van a Postgres (por usuario) o solo a la sesión (invitado).
contexto_usuario = None
if st.session_state.get("user_id"):
    contexto_usuario = {
        "user_id": st.session_state["user_id"],
        "access_token": st.session_state["access_token"],
    }

with st.sidebar:
    proveedor = st.session_state.get("proveedor_auth", "Usuario")
    correo = st.session_state.get("user_email", "")
    st.markdown(f"**Cuenta:** {proveedor}" + (f"  \n{correo}" if correo else ""))

    if contexto_usuario:
        try:
            plan = obtener_plan(contexto_usuario["user_id"], contexto_usuario["access_token"])
            if plan["plan"] == "premium":
                st.caption("Plan Premium — generaciones sin límite ✨")
                if st.button("Cancelar suscripción", use_container_width=True):
                    st.session_state["confirmar_cancelacion"] = True
                if st.session_state.get("confirmar_cancelacion"):
                    st.warning("¿Seguro? Vas a volver al plan gratuito (5 generaciones/mes).")
                    if st.button("Sí, cancelar", type="primary", use_container_width=True):
                        import requests as _requests
                        _requests.post(
                            f"{PAYMENTS_SERVICE_URL}/webhook/flow/subscription-canceled",
                            data={"customerId": plan.get("flow_customer_id", "")},
                            timeout=15,
                        )
                        st.session_state["confirmar_cancelacion"] = False
                        st.rerun()
            else:
                usados = plan["generaciones_este_mes"]
                limite = plan["limite_mensual"]
                st.progress(
                    min(usados / limite, 1.0) if limite else 0,
                    text=f"Plan gratuito — {usados}/{limite} generaciones este mes",
                )
                if st.button("Actualizar a Premium ($4.990/mes)", type="primary", use_container_width=True):
                    from core.flow_checkout import iniciar_registro_tarjeta

                    url_pago = iniciar_registro_tarjeta(
                        user_id=contexto_usuario["user_id"],
                        nombre=st.session_state.get("user_email", "Usuario"),
                        email=st.session_state.get("user_email", ""),
                    )
                    st.link_button("Ir a pagar con Flow", url_pago, use_container_width=True)
        except Exception:
            pass
    else:
        st.caption("Modo invitado — datos no guardados")

    if st.button("Cerrar Sesión", icon=":material/logout:", use_container_width=True):
        if contexto_usuario:
            cerrar_sesion(contexto_usuario["access_token"])
        st.session_state.clear()
        st.rerun()
    st.divider()
    seccion = st.radio(
        "Panel",
        ["Generador por URL", "Buscador de Vacantes", "Mis Postulaciones", "Mi Perfil", "Preguntas de Postulación", "FAQ"],
    )
    st.caption("HuntJob Chile")

# -------------------------------------------------------------
# SECCIÓN 1: GENERADOR DIRECTO POR URL
# -------------------------------------------------------------
if seccion == "Generador por URL":
    st.subheader("Generación de CV y Cover Letter desde una oferta puntual")

    perfil = cargar_perfil(contexto_usuario)
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
    if "empresa_detectada" not in st.session_state:
        st.session_state.empresa_detectada = ""

    with st.container(border=True):
        url_oferta = st.text_input("Link de la oferta de trabajo (Computrabajo, LinkedIn, etc.)")

        if url_oferta and st.button("Leer oferta y detectar cargo", icon=":material/search:"):
            with st.spinner("Extrayendo contenido de la URL..."):
                try:
                    st.session_state.texto_extraido = extraer_texto_url(url_oferta)
                except ErrorScraping as e:
                    st.error(f"No se pudo leer la oferta: {e}", icon=":material/error:")
                    st.stop()

            with st.spinner("Detectando cargo y empresa con Gemini..."):
                try:
                    deteccion = extraer_cargo_y_empresa(st.session_state.texto_extraido)
                    st.session_state.puesto_detectado = deteccion["cargo"]
                    st.session_state.empresa_detectada = deteccion["empresa"]
                except ErrorIA as e:
                    st.error(f"Error en la IA: {e}", icon=":material/error:")
                    st.stop()

    with st.container(border=True):
        col_puesto, col_empresa = st.columns(2)
        with col_puesto:
            puesto_objetivo = st.text_input(
                "Puesto detectado (editable)",
                value=st.session_state.puesto_detectado,
            )
        with col_empresa:
            empresa_objetivo = st.text_input(
                "Empresa (editable)",
                value=st.session_state.empresa_detectada,
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

            if contexto_usuario:
                permitido, aviso_uso = verificar_y_consumir_uso(
                    contexto_usuario["user_id"], contexto_usuario["access_token"]
                )
                if not permitido:
                    st.error(aviso_uso, icon=":material/lock:")
                    st.stop()
                if aviso_uso:
                    st.info(aviso_uso, icon=":material/info:")

            with st.spinner("Redactando documentos con Gemini..."):
                try:
                    documentos = generar_documentos(
                        st.session_state.texto_extraido, puesto_objetivo, mercado_destino, estilo_pdf, perfil
                    )
                except (ErrorIA, ValueError) as e:
                    st.error(f"Error al generar el contenido: {e}", icon=":material/error:")
                    st.stop()

            if contexto_usuario:
                guardar_historial(
                    contexto_usuario["user_id"],
                    contexto_usuario["access_token"],
                    puesto=puesto_objetivo,
                    empresa=empresa_objetivo or "No especificada",
                    mercado=mercado_destino,
                    url_oferta=url_oferta,
                    cv_texto=documentos["cv_texto"],
                    cover_letter_texto=documentos["cover_letter_texto"],
                    estilo_pdf=estilo_pdf,
                )

            st.success("Documentos generados correctamente.", icon=":material/check_circle:")

            with st.container(horizontal=True):
                st.download_button(
                    "Descargar CV (PDF)",
                    data=documentos["cv_bytes"],
                    file_name=documentos["nombre_cv"],
                    mime="application/pdf",
                    icon=":material/download:",
                )
                st.download_button(
                    "Descargar Cover Letter (PDF)",
                    data=documentos["cl_bytes"],
                    file_name=documentos["nombre_cl"],
                    mime="application/pdf",
                    icon=":material/download:",
                )
                if url_oferta:
                    st.link_button("Ir al portal a postular", url_oferta, icon=":material/open_in_new:")

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
            perfil_para_match = cargar_perfil(contexto_usuario)
            if "postulaciones_1click" not in st.session_state:
                st.session_state.postulaciones_1click = {}

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

                    match = st.session_state.matches.get(oferta["link"])
                    if match:
                        color_score = "green" if match["score"] >= 70 else "yellow" if match["score"] >= 40 else "red"
                        st.badge(f"Match ATS: {match['score']}/100", icon=":material/insights:", color=color_score)
                        st.caption(match["explicacion"])

                        with st.expander("Ver Auditoría de Compatibilidad ATS Detallada"):
                            st.progress(match["score"] / 100, text=f"Puntaje de Coincidencia: {match['score']}%")

                            col1, col2 = st.columns(2)
                            with col1:
                                if match.get("fortalezas"):
                                    st.markdown("**Fortalezas detectadas:**")
                                    for f in match["fortalezas"]:
                                        st.markdown(f"- {f}")
                                if match.get("palabras_faltantes"):
                                    st.markdown("**Palabras clave faltantes en tu CV:**")
                                    for p in match["palabras_faltantes"]:
                                        st.markdown(f"- `{p}`")
                            with col2:
                                if match.get("debilidades"):
                                    st.markdown("**Debilidades frente a esta oferta:**")
                                    for d in match["debilidades"]:
                                        st.markdown(f"- {d}")

                            if match.get("recomendaciones"):
                                st.markdown("**Acciones sugeridas para mejorar la postulación:**")
                                for r in match["recomendaciones"]:
                                    st.markdown(f"- {r}")

                    resultado_1click = st.session_state.postulaciones_1click.get(oferta["link"])

                    with st.container(horizontal=True, vertical_alignment="center"):
                        if oferta["link"]:
                            st.link_button(
                                "Ver oferta", oferta["link"], icon=":material/open_in_new:", key=f"ver_oferta_{indice}"
                            )
                        if oferta["link"] and not match and st.button(
                            "Analizar match ATS", icon=":material/insights:", key=f"match_{indice}"
                        ):
                            with st.spinner("Realizando auditoría ATS con tu perfil..."):
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

                        if oferta["link"] and not resultado_1click and st.button(
                            "Postular en 1 click", icon=":material/bolt:", type="primary", key=f"postular_{indice}"
                        ):
                            if contexto_usuario:
                                permitido, aviso_uso = verificar_y_consumir_uso(
                                    contexto_usuario["user_id"], contexto_usuario["access_token"]
                                )
                                if not permitido:
                                    st.error(aviso_uso, icon=":material/lock:")
                                    st.stop()
                            with st.spinner("Analizando match, redactando CV y Cover Letter a la medida..."):
                                try:
                                    texto_oferta = extraer_texto_url(oferta["link"])
                                    match_1click = st.session_state.matches.get(oferta["link"]) or analizar_match(
                                        texto_oferta, perfil_para_match
                                    )
                                    st.session_state.matches[oferta["link"]] = match_1click
                                    documentos = generar_documentos(
                                        texto_oferta,
                                        oferta["titulo"],
                                        "Chile",
                                        "Pastel",
                                        perfil_para_match,
                                        match=match_1click,
                                    )
                                    historial_id = None
                                    if contexto_usuario:
                                        historial_id = guardar_historial(
                                            contexto_usuario["user_id"],
                                            contexto_usuario["access_token"],
                                            puesto=oferta["titulo"],
                                            empresa=oferta.get("empresa", ""),
                                            mercado="Chile",
                                            url_oferta=oferta["link"],
                                            cv_texto=documentos["cv_texto"],
                                            cover_letter_texto=documentos["cover_letter_texto"],
                                            estilo_pdf="Pastel",
                                            match_score=match_1click["score"],
                                            estado="postulado",
                                        )
                                    st.session_state.postulaciones_1click[oferta["link"]] = {
                                        **documentos,
                                        "historial_id": historial_id,
                                    }
                                    st.rerun()
                                except ErrorScraping as e:
                                    st.error(f"No se pudo leer la oferta: {e}", icon=":material/error:")
                                except (ErrorIA, ValueError) as e:
                                    st.error(f"Error al generar tu postulación: {e}", icon=":material/error:")

                    if resultado_1click:
                        st.success("CV y Cover Letter listos, orientados a esta oferta.", icon=":material/check_circle:")
                        with st.container(horizontal=True):
                            st.download_button(
                                "Descargar CV",
                                data=resultado_1click["cv_bytes"],
                                file_name=resultado_1click["nombre_cv"],
                                mime="application/pdf",
                                icon=":material/download:",
                                key=f"dl_cv_{indice}",
                            )
                            st.download_button(
                                "Descargar Cover Letter",
                                data=resultado_1click["cl_bytes"],
                                file_name=resultado_1click["nombre_cl"],
                                mime="application/pdf",
                                icon=":material/download:",
                                key=f"dl_cl_{indice}",
                            )
                            st.link_button(
                                "Postular ahora en el portal", oferta["link"],
                                icon=":material/open_in_new:", key=f"ir_postular_{indice}",
                            )
                        st.caption(
                            "Descarga los documentos y termina la postulación en el portal — no enviamos "
                            "formularios automáticamente por ti, ya que eso requeriría tu sesión logueada "
                            "en cada sitio y podría infringir sus términos de uso."
                        )

# -------------------------------------------------------------
# SECCIÓN 3: MIS POSTULACIONES
# -------------------------------------------------------------
elif seccion == "Mis Postulaciones":
    st.subheader("Mis postulaciones")

    if not contexto_usuario:
        st.info(
            "Esto es solo para cuentas registradas — en modo invitado no se guarda historial. "
            "Cierra sesión y entra con Google, GitHub o Facebook para empezar a llevar registro.",
            icon=":material/info:",
        )
    else:
        historial = obtener_historial_reciente(contexto_usuario["user_id"], contexto_usuario["access_token"], limite=20)
        if not historial:
            st.info("Todavía no generaste ninguna postulación. Empieza en \"Generador por URL\" o \"Buscador de Vacantes\".", icon=":material/info:")
        else:
            for item in historial:
                with st.container(border=True):
                    col_info, col_estado = st.columns([4, 1])
                    with col_info:
                        st.markdown(f"**{item['puesto']}**")
                        st.caption(f"{item.get('empresa') or 'Empresa no especificada'} — {item.get('mercado', '')}")
                    with col_estado:
                        if item.get("estado") == "postulado":
                            st.badge("Postulado", icon=":material/check_circle:", color="green")
                        else:
                            st.badge("Generado", icon=":material/description:", color="gray")
                    with st.container(horizontal=True, vertical_alignment="center"):
                        if item.get("match_score") is not None:
                            st.caption(f"Match ATS: {item['match_score']}/100")
                        if item.get("creado_en"):
                            st.caption(str(item["creado_en"])[:16].replace("T", " "))
                        if item.get("url_oferta"):
                            st.link_button("Ver oferta", item["url_oferta"], icon=":material/open_in_new:", key=f"hist_link_{item['id']}")
                        if item.get("estado") != "postulado" and st.button(
                            "Marcar como postulado", icon=":material/check:", key=f"hist_marcar_{item['id']}"
                        ):
                            marcar_postulado(contexto_usuario["user_id"], contexto_usuario["access_token"], item["id"])
                            st.rerun()

# -------------------------------------------------------------
# SECCIÓN 4: MI PERFIL
# -------------------------------------------------------------
elif seccion == "Mi Perfil":
    st.subheader("Mi perfil")
    st.caption(
        "Con estos datos la IA compara ofertas con tu perfil y personaliza tu CV y Cover Letter. "
        "Tu nombre ya aparece en la firma de la carta."
    )

    perfil_actual = cargar_perfil(contexto_usuario)

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

        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            if st.form_submit_button("Guardar perfil", icon=":material/save:", type="primary", use_container_width=True):
                guardar_perfil(contexto_usuario, {
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
        with col_sub2:
            if st.form_submit_button("Limpiar campos del perfil", icon=":material/delete:", use_container_width=True):
                guardar_perfil(contexto_usuario, {
                    "nombre": "",
                    "email": "",
                    "telefono": "",
                    "linkedin": "",
                    "anos_experiencia": 0,
                    "seniority": "Junior",
                    "stack_principal": "",
                    "logros_y_experiencia": "",
                })
                st.success("Perfil limpiado correctamente.", icon=":material/check_circle:")
                st.rerun()

# -------------------------------------------------------------
# SECCIÓN 5: PREGUNTAS DE POSTULACIÓN
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
                    perfil_para_pregunta = cargar_perfil(contexto_usuario)
                    resultado = sugerir_respuesta(pregunta, perfil_para_pregunta, opciones=opciones)
                except ErrorIA as e:
                    st.error(f"Error en la IA: {e}", icon=":material/error:")
                    st.stop()

            st.success("Respuesta sugerida", icon=":material/check_circle:")
            st.text_area("Respuesta sugerida (cópiala en el formulario)", value=resultado["respuesta"], height=100)
            st.caption(resultado["justificacion"])

# -------------------------------------------------------------
# SECCIÓN 6: FAQ
# -------------------------------------------------------------
elif seccion == "FAQ":
    st.subheader("Preguntas frecuentes")
    st.caption("Lo esencial sobre HuntJob Chile, en pocas palabras.")
    mostrar_faq()
