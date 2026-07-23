"""
Live Score HUD Component — Dashboard de Mando de Empleabilidad HuntJob Chile.
Estética Premium Titanium Slate + Cyan Neon / Glassmorphism.

Genera el panel de control táctico que mide el Nivel de Empleabilidad del candidato,
su posición en el mercado chileno y métricas clave en vivo.
"""

import html


def renderizar_hud_empleabilidad(nombre: str, score_ats: int, vacantes_compatibles: int = 3, nivel_mercado: str = "Top 5% Chile") -> str:
    """
    Genera el HTML/CSS del Dashboard Hero HUD con estética Glassmorphism Neón.
    """
    nombre_clean = html.escape(nombre or "Postulante")
    color_score = "#10B981" if score_ats >= 80 else ("#F59E0B" if score_ats >= 60 else "#F43F5E")
    circunferencia = 282
    offset = circunferencia - (circunferencia * score_ats / 100)

    html_hud = f"""
    <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border-radius: 20px; border: 1px solid #334155; padding: 24px 28px; box-shadow: 0 15px 35px rgba(0,0,0,0.25); color: #F8FAFC; margin-bottom: 25px; position: relative; overflow: hidden;">
        
        <!-- Elemento Decorativo Neón -->
        <div style="position: absolute; top: -50px; right: -50px; width: 180px; height: 180px; background: radial-gradient(circle, rgba(14,165,233,0.2) 0%, rgba(0,0,0,0) 70%); pointer-events: none;"></div>

        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px;">
            
            <!-- Izquierda: Perfil y Seniority -->
            <div style="flex: 1; min-width: 250px;">
                <div style="display: inline-block; background: rgba(14,165,233,0.15); border: 1px solid rgba(14,165,233,0.3); border-radius: 20px; padding: 4px 14px; font-size: 0.78rem; font-weight: 700; color: #38BDF8; letter-spacing: 0.5px; margin-bottom: 10px;">
                    CENTER HUD &bull; {nivel_mercado}
                </div>
                <h2 style="font-family: 'Quicksand', sans-serif; font-weight: 800; font-size: 1.7rem; color: #FFFFFF; margin: 0 0 6px 0; line-height: 1.2;">
                    ¡Hola, {nombre_clean}!
                </h2>
                <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">
                    Tu ecosistema de postulación está activo y optimizado con IA.
                </p>
            </div>

            <!-- Centro: Medidor Gauge de Compatibilidad -->
            <div style="display: flex; align-items: center; gap: 16px; background: rgba(15,23,42,0.6); padding: 12px 20px; border-radius: 16px; border: 1px solid #334155;">
                <div style="position: relative; width: 90px; height: 90px; display: flex; align-items: center; justify-content: center;">
                    <svg width="90" height="90" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#1E293B" stroke-width="8" />
                        <circle cx="50" cy="50" r="45" fill="none" stroke="{color_score}" stroke-width="8"
                                stroke-dasharray="{circunferencia}" stroke-dashoffset="{offset}" stroke-linecap="round" transform="rotate(-90 50 50)" />
                    </svg>
                    <span style="position: absolute; font-size: 1.4rem; font-weight: 800; color: #F8FAFC;">{score_ats}%</span>
                </div>
                <div>
                    <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; color: #94A3B8; font-weight: 600;">Match Global</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: {color_score};">
                        {"Óptimo Competitivo" if score_ats >= 80 else ("Perfil Adecuado" if score_ats >= 60 else "Requiere Ajuste")}
                    </div>
                </div>
            </div>

            <!-- Derecha: Métricas Rápidas -->
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                <div style="background: rgba(30,41,59,0.7); border: 1px solid #334155; border-radius: 12px; padding: 10px 16px; text-align: center; min-width: 100px;">
                    <div style="font-size: 1.3rem; font-weight: 800; color: #38BDF8;">{vacantes_compatibles}</div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">Ofertas >90%</div>
                </div>
                <div style="background: rgba(30,41,59,0.7); border: 1px solid #334155; border-radius: 12px; padding: 10px 16px; text-align: center; min-width: 100px;">
                    <div style="font-size: 1.3rem; font-weight: 800; color: #10B981;">100%</div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">ATS Chile Ready</div>
                </div>
            </div>

        </div>
    </div>
    """
    return html_hud
