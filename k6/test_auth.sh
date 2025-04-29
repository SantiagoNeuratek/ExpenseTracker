#!/bin/bash

# Este script ejecuta una prueba de autenticación simple para verificar credenciales antes de las pruebas de carga

echo "🔑 Ejecutando prueba de autenticación..."

# Verificar si k6 está instalado
if ! command -v k6 &> /dev/null
then
    echo "❌ k6 no está instalado. Por favor, instálalo siguiendo las instrucciones en:"
    echo "   https://k6.io/docs/get-started/installation/"
    exit 1
fi

# Ejecutar la prueba
k6 run check_auth.js

# Verificar si la prueba fue exitosa
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ La prueba de autenticación falló."
    echo "   Por favor verifica las credenciales y la estructura de la solicitud en check_auth.js"
    exit 1
fi

echo ""
echo "✅ La prueba de autenticación fue exitosa"
echo "   Puedes proceder a ejecutar las pruebas de carga completas con ./run_load_tests.sh" 