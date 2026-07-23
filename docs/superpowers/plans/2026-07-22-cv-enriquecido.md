# Perfil y CV Enriquecidos — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar formación académica, experiencia laboral estructurada (múltiples trabajos), habilidades blandas, competencias técnicas, idiomas y ciudad al perfil de HuntJob Chile, y hacer que el CV generado muestre esas secciones tal cual las escribió el usuario (literal), dejando a la IA solo la redacción del resumen profesional y el pulido de los bullets de experiencia.

**Architecture:** El perfil (`core/perfil.py`) gana campos estructurados (listas de dicts para experiencia/formación/idiomas, texto multilínea para habilidades/competencias). Un helper puro `construir_secciones_cv()` en `core/generador_pdf.py` arma las 7 secciones del CV como datos (sin tocar reportlab) a partir del perfil + el resumen profesional (IA) + los bullets pulidos (IA); ese mismo helper lo reutilizan tanto el renderer de PDF como el aplanador de texto plano para el historial. `core/motor_ia.py` gana una función que pule bullets de experiencia con `response_schema` (JSON), sin tocar cargo/empresa/fechas. `app.py` reemplaza el form único de "Mi Perfil" por listas editables en `st.session_state` con botones de agregar/quitar.

**Tech Stack:** Python 3.12, Streamlit, ReportLab (PDF), Supabase (Postgres + Python client), Gemini/Groq (generación de texto), pytest (tests nuevos).

## Global Constraints

- Nunca inventar datos: la IA nunca agrega cargos, empresas, fechas, estudios, competencias o herramientas que el usuario no haya cargado — solo puede reordenar/pulir redacción de funciones ya existentes.
- Formación académica, competencias técnicas, habilidades blandas e idiomas se renderizan 100% literales, sin pasar por la IA.
- Experiencia antes que Formación en el orden del CV, siempre (sin lógica condicional por seniority).
- La sección "Idiomas" se omite del PDF si la lista está vacía (no se muestra una sección vacía).
- Migración de datos legados (`stack_principal`, `logros_y_experiencia`) es un fallback de lectura no destructivo, nunca una migración automática que borre datos existentes sin que el usuario la revise.
- La migración de esquema de Supabase (`sql/schema.sql`) la debe correr Alejandro manualmente — la app solo tiene la Anon Key, sin permiso de DDL.

---

## Task 1: Infraestructura de testing

**Files:**
- Modify: `requirements.txt`
- Create: `pytest.ini`
- Create: `tests/__init__.py`

**Interfaces:**
- Produces: comando `pytest` ejecutable desde la raíz del repo, con `core.*` importable desde cualquier test.

- [ ] **Step 1: Agregar pytest a requirements.txt**

Editar `requirements.txt` (contenido actual: `streamlit`, `requests`, `beautifulsoup4`, `reportlab`, `pyyaml`, `supabase`) agregando una línea al final:

```
pytest
```

- [ ] **Step 2: Crear pytest.ini en la raíz del repo**

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 3: Crear tests/__init__.py vacío**

```python
```

- [ ] **Step 4: Instalar pytest y verificar que corre sin tests**

Run: `cd /home/ale/Antigravity/huntjob_chile && source venv/bin/activate && pip install pytest && pytest`
Expected: `no tests ran` (o similar) sin errores de import ni de configuración.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt pytest.ini tests/__init__.py
git commit -m "chore: agrega infraestructura de pytest para el proyecto"
```

---

## Task 2: Modelo de datos del perfil (`core/perfil.py`)

**Files:**
- Modify: `core/perfil.py`
- Test: `tests/test_perfil.py`

**Interfaces:**
- Produces:
  - `VALORES_POR_DEFECTO: dict` con las llaves nuevas: `ciudad`, `experiencia_laboral`, `formacion_academica`, `idiomas`, `habilidades_blandas`, `competencias_tecnicas` (además de las ya existentes).
  - `NIVELES_IDIOMA: list[str]` = `["Básico", "Intermedio", "Avanzado", "Nativo"]`
  - `TIPOS_FORMACION: list[str]` = `["Carrera", "Curso", "Certificación"]`
  - `lineas_no_vacias(texto: str) -> list[str]`
  - `formatear_perfil(perfil: dict) -> str` (reescrita, incluye todos los campos nuevos)
  - `cargar_perfil(contexto_usuario)` ahora aplica migración de legado antes de devolver el perfil.
- Consumes: nada de otras tasks (es la base).

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_perfil.py`:

```python
from core.perfil import (
    VALORES_POR_DEFECTO,
    lineas_no_vacias,
    formatear_perfil,
    _migrar_legado,
)


def test_lineas_no_vacias_descarta_blancos():
    assert lineas_no_vacias("Python\n\n  \nSQL\n") == ["Python", "SQL"]


def test_lineas_no_vacias_texto_vacio():
    assert lineas_no_vacias("") == []
    assert lineas_no_vacias(None) == []


def test_formatear_perfil_incluye_secciones_nuevas():
    perfil = dict(VALORES_POR_DEFECTO)
    perfil.update({
        "ciudad": "Santiago",
        "experiencia_laboral": [{"cargo": "Dev", "empresa": "Acme", "fecha_inicio": "2021", "fecha_fin": "2024", "actualidad": False, "funciones": "Backend\nAPIs"}],
        "formacion_academica": [{"titulo": "Ing. Civil Informática", "institucion": "USACH", "fecha_inicio": "2015", "fecha_fin": "2020", "tipo": "Carrera"}],
        "idiomas": [{"idioma": "Inglés", "nivel": "Avanzado"}],
        "habilidades_blandas": "Trabajo en equipo\nComunicación",
        "competencias_tecnicas": "Python\nDocker",
    })
    texto = formatear_perfil(perfil)
    assert "Santiago" in texto
    assert "Acme" in texto
    assert "USACH" in texto
    assert "Inglés: Avanzado" in texto
    assert "Trabajo en equipo" in texto
    assert "Docker" in texto


def test_migrar_legado_precarga_experiencia_desde_logros():
    perfil = dict(VALORES_POR_DEFECTO)
    perfil["logros_y_experiencia"] = "Lideré migración a microservicios."
    perfil["experiencia_laboral"] = []
    resultado = _migrar_legado(perfil)
    assert len(resultado["experiencia_laboral"]) == 1
    assert resultado["experiencia_laboral"][0]["funciones"] == "Lideré migración a microservicios."
    assert resultado["experiencia_laboral"][0]["cargo"] == ""


def test_migrar_legado_no_pisa_experiencia_existente():
    perfil = dict(VALORES_POR_DEFECTO)
    perfil["logros_y_experiencia"] = "Texto viejo"
    perfil["experiencia_laboral"] = [{"cargo": "Dev", "empresa": "X", "fecha_inicio": "", "fecha_fin": "", "actualidad": False, "funciones": "Ya migrado antes"}]
    resultado = _migrar_legado(perfil)
    assert len(resultado["experiencia_laboral"]) == 1
    assert resultado["experiencia_laboral"][0]["funciones"] == "Ya migrado antes"


def test_migrar_legado_precarga_competencias_desde_stack():
    perfil = dict(VALORES_POR_DEFECTO)
    perfil["stack_principal"] = "Python, FastAPI, PostgreSQL"
    perfil["competencias_tecnicas"] = ""
    resultado = _migrar_legado(perfil)
    assert resultado["competencias_tecnicas"] == "Python, FastAPI, PostgreSQL"
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pytest tests/test_perfil.py -v`
Expected: `ImportError` o `AttributeError` — `lineas_no_vacias` y `_migrar_legado` no existen todavía.

- [ ] **Step 3: Reescribir `core/perfil.py` completo**

```python
"""
Gestión del perfil de usuario. Con cuenta real (Supabase), el perfil
vive en Postgres por user_id (ver core/db.py) — nunca en disco. En
modo invitado (sin cuenta) vive solo en st.session_state, que es
privado por navegador/pestaña y se pierde al cerrar sesión: nunca se
escribe a un archivo compartido en el servidor, que era la fuga de
datos entre visitantes que tenía la versión anterior.

El CV final mezcla dos fuentes: las secciones de este perfil (formación,
competencias, habilidades blandas, idiomas, datos personales) se
renderizan literales en core/generador_pdf.py — la IA nunca las toca.
Solo el resumen profesional y los bullets de experiencia pasan por IA
(ver core/postulacion.py y core/motor_ia.py).
"""

import streamlit as st

VALORES_POR_DEFECTO = {
    "nombre": "",
    "email": "",
    "telefono": "",
    "linkedin": "",
    "ciudad": "",
    "anos_experiencia": 0,
    "seniority": "Junior",
    "experiencia_laboral": [],
    "formacion_academica": [],
    "idiomas": [],
    "habilidades_blandas": "",
    "competencias_tecnicas": "",
    # Legado: ya no se usan en la generación del CV, se mantienen solo
    # como origen de la migración automática de lectura (ver
    # _migrar_legado). Un usuario nuevo nunca los llena.
    "stack_principal": "",
    "logros_y_experiencia": "",
}

NIVELES_SENIORITY = ["Junior", "Semi Senior", "Senior", "Lead"]
NIVELES_IDIOMA = ["Básico", "Intermedio", "Avanzado", "Nativo"]
TIPOS_FORMACION = ["Carrera", "Curso", "Certificación"]


def lineas_no_vacias(texto: str) -> list[str]:
    """
    Convierte un texto multilínea (una idea por línea, como se cargan
    habilidades y competencias en el formulario) en una lista,
    descartando líneas en blanco. Se usa tanto para renderizar el PDF
    como para el fallback de bullets de experiencia en motor_ia.py.
    """
    return [linea.strip() for linea in (texto or "").split("\n") if linea.strip()]


def _migrar_legado(perfil: dict) -> dict:
    """
    Fallback de lectura (no destructivo): si el usuario tiene datos en
    los campos viejos de texto libre pero nada todavía en los campos
    estructurados nuevos, los precarga como una primera entrada editable
    para que no pierda lo que ya había escrito. No modifica los campos
    viejos ni escribe nada en la base — solo transforma el dict en
    memoria antes de devolverlo.
    """
    perfil = dict(perfil)
    if not perfil.get("experiencia_laboral") and perfil.get("logros_y_experiencia"):
        perfil["experiencia_laboral"] = [{
            "cargo": "",
            "empresa": "",
            "fecha_inicio": "",
            "fecha_fin": "",
            "actualidad": False,
            "funciones": perfil["logros_y_experiencia"],
        }]
    if not perfil.get("competencias_tecnicas") and perfil.get("stack_principal"):
        perfil["competencias_tecnicas"] = perfil["stack_principal"]
    return perfil


def cargar_perfil(contexto_usuario: dict | None) -> dict:
    """
    contexto_usuario = {"user_id": ..., "access_token": ...} para una
    cuenta real, o None en modo invitado.
    """
    if contexto_usuario and contexto_usuario.get("user_id"):
        from core.db import obtener_perfil
        perfil = obtener_perfil(contexto_usuario["user_id"], contexto_usuario["access_token"])
    else:
        perfil = dict(VALORES_POR_DEFECTO)
        perfil.update(st.session_state.get("perfil_invitado", {}))
    return _migrar_legado(perfil)


def guardar_perfil(contexto_usuario: dict | None, datos: dict) -> None:
    if contexto_usuario and contexto_usuario.get("user_id"):
        from core.db import guardar_perfil_db
        guardar_perfil_db(contexto_usuario["user_id"], contexto_usuario["access_token"], datos)
        return

    st.session_state["perfil_invitado"] = datos


def formatear_perfil(perfil: dict) -> str:
    """
    Serializa el perfil como texto plano para incluir en prompts de IA.
    Fuente única para motor_ia.py y postulacion.py — evita duplicar el
    formato en varios lugares. Incluye todos los campos, incluso los
    que en el CV final se renderizan literales (formación, idiomas,
    etc.) — la IA los necesita como contexto de lectura para el
    resumen profesional y el análisis de match ATS, aunque no los
    redacte directamente.
    """
    partes = [
        f"Ciudad: {perfil.get('ciudad', '')}",
        f"Años de experiencia: {perfil.get('anos_experiencia', 0)}",
        f"Nivel: {perfil.get('seniority', '')}",
        f"Competencias técnicas: {', '.join(lineas_no_vacias(perfil.get('competencias_tecnicas', '')))}",
        f"Habilidades blandas: {', '.join(lineas_no_vacias(perfil.get('habilidades_blandas', '')))}",
    ]

    experiencia = perfil.get("experiencia_laboral") or []
    if experiencia:
        partes.append("Experiencia laboral:")
        for trabajo in experiencia:
            rango = trabajo.get("fecha_fin") or ("Actualidad" if trabajo.get("actualidad") else "")
            partes.append(
                f"- {trabajo.get('cargo', '')} en {trabajo.get('empresa', '')} "
                f"({trabajo.get('fecha_inicio', '')} - {rango}): {trabajo.get('funciones', '')}"
            )

    formacion = perfil.get("formacion_academica") or []
    if formacion:
        partes.append("Formación académica:")
        for estudio in formacion:
            partes.append(
                f"- {estudio.get('titulo', '')} en {estudio.get('institucion', '')} "
                f"({estudio.get('fecha_inicio', '')} - {estudio.get('fecha_fin', '')})"
            )

    idiomas = perfil.get("idiomas") or []
    if idiomas:
        partes.append(
            "Idiomas: " + ", ".join(f"{i.get('idioma', '')}: {i.get('nivel', '')}" for i in idiomas)
        )

    return "\n".join(partes)
```

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `pytest tests/test_perfil.py -v`
Expected: 6 tests, todos `PASSED`.

- [ ] **Step 5: Verificar sintaxis de todo el proyecto**

Run: `python -c "import core.perfil"`
Expected: sin errores.

- [ ] **Step 6: Commit**

```bash
git add core/perfil.py tests/test_perfil.py
git commit -m "feat(perfil): agrega formación, experiencia estructurada, idiomas, habilidades y migración de legado"
```

---

## Task 3: Migración de esquema de Supabase (`sql/schema.sql`)

**Files:**
- Modify: `sql/schema.sql`

**Interfaces:**
- Consumes: nombres de campos definidos en Task 2 (`ciudad`, `experiencia_laboral`, `formacion_academica`, `idiomas`, `habilidades_blandas`, `competencias_tecnicas`).
- Produces: columnas nuevas en la tabla `perfiles` de Supabase (no automatizable desde la app — requiere que Alejandro lo corra a mano).

- [ ] **Step 1: Agregar las columnas nuevas al final de `sql/schema.sql`**

Agregar (después del bloque `create table if not exists public.perfiles (...)`, como sentencias nuevas — no modificar el `create table` existente para no romper si alguien vuelve a correr el script completo en una base ya poblada):

```sql
-- Migración 2026-07-22: perfil enriquecido (formación, experiencia
-- estructurada, idiomas, habilidades, ciudad). Ver
-- docs/superpowers/specs/2026-07-22-cv-enriquecido-design.md
alter table public.perfiles add column if not exists ciudad text default '';
alter table public.perfiles add column if not exists experiencia_laboral jsonb default '[]';
alter table public.perfiles add column if not exists formacion_academica jsonb default '[]';
alter table public.perfiles add column if not exists idiomas jsonb default '[]';
alter table public.perfiles add column if not exists habilidades_blandas text default '';
alter table public.perfiles add column if not exists competencias_tecnicas text default '';
```

- [ ] **Step 2: Verificar que el archivo sigue siendo válido SQL (revisión visual)**

No hay forma de correr esto sin una base Supabase real — es intencional que sea manual. Confirmar visualmente que las 6 líneas nuevas usan `if not exists` (para poder re-correr el script sin error si ya se aplicó) y que los nombres calzan exactamente con `VALORES_POR_DEFECTO` de `core/perfil.py`.

- [ ] **Step 3: Commit**

```bash
git add sql/schema.sql
git commit -m "feat(db): agrega columnas de perfil enriquecido a la tabla perfiles"
```

- [ ] **Step 4: Avisar a Alejandro que debe correr la migración**

Este paso no es de código: recordar al usuario que antes de probar con una cuenta real (no invitado) debe copiar las 6 líneas nuevas de `sql/schema.sql` en el SQL Editor de su proyecto Supabase y ejecutarlas. Sin esto, `guardar_perfil_db`/`obtener_perfil` funcionan igual (Supabase no rechaza upserts con columnas de más si ya existen, pero sí con columnas que no existen todavía) — así que este paso es bloqueante para probar con cuenta real, no para modo invitado (que vive en `st.session_state`, no en Postgres).

---

## Task 4: Secciones y PDF del CV (`core/generador_pdf.py`)

**Files:**
- Modify: `core/generador_pdf.py`
- Test: `tests/test_generador_pdf.py`

**Interfaces:**
- Consumes: `lineas_no_vacias` de `core.perfil` (Task 2).
- Produces:
  - `construir_secciones_cv(perfil: dict, resumen_profesional: str, bullets_por_trabajo: list[list[str]]) -> list[dict]`
  - `generar_pdf_cv(perfil: dict, resumen_profesional: str, bullets_por_trabajo: list[list[str]], puesto: str, estilo_nombre: str = "Pastel") -> bytes`
  - `generar_pdf(...)` (existente, sin cambios de firma — sigue usándose solo para la Cover Letter).

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_generador_pdf.py`:

```python
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
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pytest tests/test_generador_pdf.py -v`
Expected: `ImportError` — `construir_secciones_cv`, `generar_pdf_cv` y `_formatear_rango_fechas` no existen todavía.

- [ ] **Step 3: Agregar las funciones nuevas a `core/generador_pdf.py`**

Agregar estas funciones e imports (mantener todo lo que ya existe en el archivo — `sanear_nombre_archivo`, `_limpiar_markdown`, `generar_pdf`, constantes de color y `PLANTILLAS_ESTILO` no cambian):

Agregar al import existente:
```python
from core.perfil import lineas_no_vacias
```

Agregar estas funciones nuevas (después de `_limpiar_markdown`, antes de `generar_pdf`):

```python
def _formatear_rango_fechas(fecha_inicio: str, fecha_fin: str, actualidad: bool) -> str:
    """Da formato 'inicio – fin' (o 'inicio – Actualidad') a un rango de fechas, tolerando campos vacíos."""
    if actualidad:
        return f"{fecha_inicio} – Actualidad" if fecha_inicio else "Actualidad"
    if fecha_inicio and fecha_fin:
        return f"{fecha_inicio} – {fecha_fin}"
    return fecha_inicio or fecha_fin or ""


def construir_secciones_cv(perfil: dict, resumen_profesional: str, bullets_por_trabajo: list[list[str]]) -> list[dict]:
    """
    Arma las secciones del CV como datos puros (sin reportlab de por
    medio), en el orden estándar chileno: Perfil Profesional,
    Experiencia Laboral, Formación Académica, Competencias Técnicas,
    Habilidades Blandas, Idiomas. Formación, competencias, habilidades
    e idiomas se arman 100% literales desde el perfil — nunca pasan
    por bullets_por_trabajo ni por ningún texto generado por IA. Una
    sección se omite por completo si no tiene contenido (ej. Idiomas
    si la lista está vacía). La usan tanto generar_pdf_cv() como el
    aplanador de texto plano en core/postulacion.py, para no duplicar
    esta lógica en dos lugares.
    """
    secciones = []

    if resumen_profesional and resumen_profesional.strip():
        secciones.append({"titulo": "Perfil Profesional", "tipo": "parrafo", "contenido": resumen_profesional.strip()})

    experiencia = perfil.get("experiencia_laboral") or []
    if experiencia:
        trabajos = []
        for indice, trabajo in enumerate(experiencia):
            encabezado_partes = [p for p in (trabajo.get("cargo"), trabajo.get("empresa")) if p]
            encabezado = " — ".join(encabezado_partes)
            rango = _formatear_rango_fechas(
                trabajo.get("fecha_inicio", ""), trabajo.get("fecha_fin", ""), trabajo.get("actualidad", False)
            )
            if rango:
                encabezado = f"{encabezado} | {rango}" if encabezado else rango
            if bullets_por_trabajo and indice < len(bullets_por_trabajo) and bullets_por_trabajo[indice]:
                bullets = bullets_por_trabajo[indice]
            else:
                bullets = lineas_no_vacias(trabajo.get("funciones", ""))
            trabajos.append({"encabezado": encabezado, "bullets": bullets})
        secciones.append({"titulo": "Experiencia Laboral", "tipo": "trabajos", "contenido": trabajos})

    formacion = perfil.get("formacion_academica") or []
    if formacion:
        estudios = []
        for estudio in formacion:
            partes = [p for p in (estudio.get("titulo"), estudio.get("institucion")) if p]
            encabezado = " — ".join(partes)
            rango = _formatear_rango_fechas(estudio.get("fecha_inicio", ""), estudio.get("fecha_fin", ""), False)
            if rango:
                encabezado = f"{encabezado} | {rango}" if encabezado else rango
            estudios.append({"encabezado": encabezado, "tipo": estudio.get("tipo", "")})
        secciones.append({"titulo": "Formación Académica", "tipo": "estudios", "contenido": estudios})

    competencias = lineas_no_vacias(perfil.get("competencias_tecnicas", ""))
    if competencias:
        secciones.append({"titulo": "Competencias Técnicas y Manejo de Software", "tipo": "lista", "contenido": competencias})

    habilidades = lineas_no_vacias(perfil.get("habilidades_blandas", ""))
    if habilidades:
        secciones.append({"titulo": "Habilidades Blandas", "tipo": "lista", "contenido": habilidades})

    idiomas = perfil.get("idiomas") or []
    lineas_idiomas = [f"{i.get('idioma', '')}: {i.get('nivel', '')}" for i in idiomas if i.get("idioma")]
    if lineas_idiomas:
        secciones.append({"titulo": "Idiomas", "tipo": "lista", "contenido": lineas_idiomas})

    return secciones


def generar_pdf_cv(
    perfil: dict,
    resumen_profesional: str,
    bullets_por_trabajo: list[list[str]],
    puesto: str,
    estilo_nombre: str = "Pastel",
) -> bytes:
    """
    Compila el CV en PDF a partir de las secciones de construir_secciones_cv().
    A diferencia de generar_pdf() (usado para la Cover Letter, un solo
    bloque de texto libre), acá cada sección tiene su propio layout
    según su tipo: párrafo, lista de trabajos con bullets, lista de
    estudios, o lista simple. Lanza ValueError si no hay ninguna
    sección con contenido, en vez de generar un PDF en blanco.
    """
    secciones = construir_secciones_cv(perfil, resumen_profesional, bullets_por_trabajo)
    if not secciones:
        raise ValueError("No se puede generar el CV: no hay ninguna sección con contenido.")

    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
    )
    estilos = getSampleStyleSheet()
    paleta_pdf = PLANTILLAS_ESTILO.get(estilo_nombre, PLANTILLAS_ESTILO["Pastel"])

    estilo_nombre_p = ParagraphStyle(
        "NombreCandidato", parent=estilos["Heading1"], fontSize=22, spaceAfter=2, textColor=paleta_pdf["nombre"]
    )
    estilo_contacto = ParagraphStyle(
        "Contacto", parent=estilos["Normal"], fontSize=9, spaceAfter=8, textColor=COLOR_CONTACTO
    )
    estilo_subtitulo = ParagraphStyle(
        "Subtitulo", parent=estilos["Heading2"], fontSize=13, spaceBefore=10, spaceAfter=8, textColor=paleta_pdf["subtitulo"]
    )
    estilo_cuerpo = ParagraphStyle(
        "CuerpoDocumento", parent=estilos["Normal"], fontSize=10.5, leading=15, spaceAfter=6, alignment=4, textColor=COLOR_CUERPO
    )
    estilo_encabezado_trabajo = ParagraphStyle(
        "EncabezadoTrabajo", parent=estilos["Normal"], fontSize=10.5, leading=14, spaceBefore=6, spaceAfter=2,
        textColor=COLOR_CUERPO, fontName="Helvetica-Bold",
    )
    estilo_bullet = ParagraphStyle(
        "Bullet", parent=estilos["Normal"], fontSize=10, leading=14, spaceAfter=3, leftIndent=12, textColor=COLOR_CUERPO
    )

    nombre = perfil.get("nombre") or "Candidato/a"
    datos_contacto = [
        dato for dato in (perfil.get("ciudad"), perfil.get("email"), perfil.get("telefono"), perfil.get("linkedin")) if dato
    ]

    elementos = [Paragraph(escape(nombre), estilo_nombre_p)]
    if datos_contacto:
        elementos.append(Paragraph(escape("  ·  ".join(datos_contacto)), estilo_contacto))
    else:
        elementos.append(Spacer(1, 6))
    elementos.append(HRFlowable(width="100%", thickness=1, color=paleta_pdf["linea"], spaceAfter=4))
    elementos.append(Paragraph(escape(f"CV Profesional — {puesto}"), estilo_subtitulo))

    for seccion in secciones:
        elementos.append(Paragraph(escape(seccion["titulo"]), estilo_subtitulo))
        if seccion["tipo"] == "parrafo":
            for linea in seccion["contenido"].split("\n"):
                linea_limpia = _limpiar_markdown(linea)
                if linea_limpia:
                    elementos.append(Paragraph(escape(linea_limpia), estilo_cuerpo))
        elif seccion["tipo"] == "trabajos":
            for trabajo in seccion["contenido"]:
                if trabajo["encabezado"]:
                    elementos.append(Paragraph(escape(trabajo["encabezado"]), estilo_encabezado_trabajo))
                for bullet in trabajo["bullets"]:
                    elementos.append(Paragraph(escape(f"• {_limpiar_markdown(bullet)}"), estilo_bullet))
        elif seccion["tipo"] == "estudios":
            for estudio in seccion["contenido"]:
                if estudio["encabezado"]:
                    texto = estudio["encabezado"]
                    if estudio.get("tipo"):
                        texto = f"{texto} ({estudio['tipo']})"
                    elementos.append(Paragraph(escape(texto), estilo_encabezado_trabajo))
        elif seccion["tipo"] == "lista":
            for item in seccion["contenido"]:
                elementos.append(Paragraph(escape(f"• {item}"), estilo_bullet))

    documento.build(elementos)
    return buffer.getvalue()
```

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `pytest tests/test_generador_pdf.py -v`
Expected: 8 tests, todos `PASSED`.

- [ ] **Step 5: Verificar sintaxis**

Run: `python -c "import core.generador_pdf"`
Expected: sin errores.

- [ ] **Step 6: Commit**

```bash
git add core/generador_pdf.py tests/test_generador_pdf.py
git commit -m "feat(pdf): renderiza el CV en 7 secciones literales + resumen/bullets de IA"
```

---

## Task 5: Pulido de bullets de experiencia con IA (`core/motor_ia.py`)

**Files:**
- Modify: `core/motor_ia.py`
- Test: `tests/test_motor_ia.py`

**Interfaces:**
- Consumes: `lineas_no_vacias` de `core.perfil` (Task 2).
- Produces: `pulir_experiencia_laboral(experiencia_laboral: list[dict], puesto_objetivo: str, texto_oferta: str) -> list[list[str]]` — lista paralela a `experiencia_laboral`, nunca lanza excepción (degrada a los bullets literales del usuario ante cualquier falla).

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_motor_ia.py`:

```python
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
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pytest tests/test_motor_ia.py -v`
Expected: `ImportError` — `pulir_experiencia_laboral` no existe todavía.

- [ ] **Step 3: Agregar la función a `core/motor_ia.py`**

Agregar al final del archivo (después de `sugerir_respuesta`):

```python
def pulir_experiencia_laboral(experiencia_laboral: list[dict], puesto_objetivo: str, texto_oferta: str) -> list[list[str]]:
    """
    Por cada trabajo, pide a la IA una versión reordenada/pulida de sus
    'funciones' ya cargadas, priorizando lo relevante para la oferta.
    Nunca inventa funciones nuevas ni recibe de vuelta cargo/empresa/
    fechas — esos campos ni se le piden, solo van como contexto de
    lectura. Devuelve una lista paralela a `experiencia_laboral`: una
    lista de bullets por cada trabajo, en el mismo orden. Ante
    cualquier falla (IA caída, JSON inválido, cantidad de trabajos
    distinta a la esperada), cada trabajo cae de vuelta a sus funciones
    tal cual el usuario las escribió — nunca se pierde información, en
    el peor caso queda sin pulir.
    """
    from core.perfil import lineas_no_vacias

    bullets_originales = [lineas_no_vacias(trabajo.get("funciones", "")) for trabajo in experiencia_laboral]
    trabajos_con_funciones = [
        (indice, trabajo) for indice, trabajo in enumerate(experiencia_laboral) if bullets_originales[indice]
    ]
    if not trabajos_con_funciones:
        return bullets_originales

    bloques = []
    for numero, (indice, trabajo) in enumerate(trabajos_con_funciones, start=1):
        funciones_texto = "\n".join(f"- {f}" for f in bullets_originales[indice])
        bloques.append(f"Trabajo {numero} — {trabajo.get('cargo', '')} en {trabajo.get('empresa', '')}:\n{funciones_texto}")

    prompt = (
        f"Eres un editor de currículums. A continuación hay {len(bloques)} trabajos de la experiencia "
        f"laboral real de un candidato que postula a '{puesto_objetivo}'. Para cada uno, reordena y pule "
        "la redacción de sus funciones ya escritas, dando prioridad a lo más relevante para la oferta de "
        "abajo. NUNCA agregues una función, herramienta o logro que no esté ya en el texto original de "
        "ese trabajo — solo puedes reordenar, resumir o mejorar la redacción de lo que ya está.\n\n"
        "Responde ÚNICAMENTE un objeto JSON con la llave \"bullets_por_trabajo\": una lista de listas de "
        f"strings, en el MISMO ORDEN y con EXACTAMENTE {len(bloques)} elementos (uno por trabajo, en el "
        "orden en que aparecen abajo).\n\n"
        + "\n\n".join(bloques)
        + f"\n\nOferta laboral:\n{texto_oferta[:LIMITE_CARACTERES_CONTEXTO]}"
    )
    schema = {
        "type": "OBJECT",
        "properties": {
            "bullets_por_trabajo": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "STRING"}}},
        },
        "required": ["bullets_por_trabajo"],
    }

    try:
        texto_res = _ejecutar_con_fallback(prompt, response_mime_type="application/json", response_schema=schema)
        resultado = json.loads(texto_res)
        pulido = resultado.get("bullets_por_trabajo", [])
        if len(pulido) != len(bloques):
            raise ValueError("La IA devolvió una cantidad de trabajos distinta a la esperada.")
    except Exception:
        return bullets_originales

    bullets_finales = list(bullets_originales)
    for (indice, _trabajo), bullets_pulidos in zip(trabajos_con_funciones, pulido):
        limpios = [str(b).strip() for b in bullets_pulidos if str(b).strip()]
        bullets_finales[indice] = limpios or bullets_originales[indice]
    return bullets_finales
```

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `pytest tests/test_motor_ia.py -v`
Expected: 5 tests, todos `PASSED`.

- [ ] **Step 5: Verificar sintaxis**

Run: `python -c "import core.motor_ia"`
Expected: sin errores.

- [ ] **Step 6: Commit**

```bash
git add core/motor_ia.py tests/test_motor_ia.py
git commit -m "feat(ia): agrega pulido acotado de bullets de experiencia con degradación a literal"
```

---

## Task 6: Wiring de la generación (`core/postulacion.py`)

**Files:**
- Modify: `core/postulacion.py`
- Test: `tests/test_postulacion.py`

**Interfaces:**
- Consumes:
  - `generar_pdf_cv`, `construir_secciones_cv` de `core.generador_pdf` (Task 4)
  - `pulir_experiencia_laboral` de `core.motor_ia` (Task 5)
- Produces: `generar_documentos(...)` — misma firma externa que hoy, mismo dict de retorno (`cv_bytes`, `cl_bytes`, `nombre_cv`, `nombre_cl`, `cv_texto`, `cover_letter_texto`). No requiere cambios en `app.py` en los call-sites existentes.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_postulacion.py`:

```python
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
```

- [ ] **Step 2: Correr los tests y confirmar que fallan**

Run: `pytest tests/test_postulacion.py -v`
Expected: `ImportError` — `_aplanar_cv_a_texto` no existe todavía, y `pulir_experiencia_laboral` no está importado en `core.postulacion` para poder mockearlo con `patch("core.postulacion.pulir_experiencia_laboral", ...)`.

- [ ] **Step 3: Reescribir `core/postulacion.py` completo**

```python
"""
Genera el CV y la Cover Letter para una oferta puntual. Único lugar
donde vive este prompt — lo usan tanto el "Generador por URL" como el
botón de 1-click desde el buscador, para no mantener el mismo texto
duplicado en dos pantallas.

El CV mezcla dos fuentes: las secciones literales del perfil (datos
personales, formación, competencias, habilidades blandas, idiomas) se
renderizan tal cual las cargó el usuario — ver
core/generador_pdf.py::construir_secciones_cv. La IA solo redacta el
resumen profesional y pule los bullets de experiencia laboral, siempre
sobre los hechos reales que ya están en el perfil.
"""

from core.motor_ia import generar_texto, pulir_experiencia_laboral, ErrorIA
from core.generador_pdf import generar_pdf, generar_pdf_cv, sanear_nombre_archivo, construir_secciones_cv
from core.perfil import formatear_perfil


def generar_documentos(
    texto_oferta: str,
    puesto_objetivo: str,
    mercado_destino: str,
    estilo_pdf: str,
    perfil: dict,
    match: dict | None = None,
) -> dict:
    """
    Genera el CV y la Cover Letter en PDF, en memoria (nunca en disco —
    evita que dos postulaciones simultáneas de usuarios distintos se
    pisen en una carpeta compartida). Si se pasa un `match` (resultado
    de analizar_match), el resumen profesional se redacta apuntando a
    cerrar esas brechas específicas en vez de un texto genérico.
    Devuelve {"cv_bytes", "cl_bytes", "nombre_cv", "nombre_cl", "cv_texto", "cover_letter_texto"}.
    Lanza ErrorIA o ValueError si algo falla.
    """
    contexto_perfil = formatear_perfil(perfil)

    instruccion_brechas = ""
    if match:
        piezas = []
        if match.get("palabras_faltantes"):
            piezas.append("Palabras clave que la oferta pide y hoy no destacan: " + ", ".join(match["palabras_faltantes"]))
        if match.get("debilidades"):
            piezas.append("Brechas detectadas frente a la oferta: " + ", ".join(match["debilidades"]))
        if piezas:
            instruccion_brechas = (
                "\n\nUn análisis ATS previo detectó estas brechas — sin inventar nada que el candidato no "
                "tenga, dale prioridad y visibilidad en el resumen a cualquier experiencia real del perfil "
                "que ayude a cerrarlas:\n- " + "\n- ".join(piezas) + "\n"
            )

    prompt_resumen = (
        f"Redacta ÚNICAMENTE el 'Perfil Profesional' de un Curriculum Vitae en español: un extracto "
        f"potente de 3 a 5 líneas, optimizado para pasar filtros ATS, para el puesto de {puesto_objetivo} "
        f"en {mercado_destino}. Usa exclusivamente la experiencia, formación y competencias reales del "
        f"candidato descritas en su perfil. NUNCA inventes tecnologías, empresas o estudios que no estén "
        f"en el perfil. No agregues título de sección ni explicaciones — responde solo el texto del extracto."
        f"{instruccion_brechas}\n\nPerfil del candidato:\n{contexto_perfil}"
    )
    resumen_profesional = generar_texto(prompt_resumen, texto_oferta)

    bullets_por_trabajo = pulir_experiencia_laboral(perfil.get("experiencia_laboral") or [], puesto_objetivo, texto_oferta)

    nombre_firma = perfil.get("nombre") or "Candidato/a"
    prompt_cover = (
        f"Escribe ÚNICAMENTE el cuerpo de una Cover Letter en español, directa y sin rodeos, "
        f"para el puesto de {puesto_objetivo} en {mercado_destino}. Si el perfil tiene "
        f"logros o experiencia, menciona como máximo uno concreto que calce con esta oferta "
        f"— si no hay logros cargados, escribe sin inventar ninguno. NUNCA indiques que el "
        f"candidato domina o usa una tecnología que no esté textualmente en sus competencias "
        f"técnicas, aunque la oferta la pida — en ese caso, puedes mencionar disposición "
        f"a aprenderla, nunca dominio que no tiene. Firma con el nombre {nombre_firma}. "
        f"No agregues explicaciones ni ningún texto que no sea la carta en sí."
        f"{instruccion_brechas}\n\n"
        f"Perfil del candidato:\n{contexto_perfil}"
    )
    cover_letter_texto = generar_texto(prompt_cover, texto_oferta)

    cargo_limpio = sanear_nombre_archivo(puesto_objetivo)
    nombre_archivo = sanear_nombre_archivo(perfil.get("nombre") or "candidato")

    cv_bytes = generar_pdf_cv(perfil, resumen_profesional, bullets_por_trabajo, puesto_objetivo, estilo_nombre=estilo_pdf)
    cl_bytes = generar_pdf(cover_letter_texto, "Cover Letter", puesto_objetivo, perfil, estilo_nombre=estilo_pdf)

    cv_texto = _aplanar_cv_a_texto(perfil, resumen_profesional, bullets_por_trabajo, puesto_objetivo)

    return {
        "cv_bytes": cv_bytes,
        "cl_bytes": cl_bytes,
        "nombre_cv": f"CV_{nombre_archivo}_{cargo_limpio}.pdf",
        "nombre_cl": f"CoverLetter_{nombre_archivo}_{cargo_limpio}.pdf",
        "cv_texto": cv_texto,
        "cover_letter_texto": cover_letter_texto,
    }


def _aplanar_cv_a_texto(perfil: dict, resumen_profesional: str, bullets_por_trabajo: list[list[str]], puesto_objetivo: str) -> str:
    """
    Versión en texto plano del CV, solo para guardar en el historial de
    postulaciones (core/db.py::guardar_historial) — nunca se muestra en
    pantalla, es un registro de auditoría. Reutiliza
    construir_secciones_cv() para no duplicar la lógica de qué va en
    cada sección.
    """
    secciones = construir_secciones_cv(perfil, resumen_profesional, bullets_por_trabajo)
    lineas = [f"CV Profesional — {puesto_objetivo}", ""]
    for seccion in secciones:
        lineas.append(seccion["titulo"].upper())
        if seccion["tipo"] == "parrafo":
            lineas.append(seccion["contenido"])
        elif seccion["tipo"] == "trabajos":
            for trabajo in seccion["contenido"]:
                if trabajo["encabezado"]:
                    lineas.append(trabajo["encabezado"])
                lineas.extend(f"- {b}" for b in trabajo["bullets"])
        elif seccion["tipo"] == "estudios":
            for estudio in seccion["contenido"]:
                lineas.append(estudio["encabezado"])
        elif seccion["tipo"] == "lista":
            lineas.extend(f"- {item}" for item in seccion["contenido"])
        lineas.append("")
    return "\n".join(lineas)
```

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `pytest tests/test_postulacion.py -v`
Expected: 2 tests, todos `PASSED`.

- [ ] **Step 5: Correr toda la suite junta**

Run: `pytest -v`
Expected: todos los tests de Tasks 2, 4, 5 y 6 en `PASSED` (21 tests en total).

- [ ] **Step 6: Verificar sintaxis**

Run: `python -c "import core.postulacion"`
Expected: sin errores.

- [ ] **Step 7: Commit**

```bash
git add core/postulacion.py tests/test_postulacion.py
git commit -m "refactor(cv): usa resumen+bullets de IA sobre secciones literales del perfil"
```

---

## Task 7: Formulario "Mi Perfil" (`app.py`)

**Files:**
- Modify: `app.py:12` (import) y `app.py:854-914` (sección completa de "Mi Perfil")

**Interfaces:**
- Consumes: `NIVELES_IDIOMA`, `TIPOS_FORMACION`, `VALORES_POR_DEFECTO` de `core.perfil` (Task 2).
- No cambia la firma de `generar_documentos()` — los call-sites en `app.py:572` y `app.py:748` no requieren cambios.

- [ ] **Step 1: Actualizar imports en `app.py`**

Agregar `import copy` junto a los otros imports de la librería estándar en la línea 1 (`import base64`):
```python
import copy
```
(Necesario para `copy.deepcopy(VALORES_POR_DEFECTO)` en el botón "Limpiar campos del perfil" — `VALORES_POR_DEFECTO` contiene listas mutables y una copia superficial las compartiría por referencia entre sesiones, el mismo riesgo que ya se corrigió en `core/perfil.py` y `core/db.py` durante la revisión de la Tarea 2.)

Cambiar la línea 12:
```python
from core.perfil import cargar_perfil, guardar_perfil, NIVELES_SENIORITY
```
por:
```python
from core.perfil import cargar_perfil, guardar_perfil, NIVELES_SENIORITY, NIVELES_IDIOMA, TIPOS_FORMACION, VALORES_POR_DEFECTO
```

- [ ] **Step 2: Reemplazar el bloque completo de "Mi Perfil" (líneas 854-914)**

Reemplazar todo el bloque desde `elif seccion == "Mi Perfil":` hasta el `st.rerun()` final del botón "Limpiar campos del perfil" (justo antes del comentario `# SECCIÓN 5: PREGUNTAS DE POSTULACIÓN`) por:

```python
elif seccion == "Mi Perfil":
    st.subheader("Mi perfil")
    st.caption(
        "Con estos datos la IA compara ofertas con tu perfil y personaliza tu CV y Cover Letter. "
        "Formación, competencias, habilidades blandas e idiomas se muestran tal cual los escribas — "
        "la IA no los reescribe, solo redacta el resumen profesional y pule los bullets de experiencia."
    )

    perfil_actual = cargar_perfil(contexto_usuario)

    if "perfil_experiencia_editable" not in st.session_state:
        st.session_state.perfil_experiencia_editable = [dict(t) for t in perfil_actual["experiencia_laboral"]]
    if "perfil_formacion_editable" not in st.session_state:
        st.session_state.perfil_formacion_editable = [dict(f) for f in perfil_actual["formacion_academica"]]
    if "perfil_idiomas_editable" not in st.session_state:
        st.session_state.perfil_idiomas_editable = [dict(i) for i in perfil_actual["idiomas"]]

    nombre = st.text_input("Nombre completo", value=perfil_actual["nombre"])
    with st.container(horizontal=True):
        ciudad = st.text_input("Ciudad / Comuna", value=perfil_actual["ciudad"])
        email = st.text_input("Email", value=perfil_actual["email"])
        telefono = st.text_input("Teléfono", value=perfil_actual["telefono"])
        linkedin = st.text_input("LinkedIn (url o usuario)", value=perfil_actual["linkedin"])
    anos_experiencia = st.number_input(
        "Años de experiencia", min_value=0, max_value=60, value=perfil_actual["anos_experiencia"]
    )
    seniority_guardado = perfil_actual["seniority"]
    indice_seniority = (
        NIVELES_SENIORITY.index(seniority_guardado) if seniority_guardado in NIVELES_SENIORITY else 0
    )
    seniority = st.selectbox("Nivel", NIVELES_SENIORITY, index=indice_seniority)

    st.divider()
    st.markdown("#### Experiencia laboral")
    for indice, trabajo in enumerate(st.session_state.perfil_experiencia_editable):
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                trabajo["cargo"] = st.text_input("Cargo", value=trabajo.get("cargo", ""), key=f"exp_cargo_{indice}")
                trabajo["fecha_inicio"] = st.text_input(
                    "Fecha inicio (ej. Marzo 2021)", value=trabajo.get("fecha_inicio", ""), key=f"exp_fi_{indice}"
                )
            with col2:
                trabajo["empresa"] = st.text_input("Empresa", value=trabajo.get("empresa", ""), key=f"exp_empresa_{indice}")
                trabajo["actualidad"] = st.checkbox(
                    "Trabajo actual", value=trabajo.get("actualidad", False), key=f"exp_act_{indice}"
                )
                trabajo["fecha_fin"] = "" if trabajo["actualidad"] else st.text_input(
                    "Fecha término (ej. Enero 2024)", value=trabajo.get("fecha_fin", ""), key=f"exp_ff_{indice}"
                )
            trabajo["funciones"] = st.text_area(
                "Funciones y responsabilidades (una por línea)",
                value=trabajo.get("funciones", ""),
                key=f"exp_func_{indice}",
                height=100,
            )
            if st.button("🗑 Quitar esta experiencia", key=f"exp_quitar_{indice}"):
                st.session_state.perfil_experiencia_editable.pop(indice)
                st.rerun()
    if st.button("+ Agregar experiencia laboral", icon=":material/add:", key="exp_agregar"):
        st.session_state.perfil_experiencia_editable.append(
            {"cargo": "", "empresa": "", "fecha_inicio": "", "fecha_fin": "", "actualidad": False, "funciones": ""}
        )
        st.rerun()

    st.divider()
    st.markdown("#### Formación académica")
    for indice, estudio in enumerate(st.session_state.perfil_formacion_editable):
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                estudio["titulo"] = st.text_input("Título / carrera", value=estudio.get("titulo", ""), key=f"form_titulo_{indice}")
                estudio["institucion"] = st.text_input("Institución", value=estudio.get("institucion", ""), key=f"form_inst_{indice}")
            with col2:
                tipo_guardado = estudio.get("tipo", "Carrera")
                indice_tipo = TIPOS_FORMACION.index(tipo_guardado) if tipo_guardado in TIPOS_FORMACION else 0
                estudio["tipo"] = st.selectbox("Tipo", TIPOS_FORMACION, index=indice_tipo, key=f"form_tipo_{indice}")
                estudio["fecha_inicio"] = st.text_input("Año inicio", value=estudio.get("fecha_inicio", ""), key=f"form_fi_{indice}")
                estudio["fecha_fin"] = st.text_input("Año término", value=estudio.get("fecha_fin", ""), key=f"form_ff_{indice}")
            if st.button("🗑 Quitar esta formación", key=f"form_quitar_{indice}"):
                st.session_state.perfil_formacion_editable.pop(indice)
                st.rerun()
    if st.button("+ Agregar formación académica", icon=":material/add:", key="form_agregar"):
        st.session_state.perfil_formacion_editable.append(
            {"titulo": "", "institucion": "", "fecha_inicio": "", "fecha_fin": "", "tipo": "Carrera"}
        )
        st.rerun()

    st.divider()
    st.markdown("#### Idiomas")
    for indice, idioma in enumerate(st.session_state.perfil_idiomas_editable):
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                idioma["idioma"] = st.text_input("Idioma", value=idioma.get("idioma", ""), key=f"idi_nombre_{indice}")
            with col2:
                nivel_guardado = idioma.get("nivel", "Intermedio")
                indice_nivel = NIVELES_IDIOMA.index(nivel_guardado) if nivel_guardado in NIVELES_IDIOMA else 1
                idioma["nivel"] = st.selectbox("Nivel", NIVELES_IDIOMA, index=indice_nivel, key=f"idi_nivel_{indice}")
            with col3:
                if st.button("🗑", key=f"idi_quitar_{indice}"):
                    st.session_state.perfil_idiomas_editable.pop(indice)
                    st.rerun()
    if st.button("+ Agregar idioma", icon=":material/add:", key="idi_agregar"):
        st.session_state.perfil_idiomas_editable.append({"idioma": "", "nivel": "Intermedio"})
        st.rerun()

    st.divider()
    competencias_tecnicas = st.text_area(
        "Competencias técnicas y manejo de software (una por línea)",
        value=perfil_actual["competencias_tecnicas"],
        height=120,
    )
    habilidades_blandas = st.text_area(
        "Habilidades blandas (una por línea)",
        value=perfil_actual["habilidades_blandas"],
        height=120,
    )

    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        if st.button("Guardar perfil", icon=":material/save:", type="primary", use_container_width=True):
            guardar_perfil(contexto_usuario, {
                "nombre": nombre,
                "email": email,
                "telefono": telefono,
                "linkedin": linkedin,
                "ciudad": ciudad,
                "anos_experiencia": anos_experiencia,
                "seniority": seniority,
                "competencias_tecnicas": competencias_tecnicas,
                "habilidades_blandas": habilidades_blandas,
                "experiencia_laboral": st.session_state.perfil_experiencia_editable,
                "formacion_academica": st.session_state.perfil_formacion_editable,
                "idiomas": st.session_state.perfil_idiomas_editable,
                "stack_principal": "",
                "logros_y_experiencia": "",
            })
            st.success("Perfil guardado.", icon=":material/check_circle:")
    with col_sub2:
        if st.button("Limpiar campos del perfil", icon=":material/delete:", use_container_width=True):
            guardar_perfil(contexto_usuario, copy.deepcopy(VALORES_POR_DEFECTO))
            st.session_state.perfil_experiencia_editable = []
            st.session_state.perfil_formacion_editable = []
            st.session_state.perfil_idiomas_editable = []
            st.success("Perfil limpiado correctamente.", icon=":material/check_circle:")
            st.rerun()
```

- [ ] **Step 3: Verificar sintaxis de toda la app**

Run: `python -c "import app"`
Expected: sin errores. (Nota: puede imprimir warnings de Streamlit sobre "missing ScriptRunContext" — es normal al importar `app.py` fuera de `streamlit run`, no es un error real.)

- [ ] **Step 4: Levantar la app y probar manualmente en el navegador**

Run: `streamlit run app.py`

En el navegador:
1. Ir a "Mi Perfil".
2. Agregar 2 experiencias laborales con cargo/empresa/fechas/funciones distintas.
3. Agregar 1 formación académica.
4. Agregar 2 idiomas.
5. Cargar competencias técnicas y habilidades blandas (varias líneas cada una).
6. Click en "Guardar perfil" — confirmar mensaje de éxito.
7. Recargar la página (F5) y volver a "Mi Perfil" — confirmar que las 2 experiencias, la formación y los 2 idiomas siguen ahí (persistencia en `session_state` en modo invitado).
8. Click en "🗑 Quitar esta experiencia" en una de las dos — confirmar que desaparece y la otra queda intacta.
9. Click en "Limpiar campos del perfil" — confirmar que todo vuelve a estar vacío.

Expected: cada paso se comporta como se describe, sin errores en la consola del navegador ni en la terminal donde corre `streamlit run`.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat(perfil): formulario con experiencia/formación/idiomas editables como listas dinámicas"
```

---

## Task 8: Verificación end-to-end manual

**Files:** ninguno (solo verificación, sin cambios de código)

- [ ] **Step 1: Perfil completo, generación desde "Generador por URL"**

Con `streamlit run app.py` corriendo:
1. En "Mi Perfil", cargar un perfil completo: nombre, ciudad, 2 experiencias laborales (con funciones reales), 1 formación académica, 2 idiomas, varias competencias técnicas y habilidades blandas. Guardar.
2. Ir a "Generador por URL", pegar el link de una oferta real (o texto de una oferta), poner un puesto objetivo, click en "Generar CV y Cover Letter".
3. Descargar el CV en PDF y abrirlo.

Expected: el PDF muestra, en este orden, Perfil Profesional (texto de IA, coherente con el perfil), Experiencia Laboral (las 2 entradas con cargo/empresa/fechas EXACTAMENTE como se cargaron, bullets razonables), Formación Académica (literal, igual a lo cargado), Competencias Técnicas (literal), Habilidades Blandas (literal), Idiomas (literal, formato "Idioma: Nivel"). Ninguna sección literal tiene texto distinto a lo tipeado.

- [ ] **Step 2: Perfil sin idiomas**

Repetir sin cargar ningún idioma (dejar la lista vacía) y generar de nuevo.

Expected: el PDF no muestra ninguna sección "Idiomas" (ni un título vacío ni un espacio en blanco notorio).

- [ ] **Step 3: Perfil legado (verificación por test automatizado, no manual)**

No existe forma de reproducir un perfil legado real en el navegador sin haber usado la versión vieja de la app (no hay datos legados reales disponibles para probar a mano). Este caso ya queda cubierto por los tests automatizados de Task 2 (`test_migrar_legado_precarga_experiencia_desde_logros`, `test_migrar_legado_no_pisa_experiencia_existente`, `test_migrar_legado_precarga_competencias_desde_stack`), que ejercitan `_migrar_legado()` directamente con datos de prueba equivalentes a un perfil legado real.

Run: `pytest tests/test_perfil.py -k migrar_legado -v`
Expected: los 3 tests de migración en `PASSED`.

- [ ] **Step 4: Suite completa de tests**

Run: `cd /home/ale/Antigravity/huntjob_chile && source venv/bin/activate && pytest -v`
Expected: todos los tests de Tasks 1-6 en `PASSED`, ningún `FAILED` ni `ERROR`.

- [ ] **Step 5: Commit final (si hubo ajustes durante la verificación manual)**

Si el Step 1 o 2 revelan algún ajuste visual necesario (espaciado, texto), hacer el cambio puntual en `core/generador_pdf.py` y commitear:

```bash
git add core/generador_pdf.py
git commit -m "fix(pdf): ajustes visuales tras verificación manual del CV enriquecido"
```

Si no hubo ajustes, este paso se omite.

---

## Resumen de archivos tocados

- `requirements.txt` (Task 1)
- `pytest.ini`, `tests/__init__.py` (Task 1, nuevos)
- `core/perfil.py` (Task 2)
- `tests/test_perfil.py` (Task 2, nuevo)
- `sql/schema.sql` (Task 3)
- `core/generador_pdf.py` (Task 4)
- `tests/test_generador_pdf.py` (Task 4, nuevo)
- `core/motor_ia.py` (Task 5)
- `tests/test_motor_ia.py` (Task 5, nuevo)
- `core/postulacion.py` (Task 6)
- `tests/test_postulacion.py` (Task 6, nuevo)
- `app.py` (Task 7)
