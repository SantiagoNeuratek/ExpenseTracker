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

# Hacer ejecutable el script de entrada - update permissions properly
RUN chmod +x /app/docker-entrypoint.sh

# Create non-root user (for better security)
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
# Make sure entrypoint script is still executable after ownership change
RUN chmod 755 /app/docker-entrypoint.sh
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/monitoring/health || exit 1

# Usar el script de entrada
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Comando para iniciar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]