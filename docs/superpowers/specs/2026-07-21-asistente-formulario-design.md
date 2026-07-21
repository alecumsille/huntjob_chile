# HuntJob Chile — Asistente de respuestas para formularios de postulación

**Fecha:** 2026-07-21
**Estado:** Aprobado por el usuario, pendiente de plan de implementación

## Contexto

Además del CV y la Cover Letter, la mayoría de las postulaciones reales
piden completar un formulario propio del portal/empresa con preguntas
puntuales ("¿Cuántos años de experiencia tienes en X?", "¿Tienes
disponibilidad para trabajar presencial?", a veces de opción múltiple).
Hoy el usuario responde esas preguntas a mano, sin ayuda de la app.

Se evaluaron dos niveles de ayuda:
1. Un asistente que sugiere la respuesta y el usuario la copia manualmente
   al formulario real.
2. Automatizar el llenado y envío del formulario real, vía control de
   navegador.

Se descartó explícitamente la opción 2: requeriría automatizar un
navegador (mismo problema técnico ya evaluado y descartado para
Indeed/GetOnBrd por protección Cloudflare), cada portal/empresa tiene un
formulario completamente distinto (nada reutilizable entre sitios), y
varios portales prohíben expresamente la postulación automatizada en sus
Términos de Servicio. Se construye la opción 1.

## Objetivo

Un nuevo tab "Preguntas de Postulación" donde el usuario pega la pregunta
del formulario real (y las alternativas, si es de opción múltiple), y la
app sugiere una respuesta basada en su perfil guardado. El usuario
siempre revisa y copia la respuesta manualmente — la app nunca completa
ni envía nada en un formulario real.

## Arquitectura

### `core/motor_ia.py`: nueva función `sugerir_respuesta`

```
sugerir_respuesta(pregunta: str, perfil: dict, opciones: list[str] | None = None) -> dict
```

Devuelve `{"respuesta": str, "justificacion": str}`.

- **Con `opciones`** (pregunta de opción múltiple): usa
  `generationConfig.responseSchema` con la propiedad `respuesta` de tipo
  `STRING` y `enum: opciones` — esto **fuerza** a Gemini a devolver
  textualmente una de las opciones dadas, nunca una respuesta inventada
  que no calce con ninguna alternativa real del formulario. Mismo
  mecanismo de JSON estructurado que ya usa `analizar_match` (fase 2),
  probado y confiable.
- **Sin `opciones`** (respuesta libre): pide una respuesta corta y
  directa, lista para pegar en el formulario, sin restricción de schema
  más allá de `{"respuesta": str, "justificacion": str}`.
- El prompt incluye el contexto del perfil (`anos_experiencia`,
  `seniority`, `stack_principal`, `logros_y_experiencia`) — mismos campos
  que ya usa `analizar_match`, no se agrega nada nuevo al perfil en esta
  fase.
- Reutiliza `_obtener_api_key()`, `URL_API`, `MODELO`,
  `TIMEOUT_SEGUNDOS` ya existentes. Lanza `ErrorIA` en cualquier fallo
  (red, JSON inválido, keys faltantes), mismo criterio que el resto del
  módulo.

### `app.py`: nuevo tab "Preguntas de Postulación"

Cuarta opción en el `st.sidebar.radio` (después de "Mi Perfil").

- `st.text_area` para la pregunta.
- `st.text_input` opcional para alternativas, separadas por coma (ej.
  "Sí, No, A veces"). Si el campo está vacío, se trata como respuesta
  libre.
- Botón "Sugerir respuesta": llama a `cargar_perfil()` +
  `sugerir_respuesta(...)`, muestra la respuesta sugerida (destacada,
  fácil de copiar) + la justificación breve debajo.
- Si el perfil está vacío/incompleto, no se bloquea — Gemini simplemente
  tiene menos contexto real, mismo criterio de degradación que el resto
  de la app.

## Fuera de alcance (explícito)

- Automatizar el llenado o envío de formularios reales en cualquier
  portal — descartado explícitamente por las razones de la sección
  Contexto.
- Detectar/extraer automáticamente las preguntas desde la página de la
  oferta o del formulario — el usuario las pega a mano.
- Guardar un historial de preguntas/respuestas sugeridas entre sesiones.
- Nuevos campos de perfil — se reutilizan los mismos que ya usa el
  matching (fase 2).

## Testing

- Probar `sugerir_respuesta` de forma standalone contra la API real de
  Gemini, con y sin `opciones`:
  - Con opciones: confirmar que la `respuesta` devuelta es exactamente
    una de las opciones dadas (no una paráfrasis ni texto inventado).
  - Sin opciones: confirmar que devuelve una respuesta no vacía y
    razonable dado un perfil de prueba.
- Verificación manual en el navegador: completar una pregunta de opción
  múltiple real (ej. "¿Tienes disponibilidad para trabajar de forma
  presencial? Sí, No, Híbrido") y una de respuesta libre (ej. "¿Por qué
  quieres trabajar en esta empresa?"), confirmar que ambas muestran una
  respuesta razonable.
