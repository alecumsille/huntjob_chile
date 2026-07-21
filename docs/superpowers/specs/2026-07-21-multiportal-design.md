# HuntJob Chile — Búsqueda Multi-Portal

**Fecha:** 2026-07-21
**Estado:** Implementado y verificado en esta sesión (búsqueda multi-portal, bugs corregidos, motor de IA migrado a Gemini)

## Contexto

`huntjob_chile` es una app Streamlit ya funcional (repo propio en GitHub:
`alecumsille/huntjob_chile`, vive en `~/gestor_cv_pro/huntjob_chile/`) que:

- Extrae el texto de una oferta laboral desde su URL.
- Usa Ollama local (modelo `phi3`) para detectar el cargo y redactar un CV y
  una Cover Letter adaptados.
- Compila ambos documentos en PDF descargable (fpdf2).
- Incluye un buscador de vacantes reales, hoy limitado a Computrabajo Chile
  (scraping con `requests` + `BeautifulSoup`).

En paralelo existía un segundo borrador, suelto en `~/huntjob_chile/` (sin
git propio, dentro del repo del home), con un dispatcher (`core/portales.py`)
pensado para buscar en 13 portales chilenos, pero sin los scrapers
implementados y con un `requirements.txt` distinto (reportlab en vez de
fpdf2). Se decidió que **ese borrador no es la base** — se descarta una vez
migrada su idea útil (el dispatcher) al proyecto real.

## Objetivo

Extender el buscador de vacantes de `huntjob_chile` para consultar varios
portales chilenos en paralelo, empezando por un subconjunto acotado en vez
de los 13 originalmente imaginados, y dejar el proyecto en un estado
profesional apto para publicarse en GitHub como la forma de distribución
"para Linux" (clonar + instalar + correr).

La app Android queda fuera de alcance de este ciclo — se documenta como
ítem de roadmap, no se diseña ni implementa ahora.

## Alcance: portales

Selección original propuesta: Computrabajo, Laborum, Indeed Chile, GetOnBrd.
Tras inspeccionar las páginas reales (vía Firecrawl/Playwright) antes de
escribir código, se encontró que **Indeed Chile y GetOnBrd están detrás de
Cloudflare** y devuelven bloqueo (Indeed) o resultados vacíos silenciosos
(GetOnBrd) ante requests sin navegador real — solo funcionan con un motor
tipo Playwright (~300MB de dependencia adicional: Chromium). Indeed además
prohíbe explícitamente el scraping en sus Términos de Servicio. Se decidió
no sumar esa dependencia pesada por ahora y reemplazar ambos por portales
que sí son accesibles con `requests` simple, manteniendo la arquitectura
liviana del proyecto.

Se implementan 2 portales en esta fase:

| Portal | Función | Estado |
|---|---|---|
| Computrabajo Chile | `buscar_computrabajo` | Ya existía (`buscar_ofertas_computrabajo`), se renombra para consistencia; bug de `ubicacion` corregido (ver sección Bugs) |
| ChileTrabajos | `buscar_chiletrabajos` | Nuevo. HTML estático simple, sin bloqueo, con paginación real verificada |

**Laborum se investigó pero se descartó en esta fase**: no tiene HTML
estático (SPA React), pero se encontró su API JSON interna
(`POST /api/avisos/searchV2`). Al probarla contra la red real, la API exige
un header `x-session-jwt` que la página solo emite vía JavaScript en el
navegador (aunque el token dura ~30 días una vez obtenido, no hay forma de
conseguirlo con un `requests.get` simple). No se implementó una función
`buscar_laborum` en el código para evitar dejar una función que siempre
falla en el repo — queda documentado acá como punto de partida si más
adelante se justifica sumar Playwright.

Los demás portales del borrador original (BNE, Trabajando.cl, Jooble,
LinkedIn, MiGuru, Un Mejor Empleo, FirstJob, Trabajos con Sentido, Indeed,
GetOnBrd) quedan fuera de esta fase. `PORTALES` en `core/portales.py` se
limita a los 2 de arriba; agregar más portales después es extender ese
diccionario y sumar una función — no un rediseño. Si en el futuro se
justifica agregar Playwright como dependencia, Laborum, Indeed y GetOnBrd
son los primeros candidatos a revisar (ya se investigó su estructura real
en esta sesión).

LinkedIn en particular no se contempla en absoluto: requiere login y
bloquea scraping agresivamente, es un problema aparte (no un ajuste
incremental de selectores).

## Arquitectura

Sin cambios de arquitectura respecto al patrón ya usado en
`core/scraper_web.py`: cada portal es una función
`buscar_<portal>(palabra_clave: str, paginas: int = 1) -> list[dict]` que:

- Devuelve una lista de dicts con las keys `titulo`, `empresa`, `ubicacion`,
  `link`.
- Levanta `ErrorScraping` (ya definida en `scraper_web.py`) ante fallos de
  red o de parseo, con mensaje explícito de qué selector/estructura falló
  (mismo criterio que ya documenta el README para Computrabajo).

`core/portales.py` (adaptado desde el borrador, con el diccionario acotado a
2 entradas) aporta:

- `PORTALES`: registro `id -> {nombre, url, funcion, categoria}`.
- `buscar_en_portal(portal_id, palabra_clave, paginas)`: llama a un portal,
  captura `ErrorScraping` y cualquier excepción inesperada, nunca propaga.
- `buscar_en_todos(palabra_clave, paginas, portales_seleccionados=None)`:
  agrega resultados de varios portales; si uno falla, los demás igual
  devuelven resultados. Devuelve `(resultados, errores)`.

Cada dict de resultado recibe además `fuente` (nombre legible del portal),
asignado por `buscar_en_portal` — así la UI puede agrupar/mostrar el origen
sin que cada scraper individual se preocupe de eso.

### Selectores reales

El selector de ChileTrabajos no se inventó: se determinó inspeccionando la
página real (vía Playwright y curl) antes de escribir el código:

- **ChileTrabajos**: `GET https://www.chiletrabajos.cl/encuentra-un-empleo`
  (página 1) o `.../encuentra-un-empleo/{(pagina-1)*30}` (páginas
  siguientes), con querystring `?2=<palabra_clave>&f=2` (nombres de campo
  numéricos heredados del formulario del sitio, verificados en vivo — no
  son un placeholder). Tarjetas en `div.job-item`, título+link en
  `h2.title a`, empresa+ubicación en el primer `h3.meta` de la tarjeta,
  fecha en el segundo.

Si un sitio cambia su estructura en el futuro, el patrón ya establecido
(excepción explícita, nunca fallo silencioso) hace evidente qué hay que
arreglar.

## UI (Streamlit)

El tab actual "Buscador Computrabajo" se **reemplaza** por "Buscador de
Vacantes":

- Checkboxes para elegir en qué portales buscar (los 2, todos marcados por
  defecto).
- Input de palabra clave (se mantiene).
- Slider de páginas a recorrer (se mantiene, aplica a todos los portales
  seleccionados).
- Botón "Buscar ofertas" llama a `buscar_en_todos` con los portales
  marcados.
- Resultados listados con la fuente visible por oferta.
- Si `errores` no está vacío, se muestran como advertencias no bloqueantes
  (los resultados de los portales que sí funcionaron igual se muestran).

El resto de la app (sección "Generador por URL") no cambia.

## Bugs encontrados y corregidos (revisión de código previa a la expansión)

Antes de sumar portales se revisó el código existente en busca de errores:

- **`buscar_ofertas_computrabajo` (ubicación incorrecta):** el selector
  `p.fs13, span.fs13` capturaba el texto "Hace X minutos" (tiempo de
  publicación) en vez de la ciudad real. La ciudad está en un `p.fs16`
  distinto (el que no contiene un link de empresa). Se corrige el selector
  y se agrega el dato de modalidad (Remoto/Híbrido/Presencial) cuando el
  sitio lo expone.
- **`generar_pdf` (caracteres especiales rompen el PDF):** el texto se pasa
  directo a `reportlab.platypus.Paragraph`, que interpreta un subconjunto de
  XML/HTML. Cualquier texto generado por la IA que contenga `&`, `<` o `>`
  (común: "I+D", "Sales & Marketing", "Python 3.11 < 3.12") puede romper la
  compilación del PDF o corromper el render. Se corrige escapando el texto
  con `xml.sax.saxutils.escape` antes de envolverlo en `Paragraph`.
- **`generar_pdf` (Markdown crudo en el PDF final):** Gemini responde con
  sintaxis Markdown (`**negrita**`, `### headers`, `***` como separador).
  ReportLab no interpreta Markdown, así que esos símbolos quedaban
  literales en el CV/Cover Letter generado — se ve poco profesional en el
  documento que el usuario efectivamente descarga y envía. Se agrega
  `_limpiar_markdown()` que quita headers, negritas/cursivas y normaliza
  bullets antes de renderizar cada línea. Verificado con una generación
  real end-to-end (oferta real de Computrabajo → Gemini → PDF).

## Cambio de motor de IA: de Ollama local a Gemini

El diseño original asumía Ollama + phi3 corriendo en local (ver README
previo). Al probarlo en esta sesión aparecieron dos problemas:

1. **Bug de nombre de modelo:** el código pedía el modelo `"phi3"`, pero el
   modelo realmente instalado en esta máquina es `"phi3.5"`. La función
   `verificar_ollama_activo` no lo detectaba porque hacía un chequeo por
   substring (`"phi3" in "phi3.5:latest"` da `True`), así que el error solo
   aparecía al intentar generar texto, no en la verificación previa.
2. **Hardware no viable para inferencia local:** esta máquina no tiene
   soporte AVX (`lscpu` no reporta ningún flag AVX). Con Ollama corriendo,
   un prompt de una sola palabra tardó más de 3 minutos sin terminar de
   responder — muy por encima de cualquier timeout razonable para una app
   interactiva (ver también `project_yoga330_hardware_limits` en la
   memoria del usuario, que ya documentaba esta limitación de hardware).

El usuario pidió explícitamente reemplazar esto por una opción gratuita o
ya disponible en el entorno. Se optó por **Gemini** (`gemini-3.1-flash-lite`)
vía la API REST de Google AI, usando la misma cuenta/estilo de key que ya
usa en `~/cli_alemania.py` (proyecto no relacionado, pero mismo proveedor).
La key se lee de la variable de entorno `GEMINI_API_KEY` — nunca
hardcodeada en el repo, siguiendo el mismo criterio de "sin credenciales
en el código" ya aplicado en el resto de esta sesión.

`core/motor_ia.py` mantiene la misma interfaz pública
(`generar_texto(prompt_sistema, texto_base) -> str`), pero la excepción se
renombra de `ErrorOllama` a `ErrorIA` (ya no es específica de Ollama).
`verificar_ollama_activo()` (un ping de red a Ollama) se reemplaza por un
chequeo simple de que `GEMINI_API_KEY` esté seteada — no hace falta un
ping aparte porque cualquier problema real de la API lo va a reportar la
propia llamada a `generateContent` con un mensaje explícito.

**Trade-off aceptado:** el texto de las ofertas y del CV ahora se envía a
la API de Gemini (ya no es 100% local/privado como con Ollama). Dado que
el hardware no permitía usar Ollama de forma utilizable de todas formas,
y que el usuario tiene esta misma cuenta de Gemini validada en otro
proyecto, se consideró un trade-off razonable y explícitamente solicitado.

## Profesionalización

- Cero emojis: ni en código, ni en la UI (`st.success`, `st.error`, etc.),
  ni en README, ni en mensajes de commit.
- README actualizado con: instalación (`git clone` + venv + `pip install -r
  requirements.txt` + `ollama pull phi3` + `streamlit run app.py`), tabla de
  portales soportados, y una sección "Roadmap" que menciona la futura app
  Android como fase separada, sin comprometer alcance ni fecha.
- Se revisa que no haya credenciales ni API keys hardcodeadas en el repo
  (motivado por haber encontrado una key real hardcodeada en
  `~/cli_alemania.py`, un proyecto no relacionado, durante esta sesión).
- `.gitignore` existente (`__pycache__/`, `*.pyc`, `salidas_pdf/`, `venv/`)
  se mantiene sin cambios — el proyecto no usa `.env` ni archivos de perfil
  con datos personales, así que no hace falta agregar nada.
- Estilo de código consistente con lo ya existente: nombres en español,
  type hints, excepciones específicas (`ErrorScraping`), sin capas de
  abstracción nuevas que no se estén usando.

## Limpieza

Una vez migrada la funcionalidad y verificada en la UI:

- Se elimina `~/huntjob_chile/` (borrador suelto, sin git propio,
  incompleto).
- Se elimina `~/gestor_cv_pro/app.py` (archivo vacío, sin relación con el
  proyecto).

## Testing

- Cada scraper (`buscar_computrabajo`, `buscar_chiletrabajos`) se prueba de
  forma standalone contra una palabra clave real (ej. "Python") antes de
  integrarlo al dispatcher, confirmando que devuelve resultados no vacíos
  con las keys esperadas.
- Verificación manual en el navegador: correr `streamlit run app.py`,
  probar el tab "Buscador de Vacantes" con distintas combinaciones de
  portales marcados/desmarcados, confirmar que un portal fallando no rompe
  a los demás.
- No se agrega suite de tests automatizados nueva en esta fase — no hay
  tests previos en el proyecto y el patrón de la sesión con este usuario es
  profesionalizar de forma reactiva, no proactiva, cuando el costo lo
  justifica.

## Fuera de alcance (explícito)

- Laborum, Indeed, GetOnBrd y los demás portales del borrador original.
- App Android.
- Empaquetado como AppImage/.deb — la distribución "para Linux" es vía
  GitHub (clonar + instalar), no un instalador nativo.
- Tests automatizados nuevos.
