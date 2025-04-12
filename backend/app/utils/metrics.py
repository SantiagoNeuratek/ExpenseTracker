from collections import defaultdict
import time
from statistics import mean
import threading
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self):
        self._metrics = defaultdict(list)
        self._lock = threading.Lock()
        self._request_count = defaultdict(int)
        self._error_count = defaultdict(int)

    def add_request_time(self, endpoint, method, status_code, duration):
        key = f"{method}:{endpoint}"
        with self._lock:
            self._metrics[key].append(duration)
            self._request_count[key] += 1
            if 400 <= status_code < 600:
                self._error_count[key] += 1

            # Mantener solo las últimas 1000 solicitudes para evitar uso excesivo de memoria
            if len(self._metrics[key]) > 1000:
                self._metrics[key] = self._metrics[key][-1000:]

    def get_metrics(self):
        with self._lock:
            result = {}
            for endpoint, times in self._metrics.items():
                if not times:
                    continue

                result[endpoint] = {
                    "count": self._request_count[endpoint],
                    "errors": self._error_count[endpoint],
                    "avg_time": mean(times),
                    "p95_time": sorted(times)[int(len(times) * 0.95)]
                    if len(times) >= 20
                    else None,
                    "min_time": min(times),
                    "max_time": max(times),
                    "requests_per_minute": self._request_count[
                        endpoint
                    ],  # Esto es acumulativo, deberías dividir por el tiempo de ejecución
                }
            return result

    def log_metrics(self, interval=300):
        """Registra las métricas cada 'interval' segundos"""
        metrics = self.get_metrics()
        for endpoint, data in metrics.items():
            logger.info(
                f"Metrics for {endpoint}: "
                f"count={data['count']}, "
                f"errors={data['errors']}, "
                f"avg_time={data['avg_time']:.4f}s, "
                f"p95_time={data['p95_time']:.4f if data['p95_time'] else 'N/A'}s"
            )


# Singleton instance
metrics = MetricsCollector()
