FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.5.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar poetry
RUN pip install "poetry==$POETRY_VERSION"

# Directorio de trabajo
WORKDIR /app

# Copiar todo el código primero
COPY . .

# Copy the env.example to .env as a starting point
RUN cp env.example .env

# Remove any existing SQLALCHEMY_DATABASE_URI from the .env file
RUN sed -i '/SQLALCHEMY_DATABASE_URI/d' .env

# ARG to control whether to install dev dependencies
ARG INSTALL_DEV=false

# Install dependencies
RUN if [ "${INSTALL_DEV}" = "true" ] ; then \
    poetry install --no-interaction --no-ansi ; \
    else \
    poetry install --no-interaction --no-ansi --only main ; \
    fi

# Install psutil separately in case it's not in poetry dependencies
RUN pip install psutil

# Create non-root user (for better security)
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/monitoring/health || exit 1

# Comando para iniciar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]