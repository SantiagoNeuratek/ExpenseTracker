# app/main.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import asyncio
from contextlib import asynccontextmanager
from typing import Callable, Dict, Any, List, Optional
import traceback

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import (
    setup_logging, get_logger, set_request_id, get_request_id,
    set_user_id, set_company_id, log_api_request, log_api_response,
    log_with_context
)
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.utils.metrics import metrics

# Setup structured logging
log_level = os.getenv("LOG_LEVEL", "INFO")
is_json_logs = os.getenv("JSON_LOGS", "true").lower() == "true"
setup_logging(app_name=settings.PROJECT_NAME, log_level=log_level, is_json=is_json_logs)
logger = get_logger(__name__)


# Función para registrar métricas periódicamente
async def log_metrics_periodically():
    """Periodically log application metrics"""
    logger.info("Starting metrics logging task")
    while True:
        metrics.log_metrics()
        await asyncio.sleep(300)  # cada 5 minutos


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Inicialización de la base de datos
    db_uri = str(settings.SQLALCHEMY_DATABASE_URI)
    masked_uri = db_uri.replace(settings.POSTGRES_PASSWORD, "********")
    log_with_context(logger, "INFO", "Initializing database", data={"database_url": masked_uri})
    db = SessionLocal()
    try:
        init_db(db)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed", exc_info=e)
        raise
    finally:
        db.close()

    # Inicia la tarea de registro periódico de métricas
    logger.info("Starting background tasks")
    task = asyncio.create_task(log_metrics_periodically())

    # Log server startup
    log_with_context(
        logger, "INFO", f"Starting {settings.PROJECT_NAME} API",
        data={"version": "1.0.0", "environment": os.getenv("ENVIRONMENT", "development")}
    )

    yield

    # Detener la tarea cuando se cierre la aplicación
    logger.info("Shutting down application")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Metrics task successfully cancelled")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para la gestión de gastos empresariales",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Middleware para CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for adding request ID and timing all requests
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    # Generate and set request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = set_request_id()
    else:
        set_request_id(request_id)
    
    path = request.url.path
    method = request.method
    
    # Skip metrics for monitoring endpoints to avoid recursion
    if "/monitoring/" in path:
        return await call_next(request)
    
    # Extract auth token if available to get user and company context
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # We don't decode the token here to avoid overhead
        # The dependencies will handle getting the user/company ID
        pass
    
    # Extract API key for public endpoints if available
    api_key = request.headers.get("API-Key")
    has_auth = bool(auth_header or api_key)
    
    # Extract query parameters and sanitize sensitive ones
    query_params = {}
    for k, v in request.query_params.items():
        # Don't log sensitive data
        if k.lower() in ["password", "token", "key", "secret"]:
            query_params[k] = "********"
        else:
            query_params[k] = v
    
    # Log the incoming request with context
    log_api_request(
        logger,
        path,
        method,
        params={
            "query": query_params,
            "client_host": request.client.host if request.client else None,
            "has_auth": has_auth,
            "headers": {k: v for k, v in request.headers.items() 
                     if k.lower() not in ["authorization", "cookie", "api-key"]}
        }
    )
    
    # Process request with timing
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        duration = time.time() - start_time
        duration_ms = duration * 1000
        
        # Record metrics
        metrics.add_request_time(path, method, response.status_code, duration)
        
        # Add timing and request ID headers
        response.headers["X-Process-Time"] = str(duration)
        response.headers["X-Request-ID"] = request_id
        
        # Log the completed request
        log_api_response(
            logger,
            path,
            method,
            response.status_code,
            duration_ms
        )
        
        return response
    except Exception as e:
        # Calculate duration even for failed requests
        duration = time.time() - start_time
        duration_ms = duration * 1000
        
        # Get full traceback for better diagnostics
        tb = traceback.format_exc()
        
        # Get detailed error info
        error_type = type(e).__name__
        error_msg = str(e)
        
        # Determine status code
        status_code = 500
        if hasattr(e, "status_code"):
            status_code = e.status_code
        
        # Log exceptions with full context
        logger.error(
            f"Request failed: {method} {path} - Error: {error_type}: {error_msg}",
            extra={
                "path": path,
                "method": method,
                "query": query_params,
                "error_type": error_type,
                "error_message": error_msg,
                "duration_ms": duration_ms
            },
            exc_info=e
        )
        
        # Record the error in metrics
        metrics.add_request_time(path, method, status_code, duration)
        
        # Re-raise the exception for FastAPI to handle
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Already logged in the middleware, just return a structured response
    request_id = get_request_id()
    
    # Get error details
    error_detail = "Se produjo un error interno del servidor."
    if hasattr(exc, "detail"):
        error_detail = exc.detail
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": error_detail,
            "request_id": request_id,
            "type": type(exc).__name__
        },
    )


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Add a basic root endpoint that redirects to the API docs
@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API. Visit /api/docs for documentation."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
