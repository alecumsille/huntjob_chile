"""
Módulo de Validación y Formateo de RUT Chileno — Módulo 11.
Inspirado en jlobos/rut.js.

Valida y da formato estandarizado al Rol Único Tributario (RUT / RUN) de personas y empresas en Chile.
"""

import re


def limpiar_rut(rut_str: str) -> str:
    """Limpia puntos, guiones y espacios de un RUT."""
    if not rut_str:
        return ""
    rut_clean = re.sub(r"[^0-9kK]", "", str(rut_str))
    return rut_clean.upper()


def calcular_dv(rut_num: int) -> str:
    """Calcula el Dígito Verificador (DV) usando el algoritmo Módulo 11."""
    suma = 0
    multiplicador = 2
    for d in reversed(str(rut_num)):
        suma += int(d) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1

    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    elif resto == 10:
        return "K"
    else:
        return str(resto)


def validar_rut(rut_str: str) -> bool:
    """Valida si un RUT chileno es matemáticamente correcto."""
    rut_clean = limpiar_rut(rut_str)
    if len(rut_clean) < 8 or len(rut_clean) > 9:
        return False

    cuerpo = rut_clean[:-1]
    dv = rut_clean[-1]

    if not cuerpo.isdigit():
        return False

    dv_calculado = calcular_dv(int(cuerpo))
    return dv.upper() == dv_calculado


def formatear_rut(rut_str: str) -> str:
    """
    Formatea un RUT a la representación estándar chilena: XX.XXX.XXX-Y
    Ejemplo: 18123456K -> 18.123.456-K
    """
    rut_clean = limpiar_rut(rut_str)
    if not rut_clean:
        return ""

    if len(rut_clean) < 2:
        return rut_clean

    cuerpo = rut_clean[:-1]
    dv = rut_clean[-1]

    # Insertar puntos de miles
    cuerpo_formateado = f"{int(cuerpo):,}".replace(",", ".")
    return f"{cuerpo_formateado}-{dv}"
