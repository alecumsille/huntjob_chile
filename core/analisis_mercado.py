"""
Módulo de análisis de mercado salarial para HuntJob Chile.
Calcula métricas estadísticas de sueldos (promedio, mínimo, máximo)
a partir de los resultados extraídos de los portales de empleo.
"""

import re


def estimar_sueldo_mercado(resultados: list[dict]) -> dict:
    """
    Parsea las ofertas laborales y devuelve estadísticas del mercado salarial:
    - sueldo_promedio (int o None)
    - sueldo_min (int o None)
    - sueldo_max (int o None)
    - cantidad_transparentes (int)
    - total_ofertas (int)
    """
    valores_salario = []

    for oferta in resultados:
        texto_sueldo = oferta.get("sueldo", "")
        if not texto_sueldo or texto_sueldo == "No especifica sueldo":
            continue

        # Extraer todos los números de 5+ dígitos o patrones con puntos ($1.500.000)
        # ej "$1.500.000 - $2.200.000 CLP" o "$1500000"
        limpio = texto_sueldo.replace(".", "").replace(",", "")
        numeros = [int(n) for n in re.findall(r"\b\d{5,8}\b", limpio)]

        if numeros:
            # Si hay rango (ej 1500000 y 2200000), tomar el promedio del rango para esa oferta
            valores_salario.append(int(sum(numeros) / len(numeros)))

    total_ofertas = len(resultados)
    cantidad_transparentes = len(valores_salario)

    if not valores_salario:
        return {
            "sueldo_promedio": None,
            "sueldo_min": None,
            "sueldo_max": None,
            "cantidad_transparentes": 0,
            "total_ofertas": total_ofertas,
            "moneda": "CLP",
        }

    promedio = int(sum(valores_salario) / len(valores_salario))
    sueldo_min = min(valores_salario)
    sueldo_max = max(valores_salario)

    return {
        "sueldo_promedio": promedio,
        "sueldo_min": sueldo_min,
        "sueldo_max": sueldo_max,
        "cantidad_transparentes": cantidad_transparentes,
        "total_ofertas": total_ofertas,
        "moneda": "CLP",
    }


def formatear_monto_clp(monto: int | None) -> str:
    """Formatea un entero en pesos chilenos ej 2150000 -> '$2.150.000 CLP'."""
    if monto is None:
        return "No disponible"
    return f"${monto:,.0f} CLP".replace(",", ".")


def generar_metricas_funnel(historial_postulaciones: list[dict], ofertas_guardadas: list[dict]) -> dict:
    """
    Calcula métricas de empleabilidad para el Dashboard:
    - total_guardadas
    - total_postuladas
    - total_entrevistas
    - total_ofertas_recibidas
    - tasa_conversion_entrevista (%)
    """
    total_guardadas = len(ofertas_guardadas)
    
    postuladas = [o for o in ofertas_guardadas if o.get("estado_kanban") == "✉️ Postulada"]
    entrevistas = [o for o in ofertas_guardadas if o.get("estado_kanban") == "🎙️ En Entrevista"]
    recibidas = [o for o in ofertas_guardadas if o.get("estado_kanban") == "🎉 Oferta Recibida"]

    total_postuladas = len(postuladas) + len(historial_postulaciones)
    total_entrevistas = len(entrevistas)
    total_ofertas_recibidas = len(recibidas)

    tasa_conversion = 0.0
    if total_postuladas > 0:
        tasa_conversion = round((total_entrevistas / total_postuladas) * 100, 1)

    return {
        "total_guardadas": total_guardadas,
        "total_postuladas": total_postuladas,
        "total_entrevistas": total_entrevistas,
        "total_ofertas_recibidas": total_ofertas_recibidas,
        "tasa_conversion_entrevista": tasa_conversion,
    }
