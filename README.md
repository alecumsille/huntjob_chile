# HuntJob Chile

Herramienta local para postulaciones: extrae el contenido de una oferta laboral desde su URL, genera CV y Cover Letter adaptados usando Gemini (Google AI), y compila los PDFs. Incluye buscador de vacantes reales en múltiples portales chilenos.

## Requisitos

- Python 3.10+
- Una API key de Gemini, gratis en [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

## Instalación

```bash
git clone https://github.com/alecumsille/huntjob_chile.git
cd huntjob_chile
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY=tu-key-de-gemini
```

## Uso

```bash
streamlit run app.py
```

`GEMINI_API_KEY` tiene que estar exportada en la sesión de terminal donde corre `streamlit run app.py` (o agregada al `.bashrc`/`.zshrc` para que persista). Sin esa variable, la sección "Generador por URL" falla con un mensaje explícito indicando cómo conseguirla — el buscador de vacantes no depende de ella y sigue funcionando igual.

## App de escritorio (Linux)

Probado en Linux Mint 22 (base Ubuntu/Debian). Abre la app en una ventana
nativa propia (GTK/WebKit) en vez de una pestaña del navegador, con un
lanzador en el menú de aplicaciones.

```bash
./instalar_escritorio.sh
```

Esto instala las dependencias del sistema que hagan falta (`python3-gi`,
GTK, WebKit2 — necesarias para la ventana nativa, no se pueden instalar
solo con `pip`), ajusta el entorno virtual para que pueda verlas, instala
`pywebview`, y agrega "HuntJob Chile" al menú de aplicaciones con su
propio ícono (`assets/icon.png`). Si `GEMINI_API_KEY` no está exportada,
la app de escritorio la busca automáticamente en `~/.gemini_key`.

También se puede correr directo sin pasar por el menú:

```bash
source venv/bin/activate
python3 desktop.py
```

Cerrar la ventana (o matar el proceso) termina el servidor de Streamlit
que corre por detrás — no queda nada corriendo en segundo plano.

## Portales soportados

| Portal | Método |
|---|---|
| Computrabajo Chile | Scraping HTML (`requests` + `BeautifulSoup`) |
| ChileTrabajos | Scraping HTML (`requests` + `BeautifulSoup`) |

Un portal marca error sin bloquear a los demás: si Computrabajo o ChileTrabajos cambian su estructura o bloquean la búsqueda, el resto sigue funcionando y el error se muestra aparte en la interfaz.

Laborum, Indeed Chile y GetOnBrd se investigaron pero quedaron fuera de esta versión: los tres exigen un navegador real (protección Cloudflare o sesión vía JavaScript) en vez de una simple petición HTTP. Ver `docs/superpowers/specs/2026-07-21-multiportal-design.md` para el detalle técnico de esa decisión.

## Estructura

```
huntjob_chile/
├── app.py                          # Interfaz Streamlit
├── desktop.py                      # Envoltorio de escritorio (ventana nativa GTK/WebKit)
├── instalar_escritorio.sh          # Instalador del lanzador de escritorio
├── huntjob-chile.desktop.template  # Plantilla del lanzador (.desktop)
├── assets/
│   └── icon.png                    # Ícono de la app de escritorio
├── core/
│   ├── scraper_web.py      # Extracción de oferta puntual + búsqueda por portal
│   ├── portales.py         # Dispatcher multi-portal (registro + búsqueda agregada)
│   ├── motor_ia.py         # Generación de texto vía Gemini (Google AI)
│   ├── generador_pdf.py    # Compilación de CV / Cover Letter en PDF
│   └── perfil.py           # Perfil de usuario (perfil/mi_perfil.yaml, no versionado)
├── .streamlit/
│   └── config.toml         # Tema visual base (paleta pastel rosado + celeste)
└── requirements.txt
```

La app además rota entre 4 variantes pastel (fondo, sidebar, botón principal) cada hora, vía un CSS mínimo inyectado en `app.py` — el theme de `config.toml` es fijo por proceso, no soporta cambios programados por sí solo.

## Mi Perfil

Tab en la app donde se completa un perfil real (nombre, años de experiencia,
seniority, stack principal, logros) que se guarda localmente en
`perfil/mi_perfil.yaml` (no se commitea, es información personal). Por ahora
solo se usa para firmar la Cover Letter con tu nombre real; las próximas
fases lo van a usar también para calcular qué tan buen fit es cada oferta
encontrada y para personalizar mucho más el contenido generado.

## Notas de mantenimiento

El módulo `core/scraper_web.py` depende de selectores CSS actuales de cada portal (`article.box_offer` en Computrabajo, `div.job-item` en ChileTrabajos). Si un sitio cambia su estructura HTML, la búsqueda de ese portal dejará de devolver resultados y la función correspondiente lo señalará explícitamente vía `ErrorScraping` — el punto a revisar es la sección de selectores dentro de esa función.

## Roadmap

**Corto plazo (app personal, en curso):**

- Perfil de usuario editable (tab "Mi Perfil") como base para matching de ofertas contra el perfil real, y para CVs/Cover Letters mucho más personalizados que hoy.
- Deduplicación de resultados cuando la misma vacante aparece en más de un portal.
- Asistente conversacional para preguntar sobre las ofertas encontradas o la estrategia de búsqueda.
- Sumar más portales livianos (sin necesidad de navegador) al diccionario `PORTALES` en `core/portales.py`.
- Evaluar agregar Playwright como dependencia si en algún momento se justifica soportar portales protegidos por Cloudflare (Laborum, Indeed, GetOnBrd).
- App para Android: fase separada, sin alcance ni fecha definidos todavía.

**Idea a largo plazo (si algún día se lanza como producto público, no decidido):**

Convertir HuntJob Chile en un sitio multiusuario es un proyecto aparte, no una
extensión incremental de la app actual — implica hosting público, apps OAuth
registradas con cada proveedor, base de datos de usuarios, pasarela de pago
y política de privacidad para datos de terceros. Ideas anotadas para cuando
(si) se decida encarar eso:

- Registro/login con Google, GitHub, Facebook o email.
- Recomendación de ofertas a partir de un CV subido por el usuario, sin
  almacenar ese CV — remarcado como garantía de privacidad en el sitio.
- Funciones "pro" de pago, posibles candidatas:
  - Alertas automáticas (diarias/semanales) de ofertas nuevas que matchean el perfil.
  - Acceso a portales que requieren Playwright (Laborum, Indeed, GetOnBrd).
  - Historial y tracking de postulaciones (a qué ofertas ya postulaste y en qué estado).
  - Múltiples perfiles/CVs para postular a distintos tipos de roles.
  - Generación ilimitada de CVs/Cover Letters vs. un límite mensual en el plan gratis.
  - Análisis de brecha de habilidades: qué te falta para calzar mejor con las ofertas que te interesan.
