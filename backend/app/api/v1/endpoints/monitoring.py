# app/api/v1/endpoints/monitoring.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi import status
from datetime import datetime, timedelta
import time
import os
import platform
import psutil
from typing import Dict, Any, Optional

from app.api.deps import get_db
from app.utils.metrics import metrics
from app.core.logging import get_logger, log_with_context

router = APIRouter()
logger = get_logger(__name__)

# Cache for health check to prevent excessive database calls
health_check_cache = {
    "status": None,
    "last_checked": None,
    "cache_ttl_seconds": 15  # Cache TTL in seconds
}


@router.get("/health", tags=["Health"], response_model_exclude_none=True)
def health_check(db: Session = Depends(get_db), full: bool = False):
    """
    Verifica el estado de salud del sistema.
    Comprueba la conectividad con la base de datos y otros servicios esenciales.
    
    - Si el parámetro full=true, realizará comprobaciones más detalladas.
    - Por defecto, utiliza un caché para evitar sobrecarga de la base de datos.
    """
    global health_check_cache
    
    # Check if we have a valid cached response (for non-full checks)
    if (not full and 
        health_check_cache["status"] is not None and 
        health_check_cache["last_checked"] is not None and
        datetime.now() - health_check_cache["last_checked"] < timedelta(seconds=health_check_cache["cache_ttl_seconds"])):
        return health_check_cache["status"]
    
    # Base health status
    health_status = {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "api": {"status": "ok"},
            "database": {"status": "unknown"}
        },
        "instance_id": os.environ.get("INSTANCE_ID", platform.node())
    }
    
    # Add optional full metrics if requested
    if full:
        health_status["metrics"] = {
            "uptime_seconds": metrics.get_uptime(),
            "request_count_1m": metrics.get_request_count_timeframe(seconds=60),
            "error_count_1m": metrics.get_error_count_timeframe(seconds=60),
            "avg_response_time_1m": metrics.get_avg_response_time_timeframe(seconds=60)
        }
    
    # Verify database connection
    try:
        # Time the database query execution
        start_time = time.time()
        
        # Run a simple query that also returns the current time from the database
        result = db.execute(text("SELECT 1 as is_alive, NOW() as server_time")).first()
        
        # Calculate query time
        db_response_time = time.time() - start_time
        
        # Database is responding
        health_status["components"]["database"] = {
            "status": "ok",
            "response_time_ms": round(db_response_time * 1000, 2),
            "server_time": result.server_time.isoformat() if hasattr(result, "server_time") else None
        }
        
        # Add detailed DB metrics in full mode
        if full:
            try:
                # Get connection pool statistics if available
                pool_info = db.get_bind().pool.status()
                health_status["components"]["database"]["pool"] = {
                    "size": pool_info.size if hasattr(pool_info, "size") else None,
                    "checkedin": pool_info.checkedin if hasattr(pool_info, "checkedin") else None,
                    "checkedout": pool_info.checkedout if hasattr(pool_info, "checkedout") else None,
                }
            except Exception:
                # Pool info might not be available
                pass
    except Exception as e:
        # Log detailed error for troubleshooting
        logger.error("Database health check failed", 
                    data={"error": str(e), "error_type": type(e).__name__}, 
                    exc_info=e)
        
        # Database connection failed
        health_status["status"] = "error"
        health_status["components"]["database"] = {
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        }

    # Update cache for non-full checks
    if not full:
        health_check_cache["status"] = health_status
        health_check_cache["last_checked"] = datetime.now()

    # If any component failed, return 503 Service Unavailable
    if health_status["status"] == "error":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            content=health_status
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
        process = psutil.Process(os.getpid())
        
        # Get memory information
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        # Get disk information
        disk_usage = psutil.disk_usage('/')
        
        # Get system load (Unix-like systems only)
        try:
            load_avg = os.getloadavg()
            load_1m, load_5m, load_15m = load_avg
        except (AttributeError, OSError):
            # Windows or other systems might not support getloadavg
            load_1m = load_5m = load_15m = None
        
        return {
            "process": {
                "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
                "memory_percent": round(process.memory_percent(), 2),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections()),
                "uptime_seconds": round(time.time() - process.create_time(), 2),
            },
            "system": {
                "cpu_count": os.cpu_count(),
                "memory_total_mb": round(system_memory.total / 1024 / 1024, 2),
                "memory_available_mb": round(system_memory.available / 1024 / 1024, 2),
                "memory_percent": system_memory.percent,
                "disk_total_gb": round(disk_usage.total / 1024 / 1024 / 1024, 2),
                "disk_used_gb": round(disk_usage.used / 1024 / 1024 / 1024, 2),
                "disk_percent": disk_usage.percent,
                "load_1m": load_1m,
                "load_5m": load_5m,
                "load_15m": load_15m,
            }
        }
    except ImportError:
        return {
            "error": "psutil no está instalado. Instálalo con 'pip install psutil' para ver métricas del sistema."
        }
    except Exception as e:
        logger.error("Error getting system health metrics", 
                   data={"error": str(e), "error_type": type(e).__name__},
                   exc_info=e)
        return {
            "error": f"Error getting system metrics: {str(e)}",
            "error_type": type(e).__name__
        }


@router.get("/readiness", tags=["Health"])
def readiness():
    """
    Endpoint for readiness probe in containerized environments.
    Indicates if the application is ready to receive traffic.
    This is useful for Kubernetes readiness probes.
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@router.get("/liveness", tags=["Health"])
def liveness():
    """
    Endpoint for liveness probe in containerized environments.
    Indicates if the application is alive and running.
    This is useful for Kubernetes liveness probes.
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
