# Suscripción Premium vía Flow.cl — diseño

## Contexto

HuntJob Chile ya tiene la infraestructura de planes construida: la tabla
`planes_usuario` en Supabase distingue `free` (5 generaciones/mes) de
`premium` (ilimitado), y `core/db.py::verificar_y_consumir_uso` ya aplica
ese límite. Lo único que falta es la forma de que un usuario realmente
se vuelva premium — hoy el mensaje "Pásate a Premium" no lleva a ningún
lado. Este spec cubre solo esa pieza: cobrar y activar/desactivar el
plan premium automáticamente.

Decisiones ya tomadas con Alejandro:
- Modelo de cobro: **suscripción mensual recurrente**, no pago único ni
  créditos prepagados.
- Pasarela: **Flow.cl** (Webpay/débito, estándar chileno — Stripe no
  cubre débito local, que es como paga la mayoría del público objetivo).
- Precio: **$4.990 CLP/mes**.
- Cuenta de comercio en Flow.cl: a crear (no existe todavía).

## Arquitectura

Streamlit (donde vive `app.py`) no puede exponer rutas HTTP propias —
solo renderiza una página vía websocket. Flow.cl necesita un webhook
server-to-server para confirmar pagos y renovaciones (no es opcional:
es la única fuente de verdad confiable, un redirect de navegador no
alcanza porque el usuario puede cerrar la pestaña antes de volver).

Por eso el trabajo se divide en dos piezas, siguiendo el mismo patrón
que ya usa el resto del ecosistema (GatitoPro, nimarco_erp,
dashboard_central: microservicios Flask chicos y aislados por tarea):

1. **`app.py` (existente, se extiende):** agrega un botón "Actualizar a
   Premium" en el sidebar, donde hoy solo se muestra la barra de
   progreso del plan gratuito. Al hacer clic, llama a la API de Flow
   para crear el pago/suscripción y redirige el navegador a la página
   de pago hospedada por Flow. Esto es una llamada saliente + redirect,
   Streamlit lo puede hacer sin problema.

2. **Nuevo microservicio Flask (`huntjob_payments` o similar, a
   definir el nombre exacto en el plan de implementación):** una sola
   ruta, `POST /webhook/flow`, que Flow llama cuando se aprueba/falla
   un cobro. Verifica la firma HMAC con el secreto de Flow, y actualiza
   `planes_usuario` en Supabase usando la **Service Role Key** (no hay
   usuario logueado en ese momento, es una llamada server-to-server —
   por eso necesita bypasear RLS con esta key, que nunca debe vivir en
   `app.py` ni en ningún `.env` compartido con el resto del ecosistema).
   Se despliega como un segundo servicio web en Render (mismo lugar
   donde ya vive HuntJob Chile), separado del proceso de Streamlit.

## Datos

Se agregan 2 columnas a `planes_usuario` (tabla existente en
`sql/schema.sql`):

- `flow_customer_id text` — identifica de quién es cada webhook que
  llega de Flow (Flow no conoce nuestro `user_id` de Supabase
  directamente, hay que mapearlo).
- `plan_vence_en timestamptz` — hasta cuándo sigue vigente el premium
  actual. Si una renovación falla y esta fecha se pasa, el plan baja a
  `free` automáticamente (chequeado en `obtener_plan`/
  `verificar_y_consumir_uso`, igual que hoy se chequea `periodo`).

## Ciclo de vida de la suscripción (eventos de Flow)

1. **Pago aprobado** (primera vez o renovación mensual): `plan =
   premium`, `plan_vence_en` se extiende un mes.
2. **Pago fallido**: Flow reintenta automáticamente según su propia
   política de reintentos — no hacemos nada nosotros en este evento,
   solo lo logueamos.
3. **Suscripción cancelada** (agotados los reintentos de Flow, o
   cancelación manual del usuario): `plan = free` inmediato.

Cancelación manual: se agrega un botón "Cancelar suscripción" en el
sidebar (visible solo si `plan == premium`) que llama a la API de Flow
para cancelar, y espera la confirmación por webhook antes de reflejar
el cambio (no se baja el plan de forma optimista en el momento del
clic, para no desincronizarse si la cancelación en Flow fallara).

## Manejo de errores

- Firma de webhook inválida → responder 401, no tocar la base de datos.
- Webhook de un `flow_customer_id` que no existe en `planes_usuario` →
  loguear como error y responder 200 igual (para que Flow no reintente
  indefinidamente algo que nunca va a resolver), sin lanzar excepción.
- Webhooks duplicados (Flow puede reenviar el mismo evento más de una
  vez, es un caso normal de webhooks) → la actualización es un
  `upsert` sobre `user_id`, no una suma ni un contador — recibir el
  mismo evento 2 veces dejaría el mismo estado final, no hay
  duplicación de efecto.
- El redirect de vuelta al navegador (`urlReturn` de Flow) es solo para
  mostrar "¡Listo, ya sos premium!" — nunca es la fuente de verdad del
  cambio de plan, eso lo decide únicamente el webhook.

## Testing y rollout

Flow.cl ofrece un ambiente sandbox con tarjetas de prueba, independiente
de la cuenta de comercio real. Plan:

1. Construir e integrar todo contra el sandbox de Flow mientras se
   tramita la aprobación de la cuenta de comercio real (que puede
   tardar).
2. Probar el flujo completo en sandbox: crear suscripción, simular
   pago aprobado, simular pago fallido, cancelar.
3. Recién al final, cuando la cuenta real esté aprobada, cambiar las
   credenciales de sandbox a producción y hacer una prueba con un pago
   real de bajo monto antes de anunciarlo.

## Fuera de alcance de este spec

- Facturación/boletas electrónicas (SII) — no se cubre acá, solo el
  cobro. Si más adelante hace falta emitir boletas, es un spec aparte.
- Recuperación de pagos fallidos con reintentos propios (fuera de los
  que ya hace Flow) — no se construye lógica adicional de dunning.
- Cualquier otro feature de producto (notificaciones, más portales,
  analítica) — quedaron fuera de esta ronda, se abordan en specs
  separados si Alejandro decide seguir por ahí después de esto.
