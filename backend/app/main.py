# app/main.py
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import asyncio
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.utils.metrics import metrics

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# Función para registrar métricas periódicamente
async def log_metrics_periodically():
    while True:
        metrics.log_metrics()
        await asyncio.sleep(300)  # cada 5 minutos


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialización de la base de datos
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()

    # Inicia la tarea de registro periódico de métricas
    task = asyncio.create_task(log_metrics_periodically())

    yield

    # Detener la tarea cuando se cierre la aplicación
    task.cancel()


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


# Middleware para recopilar métricas
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method

    # No medir las llamadas a endpoints de monitoreo para evitar conteo recursivo
    if "/monitoring/" in path:
        return await call_next(request)

    start_time = time.time()

    # Procesar la solicitud
    response = await call_next(request)

    # Medir el tiempo de respuesta
    duration = time.time() - start_time

    # Guardar las métricas
    metrics.add_request_time(path, method, response.status_code, duration)

    # Agregar el tiempo de procesamiento como header
    response.headers["X-Process-Time"] = str(duration)

    # Log de la solicitud
    logger.info(
        f"Request: {method} {path} - "
        f"Time: {duration:.4f}s - "
        f"Status: {response.status_code}"
    )

    return response


# Manejador de excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Se produjo un error interno del servidor."},
    )


# Rutas de la API
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
