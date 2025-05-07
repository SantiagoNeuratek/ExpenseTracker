from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
from unittest.mock import patch, MagicMock
import json
import os
import time
import psutil
import platform
from datetime import datetime, timedelta

# Importar el módulo con el router de monitoreo para poder mockearlo
from app.api.v1.endpoints import monitoring
from app.utils.metrics import metrics

# Test para health check
def test_health_check(client: TestClient):
    """Test basic health check endpoint"""
    # Act
    response = client.get("/api/v1/monitoring/health")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "components" in data
    assert "database" in data["components"]
    assert "api" in data["components"]

# Test para health check completo
def test_health_check_full(client: TestClient):
    """Test full health check endpoint"""
    # Act
    response = client.get("/api/v1/monitoring/health?full=true")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "metrics" in data
    assert "uptime_seconds" in data["metrics"]
    assert "request_count_1m" in data["metrics"]
    assert "error_count_1m" in data["metrics"]

# Test para health check con fallo de base de datos
def test_health_check_db_failure(client: TestClient):
    """Test health check with database failure"""
    # Setup - guarda la caché original para restaurarla después
    original_cache = monitoring.health_check_cache.copy()
    # Asegurarse de que la caché esté limpia para este test
    monitoring.health_check_cache["status"] = None
    monitoring.health_check_cache["last_checked"] = None
    
    # Mockear la función de ejecución de SQL para simular un error
    def mock_execute(*args, **kwargs):
        raise Exception("Test database connection error")
    
    # Patch de la ejecución de SQL - corregimos la ruta del mock
    with patch("sqlalchemy.orm.Session.execute", side_effect=mock_execute):
        # Act
        response = client.get("/api/v1/monitoring/health")
        
        # Assert
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "error"
        assert data["components"]["database"]["status"] == "error"
        assert "error" in data["components"]["database"]
    
    # Restaurar caché original
    monitoring.health_check_cache = original_cache

# Test para obtener métricas
def test_get_metrics(client: TestClient):
    """Test getting metrics"""
    # Act
    response = client.get("/api/v1/monitoring/metrics")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "_global" in data
    assert isinstance(data, dict)

# Test para system health
def test_system_health(client: TestClient):
    """Test system health endpoint"""
    # Act
    response = client.get("/api/v1/monitoring/system-health")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "process" in data
    assert "system" in data
    assert "memory_usage_mb" in data["process"]
    assert "memory_total_mb" in data["system"]

# Test para system health con error
def test_system_health_error(client: TestClient):
    """Test system health endpoint when it fails"""
    
    # Mock de psutil.Process para simular un error
    with patch("psutil.Process", side_effect=Exception("Test system health error")):
        # Act
        response = client.get("/api/v1/monitoring/system-health")
        
        # Assert
        assert response.status_code == 200  # Devuelve 200 pero con un mensaje de error
        data = response.json()
        assert "error" in data
        assert "Test system health error" in data["error"]

# Test para readiness probe
def test_readiness(client: TestClient):
    """Test readiness endpoint"""
    # Act
    response = client.get("/api/v1/monitoring/readiness")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data

# Test para liveness probe
def test_liveness(client: TestClient):
    """Test liveness endpoint"""
    # Act
    response = client.get("/api/v1/monitoring/liveness")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data

# Test para obtener resultados de prueba de carga
def test_get_load_test_results_file_exists(client: TestClient):
    """Test getting load test results when file exists"""
    # Datos de prueba
    test_data = {
        "topCategoriesP95": 28,
        "categoriesExpensesP95": 29,
        "summary": {
            "data_received": 123456,
            "data_sent": 78910,
            "http_req_duration": {
                "avg": 45.67,
                "min": 12.34,
                "max": 89.01,
                "p95": 67.89
            }
        }
    }
    
    # Mock para open() usando with patch
    mock_open = MagicMock()
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(test_data)
    
    # Mock para os.path.exists para que devuelva True
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open):
        
        # Act
        response = client.get("/api/v1/monitoring/load-test-results")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == test_data

# Test para el caso en que no existe el archivo de resultados
def test_get_load_test_results_file_not_exists(client: TestClient):
    """Test getting load test results when file doesn't exist"""
    # Mock para os.path.exists para que devuelva False
    with patch("os.path.exists", return_value=False):
        # Act
        response = client.get("/api/v1/monitoring/load-test-results")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        # Verifica que se devuelven datos dummy
        assert "topCategoriesP95" in data
        assert "categoriesExpensesP95" in data
        # El formato de los datos dummy no tiene 'summary'
        assert "source" in data
        assert data["source"] == "dummy"

# Test para el caso en que hay un error al leer el archivo
def test_get_load_test_results_read_error(client: TestClient):
    """Test getting load test results when there's an error reading the file"""
    # Mock para os.path.exists para que devuelva True
    # pero open lanza una excepción
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", side_effect=Exception("Test file read error")):
        
        # Act
        response = client.get("/api/v1/monitoring/load-test-results")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        # Verifica que se devuelven datos dummy
        assert "topCategoriesP95" in data
        assert "categoriesExpensesP95" in data
        # El formato de los datos dummy no tiene 'summary'
        assert "source" in data
        assert data["source"] == "dummy" 