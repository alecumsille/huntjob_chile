# 📌 CONTEXTO COMPLETO Y HANDOVER TÉCNICO — HUNTJOB CHILE

Este documento contiene toda la arquitectura, credenciales, decisiones técnicas y estado actual de la plataforma **HuntJob Chile** (desarrollada para **Cumsille Systems Suite SpA**). Entrega este archivo a cualquier modelo de IA (Claude, ChatGPT, DeepSeek, Gemini) para continuar el desarrollo sin perder continuidad.

---

## 🌐 1. DOMINIOS Y DESPLIEGUE EN PRODUCCIÓN

- **Sitio Web Oficial en Vivo:** `https://huntjob.cumsille.me` (SSL HTTPS Activo)
- **Sitio Web Corporativo:** `https://cumsille.tech`
- **Plataforma de Hosting:** **Render.com** (Servidor en contenedor Docker nativo con CNAME configurado desde Namecheap).
- **Repositorio Oficial de GitHub (Público / Licencia MIT):** `https://github.com/alecumsille/huntjob_chile`
- **Estructura del Proyecto:** Proyecto fusionado que integra la suite de interfaz web + el demonio de automatización y deduplicación `JobHunter Engine`.

---

## 🔑 2. CREDENCIALES Y CONFIGURACIÓN DEL SISTEMA

### **Supabase (Backend de Autenticación & OAuth)**
- **Supabase URL:** `https://oonkwgfawfyqtrndshhu.supabase.co`
- **Supabase Anon Key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9vbmt3Z2Zhd2Z5cXRybmRzaGh1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ2NTkwMDEsImV4cCI6MjEwMDIzNTAwMX0.dRpV8vHk5Dg5oXaoJLeiToazkTv1uh8Cbb7ZFI_tudc`
- **Supabase Admin Service Token:** `sbp_************************************` (Configurado en variables de entorno)
- **OAuth Providers Configurados:**
  - **Google OAuth:** Client ID `119749436163-70aaoeqjgu5109jpev227pgm14lruu9o.apps.googleusercontent.com`
  - **GitHub OAuth:** Client ID `Ov23lifDvVuXMPktsmU0`
  - **Facebook OAuth:** App ID `1062967339642692`
  - **Callback Redirect URI autorizada:** `https://oonkwgfawfyqtrndshhu.supabase.co/auth/v1/callback`
  - **Redirect Target:** `https://huntjob.cumsille.me`

### **Motores de Inteligencia Artificial**
- **Motor Principal:** Google Gemini 2.0 (`gemini-2.0-flash-lite`) vía `GEMINI_API_KEY`.
- **Motor Fallback (Cero Caídas):** Groq API (`llama-3.3-70b-versatile`) vía `GROQ_API_KEY`.
- **Arquitectura de Fallback:** Si Gemini responde `429 (Rate Limit)` o falla la conexión, la aplicación commuta automáticamente a Groq sin interrumpir la experiencia del usuario.

---

## 🏗️ 3. ARQUITECTURA DEL CÓDIGO Y ESTRUCTURA DE ARCHIVOS

```
huntjob_chile/
├── app.py                      # Interfaz web principal (Streamlit) con navegación y autenticación
├── desktop.py                  # Envoltorio nativo de escritorio (GTK/WebKit) para Linux Mint/Ubuntu
├── Dockerfile                  # Contenedor optimizado de producción en Python 3.12-slim
├── LICENSE                     # Licencia MIT a nombre de Alejandro Cumsille
├── README.md                  # Documentación ejecutiva del producto con badges y gráficos
├── assets/                     # Recursos gráficos:
│   ├── icon.png                # Logo oficial de la app (lupa feliz)
│   ├── chile.png               # Bandera chilena (con multiply blend mode)
│   ├── css_logo.png            # Logo oficial de Cumsille Systems Suite
│   ├── google.png              # Icono oficial Icons8 transparente
│   ├── github.png              # Icono oficial Icons8 transparente
│   └── facebook.png            # Icono oficial Icons8 transparente
├── core/
│   ├── scraper_web.py          # Scraping y parsing HTML/API de portales de empleo
│   ├── portales.py             # Dispatcher multicanal tolerante a fallos
│   ├── motor_ia.py             # Generación de texto + Auditoría ATS (Score 0-100%, fortalezas, palabras clave)
│   ├── generador_pdf.py        # Compilación ReportLab en PDF con 4 temas (Pastel, Ejecutivo, Dark, Esmeralda)
│   ├── perfil.py               # Gestión aislada de perfil en session_state y YAML
│   ├── db.py                   # Persistencia relacional SQLite para el historial
│   ├── job_hunter_bot.py       # Demonio de rastreo en segundo plano (fusionado)
│   └── sync_mis_empleos.py     # Sincronizador de postulación multicanal (fusionado)
└── perfil/
    └── mi_perfil.yaml          # Configuración del perfil de usuario activo
```

---

## 🛠️ 4. FUNCIONALIDADES COMPROBADAS Y ACTIVAS

1. **Buscador Multi-Portal en Tiempo Real:**
   - Indexa simultáneamente en **Get on Board, Chiletrabajos, Trabajando, Laborum y LinkedIn**.
   - Los errores de un portal individual no detienen los resultados de los demás.

2. **Auditoría de Compatibilidad ATS (Score 0-100%):**
   - El botón *"Analizar match ATS"* calcula el porcentaje de afinidad con la vacante.
   - Desglosa **Fortalezas detectadas**, **Palabras clave faltantes en tu CV** y **Acciones de optimización**.

3. **Generador de CVs & Cover Letters en PDF:**
   - Generación adaptada según la vacante seleccionada o URL ingresada.
   - Permite descargar PDF con 4 paletas de diseño profesional.

4. **Autenticación & Manejo de Sesiones:**
   - Botón de **"Cerrar Sesión"** en la barra lateral que limpia el `st.session_state` y devuelve a la pantalla de ingreso social.
   - Botón **"Limpiar campos del perfil"** en la pestaña *Mi Perfil* para vaciar datos personales de forma segura.

5. **Alineación de Marca & Open Graph:**
   - Inyección dinámica en el `<head>` del DOM para mostrar la vista previa con el logo de la lupa feliz al compartir la URL `https://huntjob.cumsille.me` en WhatsApp, Telegram o LinkedIn.

---

## 📋 5. GUÍA RÁPIDA DE COMANDOS DE DESARROLLO

```bash
# Entrar al proyecto y activar entorno virtual
cd /home/ale/gestor_cv_pro/huntjob_chile
source venv/bin/activate

# Probar la aplicación en local
streamlit run app.py

# Verificar sintaxis
python -c "import app"

# Git Push a producción
git add .
git commit -m "update: descripción del cambio"
git push origin main
```

---

## 🎯 6. ROADMAP & PRÓXIMOS PASOS RECOMENDADOS

1. **Agregar más portales al scraper:** Incorporar scrapers para *Indeed Chile* y *TrabajoConSentido*.
2. **Bot de Postulación Masiva en 1-Clic:** Integrar Playwright Go para automatizar el llenado de formularios simples en Get on Board.
3. **Módulo de Analítica de Postulaciones:** Mostrar un gráfico interactivo en Streamlit con la tasa de conversión de postulaciones y respuestas recibidas.
