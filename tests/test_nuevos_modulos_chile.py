import pytest
from core.rut_chile import validar_rut, formatear_rut, limpiar_rut, calcular_dv
from core.guia_laboral import obtener_rango_salarial_sugerido, GUIA_LABORAL_CHILE
from core.mercado_regional import consultar_demanda_regional


def test_validar_rut_chileno_correctos():
    # 19000000 -> DV 1
    dv = calcular_dv(19000000)
    rut_valido = f"19.000.000-{dv}"
    assert validar_rut(rut_valido) is True
    assert validar_rut("111111119") is False


def test_formatear_rut_estandar():
    assert formatear_rut("190000001") == "19.000.000-1"
    assert limpiar_rut("19.000.000-1") == "190000001"


def test_guia_laboral_estimacion_salarial():
    res = obtener_rango_salarial_sugerido("desarrollo_software", 6)
    assert res["seniority"] == "senior"
    assert "CLP" in res["rango_estimado_clp"]
    assert "jornada_laboral" in GUIA_LABORAL_CHILE


def test_mercado_regional_antofagasta():
    res = consultar_demanda_regional("Antofagasta")
    assert res["nombre"] == "Antofagasta"
    assert "Minería" in res["industria_clave"]
