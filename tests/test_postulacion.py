from unittest.mock import patch
from core.postulacion import generar_documentos, _aplanar_cv_a_texto


def _perfil_prueba():
    return {
        "nombre": "Ana Pérez",
        "ciudad": "Santiago",
        "email": "ana@correo.cl",
        "telefono": "",
        "linkedin": "",
        "anos_experiencia": 3,
        "seniority": "Semi Senior",
        "experiencia_laboral": [{"cargo": "Dev", "empresa": "Acme", "fecha_inicio": "2021", "fecha_fin": "2024", "actualidad": False, "funciones": "Backend\nAPIs"}],
        "formacion_academica": [],
        "idiomas": [],
        "habilidades_blandas": "",
        "competencias_tecnicas": "Python",
        "stack_principal": "",
        "logros_y_experiencia": "",
    }


def test_generar_documentos_devuelve_mismas_llaves_que_antes():
    with patch("core.postulacion.generar_texto", return_value="Resumen generado."), \
         patch("core.postulacion.pulir_experiencia_laboral", return_value=[["Bullet pulido"]]):
        resultado = generar_documentos("texto oferta", "Backend Developer", "Chile", "Pastel", _perfil_prueba())
    assert set(resultado.keys()) == {"cv_bytes", "cl_bytes", "nombre_cv", "nombre_cl", "cv_texto", "cover_letter_texto"}
    assert isinstance(resultado["cv_bytes"], bytes) and len(resultado["cv_bytes"]) > 0
    assert isinstance(resultado["cl_bytes"], bytes) and len(resultado["cl_bytes"]) > 0


def test_aplanar_cv_a_texto_incluye_secciones_literales():
    perfil = _perfil_prueba()
    texto = _aplanar_cv_a_texto(perfil, "Resumen generado.", [["Bullet pulido"]], "Backend Developer")
    assert "COMPETENCIAS TÉCNICAS Y MANEJO DE SOFTWARE" in texto.upper()
    assert "Python" in texto
    assert "Bullet pulido" in texto
