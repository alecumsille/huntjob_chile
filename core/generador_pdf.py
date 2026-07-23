"""
Módulo de compilación de PDF. Diseño minimalista, tipografía y espaciado
consistentes. Sanea nombres de archivo para evitar rutas inválidas.
"""

import re
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from core.perfil import lineas_no_vacias

# Mismos acentos pastel del tema de la app (rosado + celeste), aplicados
# solo como color de texto/línea — no afecta cómo un ATS extrae el texto,
# el color es puramente visual.
COLOR_NOMBRE = "#C87FA0"
COLOR_SUBTITULO = "#5B9BD5"
COLOR_CUERPO = "#333333"
COLOR_CONTACTO = "#777777"

PLANTILLAS_ESTILO = {
    "Pastel": {"nombre": "#C87FA0", "subtitulo": "#5B9BD5", "linea": "#5B9BD5"},
    "Ejecutivo / Marino": {"nombre": "#1B365D", "subtitulo": "#005691", "linea": "#005691"},
    "Minimalista Oscuro": {"nombre": "#222222", "subtitulo": "#444444", "linea": "#666666"},
    "Esmeralda / Tech": {"nombre": "#0F5132", "subtitulo": "#198754", "linea": "#198754"},
}


def sanear_nombre_archivo(texto: str) -> str:
    """
    Convierte un string arbitrario en un nombre de archivo seguro.
    Si el resultado queda vacío (ej. texto compuesto solo de símbolos),
    devuelve un valor por defecto en vez de un nombre de archivo roto.
    """
    limpio = re.sub(r'[\\/*?:"<>|\s]', "_", texto.strip())
    limpio = re.sub(r"_+", "_", limpio).strip("_")
    return limpio if limpio else "documento_sin_titulo"


def formatear_para_reportlab(linea: str) -> str:
    """
    Sanea el texto para ReportLab preservando marcas de negrita (<b>...</b> o **...**).
    Escapa la sintaxis XML (&, <, >) pero restituye únicamente las etiquetas <b> y </b>
    para que ReportLab renderice el texto con negritas en el PDF.
    """
    if not linea:
        return ""
    limpia = linea.strip()
    limpia = re.sub(r"^#{1,6}\s*", "", limpia)
    limpia = re.sub(r"^[*-]\s+", "", limpia)
    limpia = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", limpia)

    limpia = limpia.replace("<b>", "___BOLD_START___").replace("</b>", "___BOLD_END___")
    limpia = limpia.replace("<strong>", "___BOLD_START___").replace("</strong>", "___BOLD_END___")

    limpia = escape(limpia)

    limpia = limpia.replace("___BOLD_START___", "<b>").replace("___BOLD_END___", "</b>")
    return limpia


def _limpiar_markdown(linea: str) -> str:
    """
    Conserva compatibilidad retroactiva. Usa formatear_para_reportlab.
    """
    return formatear_para_reportlab(linea)


def _formatear_rango_fechas(fecha_inicio: str, fecha_fin: str, actualidad: bool) -> str:
    """Da formato 'inicio – fin' (o 'inicio – Actualidad') a un rango de fechas, tolerando campos vacíos."""
    if actualidad:
        return f"{fecha_inicio} – Actualidad" if fecha_inicio else "Actualidad"
    if fecha_inicio and fecha_fin:
        return f"{fecha_inicio} – {fecha_fin}"
    return fecha_inicio or fecha_fin or ""


def construir_secciones_cv(
    perfil: dict,
    resumen_profesional: str,
    bullets_por_trabajo: list[list[str]],
    resumen_fit: list[dict] | None = None,
) -> list[dict]:
    """
    Arma las secciones del CV como datos puros en el esqueleto ATS estándar:
    1. Perfil Profesional
    2. Resumen de Ajuste y Requisitos Clave (si está disponible)
    3. Experiencia Laboral
    4. Formación Académica
    5. Competencias Técnicas
    6. Habilidades Blandas
    7. Idiomas
    """
    secciones = []

    if resumen_profesional and resumen_profesional.strip():
        secciones.append({"titulo": "Perfil Profesional", "tipo": "parrafo", "contenido": resumen_profesional.strip()})

    if resumen_fit:
        lineas_fit = []
        for item in resumen_fit:
            req = item.get("requisito", "").strip()
            cand = item.get("postulante", "").strip()
            est = item.get("estado", "Cumplido").strip()
            if req:
                lineas_fit.append(f"<b>Requisito Clave:</b> {req} | <b>Perfil:</b> {cand} ({est})")
        if lineas_fit:
            secciones.append({"titulo": "Resumen de Ajuste y Requisitos Clave", "tipo": "lista", "contenido": lineas_fit})

    experiencia = perfil.get("experiencia_laboral") or []
    if experiencia:
        trabajos = []
        for indice, trabajo in enumerate(experiencia):
            encabezado_partes = [p for p in (trabajo.get("cargo"), trabajo.get("empresa")) if p]
            encabezado = " — ".join(encabezado_partes)
            rango = _formatear_rango_fechas(
                trabajo.get("fecha_inicio", ""), trabajo.get("fecha_fin", ""), trabajo.get("actualidad", False)
            )
            if rango:
                encabezado = f"{encabezado} | {rango}" if encabezado else rango
            if bullets_por_trabajo and indice < len(bullets_por_trabajo) and bullets_por_trabajo[indice]:
                bullets = bullets_por_trabajo[indice]
            else:
                bullets = lineas_no_vacias(trabajo.get("funciones", ""))
            trabajos.append({"encabezado": encabezado, "bullets": bullets})
        secciones.append({"titulo": "Experiencia Laboral", "tipo": "trabajos", "contenido": trabajos})

    formacion = perfil.get("formacion_academica") or []
    if formacion:
        estudios = []
        for estudio in formacion:
            partes = [p for p in (estudio.get("titulo"), estudio.get("institucion")) if p]
            encabezado = " — ".join(partes)
            rango = _formatear_rango_fechas(estudio.get("fecha_inicio", ""), estudio.get("fecha_fin", ""), False)
            if rango:
                encabezado = f"{encabezado} | {rango}" if encabezado else rango
            estudios.append({"encabezado": encabezado, "tipo": estudio.get("tipo", "")})
        secciones.append({"titulo": "Formación Académica", "tipo": "estudios", "contenido": estudios})

    competencias = lineas_no_vacias(perfil.get("competencias_tecnicas", ""))
    if competencias:
        secciones.append({"titulo": "Competencias Técnicas y Manejo de Software", "tipo": "lista", "contenido": competencias})

    habilidades = lineas_no_vacias(perfil.get("habilidades_blandas", ""))
    if habilidades:
        secciones.append({"titulo": "Habilidades Blandas", "tipo": "lista", "contenido": habilidades})

    idiomas = perfil.get("idiomas") or []
    lineas_idiomas = [f"{i.get('idioma', '')}: {i.get('nivel', '')}" for i in idiomas if i.get("idioma")]
    if lineas_idiomas:
        secciones.append({"titulo": "Idiomas", "tipo": "lista", "contenido": lineas_idiomas})

    return secciones


def generar_pdf_cv(
    perfil: dict,
    resumen_profesional: str,
    bullets_por_trabajo: list[list[str]],
    puesto: str,
    estilo_nombre: str = "Pastel",
    resumen_fit: list[dict] | None = None,
) -> bytes:
    """
    Compila el CV en PDF a partir de las secciones de construir_secciones_cv().
    Soporta formato de negritas <b>...</b> de ReportLab para destacar requisitos clave.
    """
    secciones = construir_secciones_cv(perfil, resumen_profesional, bullets_por_trabajo, resumen_fit=resumen_fit)
    if not secciones:
        raise ValueError("No se puede generar el CV: no hay ninguna sección con contenido.")

    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
    )
    estilos = getSampleStyleSheet()
    paleta_pdf = PLANTILLAS_ESTILO.get(estilo_nombre, PLANTILLAS_ESTILO["Pastel"])

    estilo_nombre_p = ParagraphStyle(
        "NombreCandidato", parent=estilos["Heading1"], fontSize=22, spaceAfter=2, textColor=paleta_pdf["nombre"]
    )
    estilo_contacto = ParagraphStyle(
        "Contacto", parent=estilos["Normal"], fontSize=9, spaceAfter=8, textColor=COLOR_CONTACTO
    )
    estilo_subtitulo = ParagraphStyle(
        "Subtitulo", parent=estilos["Heading2"], fontSize=13, spaceBefore=10, spaceAfter=8, textColor=paleta_pdf["subtitulo"]
    )
    estilo_cuerpo = ParagraphStyle(
        "CuerpoDocumento", parent=estilos["Normal"], fontSize=10.5, leading=15, spaceAfter=6, alignment=4, textColor=COLOR_CUERPO
    )
    estilo_encabezado_trabajo = ParagraphStyle(
        "EncabezadoTrabajo", parent=estilos["Normal"], fontSize=10.5, leading=14, spaceBefore=6, spaceAfter=2,
        textColor=COLOR_CUERPO, fontName="Helvetica-Bold",
    )
    estilo_bullet = ParagraphStyle(
        "Bullet", parent=estilos["Normal"], fontSize=10, leading=14, spaceAfter=3, leftIndent=12, textColor=COLOR_CUERPO
    )

    nombre = perfil.get("nombre") or "Candidato/a"
    datos_contacto = [
        dato for dato in (perfil.get("ciudad"), perfil.get("email"), perfil.get("telefono"), perfil.get("linkedin")) if dato
    ]

    elementos = [Paragraph(escape(nombre), estilo_nombre_p)]
    if datos_contacto:
        elementos.append(Paragraph(escape("  ·  ".join(datos_contacto)), estilo_contacto))
    else:
        elementos.append(Spacer(1, 6))
    elementos.append(HRFlowable(width="100%", thickness=1, color=paleta_pdf["linea"], spaceAfter=4))
    elementos.append(Paragraph(escape(f"CV Profesional — {puesto}"), estilo_subtitulo))

    for seccion in secciones:
        elementos.append(Paragraph(escape(seccion["titulo"]), estilo_subtitulo))
        if seccion["tipo"] == "parrafo":
            for linea in seccion["contenido"].split("\n"):
                linea_fmt = formatear_para_reportlab(linea)
                if linea_fmt:
                    elementos.append(Paragraph(linea_fmt, estilo_cuerpo))
        elif seccion["tipo"] == "trabajos":
            for trabajo in seccion["contenido"]:
                if trabajo["encabezado"]:
                    elementos.append(Paragraph(escape(trabajo["encabezado"]), estilo_encabezado_trabajo))
                for bullet in trabajo["bullets"]:
                    elementos.append(Paragraph(f"• {formatear_para_reportlab(bullet)}", estilo_bullet))
        elif seccion["tipo"] == "estudios":
            for estudio in seccion["contenido"]:
                if estudio["encabezado"]:
                    texto = estudio["encabezado"]
                    if estudio.get("tipo"):
                        texto = f"{texto} ({estudio['tipo']})"
                    elementos.append(Paragraph(escape(texto), estilo_encabezado_trabajo))
        elif seccion["tipo"] == "lista":
            for item in seccion["contenido"]:
                elementos.append(Paragraph(f"• {formatear_para_reportlab(item)}", estilo_bullet))

    documento.build(elementos)
    return buffer.getvalue()


def generar_pdf(contenido_texto: str, tipo_documento: str, puesto: str, perfil: dict, estilo_nombre: str = "Pastel") -> bytes:
    """
    Compila un PDF en memoria (nunca en disco — con múltiples usuarios
    reales, un archivo compartido en salidas_pdf/ podía pisarse entre
    postulaciones simultáneas) con encabezado real (nombre, contacto,
    tipo de documento + puesto) y cuerpo en párrafos separados. Diseño
    simple de una sola columna, sin tablas ni texto en imágenes — apto
    para parsers ATS, que solo leen texto plano en orden de lectura
    normal. Lanza ValueError si el contenido está vacío, en vez de
    generar un PDF en blanco silenciosamente.
    """
    if not contenido_texto or not contenido_texto.strip():
        raise ValueError(f"No se puede generar el {tipo_documento}: el contenido está vacío.")

    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
    )
    estilos = getSampleStyleSheet()

    paleta_pdf = PLANTILLAS_ESTILO.get(estilo_nombre, PLANTILLAS_ESTILO["Pastel"])

    estilo_nombre_p = ParagraphStyle(
        "NombreCandidato",
        parent=estilos["Heading1"],
        fontSize=22,
        spaceAfter=2,
        textColor=paleta_pdf["nombre"],
    )
    estilo_contacto = ParagraphStyle(
        "Contacto",
        parent=estilos["Normal"],
        fontSize=9,
        spaceAfter=8,
        textColor=COLOR_CONTACTO,
    )
    estilo_subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=estilos["Heading2"],
        fontSize=13,
        spaceBefore=10,
        spaceAfter=12,
        textColor=paleta_pdf["subtitulo"],
    )
    estilo_cuerpo = ParagraphStyle(
        "CuerpoDocumento",
        parent=estilos["Normal"],
        fontSize=10.5,
        leading=15,
        spaceAfter=8,
        alignment=4,  # justificado
        textColor=COLOR_CUERPO,
    )

    nombre = perfil.get("nombre") or "Candidato/a"
    datos_contacto = [
        dato for dato in (perfil.get("email"), perfil.get("telefono"), perfil.get("linkedin")) if dato
    ]

    elementos = [Paragraph(escape(nombre), estilo_nombre_p)]
    if datos_contacto:
        elementos.append(Paragraph(escape("  ·  ".join(datos_contacto)), estilo_contacto))
    else:
        elementos.append(Spacer(1, 6))

    elementos.append(HRFlowable(width="100%", thickness=1, color=paleta_pdf["linea"], spaceAfter=4))
    elementos.append(Paragraph(escape(f"{tipo_documento} — {puesto}"), estilo_subtitulo))

    for linea in contenido_texto.split("\n"):
        linea_limpia = _limpiar_markdown(linea)
        if linea_limpia:
            elementos.append(Paragraph(escape(linea_limpia), estilo_cuerpo))

    documento.build(elementos)
    return buffer.getvalue()
