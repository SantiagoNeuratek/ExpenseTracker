FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.5.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Instalar poetry
RUN pip install "poetry==$POETRY_VERSION"

# Directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración
COPY pyproject.toml poetry.lock* ./

# Instalar dependencias
RUN poetry install --no-interaction --no-ansi --no-dev

# Copiar el resto del código
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando para iniciar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]