# HuntJob Chile — Matching de ofertas contra el perfil (fase 2)

**Fecha:** 2026-07-21
**Estado:** Aprobado por el usuario, pendiente de plan de implementación

## Contexto

Con el perfil de usuario ya implementado (fase 1: `core/perfil.py`, tab
"Mi Perfil"), la siguiente fase del roadmap "app más inteligente" es
comparar las ofertas encontradas en el Buscador de Vacantes contra ese
perfil real, para que el usuario sepa qué tan buen fit es cada una sin
tener que leer la oferta completa él mismo.

Una búsqueda puede traer 20-50 resultados. Pedirle a Gemini un análisis
para cada uno automáticamente sería lento (decenas de llamadas
secuenciales) y gastaría cuota de la API sin necesidad, para ofertas que
el usuario ni siquiera va a mirar. Se decidió que el análisis sea **bajo
demanda**: un botón por tarjeta, no automático para toda la lista.

## Objetivo

Agregar un botón "Analizar match" a cada tarjeta de resultado en
"Buscador de Vacantes". Al presionarlo, se extrae el texto completo de
esa oferta puntual y se compara contra el perfil guardado, mostrando un
score de 0 a 100 más una explicación breve (fortalezas y brechas, ej.
años de experiencia insuficientes o stack no mencionado).

## Verificación técnica previa

Se confirmó en vivo contra la API real de Gemini (modelo
`gemini-3.1-flash-lite`, el mismo que ya usa el proyecto) que el modo de
respuesta JSON estructurada (`generationConfig.responseMimeType:
"application/json"` + `responseSchema`) funciona correctamente y devuelve
un JSON válido con los campos pedidos. Se usa este mecanismo en vez de
parsear texto libre con regex — mucho más confiable, sin ambigüedad sobre
dónde está el número del score dentro de una respuesta en prosa.

## Arquitectura

### `core/motor_ia.py`: nueva función `analizar_match`

```
analizar_match(texto_oferta: str, perfil: dict) -> dict
```

- Arma un prompt con los campos relevantes del perfil (`anos_experiencia`,
  `seniority`, `stack_principal`, `logros_y_experiencia` — `nombre`,
  `email`, `telefono`, `linkedin` no aportan nada a un análisis de fit
  técnico, no se incluyen) y el texto de la oferta (truncado a
  `LIMITE_CARACTERES_CONTEXTO`, igual que `generar_texto`).
- Pide a Gemini un JSON con `{"score": int, "explicacion": str}` vía
  `generationConfig.responseSchema`.
- Devuelve `{"score": int, "explicacion": str}`. Lanza `ErrorIA` si la
  API falla, si la respuesta no es JSON válido, o si faltan las keys
  esperadas — mismo criterio de "fallar explícito" que ya usa
  `generar_texto`.
- Reutiliza `_obtener_api_key()` (ya soporta env var y `st.secrets`) y
  `TIMEOUT_SEGUNDOS`/`LIMITE_CARACTERES_CONTEXTO` existentes.

### `app.py`: sección "Buscador de Vacantes"

**Cambio de persistencia (necesario, no opcional):** hoy `resultados` y
`errores` son variables locales dentro del `if buscar:`, que solo existen
en el render inmediatamente posterior a apretar "Buscar ofertas". Un
botón "Analizar match" dentro de una tarjeta, al apretarse, dispara un
rerun de todo el script donde `buscar` vuelve a ser `False` — sin
persistencia, la lista de resultados desaparecería. Se guardan en
`st.session_state.resultados_busqueda` y
`st.session_state.errores_busqueda`, seteados tanto al buscar como
recuperados en renders posteriores.

**Por cada tarjeta de oferta:**
- Botón "Analizar match" (icon `:material/insights:`). Al presionarlo:
  - `st.spinner` mientras se extrae el texto (`extraer_texto_url`) y se
    llama a `analizar_match`.
  - Si `extraer_texto_url` o `analizar_match` fallan (`ErrorScraping` /
    `ErrorIA`), se muestra el error en la tarjeta sin romper el resto de
    la lista — mismo patrón que ya usa el buscador multi-portal.
  - El resultado (`score` + `explicacion`) se guarda en
    `st.session_state.matches`, un dict keyed por `oferta["link"]` (único
    por oferta real), para no tener que re-analizar si el usuario
    interactúa con otra parte de la página.
- Si ya hay un match analizado para esa oferta (existe en
  `st.session_state.matches`), se muestra el score + explicación en vez
  del botón (o junto a un botón "Volver a analizar", a definir en el
  plan de implementación si agrega valor real).
- Visualización del score: color según rango — verde (`st.badge(...,
  color="green")`) si `score >= 70`, amarillo (`color="yellow"`) si `40
  <= score < 70`, rojo (`color="red"`) si `score < 40`. La explicación se
  muestra como `st.caption` o texto normal debajo.

## Fuera de alcance (explícito)

- Análisis automático para todos los resultados de una búsqueda — sigue
  siendo bajo demanda, por diseño (costo/tiempo).
- Usar el resultado del matching para ordenar/filtrar la lista de
  resultados por score — posible mejora futura, no pedida ahora.
- Cachear el análisis en disco entre sesiones (hoy vive solo en
  `st.session_state`, se pierde al cerrar la pestaña/sesión) — no se
  pidió persistencia entre sesiones para esto.
- Usar `logros_y_experiencia` para generar el CV/CL en sí — eso es fase 3
  (personalización), un trabajo separado.

## Testing

- Probar `analizar_match` de forma standalone contra un perfil de prueba
  y una oferta real, confirmando que devuelve un dict con `score` (int)
  y `explicacion` (str) no vacíos.
- Probar el caso de mismatch obvio (perfil junior Python vs oferta senior
  Java) y confirmar que el score sale bajo — ya verificado manualmente
  contra la API real en la fase de diseño (score 20 para ese caso).
- Verificación manual en el navegador: buscar ofertas, analizar el match
  de 2-3 tarjetas distintas, confirmar que cada una mantiene su propio
  resultado, que la lista completa de resultados no desaparece al
  analizar una tarjeta, y que un error en una tarjeta no rompe las demás.
