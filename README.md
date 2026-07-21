# HuntJob Chile

Herramienta local para postulaciones: extrae el contenido de una oferta laboral desde su URL, genera CV y Cover Letter adaptados usando un modelo local vía Ollama, y compila los PDFs. Incluye buscador de vacantes reales en Computrabajo Chile.

## Requisitos

- Python 3.10+
- [Ollama](https://ollama.com) corriendo localmente con el modelo `phi3` instalado:

```bash
ollama pull phi3
ollama serve
```

## Instalación

```bash
git clone https://github.com/alecumsille/huntjob_chile.git
cd huntjob_chile
pip install -r requirements.txt
```

## Uso

```bash
streamlit run app.py
```

## Estructura

```
huntjob_chile/
├── app.py                  # Interfaz Streamlit
├── core/
│   ├── scraper_web.py      # Extracción de oferta puntual + búsqueda en Computrabajo
│   ├── motor_ia.py         # Generación de texto vía Ollama (phi3)
│   └── generador_pdf.py    # Compilación de CV / Cover Letter en PDF
└── requirements.txt
```

## Notas de mantenimiento

El módulo `core/scraper_web.py` depende de los selectores CSS actuales de Computrabajo (`article.box_offer` y derivados). Si el sitio cambia su estructura HTML, la búsqueda dejará de devolver resultados y `buscar_ofertas_computrabajo` lo señalará explícitamente en el traceback — el punto a revisar es la sección de selectores dentro de esa función.
