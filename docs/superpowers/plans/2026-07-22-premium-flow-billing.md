# Suscripción Premium vía Flow.cl — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cobrar automáticamente una suscripción mensual de $4.990 CLP vía Flow.cl y activar/desactivar el plan `premium` que ya existe en `planes_usuario` (Supabase) según el resultado de esos cobros.

**Architecture:** Dos repos. `huntjob_chile` (Streamlit, existente) agrega un botón que llama a la API de Flow y redirige al navegador — eso no requiere recibir webhooks. Un repo nuevo, `huntjob_payments` (Flask, standalone, deploy propio en Render), recibe los dos callbacks server-to-server que Flow necesita mandar (registro de tarjeta, cobro recurrente) y es el único que toca `planes_usuario` con la Service Role Key de Supabase.

**Tech Stack:** Python 3.12, Flask + gunicorn (huntjob_payments), `requests` para llamar a la API de Flow, `supabase-py` (cliente admin), `pytest` + `unittest.mock` para tests.

## Global Constraints

- Ambiente de desarrollo: **sandbox de Flow** (`https://sandbox.flow.cl/api`) hasta que la cuenta de comercio real quede aprobada — nunca apuntar a producción (`https://www.flow.cl/api`) durante este plan.
- La Service Role Key de Supabase vive **solo** en `huntjob_payments/.env` (nunca en `huntjob_chile`, nunca en un `.env` que se suba a git).
- Precio: `amount=4990`, `currency=CLP`, `interval=3` (mensual) — valores exactos de la API de Flow, no placeholders.
- `planId` del Plan de Flow: `"huntjob_premium_mensual"` — fijo, no cambiar salvo que se decida rehacer el plan de cobro.
- **Corrección respecto al spec original:** el spec asumía que el webhook de Flow llega firmado y hay que validar esa firma. Según la documentación real de Flow, el webhook solo manda un `token` sin firmar — la seguridad viene de que el `token` únicamente resuelve datos válidos al consultarlo de vuelta contra un endpoint firmado (`payment/getStatus`, `customer/getRegisterStatus`). Por eso las rutas de este plan no verifican firma en la entrada, solo validan que venga el `token` y confían en la respuesta de la consulta firmada de vuelta.

---

## Parte 1 — `huntjob_payments` (repo nuevo)

### Task 1: Scaffold del repo + firma HMAC de Flow

**Files:**
- Create: `~/Antigravity/huntjob_payments/flow_client.py`
- Create: `~/Antigravity/huntjob_payments/requirements.txt`
- Create: `~/Antigravity/huntjob_payments/.gitignore`
- Create: `~/Antigravity/huntjob_payments/.env.example`
- Test: `~/Antigravity/huntjob_payments/tests/test_flow_client.py`

**Interfaces:**
- Produces: `flow_client.firmar(params: dict) -> str` — devuelve el hash HMAC-SHA256 hex.

- [ ] **Step 1: Crear el repo y la estructura de carpetas**

```bash
mkdir -p ~/Antigravity/huntjob_payments/tests
cd ~/Antigravity/huntjob_payments
git init -q
```

- [ ] **Step 2: Escribir `.gitignore` y `.env.example`**

`~/Antigravity/huntjob_payments/.gitignore`:
```
__pycache__/
*.pyc
venv/
.env
```

`~/Antigravity/huntjob_payments/.env.example`:
```
# Credenciales de comercio Flow.cl (sandbox mientras no este aprobada la cuenta real)
FLOW_API_KEY=
FLOW_SECRET_KEY=
FLOW_BASE_URL=https://sandbox.flow.cl/api

# Supabase — Service Role Key, bypasea RLS. NUNCA compartir con huntjob_chile.
SUPABASE_URL=https://oonkwgfawfyqtrndshhu.supabase.co
SUPABASE_SERVICE_ROLE_KEY=

# URL publica de este servicio una vez deployado (para armar los callbacks de Flow)
PUBLIC_BASE_URL=http://localhost:5000
```

- [ ] **Step 3: Escribir la prueba de firma que falla**

`~/Antigravity/huntjob_payments/tests/test_flow_client.py`:
```python
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flow_client import firmar


def test_firmar_ordena_alfabeticamente_y_concatena():
    # Ejemplo tomado literal de la documentacion de Flow.
    params = {
        "apiKey": "XXXX-XXXX-XXXX",
        "currency": "CLP",
        "amount": 5000,
    }
    secret_key = "un_secret_de_prueba"

    resultado = firmar(params, secret_key)

    import hmac
    import hashlib
    string_esperado = "amount5000apiKeyXXXX-XXXX-XXXXcurrencyCLP"
    esperado = hmac.new(
        secret_key.encode("utf-8"), string_esperado.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    assert resultado == esperado
```

- [ ] **Step 4: Correr el test y verificar que falla**

Run: `cd ~/Antigravity/huntjob_payments && python3 -m pytest tests/test_flow_client.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'flow_client'` (el archivo todavía no existe)

- [ ] **Step 5: Implementar `firmar()`**

`~/Antigravity/huntjob_payments/flow_client.py`:
```python
"""
Cliente de la API de Flow.cl (https://www.flow.cl/docs/api.html).

Firma cada request con HMAC-SHA256 sobre los parametros ordenados
alfabeticamente por nombre, concatenados como nombre+valor+nombre+valor,
usando el SecretKey del comercio como llave.
"""

import hashlib
import hmac


def firmar(params: dict, secret_key: str) -> str:
    claves_ordenadas = sorted(params.keys())
    string_a_firmar = "".join(f"{clave}{params[clave]}" for clave in claves_ordenadas)
    return hmac.new(
        secret_key.encode("utf-8"), string_a_firmar.encode("utf-8"), hashlib.sha256
    ).hexdigest()
```

- [ ] **Step 6: Correr el test y verificar que pasa**

Run: `cd ~/Antigravity/huntjob_payments && python3 -m pytest tests/test_flow_client.py -v`
Expected: PASS

- [ ] **Step 7: `requirements.txt` y commit**

`~/Antigravity/huntjob_payments/requirements.txt`:
```
flask==3.1.0
gunicorn==23.0.0
requests==2.34.2
supabase==2.31.0
python-dotenv==1.0.1
pytest==8.3.4
```

```bash
cd ~/Antigravity/huntjob_payments
git add flow_client.py requirements.txt .gitignore .env.example tests/test_flow_client.py
git commit -m "feat: firma HMAC-SHA256 de requests a Flow.cl"
```

---

### Task 2: Cliente de Flow — customer, registro de tarjeta y plan

**Files:**
- Modify: `~/Antigravity/huntjob_payments/flow_client.py`
- Test: `~/Antigravity/huntjob_payments/tests/test_flow_client.py`

**Interfaces:**
- Consumes: `firmar(params, secret_key) -> str` (Task 1)
- Produces:
  - `crear_cliente(nombre, email, external_id) -> dict` (con `customerId`)
  - `enviar_a_registrar_tarjeta(customer_id, url_return) -> dict` (con `url`, `token`)
  - `obtener_estado_registro_tarjeta(token) -> dict` (con `status`, `customerId`)
  - `crear_plan_si_no_existe() -> dict`
  - `crear_suscripcion(customer_id) -> dict` (con `subscriptionId`)
  - `cancelar_suscripcion(subscription_id, inmediata: bool) -> dict`

- [ ] **Step 1: Escribir los tests con `requests` mockeado**

Agregar a `~/Antigravity/huntjob_payments/tests/test_flow_client.py`:
```python
from unittest.mock import patch, MagicMock

import flow_client


def _mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


@patch("flow_client.requests.post")
def test_crear_cliente_llama_al_endpoint_correcto(mock_post):
    mock_post.return_value = _mock_response({"customerId": "cus_abc123"})

    resultado = flow_client.crear_cliente(
        nombre="Juan Perez",
        email="juan@example.com",
        external_id="user-uuid-123",
        api_key="apikey-test",
        secret_key="secret-test",
        base_url="https://sandbox.flow.cl/api",
    )

    assert resultado["customerId"] == "cus_abc123"
    url_llamada = mock_post.call_args[0][0]
    assert url_llamada == "https://sandbox.flow.cl/api/customer/create"
    datos_enviados = mock_post.call_args[1]["data"]
    assert datos_enviados["name"] == "Juan Perez"
    assert datos_enviados["externalId"] == "user-uuid-123"
    assert "s" in datos_enviados


@patch("flow_client.requests.post")
def test_enviar_a_registrar_tarjeta_arma_url_con_token(mock_post):
    mock_post.return_value = _mock_response(
        {"url": "https://sandbox.flow.cl/app/customer/disclaimer.php", "token": "TOKEN123"}
    )

    resultado = flow_client.enviar_a_registrar_tarjeta(
        customer_id="cus_abc123",
        url_return="https://huntjob-payments.onrender.com/webhook/flow/card-registered",
        api_key="apikey-test",
        secret_key="secret-test",
        base_url="https://sandbox.flow.cl/api",
    )

    assert resultado["token"] == "TOKEN123"
    assert resultado["url"] == "https://sandbox.flow.cl/app/customer/disclaimer.php"


@patch("flow_client.requests.get")
def test_obtener_estado_registro_tarjeta(mock_get):
    mock_get.return_value = _mock_response(
        {"status": "1", "customerId": "cus_abc123", "creditCardType": "Visa"}
    )

    resultado = flow_client.obtener_estado_registro_tarjeta(
        token="TOKEN123",
        api_key="apikey-test",
        secret_key="secret-test",
        base_url="https://sandbox.flow.cl/api",
    )

    assert resultado["status"] == "1"
    assert resultado["customerId"] == "cus_abc123"


@patch("flow_client.requests.post")
def test_crear_suscripcion(mock_post):
    mock_post.return_value = _mock_response(
        {"subscriptionId": "sus_xyz789", "planId": "huntjob_premium_mensual"}
    )

    resultado = flow_client.crear_suscripcion(
        customer_id="cus_abc123",
        api_key="apikey-test",
        secret_key="secret-test",
        base_url="https://sandbox.flow.cl/api",
    )

    assert resultado["subscriptionId"] == "sus_xyz789"
    datos_enviados = mock_post.call_args[1]["data"]
    assert datos_enviados["planId"] == "huntjob_premium_mensual"
    assert datos_enviados["customerId"] == "cus_abc123"


@patch("flow_client.requests.post")
def test_cancelar_suscripcion_inmediata(mock_post):
    mock_post.return_value = _mock_response({"subscriptionId": "sus_xyz789", "status": "3"})

    flow_client.cancelar_suscripcion(
        subscription_id="sus_xyz789",
        inmediata=True,
        api_key="apikey-test",
        secret_key="secret-test",
        base_url="https://sandbox.flow.cl/api",
    )

    datos_enviados = mock_post.call_args[1]["data"]
    assert datos_enviados["at_period_end"] == 0
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `cd ~/Antigravity/huntjob_payments && python3 -m pytest tests/test_flow_client.py -v`
Expected: FAIL — `AttributeError: module 'flow_client' has no attribute 'crear_cliente'` (y las otras funciones)

- [ ] **Step 3: Implementar las funciones**

Agregar a `~/Antigravity/huntjob_payments/flow_client.py`:
```python
import requests


def crear_cliente(nombre: str, email: str, external_id: str, api_key: str, secret_key: str, base_url: str) -> dict:
    params = {"apiKey": api_key, "name": nombre, "email": email, "externalId": external_id}
    params["s"] = firmar(params, secret_key)
    respuesta = requests.post(f"{base_url}/customer/create", data=params, timeout=15)
    respuesta.raise_for_status()
    return respuesta.json()


def enviar_a_registrar_tarjeta(customer_id: str, url_return: str, api_key: str, secret_key: str, base_url: str) -> dict:
    params = {"apiKey": api_key, "customerId": customer_id, "url_return": url_return}
    params["s"] = firmar(params, secret_key)
    respuesta = requests.post(f"{base_url}/customer/register", data=params, timeout=15)
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_estado_registro_tarjeta(token: str, api_key: str, secret_key: str, base_url: str) -> dict:
    params = {"apiKey": api_key, "token": token}
    params["s"] = firmar(params, secret_key)
    respuesta = requests.get(f"{base_url}/customer/getRegisterStatus", params=params, timeout=15)
    respuesta.raise_for_status()
    return respuesta.json()


PLAN_ID = "huntjob_premium_mensual"


def crear_plan_si_no_existe(url_callback: str, api_key: str, secret_key: str, base_url: str) -> dict:
    """
    Idempotente: si el plan ya existe, Flow responde 400 (planId
    duplicado) y devolvemos el plan existente consultandolo en vez de
    fallar. Se corre una sola vez como setup, no en cada deploy.
    """
    params = {
        "apiKey": api_key,
        "planId": PLAN_ID,
        "name": "HuntJob Chile Premium (mensual)",
        "currency": "CLP",
        "amount": 4990,
        "interval": 3,
        "urlCallback": url_callback,
    }
    params["s"] = firmar(params, secret_key)
    respuesta = requests.post(f"{base_url}/plans/create", data=params, timeout=15)
    if respuesta.status_code == 400:
        return obtener_plan(api_key, secret_key, base_url)
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_plan(api_key: str, secret_key: str, base_url: str) -> dict:
    params = {"apiKey": api_key, "planId": PLAN_ID}
    params["s"] = firmar(params, secret_key)
    respuesta = requests.get(f"{base_url}/plans/get", params=params, timeout=15)
    respuesta.raise_for_status()
    return respuesta.json()


def crear_suscripcion(customer_id: str, api_key: str, secret_key: str, base_url: str) -> dict:
    params = {"apiKey": api_key, "planId": PLAN_ID, "customerId": customer_id}
    params["s"] = firmar(params, secret_key)
    respuesta = requests.post(f"{base_url}/subscription/create", data=params, timeout=15)
    respuesta.raise_for_status()
    return respuesta.json()


def cancelar_suscripcion(subscription_id: str, inmediata: bool, api_key: str, secret_key: str, base_url: str) -> dict:
    params = {
        "apiKey": api_key,
        "subscriptionId": subscription_id,
        "at_period_end": 0 if inmediata else 1,
    }
    params["s"] = firmar(params, secret_key)
    respuesta = requests.post(f"{base_url}/subscription/cancel", data=params, timeout=15)
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_estado_pago(token: str, api_key: str, secret_key: str, base_url: str) -> dict:
    """Usado por el webhook de cobros recurrentes (ver Task 6)."""
    params = {"apiKey": api_key, "token": token}
    params["s"] = firmar(params, secret_key)
    respuesta = requests.get(f"{base_url}/payment/getStatus", params=params, timeout=15)
    respuesta.raise_for_status()
    return respuesta.json()
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `cd ~/Antigravity/huntjob_payments && python3 -m pytest tests/test_flow_client.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
cd ~/Antigravity/huntjob_payments
git add flow_client.py tests/test_flow_client.py
git commit -m "feat: cliente completo de Flow (customer, tarjeta, plan, suscripcion)"
```

---

### Task 3: Cliente admin de Supabase + migración de `planes_usuario`

**Files:**
- Modify: `~/Antigravity/huntjob_chile/sql/schema.sql`
- Create: `~/Antigravity/huntjob_payments/supabase_admin.py`
- Test: `~/Antigravity/huntjob_payments/tests/test_supabase_admin.py`

**Interfaces:**
- Produces:
  - `activar_premium(user_id: str, flow_customer_id: str) -> None`
  - `desactivar_premium(flow_customer_id: str) -> bool` (False si no encontro al usuario)
  - `buscar_user_id_por_customer_id(flow_customer_id: str) -> str | None`

- [ ] **Step 1: Migración SQL (se corre a mano en Supabase, igual que el schema original)**

Agregar al final de `~/Antigravity/huntjob_chile/sql/schema.sql`:
```sql
-- Suscripcion Premium via Flow.cl (2026-07-22)
alter table public.planes_usuario
    add column if not exists flow_customer_id text unique,
    add column if not exists plan_vence_en timestamptz;
```

- [ ] **Step 2: Escribir los tests con el cliente de Supabase mockeado**

`~/Antigravity/huntjob_payments/tests/test_supabase_admin.py`:
```python
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import supabase_admin


@patch("supabase_admin._cliente_admin")
def test_activar_premium_hace_upsert_con_fecha_de_vencimiento(mock_cliente_fn):
    mock_cliente = MagicMock()
    mock_cliente_fn.return_value = mock_cliente

    supabase_admin.activar_premium(user_id="uuid-123", flow_customer_id="cus_abc123")

    mock_cliente.table.assert_called_with("planes_usuario")
    llamada_upsert = mock_cliente.table.return_value.upsert
    fila = llamada_upsert.call_args[0][0]
    assert fila["user_id"] == "uuid-123"
    assert fila["plan"] == "premium"
    assert fila["flow_customer_id"] == "cus_abc123"
    assert "plan_vence_en" in fila


@patch("supabase_admin._cliente_admin")
def test_buscar_user_id_por_customer_id_encontrado(mock_cliente_fn):
    mock_cliente = MagicMock()
    mock_cliente_fn.return_value = mock_cliente
    mock_cliente.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
        {"user_id": "uuid-123"}
    ]

    resultado = supabase_admin.buscar_user_id_por_customer_id("cus_abc123")

    assert resultado == "uuid-123"


@patch("supabase_admin._cliente_admin")
def test_buscar_user_id_por_customer_id_no_encontrado(mock_cliente_fn):
    mock_cliente = MagicMock()
    mock_cliente_fn.return_value = mock_cliente
    mock_cliente.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []

    resultado = supabase_admin.buscar_user_id_por_customer_id("cus_no_existe")

    assert resultado is None


@patch("supabase_admin._cliente_admin")
def test_desactivar_premium_encontrado(mock_cliente_fn):
    mock_cliente = MagicMock()
    mock_cliente_fn.return_value = mock_cliente
    mock_cliente.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
        {"user_id": "uuid-123"}
    ]

    resultado = supabase_admin.desactivar_premium("cus_abc123")

    assert resultado is True
    llamada_update = mock_cliente.table.return_value.update
    fila = llamada_update.call_args[0][0]
    assert fila["plan"] == "free"
```

- [ ] **Step 3: Correr los tests y verificar que fallan**

Run: `cd ~/Antigravity/huntjob_payments && python3 -m pytest tests/test_supabase_admin.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'supabase_admin'`

- [ ] **Step 4: Implementar `supabase_admin.py`**

`~/Antigravity/huntjob_payments/supabase_admin.py`:
```python
"""
Cliente de Supabase con la Service Role Key — bypasea Row Level
Security a proposito, porque este servicio corre server-to-server sin
un usuario logueado (recibe webhooks de Flow, no requests de un
navegador). Por eso esta key nunca debe compartirse con huntjob_chile.
"""

import os
from datetime import datetime, timedelta, timezone

from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

LIMITE_GRATIS_MENSUAL = 5


def _cliente_admin() -> Client:
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Falta SUPABASE_SERVICE_ROLE_KEY en el entorno.")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def activar_premium(user_id: str, flow_customer_id: str) -> None:
    vence_en = datetime.now(timezone.utc) + timedelta(days=31)
    _cliente_admin().table("planes_usuario").upsert(
        {
            "user_id": user_id,
            "plan": "premium",
            "flow_customer_id": flow_customer_id,
            "plan_vence_en": vence_en.isoformat(),
        },
        on_conflict="user_id",
    ).execute()


def buscar_user_id_por_customer_id(flow_customer_id: str) -> str | None:
    resultado = (
        _cliente_admin()
        .table("planes_usuario")
        .select("user_id")
        .eq("flow_customer_id", flow_customer_id)
        .limit(1)
        .execute()
    )
    filas = resultado.data or []
    return filas[0]["user_id"] if filas else None


def desactivar_premium(flow_customer_id: str) -> bool:
    user_id = buscar_user_id_por_customer_id(flow_customer_id)
    if not user_id:
        return False
    _cliente_admin().table("planes_usuario").update(
        {"plan": "free", "limite_mensual": LIMITE_GRATIS_MENSUAL, "plan_vence_en": None}
    ).eq("user_id", user_id).execute()
    return True
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `cd ~/Antigravity/huntjob_payments && python3 -m pytest tests/test_supabase_admin.py -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit en ambos repos**

```bash
cd ~/Antigravity/huntjob_chile
git add sql/schema.sql
git commit -m "feat(sql): columnas flow_customer_id y plan_vence_en en planes_usuario"
git push

cd ~/Antigravity/huntjob_payments
git add supabase_admin.py tests/test_supabase_admin.py
git commit -m "feat: cliente admin de Supabase (Service Role Key) para activar/desactivar premium"
```

**Nota manual:** correr la migración del Step 1 en Supabase Dashboard > SQL Editor antes de probar nada en vivo — no se aplica sola.

---

### Task 4: Servidor Flask + ruta `/webhook/flow/card-registered`

**Files:**
- Create: `~/Antigravity/huntjob_payments/app.py`
- Create: `~/Antigravity/huntjob_payments/config.py`
- Test: `~/Antigravity/huntjob_payments/tests/test_app.py`

**Interfaces:**
- Consumes: `flow_client.obtener_estado_registro_tarjeta`, `flow_client.crear_suscripcion` (Task 2); `supabase_admin.activar_premium`, `supabase_admin.buscar_user_id_por_customer_id` (Task 3)
- Produces: Flask app `app` con ruta `POST /webhook/flow/card-registered`

Este es el callback de `customer/register` (ver Task 5 para donde se dispara ese registro desde `huntjob_chile`). El `externalId` que se le pasa a Flow al crear el cliente **es el `user_id` de Supabase** — así este webhook puede activar el plan sin necesitar una sesión de usuario.

- [ ] **Step 1: `config.py` con las variables de entorno centralizadas**

`~/Antigravity/huntjob_payments/config.py`:
```python
import os

FLOW_API_KEY = os.environ.get("FLOW_API_KEY", "")
FLOW_SECRET_KEY = os.environ.get("FLOW_SECRET_KEY", "")
FLOW_BASE_URL = os.environ.get("FLOW_BASE_URL", "https://sandbox.flow.cl/api")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:5000")
```

- [ ] **Step 2: Test de la ruta con Flask test client**

`~/Antigravity/huntjob_payments/tests/test_app.py`:
```python
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as app_module


def _cliente_de_prueba():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


@patch("app.supabase_admin.activar_premium")
@patch("app.flow_client.crear_suscripcion")
@patch("app.flow_client.obtener_estado_registro_tarjeta")
def test_card_registered_activa_premium_si_tarjeta_quedo_registrada(
    mock_estado, mock_suscripcion, mock_activar
):
    mock_estado.return_value = {
        "status": "1",
        "customerId": "cus_abc123",
        "externalId": "uuid-usuario-123",
    }
    mock_suscripcion.return_value = {"subscriptionId": "sus_xyz789"}

    cliente = _cliente_de_prueba()
    respuesta = cliente.post("/webhook/flow/card-registered", data={"token": "TOKEN123"})

    assert respuesta.status_code == 200
    mock_suscripcion.assert_called_once()
    mock_activar.assert_called_once_with(user_id="uuid-usuario-123", flow_customer_id="cus_abc123")


@patch("app.supabase_admin.activar_premium")
@patch("app.flow_client.crear_suscripcion")
@patch("app.flow_client.obtener_estado_registro_tarjeta")
def test_card_registered_no_activa_nada_si_registro_fallo(
    mock_estado, mock_suscripcion, mock_activar
):
    mock_estado.return_value = {"status": "2", "customerId": "cus_abc123"}

    cliente = _cliente_de_prueba()
    respuesta = cliente.post("/webhook/flow/card-registered", data={"token": "TOKEN123"})

    assert respuesta.status_code == 200
    mock_suscripcion.assert_not_called()
    mock_activar.assert_not_called()


def test_card_registered_sin_token_devuelve_400():
    cliente = _cliente_de_prueba()
    respuesta = cliente.post("/webhook/flow/card-registered", data={})
    assert respuesta.status_code == 400
```

- [ ] **Step 3: Correr los tests y verificar que fallan**

Run: `cd ~/Antigravity/huntjob_payments && python3 -m pytest tests/test_app.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 4: Implementar `app.py`**

`~/Antigravity/huntjob_payments/app.py`:
```python
"""
Servicio Flask standalone que recibe los webhooks de Flow.cl para la
suscripcion Premium de HuntJob Chile. Streamlit (huntjob_chile) no
puede exponer rutas HTTP propias, por eso este servicio vive aparte,
con su propio deploy en Render — mismo patron que GatitoPro/nimarco_erp.
"""

import logging

from flask import Flask, request, jsonify

import config
import flow_client
import supabase_admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("huntjob_payments")

app = Flask(__name__)


@app.route("/webhook/flow/card-registered", methods=["POST"])
def webhook_card_registered():
    """
    Flow llama aca despues de que el cliente registra su tarjeta
    (ver customer/register). El commercio debe consumir
    customer/getRegisterStatus con el token recibido para saber si
    quedo registrada, segun la doc oficial de Flow.
    """
    token = request.form.get("token")
    if not token:
        return jsonify({"error": "falta el parametro token"}), 400

    estado = flow_client.obtener_estado_registro_tarjeta(
        token=token,
        api_key=config.FLOW_API_KEY,
        secret_key=config.FLOW_SECRET_KEY,
        base_url=config.FLOW_BASE_URL,
    )

    if str(estado.get("status")) != "1":
        logger.info("Registro de tarjeta no exitoso: %s", estado)
        return jsonify({"status": "ignorado"}), 200

    customer_id = estado["customerId"]
    user_id = estado.get("externalId")

    suscripcion = flow_client.crear_suscripcion(
        customer_id=customer_id,
        api_key=config.FLOW_API_KEY,
        secret_key=config.FLOW_SECRET_KEY,
        base_url=config.FLOW_BASE_URL,
    )
    logger.info("Suscripcion creada: %s", suscripcion.get("subscriptionId"))

    supabase_admin.activar_premium(user_id=user_id, flow_customer_id=customer_id)
    return jsonify({"status": "premium activado"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

**Nota:** `customer/getRegisterStatus` no documenta explícitamente que devuelva `externalId` en su response de ejemplo — la doc de Flow solo muestra `status`, `customerId`, `creditCardType`, `last4CardDigits`. Si en el sandbox real no viene `externalId` en esa respuesta, hay que buscarlo con `buscar_user_id_por_customer_id` cruzando por otra via, o guardar una tabla temporal `customer_id -> user_id` al momento de llamar a `customer/register` (antes de que Flow redirija). Verificar esto en el Task 8 (pruebas end-to-end en sandbox) antes de dar esto por cerrado.

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `cd ~/Antigravity/huntjob_payments && python3 -m pytest tests/test_app.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
cd ~/Antigravity/huntjob_payments
git add app.py config.py tests/test_app.py
git commit -m "feat: webhook de registro de tarjeta, activa suscripcion+premium"
```

---

### Task 5: Ruta `/webhook/flow/charge` (cobros recurrentes) + cancelación

**Files:**
- Modify: `~/Antigravity/huntjob_payments/app.py`
- Modify: `~/Antigravity/huntjob_payments/tests/test_app.py`

**Interfaces:**
- Consumes: `flow_client.obtener_estado_pago` (Task 2); `supabase_admin.activar_premium`, `supabase_admin.desactivar_premium`, `supabase_admin.buscar_user_id_por_customer_id` (Task 3)
- Produces: ruta `POST /webhook/flow/charge`

**Importante — esto necesita verificarse contra el sandbox real (Task 8):** la doc de Flow confirma que el `urlCallback` del Plan recibe un `token` vía POST (mismo patrón general que el resto de las notificaciones asíncronas), pero no deja explícito con qué servicio se resuelve ese token para un cobro de suscripción — a diferencia de `payment/create`, que documenta `payment/getStatus` sin ambigüedad. La implementación de abajo asume que también se resuelve con `payment/getStatus` (porque toda suscripción de Flow genera una orden de pago por debajo), campo `status == 2` como "pagado". El Task 8 confirma esto empíricamente antes de ir a producción.

- [ ] **Step 1: Agregar los tests de la ruta de cobro**

Agregar a `~/Antigravity/huntjob_payments/tests/test_app.py`:
```python
@patch("app.supabase_admin.activar_premium")
@patch("app.supabase_admin.buscar_user_id_por_customer_id")
@patch("app.flow_client.obtener_estado_pago")
def test_charge_webhook_renueva_premium_si_pago_aprobado(
    mock_estado_pago, mock_buscar_user, mock_activar
):
    mock_estado_pago.return_value = {"status": 2, "flowOrder": 999, "commerceOrder": "cus_abc123"}
    mock_buscar_user.return_value = "uuid-usuario-123"

    cliente = _cliente_de_prueba()
    respuesta = cliente.post("/webhook/flow/charge", data={"token": "TOKEN_COBRO"})

    assert respuesta.status_code == 200
    mock_activar.assert_called_once_with(user_id="uuid-usuario-123", flow_customer_id="cus_abc123")


@patch("app.supabase_admin.desactivar_premium")
@patch("app.flow_client.obtener_estado_pago")
def test_charge_webhook_no_toca_nada_si_pago_pendiente(mock_estado_pago, mock_desactivar):
    mock_estado_pago.return_value = {"status": 1, "commerceOrder": "cus_abc123"}

    cliente = _cliente_de_prueba()
    respuesta = cliente.post("/webhook/flow/charge", data={"token": "TOKEN_COBRO"})

    assert respuesta.status_code == 200
    mock_desactivar.assert_not_called()


@patch("app.supabase_admin.desactivar_premium")
def test_cancel_webhook_desactiva_premium(mock_desactivar):
    mock_desactivar.return_value = True

    cliente = _cliente_de_prueba()
    respuesta = cliente.post("/webhook/flow/subscription-canceled", data={"customerId": "cus_abc123"})

    assert respuesta.status_code == 200
    mock_desactivar.assert_called_once_with("cus_abc123")
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `cd ~/Antigravity/huntjob_payments && python3 -m pytest tests/test_app.py -v`
Expected: FAIL — la ruta `/webhook/flow/charge` no existe (404)

- [ ] **Step 3: Implementar las rutas**

Agregar a `~/Antigravity/huntjob_payments/app.py` (antes de `if __name__ == "__main__":`):
```python
@app.route("/webhook/flow/charge", methods=["POST"])
def webhook_charge():
    """
    Configurado como urlCallback del Plan (ver flow_client.crear_plan_si_no_existe).
    Se dispara en cada cobro mensual de la suscripcion.
    """
    token = request.form.get("token")
    if not token:
        return jsonify({"error": "falta el parametro token"}), 400

    estado = flow_client.obtener_estado_pago(
        token=token,
        api_key=config.FLOW_API_KEY,
        secret_key=config.FLOW_SECRET_KEY,
        base_url=config.FLOW_BASE_URL,
    )

    if estado.get("status") != 2:
        logger.info("Cobro no aprobado todavia (status=%s), no se toca el plan", estado.get("status"))
        return jsonify({"status": "pendiente"}), 200

    flow_customer_id = estado.get("commerceOrder")
    user_id = supabase_admin.buscar_user_id_por_customer_id(flow_customer_id)
    if not user_id:
        logger.error("Cobro aprobado de un customerId desconocido: %s", flow_customer_id)
        return jsonify({"status": "customer desconocido"}), 200

    supabase_admin.activar_premium(user_id=user_id, flow_customer_id=flow_customer_id)
    return jsonify({"status": "premium renovado"}), 200


@app.route("/webhook/flow/subscription-canceled", methods=["POST"])
def webhook_subscription_canceled():
    """
    No es un callback nativo de Flow (Flow no dispara webhooks por
    cancelacion, solo deja de enviar cobros). Esta ruta la llama
    huntjob_chile inmediatamente despues de pedirle a Flow que
    cancele, para no esperar hasta el proximo ciclo de facturacion.
    """
    customer_id = request.form.get("customerId")
    if not customer_id:
        return jsonify({"error": "falta el parametro customerId"}), 400

    encontrado = supabase_admin.desactivar_premium(customer_id)
    if not encontrado:
        return jsonify({"status": "customer desconocido"}), 200
    return jsonify({"status": "premium desactivado"}), 200
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `cd ~/Antigravity/huntjob_payments && python3 -m pytest tests/ -v`
Expected: PASS (todos los tests de los 5 tasks anteriores, ~16 tests)

- [ ] **Step 5: Commit**

```bash
cd ~/Antigravity/huntjob_payments
git add app.py tests/test_app.py
git commit -m "feat: webhook de cobros recurrentes y ruta de cancelacion"
```

---

### Task 6: Dockerfile + deploy a Render

**Files:**
- Create: `~/Antigravity/huntjob_payments/Dockerfile`
- Create: `~/Antigravity/huntjob_payments/README.md`

- [ ] **Step 1: Dockerfile**

`~/Antigravity/huntjob_payments/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
```

- [ ] **Step 2: README con las instrucciones de deploy**

`~/Antigravity/huntjob_payments/README.md`:
```markdown
# HuntJob Payments

Microservicio Flask standalone que recibe los webhooks de Flow.cl para
la suscripcion Premium de HuntJob Chile. Ver el spec completo en
`huntjob_chile/docs/superpowers/specs/2026-07-22-premium-flow-billing-design.md`.

## Correr local

\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # completar con las credenciales reales
python3 app.py
\`\`\`

## Setup del Plan de Flow (una sola vez)

\`\`\`bash
python3 -c "
import config, flow_client
resultado = flow_client.crear_plan_si_no_existe(
    url_callback=config.PUBLIC_BASE_URL + '/webhook/flow/charge',
    api_key=config.FLOW_API_KEY,
    secret_key=config.FLOW_SECRET_KEY,
    base_url=config.FLOW_BASE_URL,
)
print(resultado)
"
\`\`\`

## Deploy

Servicio Web nuevo en Render, mismo team que `huntjob_chile`. Variables
de entorno: las de `.env.example`, con `PUBLIC_BASE_URL` apuntando a la
URL real que Render asigne.
```

- [ ] **Step 3: Commit**

```bash
cd ~/Antigravity/huntjob_payments
git add Dockerfile README.md
git commit -m "chore: Dockerfile y README de deploy"
```

- [ ] **Step 4: Crear repo en GitHub y pushear**

```bash
cd ~/Antigravity/huntjob_payments
gh repo create alecumsille/huntjob_payments --private --source=. --remote=origin
git push -u origin master
```

- [ ] **Step 5: Deploy manual a Render (vía dashboard, no automatizable desde acá)**

En https://dashboard.render.com — New > Web Service > conectar `alecumsille/huntjob_payments` > Docker > completar las env vars del `.env.example` (con las credenciales reales del sandbox de Flow y la Service Role Key de Supabase, sacada de Supabase Dashboard > Settings > API).

---

## Parte 2 — `huntjob_chile` (repo existente)

### Task 7: Botón "Actualizar a Premium" y "Cancelar suscripción" en `app.py`

**Files:**
- Create: `~/Antigravity/huntjob_chile/core/flow_checkout.py`
- Modify: `~/Antigravity/huntjob_chile/app.py:346-378` (bloque del sidebar)
- Modify: `~/Antigravity/huntjob_chile/requirements.txt`

**Interfaces:**
- Produces: `flow_checkout.iniciar_registro_tarjeta(user_id, nombre, email) -> str` (URL de redirect)

- [ ] **Step 1: `core/flow_checkout.py`**

`~/Antigravity/huntjob_chile/core/flow_checkout.py`:
```python
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
```

- [ ] **Step 2: Agregar el botón en el sidebar**

En `~/Antigravity/huntjob_chile/app.py`, dentro del bloque `with st.sidebar:` (alrededor de la línea 354-364, justo después de donde se muestra la barra de progreso del plan gratuito), agregar:

```python
    if contexto_usuario:
        try:
            plan = obtener_plan(contexto_usuario["user_id"], contexto_usuario["access_token"])
            if plan["plan"] == "premium":
                st.caption("Plan Premium — generaciones sin límite ✨")
                if st.button("Cancelar suscripción", use_container_width=True):
                    st.session_state["confirmar_cancelacion"] = True
                if st.session_state.get("confirmar_cancelacion"):
                    st.warning("¿Seguro? Vas a volver al plan gratuito (5 generaciones/mes).")
                    if st.button("Sí, cancelar", type="primary", use_container_width=True):
                        import requests as _requests
                        _requests.post(
                            f"{PAYMENTS_SERVICE_URL}/webhook/flow/subscription-canceled",
                            data={"customerId": plan.get("flow_customer_id", "")},
                            timeout=15,
                        )
                        st.session_state["confirmar_cancelacion"] = False
                        st.rerun()
            else:
                usados = plan["generaciones_este_mes"]
                limite = plan["limite_mensual"]
                st.progress(
                    min(usados / limite, 1.0) if limite else 0,
                    text=f"Plan gratuito — {usados}/{limite} generaciones este mes",
                )
                if st.button("Actualizar a Premium ($4.990/mes)", type="primary", use_container_width=True):
                    from core.flow_checkout import iniciar_registro_tarjeta

                    url_pago = iniciar_registro_tarjeta(
                        user_id=contexto_usuario["user_id"],
                        nombre=st.session_state.get("user_email", "Usuario"),
                        email=st.session_state.get("user_email", ""),
                    )
                    st.link_button("Ir a pagar con Flow", url_pago, use_container_width=True)
        except Exception:
            pass
    else:
        st.caption("Modo invitado — datos no guardados")
```

Esto **reemplaza** el bloque `if contexto_usuario: try: ... except Exception: pass` que ya existe en esa sección (líneas 351-364 aproximadamente) — no se agrega en paralelo, se modifica ese mismo bloque.

También agregar el import al principio del archivo, junto a los demás imports de `core.*`:
```python
from core.flow_checkout import PAYMENTS_SERVICE_URL
```

- [ ] **Step 3: Agregar dependencias faltantes a `requirements.txt`**

`~/Antigravity/huntjob_chile/requirements.txt` — verificar que `requests` ya está (sí está, se usa en `core/scraper_web.py`); no hace falta agregar nada nuevo.

- [ ] **Step 4: Probar localmente**

```bash
cd ~/Antigravity/huntjob_chile
python3 -m py_compile app.py core/flow_checkout.py
```
Expected: sin errores de sintaxis. (Prueba funcional real de extremo a extremo requiere el servicio `huntjob_payments` ya deployado — se hace en el Task 8.)

- [ ] **Step 5: Commit y push**

```bash
cd ~/Antigravity/huntjob_chile
git add app.py core/flow_checkout.py
git commit -m "feat: boton Actualizar a Premium / Cancelar suscripcion via Flow.cl"
git push
```

---

### Task 8: Prueba end-to-end en sandbox y ajuste del webhook de cobro

**Files:**
- Modify: `~/Antigravity/huntjob_payments/app.py` (solo si el diagnóstico de este task encuentra que el payload real difiere de lo asumido en el Task 5)

- [ ] **Step 1: Correr el setup del Plan contra el sandbox real**

Con la cuenta de sandbox de Flow ya creada y el servicio deployado en Render, correr el script del README del Task 6, apuntando `PUBLIC_BASE_URL` a la URL real de Render.

- [ ] **Step 2: Probar el flujo completo con una tarjeta de prueba**

Desde `huntjob.cumsille.me`, loguearse con una cuenta real, click en "Actualizar a Premium", completar el pago con una tarjeta de prueba chilena (las tarjetas de sandbox están documentadas en https://www.flow.cl/docs/api.html#section/Introduccion/Realizar-pruebas-en-nuestro-ambiente-Sandbox).

- [ ] **Step 3: Verificar en Supabase que el plan quedó en `premium`**

En Supabase Dashboard > Table Editor > `planes_usuario`, confirmar que la fila del usuario de prueba tiene `plan = premium`, `flow_customer_id` con el `cus_...` correcto, y `plan_vence_en` seteado ~1 mes adelante.

- [ ] **Step 4: Inspeccionar el payload real del webhook de cobro**

Revisar los logs de Render del servicio `huntjob_payments` (`estado = flow_client.obtener_estado_pago(...)` loguea el resultado completo vía `logger.info`) para el primer cobro real generado por la suscripción de prueba. Confirmar que `commerceOrder` efectivamente trae el `flow_customer_id` como se asumió en el Task 5 — si Flow devuelve otro campo (por ejemplo si `commerceOrder` viene vacío o con otro valor), ajustar `webhook_charge()` en `app.py` para leer el campo correcto, agregar un test que cubra ese caso real, y hacer commit del fix.

- [ ] **Step 5: Probar la cancelación**

Click en "Cancelar suscripción" en la UI, confirmar que `planes_usuario.plan` vuelve a `free` inmediatamente y que en el dashboard de Flow la suscripción queda cancelada.

- [ ] **Step 6: Commit final si hubo ajustes**

```bash
cd ~/Antigravity/huntjob_payments
git add app.py tests/test_app.py
git commit -m "fix: ajustar parseo del webhook de cobro segun payload real de sandbox"
git push
```
