# Datos reales en dashboard, apply y postulaciones

## Problema

El dashboard principal (`src/app/dashboard/page.tsx`) usa datos falsos en dos lugares:
- El feed de "actividad reciente" es un array hardcodeado (Stripe, Vercel, Airbnb, Meta).
- El botón "Aplicar con IA" manda un `mockProfile` fijo a `/api/apply` en vez del perfil real del usuario logueado.

`src/app/dashboard/applications/page.tsx` sí consulta Supabase, pero si la consulta falla o devuelve cero filas, cae silenciosamente a `mockApplications` — un usuario nuevo ve postulaciones que no son suyas sin ningún aviso.

`/api/apply` (backend) ya está bien construido: valida auth real, valida dominio, adapta el CV con IA, e inserta en `applications` y `resumes` con el `user_id` real. El problema es exclusivamente en lo que el frontend le manda y le muestra.

No existe hoy ningún lugar donde el usuario cargue un CV base estructurado (experiencia, educación, skills) — la tabla `profiles` solo tiene campos planos de contacto (`full_name`, `phone`, `desired_role`, etc.), no arrays de experiencia/educación.

## Objetivo

Que el dashboard, el flujo de aplicar con IA y la página de postulaciones reflejen siempre datos reales del usuario — nunca placeholders — y que un usuario nuevo sin CV cargado pueda llegar a su primera postulación sin fricción.

## Decisión de diseño clave: de dónde sale el CV base

`resumes.cv_data` (JSONB) ya tiene exactamente la forma que necesita `/api/apply` (`CVData`: `personalInfo`, `summary`, `experience[]`, `education[]`, `skills[]`) — cada apply exitoso ya inserta una fila ahí. En vez de agregar columnas nuevas a `profiles` o una tabla nueva, **el CV base es el `resumes` más reciente del usuario** (`order by created_at desc limit 1`). Cero migración de esquema.

- Si el usuario ya tiene al menos un `resumes` → se usa el más reciente como `profile` real en el próximo apply.
- Si no tiene ninguno (usuario nuevo) → se activa el flujo de captura (ver abajo) antes de dejarlo aplicar. Ese primer CV capturado se guarda como su primer `resumes` y de ahí en adelante sigue la regla de arriba.

## A. Arquitectura / flujo de datos

```
Usuario aprieta "Aplicar con IA" en /dashboard
        │
        ▼
¿Tiene al menos 1 fila en resumes? ──No──► Flujo de captura de CV (sección B)
        │ Sí                                        │
        ▼                                            │ (al guardar, sigue abajo)
Usa resumes más reciente.cv_data como `profile`      │
        │◄───────────────────────────────────────────┘
        ▼
POST /api/apply { url, profile }   (ya existe, sin cambios)
```

Único endpoint nuevo: `POST /api/cv/parse` — recibe un PDF, devuelve `CVData` extraído por IA. No persiste nada; el guardado lo hace el cliente insertando directo en `resumes` (mismo patrón que ya usan `applications/page.tsx` y `settings/page.tsx` con el cliente Supabase del browser).

## B. Captura de CV base (primer uso)

**Endpoint `POST /api/cv/parse`:**
- Mismo patrón de auth que `/api/apply` (Supabase server client vía cookies, 401 si no hay sesión).
- Se agrega a `isAiRoute()` en `src/middleware.ts` para compartir el rate limit de rutas IA (5 req/min).
- Recibe `multipart/form-data` con el PDF. Valida `application/pdf` y tamaño máximo 5MB (mismo criterio que `validatePayloadSize` en `src/lib/security/sanitizer.ts`).
- El `CVSchema` (zod) hoy vive inline en `src/lib/ai/cv-adapter.ts` — se extrae a `src/lib/ai/cv-schema.ts` para reusarlo en ambos endpoints.
- Usa `executeWithFallback` (ya existe en `src/lib/ai/provider.ts`) + `generateObject` con el PDF como file-part multimodal directo a Gemini — sin agregar ninguna librería de parseo de PDF.
- Los campos de texto extraídos (`summary`, `achievements`) pasan por el detector de inyección de prompts ya existente en `src/lib/security/sanitizer.ts` antes de devolverse al cliente — mismo mecanismo que ya protege otras rutas, no es un sistema nuevo.
- No descuenta `ai_credits_used` (es onboarding único, no una postulación).
- Devuelve el `CVData` extraído (o parcialmente vacío si el PDF no se pudo leer — nunca un error duro que bloquee al usuario).

**UI — paso inline en `dashboard/page.tsx`** (sin agregar componente Dialog, no existe hoy en `src/components/ui/`):
1. Si el usuario aprieta "Aplicar con IA" y no tiene `resumes`, la tarjeta de "pegar URL" se reemplaza por un input de archivo PDF + botón "Analizar con IA".
2. Al volver el parse, se muestra un formulario editable pre-llenado (mismos componentes `Input`/`Textarea`/`Card` que ya usa `settings/page.tsx`): datos personales, resumen, experiencia (lista con agregar/quitar fila), educación (ídem), skills. Validación simple de campos requeridos (nombre, email) antes de guardar.
3. "Guardar y continuar" inserta en `resumes` (`name: "Mi CV Base"`, `cv_data`) vía el cliente Supabase del browser, y automáticamente continúa el `handleApply` original con ese `cv_data`.

Ese primer resume queda mezclado con los CVs adaptados en `/dashboard/resumes` — es solo otra fila, sin tabla ni flag especial.

## C. Dashboard principal — feed real + apply real

**Feed de actividad:** el `activities` state hardcodeado se reemplaza por un `useEffect` que hace `supabase.from('applications').select('*').eq('user_id', user.id).order('applied_at', {ascending:false}).limit(4)`, mapeado a la misma forma visual (rol/empresa/estado/tiempo-relativo/color según `status`). Sin datos → estado vacío real ("Aún no tienes postulaciones — pega una URL abajo para empezar"), nunca datos falsos.

**`handleApply`:** antes de llamar a `/api/apply`, consulta `resumes` más reciente del usuario.
- Hay resultado → se usa `cv_data` como `profile` (reemplaza `mockProfile`).
- No hay → dispara el flujo de captura de la sección B; al terminar, continúa automáticamente con el apply.

**Tiempo relativo:** no hay `date-fns` ni librería similar en el proyecto. Se agrega un helper propio (`formatRelativeTime`) en vez de sumar una dependencia nueva.

## D. Postulaciones — sacar el fallback fantasma

En `applications/page.tsx`, la lógica `if (error || !data || data.length === 0) setApplications(mockApplications)` se elimina junto con el array `mockApplications`. Nuevo comportamiento:
- Error real de Supabase → banner de error con botón "Reintentar".
- Sin error, cero filas → estado vacío ("Aún no registras postulaciones") usando el botón "Nueva Postulación" ya existente como CTA.

## E. Manejo de errores / edge cases

- **PDF ilegible o sin texto extraíble** (escaneado como imagen, no es un CV, corrupto): no bloquea al usuario — se muestra "No pudimos leer tu PDF, revisa el formulario y complétalo a mano" y se lo lleva igual al formulario editable (vacío o parcial).
- **Archivo inválido**: se valida `application/pdf` + tamaño máx. 5MB en cliente (antes de subir) y en el endpoint.
- **Inyección de prompt vía PDF**: cubierto arriba (sección B) reusando el sanitizador existente.
- **Doble submit**: botón deshabilitado mientras guarda (patrón `isSubmitting` ya usado en `applications` y `settings`).
- **Créditos de IA agotados**: se detectó que `/api/apply` hoy no tiene ningún gate de `ai_credits_limit` — incrementa el contador pero nunca bloquea. Es un hueco preexistente, fuera del alcance de este diseño; se deja anotado para una iteración aparte.
- **Campos requeridos vacíos** en el formulario de captura: validación simple antes de insertar.

## F. Testing

El repo no tiene framework de test instalado (ni jest ni vitest). Agregar uno para esta feature sería sobre-ingeniería para el tamaño del cambio, así que la verificación es manual en navegador real:

1. Usuario nuevo sin `resumes` → "Aplicar con IA" → aparece captura de PDF (no la URL directo).
2. Sube un PDF real de CV → se extrae y precarga el formulario → editar y guardar → queda en `resumes` y sigue el apply automáticamente.
3. Sube un PDF corrupto/no-CV → no rompe, cae al formulario vacío editable.
4. Usuario con `resumes` existentes → "Aplicar con IA" usa el último real, sin pasar por captura.
5. Dashboard: feed de actividad muestra postulaciones reales (o estado vacío) — cero nombres inventados.
6. `/dashboard/applications` con tabla vacía → estado vacío real; forzando un error de red → banner de error, nunca `mockApplications`.

## Fuera de alcance (anotado, no se hace acá)

- Gate de `ai_credits_limit` en `/api/apply` (hueco preexistente, no introducido por este cambio).
- Componente `Dialog` reusable — se optó por flujo inline en vez de modal.
- Editar o eliminar entradas individuales de experiencia/educación después de guardadas fuera del flujo de captura inicial (eso viviría en una futura pantalla de "editar mi CV base").
