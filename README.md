# 🚀 HuntJob Chile — Plataforma Inteligente de Empleos & Auditoría ATS

[![Sitio Web Oficial](https://img.shields.io/badge/Sitio_Web-huntjob.cumsille.me-blue?style=for-the-badge&logo=googlechrome&logoColor=white)](https://huntjob.cumsille.me)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Render](https://img.shields.io/badge/Despliegue-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)

**HuntJob Chile** es la suite de aceleración laboral diseñada para profesionales y talentos en Chile. Reúne en un solo lugar la búsqueda en tiempo real en los principales portales del país (**Get on Board, Chiletrabajos, Trabajando, Laborum y LinkedIn**), audita tu perfil contra las vacantes usando Inteligencia Artificial de última generación y genera currículums optimizados en PDF diseñados para superar los filtros **ATS (Applicant Tracking Systems)**.

---

## 🔥 ¿Por qué destaca HuntJob Chile frente a otras plataformas?

| Característica | Portales Tradicionales | Otras Apps con IA | **HuntJob Chile** |
|---|:---:|:---:|:---:|
| **Búsqueda Multi-Portal** | ❌ 1 solo portal por pestaña | ❌ Requiere copiar URLs a mano | **✅ Indexación agregada en tiempo real** |
| **Auditoría ATS en Vivo** | ❌ No disponible | ⚠️ Respuestas genéricas | **✅ Score 0-100%, fortalezas y palabras faltantes** |
| **Disponibilidad Indestructible** | ⚠️ Fallan si el servidor se satura | ❌ Bloqueo por límites de cuota (429) | **✅ Motor Híbrido Gemini + Groq (Llama 3.3 70B)** |
| **Exportación Ejecutiva** | ❌ Formatos básicos o planos | ❌ Cobros por descargar PDF | **✅ 4 plantillas visuales PDF de descarga gratuita** |
| **Privacidad & Aislamiento** | ⚠️ Venta de datos personales | ⚠️ Datos compartidos en la nube | **✅ Sesión aislada en memoria sin persistir tu CV** |

---

## ✨ Novedades & Funcionalidades Destacadas

- 🔍 **Indexación Multicanal en Tiempo Real:** Busca simultáneamente en los portales más importantes de Chile sin perder tiempo abriendo decenas de pestañas.
- 🎯 **Auditoría de Compatibilidad ATS:** Analiza el nivel de coincidencia de tu perfil con la vacante objetivo. Recibe un diagnóstico con:
  - Puntaje de compatibilidad (Score 0-100%).
  - Fortalezas detectadas en tu perfil.
  - Palabras clave y herramientas faltantes en tu CV.
  - Recomendaciones tácticas de optimización.
- ⚡ **Resiliencia & Cero Caídas de IA:** Implementa una arquitectura con fallback automático (Google Gemini 2.0 Flash -> Groq Llama 3.3 70B). Si una API alcanza su límite de cuotas, la otra toma el relevo de forma transparente.
- 📄 **Generador de CVs & Cover Letters en PDF:** Produce documentos estructurados, elegantes y listos para enviar en 4 paletas de diseño ejecutivo (Pastel, Ejecutivo, Minimalista Oscuro, Esmeralda).
- 🔒 **Social Auth & Sesión Segura:** Integración nativa de autenticación con Google, GitHub y Facebook vía Supabase.

---

## 🛠️ Requisitos del Sistema

- **Python 3.10+** (para ejecución local o servidores dedicados)
- **Docker** (para despliegue en contenedores)
- API Keys opcionales: `GEMINI_API_KEY`, `GROQ_API_KEY` (configurables en variables de entorno)

---

## 🚀 Instalación y Ejecución Local

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/alecumsille/huntjob_chile.git
   cd huntjob_chile
   ```

2. **Crear entorno virtual e instalar dependencias:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configurar claves de entorno (opcional):**
   ```bash
   export GEMINI_API_KEY="tu_clave_gemini"
   export GROQ_API_KEY="tu_clave_groq"
   ```

4. **Lanzar la aplicación:**
   ```bash
   streamlit run app.py
   ```

---

## 🐳 Ejecución con Docker

Si prefieres ejecutar la aplicación dentro de un contenedor o desplegarla en servicios como Render, Railway o Koyeb:

```bash
# Construir la imagen Docker
docker build -t huntjob-chile .

# Ejecutar el contenedor en el puerto 8501
docker run -p 8501:8501 -e GEMINI_API_KEY="tu_clave" huntjob-chile
```

---

## 💻 Aplicación de Escritorio (Linux)

Para usuarios de Linux Mint / Ubuntu que prefieren ejecutar HuntJob Chile como una aplicación nativa de escritorio:

```bash
./instalar_escritorio.sh
```
Esto creará el acceso directo en el menú de tu sistema con la ventana nativa (GTK/WebKit) y su ícono corporativo.

---

## 📄 Licencia & Créditos

Desarrollado con ❤️ para impulsar el talento en Chile.  
Sitio Oficial: [https://huntjob.cumsille.me](https://huntjob.cumsille.me)
