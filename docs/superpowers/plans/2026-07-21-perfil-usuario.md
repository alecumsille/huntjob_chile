# Perfil de usuario Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar a HuntJob Chile un perfil de usuario persistente y editable (nombre, años de experiencia, seniority, stack, logros), como base para las próximas fases de matching y personalización de CV/CL.

**Architecture:** Un módulo nuevo `core/perfil.py` con dos funciones puras de I/O (`cargar_perfil`/`guardar_perfil`) sobre un YAML local no versionado; un tab nuevo "Mi Perfil" en `app.py` que usa esas funciones; y una integración mínima que reemplaza el nombre hardcodeado "Ale Cumsille" en la Cover Letter por el nombre del perfil.

**Tech Stack:** Python 3.10+, Streamlit, PyYAML (nueva dependencia).

## Global Constraints

- El archivo de perfil (`perfil/mi_perfil.yaml`) contiene datos personales del usuario y NUNCA se commitea — debe quedar cubierto por `.gitignore` antes de que exista el archivo real.
- `cargar_perfil()` nunca lanza excepción por archivo faltante — "sin perfil guardado" es un estado válido, no un error.
- Sin capas de abstracción nuevas más allá de las dos funciones — no hay clases, no hay ORM, es lectura/escritura directa de un dict a YAML.
- Cero emojis en código, UI y mensajes (Material icons sí están bien, ya es el estilo establecido en `app.py`).
- No se toca nada de matching, personalización de prompts más allá del nombre, deduplicación ni chat — eso son fases futuras separadas.

---

### Task 1: Módulo de almacenamiento del perfil

**Files:**
- Create: `core/perfil.py`
- Modify: `requirements.txt`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `cargar_perfil() -> dict` con keys `nombre` (str), `anos_experiencia` (int), `seniority` (str), `stack_principal` (str), `logros_y_experiencia` (str). Devuelve valores por defecto (`""`, `0`, `"Junior"`, `""`, `""`) si `perfil/mi_perfil.yaml` no existe.
- Produces: `guardar_perfil(datos: dict) -> None`. Crea la carpeta `perfil/` si no existe y escribe `datos` como YAML en `perfil/mi_perfil.yaml`.

- [ ] **Step 1: Agregar pyyaml a requirements.txt**

Editar `requirements.txt` para que quede:

```
streamlit
requests
beautifulsoup4
reportlab
pyyaml
```

- [ ] **Step 2: Agregar perfil/ al .gitignore**

Editar `.gitignore` para que quede:

```
__pycache__/
*.pyc
salidas_pdf/
venv/
perfil/
```

- [ ] **Step 3: Instalar pyyaml en el venv del proyecto**

Run: `cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate && pip install pyyaml`
Expected: instala sin errores (agrega `PyYAML` a los paquetes del venv).

- [ ] **Step 4: Escribir core/perfil.py**

```python
"""
Módulo de almacenamiento del perfil de usuario. Persiste en un YAML local
que nunca se commitea (ver .gitignore) — son datos personales. "Sin
perfil guardado" es un estado válido: cargar_perfil() nunca lanza
excepción por archivo faltante, solo devuelve valores por defecto.
"""

import os
import yaml

CARPETA_PERFIL = "perfil"
RUTA_PERFIL = os.path.join(CARPETA_PERFIL, "mi_perfil.yaml")

VALORES_POR_DEFECTO = {
    "nombre": "",
    "anos_experiencia": 0,
    "seniority": "Junior",
    "stack_principal": "",
    "logros_y_experiencia": "",
}

NIVELES_SENIORITY = ["Junior", "Semi Senior", "Senior", "Lead"]


def cargar_perfil() -> dict:
    """
    Lee perfil/mi_perfil.yaml si existe. Si no existe, o si el YAML no
    trae alguno de los campos esperados, completa con VALORES_POR_DEFECTO
    en vez de lanzar una excepción.
    """
    if not os.path.exists(RUTA_PERFIL):
        return dict(VALORES_POR_DEFECTO)

    with open(RUTA_PERFIL, "r", encoding="utf-8") as archivo:
        datos_guardados = yaml.safe_load(archivo) or {}

    perfil = dict(VALORES_POR_DEFECTO)
    perfil.update(datos_guardados)
    return perfil


def guardar_perfil(datos: dict) -> None:
    """
    Escribe datos como YAML en perfil/mi_perfil.yaml, creando la carpeta
    perfil/ si todavía no existe.
    """
    os.makedirs(CARPETA_PERFIL, exist_ok=True)
    with open(RUTA_PERFIL, "w", encoding="utf-8") as archivo:
        yaml.safe_dump(datos, archivo, allow_unicode=True, sort_keys=False)
```

- [ ] **Step 5: Verificar manualmente que cargar_perfil funciona sin archivo**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
rm -f perfil/mi_perfil.yaml
python3 -c "
from core.perfil import cargar_perfil
p = cargar_perfil()
assert p == {'nombre': '', 'anos_experiencia': 0, 'seniority': 'Junior', 'stack_principal': '', 'logros_y_experiencia': ''}, p
print('OK: perfil por defecto sin archivo')
"
```
Expected: imprime `OK: perfil por defecto sin archivo` sin excepciones.

- [ ] **Step 6: Verificar manualmente que guardar_perfil + cargar_perfil hacen round-trip**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
python3 -c "
from core.perfil import guardar_perfil, cargar_perfil

datos = {
    'nombre': 'Ale Cumsille',
    'anos_experiencia': 5,
    'seniority': 'Senior',
    'stack_principal': 'Python, Django, FastAPI, PostgreSQL, Docker',
    'logros_y_experiencia': 'Desplegué GatitoPro en produccion.',
}
guardar_perfil(datos)
recargado = cargar_perfil()
assert recargado == datos, recargado
print('OK: round-trip guardar/cargar perfil')
"
ls perfil/mi_perfil.yaml
```
Expected: imprime `OK: round-trip guardar/cargar perfil` y confirma que `perfil/mi_perfil.yaml` existe.

- [ ] **Step 7: Confirmar que perfil/ queda ignorado por git**

Run: `cd /home/ale/gestor_cv_pro/huntjob_chile && git status --short`
Expected: `perfil/mi_perfil.yaml` NO aparece en la salida (ni como `??` ni como modificado) — si aparece, revisar el Step 2 antes de seguir.

- [ ] **Step 8: Commit**

```bash
cd /home/ale/gestor_cv_pro/huntjob_chile
git add core/perfil.py requirements.txt .gitignore
git commit -m "feat: modulo de almacenamiento del perfil de usuario (perfil/mi_perfil.yaml)"
```

---

### Task 2: Tab "Mi Perfil" en la UI

**Files:**
- Modify: `app.py:17-21` (agregar tercera opción al radio del sidebar)
- Modify: `app.py` (agregar nueva sección al final del archivo, después de la sección "Buscador de Vacantes")

**Interfaces:**
- Consumes: `cargar_perfil() -> dict` y `guardar_perfil(datos: dict) -> None` de `core/perfil.py` (Task 1); `NIVELES_SENIORITY` (list[str]) de `core/perfil.py`.

- [ ] **Step 1: Agregar el import de core.perfil**

En `app.py`, después de la línea `from core.portales import PORTALES, buscar_en_todos`, agregar:

```python
from core.perfil import cargar_perfil, guardar_perfil, NIVELES_SENIORITY
```

- [ ] **Step 2: Agregar "Mi Perfil" como tercera opción del sidebar**

Reemplazar en `app.py`:

```python
with st.sidebar:
    seccion = st.radio(
        "Panel",
        ["Generador por URL", "Buscador de Vacantes"],
    )
    st.caption("HuntJob Chile")
```

por:

```python
with st.sidebar:
    seccion = st.radio(
        "Panel",
        ["Generador por URL", "Buscador de Vacantes", "Mi Perfil"],
    )
    st.caption("HuntJob Chile")
```

- [ ] **Step 3: Agregar la sección "Mi Perfil" al final de app.py**

Al final del archivo (después del `for oferta in resultados:` de la sección "Buscador de Vacantes"), agregar:

```python

# -------------------------------------------------------------
# SECCIÓN 3: MI PERFIL
# -------------------------------------------------------------
elif seccion == "Mi Perfil":
    st.subheader("Mi perfil")
    st.caption(
        "Estos datos van a servir para que la IA compare ofertas contra tu "
        "perfil real y genere CVs/Cover Letters mucho más personalizados "
        "en las próximas versiones. Por ahora, el nombre ya se usa para "
        "firmar la Cover Letter."
    )

    perfil_actual = cargar_perfil()

    with st.form("form_perfil"):
        nombre = st.text_input("Nombre completo", value=perfil_actual["nombre"])
        anos_experiencia = st.number_input(
            "Años de experiencia", min_value=0, max_value=60, value=perfil_actual["anos_experiencia"]
        )
        seniority = st.selectbox(
            "Nivel", NIVELES_SENIORITY, index=NIVELES_SENIORITY.index(perfil_actual["seniority"])
        )
        stack_principal = st.text_input(
            "Stack principal (lenguajes, frameworks, herramientas)",
            value=perfil_actual["stack_principal"],
        )
        logros_y_experiencia = st.text_area(
            "Logros y experiencia (proyectos reales, resultados concretos)",
            value=perfil_actual["logros_y_experiencia"],
            height=200,
        )

        if st.form_submit_button("Guardar perfil", icon=":material/save:", type="primary"):
            guardar_perfil({
                "nombre": nombre,
                "anos_experiencia": anos_experiencia,
                "seniority": seniority,
                "stack_principal": stack_principal,
                "logros_y_experiencia": logros_y_experiencia,
            })
            st.success("Perfil guardado.", icon=":material/check_circle:")
```

- [ ] **Step 4: Verificar sintaxis**

Run: `cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate && python3 -c "import ast; ast.parse(open('app.py').read()); print('sintaxis OK')"`
Expected: `sintaxis OK`

- [ ] **Step 5: Probar el tab en el navegador**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
export GEMINI_API_KEY=$(cat /home/ale/.gemini_key)
nohup streamlit run app.py --server.headless true --server.port 8501 > /tmp/streamlit_perfil_test.log 2>&1 &
sleep 4
curl -s -o /dev/null -w "HTTP:%{http_code}\n" http://localhost:8501
```
Expected: `HTTP:200`. Luego abrir el navegador, ir al tab "Mi Perfil", completar el formulario con datos de prueba, apretar "Guardar perfil", confirmar que aparece "Perfil guardado.", recargar la página y confirmar que los campos siguen con los mismos valores.

- [ ] **Step 6: Detener el servidor de prueba**

Run: `pkill -f "streamlit run app.py"`

- [ ] **Step 7: Commit**

```bash
cd /home/ale/gestor_cv_pro/huntjob_chile
git add app.py
git commit -m "feat: tab Mi Perfil con formulario editable"
```

---

### Task 3: Usar el nombre del perfil en la Cover Letter + README

**Files:**
- Modify: `app.py:83-96` (sección "Generador por URL", prompt de Cover Letter y nombres de archivo)
- Modify: `README.md`

**Interfaces:**
- Consumes: `cargar_perfil() -> dict` de `core/perfil.py` (Task 1), ya importado en Task 2.

- [ ] **Step 1: Cargar el perfil al entrar a la sección "Generador por URL"**

En `app.py`, dentro del bloque `if seccion == "Generador por URL":`, justo después de `st.subheader("Generación de CV y Cover Letter desde una oferta puntual")`, agregar:

```python
    perfil = cargar_perfil()
    if not perfil["nombre"]:
        st.warning(
            "No completaste tu perfil todavía — los documentos se van a generar sin firma. "
            "Anda al tab \"Mi Perfil\" para completarlo.",
            icon=":material/warning:",
        )
```

- [ ] **Step 2: Reemplazar el nombre hardcodeado en el prompt de la Cover Letter**

Reemplazar en `app.py`:

```python
                    prompt_cover = (
                        f"Actúa como desarrollador senior en Python. Escribe una Cover Letter directa y sin rodeos "
                        f"para {puesto_objetivo} en {mercado_destino}. Firma con el nombre Ale Cumsille."
                    )
```

por:

```python
                    nombre_firma = perfil["nombre"] or "Candidato/a"
                    prompt_cover = (
                        f"Actúa como desarrollador senior en Python. Escribe una Cover Letter directa y sin rodeos "
                        f"para {puesto_objetivo} en {mercado_destino}. Firma con el nombre {nombre_firma}."
                    )
```

- [ ] **Step 3: Reemplazar el nombre hardcodeado en los nombres de archivo del PDF**

Reemplazar en `app.py`:

```python
            cargo_limpio = sanear_nombre_archivo(puesto_objetivo)
            ruta_cv = os.path.join(CARPETA_SALIDA, f"CV_Ale_Cumsille_{cargo_limpio}.pdf")
            ruta_cl = os.path.join(CARPETA_SALIDA, f"CoverLetter_Ale_Cumsille_{cargo_limpio}.pdf")
```

por:

```python
            cargo_limpio = sanear_nombre_archivo(puesto_objetivo)
            nombre_archivo = sanear_nombre_archivo(perfil["nombre"] or "candidato")
            ruta_cv = os.path.join(CARPETA_SALIDA, f"CV_{nombre_archivo}_{cargo_limpio}.pdf")
            ruta_cl = os.path.join(CARPETA_SALIDA, f"CoverLetter_{nombre_archivo}_{cargo_limpio}.pdf")
```

- [ ] **Step 4: Verificar sintaxis**

Run: `cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate && python3 -c "import ast; ast.parse(open('app.py').read()); print('sintaxis OK')"`
Expected: `sintaxis OK`

- [ ] **Step 5: Prueba end-to-end real: perfil + generación de Cover Letter**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
export GEMINI_API_KEY=$(cat /home/ale/.gemini_key)
python3 -c "
from core.perfil import guardar_perfil
guardar_perfil({
    'nombre': 'Alejandro Cumsille',
    'anos_experiencia': 5,
    'seniority': 'Senior',
    'stack_principal': 'Python, Django, FastAPI, PostgreSQL, Docker',
    'logros_y_experiencia': 'Desplegue GatitoPro en produccion, arme el ERP de Nimarco.',
})
from core.scraper_web import extraer_texto_url
from core.motor_ia import generar_texto
from core.perfil import cargar_perfil

perfil = cargar_perfil()
texto = extraer_texto_url('https://www.computrabajo.cl/ofertas-de-trabajo/oferta-de-trabajo-de-desarrollador-python-django-en-santiago-las-condes-F44A87ACC62FF56C61373E686DCF3405')
nombre_firma = perfil['nombre'] or 'Candidato/a'
prompt_cover = f'Actua como desarrollador senior en Python. Escribe una Cover Letter directa y sin rodeos para Desarrollador Python Django en Chile. Firma con el nombre {nombre_firma}.'
cover = generar_texto(prompt_cover, texto)
assert 'Alejandro Cumsille' in cover, cover
print('OK: la Cover Letter firma con el nombre del perfil')
"
```
Expected: `OK: la Cover Letter firma con el nombre del perfil`

- [ ] **Step 6: Actualizar README.md**

En la sección `## Estructura` de `README.md`, reemplazar:

```
├── core/
│   ├── scraper_web.py      # Extracción de oferta puntual + búsqueda por portal
│   ├── portales.py         # Dispatcher multi-portal (registro + búsqueda agregada)
│   ├── motor_ia.py         # Generación de texto vía Gemini (Google AI)
│   └── generador_pdf.py    # Compilación de CV / Cover Letter en PDF
```

por:

```
├── core/
│   ├── scraper_web.py      # Extracción de oferta puntual + búsqueda por portal
│   ├── portales.py         # Dispatcher multi-portal (registro + búsqueda agregada)
│   ├── motor_ia.py         # Generación de texto vía Gemini (Google AI)
│   ├── generador_pdf.py    # Compilación de CV / Cover Letter en PDF
│   └── perfil.py           # Perfil de usuario (perfil/mi_perfil.yaml, no versionado)
```

Y agregar al final del archivo, antes de `## Roadmap`, una sección nueva:

```markdown
## Mi Perfil

Tab en la app donde se completa un perfil real (nombre, años de experiencia,
seniority, stack principal, logros) que se guarda localmente en
`perfil/mi_perfil.yaml` (no se commitea, es información personal). Por ahora
solo se usa para firmar la Cover Letter con tu nombre real; las próximas
fases lo van a usar también para calcular qué tan buen fit es cada oferta
encontrada y para personalizar mucho más el contenido generado.
```

- [ ] **Step 7: Commit**

```bash
cd /home/ale/gestor_cv_pro/huntjob_chile
git add app.py README.md
git commit -m "feat: usar el nombre del perfil en la Cover Letter y los PDF generados"
git push origin main
```

---

## Self-Review

**Spec coverage:**
- Campos del perfil (nombre, años, seniority, stack, logros) → Task 1 (`VALORES_POR_DEFECTO`) y Task 2 (formulario).
- Almacenamiento en `perfil/mi_perfil.yaml`, gitignored, pyyaml → Task 1.
- UI: tab "Mi Perfil" con formulario y botón guardar → Task 2.
- Integración: nombre reemplaza el hardcodeado en la Cover Letter → Task 3.
- Fuera de alcance (matching, personalización de prompts más allá del nombre, dedup, chat) → no aparece ninguna tarea que los toque, correcto.
- Testing del spec (guardar+recargar, `.gitignore` cubre el archivo, Cover Letter firma con el nombre real, caso sin perfil no crashea) → Steps 5-6 de Task 1, Step 5 de Task 2, Step 5 de Task 3.

**Placeholder scan:** sin TBD/TODO, todos los steps tienen código completo.

**Type consistency:** `cargar_perfil() -> dict` y `guardar_perfil(datos: dict) -> None` se usan con las mismas keys (`nombre`, `anos_experiencia`, `seniority`, `stack_principal`, `logros_y_experiencia`) en Task 1, 2 y 3. `NIVELES_SENIORITY` se define en Task 1 y se consume en Task 2 sin cambios de nombre.
