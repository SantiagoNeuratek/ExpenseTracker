#!/bin/bash

set -e

echo "🧹 Limpiando entorno anterior..."

# Verificar si existe el directorio frontend de Streamlit y eliminarlo
if [ -d "frontend" ]; then
  echo "🗑️ Eliminando directorio frontend (Streamlit)..."
  rm -rf frontend
fi

# Detener y eliminar contenedores existentes
echo "🛑 Deteniendo contenedores existentes..."
docker-compose down -v 2>/dev/null || true

# Eliminar volúmenes para comenzar con una base de datos limpia
echo "🗑️ Eliminando volúmenes para comenzar con una base de datos fresca..."
docker volume rm expense_tracker_postgres_data 2>/dev/null || true

# Verificar permisos del script docker-entrypoint.sh
if [ -f "backend/docker-entrypoint.sh" ]; then
  echo "🔒 Asegurando permisos del script docker-entrypoint.sh..."
  chmod +x backend/docker-entrypoint.sh
fi

echo "🏗️ Construyendo y levantando servicios..."
docker-compose up --build -d

echo "📋 Mostrando estado de los servicios..."
docker-compose ps

echo "🌟 Configuración completada con éxito!"
echo ""
echo "✅ El backend está ejecutándose en: http://localhost:8000"
echo "✅ El frontend está ejecutándose en: http://localhost"
echo "✅ La base de datos PostgreSQL está en el puerto 5433"
echo ""
echo "🔍 Para ver los logs ejecuta: docker-compose logs -f"
echo "🛑 Para detener los servicios ejecuta: docker-compose down"
echo ""
echo "📝 Credenciales por defecto:"
echo "   🔹 Administrador: admin@saas.com / Password1"
echo "   🔹 Usuario: usuario@ort.com / Password1"
echo ""
echo "😊 ¡Disfruta de ExpenseTracker!" 