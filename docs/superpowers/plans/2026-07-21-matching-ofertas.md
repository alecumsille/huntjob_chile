# Matching de ofertas contra el perfil Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar un botón "Analizar match" por tarjeta de oferta en "Buscador de Vacantes" que compara esa oferta puntual contra el perfil guardado y muestra un score 0-100 + explicación breve.

**Architecture:** Una función nueva en `core/motor_ia.py` (`analizar_match`) que pide a Gemini una respuesta JSON estructurada (score + explicación) en vez de texto libre parseado con regex. En `app.py`, los resultados de búsqueda pasan a vivir en `st.session_state` (hoy son variables locales que desaparecen en cualquier rerun disparado por un botón dentro de una tarjeta), y cada tarjeta gestiona su propio análisis vía un dict en `st.session_state.matches` keyed por el link de la oferta.

**Tech Stack:** Python 3.10+, Streamlit, Gemini API (`generationConfig.responseSchema`, ya verificado en vivo contra el modelo `gemini-3.1-flash-lite`).

## Global Constraints

- `analizar_match` usa `_obtener_api_key()` y las constantes (`TIMEOUT_SEGUNDOS`, `LIMITE_CARACTERES_CONTEXTO`, `URL_API`, `MODELO`) ya existentes en `core/motor_ia.py` — no se duplican.
- El análisis es bajo demanda, nunca automático para toda la lista de resultados (costo/tiempo de la API).
- Un error al analizar una oferta no debe romper ni ocultar el resto de la lista de resultados.
- Cero emojis en código, UI y mensajes (Material icons sí, ya es el estilo establecido).
- No usar `logros_y_experiencia` para generar CV/CL — esa es la fase 3 (personalización), un trabajo separado, no tocarlo en este plan.
- No agregar ordenamiento/filtrado de resultados por score, ni persistencia del análisis entre sesiones (fuera de alcance del spec).

---

### Task 1: `analizar_match` en core/motor_ia.py

**Files:**
- Modify: `core/motor_ia.py` (agregar función nueva al final del archivo)

**Interfaces:**
- Consumes: `_obtener_api_key()`, `URL_API`, `MODELO`, `TIMEOUT_SEGUNDOS`, `LIMITE_CARACTERES_CONTEXTO`, `ErrorIA` (todos ya existen en el mismo archivo).
- Produces: `analizar_match(texto_oferta: str, perfil: dict) -> dict` con keys `score` (int, 0-100) y `explicacion` (str). Lanza `ErrorIA` en cualquier fallo.

- [ ] **Step 1: Agregar el import de json**

Al inicio de `core/motor_ia.py`, reemplazar:

```python
import os
import requests
```

por:

```python
import json
import os
import requests
```

- [ ] **Step 2: Escribir analizar_match**

Al final de `core/motor_ia.py`, agregar:

```python


def analizar_match(texto_oferta: str, perfil: dict) -> dict:
    """
    Compara el perfil del usuario contra una oferta real y devuelve un
    score 0-100 + explicación breve, vía respuesta JSON estructurada de
    Gemini (más confiable que parsear texto libre con regex). Lanza
    ErrorIA con el detalle exacto si algo falla.
    """
    api_key = _obtener_api_key()

    contexto_perfil = (
        f"Años de experiencia: {perfil.get('anos_experiencia', 0)}\n"
        f"Nivel: {perfil.get('seniority', '')}\n"
        f"Stack principal: {perfil.get('stack_principal', '')}\n"
        f"Logros y experiencia: {perfil.get('logros_y_experiencia', '')}"
    )
    prompt = (
        "Compara el perfil del candidato contra la oferta laboral. Da un score de 0 "
        "a 100 de qué tan buen match es, y una explicación breve (2 a 3 líneas) de "
        "por qué, mencionando fortalezas y posibles brechas (ej. años de experiencia "
        "insuficientes, tecnologías del stack que la oferta pide y el candidato no "
        "menciona).\n\n"
        f"Perfil del candidato:\n{contexto_perfil}\n\n"
        f"Oferta laboral:\n{texto_oferta[:LIMITE_CARACTERES_CONTEXTO]}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "score": {"type": "INTEGER"},
                    "explicacion": {"type": "STRING"},
                },
                "required": ["score", "explicacion"],
            },
        },
    }
    url = URL_API.format(modelo=MODELO)

    try:
        respuesta = requests.post(
            url, params={"key": api_key}, json=payload, timeout=TIMEOUT_SEGUNDOS
        )
    except requests.exceptions.Timeout:
        raise ErrorIA(f"Gemini no respondió en {TIMEOUT_SEGUNDOS}s.")
    except requests.exceptions.ConnectionError as e:
        raise ErrorIA(f"Se perdió la conexión con Gemini: {e}")

    if respuesta.status_code != 200:
        raise ErrorIA(f"Gemini devolvió código {respuesta.status_code}: {respuesta.text[:200]}")

    cuerpo = respuesta.json()
    try:
        texto_generado = cuerpo["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise ErrorIA(f"Gemini respondió sin contenido generado: {cuerpo}")

    try:
        resultado = json.loads(texto_generado)
    except json.JSONDecodeError:
        raise ErrorIA(f"Gemini no devolvió JSON válido: {texto_generado[:200]}")

    if "score" not in resultado or "explicacion" not in resultado:
        raise ErrorIA(f"La respuesta de Gemini no trae score/explicacion: {resultado}")

    return {"score": int(resultado["score"]), "explicacion": str(resultado["explicacion"])}
```

- [ ] **Step 3: Verificar sintaxis**

Run: `cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate && python3 -c "import ast; ast.parse(open('core/motor_ia.py').read()); print('sintaxis OK')"`
Expected: `sintaxis OK`

- [ ] **Step 4: Prueba real contra un mismatch obvio**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
export GEMINI_API_KEY=$(cat /home/ale/.gemini_key)
python3 -c "
from core.motor_ia import analizar_match

perfil_junior_python = {
    'anos_experiencia': 3,
    'seniority': 'Semi Senior',
    'stack_principal': 'Python, Django, FastAPI, AWS',
    'logros_y_experiencia': '',
}
oferta_java_senior = (
    'Se busca Desarrollador Senior Java con 8+ años de experiencia en Spring Boot, '
    'microservicios y Kubernetes. Excluyente experiencia liderando equipos.'
)
resultado = analizar_match(oferta_java_senior, perfil_junior_python)
print('score:', resultado['score'])
print('explicacion:', resultado['explicacion'])
assert isinstance(resultado['score'], int)
assert 0 <= resultado['score'] <= 100
assert resultado['score'] < 50, 'esperaba un score bajo para un mismatch obvio de stack y seniority'
assert resultado['explicacion'].strip()
print('OK: mismatch obvio da score bajo')
"
```
Expected: imprime el score (debería ser bajo, ~20-40) y la explicación, termina con `OK: mismatch obvio da score bajo`.

- [ ] **Step 5: Prueba real contra un buen match**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
export GEMINI_API_KEY=$(cat /home/ale/.gemini_key)
python3 -c "
from core.motor_ia import analizar_match

perfil = {
    'anos_experiencia': 3,
    'seniority': 'Semi Senior',
    'stack_principal': 'Python, Django, FastAPI, AWS, Docker',
    'logros_y_experiencia': 'Desplegue APIs REST en produccion con Django.',
}
oferta = (
    'Se busca Desarrollador Python con experiencia en Django o FastAPI, '
    'conocimientos de AWS y Docker. 2 a 4 años de experiencia.'
)
resultado = analizar_match(oferta, perfil)
print('score:', resultado['score'])
print('explicacion:', resultado['explicacion'])
assert resultado['score'] >= 60, 'esperaba un score alto para un match razonable'
print('OK: buen match da score alto')
"
```
Expected: imprime el score (debería ser alto, ~70-95) y termina con `OK: buen match da score alto`.

- [ ] **Step 6: Commit**

```bash
cd /home/ale/gestor_cv_pro/huntjob_chile
git add core/motor_ia.py
git commit -m "feat: analizar_match en motor_ia.py, respuesta JSON estructurada de Gemini"
```

---

### Task 2: Botón "Analizar match" por tarjeta en Buscador de Vacantes

**Files:**
- Modify: `app.py` (import de `analizar_match` y `ErrorScraping` ya están importados; sección "Buscador de Vacantes", líneas ~212-260 al momento de escribir este plan)

**Interfaces:**
- Consumes: `analizar_match(texto_oferta: str, perfil: dict) -> dict` de Task 1; `extraer_texto_url(url: str) -> str` y `ErrorScraping` (ya importados en `app.py`); `cargar_perfil()` (ya importado).

- [ ] **Step 1: Agregar el import de analizar_match**

En `app.py`, reemplazar:

```python
from core.motor_ia import generar_texto, ErrorIA
```

por:

```python
from core.motor_ia import generar_texto, analizar_match, ErrorIA
```

- [ ] **Step 2: Reemplazar la sección "Buscador de Vacantes" completa**

Reemplazar todo el bloque de `app.py` desde `elif seccion == "Buscador de Vacantes":` hasta el `st.link_button(...)` final de esa sección (justo antes del comentario `# SECCIÓN 3: MI PERFIL`) por:

```python
elif seccion == "Buscador de Vacantes":
    st.subheader("Búsqueda de vacantes reales")

    nombres_portales = [portal["nombre"] for portal in PORTALES.values()]
    id_por_nombre = {portal["nombre"]: portal_id for portal_id, portal in PORTALES.items()}

    if "resultados_busqueda" not in st.session_state:
        st.session_state.resultados_busqueda = []
    if "errores_busqueda" not in st.session_state:
        st.session_state.errores_busqueda = []
    if "matches" not in st.session_state:
        st.session_state.matches = {}

    columna_filtros, columna_resultados = st.columns([1, 3])

    with columna_filtros:
        with st.container(border=True):
            palabra_clave = st.text_input("Palabra clave", value="Python")
            cantidad_paginas = st.slider("Páginas a recorrer", min_value=1, max_value=5, value=1)
            portales_elegidos = st.pills(
                "Portales",
                nombres_portales,
                selection_mode="multi",
                default=nombres_portales,
            )
            portales_marcados = [id_por_nombre[nombre] for nombre in portales_elegidos]
            buscar = st.button("Buscar ofertas", icon=":material/search:", type="primary")

    if buscar:
        if not portales_marcados:
            st.error("Marca al menos un portal para buscar.", icon=":material/error:")
            st.stop()

        with st.spinner(f"Consultando {len(portales_marcados)} portal(es) para '{palabra_clave}'..."):
            resultados, errores = buscar_en_todos(palabra_clave, cantidad_paginas, portales_marcados)

        st.session_state.resultados_busqueda = resultados
        st.session_state.errores_busqueda = errores
        st.session_state.matches = {}

    with columna_resultados:
        for error in st.session_state.errores_busqueda:
            st.warning(f"No se pudo buscar en {error}", icon=":material/warning:")

        if not st.session_state.resultados_busqueda:
            if buscar:
                st.info("No se encontraron ofertas para esa palabra clave en los portales seleccionados.")
        else:
            st.success(f"Se encontraron {len(st.session_state.resultados_busqueda)} vacantes.", icon=":material/check_circle:")
            perfil_para_match = cargar_perfil()

            for oferta in st.session_state.resultados_busqueda:
                with st.container(border=True):
                    st.markdown(f"#### {oferta['titulo']}")
                    st.caption(f"{oferta['empresa']} — {oferta['ubicacion']}")
                    with st.container(horizontal=True, vertical_alignment="center"):
                        st.badge(oferta["fuente"], icon=":material/travel_explore:", color="gray")
                        if oferta.get("modalidad"):
                            st.badge(oferta["modalidad"], icon=":material/home_work:", color="blue")
                        if oferta.get("publicado"):
                            st.caption(oferta["publicado"])
                    if oferta["link"]:
                        st.link_button("Ver oferta", oferta["link"], icon=":material/open_in_new:")

                    match = st.session_state.matches.get(oferta["link"])
                    if match:
                        color_score = "green" if match["score"] >= 70 else "yellow" if match["score"] >= 40 else "red"
                        st.badge(f"Match: {match['score']}/100", icon=":material/insights:", color=color_score)
                        st.caption(match["explicacion"])
                    elif oferta["link"] and st.button(
                        "Analizar match", icon=":material/insights:", key=f"match_{oferta['link']}"
                    ):
                        with st.spinner("Analizando match con tu perfil..."):
                            try:
                                texto_oferta = extraer_texto_url(oferta["link"])
                                st.session_state.matches[oferta["link"]] = analizar_match(
                                    texto_oferta, perfil_para_match
                                )
                                st.rerun()
                            except ErrorScraping as e:
                                st.error(f"No se pudo leer la oferta: {e}", icon=":material/error:")
                            except ErrorIA as e:
                                st.error(f"Fallo en la capa de IA: {e}", icon=":material/error:")
```

- [ ] **Step 3: Verificar sintaxis**

Run: `cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate && python3 -c "import ast; ast.parse(open('app.py').read()); print('sintaxis OK')"`
Expected: `sintaxis OK`

- [ ] **Step 4: Probar en el navegador**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
export GEMINI_API_KEY=$(cat /home/ale/.gemini_key)
nohup streamlit run app.py --server.headless true --server.port 8501 > /tmp/streamlit_matching_test.log 2>&1 &
disown
sleep 4
curl -s -o /dev/null -w "HTTP:%{http_code}\n" http://localhost:8501
```
Expected: `HTTP:200`. Luego, en el navegador (o vía Playwright):
1. Ir al tab "Buscador de Vacantes", buscar "Python" con al menos un portal marcado.
2. Confirmar que aparece la lista de resultados.
3. Apretar "Analizar match" en una tarjeta — confirmar que aparece un spinner, y luego el badge de score + explicación en esa tarjeta, sin que el resto de la lista desaparezca.
4. Apretar "Analizar match" en OTRA tarjeta distinta — confirmar que la primera tarjeta mantiene su score ya calculado (no se pierde) y la segunda ahora también lo tiene.
5. Detener el servidor: `pkill -f "streamlit run app.py"`

- [ ] **Step 5: Commit**

```bash
cd /home/ale/gestor_cv_pro/huntjob_chile
git add app.py
git commit -m "feat: boton Analizar match por tarjeta en Buscador de Vacantes"
git push origin main
```

---

## Self-Review

**Spec coverage:**
- `analizar_match` con JSON estructurado, usando anos_experiencia/seniority/stack_principal/logros_y_experiencia → Task 1.
- Botón bajo demanda por tarjeta, no automático → Task 2.
- Persistencia de resultados/errores en session_state para que un botón de tarjeta no borre la lista → Task 2, Step 2 (`st.session_state.resultados_busqueda`/`errores_busqueda`).
- Persistencia del match por oferta (`st.session_state.matches` keyed por link) para no re-analizar → Task 2, Step 2.
- Colores por rango de score (verde/amarillo/rojo) → Task 2, Step 2.
- Un error en una tarjeta no rompe las demás → Task 2, Step 2 (try/except dentro del loop, por oferta).
- Fuera de alcance (auto-análisis masivo, ordenar por score, cache entre sesiones, usar logros en prompts de CV/CL) → ninguna tarea lo toca, correcto.

**Placeholder scan:** sin TBD/TODO, código completo en todos los steps.

**Type consistency:** `analizar_match(texto_oferta: str, perfil: dict) -> dict` con keys `score`/`explicacion` se usa igual en Task 1 (definición) y Task 2 (consumo). `st.session_state.matches[oferta["link"]]` guarda exactamente ese dict.
