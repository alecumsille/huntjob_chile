FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Streamlit no permite fijar meta tags Open Graph en el HTML servidor
# (todo lo que agrega la app vive dentro del <div id="root"> que arma
# React en el navegador, invisible para bots de preview de links que no
# ejecutan JS). Se parchea el index.html estático de Streamlit acá, una
# sola vez, al construir la imagen.
RUN python scripts/patch_index_html.py

# Exponer el puerto por defecto
EXPOSE 8501

# Comando de arranque de la app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
