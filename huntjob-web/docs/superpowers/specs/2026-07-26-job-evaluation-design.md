# Evaluación A-F de ofertas de trabajo

## Problema

HuntJob Web permite postular a una oferta (`/api/apply`) con un CV tailorado automáticamente, pero no ayuda al usuario a decidir **si vale la pena postular en primer lugar**. El usuario pega cualquier URL y el sistema scrapea + tailora + aplica, sin ningún filtro de calidad de la oferta antes de gastar tiempo (o créditos de IA) en ella.

Existe además un módulo (`src/lib/ai/ats-scorer.ts`) que ya calcula un score de match CV-vs-oferta en 4 dimensiones (hard skills, seniority, formación, soft skills) — pero no está conectado a ninguna pantalla ni endpoint. Es trabajo real ya hecho, sin usar.

Inspirado en el proyecto open source `career-ops` (github.com/santifer/career-ops — un kit de skills para CLIs de IA, no una librería instalable), este feature busca dar al usuario un filtro real: una evaluación estructurada de la oferta *antes* de decidir postular, con la misma filosofía de career-ops: "esto es un filtro, no spray-and-pray — no vale la pena postular a todo".

## Objetivo

Agregar un paso de evaluación opcional-pero-recomendado antes de postular: el usuario pega la URL de una oferta, el sistema la evalúa en 6 bloques + un séptimo bloque de detección de ofertas sospechosas/falsas, y le da un score 1.0-5.0. Desde ese reporte, el usuario puede decidir postular (reutilizando el flujo de tailoring de CV ya existente) o descartar la oferta.

## Diseño

### Arquitectura

**Nueva tabla `job_evaluations`** (Supabase):

```sql
CREATE TABLE IF NOT EXISTS job_evaluations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  job_url TEXT NOT NULL,
  company_name TEXT NOT NULL,
  job_title TEXT NOT NULL,
  jd_raw TEXT NOT NULL,
  overall_score NUMERIC(2,1) NOT NULL CHECK (overall_score >= 1.0 AND overall_score <= 5.0),
  blocks JSONB NOT NULL,
  is_suspicious BOOLEAN NOT NULL DEFAULT false,
  suspicious_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE applications ADD COLUMN IF NOT EXISTS evaluation_id UUID REFERENCES job_evaluations(id);
```

Se guarda **desacoplada** de `applications`: el usuario evalúa muchas ofertas, postula a pocas. `applications.evaluation_id` es un link opcional hacia la evaluación que originó esa postulación (nullable, ya que las postulaciones existentes sin evaluar siguen siendo válidas).

**Nuevo endpoint `POST /api/evaluate`** (`src/app/api/evaluate/route.ts`), siguiendo exactamente el mismo patrón de seguridad que `/api/apply/route.ts`:
1. Auth check (401 si no hay sesión).
2. Gate de créditos IA (403 si `ai_credits_used >= ai_credits_limit`) — **antes** de scrapear/llamar IA, igual que `/api/apply`.
3. Valida que la URL sea de un dominio permitido (reutiliza la misma lista `ALLOWED_DOMAINS` de `/api/apply`).
4. Scrapea la oferta con `scrapeJobOffer` (reutilizado de `@/lib/scraper/extractor`).
5. Sanitiza el contenido scrapeado con `sanitizer.ts` (mismo anti-prompt-injection que ya existe).
6. Ejecuta 2 llamadas de IA (detalladas abajo).
7. Calcula el score final, guarda la fila en `job_evaluations`, descuenta **1 crédito** (no 2, aunque sean 2 llamadas de IA internas), retorna el reporte completo.

**Las 2 llamadas de IA:**
- **Bloque "CV Match"**: reutiliza `evaluateATS()` de `src/lib/ai/ats-scorer.ts` **tal cual**, sin modificarlo. Su `overallScore` (0-100) se normaliza a escala 1.0-5.0 para integrarlo al resto (`score_5 = 1.0 + (overallScore / 100) * 4.0`).
- **Los otros 6 bloques**, en un solo `generateObject` nuevo (`src/lib/ai/job-evaluator.ts`), reutilizando `executeWithFallback` de `src/lib/ai/provider.ts` (mismo fallback OpenAI→Gemini que ya usa el resto de la app):
  - **Resumen del rol**: qué hace el puesto, en 2-3 frases, en lenguaje simple.
  - **Estrategia de nivel**: si el nivel pedido (junior/semi-senior/senior) calza con el perfil del usuario, y si conviene negociar hacia arriba o hacia abajo.
  - **Investigación salarial**: rango de mercado estimado para el rol/ubicación/seniority (con disclaimer de que es una estimación de la IA, no un dato verificado).
  - **Personalización**: qué ángulo específico del perfil del usuario destacar para esta oferta en particular.
  - **Prep de entrevista (STAR+R)**: 2-3 preguntas de entrevista probables para este rol específico, con una sugerencia de qué tipo de historia STAR+R traer para cada una (sin generar el banco de historias completo — eso es el feature #5, fuera de este spec).
  - **Bloque G (legitimidad)**: `is_suspicious: boolean` + `reason: string | null`. Señales a evaluar: antigüedad excesiva de la publicación (si el scraper la expone), ausencia total de rango salarial combinada con urgencia excesiva en el texto, descripciones genéricas/copy-paste sin detalles reales del equipo o stack, solicitud de datos personales sensibles antes de una entrevista real.

**Score final**: promedio ponderado de los 6 bloques puntuables (CV Match 30%, Estrategia de Nivel 15%, Investigación Salarial 15%, Personalización 15%, Resumen del Rol/interés 15%, Prep de Entrevista 10%). El Bloque G no puntúa — solo marca `is_suspicious`, mostrado como alerta separada, sin ocultar ni afectar el score numérico.

**Nueva pantalla `/dashboard/evaluate`**: input de URL → reporte con score grande + los 6 bloques expandibles + banner de alerta si `is_suspicious` → botón "Aplicar con CV tailorado para esta oferta", que llama a `/api/apply` pasando `evaluation_id` en el body para que quede linkeada.

### Manejo de errores

- Scraping falla (dominio no permitido, timeout, oferta ya no existe): mismo comportamiento que `/api/apply` hoy — error claro, sin descontar crédito.
- JD extraída demasiado corta/vacía (< 100 caracteres útiles tras sanitizar): error explícito ("no se pudo extraer suficiente contenido de la oferta para evaluarla"), sin descontar crédito.
- Falla de IA (ambos proveedores caídos vía `executeWithFallback`): error claro, sin descontar crédito.
- Límite de créditos alcanzado: 403 con el mismo mensaje/patrón ya usado en `/api/apply`.
- Rate limiting: `/api/evaluate` se agrega al grupo de rutas de IA en `middleware.ts` (5/min), igual que `/api/apply` y `/api/cv/parse`.

### Testing

Sin framework de tests automatizados para rutas de IA en esta app (se valida con Zod schemas + verificación manual, mismo patrón ya establecido). Plan de verificación manual:
1. Evaluar una oferta real de un dominio permitido (ej. getonbrd.com) y confirmar que devuelve los 7 bloques + un score 1.0-5.0 coherente.
2. Confirmar que se descuenta exactamente 1 crédito por evaluación completa (no 2), revisando `ai_credits_used` antes/después en Supabase.
3. Provocar un caso sospechoso (JD con urgencia excesiva y sin rango salarial) y confirmar que el Bloque G lo marca con un motivo concreto, y que el banner aparece sin ocultar el score.
4. Desde una evaluación, usar "Aplicar con CV tailorado" y confirmar que la fila resultante en `applications` tiene `evaluation_id` seteado correctamente.
5. Confirmar que si el límite de créditos ya está alcanzado, `/api/evaluate` devuelve 403 sin scrapear ni llamar IA.

## Fuera de alcance

- Los otros 4 features inspirados en career-ops (carta de presentación, borrador de email, descubrimiento de contacto, banco de historias STAR+R) — cada uno es su propio spec/plan separado, a diseñar después.
- No se modifica `ats-scorer.ts` — se reutiliza tal cual.
- No se persiste ni se re-evalúa automáticamente una oferta ya evaluada (si el usuario pega la misma URL de nuevo, se crea una nueva fila en `job_evaluations` y se gasta otro crédito — no hay caché ni deduplicación en esta primera versión).
- La investigación salarial es una estimación de la IA, no se integra con ninguna API de datos salariales real (ej. Levels.fyi, Glassdoor) — puede ser una iteración futura si se nota que la estimación es poco confiable.
