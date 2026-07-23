"""
Guía Laboral de Chile & Asesor de Normativa y Sueldos.
Inspirado en devschile/guia-laboral.

Proporciona información estructurada sobre el Código del Trabajo de Chile,
rangos de remuneración estimados por área laboral y recomendaciones para el postulante.
"""

# Base de conocimiento laboral de Chile (Código del Trabajo Ley N° 21.561 40 Horas, Contratos, Finiquitos)
GUIA_LABORAL_CHILE = {
    "jornada_laboral": {
        "normativa": "Ley N° 21.561 — Reducción gradual a 40 horas semanales.",
        "maximo_diario": "10 horas ordinarias por día.",
        "horas_extras": "Máximo 2 horas extraordinarias por día con recargo mínimo del 50% sobre el sueldo base."
    },
    "tipos_contrato": [
        "Contrato Indefinido: Otorga derecho a indemnización por años de servicio.",
        "Contrato a Plazo Fijo: Máximo 1 año de duración (o 2 años para profesionales/técnicos).",
        "Contrato por Obra o Faena: Concluye al finalizar el trabajo específico asignado."
    ],
    "cotizaciones": {
        "afp": "10% + comisión de la AFP elegida.",
        "salud": "7% obligatorio (FONASA e ISAPRE).",
        "seguro_cesantia": "0.6% trabajador / 2.4% empleador en contratos indefinidos."
    }
}

ESTIMACION_SALARIAL_CHILE = {
    "desarrollo_software": {"junior": "800.000 - 1.400.000 CLP", "semi_senior": "1.500.000 - 2.400.000 CLP", "senior": "2.500.000 - 4.200.000 CLP"},
    "administracion_contabilidad": {"junior": "650.000 - 950.000 CLP", "semi_senior": "1.000.000 - 1.600.000 CLP", "senior": "1.700.000 - 2.800.000 CLP"},
    "ingenieria_operaciones": {"junior": "900.000 - 1.500.000 CLP", "semi_senior": "1.600.000 - 2.600.000 CLP", "senior": "2.700.000 - 4.500.000 CLP"},
    "ventas_comercial": {"junior": "600.000 - 900.000 CLP + Comisiones", "semi_senior": "1.000.000 - 1.800.000 CLP + Comisiones", "senior": "1.900.000 - 3.500.000 CLP + Comisiones"},
    "general": {"junior": "600.000 - 1.000.000 CLP", "semi_senior": "1.100.000 - 1.800.000 CLP", "senior": "1.900.000 - 3.000.000 CLP"}
}


def obtener_rango_salarial_sugerido(area: str, experiencia_años: int) -> dict:
    """Estimación aproximada de sueldo bruto/líquido en Chile según años de experiencia."""
    seniority = "junior"
    if experiencia_años >= 5:
        seniority = "senior"
    elif experiencia_años >= 2:
        seniority = "semi_senior"

    area_key = area.lower().replace(" ", "_") if area else "general"
    rangos_area = ESTIMACION_SALARIAL_CHILE.get(area_key, ESTIMACION_SALARIAL_CHILE["general"])
    
    return {
        "seniority": seniority,
        "rango_estimado_clp": rangos_area.get(seniority, rangos_area["junior"]),
        "moneda": "CLP",
        "fuente": "Guía Laboral Chile — Estudio de Mercado Tech & Servicios"
    }
