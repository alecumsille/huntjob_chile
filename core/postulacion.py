"""
Genera el CV y la Cover Letter para una oferta puntual. Único lugar
donde vive este prompt — lo usan tanto el "Generador por URL" como el
botón de 1-click desde el buscador, para no mantener el mismo texto
duplicado en dos pantallas.

El CV mezcla dos fuentes: las secciones literales del perfil (datos
personales, formación, competencias, habilidades blandas, idiomas) se
renderizan tal cual las cargó el usuario — ver
core/generador_pdf.py::construir_secciones_cv. La IA solo redacta el
resumen profesional y pule los bullets de experiencia laboral, siempre
sobre los hechos reales que ya están en el perfil.
"""

from core.motor_ia import generar_texto, pulir_experiencia_laboral, ErrorIA
from core.generador_pdf import generar_pdf, generar_pdf_cv, sanear_nombre_archivo, construir_secciones_cv
from core.perfil import formatear_perfil


def generar_documentos(
    texto_oferta: str,
    puesto_objetivo: str,
    mercado_destino: str,
    estilo_pdf: str,
    perfil: dict,
    match: dict | None = None,
) -> dict:
    """
    Genera el CV y la Cover Letter en PDF, en memoria (nunca en disco —
    evita que dos postulaciones simultáneas de usuarios distintos se
    pisen en una carpeta compartida). Si se pasa un `match` (resultado
    de analizar_match), el resumen profesional se redacta apuntando a
    cerrar esas brechas específicas en vez de un texto genérico.
    Devuelve {"cv_bytes", "cl_bytes", "nombre_cv", "nombre_cl", "cv_texto", "cover_letter_texto"}.
    Lanza ErrorIA o ValueError si algo falla.
    """
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
                "tenga, dale prioridad y visibilidad en el resumen a cualquier experiencia real del perfil "
                "que ayude a cerrarlas:\n- " + "\n- ".join(piezas) + "\n"
            )

    prompt_resumen = (
        f"Redacta ÚNICAMENTE el 'Perfil Profesional' de un Curriculum Vitae en español: un extracto "
        f"potente de 3 a 5 líneas, optimizado para pasar filtros ATS, para el puesto de {puesto_objetivo} "
        f"en {mercado_destino}. Usa exclusivamente la experiencia, formación y competencias reales del "
        f"candidato descritas en su perfil. NUNCA inventes tecnologías, empresas o estudios que no estén "
        f"en el perfil. No agregues título de sección ni explicaciones — responde solo el texto del extracto."
        f"{instruccion_brechas}\n\nPerfil del candidato:\n{contexto_perfil}"
    )
    resumen_profesional = generar_texto(prompt_resumen, texto_oferta)

    bullets_por_trabajo = pulir_experiencia_laboral(perfil.get("experiencia_laboral") or [], puesto_objetivo, texto_oferta)

    nombre_firma = perfil.get("nombre") or "Candidato/a"
    prompt_cover = (
        f"Escribe ÚNICAMENTE el cuerpo de una Cover Letter en español, directa y sin rodeos, "
        f"para el puesto de {puesto_objetivo} en {mercado_destino}. Si el perfil tiene "
        f"logros o experiencia, menciona como máximo uno concreto que calce con esta oferta "
        f"— si no hay logros cargados, escribe sin inventar ninguno. NUNCA indiques que el "
        f"candidato domina o usa una tecnología que no esté textualmente en sus competencias "
        f"técnicas, aunque la oferta la pida — en ese caso, puedes mencionar disposición "
        f"a aprenderla, nunca dominio que no tiene. Firma con el nombre {nombre_firma}. "
        f"No agregues explicaciones ni ningún texto que no sea la carta en sí."
        f"{instruccion_brechas}\n\n"
        f"Perfil del candidato:\n{contexto_perfil}"
    )
    cover_letter_texto = generar_texto(prompt_cover, texto_oferta)

    cargo_limpio = sanear_nombre_archivo(puesto_objetivo)
    nombre_archivo = sanear_nombre_archivo(perfil.get("nombre") or "candidato")

    cv_bytes = generar_pdf_cv(perfil, resumen_profesional, bullets_por_trabajo, puesto_objetivo, estilo_nombre=estilo_pdf)
    cl_bytes = generar_pdf(cover_letter_texto, "Cover Letter", puesto_objetivo, perfil, estilo_nombre=estilo_pdf)

    cv_texto = _aplanar_cv_a_texto(perfil, resumen_profesional, bullets_por_trabajo, puesto_objetivo)

    return {
        "cv_bytes": cv_bytes,
        "cl_bytes": cl_bytes,
        "nombre_cv": f"CV_{nombre_archivo}_{cargo_limpio}.pdf",
        "nombre_cl": f"CoverLetter_{nombre_archivo}_{cargo_limpio}.pdf",
        "cv_texto": cv_texto,
        "cover_letter_texto": cover_letter_texto,
    }


def _aplanar_cv_a_texto(perfil: dict, resumen_profesional: str, bullets_por_trabajo: list[list[str]], puesto_objetivo: str) -> str:
    """
    Versión en texto plano del CV, solo para guardar en el historial de
    postulaciones (core/db.py::guardar_historial) — nunca se muestra en
    pantalla, es un registro de auditoría. Reutiliza
    construir_secciones_cv() para no duplicar la lógica de qué va en
    cada sección.
    """
    secciones = construir_secciones_cv(perfil, resumen_profesional, bullets_por_trabajo)
    lineas = [f"CV Profesional — {puesto_objetivo}", ""]
    for seccion in secciones:
        lineas.append(seccion["titulo"].upper())
        if seccion["tipo"] == "parrafo":
            lineas.append(seccion["contenido"])
        elif seccion["tipo"] == "trabajos":
            for trabajo in seccion["contenido"]:
                if trabajo["encabezado"]:
                    lineas.append(trabajo["encabezado"])
                lineas.extend(f"- {b}" for b in trabajo["bullets"])
        elif seccion["tipo"] == "estudios":
            for estudio in seccion["contenido"]:
                lineas.append(estudio["encabezado"])
        elif seccion["tipo"] == "lista":
            lineas.extend(f"- {item}" for item in seccion["contenido"])
        lineas.append("")
    return "\n".join(lineas)
