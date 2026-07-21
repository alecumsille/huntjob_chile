# HuntJob Chile — Perfil de usuario (fase 1 de "app más inteligente")

**Fecha:** 2026-07-21
**Estado:** Aprobado por el usuario, pendiente de plan de implementación

## Contexto

El usuario pidió hacer la app "mucho más inteligente", con cuatro ideas
concretas: matching de ofertas contra su perfil, CVs/Cover Letters más
personalizados, deduplicación de resultados entre portales, y un asistente
conversacional. Las cuatro son features grandes para un solo ciclo de
diseño, y dos de ellas (matching y personalización) dependen de algo que
hoy no existe: un perfil real del usuario guardado en la app. Hoy el
nombre "Ale Cumsille" está hardcodeado directamente en los prompts de
`app.py`, y no hay ningún dato sobre años de experiencia, stack o logros
reales que la IA pueda usar como contexto.

Se acordó construir en este orden: (1) perfil de usuario, (2) matching,
(3) personalización de CV/CL, (4) deduplicación, (5) chat asistente. Este
documento cubre solo la fase 1. Las siguientes fases se diseñan por
separado, cada una con su propio spec corto, una vez completada esta.

## Objetivo

Crear un perfil de usuario persistente y editable desde la propia app, que
sirva de base de datos real para las fases 2 y 3. En esta fase **no** se
usa el perfil para matching ni para mejorar los prompts de generación de
CV/CL más allá del nombre de firma — eso es explícitamente el trabajo de
las fases siguientes.

## Campos del perfil

| Campo | Tipo | Notas |
|---|---|---|
| `nombre` | texto corto | Reemplaza el "Ale Cumsille" hardcodeado en la Cover Letter |
| `anos_experiencia` | número entero | |
| `seniority` | selección | Junior / Semi Senior / Senior / Lead |
| `stack_principal` | texto corto | Lenguajes, frameworks, herramientas — libre pero acotado a una línea |
| `logros_y_experiencia` | texto largo | Proyectos reales, resultados cuantificables. Es el campo que va a alimentar matching (fase 2) y personalización (fase 3) — el más importante de los cinco |

Ningún campo es estrictamente obligatorio para guardar el formulario
(salvo `nombre`, sin el cual no hay a quién firmar la Cover Letter); si
`logros_y_experiencia` queda vacío, las fases futuras van a tener menos
contexto real para trabajar, pero eso no es un error de esta fase.

## Almacenamiento

- Carpeta nueva `perfil/`, archivo `perfil/mi_perfil.yaml`.
- Se agrega `perfil/` al `.gitignore` existente — son datos personales del
  usuario, nunca se suben al repo público en GitHub.
- Nueva dependencia: `pyyaml` (agregar a `requirements.txt`). Es una
  dependencia liviana y ya aparecía en el borrador previo
  (`~/huntjob_chile`, descartado en la sesión anterior), así que no es una
  elección nueva sin precedente en este proyecto.
- Módulo nuevo `core/perfil.py` con:
  - `cargar_perfil() -> dict`: lee el YAML si existe, devuelve un dict con
    valores por defecto (strings vacíos, 0, primer valor de seniority) si
    el archivo no existe todavía — nunca lanza excepción por archivo
    faltante, ya que "sin perfil guardado" es un estado válido y esperado
    la primera vez que se abre la app.
  - `guardar_perfil(datos: dict) -> None`: escribe el YAML, creando la
    carpeta `perfil/` si no existe.

## UI (Streamlit)

Nuevo tab "Mi Perfil" en el `st.sidebar.radio` (tercera opción, después de
"Generador por URL" y "Buscador de Vacantes").

- Al entrar, se llama `cargar_perfil()` y se usan sus valores como
  `value=`/`index=` por defecto de cada widget del formulario.
- Un `st.form` agrupa los 5 campos + un `st.form_submit_button("Guardar
  perfil")`.
- Al enviar el formulario, se llama `guardar_perfil()` con los valores
  actuales y se muestra `st.success("Perfil guardado.")`.
- Encima del formulario, un `st.caption` explica brevemente para qué sirve
  el perfil (que alimenta matching y personalización en próximas
  versiones), para que no se sienta como una pantalla suelta sin
  propósito visible todavía.

## Integración con lo existente

En la sección "Generador por URL", el prompt de la Cover Letter hoy tiene
`f"Firma con el nombre Ale Cumsille."` hardcodeado. Se reemplaza por el
`nombre` cargado desde `cargar_perfil()`. Si el perfil no tiene nombre
guardado (primera vez, formulario nunca completado), se muestra una
advertencia (`st.warning`) sugiriendo completar el tab "Mi Perfil" antes
de generar documentos, pero no se bloquea la generación — mantiene el
mismo criterio de "fallar explícito pero no bloquear features que sí
pueden funcionar" que ya usa el resto de la app (ver `buscar_en_todos`).

No se toca nada más de los prompts existentes en esta fase.

## Fuera de alcance (explícito)

- Usar `stack_principal` o `logros_y_experiencia` en los prompts de
  generación de CV/CL — fase 3 (personalización).
- Calcular matching/score de las ofertas contra el perfil — fase 2.
- Deduplicación de resultados — fase 4.
- Chat asistente — fase 5.
- Validación estricta de campos (ej. rangos de años de experiencia) — no
  hay indicio de que haga falta, YAGNI.

## Testing

- Guardar el formulario con datos de prueba, recargar la app (`streamlit
  run` de nuevo) y confirmar que los campos se precargan con lo guardado.
- Confirmar que `perfil/mi_perfil.yaml` no aparece en `git status` (cubierto
  por `.gitignore`).
- Generar una Cover Letter real y confirmar que firma con el nombre del
  perfil en vez de "Ale Cumsille" hardcodeado.
- Probar el caso sin perfil guardado (archivo inexistente): la app no
  debe crashear, el formulario debe verse vacío con los valores por
  defecto razonables.
