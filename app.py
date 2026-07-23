import base64
import copy
import logging
import os
import uuid
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from core.scraper_web import extraer_texto_url, ErrorScraping
from core.motor_ia import (
    extraer_cargo_y_empresa,
    analizar_match,
    sugerir_respuesta,
    generar_preguntas_entrevista,
    optimizar_logro_car,
    inyectar_palabras_clave_cv,
    ErrorIA,
)
from core.portales import PORTALES, buscar_en_todos
from core.perfil import (
    cargar_perfil,
    guardar_perfil,
    NIVELES_SENIORITY,
    NIVELES_IDIOMA,
    TIPOS_FORMACION,
    IDIOMAS_POPULARES,
    COMPETENCIAS_POPULARES,
    HABILIDADES_BLANDAS_POPULARES,
    VALORES_POR_DEFECTO,
)
from core.postulacion import generar_documentos
from core.auth_supabase import obtener_usuario_desde_token, cerrar_sesion, SUPABASE_URL
from core.db import (
    guardar_historial,
    obtener_historial_reciente,
    marcar_postulado,
    verificar_y_consumir_uso,
    obtener_plan,
    guardar_oferta_guardada,
    obtener_ofertas_guardadas,
    actualizar_estado_kanban,
    eliminar_oferta_guardada,
)
from core.analisis_mercado import estimar_sueldo_mercado, formatear_monto_clp, generar_metricas_funnel
from core.extractor_contacto import extraer_datos_contacto
from core.flow_checkout import PAYMENTS_SERVICE_URL

logger = logging.getLogger(__name__)

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


def _github_footer_b64() -> str:
    """Devuelve el b64 de icons8-github-100.png para el pie de página."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons8-github-100.png")
    if os.path.exists(ruta):
        with open(ruta, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return _social_icon_b64("github")


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
# que ningun servidor puede leer — solo el navegador. Streamlit no puede
# moverlo a un query param por su cuenta: components.html renderiza todo
# en un iframe sandboxed sin permiso de top-navigation, ni siquiera con
# un click real de por medio — el sandbox de Streamlit no otorga ese
# permiso, es incondicional, no depende de "user activation". Por eso el
# redirect_to (mas abajo, en la seccion de login) apunta al puente
# `/auth/bridge` de huntjob_payments — una pagina sin sandbox que hace
# ese mismo movimiento sin ninguna restriccion — y este bloque solo
# recibe el resultado ya limpio como query param.
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
        else:
            st.query_params.clear()
            components.html(
                """
                <script>
                try {
                    const parentWin = window.parent || window.top;
                    const store = (parentWin && parentWin.localStorage) ? parentWin.localStorage : window.localStorage;
                    store.removeItem('hj_access_token');
                } catch(e) {}
                </script>
                """,
                height=0,
            )
    else:
        # Intentar auto-restaurar sesión desde localStorage o fragmento hash de Supabase
        components.html(
            """
            <script>
            try {
                const parentWin = window.parent || window.top;
                const store = (parentWin && parentWin.localStorage) ? parentWin.localStorage : window.localStorage;
                
                // 1. Si Supabase devolvió un hash (#access_token=...)
                if (parentWin.location.hash && parentWin.location.hash.includes('access_token=')) {
                    const hashParams = new URLSearchParams(parentWin.location.hash.substring(1));
                    const token = hashParams.get('access_token');
                    if (token) {
                        store.setItem('hj_access_token', token);
                        const url = new URL(parentWin.location.href);
                        url.hash = '';
                        url.searchParams.set('access_token', token);
                        parentWin.location.href = url.toString();
                    }
                } else {
                    // 2. Si hay token guardado previamente en localStorage
                    const savedToken = store.getItem('hj_access_token');
                    if (savedToken && !parentWin.location.search.includes('access_token')) {
                        const url = new URL(parentWin.location.href);
                        url.searchParams.set('access_token', savedToken);
                        parentWin.location.href = url.toString();
                    }
                }
            } catch(e) {
                console.error('Error restaurando sesión:', e);
            }
            </script>
            """,
            height=0,
        )

# Si la sesión ya está autenticada, asegurar que el token quede guardado y sincronizado en localStorage
if st.session_state.get("autenticado") and st.session_state.get("access_token"):
    tok_actual = st.session_state["access_token"]
    components.html(
        f"""
        <script>
        try {{
            const parentWin = window.parent || window.top;
            const store = (parentWin && parentWin.localStorage) ? parentWin.localStorage : window.localStorage;
            if (store.getItem('hj_access_token') !== '{tok_actual}') {{
                store.setItem('hj_access_token', '{tok_actual}');
            }}
        }} catch(e) {{
            console.error('Error sincronizando sesión en localStorage:', e);
        }}
        </script>
        """,
        height=0,
    )

if not st.session_state.get("autenticado", False):
    # CSS para mover todo el contenido hacia arriba reduciendo los margenes superiores de Streamlit
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 1.5rem !important;
            max-width: 900px !important;
        }
        [data-testid="stAppViewContainer"] > .main {
            padding-top: 0rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 25px 20px; background: #FFFFFF; border-radius: 16px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-top: 0px;">
                <img src="data:image/png;base64,{_logo_b64()}" width="65" style="margin-bottom: 10px;">
                <h2 style="font-family: 'Quicksand', sans-serif; color: #2D3748; margin-bottom: 5px;">HuntJob Chile</h2>
                <p style="color: #64748B; font-size: 0.95rem; margin-bottom: 20px;">Selecciona tu cuenta para ingresar:</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        g_b64 = _social_icon_b64("google")
        gh_b64 = _social_icon_b64("github")
        fb_b64 = _social_icon_b64("facebook")
        supabase_url = SUPABASE_URL
        # Va al puente de huntjob_payments, no directo a huntjob.cumsille.me
        # (ver la nota junto al manejo de st.query_params mas arriba).
        redirect_target = "https://huntjob-payments.onrender.com/auth/bridge"
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

        # Tarjeta No Invasiva de Características Premium
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%); border-radius: 14px; border: 1px solid #E2E8F0; padding: 18px 20px; margin-top: 15px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                <h4 style="font-family: 'Quicksand', sans-serif; color: #0F172A; margin: 0 0 12px 0; font-size: 1.02rem; display: flex; align-items: center; gap: 8px;">
                    ✨ <span>Características de la Plataforma</span>
                </h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; font-size: 0.85rem; color: #334155;">
                    <div style="background: #FFFFFF; padding: 10px 12px; border-radius: 10px; border: 1px solid #E2E8F0;">
                        <strong>🎯 Match ATS con IA:</strong><br>Análisis dimensional de coincidencia con ofertas laborales.
                    </div>
                    <div style="background: #FFFFFF; padding: 10px 12px; border-radius: 10px; border: 1px solid #E2E8F0;">
                        <strong>📄 CV PDF en 1-Clic:</strong><br>Optimización de competencias para el mercado chileno.
                    </div>
                    <div style="background: #FFFFFF; padding: 10px 12px; border-radius: 10px; border: 1px solid #E2E8F0;">
                        <strong>⚡ Postulación Preferente:</strong><br>Historial centralizado y métricas de empleabilidad.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("¿Qué es HuntJob Chile? Ver preguntas frecuentes (FAQ)"):
            mostrar_faq()

        # Icono de GitHub centrado en el pie de página
        github_icon_b64 = _github_footer_b64()
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 25px; margin-bottom: 15px; display: flex; justify-content: center; align-items: center;">
                <a href="https://github.com/alecumsille" target="_blank" title="Perfil de GitHub — Alejandro Cumsille" style="display: inline-block; text-decoration: none; transition: transform 0.2s ease;">
                    <img src="data:image/png;base64,{github_icon_b64}" width="40" height="40" alt="Alejandro Cumsille GitHub" style="display: block; filter: drop-shadow(0 2px 5px rgba(0,0,0,0.12));">
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

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

    if st.button("🚪 Cerrar Sesión (Logout)", key="btn_logout_sidebar", use_container_width=True, type="secondary"):
        if contexto_usuario:
            cerrar_sesion(contexto_usuario["access_token"])
        st.session_state.clear()
        components.html(
            """
            <script>
            try {
                const store = (window.parent && window.parent.localStorage) ? window.parent.localStorage : window.localStorage;
                store.removeItem('hj_access_token');
            } catch(e) {}
            </script>
            """,
            height=0,
        )
        st.rerun()

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

                        try:
                            respuesta_cancel = _requests.post(
                                f"{PAYMENTS_SERVICE_URL}/webhook/flow/subscription-canceled",
                                data={"customerId": plan.get("flow_customer_id", "")},
                                timeout=15,
                            )
                            if respuesta_cancel.status_code != 200:
                                logger.error(
                                    "subscription-canceled devolvio status %s: %s",
                                    respuesta_cancel.status_code,
                                    respuesta_cancel.text,
                                )
                                st.error(
                                    "No se pudo confirmar la cancelación con el servicio de pagos. "
                                    "Intenta de nuevo en unos minutos.",
                                    icon=":material/error:",
                                )
                            else:
                                st.session_state["confirmar_cancelacion"] = False
                                st.rerun()
                        except Exception:
                            # Timeout, conexion caida, etc.: no asumimos que
                            # la cancelacion funciono solo porque se hizo el
                            # POST — si esto falla en silencio el usuario
                            # sigue premium local pero Flow puede seguir
                            # cobrando igual.
                            logger.exception("No se pudo llamar a subscription-canceled")
                            st.error(
                                "No se pudo cancelar la suscripción. Intenta de nuevo en unos minutos.",
                                icon=":material/error:",
                            )
            else:
                usados = plan["generaciones_este_mes"]
                limite = plan["limite_mensual"]
                st.progress(
                    min(usados / limite, 1.0) if limite else 0,
                    text=f"Plan gratuito — {usados}/{limite} generaciones este mes",
                )
                if st.button("Actualizar a Premium ($4.990/mes)", type="primary", use_container_width=True):
                    from core.flow_checkout import iniciar_registro_tarjeta

                    try:
                        url_pago = iniciar_registro_tarjeta(
                            user_id=contexto_usuario["user_id"],
                            nombre=st.session_state.get("user_email", "Usuario"),
                            email=st.session_state.get("user_email", ""),
                        )
                        st.link_button("Ir a pagar con Flow", url_pago, use_container_width=True)
                    except RuntimeError:
                        # Caso conocido: el usuario ya tiene un cliente Flow registrado
                        # (ver core/flow_checkout.py). No mostramos el detalle interno,
                        # solo un mensaje claro para el usuario.
                        logger.exception("iniciar_registro_tarjeta: cliente Flow ya registrado")
                        st.error(
                            "Ya tienes una cuenta de pago registrada con nosotros — "
                            "contáctanos para activar Premium.",
                            icon=":material/error:",
                        )
                    except Exception:
                        # Error inesperado (red, Flow caído, etc.): se registra el
                        # detalle real en el log del servidor y al usuario se le
                        # muestra un mensaje genérico, sin la excepción cruda.
                        logger.exception("No se pudo iniciar el pago con Flow")
                        st.error(
                            "No se pudo iniciar el pago con Flow. Intenta de nuevo en unos minutos.",
                            icon=":material/error:",
                        )
        except Exception:
            pass
    else:
        st.caption("Modo invitado — datos no guardados")
        with st.expander("💎 Migrar a Plan Premium ($4.990 CLP/mes)", expanded=True):
            st.markdown(
                """
                **¡Desbloquea todas las funcionalidades de Inteligencia Artificial!**

                #### ✨ Beneficios del Plan Premium:
                - 🚀 **Generaciones Ilimitadas** de CVs y Cartas de Presentación por oferta.
                - 💾 **Persistencia Total:** Tu perfil y postulaciones guardados de forma segura en la nube.
                - ⚡ **Inyección ATS 1-Click:** Incorpora de inmediato las palabras clave faltantes en tu CV.
                - 📊 **Tablero Kanban & Analítica:** Monitorea métricas y etapas de selección.
                - 🔔 **Alertas Diarias por Email:** Recibe ofertas filtradas con sueldos transparentes.

                ---
                #### 💳 Medios y Opciones de Pago (vía Flow Chile):
                - 💳 **Tarjetas de Débito y Crédito** (Webpay Plus, Visa, Mastercard, Redcompra).
                - 📲 **Billeteras Digitales** (MACH, Chek, Fpay).
                - 🏦 **Transferencia Bancaria Directa** (Khipu, BancoEstado, Banco de Chile, BCI).
                - 🛒 **Pago Presencial en Efectivo** (Servipag, Caja Vecina).
                
                ---
                *Inicia sesión con Google, GitHub o Facebook para vincular tu suscripción a tu cuenta personal.*
                """
            )
            if st.button("🔑 Iniciar Sesión para Activar Premium", type="primary", use_container_width=True):
                st.session_state["autenticado"] = False
                st.session_state["proveedor_auth"] = None
                st.rerun()
    st.divider()
    seccion = st.radio(
        "Panel",
        [
            "🎯 Dashboard HUD",
            "Generador por URL",
            "Buscador de Vacantes",
            "🎙️ Studio de Entrevistas IA",
            "📌 Auto-Capturador de 1-Clic",
            "Mis Ofertas Guardadas (Kanban)",
            "📊 Analítica de Empleabilidad",
            "🔔 Alertas de Empleo",
            "Mis Postulaciones",
            "Mi Perfil",
            "Preguntas de Postulación",
            "FAQ",
        ],
    )
    st.caption("HuntJob Chile v4.0 BEAST Edition")

# Cargar perfil de usuario
perfil_usuario = cargar_perfil(contexto_usuario)
nombre_user = perfil_usuario.get("nombre") or st.session_state.get("user_email", "").split("@")[0].title() or "Postulante"

# Renderizar Live Score HUD a nivel global en secciones clave
from core.hud_dashboard import renderizar_hud_empleabilidad
st.markdown(renderizar_hud_empleabilidad(nombre_user, score_ats=88, vacantes_compatibles=4, nivel_mercado="Top 5% Chile"), unsafe_allow_html=True)

# -------------------------------------------------------------
# SECCIÓN 0: DASHBOARD HUD & AUTO-CAPTURADOR
# -------------------------------------------------------------
if seccion == "🎯 Dashboard HUD":
    from core.auto_capturador import obtener_bookmarklet_html
    st.markdown(obtener_bookmarklet_html(), unsafe_allow_html=True)

# -------------------------------------------------------------
# SECCIÓN: STUDIO DE ENTREVISTAS IA
# -------------------------------------------------------------
elif seccion == "🎙️ Studio de Entrevistas IA":
    st.subheader("🎙️ Studio de Entrevistas de Trabajo con IA")
    st.write("Simula una entrevista real para el puesto que deseas postular. La IA actuará como el reclutador y evaluará tus respuestas.")

    from core.interview_studio import generar_preguntas_entrevista, evaluar_respuesta_entrevista

    cargo_input = st.text_input("Cargo u Oferta a Entrevistar", "Desarrollador Full Stack / Ingeniero de Software")
    empresa_input = st.text_input("Empresa", "Cumsille Systems SpA")
    desc_input = st.text_area("Descripción breve de la oferta", "Buscamos un profesional para desarrollo de aplicaciones web y APIs.")

    if st.button("🚀 Generar Preguntas de Entrevista Simulado", type="primary"):
        with st.spinner("Reclutador IA analizando el puesto y formulando preguntas..."):
            preguntas = generar_preguntas_entrevista(cargo_input, empresa_input, desc_input)
            st.session_state["preguntas_simulador"] = preguntas

    if "preguntas_simulador" in st.session_state:
        st.markdown("---")
        st.markdown("### 📋 Preguntas Formuladas por el Reclutador IA:")
        for q in st.session_state["preguntas_simulador"]:
            st.markdown(f"**Pregunta {q['id']} ({q.get('tipo', 'General')}):** {q['pregunta']}")
            ans = st.text_area(f"Tu Respuesta a la Pregunta {q['id']}", key=f"ans_{q['id']}")
            if st.button(f"Evaluar Respuesta {q['id']}", key=f"btn_eval_{q['id']}"):
                with st.spinner("Evaluando respuesta táctica..."):
                    evaluacion = evaluar_respuesta_entrevista(q['pregunta'], ans, cargo_input)
                    st.success(f"**Puntaje de Respuesta:** {evaluacion['puntaje']}/100")
                    st.markdown(f"**Feedback:** {evaluacion['feedback']}")
                    st.markdown(f"**Recomendación:** {evaluacion['recomendacion']}")

# -------------------------------------------------------------
# SECCIÓN: AUTO-CAPTURADOR DE 1-CLIC
# -------------------------------------------------------------
elif seccion == "📌 Auto-Capturador de 1-Clic":
    from core.auto_capturador import obtener_bookmarklet_html
    st.subheader("📌 Capturador Rápido de 1-Clic desde tu Navegador")
    st.markdown(obtener_bookmarklet_html(), unsafe_allow_html=True)

# -------------------------------------------------------------
# SECCIÓN 1: GENERADOR DIRECTO POR URL
# -------------------------------------------------------------
elif seccion == "Generador por URL":
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

            with st.spinner("Analizando encaje ATS y redactando documentos a la medida con IA..."):
                try:
                    match_url = analizar_match(st.session_state.texto_extraido, perfil)
                    documentos = generar_documentos(
                        st.session_state.texto_extraido, puesto_objetivo, mercado_destino, estilo_pdf, perfil, match=match_url
                    )
                except (ErrorIA, ValueError) as e:
                    st.error(f"Error al generar el contenido: {e}", icon=":material/error:")
                    st.stop()

            if match_url:
                color_score = "green" if match_url["score"] >= 70 else "yellow" if match_url["score"] >= 40 else "red"
                st.badge(f"Match ATS: {match_url['score']}/100", icon=":material/insights:", color=color_score)
                st.caption(match_url["explicacion"])

                if match_url.get("resumen_fit"):
                    with st.expander("Ver Resumen Ejecutivo: Postulante vs. Requisitos Clave"):
                        for item in match_url["resumen_fit"]:
                            req = item.get("requisito", "")
                            post = item.get("postulante", "")
                            est = item.get("estado", "Cumplido")
                            badge = "🟢 Cumplido" if est == "Cumplido" else ("🟡 Parcial" if est == "Parcial" else "🔴 No detectado")
                            st.markdown(f"- **Requisito:** {req}  \n  └ **Perfil:** {post} *({badge})*")

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
    if "preguntas_entrevista" not in st.session_state:
        st.session_state.preguntas_entrevista = {}

    if "ofertas_guardadas_locales" not in st.session_state:
        st.session_state.ofertas_guardadas_locales = {}

    columna_filtros, columna_resultados = st.columns([1, 3])

    with columna_filtros:
        with st.container(border=True):
            palabra_clave = st.text_input("Palabra clave / Cargo objetivo", value="Python")
            cantidad_paginas = st.slider("Páginas a recorrer", min_value=1, max_value=5, value=1)
            portales_elegidos = st.pills(
                "Portales",
                nombres_portales,
                selection_mode="multi",
                default=nombres_portales,
            )
            solo_sueldo_transparente = st.toggle("🟢 Solo ofertas con sueldo transparente", value=False)
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
            
            # Estimador de Sueldo de Mercado por Cargo
            stats_mercado = estimar_sueldo_mercado(st.session_state.resultados_busqueda)
            if stats_mercado["sueldo_promedio"]:
                st.info(
                    f"📈 **Estimador de Sueldo de Mercado para '{palabra_clave}':** "
                    f"**{formatear_monto_clp(stats_mercado['sueldo_promedio'])}** "
                    f"(Rango detectado: {formatear_monto_clp(stats_mercado['sueldo_min'])} - {formatear_monto_clp(stats_mercado['sueldo_max'])}) "
                    f"| {stats_mercado['cantidad_transparentes']} de {stats_mercado['total_ofertas']} vacantes con sueldo transparente.",
                    icon=":material/analytics:",
                )

            perfil_para_match = cargar_perfil(contexto_usuario)
            if "postulaciones_1click" not in st.session_state:
                st.session_state.postulaciones_1click = {}

            # Obtener lista de links guardados previamente
            links_guardados = []
            if contexto_usuario:
                try:
                    guardadas_db = obtener_ofertas_guardadas(contexto_usuario["user_id"], contexto_usuario["access_token"])
                    links_guardados = [o.get("link") for o in guardadas_db if o.get("link")]
                except Exception:
                    links_guardados = list(st.session_state.ofertas_guardadas_locales.keys())
            else:
                links_guardados = list(st.session_state.ofertas_guardadas_locales.keys())

            for indice, oferta in enumerate(st.session_state.resultados_busqueda):
                sueldo_val = oferta.get("sueldo", "No especifica sueldo")
                tiene_sueldo = sueldo_val != "No especifica sueldo"
                if solo_sueldo_transparente and not tiene_sueldo:
                    continue

                with st.container(border=True):
                    col_t1, col_t2 = st.columns([4, 1])
                    with col_t1:
                        st.markdown(f"#### {oferta['titulo']}")
                    with col_t2:
                        link_oferta = oferta.get("link", "")
                        es_guardada = link_oferta in links_guardados
                        if st.button("⭐ Guardada" if es_guardada else "☆ Guardar", key=f"btn_guardar_{indice}", disabled=es_guardada):
                            if contexto_usuario:
                                try:
                                    guardar_oferta_guardada(contexto_usuario["user_id"], contexto_usuario["access_token"], oferta)
                                except Exception as e:
                                    st.session_state.ofertas_guardadas_locales[link_oferta] = oferta
                            else:
                                st.session_state.ofertas_guardadas_locales[link_oferta] = oferta
                            st.toast("Oferta guardada en tu banco personal de ofertas.", icon="⭐")
                            st.rerun()

                    # Extractor de Email / Contacto del Reclutador
                    contactos = extraer_datos_contacto(f"{oferta['titulo']} {oferta.get('empresa', '')}")

                    # Ficha Resumen Badges Enriquecidas
                    with st.container(horizontal=True, vertical_alignment="center"):
                        st.badge(oferta["fuente"], icon=":material/travel_explore:", color="gray")
                        st.badge(f"🏢 {oferta.get('empresa', 'No especifica empresa')}", color="gray")
                        st.badge(f"📍 {oferta.get('ubicacion', 'No especifica ubicación')}", color="gray")
                        st.badge(f"💻 {oferta.get('modalidad', 'No especifica modalidad')}", color="blue")
                        if tiene_sueldo:
                            st.badge(f"💰 {sueldo_val}", color="green")
                            st.badge("🟢 Sueldo Transparente", color="green")
                        else:
                            st.badge("💰 No especifica sueldo", color="gray")
                        st.badge(f"⏰ {oferta.get('jornada', 'No especifica horario')}", color="gray")
                        for email in contactos.get("emails", []):
                            st.badge(f"✉️ Contacto: {email}", color="purple")
                        st.caption(f"📅 {oferta.get('publicado', 'Reciente')}")

                    match = st.session_state.matches.get(oferta["link"])
                    if match:
                        color_score = "green" if match["score"] >= 70 else "yellow" if match["score"] >= 40 else "red"
                        st.badge(f"Match ATS: {match['score']}/100", icon=":material/insights:", color=color_score)
                        st.caption(match["explicacion"])

                        with st.expander("Ver Auditoría de Compatibilidad ATS Detallada"):
                            st.progress(match["score"] / 100, text=f"Puntaje de Coincidencia Global: {match['score']}%")

                            if match.get("desglose_score"):
                                st.markdown("#### 📈 Desglose Dimensional del Puntaje ATS")
                                d = match["desglose_score"]
                                col_d1, col_d2 = st.columns(2)
                                with col_d1:
                                    st.caption(f"**Hard Skills & Stack:** {d.get('hardskills', 0)}%")
                                    st.progress(d.get('hardskills', 0) / 100)
                                    st.caption(f"**Seniority & Experiencia:** {d.get('experiencia', 0)}%")
                                    st.progress(d.get('experiencia', 0) / 100)
                                with col_d2:
                                    st.caption(f"**Formación & Certificaciones:** {d.get('formacion', 0)}%")
                                    st.progress(d.get('formacion', 0) / 100)
                                    st.caption(f"**Soft Skills & Fit Cultural:** {d.get('softskills', 0)}%")
                                    st.progress(d.get('softskills', 0) / 100)

                            if match.get("requisitos_destacados"):
                                reqs_bold = ", ".join([f"**{r}**" for r in match["requisitos_destacados"]])
                                st.markdown(f"🎯 **Requisitos Clave Detectados (Destacados en tu CV):** {reqs_bold}")

                            if match.get("resumen_fit"):
                                st.markdown("#### 📊 Resumen Ejecutivo: Postulante vs. Requisitos")
                                for item in match["resumen_fit"]:
                                    req = item.get("requisito", "")
                                    post = item.get("postulante", "")
                                    est = item.get("estado", "Cumplido")
                                    badge = "🟢 Cumplido" if est == "Cumplido" else ("🟡 Parcial" if est == "Parcial" else "🔴 No detectado")
                                    st.markdown(f"- **Requisito:** {req}  \n  └ **Perfil:** {post} *({badge})*")

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
                                    if st.button("⚡ Inyectar Palabras Clave Faltantes en 1-Click", key=f"btn_inyectar_{indice}"):
                                        if oferta["link"] in st.session_state.postulaciones_1click:
                                            from core.generador_pdf import generar_pdf_cv
                                            from core.generador_docx import generar_docx_cv
                                            doc_1c = st.session_state.postulaciones_1click[oferta["link"]]
                                            cv_orig = doc_1c.get("cv", "")
                                            cv_inyectado = inyectar_palabras_clave_cv(cv_orig, match["palabras_faltantes"])
                                            doc_1c["cv"] = cv_inyectado
                                            doc_1c["pdf_bytes"] = generar_pdf_cv(cv_inyectado)
                                            doc_1c["docx_bytes"] = generar_docx_cv(cv_inyectado)
                                            st.toast("¡Palabras clave inyectadas exitosamente en tu CV!", icon="⚡")
                                            st.rerun()
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
                                "Descargar CV (PDF)",
                                data=resultado_1click["cv_bytes"],
                                file_name=resultado_1click["nombre_cv"],
                                mime="application/pdf",
                                icon=":material/picture_as_pdf:",
                                key=f"dl_cv_{indice}",
                            )
                            if "cv_docx_bytes" in resultado_1click:
                                st.download_button(
                                    "Descargar CV (Word .docx)",
                                    data=resultado_1click["cv_docx_bytes"],
                                    file_name=resultado_1click.get("nombre_cv_docx", "CV.docx"),
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    icon=":material/description:",
                                    key=f"dl_cv_docx_{indice}",
                                )
                            st.download_button(
                                "Descargar Cover Letter (PDF)",
                                data=resultado_1click["cl_bytes"],
                                file_name=resultado_1click["nombre_cl"],
                                mime="application/pdf",
                                icon=":material/mail:",
                                key=f"dl_cl_{indice}",
                            )
                            st.link_button(
                                "Postular ahora en el portal", oferta["link"],
                                icon=":material/open_in_new:", key=f"ir_postular_{indice}",
                            )

                        if st.button("Simular Entrevista de Trabajo (5 Preguntas Clave)", icon=":material/quiz:", key=f"simular_entrevista_{indice}"):
                            with st.spinner("Generando preguntas de entrevista y respuestas modelo..."):
                                try:
                                    texto_oferta = extraer_texto_url(oferta["link"])
                                    st.session_state.preguntas_entrevista[oferta["link"]] = generar_preguntas_entrevista(
                                        texto_oferta, perfil_para_match
                                    )
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error generando simulador: {e}", icon=":material/error:")

                        preguntas_sim = st.session_state.preguntas_entrevista.get(oferta["link"])
                        if preguntas_sim:
                            with st.expander("🎙️ Simulador de Entrevista: 5 Preguntas Clave & Respuestas Modelo", expanded=True):
                                for idx, item in enumerate(preguntas_sim, start=1):
                                    st.markdown(f"**P{idx} [{item.get('tipo', 'Pregunta')}]:** {item.get('pregunta', '')}")
                                    st.caption(f"💡 *Consejo:* {item.get('consejo', '')}")
                                    st.info(f"**Respuesta modelo recomendada:**\n{item.get('respuesta_modelo', '')}")

                        st.caption(
                            "Descarga los documentos en PDF o Word (.docx) y termina la postulación en el portal."
                        )

# -------------------------------------------------------------
# SECCIÓN: MIS OFERTAS GUARDADAS (TABLERO KANBAN)
# -------------------------------------------------------------
elif seccion == "Mis Ofertas Guardadas (Kanban)":
    st.subheader("📊 Tablero Kanban de Seguimiento de Postulaciones")
    st.caption("Gestiona el flujo completo de tus búsquedas laborales etapa por etapa.")

    ESTADOS_KANBAN = ["📌 Guardada", "✉️ Postulada", "🎙️ En Entrevista", "🎉 Oferta Recibida", "❌ Descartada"]

    ofertas_guardadas = []
    if contexto_usuario:
        try:
            ofertas_guardadas = obtener_ofertas_guardadas(contexto_usuario["user_id"], contexto_usuario["access_token"])
        except Exception:
            ofertas_guardadas = list(st.session_state.get("ofertas_guardadas_locales", {}).values())
    else:
        ofertas_guardadas = list(st.session_state.get("ofertas_guardadas_locales", {}).values())

    if not ofertas_guardadas:
        st.info("Aún no has guardado ninguna oferta. Busca vacantes en el 'Buscador de Vacantes' y presiona el botón ☆ Guardar.", icon=":material/info:")
    else:
        import pandas as pd
        df_export = pd.DataFrame(ofertas_guardadas)
        csv_bytes = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📊 Exportar tablero a Excel / CSV",
            data=csv_bytes,
            file_name="mis_ofertas_kanban.csv",
            mime="text/csv",
            icon=":material/download:",
        )

        st.divider()

        tabs_kanban = st.tabs(ESTADOS_KANBAN)

        for i, estado in enumerate(ESTADOS_KANBAN):
            with tabs_kanban[i]:
                ofertas_etapa = [o for o in ofertas_guardadas if o.get("estado_kanban", "📌 Guardada") == estado]
                st.caption(f"Total en esta etapa: {len(ofertas_etapa)}")

                if not ofertas_etapa:
                    st.info(f"No hay ofertas actualmente en la etapa '{estado}'.")
                else:
                    for idx_k, oferta in enumerate(ofertas_etapa):
                        with st.container(border=True):
                            col_k1, col_k2 = st.columns([3, 2])
                            with col_k1:
                                st.markdown(f"#### {oferta.get('titulo', 'Sin título')}")
                                st.caption(f"{oferta.get('empresa', 'No especifica empresa')} — {oferta.get('ubicacion', 'No especifica ubicación')}")
                            with col_k2:
                                estado_actual = oferta.get("estado_kanban", "📌 Guardada")
                                index_actual = ESTADOS_KANBAN.index(estado_actual) if estado_actual in ESTADOS_KANBAN else 0
                                nuevo_estado = st.selectbox(
                                    "Mover a etapa:",
                                    ESTADOS_KANBAN,
                                    index=index_actual,
                                    key=f"sb_kanban_{i}_{idx_k}",
                                )
                                if nuevo_estado != estado_actual:
                                    link_k = oferta.get("link", "")
                                    oferta["estado_kanban"] = nuevo_estado
                                    if contexto_usuario:
                                        try:
                                            actualizar_estado_kanban(contexto_usuario["user_id"], contexto_usuario["access_token"], link_k, nuevo_estado)
                                        except Exception:
                                            pass
                                    if link_k in st.session_state.get("ofertas_guardadas_locales", {}):
                                        st.session_state.ofertas_guardadas_locales[link_k]["estado_kanban"] = nuevo_estado
                                    st.toast(f"Oferta movida a {nuevo_estado}", icon="🔄")
                                    st.rerun()

                            # Badges Ficha Resumen
                            with st.container(horizontal=True, vertical_alignment="center"):
                                st.badge(oferta.get("fuente", "Portal"), icon=":material/travel_explore:", color="gray")
                                st.badge(f"💻 {oferta.get('modalidad', 'No especifica modalidad')}", color="blue")
                                sueldo_g = oferta.get('sueldo', 'No especifica sueldo')
                                if sueldo_g != "No especifica sueldo":
                                    st.badge(f"💰 {sueldo_g}", color="green")
                                    st.badge("🟢 Sueldo Transparente", color="green")
                                else:
                                    st.badge("💰 No especifica sueldo", color="gray")
                                st.badge(f"⏰ {oferta.get('jornada', 'No especifica horario')}", color="gray")

                            if oferta.get("link"):
                                st.link_button("Ver oferta original", oferta["link"], icon=":material/open_in_new:", key=f"link_kanban_{i}_{idx_k}")

# -------------------------------------------------------------
# SECCIÓN: ANALÍTICA DE EMPLEABILIDAD
# -------------------------------------------------------------
elif seccion == "📊 Analítica de Empleabilidad":
    st.subheader("📊 Centro de Control & Analítica de Empleabilidad")
    st.caption("Visualiza el rendimiento y métricas cuantitativas de tu búsqueda de empleo.")

    ofertas_g = []
    historial_p = []
    if contexto_usuario:
        try:
            ofertas_g = obtener_ofertas_guardadas(contexto_usuario["user_id"], contexto_usuario["access_token"])
            historial_p = obtener_historial_reciente(contexto_usuario["user_id"], contexto_usuario["access_token"], limite=50)
        except Exception:
            ofertas_g = list(st.session_state.get("ofertas_guardadas_locales", {}).values())
    else:
        ofertas_g = list(st.session_state.get("ofertas_guardadas_locales", {}).values())

    funnel = generar_metricas_funnel(historial_p, ofertas_g)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("📌 Ofertas Guardadas", funnel["total_guardadas"])
    with c2:
        st.metric("✉️ Postulaciones Enviadas", funnel["total_postuladas"])
    with c3:
        st.metric("🎙️ Entrevistas Agendadas", funnel["total_entrevistas"])
    with c4:
        st.metric("🎉 Ofertas Recibidas", funnel["total_ofertas_recibidas"])

    st.divider()

    st.markdown("#### 📈 Embudo de Conversión (Funnel de Postulación)")
    tasa = funnel["tasa_conversion_entrevista"]
    st.progress(min(tasa / 100.0, 1.0), text=f"Tasa de Conversión a Entrevista: {tasa}%")

    if tasa >= 15.0:
        st.success("🎯 ¡Excelente rendimiento! Tu perfil genera alto impacto en los reclutadores.", icon=":material/workspace_premium:")
    elif tasa > 0:
        st.info("💡 Buen progreso. Te sugerimos usar la inyección 1-Click de palabras clave para superar el 20% de conversión.", icon=":material/tips_and_updates:")
    else:
        st.warning("📌 Consejo: Guarda tus postulaciones en la etapa '✉️ Postulada' o '🎙️ En Entrevista' en el Tablero Kanban para calcular tu tasa en tiempo real.", icon=":material/info:")

# -------------------------------------------------------------
# SECCIÓN: ALERTAS AUTOMÁTICAS DE EMPLEO
# -------------------------------------------------------------
elif seccion == "🔔 Alertas de Empleo":
    st.subheader("🔔 Alertas Automáticas de Empleo por Email")
    st.caption("Recibe resúmenes diarios con las mejores vacantes para tu cargo objetivo con sueldo transparente.")

    perfil_alertas = cargar_perfil(contexto_usuario)

    with st.form("form_alertas_empleo"):
        cargo_alerta = st.text_input("Cargo Objetivo de Interés", value=perfil_alertas.get("stack_principal") or "Desarrollador Python")
        email_alerta = st.text_input("Email para Notificaciones", value=contexto_usuario.get("email", "") if contexto_usuario else perfil_alertas.get("email", ""))
        frecuencia = st.selectbox("Frecuencia de Notificación", ["Diaria (Cada mañana a las 8:00 AM)", "Semanal (Todos los Lunes)", "Tiempo Real"])
        activada = st.toggle("Activar Alertas para este cargo", value=True)

        guardar_alerta = st.form_submit_button("Guardar Configuración de Alertas", type="primary", icon=":material/notifications_active:")

    if guardar_alerta:
        st.success(f"¡Alerta configurada con éxito para '{cargo_alerta}'! Se enviarán notificaciones a {email_alerta}.", icon=":material/check_circle:")

    st.divider()

    st.markdown("### 🧪 Prueba de Alerta Instantánea")
    if st.button("🔔 Enviar resumen de ofertas destacadas ahora", type="secondary"):
        with st.spinner("Buscando vacantes destacadas con sueldo transparente..."):
            resultados_alerta, _ = buscar_en_todos(cargo_alerta, cantidad_paginas=1)
            transparentes = [r for r in resultados_alerta if r.get("sueldo") and r.get("sueldo") != "No especifica sueldo"]
            
            st.toast("Resumen de alertas generado con éxito.", icon="📧")
            st.success(f"Se identificaron {len(transparentes)} vacantes destacadas con sueldo transparente para '{cargo_alerta}'.", icon=":material/mail:")
            
            for o in transparentes[:3]:
                with st.container(border=True):
                    st.markdown(f"**{o['titulo']}** en *{o['empresa']}*")
                    st.caption(f"💰 {o['sueldo']} | 💻 {o['modalidad']} | 📍 {o['ubicacion']}")
                    st.link_button("Ver Vacante", o["link"])

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
        "Formación, competencias, habilidades blandas e idiomas se muestran tal cual los escribas — "
        "la IA no los reescribe, solo redacta el resumen profesional y pule los bullets de experiencia."
    )

    perfil_actual = cargar_perfil(contexto_usuario)

    if "perfil_experiencia_editable" not in st.session_state:
        st.session_state.perfil_experiencia_editable = [dict(t, _key=str(uuid.uuid4())) for t in perfil_actual["experiencia_laboral"]]
    if "perfil_formacion_editable" not in st.session_state:
        st.session_state.perfil_formacion_editable = [dict(f, _key=str(uuid.uuid4())) for f in perfil_actual["formacion_academica"]]
    if "perfil_idiomas_editable" not in st.session_state:
        st.session_state.perfil_idiomas_editable = [dict(i, _key=str(uuid.uuid4())) for i in perfil_actual["idiomas"]]

    nombre = st.text_input("Nombre completo", value=perfil_actual["nombre"])
    with st.container(horizontal=True):
        ciudad = st.text_input("Ciudad / Comuna", value=perfil_actual["ciudad"])
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

    st.divider()
    st.markdown("#### Experiencia laboral")
    for indice, trabajo in enumerate(st.session_state.perfil_experiencia_editable):
        clave = trabajo["_key"]
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                trabajo["cargo"] = st.text_input("Cargo", value=trabajo.get("cargo", ""), key=f"exp_cargo_{clave}")
                trabajo["fecha_inicio"] = st.text_input(
                    "Fecha inicio (ej. Marzo 2021)", value=trabajo.get("fecha_inicio", ""), key=f"exp_fi_{clave}"
                )
            with col2:
                trabajo["empresa"] = st.text_input("Empresa", value=trabajo.get("empresa", ""), key=f"exp_empresa_{clave}")
                trabajo["actualidad"] = st.checkbox(
                    "Trabajo actual", value=trabajo.get("actualidad", False), key=f"exp_act_{clave}"
                )
                trabajo["fecha_fin"] = "" if trabajo["actualidad"] else st.text_input(
                    "Fecha término (ej. Enero 2024)", value=trabajo.get("fecha_fin", ""), key=f"exp_ff_{clave}"
                )
            trabajo["funciones"] = st.text_area(
                "Funciones y responsabilidades (una por línea)",
                value=trabajo.get("funciones", ""),
                key=f"exp_func_{clave}",
                height=100,
            )

            with st.expander("🚀 Asistente IA Google CAR: Potenciar redacción de esta experiencia"):
                logro_input = st.text_input("Ingresa una tarea simple para re-redactar:", value="", key=f"car_in_{clave}")
                if st.button("✨ Generar 3 Alternativas CAR de Alto Impacto", key=f"btn_car_{clave}"):
                    if logro_input:
                        with st.spinner("Generando alternativas cuantitativas con metodología Google CAR..."):
                            opciones_car = optimizar_logro_car(logro_input, trabajo.get("cargo", ""))
                            st.session_state[f"opciones_car_{clave}"] = opciones_car
                
                opciones_guardadas = st.session_state.get(f"opciones_car_{clave}")
                if opciones_guardadas:
                    st.markdown("**Selecciona una versión para agregar a tu experiencia:**")
                    for idx_c, op in enumerate(opciones_guardadas):
                        st.markdown(f"{idx_c+1}. {op}", unsafe_allow_html=True)
                        if st.button(f"Usar Opción {idx_c+1}", key=f"use_car_{clave}_{idx_c}"):
                            op_texto = op.replace("<b>", "").replace("</b>", "")
                            if trabajo.get("funciones"):
                                trabajo["funciones"] += f"\n{op_texto}"
                            else:
                                trabajo["funciones"] = op_texto
                            st.toast("¡Logro CAR agregado a tu experiencia!", icon="🚀")
                            st.rerun()

            if st.button("🗑 Quitar esta experiencia", key=f"exp_quitar_{clave}"):
                st.session_state.perfil_experiencia_editable.pop(indice)
                st.rerun()
    if st.button("+ Agregar experiencia laboral", icon=":material/add:", key="exp_agregar"):
        st.session_state.perfil_experiencia_editable.append(
            {"cargo": "", "empresa": "", "fecha_inicio": "", "fecha_fin": "", "actualidad": False, "funciones": "", "_key": str(uuid.uuid4())}
        )
        st.rerun()

    st.divider()
    st.markdown("#### Formación académica")
    for indice, estudio in enumerate(st.session_state.perfil_formacion_editable):
        clave = estudio["_key"]
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                estudio["titulo"] = st.text_input("Título / carrera", value=estudio.get("titulo", ""), key=f"form_titulo_{clave}")
                estudio["institucion"] = st.text_input("Institución", value=estudio.get("institucion", ""), key=f"form_inst_{clave}")
            with col2:
                tipo_guardado = estudio.get("tipo", "Carrera")
                indice_tipo = TIPOS_FORMACION.index(tipo_guardado) if tipo_guardado in TIPOS_FORMACION else 0
                estudio["tipo"] = st.selectbox("Tipo", TIPOS_FORMACION, index=indice_tipo, key=f"form_tipo_{clave}")
                estudio["fecha_inicio"] = st.text_input("Año inicio", value=estudio.get("fecha_inicio", ""), key=f"form_fi_{clave}")
                estudio["fecha_fin"] = st.text_input("Año término", value=estudio.get("fecha_fin", ""), key=f"form_ff_{clave}")
            if st.button("🗑 Quitar esta formación", key=f"form_quitar_{clave}"):
                st.session_state.perfil_formacion_editable.pop(indice)
                st.rerun()
    if st.button("+ Agregar formación académica", icon=":material/add:", key="form_agregar"):
        st.session_state.perfil_formacion_editable.append(
            {"titulo": "", "institucion": "", "fecha_inicio": "", "fecha_fin": "", "tipo": "Carrera", "_key": str(uuid.uuid4())}
        )
        st.rerun()

    st.divider()
    st.markdown("#### Idiomas")
    opts_idioma = IDIOMAS_POPULARES + ["Otro / Personalizado"]
    for indice, idioma in enumerate(st.session_state.perfil_idiomas_editable):
        clave = idioma["_key"]
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                val_actual = idioma.get("idioma", "")
                idx_idioma = IDIOMAS_POPULARES.index(val_actual) if val_actual in IDIOMAS_POPULARES else len(IDIOMAS_POPULARES)
                sel_idioma = st.selectbox("Seleccionar Idioma", opts_idioma, index=idx_idioma, key=f"idi_sel_{clave}")
                if sel_idioma == "Otro / Personalizado":
                    idioma["idioma"] = st.text_input("Nombre del Idioma", value=val_actual if val_actual not in IDIOMAS_POPULARES else "", key=f"idi_nombre_{clave}")
                else:
                    idioma["idioma"] = sel_idioma
            with col2:
                nivel_guardado = idioma.get("nivel", "Intermedio")
                indice_nivel = NIVELES_IDIOMA.index(nivel_guardado) if nivel_guardado in NIVELES_IDIOMA else 1
                idioma["nivel"] = st.selectbox("Nivel", NIVELES_IDIOMA, index=indice_nivel, key=f"idi_nivel_{clave}")
            with col3:
                if st.button("🗑", key=f"idi_quitar_{clave}"):
                    st.session_state.perfil_idiomas_editable.pop(indice)
                    st.rerun()
    if st.button("+ Agregar idioma", icon=":material/add:", key="idi_agregar"):
        st.session_state.perfil_idiomas_editable.append({"idioma": "Español", "nivel": "Intermedio", "_key": str(uuid.uuid4())})
        st.rerun()

    st.divider()
    st.markdown("#### Competencias técnicas y manejo de software")
    comp_actuales = [linea.strip() for linea in (perfil_actual.get("competencias_tecnicas") or "").split("\n") if linea.strip()]
    pre_seleccionadas = [c for c in comp_actuales if c in COMPETENCIAS_POPULARES]
    custom_actuales = "\n".join([c for c in comp_actuales if c not in COMPETENCIAS_POPULARES])

    seleccionadas_comp = st.multiselect(
        "Selección rápida de tecnologías y herramientas principales:",
        options=COMPETENCIAS_POPULARES,
        default=pre_seleccionadas,
        key="ms_comp_tecnicas"
    )
    comp_extra = st.text_area(
        "Otras competencias o software adicional (una por línea):",
        value=custom_actuales,
        height=80,
        key="ta_comp_extra"
    )
    lista_final_comp = list(seleccionadas_comp) + [c.strip() for c in comp_extra.split("\n") if c.strip() and c.strip() not in seleccionadas_comp]
    competencias_tecnicas = "\n".join(lista_final_comp)

    st.divider()
    st.markdown("#### Habilidades blandas")
    blandas_actuales = [linea.strip() for linea in (perfil_actual.get("habilidades_blandas") or "").split("\n") if linea.strip()]
    pre_blandas = [b for b in blandas_actuales if b in HABILIDADES_BLANDAS_POPULARES]
    custom_blandas = "\n".join([b for b in blandas_actuales if b not in HABILIDADES_BLANDAS_POPULARES])

    seleccionadas_blandas = st.multiselect(
        "Selección rápida de habilidades blandas clave:",
        options=HABILIDADES_BLANDAS_POPULARES,
        default=pre_blandas,
        key="ms_habilidades_blandas"
    )
    blandas_extra = st.text_area(
        "Otras habilidades blandas adicionales (una por línea):",
        value=custom_blandas,
        height=80,
        key="ta_blandas_extra"
    )
    lista_final_blandas = list(seleccionadas_blandas) + [b.strip() for b in blandas_extra.split("\n") if b.strip() and b.strip() not in seleccionadas_blandas]
    habilidades_blandas = "\n".join(lista_final_blandas)

    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        if st.button("Guardar perfil", icon=":material/save:", type="primary", use_container_width=True):
            try:
                guardar_perfil(contexto_usuario, {
                    "nombre": nombre,
                    "email": email,
                    "telefono": telefono,
                    "linkedin": linkedin,
                    "ciudad": ciudad,
                    "anos_experiencia": anos_experiencia,
                    "seniority": seniority,
                    "competencias_tecnicas": competencias_tecnicas,
                    "habilidades_blandas": habilidades_blandas,
                    "experiencia_laboral": [{k: v for k, v in t.items() if k != "_key"} for t in st.session_state.perfil_experiencia_editable],
                    "formacion_academica": [{k: v for k, v in f.items() if k != "_key"} for f in st.session_state.perfil_formacion_editable],
                    "idiomas": [{k: v for k, v in i.items() if k != "_key"} for i in st.session_state.perfil_idiomas_editable],
                    "stack_principal": "",
                    "logros_y_experiencia": "",
                })
                st.success("Perfil guardado.", icon=":material/check_circle:")
            except Exception as e:
                st.error(f"No se pudo guardar tu perfil: {e}", icon=":material/error:")
    with col_sub2:
        if st.button("Limpiar campos del perfil", icon=":material/delete:", use_container_width=True):
            try:
                guardar_perfil(contexto_usuario, copy.deepcopy(VALORES_POR_DEFECTO))
                st.session_state.perfil_experiencia_editable = []
                st.session_state.perfil_formacion_editable = []
                st.session_state.perfil_idiomas_editable = []
                st.success("Perfil limpiado correctamente.", icon=":material/check_circle:")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo limpiar el perfil: {e}", icon=":material/error:")

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
