#!/bin/bash

set -e

# Esperar a que la base de datos esté lista
echo "Esperando a que la base de datos esté lista..."
sleep 5

# Ejecutar migraciones
echo "Ejecutando migraciones de la base de datos..."
alembic upgrade head

# Cargar datos iniciales si es necesario
if [ "$LOAD_INITIAL_DATA" = "true" ]; then
    echo "Cargando datos iniciales..."
    python -c "from app.db.init_db import init_db; from app.db.session import SessionLocal; init_db(SessionLocal())"
fi

# Ejecutar el comando pasado a docker-entrypoint
exec "$@" 