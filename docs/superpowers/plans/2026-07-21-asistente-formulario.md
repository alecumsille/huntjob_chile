# Asistente de respuestas para formularios Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nuevo tab "Preguntas de Postulación" donde el usuario pega una pregunta del formulario real de una postulación (con alternativas opcionales) y recibe una respuesta sugerida basada en su perfil, lista para copiar manualmente.

**Architecture:** Una función nueva en `core/motor_ia.py` (`sugerir_respuesta`) que usa el mismo mecanismo de JSON estructurado de Gemini que ya usa `analizar_match` — cuando hay alternativas, restringe la respuesta a un `enum` exacto de esas alternativas (verificado en vivo: Gemini nunca inventa una opción fuera de la lista dada). Un nuevo tab en `app.py` con un formulario simple.

**Tech Stack:** Python 3.10+, Streamlit, Gemini API (`generationConfig.responseSchema` con `enum`, ya verificado en vivo).

## Global Constraints

- `sugerir_respuesta` reutiliza `_obtener_api_key()`, `URL_API`, `MODELO`, `TIMEOUT_SEGUNDOS` ya existentes en `core/motor_ia.py` — no se duplican.
- La app NUNCA completa ni envía un formulario real — solo sugiere texto para que el usuario lo copie manualmente. No se agrega ninguna automatización de navegador en este plan.
- Con alternativas dadas, la respuesta debe ser textualmente una de esas alternativas (uso de `enum` en el schema) — nunca una paráfrasis o algo fuera de la lista.
- Cero emojis en código, UI y mensajes.
- No se agregan campos nuevos al perfil — se reutilizan `anos_experiencia`, `seniority`, `stack_principal`, `logros_y_experiencia`, igual que `analizar_match`.
- No se guarda historial de preguntas/respuestas entre sesiones.

---

### Task 1: `sugerir_respuesta` en core/motor_ia.py

**Files:**
- Modify: `core/motor_ia.py` (agregar función nueva al final del archivo, después de `analizar_match`)

**Interfaces:**
- Consumes: `_obtener_api_key()`, `URL_API`, `MODELO`, `TIMEOUT_SEGUNDOS`, `ErrorIA` (ya existen en el mismo archivo).
- Produces: `sugerir_respuesta(pregunta: str, perfil: dict, opciones: list[str] | None = None) -> dict` con keys `respuesta` (str) y `justificacion` (str). Lanza `ErrorIA` en cualquier fallo.

- [ ] **Step 1: Escribir sugerir_respuesta**

Al final de `core/motor_ia.py`, agregar:

```python


def sugerir_respuesta(pregunta: str, perfil: dict, opciones: list[str] | None = None) -> dict:
    """
    Sugiere una respuesta para una pregunta de formulario de postulación,
    basada en el perfil del usuario. Si se dan opciones (pregunta de
    opción múltiple), la respuesta queda restringida por schema a ser
    textualmente una de esas opciones — Gemini nunca puede inventar una
    alternativa que no esté en la lista. Lanza ErrorIA con el detalle
    exacto si algo falla.
    """
    api_key = _obtener_api_key()

    contexto_perfil = (
        f"Años de experiencia: {perfil.get('anos_experiencia', 0)}\n"
        f"Nivel: {perfil.get('seniority', '')}\n"
        f"Stack principal: {perfil.get('stack_principal', '')}\n"
        f"Logros y experiencia: {perfil.get('logros_y_experiencia', '')}"
    )

    propiedad_respuesta = {"type": "STRING"}
    instruccion_opciones = ""
    if opciones:
        propiedad_respuesta["enum"] = opciones
        instruccion_opciones = (
            f" Debes elegir EXACTAMENTE una de estas alternativas, tal como están "
            f"escritas: {', '.join(opciones)}."
        )

    prompt = (
        "Sos un candidato respondiendo una pregunta de un formulario de postulación "
        "laboral, usando tu perfil real como base. Da una respuesta corta y directa, "
        f"lista para copiar en el formulario, y una justificación breve (1 a 2 "
        f"líneas).{instruccion_opciones}\n\n"
        f"Perfil del candidato:\n{contexto_perfil}\n\n"
        f"Pregunta del formulario:\n{pregunta}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "respuesta": propiedad_respuesta,
                    "justificacion": {"type": "STRING"},
                },
                "required": ["respuesta", "justificacion"],
            },
        },
    }
    url = URL_API.format(modelo=MODELO)

    try:
        respuesta_http = requests.post(
            url, params={"key": api_key}, json=payload, timeout=TIMEOUT_SEGUNDOS
        )
    except requests.exceptions.Timeout:
        raise ErrorIA(f"Gemini no respondió en {TIMEOUT_SEGUNDOS}s.")
    except requests.exceptions.ConnectionError as e:
        raise ErrorIA(f"Se perdió la conexión con Gemini: {e}")

    if respuesta_http.status_code != 200:
        raise ErrorIA(f"Gemini devolvió código {respuesta_http.status_code}: {respuesta_http.text[:200]}")

    cuerpo = respuesta_http.json()
    try:
        texto_generado = cuerpo["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise ErrorIA(f"Gemini respondió sin contenido generado: {cuerpo}")

    try:
        resultado = json.loads(texto_generado)
    except json.JSONDecodeError:
        raise ErrorIA(f"Gemini no devolvió JSON válido: {texto_generado[:200]}")

    if "respuesta" not in resultado or "justificacion" not in resultado:
        raise ErrorIA(f"La respuesta de Gemini no trae respuesta/justificacion: {resultado}")

    return {"respuesta": str(resultado["respuesta"]), "justificacion": str(resultado["justificacion"])}
```

- [ ] **Step 2: Verificar sintaxis**

Run: `cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate && python3 -c "import ast; ast.parse(open('core/motor_ia.py').read()); print('sintaxis OK')"`
Expected: `sintaxis OK`

- [ ] **Step 3: Prueba real con alternativas (opción múltiple)**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
export GEMINI_API_KEY=$(cat /home/ale/.gemini_key)
python3 -c "
from core.motor_ia import sugerir_respuesta

perfil = {
    'anos_experiencia': 3,
    'seniority': 'Semi Senior',
    'stack_principal': 'Python, Django, FastAPI',
    'logros_y_experiencia': 'Trabaja mejor de forma remota, vive en Santiago.',
}
opciones = ['Sí', 'No', 'Híbrido']
resultado = sugerir_respuesta(
    '¿Tienes disponibilidad para trabajar de forma presencial en Las Condes?',
    perfil,
    opciones=opciones,
)
print('respuesta:', repr(resultado['respuesta']))
print('justificacion:', resultado['justificacion'])
assert resultado['respuesta'] in opciones, f\"la respuesta '{resultado['respuesta']}' no esta en las opciones dadas\"
assert resultado['justificacion'].strip()
print('OK: la respuesta es exactamente una de las alternativas dadas')
"
```
Expected: imprime la respuesta (debe ser exactamente "Sí", "No" o "Híbrido") y termina con `OK: la respuesta es exactamente una de las alternativas dadas`.

- [ ] **Step 4: Prueba real sin alternativas (respuesta libre)**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
export GEMINI_API_KEY=$(cat /home/ale/.gemini_key)
python3 -c "
from core.motor_ia import sugerir_respuesta

perfil = {
    'anos_experiencia': 3,
    'seniority': 'Semi Senior',
    'stack_principal': 'Python, Django, FastAPI, AWS',
    'logros_y_experiencia': 'Desplegue APIs REST en produccion con Django.',
}
resultado = sugerir_respuesta('¿Por qué te interesa este puesto?', perfil)
print('respuesta:', resultado['respuesta'])
print('justificacion:', resultado['justificacion'])
assert resultado['respuesta'].strip()
assert resultado['justificacion'].strip()
print('OK: respuesta libre no vacia')
"
```
Expected: imprime una respuesta razonable y termina con `OK: respuesta libre no vacia`.

- [ ] **Step 5: Commit**

```bash
cd /home/ale/gestor_cv_pro/huntjob_chile
git add core/motor_ia.py
git commit -m "feat: sugerir_respuesta en motor_ia.py, con enum para preguntas de opcion multiple"
```

---

### Task 2: Tab "Preguntas de Postulación" en app.py

**Files:**
- Modify: `app.py:7` (agregar `sugerir_respuesta` al import de `core.motor_ia`)
- Modify: `app.py:86-91` (agregar cuarta opción al sidebar radio)
- Modify: `app.py` (agregar nueva sección al final del archivo, después de la sección "Mi Perfil")

**Interfaces:**
- Consumes: `sugerir_respuesta(pregunta: str, perfil: dict, opciones: list[str] | None = None) -> dict` de Task 1; `cargar_perfil()` (ya importado); `ErrorIA` (ya importado).

- [ ] **Step 1: Agregar el import de sugerir_respuesta**

En `app.py`, reemplazar:

```python
from core.motor_ia import generar_texto, analizar_match, ErrorIA
```

por:

```python
from core.motor_ia import generar_texto, analizar_match, sugerir_respuesta, ErrorIA
```

- [ ] **Step 2: Agregar la cuarta opción al sidebar**

En `app.py`, reemplazar:

```python
with st.sidebar:
    seccion = st.radio(
        "Panel",
        ["Generador por URL", "Buscador de Vacantes", "Mi Perfil"],
    )
    st.caption("HuntJob Chile")
```

por:

```python
with st.sidebar:
    seccion = st.radio(
        "Panel",
        ["Generador por URL", "Buscador de Vacantes", "Mi Perfil", "Preguntas de Postulación"],
    )
    st.caption("HuntJob Chile")
```

- [ ] **Step 3: Agregar la sección al final de app.py**

Al final del archivo (después del `st.success("Perfil guardado.", ...)` que cierra la sección "Mi Perfil"), agregar:

```python

# -------------------------------------------------------------
# SECCIÓN 4: PREGUNTAS DE POSTULACIÓN
# -------------------------------------------------------------
elif seccion == "Preguntas de Postulación":
    st.subheader("Asistente de respuestas para formularios de postulación")
    st.caption(
        "Pegá la pregunta tal cual aparece en el formulario real (y las alternativas, "
        "si es de opción múltiple). La respuesta sugerida es para copiar manualmente — "
        "la app nunca completa ni envía nada en un formulario real."
    )

    with st.container(border=True):
        pregunta = st.text_area("Pregunta del formulario")
        opciones_texto = st.text_input(
            "Alternativas (separadas por coma, dejar vacío si es respuesta libre)"
        )

        if st.button("Sugerir respuesta", icon=":material/lightbulb:", type="primary"):
            if not pregunta.strip():
                st.error("Pegá la pregunta del formulario primero.", icon=":material/error:")
                st.stop()

            opciones = (
                [opcion.strip() for opcion in opciones_texto.split(",") if opcion.strip()]
                if opciones_texto.strip()
                else None
            )

            with st.spinner("Pensando la mejor respuesta..."):
                try:
                    perfil_para_pregunta = cargar_perfil()
                    resultado = sugerir_respuesta(pregunta, perfil_para_pregunta, opciones=opciones)
                except ErrorIA as e:
                    st.error(f"Fallo en la capa de IA: {e}", icon=":material/error:")
                    st.stop()

            st.success("Respuesta sugerida", icon=":material/check_circle:")
            st.text_area("Respuesta (copiá esto al formulario real)", value=resultado["respuesta"], height=100)
            st.caption(resultado["justificacion"])
```

- [ ] **Step 4: Verificar sintaxis**

Run: `cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate && python3 -c "import ast; ast.parse(open('app.py').read()); print('sintaxis OK')"`
Expected: `sintaxis OK`

- [ ] **Step 5: Probar en el navegador (opción múltiple y respuesta libre)**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
export GEMINI_API_KEY=$(cat /home/ale/.gemini_key)
nohup streamlit run app.py --server.headless true --server.port 8501 > /tmp/streamlit_formulario_test.log 2>&1 &
disown
sleep 4
curl -s -o /dev/null -w "HTTP:%{http_code}\n" http://localhost:8501
```
Expected: `HTTP:200`. Luego, vía Playwright o navegador manual:
1. Ir al tab "Preguntas de Postulación".
2. Completar pregunta: "¿Tienes disponibilidad para trabajar de forma presencial en Las Condes?", alternativas: "Sí, No, Híbrido". Apretar "Sugerir respuesta". Confirmar que la respuesta mostrada es EXACTAMENTE "Sí", "No" o "Híbrido" (no una paráfrasis), con justificación.
3. Borrar las alternativas, cambiar la pregunta a "¿Por qué te interesa este puesto?" y volver a apretar "Sugerir respuesta". Confirmar que da una respuesta libre razonable.
4. Detener el servidor: `pkill -f "streamlit run app.py"`

- [ ] **Step 6: Commit y push**

```bash
cd /home/ale/gestor_cv_pro/huntjob_chile
git add app.py
git commit -m "feat: tab Preguntas de Postulacion con sugerencia de respuesta via IA"
git push origin main
```

---

## Self-Review

**Spec coverage:**
- `sugerir_respuesta` con enum para opción múltiple, respuesta libre sin opciones → Task 1.
- Reutiliza los mismos campos de perfil que `analizar_match`, sin agregar campos nuevos → Task 1 (`contexto_perfil` idéntico al de `analizar_match`).
- Tab nuevo, formulario simple (pregunta + alternativas opcionales + botón) → Task 2.
- Nunca completa/envía un formulario real, solo sugiere texto para copiar → Task 2 (caption explícito + `st.text_area` de solo lectura visual para copiar).
- Fuera de alcance (automatización de navegador, extracción automática de preguntas, historial entre sesiones, campos nuevos de perfil) → ninguna tarea lo toca, correcto.
- Testing del spec (enum exacto, respuesta libre no vacía, verificación manual de ambos casos en el navegador) → Task 1 Steps 3-4, Task 2 Step 5.

**Placeholder scan:** sin TBD/TODO, código completo en todos los steps.

**Type consistency:** `sugerir_respuesta(pregunta: str, perfil: dict, opciones: list[str] | None = None) -> dict` con keys `respuesta`/`justificacion` se usa igual en Task 1 (definición) y Task 2 (consumo, `resultado["respuesta"]`/`resultado["justificacion"]`).
