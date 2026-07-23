from core.perfil import (
    VALORES_POR_DEFECTO,
    lineas_no_vacias,
    formatear_perfil,
    _migrar_legado,
)


def test_lineas_no_vacias_descarta_blancos():
    assert lineas_no_vacias("Python\n\n  \nSQL\n") == ["Python", "SQL"]


def test_lineas_no_vacias_texto_vacio():
    assert lineas_no_vacias("") == []
    assert lineas_no_vacias(None) == []


def test_formatear_perfil_incluye_secciones_nuevas():
    perfil = dict(VALORES_POR_DEFECTO)
    perfil.update({
        "ciudad": "Santiago",
        "experiencia_laboral": [{"cargo": "Dev", "empresa": "Acme", "fecha_inicio": "2021", "fecha_fin": "2024", "actualidad": False, "funciones": "Backend\nAPIs"}],
        "formacion_academica": [{"titulo": "Ing. Civil Informática", "institucion": "USACH", "fecha_inicio": "2015", "fecha_fin": "2020", "tipo": "Carrera"}],
        "idiomas": [{"idioma": "Inglés", "nivel": "Avanzado"}],
        "habilidades_blandas": "Trabajo en equipo\nComunicación",
        "competencias_tecnicas": "Python\nDocker",
    })
    texto = formatear_perfil(perfil)
    assert "Santiago" in texto
    assert "Acme" in texto
    assert "USACH" in texto
    assert "Inglés: Avanzado" in texto
    assert "Trabajo en equipo" in texto
    assert "Docker" in texto


def test_migrar_legado_precarga_experiencia_desde_logros():
    perfil = dict(VALORES_POR_DEFECTO)
    perfil["logros_y_experiencia"] = "Lideré migración a microservicios."
    perfil["experiencia_laboral"] = []
    resultado = _migrar_legado(perfil)
    assert len(resultado["experiencia_laboral"]) == 1
    assert resultado["experiencia_laboral"][0]["funciones"] == "Lideré migración a microservicios."
    assert resultado["experiencia_laboral"][0]["cargo"] == ""


def test_migrar_legado_no_pisa_experiencia_existente():
    perfil = dict(VALORES_POR_DEFECTO)
    perfil["logros_y_experiencia"] = "Texto viejo"
    perfil["experiencia_laboral"] = [{"cargo": "Dev", "empresa": "X", "fecha_inicio": "", "fecha_fin": "", "actualidad": False, "funciones": "Ya migrado antes"}]
    resultado = _migrar_legado(perfil)
    assert len(resultado["experiencia_laboral"]) == 1
    assert resultado["experiencia_laboral"][0]["funciones"] == "Ya migrado antes"


def test_migrar_legado_precarga_competencias_desde_stack():
    perfil = dict(VALORES_POR_DEFECTO)
    perfil["stack_principal"] = "Python, FastAPI, PostgreSQL"
    perfil["competencias_tecnicas"] = ""
    resultado = _migrar_legado(perfil)
    assert resultado["competencias_tecnicas"] == "Python, FastAPI, PostgreSQL"
