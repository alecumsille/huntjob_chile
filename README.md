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
├── app.py                  # Interfaz Streamlit
├── core/
│   ├── scraper_web.py      # Extracción de oferta puntual + búsqueda por portal
│   ├── portales.py         # Dispatcher multi-portal (registro + búsqueda agregada)
│   ├── motor_ia.py         # Generación de texto vía Gemini (Google AI)
│   └── generador_pdf.py    # Compilación de CV / Cover Letter en PDF
└── requirements.txt
```

## Notas de mantenimiento

El módulo `core/scraper_web.py` depende de selectores CSS actuales de cada portal (`article.box_offer` en Computrabajo, `div.job-item` en ChileTrabajos). Si un sitio cambia su estructura HTML, la búsqueda de ese portal dejará de devolver resultados y la función correspondiente lo señalará explícitamente vía `ErrorScraping` — el punto a revisar es la sección de selectores dentro de esa función.

## Roadmap

- Sumar más portales livianos (sin necesidad de navegador) al diccionario `PORTALES` en `core/portales.py`.
- Evaluar agregar Playwright como dependencia si en algún momento se justifica soportar portales protegidos por Cloudflare (Laborum, Indeed, GetOnBrd).
- App para Android: fase separada, sin alcance ni fecha definidos todavía.
