# ==============================================================================
# Dockerfile para Travel Agent - Florida 2027
# Utiliza la imagen oficial de Playwright con soporte completo de Chromium y dependencias OS.
# ==============================================================================
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Instalar dependencias del proyecto
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    playwright install chromium

# Copiar el código fuente
COPY tracker/ tracker/
COPY flows/ flows/
COPY config.py main.py .

# Crear directorios para volúmenes persistentes
RUN mkdir -p data capturas logs .browser_profile

# Comando por defecto: ejecutar una pasada del tracker
ENTRYPOINT ["python", "main.py"]
CMD ["run"]

