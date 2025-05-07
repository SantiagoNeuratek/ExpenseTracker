from collections import defaultdict
import time
from statistics import mean, median
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self):
        self._metrics = defaultdict(list)
        self._lock = threading.Lock()
        self._request_count = defaultdict(int)
        self._error_count = defaultdict(int)
        self._start_time = time.time()
        self._request_times_with_timestamp = defaultdict(list)  # For time-based analysis
        self._slow_requests = []  # Track slow requests (>500ms)
        self._max_slow_requests = 100  # Maximum number of slow requests to keep

    def add_request_time(self, endpoint: str, method: str, status_code: int, duration: float):
        """
        Record metrics for a request
        
        Args:
            endpoint: The endpoint path
            method: HTTP method (GET, POST, etc.)
            status_code: HTTP status code
            duration: Request duration in seconds
        """
        key = f"{method}:{endpoint}"
        timestamp = time.time()
        
        with self._lock:
            # Record basic metrics
            self._metrics[key].append(duration)
            self._request_count[key] += 1
            if 400 <= status_code < 600:
                self._error_count[key] += 1

            # Record time-based metrics for more detailed analysis
            self._request_times_with_timestamp[key].append((timestamp, duration, status_code))
            
            # Track slow requests (for debugging)
            if duration > 0.5:  # 500ms threshold
                self._slow_requests.append({
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code,
                    "duration": duration,
                    "timestamp": datetime.fromtimestamp(timestamp).isoformat()
                })
                # Keep the list at a reasonable size
                if len(self._slow_requests) > self._max_slow_requests:
                    self._slow_requests = self._slow_requests[-self._max_slow_requests:]
            
            # Maintain only the latest 1000 requests per endpoint to avoid memory issues
            if len(self._metrics[key]) > 1000:
                self._metrics[key] = self._metrics[key][-1000:]
            
            # Clean up older time-based metrics (keep last hour)
            oldest_allowed = timestamp - 3600  # 1 hour
            self._request_times_with_timestamp[key] = [
                item for item in self._request_times_with_timestamp[key] 
                if item[0] >= oldest_allowed
            ]

    def get_metrics(self):
        """Get aggregated metrics for all endpoints"""
        with self._lock:
            result = {}
            for endpoint, times in self._metrics.items():
                if not times:
                    continue

                # Calculate percentiles
                sorted_times = sorted(times)
                p95 = sorted_times[int(len(times) * 0.95)] if len(times) >= 20 else None
                p99 = sorted_times[int(len(times) * 0.99)] if len(times) >= 100 else None

                result[endpoint] = {
                    "count": self._request_count[endpoint],
                    "errors": self._error_count[endpoint],
                    "avg_time": mean(times),
                    "median_time": median(times) if times else None,
                    "p95_time": p95,
                    "p99_time": p99,
                    "min_time": min(times),
                    "max_time": max(times),
                    "error_rate": (self._error_count[endpoint] / self._request_count[endpoint]) * 100 
                        if self._request_count[endpoint] > 0 else 0
                }
            
            # Add global metrics
            total_requests = sum(self._request_count.values())
            total_errors = sum(self._error_count.values())
            
            result["_global"] = {
                "uptime_seconds": time.time() - self._start_time,
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": (total_errors / total_requests) * 100 if total_requests > 0 else 0,
                "requests_per_minute": total_requests / ((time.time() - self._start_time) / 60) 
                    if time.time() > self._start_time else 0,
                "slow_requests_count": len(self._slow_requests)
            }
            
            return result
    
    def get_uptime(self) -> float:
        """Get the API uptime in seconds"""
        return time.time() - self._start_time
    
    def get_request_count_timeframe(self, seconds: int = 60) -> int:
        """Get the number of requests in the last N seconds"""
        cutoff_time = time.time() - seconds
        count = 0
        
        with self._lock:
            for endpoint, times_list in self._request_times_with_timestamp.items():
                count += sum(1 for t, _, _ in times_list if t >= cutoff_time)
        
        return count
    
    def get_error_count_timeframe(self, seconds: int = 60) -> int:
        """Get the number of errors in the last N seconds"""
        cutoff_time = time.time() - seconds
        count = 0
        
        with self._lock:
            for endpoint, times_list in self._request_times_with_timestamp.items():
                count += sum(1 for t, _, status in times_list if t >= cutoff_time and 400 <= status < 600)
        
        return count
    
    def get_avg_response_time_timeframe(self, seconds: int = 60) -> Optional[float]:
        """Get the average response time in the last N seconds"""
        cutoff_time = time.time() - seconds
        all_times = []
        
        with self._lock:
            for endpoint, times_list in self._request_times_with_timestamp.items():
                all_times.extend([duration for t, duration, _ in times_list if t >= cutoff_time])
        
        if all_times:
            return sum(all_times) / len(all_times)
        return None
    
    def get_endpoint_stats_timeframe(self, endpoint: str, method: str, seconds: int = 60) -> Dict[str, Any]:
        """Get detailed stats for a specific endpoint in the last N seconds"""
        key = f"{method}:{endpoint}"
        cutoff_time = time.time() - seconds
        times = []
        errors = 0
        
        with self._lock:
            if key in self._request_times_with_timestamp:
                for t, duration, status in self._request_times_with_timestamp[key]:
                    if t >= cutoff_time:
                        times.append(duration)
                        if 400 <= status < 600:
                            errors += 1
        
        if not times:
            return {"count": 0}
        
        sorted_times = sorted(times)
        p95 = sorted_times[int(len(times) * 0.95)] if len(times) >= 20 else None
        
        return {
            "count": len(times),
            "errors": errors,
            "avg_time": sum(times) / len(times),
            "median_time": median(times) if times else None,
            "p95_time": p95,
            "min_time": min(times),
            "max_time": max(times),
            "error_rate": (errors / len(times)) * 100 if times else 0
        }
    
    def get_slow_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent slow requests"""
        with self._lock:
            return self._slow_requests[-limit:]
        
    def reset_metrics(self):
        """Reset all metrics (mainly for testing)"""
        with self._lock:
            self._metrics = defaultdict(list)
            self._request_count = defaultdict(int)
            self._error_count = defaultdict(int)
            self._start_time = time.time()
            self._request_times_with_timestamp = defaultdict(list)
            self._slow_requests = []

    def log_metrics(self, interval=300):
        """Log metrics summary every 'interval' seconds"""
        metrics_data = self.get_metrics()
        
        # Log global stats
        global_stats = metrics_data.pop("_global", {})
        uptime = int(global_stats.get('uptime_seconds', 0))
        requests = global_stats.get('total_requests', 0)
        errors = global_stats.get('total_errors', 0)
        error_rate = global_stats.get('error_rate', 0)
        req_per_min = global_stats.get('requests_per_minute', 0)
        
        logger.info(
            f"Global metrics (uptime: {uptime}s): "
            f"requests={requests}, "
            f"errors={errors}, "
            f"error_rate={error_rate:.2f}%, "
            f"req/min={req_per_min:.2f}"
        )
        
        # Log per-endpoint metrics (top 5 by count)
        sorted_endpoints = sorted(
            metrics_data.items(), 
            key=lambda x: x[1].get('count', 0), 
            reverse=True
        )[:5]
        
        for endpoint, data in sorted_endpoints:
            count = data.get('count', 0)
            errors = data.get('errors', 0)
            avg_time = data.get('avg_time', 0)
            p95_time = data.get('p95_time')
            error_rate = data.get('error_rate', 0)
            
            p95_str = f"{p95_time:.4f}s" if p95_time is not None else "N/A"
            
            logger.info(
                f"Metrics for {endpoint}: "
                f"count={count}, "
                f"errors={errors}, "
                f"avg={avg_time:.4f}s, "
                f"p95={p95_str}, "
                f"error_rate={error_rate:.2f}%"
            )
        
        # Log slow requests if any
        slow_reqs = self.get_slow_requests(5)
        if slow_reqs:
            logger.warning(
                f"Recent slow requests (>{0.5:.0f}ms): {len(slow_reqs)} total, "
                f"showing most recent {len(slow_reqs)}"
            )
            for req in slow_reqs:
                logger.warning(
                    f"Slow request: {req['method']}:{req['endpoint']} - "
                    f"{req['duration']*1000:.0f}ms, status={req['status_code']}"
                )


# Singleton instance
metrics = MetricsCollector()
