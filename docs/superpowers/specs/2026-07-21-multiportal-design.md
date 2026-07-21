# HuntJob Chile — Búsqueda Multi-Portal

**Fecha:** 2026-07-21
**Estado:** Aprobado por el usuario, pendiente de plan de implementación

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

Se implementan 4 portales en esta fase:

| Portal | Función | Estado |
|---|---|---|
| Computrabajo Chile | `buscar_computrabajo` | Ya existe (`buscar_ofertas_computrabajo`), se renombra para consistencia |
| Laborum | `buscar_laborum` | Nuevo |
| Indeed Chile | `buscar_indeed` | Nuevo |
| GetOnBrd | `buscar_getonbrd` | Nuevo |

Los otros 9 portales del borrador original (BNE, ChileTrabajos,
Trabajando.cl, Jooble, LinkedIn, MiGuru, Un Mejor Empleo, FirstJob, Trabajos
con Sentido) quedan fuera de esta fase. `PORTALES` en `core/portales.py` se
limita a los 4 de arriba; agregar más portales después es extender ese
diccionario y sumar una función — no un rediseño.

LinkedIn en particular no se contempla en absoluto por ahora: requiere login
y bloquea scraping agresivamente, es un problema aparte (no un ajuste
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
4 entradas) aporta:

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

Los selectores CSS de Laborum, Indeed Chile y GetOnBrd no se inventan: se
determinan inspeccionando las páginas reales de resultados de búsqueda de
cada sitio (vía Firecrawl) durante la implementación. Si un sitio cambia su
estructura en el futuro, el patrón ya establecido (excepción explícita,
nunca fallo silencioso) hace evidente qué romper hay que arreglar.

## UI (Streamlit)

El tab actual "Buscador Computrabajo" se **reemplaza** por "Buscador de
Vacantes":

- Checkboxes para elegir en qué portales buscar (los 4, todos marcados por
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
- `.gitignore` existente (`datos/`, `perfil/mi_perfil.yaml`, `salidas_pdf/`,
  `.env`, etc.) se mantiene sin cambios — ya cubre lo necesario.
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

- Cada scraper nuevo (`buscar_laborum`, `buscar_indeed`, `buscar_getonbrd`)
  se prueba de forma standalone contra una palabra clave real (ej.
  "Python") antes de integrarlo al dispatcher, confirmando que devuelve
  resultados no vacíos con las keys esperadas.
- Verificación manual en el navegador: correr `streamlit run app.py`,
  probar el tab "Buscador de Vacantes" con distintas combinaciones de
  portales marcados/desmarcados, confirmar que un portal fallando no rompe
  a los demás.
- No se agrega suite de tests automatizados nueva en esta fase — no hay
  tests previos en el proyecto y el patrón de la sesión con este usuario es
  profesionalizar de forma reactiva, no proactiva, cuando el costo lo
  justifica.

## Fuera de alcance (explícito)

- Los otros 9 portales del borrador original.
- App Android.
- Empaquetado como AppImage/.deb — la distribución "para Linux" es vía
  GitHub (clonar + instalar), no un instalador nativo.
- Tests automatizados nuevos.
