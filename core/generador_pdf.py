"""
Módulo de compilación de PDF. Diseño minimalista, tipografía y espaciado
consistentes. Sanea nombres de archivo para evitar rutas inválidas.
"""

import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

COLOR_TITULO = "#111111"
COLOR_CUERPO = "#333333"


def sanear_nombre_archivo(texto: str) -> str:
    """
    Convierte un string arbitrario en un nombre de archivo seguro.
    Si el resultado queda vacío (ej. texto compuesto solo de símbolos),
    devuelve un valor por defecto en vez de un nombre de archivo roto.
    """
    limpio = re.sub(r'[\\/*?:"<>|\s]', "_", texto.strip())
    limpio = re.sub(r"_+", "_", limpio).strip("_")
    return limpio if limpio else "documento_sin_titulo"


def generar_pdf(ruta_salida: str, contenido_texto: str, titulo: str) -> None:
    """
    Compila un PDF con estilo simétrico: título destacado y cuerpo en
    párrafos separados. Lanza ValueError si el contenido está vacío,
    en vez de generar un PDF en blanco silenciosamente.
    """
    if not contenido_texto or not contenido_texto.strip():
        raise ValueError(f"No se puede generar '{ruta_salida}': el contenido está vacío.")

    documento = SimpleDocTemplate(ruta_salida, pagesize=letter)
    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloDocumento",
        parent=estilos["Heading1"],
        fontSize=16,
        spaceAfter=10,
        textColor=COLOR_TITULO,
    )
    estilo_cuerpo = ParagraphStyle(
        "CuerpoDocumento",
        parent=estilos["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
        textColor=COLOR_CUERPO,
    )

    elementos = [Paragraph(titulo, estilo_titulo), Spacer(1, 8)]
    for linea in contenido_texto.split("\n"):
        if linea.strip():
            elementos.append(Paragraph(linea, estilo_cuerpo))

    documento.build(elementos)
