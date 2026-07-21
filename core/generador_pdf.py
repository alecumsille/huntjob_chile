"""
Módulo de compilación de PDF. Diseño minimalista, tipografía y espaciado
consistentes. Sanea nombres de archivo para evitar rutas inválidas.
"""

import re
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Mismos acentos pastel del tema de la app (rosado + celeste), aplicados
# solo como color de texto/línea — no afecta cómo un ATS extrae el texto,
# el color es puramente visual.
COLOR_NOMBRE = "#C87FA0"
COLOR_SUBTITULO = "#5B9BD5"
COLOR_CUERPO = "#333333"
COLOR_CONTACTO = "#777777"


def sanear_nombre_archivo(texto: str) -> str:
    """
    Convierte un string arbitrario en un nombre de archivo seguro.
    Si el resultado queda vacío (ej. texto compuesto solo de símbolos),
    devuelve un valor por defecto en vez de un nombre de archivo roto.
    """
    limpio = re.sub(r'[\\/*?:"<>|\s]', "_", texto.strip())
    limpio = re.sub(r"_+", "_", limpio).strip("_")
    return limpio if limpio else "documento_sin_titulo"


def _limpiar_markdown(linea: str) -> str:
    """
    Gemini suele responder con sintaxis Markdown (headers, negritas,
    separadores). El PDF no renderiza Markdown, así que sin esto los
    símbolos ("**", "###", "***") quedan literales en el documento final.
    """
    limpia = linea.strip()
    limpia = re.sub(r"^#{1,6}\s*", "", limpia)  # headers (#, ##, ###...)
    limpia = re.sub(r"^[*-]\s+", "- ", limpia)  # bullets ("* x" o "- x")
    limpia = re.sub(r"\*\*\*|\*\*|(?<!\w)\*(?!\s)", "", limpia)  # negrita/cursiva
    return limpia


def generar_pdf(ruta_salida: str, contenido_texto: str, tipo_documento: str, puesto: str, perfil: dict) -> None:
    """
    Compila un PDF con encabezado real (nombre, contacto, tipo de
    documento + puesto) y cuerpo en párrafos separados. Diseño simple de
    una sola columna, sin tablas ni texto en imágenes — apto para
    parsers ATS, que solo leen texto plano en orden de lectura normal.
    Lanza ValueError si el contenido está vacío, en vez de generar un
    PDF en blanco silenciosamente.
    """
    if not contenido_texto or not contenido_texto.strip():
        raise ValueError(f"No se puede generar '{ruta_salida}': el contenido está vacío.")

    documento = SimpleDocTemplate(
        ruta_salida,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
    )
    estilos = getSampleStyleSheet()

    estilo_nombre = ParagraphStyle(
        "NombreCandidato",
        parent=estilos["Heading1"],
        fontSize=22,
        spaceAfter=2,
        textColor=COLOR_NOMBRE,
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
        textColor=COLOR_SUBTITULO,
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

    elementos = [Paragraph(escape(nombre), estilo_nombre)]
    if datos_contacto:
        elementos.append(Paragraph(escape("  ·  ".join(datos_contacto)), estilo_contacto))
    else:
        elementos.append(Spacer(1, 6))

    elementos.append(HRFlowable(width="100%", thickness=1, color=COLOR_SUBTITULO, spaceAfter=4))
    elementos.append(Paragraph(escape(f"{tipo_documento} — {puesto}"), estilo_subtitulo))

    for linea in contenido_texto.split("\n"):
        linea_limpia = _limpiar_markdown(linea)
        if linea_limpia:
            elementos.append(Paragraph(escape(linea_limpia), estilo_cuerpo))

    documento.build(elementos)
