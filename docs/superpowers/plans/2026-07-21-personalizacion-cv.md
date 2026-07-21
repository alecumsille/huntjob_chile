# Personalización real de CV/Cover Letter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Los prompts de CV y Cover Letter en "Generador por URL" usan el perfil real (años de experiencia, seniority, stack principal, logros y experiencia) en vez del texto genérico hardcodeado "enfocado en Python, arquitectura backend y automatización".

**Architecture:** Un solo cambio contenido en `app.py`, sección "Generador por URL": se arma un `contexto_perfil` (mismo patrón ya usado en `core/motor_ia.py` para `analizar_match`/`sugerir_respuesta`) y se inyecta en `prompt_cv`/`prompt_cover`. No se toca `core/motor_ia.py` ni `core/generador_pdf.py` — sigue siendo texto libre vía `generar_texto`, no JSON estructurado.

**Tech Stack:** Python 3.10+, Streamlit, Gemini API (vía `generar_texto`, ya existente).

## Global Constraints

- No cambiar el mecanismo de generación: sigue siendo `generar_texto` (texto libre), no se introduce JSON estructurado acá.
- Perfil vacío/incompleto no debe bloquear la generación — Gemini simplemente tiene menos contexto, mismo criterio ya usado en el resto de la app.
- No se tocan `core/generador_pdf.py`, el flujo de descarga, ni se agregan campos nuevos al perfil.
- Cero emojis en código, UI y mensajes.

---

### Task 1: Inyectar el perfil real en los prompts de CV y Cover Letter

**Files:**
- Modify: `app.py:153-169` (sección "Generador por URL", bloque de armado de `prompt_cv`/`prompt_cover`)

**Interfaces:**
- Consumes: `perfil` (dict ya cargado vía `cargar_perfil()` más arriba en la misma sección, con keys `anos_experiencia`, `seniority`, `stack_principal`, `logros_y_experiencia`, `nombre`).

- [ ] **Step 1: Reemplazar el bloque de prompts**

En `app.py`, reemplazar:

```python
                    prompt_cv = (
                        f"Escribe ÚNICAMENTE el extracto de perfil profesional para un CV, en español, "
                        f"para el puesto de {puesto_objetivo} en {mercado_destino}, enfocado en Python, "
                        f"arquitectura backend y automatización. Un párrafo de 4 a 6 líneas, listo para "
                        f"pegar directo en un CV real, con las palabras clave técnicas relevantes para "
                        f"pasar filtros ATS. No agregues explicaciones, títulos, análisis de por qué "
                        f"funciona, consejos, ni ningún texto dirigido al candidato — solo el extracto en sí."
                    )
                    nombre_firma = perfil["nombre"] or "Candidato/a"
                    prompt_cover = (
                        f"Escribe ÚNICAMENTE el cuerpo de una Cover Letter en español, directa y sin rodeos, "
                        f"para el puesto de {puesto_objetivo} en {mercado_destino}. Firma con el nombre "
                        f"{nombre_firma}. No agregues explicaciones, análisis, ni ningún texto que no sea "
                        f"la carta en sí."
                    )
```

por:

```python
                    contexto_perfil = (
                        f"Años de experiencia: {perfil.get('anos_experiencia', 0)}\n"
                        f"Nivel: {perfil.get('seniority', '')}\n"
                        f"Stack principal: {perfil.get('stack_principal', '')}\n"
                        f"Logros y experiencia: {perfil.get('logros_y_experiencia', '')}"
                    )
                    prompt_cv = (
                        f"Escribe ÚNICAMENTE el extracto de perfil profesional para un CV, en español, "
                        f"para el puesto de {puesto_objetivo} en {mercado_destino}. Basate en el stack y "
                        f"los logros reales del candidato de abajo — seleccioná solo lo que sea relevante "
                        f"para esta oferta puntual, no listes todo, y no inventes nada que no esté en el "
                        f"perfil. Un párrafo de 4 a 6 líneas, listo para pegar directo en un CV real, con "
                        f"las palabras clave técnicas relevantes para pasar filtros ATS. No agregues "
                        f"explicaciones, títulos, análisis de por qué funciona, consejos, ni ningún texto "
                        f"dirigido al candidato — solo el extracto en sí.\n\n"
                        f"Perfil del candidato:\n{contexto_perfil}"
                    )
                    nombre_firma = perfil["nombre"] or "Candidato/a"
                    prompt_cover = (
                        f"Escribe ÚNICAMENTE el cuerpo de una Cover Letter en español, directa y sin rodeos, "
                        f"para el puesto de {puesto_objetivo} en {mercado_destino}. Si el perfil de abajo "
                        f"tiene logros o experiencia cargada, mencioná como máximo uno concreto que calce "
                        f"con esta oferta puntual, en vez de lenguaje genérico de relleno — si no hay logros "
                        f"cargados, escribí sin inventar ninguno. Firma con el nombre {nombre_firma}. No "
                        f"agregues explicaciones, análisis, ni ningún texto que no sea la carta en sí.\n\n"
                        f"Perfil del candidato:\n{contexto_perfil}"
                    )
```

- [ ] **Step 2: Verificar sintaxis**

Run: `cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate && python3 -c "import ast; ast.parse(open('app.py').read()); print('sintaxis OK')"`
Expected: `sintaxis OK`

- [ ] **Step 3: Prueba real con perfil completo (stack distinto a Python para confirmar que ya no está hardcodeado)**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
export GEMINI_API_KEY=$(cat /home/ale/.gemini_key)
python3 -c "
from core.motor_ia import generar_texto

perfil = {
    'nombre': 'César Alejandro Cumsille Sepúlveda',
    'anos_experiencia': 5,
    'seniority': 'Senior',
    'stack_principal': 'Node.js, TypeScript, React, PostgreSQL',
    'logros_y_experiencia': 'Lideré la migración de un monolito a microservicios en Node.js, reduciendo tiempos de deploy en 40 por ciento.',
}
puesto_objetivo = 'Desarrollador Full Stack'
mercado_destino = 'Chile'
contexto_perfil = (
    f\"Años de experiencia: {perfil.get('anos_experiencia', 0)}\n\"
    f\"Nivel: {perfil.get('seniority', '')}\n\"
    f\"Stack principal: {perfil.get('stack_principal', '')}\n\"
    f\"Logros y experiencia: {perfil.get('logros_y_experiencia', '')}\"
)
prompt_cv = (
    f'Escribe ÚNICAMENTE el extracto de perfil profesional para un CV, en español, '
    f'para el puesto de {puesto_objetivo} en {mercado_destino}. Basate en el stack y '
    f'los logros reales del candidato de abajo — seleccioná solo lo que sea relevante '
    f'para esta oferta puntual, no listes todo, y no inventes nada que no esté en el '
    f'perfil. Un párrafo de 4 a 6 líneas, listo para pegar directo en un CV real, con '
    f'las palabras clave técnicas relevantes para pasar filtros ATS. No agregues '
    f'explicaciones, títulos, análisis de por qué funciona, consejos, ni ningún texto '
    f'dirigido al candidato — solo el extracto en sí.\n\n'
    f'Perfil del candidato:\n{contexto_perfil}'
)
texto_oferta_prueba = 'Buscamos Desarrollador Full Stack con experiencia en Node.js, React y bases de datos relacionales.'
cv = generar_texto(prompt_cv, texto_oferta_prueba)
print(cv)
assert 'Node.js' in cv or 'React' in cv or 'TypeScript' in cv, 'esperaba que el CV mencione el stack real del perfil (Node.js/React/TypeScript), no Python generico'
assert 'Python' not in cv, 'el CV no deberia mencionar Python - el perfil de prueba no lo tiene, y el prompt ya no lo hardcodea'
print('OK: el CV refleja el stack real del perfil, no el hardcodeado anterior')
"
```
Expected: imprime el extracto de CV generado (debe mencionar Node.js/React/TypeScript, nunca Python) y termina con `OK: el CV refleja el stack real del perfil, no el hardcodeado anterior`.

- [ ] **Step 4: Prueba real con perfil vacío (no debe romper)**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
export GEMINI_API_KEY=$(cat /home/ale/.gemini_key)
python3 -c "
from core.motor_ia import generar_texto

perfil = {'nombre': '', 'anos_experiencia': 0, 'seniority': 'Junior', 'stack_principal': '', 'logros_y_experiencia': ''}
puesto_objetivo = 'Desarrollador Backend'
mercado_destino = 'Chile'
contexto_perfil = (
    f\"Años de experiencia: {perfil.get('anos_experiencia', 0)}\n\"
    f\"Nivel: {perfil.get('seniority', '')}\n\"
    f\"Stack principal: {perfil.get('stack_principal', '')}\n\"
    f\"Logros y experiencia: {perfil.get('logros_y_experiencia', '')}\"
)
prompt_cv = (
    f'Escribe ÚNICAMENTE el extracto de perfil profesional para un CV, en español, '
    f'para el puesto de {puesto_objetivo} en {mercado_destino}. Basate en el stack y '
    f'los logros reales del candidato de abajo — seleccioná solo lo que sea relevante '
    f'para esta oferta puntual, no listes todo, y no inventes nada que no esté en el '
    f'perfil. Un párrafo de 4 a 6 líneas, listo para pegar directo en un CV real, con '
    f'las palabras clave técnicas relevantes para pasar filtros ATS. No agregues '
    f'explicaciones, títulos, análisis de por qué funciona, consejos, ni ningún texto '
    f'dirigido al candidato — solo el extracto en sí.\n\n'
    f'Perfil del candidato:\n{contexto_perfil}'
)
texto_oferta_prueba = 'Buscamos Desarrollador Backend con experiencia en APIs REST.'
cv = generar_texto(prompt_cv, texto_oferta_prueba)
print(cv)
assert cv.strip(), 'no deberia devolver texto vacio con perfil incompleto'
print('OK: perfil vacio no rompe la generacion')
"
```
Expected: imprime un extracto de CV razonable (genérico, ya que no hay datos reales) y termina con `OK: perfil vacio no rompe la generacion`.

- [ ] **Step 5: Probar el flujo completo en el navegador**

Run:
```bash
cd /home/ale/gestor_cv_pro/huntjob_chile && source venv/bin/activate
export GEMINI_API_KEY=$(cat /home/ale/.gemini_key)
nohup streamlit run app.py --server.headless true --server.port 8501 > /tmp/streamlit_personalizacion_test.log 2>&1 &
disown
sleep 4
curl -s -o /dev/null -w "HTTP:%{http_code}\n" http://localhost:8501
```
Expected: `HTTP:200`. Con un navegador (o Playwright), ir a "Mi Perfil" y confirmar que el perfil guardado tiene `stack_principal`/`logros_y_experiencia` con datos reales (si no, completar unos de prueba y guardar). Ir a "Generador por URL", pegar una oferta real, generar CV y Cover Letter, y confirmar (leyendo el PDF resultante o el texto en pantalla) que el contenido menciona el stack/logros reales del perfil en vez de contenido genérico. Detener el servidor: `pkill -f "streamlit run app.py"`.

- [ ] **Step 6: Commit y push**

```bash
cd /home/ale/gestor_cv_pro/huntjob_chile
git add app.py
git commit -m "feat: personalizar CV/Cover Letter con el perfil real (stack, logros, experiencia)"
git push origin main
```

---

## Self-Review

**Spec coverage:**
- Eliminar el "enfocado en Python..." hardcodeado, usar `stack_principal` real → Task 1, Step 1.
- `contexto_perfil` con los mismos 4 campos que ya usan `analizar_match`/`sugerir_respuesta` → Task 1, Step 1.
- Seleccionar solo logros relevantes a la oferta puntual, sin inventar → instrucción explícita en ambos prompts, Task 1, Step 1.
- Perfil vacío no bloquea la generación → Task 1, Step 4 (prueba explícita de este caso).
- Fuera de alcance (JSON estructurado, generador_pdf.py, campos nuevos de perfil) → ninguna tarea lo toca, correcto.

**Placeholder scan:** sin TBD/TODO, código completo en todos los steps.

**Type consistency:** `contexto_perfil` se construye igual que en `core/motor_ia.py` (`analizar_match`/`sugerir_respuesta`), mismos nombres de campos del dict `perfil` (`anos_experiencia`, `seniority`, `stack_principal`, `logros_y_experiencia`) en los tres lugares del código.
