from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
import os
from sqlalchemy.orm import Session
import json

# Importar el módulo main para poder mockearlo
from app.main import app, request_middleware, global_exception_handler, log_metrics_periodically
from app.core.logging import get_request_id


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


# Test para la ruta principal
def test_root_endpoint(client: TestClient):
    """Test the root endpoint returns successfully"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Welcome to" in data["message"]
    assert "API. Visit /api/docs for documentation" in data["message"]


# Test para el middleware de solicitudes
@pytest.mark.asyncio
async def test_request_middleware():
    """Test the request middleware function"""
    # Crear mock para la solicitud
    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/test"
    mock_request.method = "GET"
    mock_request.query_params = {"query": "test", "password": "secret"}
    mock_request.headers = {}
    mock_request.client.host = "127.0.0.1"
    
    # Crear mock para la función call_next
    async def mock_call_next(request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        return mock_response
    
    # Ejecutar el middleware
    response = await request_middleware(mock_request, mock_call_next)
    
    # Verificar que se ha establecido un request_id
    assert get_request_id() is not None
    
    # Verificar que la respuesta tiene headers añadidos
    assert "X-Process-Time" in response.headers
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == get_request_id()


# Test para el middleware de solicitudes con ID de solicitud existente
@pytest.mark.asyncio
async def test_request_middleware_with_request_id():
    """Test the request middleware function with an existing request ID"""
    # Crear mock para la solicitud con un ID de solicitud
    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/test"
    mock_request.method = "GET"
    mock_request.query_params = {}
    mock_request.headers = {"X-Request-ID": "test-request-id"}
    mock_request.client.host = "127.0.0.1"
    
    # Crear mock para la función call_next
    async def mock_call_next(request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        return mock_response
    
    # Ejecutar el middleware
    response = await request_middleware(mock_request, mock_call_next)
    
    # Verificar que se ha utilizado el request_id proporcionado
    assert get_request_id() == "test-request-id"
    
    # Verificar que la respuesta tiene headers añadidos
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == "test-request-id"


# Test para el middleware de solicitudes para rutas de monitoreo
@pytest.mark.asyncio
async def test_request_middleware_monitoring_path():
    """Test the request middleware skips processing for monitoring paths"""
    # Crear mock para la solicitud
    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/monitoring/health"
    mock_request.method = "GET"
    mock_request.query_params = {}
    mock_request.headers = {}
    
    # Crear mock para la función call_next
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    
    async def mock_call_next(request):
        return mock_response
    
    # Ejecutar el middleware
    response = await request_middleware(mock_request, mock_call_next)
    
    # Verificar que se devuelve directamente la respuesta sin procesamiento adicional
    assert response == mock_response
    assert not hasattr(response.headers, "X-Process-Time")


# Test para el middleware con excepción
@pytest.mark.asyncio
async def test_request_middleware_with_exception():
    """Test the request middleware handles exceptions correctly"""
    # Crear mock para la solicitud
    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/test"
    mock_request.method = "GET"
    mock_request.query_params = {}
    mock_request.headers = {}
    mock_request.client.host = "127.0.0.1"
    
    # Crear mock para la función call_next que lanza una excepción
    async def mock_call_next(request):
        raise ValueError("Test exception")
    
    # Ejecutar el middleware y esperar que relance la excepción
    with pytest.raises(ValueError) as excinfo:
        await request_middleware(mock_request, mock_call_next)
    
    # Verificar que la excepción es la que esperamos
    assert "Test exception" in str(excinfo.value)


# Test para el manejador global de excepciones
@pytest.mark.asyncio
async def test_global_exception_handler():
    """Test the global exception handler returns a structured response"""
    # Crear mock para la solicitud
    mock_request = MagicMock()
    
    # Crear una excepción con detalle
    exception = ValueError("Test exception")
    exception.detail = "Detailed error message"
    
    # Ejecutar el manejador de excepciones
    response = await global_exception_handler(mock_request, exception)
    
    # Verificar la respuesta
    assert response.status_code == 500
    content = json.loads(response.body)
    assert content["detail"] == "Detailed error message"
    assert content["type"] == "ValueError"
    assert "request_id" in content


# Test para log_metrics_periodically
@pytest.mark.asyncio
async def test_log_metrics_periodically():
    """Test log_metrics_periodically function"""
    # Mock para la función de registro de métricas
    with patch("app.utils.metrics.metrics.log_metrics") as mock_log_metrics, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        
        # Configurar mock_sleep para lanzar una excepción después de la primera llamada
        mock_sleep.side_effect = [None, asyncio.CancelledError()]
        
        # Ejecutar la función hasta que se lance la excepción
        with pytest.raises(asyncio.CancelledError):
            await log_metrics_periodically()
        
        # Verificar que se llamó a log_metrics al menos una vez
        mock_log_metrics.assert_called()
        # Verificar que se llamó a sleep con el intervalo correcto
        mock_sleep.assert_called_with(300)


# Test para middleware con autenticación
@pytest.mark.asyncio
async def test_request_middleware_with_auth_header():
    """Test the request middleware processes auth headers correctly"""
    # Crear mock para la solicitud con header de autorización
    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/test"
    mock_request.method = "GET"
    mock_request.query_params = {}
    mock_request.headers = {"Authorization": "Bearer test-token"}
    mock_request.client.host = "127.0.0.1"
    
    # Crear mock para la función call_next
    async def mock_call_next(request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        return mock_response
    
    # Ejecutar el middleware
    response = await request_middleware(mock_request, mock_call_next)
    
    # Verificar que la respuesta tiene headers añadidos
    assert "X-Process-Time" in response.headers
    assert "X-Request-ID" in response.headers


# Test para middleware con API key
@pytest.mark.asyncio
async def test_request_middleware_with_api_key():
    """Test the request middleware processes API key headers correctly"""
    # Crear mock para la solicitud con header de API key
    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/test"
    mock_request.method = "GET"
    mock_request.query_params = {}
    mock_request.headers = {"api-key": "test-api-key"}
    mock_request.client.host = "127.0.0.1"
    
    # Crear mock para la función call_next
    async def mock_call_next(request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        return mock_response
    
    # Ejecutar el middleware
    response = await request_middleware(mock_request, mock_call_next)
    
    # Verificar que la respuesta tiene headers añadidos
    assert "X-Process-Time" in response.headers
    assert "X-Request-ID" in response.headers 