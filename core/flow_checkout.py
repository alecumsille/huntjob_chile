"""
Llama a la API de Flow desde huntjob_chile para armar el link de pago.
Esto SI lo puede hacer Streamlit (es una llamada saliente + redirect),
a diferencia de recibir webhooks, que vive en huntjob_payments.
"""

import hashlib
import hmac
import os

import requests
import streamlit as st

PAYMENTS_SERVICE_URL = "https://huntjob-payments.onrender.com"


def _obtener_config(nombre_var: str) -> str:
    valor = os.environ.get(nombre_var, "").strip()
    if not valor:
        try:
            valor = st.secrets.get(nombre_var, "").strip()
        except Exception:
            valor = ""
    return valor


FLOW_API_KEY = _obtener_config("FLOW_API_KEY")
FLOW_SECRET_KEY = _obtener_config("FLOW_SECRET_KEY")
FLOW_BASE_URL = _obtener_config("FLOW_BASE_URL") or "https://sandbox.flow.cl/api"


def _firmar(params: dict) -> str:
    claves_ordenadas = sorted(params.keys())
    string_a_firmar = "".join(f"{clave}{params[clave]}" for clave in claves_ordenadas)
    return hmac.new(
        FLOW_SECRET_KEY.encode("utf-8"), string_a_firmar.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def iniciar_registro_tarjeta(user_id: str, nombre: str, email: str) -> str:
    """Crea el cliente en Flow (si no existe) y devuelve la URL a la que redirigir al usuario."""
    params_cliente = {"apiKey": FLOW_API_KEY, "name": nombre, "email": email, "externalId": user_id}
    params_cliente["s"] = _firmar(params_cliente)
    respuesta = requests.post(f"{FLOW_BASE_URL}/customer/create", data=params_cliente, timeout=15)

    if respuesta.status_code == 400:
        # externalId ya existe -> ya es cliente de Flow, reusar
        customer_id = None
    else:
        respuesta.raise_for_status()
        customer_id = respuesta.json()["customerId"]

    if customer_id is None:
        raise RuntimeError(
            "El usuario ya tiene un cliente Flow registrado; falta implementar la busqueda "
            "por externalId (customer/get no la soporta por externalId directamente, "
            "revisar en el momento de probar este caso real)."
        )

    params_registro = {
        "apiKey": FLOW_API_KEY,
        "customerId": customer_id,
        "url_return": f"{PAYMENTS_SERVICE_URL}/webhook/flow/card-registered",
    }
    params_registro["s"] = _firmar(params_registro)
    respuesta_registro = requests.post(f"{FLOW_BASE_URL}/customer/register", data=params_registro, timeout=15)
    respuesta_registro.raise_for_status()
    datos = respuesta_registro.json()
    return f"{datos['url']}?token={datos['token']}"
