from core.generador_pdf import construir_secciones_cv, generar_pdf_cv, _formatear_rango_fechas


def _perfil_base(**overrides):
    perfil = {
        "nombre": "Ana Pérez",
        "ciudad": "Santiago",
        "email": "ana@correo.cl",
        "telefono": "+56912345678",
        "linkedin": "linkedin.com/in/anaperez",
        "experiencia_laboral": [],
        "formacion_academica": [],
        "idiomas": [],
        "habilidades_blandas": "",
        "competencias_tecnicas": "",
    }
    perfil.update(overrides)
    return perfil


def test_formatear_rango_fechas_actualidad():
    assert _formatear_rango_fechas("2021", "", True) == "2021 – Actualidad"


def test_formatear_rango_fechas_cerrado():
    assert _formatear_rango_fechas("2021", "2024", False) == "2021 – 2024"


def test_construir_secciones_omite_idiomas_vacio():
    perfil = _perfil_base()
    secciones = construir_secciones_cv(perfil, "Resumen de prueba.", [])
    titulos = [s["titulo"] for s in secciones]
    assert "Idiomas" not in titulos


def test_construir_secciones_incluye_idiomas_si_hay():
    perfil = _perfil_base(idiomas=[{"idioma": "Inglés", "nivel": "Avanzado"}])
    secciones = construir_secciones_cv(perfil, "Resumen.", [])
    seccion_idiomas = next(s for s in secciones if s["titulo"] == "Idiomas")
    assert seccion_idiomas["contenido"] == ["Inglés: Avanzado"]


def test_construir_secciones_experiencia_usa_bullets_pulidos():
    perfil = _perfil_base(experiencia_laboral=[
        {"cargo": "Dev", "empresa": "Acme", "fecha_inicio": "2021", "fecha_fin": "2024", "actualidad": False, "funciones": "Backend\nAPIs"}
    ])
    secciones = construir_secciones_cv(perfil, "Resumen.", [["Bullet pulido 1", "Bullet pulido 2"]])
    seccion_exp = next(s for s in secciones if s["titulo"] == "Experiencia Laboral")
    assert seccion_exp["contenido"][0]["encabezado"] == "Dev — Acme | 2021 – 2024"
    assert seccion_exp["contenido"][0]["bullets"] == ["Bullet pulido 1", "Bullet pulido 2"]


def test_construir_secciones_experiencia_sin_bullets_pulidos_usa_literal():
    perfil = _perfil_base(experiencia_laboral=[
        {"cargo": "Dev", "empresa": "Acme", "fecha_inicio": "2021", "fecha_fin": "2024", "actualidad": False, "funciones": "Backend\nAPIs"}
    ])
    secciones = construir_secciones_cv(perfil, "Resumen.", [])
    seccion_exp = next(s for s in secciones if s["titulo"] == "Experiencia Laboral")
    assert seccion_exp["contenido"][0]["bullets"] == ["Backend", "APIs"]


def test_generar_pdf_cv_produce_bytes_no_vacios():
    perfil = _perfil_base(
        experiencia_laboral=[{"cargo": "Dev", "empresa": "Acme", "fecha_inicio": "2021", "fecha_fin": "2024", "actualidad": False, "funciones": "Backend"}],
        competencias_tecnicas="Python\nDocker",
    )
    pdf_bytes = generar_pdf_cv(perfil, "Resumen de prueba.", [["Backend"]], "Backend Developer")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_generar_pdf_cv_falla_sin_ninguna_seccion():
    perfil = _perfil_base()
    import pytest
    with pytest.raises(ValueError):
        generar_pdf_cv(perfil, "", [], "Backend Developer")
