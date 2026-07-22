"""
Genera el CV y la Cover Letter para una oferta puntual. Único lugar
donde vive este prompt — lo usan tanto el "Generador por URL" como el
botón de 1-click desde el buscador, para no mantener el mismo texto
duplicado en dos pantallas.
"""

import os

from core.motor_ia import generar_texto, ErrorIA
from core.generador_pdf import generar_pdf, sanear_nombre_archivo
from core.perfil import formatear_perfil

CARPETA_SALIDA = "salidas_pdf"


def generar_documentos(
    texto_oferta: str,
    puesto_objetivo: str,
    mercado_destino: str,
    estilo_pdf: str,
    perfil: dict,
    match: dict | None = None,
) -> dict:
    """
    Genera y guarda en disco el CV y la Cover Letter en PDF. Si se pasa
    un `match` (resultado de analizar_match), el CV se redacta apuntando
    a cerrar esas brechas específicas en vez de un texto genérico.
    Devuelve {"ruta_cv", "ruta_cl", "cv_texto", "cover_letter_texto"}.
    Lanza ErrorIA o ValueError si algo falla.
    """
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    contexto_perfil = formatear_perfil(perfil)

    instruccion_brechas = ""
    if match:
        piezas = []
        if match.get("palabras_faltantes"):
            piezas.append("Palabras clave que la oferta pide y hoy no destacan: " + ", ".join(match["palabras_faltantes"]))
        if match.get("debilidades"):
            piezas.append("Brechas detectadas frente a la oferta: " + ", ".join(match["debilidades"]))
        if piezas:
            instruccion_brechas = (
                "\n\nUn análisis ATS previo detectó estas brechas — sin inventar nada que el candidato no "
                "tenga, dale prioridad y visibilidad a cualquier experiencia real del perfil que ayude a "
                "cerrarlas (reordena, no inventes):\n- " + "\n- ".join(piezas) + "\n"
            )

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
        f"NUNCA inventes tecnologías o empresas que no estén en el perfil del candidato."
        f"{instruccion_brechas}\n\n"
        f"Perfil del candidato:\n{contexto_perfil}"
    )
    nombre_firma = perfil.get("nombre") or "Candidato/a"
    prompt_cover = (
        f"Escribe ÚNICAMENTE el cuerpo de una Cover Letter en español, directa y sin rodeos, "
        f"para el puesto de {puesto_objetivo} en {mercado_destino}. Si el perfil tiene "
        f"logros o experiencia, menciona como máximo uno concreto que calce con esta oferta "
        f"— si no hay logros cargados, escribe sin inventar ninguno. NUNCA indiques que el "
        f"candidato domina o usa una tecnología que no esté textualmente en su 'Stack "
        f"principal', aunque la oferta la pida — en ese caso, puedes mencionar disposición "
        f"a aprenderla, nunca dominio que no tiene. Firma con el nombre {nombre_firma}. "
        f"No agregues explicaciones ni ningún texto que no sea la carta en sí."
        f"{instruccion_brechas}\n\n"
        f"Perfil del candidato:\n{contexto_perfil}"
    )

    cv_texto = generar_texto(prompt_cv, texto_oferta)
    cover_letter_texto = generar_texto(prompt_cover, texto_oferta)

    cargo_limpio = sanear_nombre_archivo(puesto_objetivo)
    nombre_archivo = sanear_nombre_archivo(perfil.get("nombre") or "candidato")
    ruta_cv = os.path.join(CARPETA_SALIDA, f"CV_{nombre_archivo}_{cargo_limpio}.pdf")
    ruta_cl = os.path.join(CARPETA_SALIDA, f"CoverLetter_{nombre_archivo}_{cargo_limpio}.pdf")

    generar_pdf(ruta_cv, cv_texto, "CV Profesional", puesto_objetivo, perfil, estilo_nombre=estilo_pdf)
    generar_pdf(ruta_cl, cover_letter_texto, "Cover Letter", puesto_objetivo, perfil, estilo_nombre=estilo_pdf)

    return {
        "ruta_cv": ruta_cv,
        "ruta_cl": ruta_cl,
        "cv_texto": cv_texto,
        "cover_letter_texto": cover_letter_texto,
    }
