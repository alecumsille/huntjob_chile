"""
Auto-Capturador de Ofertas Laborales — HuntJob Chile.

Bookmarklet / Script de 1-Clic para capturar ofertas desde cualquier sitio web
(LinkedIn, ChileTrabajos, Laborum, Computrabajo) y procesarlas automáticamente.
"""

BOOKMARKLET_JS_CODE = """javascript:(function(){
    var titulo = document.querySelector('h1')?.innerText || document.title;
    var texto = document.body.innerText.substring(0, 3000);
    var targetUrl = 'https://huntjob.cumsille.me/?import_title=' + encodeURIComponent(titulo) + '&import_text=' + encodeURIComponent(texto);
    window.open(targetUrl, '_blank');
})();"""


def obtener_bookmarklet_html() -> str:
    """
    Devuelve el código HTML para arrastrar el botón flotante a la barra de marcadores del navegador.
    """
    html_code = f"""
    <div style="background: #1E293B; border-radius: 12px; border: 1px solid #334155; padding: 16px; margin: 15px 0;">
        <h4 style="color: #F8FAFC; margin-top: 0; margin-bottom: 8px;">🚀 Capturador Rápido de 1-Clic (Bookmarklet)</h4>
        <p style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 12px;">
            Arrastra el siguiente botón a la <strong>Barra de Marcadores</strong> de tu navegador (Chrome, Edge, Brave). 
            Cuando veas una oferta de trabajo en LinkedIn o ChileTrabajos, haz 1-Clic para enviarla a HuntJob.
        </p>
        <div style="text-align: center;">
            <a href="{BOOKMARKLET_JS_CODE}" style="display: inline-block; background: linear-gradient(135deg, #0EA5E9 0%, #6366F1 100%); color: #FFFFFF; font-weight: 700; padding: 10px 20px; border-radius: 20px; text-decoration: none; box-shadow: 0 4px 12px rgba(14,165,233,0.3); cursor: move;">
                📌 Capturar con HuntJob
            </a>
        </div>
    </div>
    """
    return html_code
