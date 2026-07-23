import json
import core.motor_ia as motor_ia
from core.motor_ia import pulir_experiencia_laboral


def test_sin_trabajos_con_funciones_no_llama_ia(monkeypatch):
    llamado = {"veces": 0}

    def fake_ejecutar(*args, **kwargs):
        llamado["veces"] += 1
        return "{}"

    monkeypatch.setattr(motor_ia, "_ejecutar_con_fallback", fake_ejecutar)
    experiencia = [{"cargo": "Dev", "empresa": "Acme", "funciones": ""}]
    resultado = pulir_experiencia_laboral(experiencia, "Backend Developer", "oferta")
    assert resultado == [[]]
    assert llamado["veces"] == 0


def test_pule_bullets_en_el_mismo_orden(monkeypatch):
    def fake_ejecutar(prompt, response_mime_type=None, response_schema=None):
        return json.dumps({"bullets_por_trabajo": [["Bullet pulido A", "Bullet pulido B"]]})

    monkeypatch.setattr(motor_ia, "_ejecutar_con_fallback", fake_ejecutar)
    experiencia = [{"cargo": "Dev", "empresa": "Acme", "funciones": "Original A\nOriginal B"}]
    resultado = pulir_experiencia_laboral(experiencia, "Backend Developer", "oferta")
    assert resultado == [["Bullet pulido A", "Bullet pulido B"]]


def test_degrada_a_literal_si_la_ia_falla(monkeypatch):
    def fake_ejecutar(*args, **kwargs):
        raise motor_ia.ErrorIA("falló")

    monkeypatch.setattr(motor_ia, "_ejecutar_con_fallback", fake_ejecutar)
    experiencia = [{"cargo": "Dev", "empresa": "Acme", "funciones": "Original A\nOriginal B"}]
    resultado = pulir_experiencia_laboral(experiencia, "Backend Developer", "oferta")
    assert resultado == [["Original A", "Original B"]]


def test_degrada_a_literal_si_la_ia_devuelve_cantidad_distinta(monkeypatch):
    def fake_ejecutar(prompt, response_mime_type=None, response_schema=None):
        return json.dumps({"bullets_por_trabajo": [["Solo un trabajo"]]})

    monkeypatch.setattr(motor_ia, "_ejecutar_con_fallback", fake_ejecutar)
    experiencia = [
        {"cargo": "Dev", "empresa": "Acme", "funciones": "Original A"},
        {"cargo": "QA", "empresa": "Beta", "funciones": "Original B"},
    ]
    resultado = pulir_experiencia_laboral(experiencia, "Backend Developer", "oferta")
    assert resultado == [["Original A"], ["Original B"]]


def test_preserva_trabajos_sin_funciones_junto_a_los_que_si_tienen(monkeypatch):
    def fake_ejecutar(prompt, response_mime_type=None, response_schema=None):
        return json.dumps({"bullets_por_trabajo": [["Pulido"]]})

    monkeypatch.setattr(motor_ia, "_ejecutar_con_fallback", fake_ejecutar)
    experiencia = [
        {"cargo": "Dev", "empresa": "Acme", "funciones": "Original"},
        {"cargo": "Practicante", "empresa": "Beta", "funciones": ""},
    ]
    resultado = pulir_experiencia_laboral(experiencia, "Backend Developer", "oferta")
    assert resultado == [["Pulido"], []]
