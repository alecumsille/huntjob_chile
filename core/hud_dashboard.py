"""
Live Score HUD Component — Dashboard de Mando de Empleabilidad HuntJob Chile.
Estética Premium Titanium Slate + Cyan Neon / Glassmorphism.
"""

import html


def renderizar_hud_empleabilidad(nombre: str, score_ats: int, vacantes_compatibles: int = 4, nivel_mercado: str = "Top 5% Chile") -> str:
    """
    Genera el HTML/CSS del Dashboard Hero HUD limpio sin sangrías ni comentarios HTML que puedan romper el parser de Streamlit.
    """
    nombre_clean = html.escape(nombre or "Postulante")
    color_score = "#10B981" if score_ats >= 80 else ("#F59E0B" if score_ats >= 60 else "#F43F5E")
    circunferencia = 282
    offset = int(circunferencia - (circunferencia * score_ats / 100))

    html_hud = (
        f'<div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border-radius: 18px; border: 1px solid #334155; padding: 20px 24px; color: #F8FAFC; margin-bottom: 20px;">'
        f'<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;">'
        f'<div style="flex: 1; min-width: 220px;">'
        f'<div style="display: inline-block; background: rgba(14,165,233,0.2); border: 1px solid #38BDF8; border-radius: 15px; padding: 3px 12px; font-size: 0.75rem; font-weight: 700; color: #38BDF8; margin-bottom: 8px;">CENTER HUD &bull; {nivel_mercado}</div>'
        f'<h3 style="font-family: sans-serif; font-weight: 800; font-size: 1.5rem; color: #FFFFFF; margin: 0 0 4px 0;">¡Hola, {nombre_clean}!</h3>'
        f'<p style="color: #94A3B8; font-size: 0.85rem; margin: 0;">Tu ecosistema de postulación está activo y optimizado con IA.</p>'
        f'</div>'
        f'<div style="display: flex; align-items: center; gap: 15px; background: rgba(15,23,42,0.7); padding: 10px 18px; border-radius: 14px; border: 1px solid #334155;">'
        f'<div style="position: relative; width: 80px; height: 80px; display: flex; align-items: center; justify-content: center;">'
        f'<svg width="80" height="80" viewBox="0 0 100 100">'
        f'<circle cx="50" cy="50" r="45" fill="none" stroke="#1E293B" stroke-width="8" />'
        f'<circle cx="50" cy="50" r="45" fill="none" stroke="{color_score}" stroke-width="8" stroke-dasharray="{circunferencia}" stroke-dashoffset="{offset}" stroke-linecap="round" transform="rotate(-90 50 50)" />'
        f'</svg>'
        f'<span style="position: absolute; font-size: 1.25rem; font-weight: 800; color: #F8FAFC;">{score_ats}%</span>'
        f'</div>'
        f'<div>'
        f'<div style="font-size: 0.75rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Match Global</div>'
        f'<div style="font-size: 1rem; font-weight: 700; color: {color_score};">Competitivo</div>'
        f'</div>'
        f'</div>'
        f'<div style="display: flex; gap: 10px;">'
        f'<div style="background: rgba(30,41,59,0.8); border: 1px solid #334155; border-radius: 12px; padding: 8px 14px; text-align: center;">'
        f'<div style="font-size: 1.2rem; font-weight: 800; color: #38BDF8;">{vacantes_compatibles}</div>'
        f'<div style="font-size: 0.7rem; color: #94A3B8;">Ofertas >90%</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    return html_hud
