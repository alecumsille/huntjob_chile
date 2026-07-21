"""
Módulo de almacenamiento del perfil de usuario. Persiste en un YAML local
que nunca se commitea (ver .gitignore) — son datos personales. "Sin
perfil guardado" es un estado válido: cargar_perfil() nunca lanza
excepción por archivo faltante, solo devuelve valores por defecto.
"""

import os
import yaml

CARPETA_PERFIL = "perfil"
RUTA_PERFIL = os.path.join(CARPETA_PERFIL, "mi_perfil.yaml")

VALORES_POR_DEFECTO = {
    "nombre": "",
    "email": "",
    "telefono": "",
    "linkedin": "",
    "anos_experiencia": 0,
    "seniority": "Junior",
    "stack_principal": "",
    "logros_y_experiencia": "",
}

NIVELES_SENIORITY = ["Junior", "Semi Senior", "Senior", "Lead"]


def cargar_perfil() -> dict:
    """
    Lee perfil/mi_perfil.yaml si existe. Si no existe, o si el YAML no
    trae alguno de los campos esperados, completa con VALORES_POR_DEFECTO
    en vez de lanzar una excepción.
    """
    if not os.path.exists(RUTA_PERFIL):
        return dict(VALORES_POR_DEFECTO)

    try:
        with open(RUTA_PERFIL, "r", encoding="utf-8") as archivo:
            datos_guardados = yaml.safe_load(archivo) or {}
    except yaml.YAMLError:
        return dict(VALORES_POR_DEFECTO)

    if not isinstance(datos_guardados, dict):
        return dict(VALORES_POR_DEFECTO)

    perfil = dict(VALORES_POR_DEFECTO)
    perfil.update(datos_guardados)
    return perfil


def guardar_perfil(datos: dict) -> None:
    """
    Escribe datos como YAML en perfil/mi_perfil.yaml, creando la carpeta
    perfil/ si todavía no existe.
    """
    os.makedirs(CARPETA_PERFIL, exist_ok=True)
    with open(RUTA_PERFIL, "w", encoding="utf-8") as archivo:
        yaml.safe_dump(datos, archivo, allow_unicode=True, sort_keys=False)


def formatear_perfil(perfil: dict) -> str:
    """
    Serializa el perfil como texto plano para incluir en prompts de IA.
    Fuente única para motor_ia.py y app.py — evita duplicar el formato
    en tres lugares distintos.
    """
    return (
        f"Años de experiencia: {perfil.get('anos_experiencia', 0)}\n"
        f"Nivel: {perfil.get('seniority', '')}\n"
        f"Stack principal: {perfil.get('stack_principal', '')}\n"
        f"Logros y experiencia: {perfil.get('logros_y_experiencia', '')}"
    )
