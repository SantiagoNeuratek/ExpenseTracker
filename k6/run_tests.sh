#!/bin/bash

# Script para ejecutar todas las pruebas de carga y generar reportes

echo "=================================="
echo "Iniciando pruebas de carga para ExpenseTracker"
echo "=================================="

# Crear directorio para reportes si no existe
REPORT_DIR="./reports"
mkdir -p $REPORT_DIR

# Timestamp para los reportes
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Función para ejecutar una prueba con k6 y guardar el resultado
run_test() {
    TEST_FILE=$1
    TEST_NAME=$(basename $TEST_FILE .js)
    
    echo ""
    echo "Ejecutando prueba: $TEST_NAME"
    echo "--------------------------------"
    
    # Ejecutar la prueba y guardar resultados en formato JSON
    k6 run $TEST_FILE --summary-export=$REPORT_DIR/${TEST_NAME}_report_${TIMESTAMP}.json
    
    # Verificar resultado
    if [ $? -eq 0 ]; then
        echo "✅ Prueba $TEST_NAME completada exitosamente"
    else
        echo "❌ Prueba $TEST_NAME falló"
    fi
}

# Ejecutar cada prueba de carga
run_test "expenses_by_category.js"
run_test "top_categories.js"

# Generar un resumen de los resultados
echo ""
echo "=================================="
echo "Resumen de resultados"
echo "=================================="
echo "Reportes guardados en: $REPORT_DIR"
echo ""

# Listar los reportes generados
ls -la $REPORT_DIR/*_${TIMESTAMP}.json

echo ""
echo "Para ver detalles de un reporte específico ejecuta:"
echo "cat $REPORT_DIR/nombre_reporte.json | jq"
echo ""
echo "Pruebas de carga completadas"
echo "==================================" 