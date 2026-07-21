# HuntJob Chile — Personalización real de CV/Cover Letter (fase 3)

**Fecha:** 2026-07-21
**Estado:** Aprobado por el usuario, pendiente de plan de implementación

## Contexto

El perfil de usuario (fase 1) guarda `anos_experiencia`, `seniority`,
`stack_principal` y `logros_y_experiencia`. El matching (fase 2) y el
asistente de formularios ya usan esos campos para dar respuestas
fundadas en datos reales. Los prompts de generación de CV y Cover Letter
en `app.py` (sección "Generador por URL"), en cambio, todavía no leen
nada del perfil salvo el `nombre` para la firma — y peor, el prompt del
CV tiene **hardcodeado** `"enfocado en Python, arquitectura backend y
automatización"`, un supuesto genérico que quedó de antes de que
existiera el perfil. Esto significa que hoy el CV generado no refleja la
experiencia real del usuario, y además asume incorrectamente que
cualquier usuario de la app es un desarrollador Python backend.

## Objetivo

Que los prompts de CV y Cover Letter usen el perfil real (años de
experiencia, seniority, stack principal, logros y experiencia) en vez de
texto genérico hardcodeado, para que el contenido generado refleje a la
persona real detrás del perfil.

## Diseño

En `app.py`, sección "Generador por URL", justo antes de armar
`prompt_cv`/`prompt_cover`, se construye el mismo `contexto_perfil` que ya
usan `analizar_match` y `sugerir_respuesta` en `core/motor_ia.py`:

```python
contexto_perfil = (
    f"Años de experiencia: {perfil.get('anos_experiencia', 0)}\n"
    f"Nivel: {perfil.get('seniority', '')}\n"
    f"Stack principal: {perfil.get('stack_principal', '')}\n"
    f"Logros y experiencia: {perfil.get('logros_y_experiencia', '')}"
)
```

**`prompt_cv`:** se elimina el `"enfocado en Python, arquitectura backend
y automatización"` hardcodeado. En su lugar, el prompt incluye
`contexto_perfil` completo y pide explícitamente que el extracto se base
en el stack y los logros reales del candidato, seleccionando solo lo que
sea relevante para la oferta puntual — no todos los logros, y nada
inventado que no esté en el perfil.

**`prompt_cover`:** mismo `contexto_perfil` agregado, con instrucción de
mencionar como máximo un logro concreto real (si el perfil tiene
`logros_y_experiencia` cargado) que calce con la oferta, en vez de
lenguaje genérico de relleno.

**Perfil vacío/incompleto:** si `stack_principal`/`logros_y_experiencia`
están vacíos, el prompt igual funciona — Gemini simplemente tiene menos
contexto real para trabajar, mismo criterio de degradación gradual ya
usado en el resto de la app (no se bloquea la generación).

## Fuera de alcance (explícito)

- Cambiar el mecanismo de generación (sigue siendo `generar_texto`, texto
  libre — no se necesita el modo JSON estructurado acá, a diferencia de
  `analizar_match`/`sugerir_respuesta`).
- Tocar `core/generador_pdf.py` o el flujo de descarga — sin cambios.
- Agregar campos nuevos al perfil.
- Deduplicación de resultados o chat asistente — fases separadas.

## Testing

- Generar un CV real de prueba con un perfil que tenga `stack_principal`
  y `logros_y_experiencia` completos, y confirmar que el extracto
  generado menciona contenido relacionado con esos logros reales (no
  genérico "Python, arquitectura backend" si el perfil de prueba usa un
  stack distinto).
- Generar con un perfil vacío (sin logros) y confirmar que igual produce
  un extracto razonable, sin errores.
- Verificación manual en el navegador: flujo completo real
  (URL → detectar cargo → generar CV/CL → PDF), confirmando que el
  contenido del PDF refleja el perfil real cargado.
