"""
Generador de Tarjetas de Previsualización Social OpenGraph (OG:Image) — HuntJob Chile.
Inspirado en Kocal/open-graph-image-generator y dynamic-og-images-example.

Genera tarjetas visuales en formato HTML/SVG con la puntuación de Match ATS del postulante,
cargo objetivo y nivel de coincidencia para compartir en LinkedIn, Twitter/X y WhatsApp.
"""

import html


def generar_tarjeta_og_svg(nombre: str, cargo: str, score_ats: int, nivel_match: str) -> str:
    """
    Genera el código SVG de alta resolución para la tarjeta de previsualización social OpenGraph.
    """
    nombre_clean = html.escape(nombre or "Postulante")
    cargo_clean = html.escape(cargo or "Profesional")

    color_score = "#10B981" if score_ats >= 80 else ("#F59E0B" if score_ats >= 60 else "#F43F5E")

    svg_content = f"""<svg width="1200" height="630" viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0F172A" />
      <stop offset="100%" stop-color="#1E293B" />
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0EA5E9" />
      <stop offset="100%" stop-color="#6366F1" />
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="1200" height="630" fill="url(#bg)" />
  <rect x="0" y="0" width="1200" height="8" fill="url(#accent)" />

  <!-- Grid Glow Pattern -->
  <circle cx="1000" cy="100" r="300" fill="#0EA5E9" opacity="0.08" filter="blur(60px)" />
  <circle cx="200" cy="500" r="250" fill="#6366F1" opacity="0.08" filter="blur(60px)" />

  <!-- Badge Header -->
  <rect x="80" y="80" width="180" height="36" rx="18" fill="#0EA5E9" opacity="0.15" />
  <text x="170" y="104" font-family="sans-serif" font-size="14" font-weight="700" fill="#0EA5E9" text-anchor="middle">HUNTJOB CHILE</text>

  <!-- Candidate Name & Role -->
  <text x="80" y="200" font-family="sans-serif" font-size="44" font-weight="800" fill="#F8FAFC">{nombre_clean}</text>
  <text x="80" y="245" font-family="sans-serif" font-size="24" font-weight="500" fill="#94A3B8">Postulación a: {cargo_clean}</text>

  <!-- Score Ring Card -->
  <rect x="80" y="310" width="1040" height="240" rx="16" fill="#1E293B" stroke="#334155" stroke-width="2" />

  <!-- Score Circle -->
  <circle cx="200" cy="430" r="70" fill="none" stroke="#334155" stroke-width="12" />
  <circle cx="200" cy="430" r="70" fill="none" stroke="{color_score}" stroke-width="12" stroke-dasharray="440" stroke-dashoffset="{440 - (440 * score_ats / 100)}" stroke-linecap="round" />
  <text x="200" y="440" font-family="sans-serif" font-size="42" font-weight="800" fill="#F8FAFC" text-anchor="middle">{score_ats}%</text>

  <!-- Match Details -->
  <text x="320" y="400" font-family="sans-serif" font-size="28" font-weight="700" fill="#F8FAFC">Compatibilidad ATS: {nivel_match}</text>
  <text x="320" y="440" font-family="sans-serif" font-size="18" fill="#94A3B8">Currículum optimizado con IA y alineado a la normativa laboral chilena.</text>

  <!-- Footer Link -->
  <text x="1120" y="600" font-family="sans-serif" font-size="16" font-weight="600" fill="#64748B" text-anchor="end">https://huntjob.cumsille.me</text>
</svg>"""

    return svg_content
