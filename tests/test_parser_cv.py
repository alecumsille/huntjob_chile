from core.parser_cv import parsear_cv_completo


def test_parsear_cv_completo_extrae_datos_correctamente():
    sample_cv = """
    Alejandro Cumsille
    Email: contacto@cumsille.tech
    Teléfono: +56 9 1234 5678
    LinkedIn: https://www.linkedin.com/in/alecumsille
    
    Senior Full Stack Engineer con 6+ años de experiencia.
    Experto en Python, React, SQL, Docker, AWS y Node.js.
    Excelente Comunicación Efectiva y Liderazgo de Equipos.
    Inglés fluido y avanzado.
    """
    res = parsear_cv_completo(sample_cv)
    assert res["nombre"] == "Alejandro Cumsille"
    assert res["email"] == "contacto@cumsille.tech"
    assert "+56" in res["telefono"]
    assert "linkedin.com/in/alecumsille" in res["linkedin"]
    assert "Python" in res["competencias_tecnicas"]
    assert "React" in res["competencias_tecnicas"]
    assert "Liderazgo de Equipos" in res["habilidades_blandas"]
    assert res["seniority"] == "Senior"
    assert res["anos_experiencia"] == 5
    assert len(res["idiomas"]) > 0
