"""
Módulo de caché en memoria para mejorar el rendimiento de endpoints críticos.
Implementa un sistema de caché simple con expiración para reducir la carga en la base de datos.
"""
import time
import threading
from typing import Dict, Any, Optional, Tuple


class CacheItem:
    def __init__(self, value: Any, expire_time: Optional[float] = None):
        self.value = value
        self.expire_time = expire_time
        self.creation_time = time.time()

    def is_expired(self) -> bool:
        """Comprueba si el elemento ha expirado"""
        if self.expire_time is None:
            return False
        return time.time() > self.expire_time


class SimpleCache:
    """
    Implementación simple de un sistema de caché en memoria con expiración.
    Útil para reducir la carga en la base de datos para endpoints de alto tráfico.
    """
    def __init__(self):
        self._cache: Dict[str, CacheItem] = {}
        self._lock = threading.Lock()
        self._max_items = 1000  # Máximo número de elementos en caché
        self._cleanup_interval = 60  # Intervalo de limpieza en segundos
        self._last_cleanup = time.time()

    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor de la caché si existe y no ha expirado.

        Args:
            key: La clave del elemento a recuperar.

        Returns:
            El valor almacenado o None si no existe o ha expirado.
        """
        with self._lock:
            # Hacer limpieza periódica
            self._cleanup_if_needed()
            
            # Comprobar si existe y no ha expirado
            if key in self._cache:
                item = self._cache[key]
                if not item.is_expired():
                    return item.value
                # Si ha expirado, eliminarlo
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Almacena un valor en la caché con un tiempo de vida opcional.

        Args:
            key: La clave para almacenar el valor.
            value: El valor a almacenar.
            ttl: Tiempo de vida en segundos. None para que no expire.
        """
        with self._lock:
            # Calcular tiempo de expiración
            expire_time = None
            if ttl is not None:
                expire_time = time.time() + ttl
            
            # Almacenar el valor
            self._cache[key] = CacheItem(value, expire_time)
            
            # Comprobar si necesitamos limpiar
            if len(self._cache) > self._max_items:
                self._evict_oldest()

    def delete(self, key: str) -> None:
        """
        Elimina un elemento de la caché.

        Args:
            key: La clave del elemento a eliminar.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self) -> None:
        """Elimina todos los elementos de la caché."""
        with self._lock:
            self._cache.clear()

    def _cleanup_if_needed(self) -> None:
        """Elimina elementos expirados si ha pasado el intervalo de limpieza."""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup()
            self._last_cleanup = now

    def _cleanup(self) -> None:
        """Elimina todos los elementos expirados de la caché."""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]

    def _evict_oldest(self) -> None:
        """Elimina los elementos más antiguos cuando la caché está llena."""
        # Ordenar por tiempo de creación
        sorted_items = sorted(self._cache.items(), key=lambda x: x[1].creation_time)
        # Eliminar al menos 10% de los elementos
        items_to_remove = max(1, len(self._cache) // 10)
        for i in range(items_to_remove):
            if i < len(sorted_items):
                del self._cache[sorted_items[i][0]]

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la caché."""
        with self._lock:
            active_items = sum(1 for item in self._cache.values() if not item.is_expired())
            return {
                "total_items": len(self._cache),
                "active_items": active_items,
                "expired_items": len(self._cache) - active_items,
                "hit_ratio": 0,  # Añadir contador de hits/misses en futuras versiones
            }


# Singleton instance
cache = SimpleCache() 