"""
Módulo Privacy Shield — Protección de datos personales sensibles conforme a la
Ley N° 19.628 sobre Protección de la Vida Privada en Chile.

Anonimiza RUT/DNI, números telefónicos privados y direcciones antes de enviar
el contenido del perfil a APIs de inteligencia artificial de terceros.
"""

import re

# Expresiones regulares para datos personales chilenos
RUT_REGEX = r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b"
TELEFONO_CHILE_REGEX = r"(?:\+?56\s?9?\s?\d{4}\s?\d{4}|\b9\d{8}\b)"
DIRECCION_REGEX = r"\b(?:Av\.|Avenida|Calle|Pasaje|Pasaaje)\s+[A-Za-z0-9\s]+#?\d{1,5}\b"


def anonimizar_datos_sensibles(texto: str) -> tuple[str, dict]:
    """
    Sustituye datos personales sensibles en el texto por tokens seguros.
    Devuelve (texto_anonimizado, mapa_reemplazos).
    """
    if not texto:
        return "", {}

    mapa_reemplazos = {}
    texto_anon = texto

    # 1. Anonimizar RUT
    ruts = re.findall(RUT_REGEX, texto_anon)
    for idx, rut in enumerate(set(ruts)):
        token = f"[RUT_PROTEGIDO_{idx+1}]"
        mapa_reemplazos[token] = rut
        texto_anon = texto_anon.replace(rut, token)

    # 2. Anonimizar Teléfono
    telefonos = re.findall(TELEFONO_CHILE_REGEX, texto_anon)
    for idx, tel in enumerate(set(telefonos)):
        token = f"[TELEFONO_PROTEGIDO_{idx+1}]"
        mapa_reemplazos[token] = tel
        texto_anon = texto_anon.replace(tel, token)

    # 3. Anonimizar Dirección Domiciliaria
    direcciones = re.findall(DIRECCION_REGEX, texto_anon, flags=re.IGNORECASE)
    for idx, dir_str in enumerate(set(direcciones)):
        token = f"[DIRECCION_PROTEGIDA_{idx+1}]"
        mapa_reemplazos[token] = dir_str
        texto_anon = texto_anon.replace(dir_str, token)

    return texto_anon, mapa_reemplazos


def restaurar_datos_sensibles(texto_anonimizado: str, mapa_reemplazos: dict) -> str:
    """
    Restaura los datos sensibles originales sobre el texto procesado por la IA.
    """
    if not texto_anonimizado or not mapa_reemplazos:
        return texto_anonimizado

    texto_restaurado = texto_anonimizado
    for token, valor_original in mapa_reemplazos.items():
        texto_restaurado = texto_restaurado.replace(token, valor_original)

    return texto_restaurado
