# HuntJob Chile — Perfil y CV enriquecidos (datos literales + IA acotada)

**Fecha:** 2026-07-22
**Estado:** Aprobado por el usuario, pendiente de plan de implementación

## Contexto

El perfil de usuario (fase 1) y la personalización de prompts (fase 3,
ver `2026-07-21-personalizacion-cv-design.md`) dejaron el CV generado
100% en manos de la IA: todo el contenido —incluido el stack y los
logros— sale de dos campos de texto libre (`stack_principal`,
`logros_y_experiencia`) que Gemini convierte en prosa. Esto tiene dos
problemas: (1) un CV real chileno necesita secciones que hoy no existen
en absoluto —formación académica, habilidades blandas separadas de las
técnicas, idiomas, ciudad— y (2) al depender de que la IA redacte todo
en prosa libre, hechos concretos (fechas, nombres de instituciones,
herramientas exactas) quedan expuestos a que la IA los parafrasee o
reordene de forma imprecisa, cuando deberían mostrarse tal cual el
usuario los escribió.

Se revisaron 3 guías de referencia sobre cómo armar un CV en Chile
(Computrabajo, Laborum, CVMaker) para definir la estructura estándar:
datos personales (nombre, ciudad/comuna, teléfono, email — sin
dirección exacta, estado civil ni edad), perfil profesional, experiencia
laboral (cargo, empresa, fechas, funciones con verbos de acción),
formación académica (título, institución, fechas), habilidades técnicas
y blandas por separado, idiomas, y una extensión de 1-2 páginas en PDF.

## Objetivo

Enriquecer el perfil con datos estructurados y literales (formación
académica, experiencia laboral por trabajo, habilidades blandas,
competencias técnicas, idiomas, ciudad), y cambiar el CV generado para
que esas secciones se rendericen tal cual las escribió el usuario, sin
que la IA las reescriba — dejando a la IA solo la redacción del "Perfil
profesional" y el pulido/priorización de los bullets de experiencia,
siempre sobre hechos reales que el usuario ya cargó.

## Diseño

### 1. Modelo de datos (`core/perfil.py`)

`VALORES_POR_DEFECTO` gana estos campos:

```python
"ciudad": "",
"experiencia_laboral": [],   # [{cargo, empresa, fecha_inicio, fecha_fin, actualidad, funciones}]
"formacion_academica": [],   # [{titulo, institucion, fecha_inicio, fecha_fin, tipo}]  tipo: Carrera/Curso/Certificación
"idiomas": [],               # [{idioma, nivel}]  nivel: Básico/Intermedio/Avanzado/Nativo
"habilidades_blandas": "",   # texto multilínea, una habilidad por línea
"competencias_tecnicas": "", # texto multilínea, una competencia/herramienta por línea
```

`stack_principal` y `logros_y_experiencia` se mantienen en
`VALORES_POR_DEFECTO` únicamente como origen de la migración automática
(ver sección 3) — dejan de usarse en la generación del CV.

`formatear_perfil()` se reescribe para serializar todos los campos
nuevos (literal, sin resumir) — sigue siendo la fuente única que
consumen `motor_ia.py` (match ATS, asistente de formularario) y
`postulacion.py`.

### 2. Migración de Supabase (`sql/schema.sql`)

Se agregan columnas nuevas a `perfiles` con `ALTER TABLE`:

```sql
alter table public.perfiles add column if not exists ciudad text default '';
alter table public.perfiles add column if not exists experiencia_laboral jsonb default '[]';
alter table public.perfiles add column if not exists formacion_academica jsonb default '[]';
alter table public.perfiles add column if not exists idiomas jsonb default '[]';
alter table public.perfiles add column if not exists habilidades_blandas text default '';
alter table public.perfiles add column if not exists competencias_tecnicas text default '';
```

Esto lo debe correr Alejandro manualmente en el SQL Editor de Supabase
— la app solo tiene la Anon Key (sin permiso de DDL), por diseño de
seguridad ya establecido.

### 3. Migración de datos existentes (al cargar el perfil)

En `cargar_perfil()`, después de obtener el perfil (de Postgres o
`session_state`): si `experiencia_laboral` está vacío y
`logros_y_experiencia` tiene contenido, se antepone una entrada
`{"cargo": "", "empresa": "", "fecha_inicio": "", "fecha_fin": "",
"actualidad": False, "funciones": logros_y_experiencia}` — editable, no
se borra el campo viejo. Mismo criterio para `stack_principal` →
primera línea de `competencias_tecnicas` si esta última está vacía. Es
un fallback de lectura, no una migración destructiva de una sola vez en
la base.

### 4. Formulario "Mi Perfil" (`app.py`)

Streamlit no permite botones reactivos de agregar/quitar dentro de
`st.form` (solo reacciona al submit). La pestaña deja de ser un único
form:

- Datos simples (nombre, ciudad, email, teléfono, linkedin, años de
  experiencia, seniority, habilidades blandas, competencias técnicas)
  siguen en `st.form("form_perfil_basico")`.
- Experiencia laboral, formación académica e idiomas se manejan fuera
  del form, respaldados por listas en `st.session_state`
  (`st.session_state.experiencia_editable`, etc.), cada entrada
  renderizada con sus campos propios (keys únicas por índice) y un
  botón "🗑 Quitar esta entrada". Un botón "+ Agregar experiencia" (e
  idem formación/idioma) al final de cada bloque agrega un dict vacío
  a la lista y hace `st.rerun()`.
- Un botón "Guardar perfil" (fuera de cualquier form, para poder juntar
  tanto los campos del form básico como las listas dinámicas) llama a
  `guardar_perfil()` con todo junto.

### 5. Generación (`core/postulacion.py`)

Se reemplaza el prompt único de 3 secciones por dos llamadas a la IA,
ambas acotadas:

- **Resumen profesional:** un párrafo de 3-4 líneas (como hoy), a
  partir del perfil completo — sigue siendo texto libre vía
  `generar_texto`.
- **Bullets de experiencia pulidos:** por cada entrada de
  `experiencia_laboral`, se pide a la IA (con `response_schema`, mismo
  patrón que `analizar_match`/`extraer_cargo_y_empresa` en
  `motor_ia.py`) que devuelva una versión reordenada/pulida de las
  `funciones` ya cargadas por el usuario para ese trabajo puntual,
  priorizando lo relevante para la oferta — nunca inventa funciones
  nuevas, cargos, empresas o fechas, que siempre vienen literales del
  perfil.

Formación académica, competencias técnicas, habilidades blandas e
idiomas **no pasan por la IA** — se renderizan directo desde el perfil.

### 6. PDF (`core/generador_pdf.py`)

`generar_pdf()` cambia de recibir un solo bloque de texto a recibir el
`perfil` completo + el resumen profesional (IA) + los bullets pulidos
por trabajo (IA), y arma las secciones en este orden:

1. Encabezado: nombre, ciudad, contacto (email · teléfono · LinkedIn)
2. Perfil Profesional (IA)
3. Experiencia Laboral — por cada trabajo: `Cargo — Empresa | fecha_inicio – fecha_fin` (o "Actualidad") literal, seguido de los bullets pulidos
4. Formación Académica — por cada entrada: `Título — Institución | fechas`, literal
5. Competencias Técnicas y Manejo de Software — lista literal
6. Habilidades Blandas — lista literal
7. Idiomas — `Idioma: Nivel`, literal (se omite la sección entera si la lista está vacía)

Los 4 temas visuales (Pastel, Ejecutivo, Minimalista Oscuro, Esmeralda)
se mantienen sin cambios — solo cambia qué contenido se dibuja, no la
paleta ni la tipografía.

### 7. Cover Letter

Sin cambios de lógica — sigue usando `formatear_perfil()`, que ahora
trae más contexto real (formación, idiomas, etc.) disponible si la IA
lo necesita para una mención puntual, sin secciones nuevas obligatorias
en la carta.

## Fuera de alcance (explícito)

- Reordenar Experiencia después de Formación para perfiles junior/recién
  egresados (mencionado en una de las guías como opcional) — se deja
  siempre Experiencia antes que Formación, sin lógica condicional.
- Tags/chips de UI para habilidades — se usa texto multilínea simple.
- Foto de perfil, referencias laborales, u otras secciones que las
  guías marcan como opcionales/no recomendadas en Chile.
- Cambiar el análisis ATS (`analizar_match`) — sigue comparando contra
  `formatear_perfil()` como ya hace, sin cambios de lógica propia.
- Migrar o tocar el Cover Letter más allá de que reciba el perfil
  enriquecido como contexto (sin secciones nuevas obligatorias ahí).

## Testing

- Perfil nuevo (usuario sin datos previos): cargar 2 experiencias, 1
  formación, 2 idiomas, generar CV, confirmar que las 7 secciones
  aparecen en el orden correcto y que Formación/Competencias/Habilidades
  Blandas/Idiomas coinciden EXACTAMENTE con lo tipeado (sin parafraseo).
- Perfil legado (con `logros_y_experiencia` y `stack_principal` viejos,
  sin nada en los campos nuevos): confirmar que la migración de lectura
  precarga una entrada de experiencia editable con ese texto, sin
  perder el dato.
- Perfil sin idiomas cargados: confirmar que la sección "Idiomas" no
  aparece en el PDF (no una sección vacía).
- Verificación manual en navegador: flujo completo (URL → generar CV) y
  descarga del PDF real, revisando visualmente que el orden y el
  contenido literal calcen con lo cargado en "Mi Perfil".
