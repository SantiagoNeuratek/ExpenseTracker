# app/api/v1/endpoints/monitoring.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi import status
from datetime import datetime
import time

from app.api.deps import get_db
from app.utils.metrics import metrics

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """
    Verifica el estado de salud del sistema.
    Comprueba la conectividad con la base de datos y otros servicios esenciales.
    """
    health_status = {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "components": {"api": {"status": "ok"}, "database": {"status": "ok"}},
    }

    # Verificar conexión con la base de datos
    try:
        # Ejecutar una consulta simple para verificar que la conexión está activa
        db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["status"] = "error"
        health_status["components"]["database"] = {"status": "error", "error": str(e)}

    # Si algún componente falló, devolver código 503 (Service Unavailable)
    if health_status["status"] == "error":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status
        )

    return health_status


@router.get("/metrics", tags=["Monitoring"])
def get_metrics():
    """
    Obtiene métricas detalladas sobre el rendimiento de los endpoints
    """
    return metrics.get_metrics()


@router.get("/system-health", tags=["Monitoring"])
def system_health():
    """
    Proporciona información sobre el estado del sistema y recursos actuales
    """
    try:
        import os
        import psutil

        process = psutil.Process(os.getpid())

        return {
            "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections()),
            "uptime_seconds": time.time() - process.create_time(),
        }
    except ImportError:
        return {
            "error": "psutil no está instalado. Instálalo con 'pip install psutil' para ver métricas del sistema."
        }
