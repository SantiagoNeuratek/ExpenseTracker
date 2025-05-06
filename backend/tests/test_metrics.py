import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.utils.metrics import MetricsCollector


@pytest.fixture
def metrics_collector():
    """Fixture to provide a clean MetricsCollector instance"""
    collector = MetricsCollector()
    collector.reset_metrics()
    return collector


def test_add_request_time(metrics_collector):
    """Test recording metrics for a request"""
    # Arrange
    endpoint = "/api/v1/test"
    method = "GET"
    status_code = 200
    duration = 0.1
    
    # Act
    metrics_collector.add_request_time(endpoint, method, status_code, duration)
    
    # Assert
    metrics = metrics_collector.get_metrics()
    assert f"{method}:{endpoint}" in metrics
    assert metrics[f"{method}:{endpoint}"]["count"] == 1
    assert metrics[f"{method}:{endpoint}"]["errors"] == 0
    assert metrics[f"{method}:{endpoint}"]["avg_time"] == duration


def test_add_error_request(metrics_collector):
    """Test recording metrics for an error request"""
    # Arrange
    endpoint = "/api/v1/test"
    method = "GET"
    status_code = 500  # Error status code
    duration = 0.1
    
    # Act
    metrics_collector.add_request_time(endpoint, method, status_code, duration)
    
    # Assert
    metrics = metrics_collector.get_metrics()
    assert metrics[f"{method}:{endpoint}"]["errors"] == 1
    assert metrics[f"{method}:{endpoint}"]["error_rate"] == 100.0  # 100% error rate


def test_add_many_requests(metrics_collector):
    """Test recording multiple requests for statistical calculations"""
    # Arrange
    endpoint = "/api/v1/test"
    method = "GET"
    durations = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    # Act - Add multiple requests
    for duration in durations:
        metrics_collector.add_request_time(endpoint, method, 200, duration)
    
    # Assert
    metrics = metrics_collector.get_metrics()
    assert metrics[f"{method}:{endpoint}"]["count"] == 5
    assert metrics[f"{method}:{endpoint}"]["avg_time"] == 0.3  # (0.1+0.2+0.3+0.4+0.5)/5
    assert metrics[f"{method}:{endpoint}"]["median_time"] == 0.3
    assert metrics[f"{method}:{endpoint}"]["min_time"] == 0.1
    assert metrics[f"{method}:{endpoint}"]["max_time"] == 0.5


def test_add_slow_requests(metrics_collector):
    """Test tracking of slow requests"""
    # Arrange
    endpoint = "/api/v1/test"
    method = "GET"
    duration = 0.6  # > 500ms threshold
    
    # Act
    metrics_collector.add_request_time(endpoint, method, 200, duration)
    
    # Assert
    slow_requests = metrics_collector.get_slow_requests()
    assert len(slow_requests) == 1
    assert slow_requests[0]["endpoint"] == endpoint
    assert slow_requests[0]["method"] == method
    assert slow_requests[0]["duration"] == duration


def test_limit_slow_requests(metrics_collector):
    """Test that slow requests list is limited to max size"""
    # Arrange - Set smaller max size for test
    metrics_collector._max_slow_requests = 3
    
    # Act - Add more than max_slow_requests
    for i in range(5):
        metrics_collector.add_request_time(f"/api/v1/test{i}", "GET", 200, 0.6)
    
    # Assert
    slow_requests = metrics_collector.get_slow_requests()
    assert len(slow_requests) == 3  # Only keeping latest 3
    
    # Check that we have the latest ones
    endpoints = [req["endpoint"] for req in slow_requests]
    assert "/api/v1/test0" not in endpoints
    assert "/api/v1/test1" not in endpoints
    
    # Al menos uno de los tres últimos debe estar presente
    assert any(endpoint in endpoints for endpoint in ["/api/v1/test2", "/api/v1/test3", "/api/v1/test4"])


def test_maintain_metrics_limit(metrics_collector):
    """Test that metrics are limited per endpoint"""
    # Arrange
    key = "GET:/api/v1/test"
    # Directly manipulate the underlying metrics to add more than the limit
    metrics_collector._metrics[key] = [0.1] * 1500
    
    # Act - Add one more request to trigger cleanup
    metrics_collector.add_request_time("/api/v1/test", "GET", 200, 0.2)
    
    # Assert
    # Should keep only the latest 1000 metrics (999 old ones + the new 0.2)
    assert len(metrics_collector._metrics[key]) == 1000
    assert 0.2 in metrics_collector._metrics[key]


def test_cleanup_old_timestamps(metrics_collector):
    """Test that old timestamps are cleaned up"""
    # Arrange
    key = "GET:/api/v1/test"
    current_time = time.time()
    
    # Add some old timestamps (>1 hour old)
    old_time = current_time - 3700  # 1 hour + 100 seconds ago
    metrics_collector._request_times_with_timestamp[key] = [
        (old_time, 0.1, 200),
        (old_time + 100, 0.2, 200),
        (current_time - 100, 0.3, 200)  # Recent one
    ]
    
    # Act - Add a new request to trigger cleanup
    metrics_collector.add_request_time("/api/v1/test", "GET", 200, 0.4)
    
    # Assert - Should only keep the recent ones (<1 hour old)
    timestamps = metrics_collector._request_times_with_timestamp[key]
    assert len(timestamps) == 2
    assert all(t[0] > current_time - 3600 for t in timestamps)


def test_get_uptime(metrics_collector):
    """Test getting API uptime"""
    # Arrange
    # Reset start time to a known value
    start_time = time.time() - 100  # 100 seconds ago
    metrics_collector._start_time = start_time
    
    # Act
    uptime = metrics_collector.get_uptime()
    
    # Assert
    assert uptime >= 100
    assert uptime < 110  # Allow for small delay in test execution


def test_get_request_count_timeframe(metrics_collector):
    """Test getting request count for a time frame"""
    # Arrange
    current_time = time.time()
    key1 = "GET:/api/v1/test1"
    key2 = "GET:/api/v1/test2"
    
    # Add some timestamps at different times
    metrics_collector._request_times_with_timestamp[key1] = [
        (current_time - 120, 0.1, 200),  # 2 minutes ago
        (current_time - 30, 0.2, 200),   # 30 seconds ago
    ]
    metrics_collector._request_times_with_timestamp[key2] = [
        (current_time - 50, 0.3, 200),   # 50 seconds ago
        (current_time - 20, 0.4, 200),   # 20 seconds ago
    ]
    
    # Act
    count_1m = metrics_collector.get_request_count_timeframe(60)  # Last minute
    count_3m = metrics_collector.get_request_count_timeframe(180)  # Last 3 minutes
    
    # Assert
    assert count_1m == 3  # 3 requests in the last minute
    assert count_3m == 4  # 4 requests in the last 3 minutes


def test_get_error_count_timeframe(metrics_collector):
    """Test getting error count for a time frame"""
    # Arrange
    current_time = time.time()
    key = "GET:/api/v1/test"
    
    # Add some timestamps with different status codes
    metrics_collector._request_times_with_timestamp[key] = [
        (current_time - 120, 0.1, 200),  # 2 minutes ago, ok
        (current_time - 30, 0.2, 500),   # 30 seconds ago, error
        (current_time - 20, 0.3, 404),   # 20 seconds ago, error
        (current_time - 10, 0.4, 200),   # 10 seconds ago, ok
    ]
    
    # Act
    error_count_1m = metrics_collector.get_error_count_timeframe(60)  # Last minute
    error_count_3m = metrics_collector.get_error_count_timeframe(180)  # Last 3 minutes
    
    # Assert
    assert error_count_1m == 2  # 2 errors in the last minute
    assert error_count_3m == 2  # 2 errors in the last 3 minutes (no more errors beyond 1m)


def test_get_avg_response_time_timeframe(metrics_collector):
    """Test getting average response time for a time frame"""
    # Arrange
    current_time = time.time()
    key = "GET:/api/v1/test"
    
    # Add some timestamps with different durations
    metrics_collector._request_times_with_timestamp[key] = [
        (current_time - 120, 0.1, 200),  # 2 minutes ago
        (current_time - 30, 0.2, 200),   # 30 seconds ago
        (current_time - 20, 0.3, 200),   # 20 seconds ago
        (current_time - 10, 0.4, 200),   # 10 seconds ago
    ]
    
    # Act
    avg_1m = metrics_collector.get_avg_response_time_timeframe(60)  # Last minute
    avg_3m = metrics_collector.get_avg_response_time_timeframe(180)  # Last 3 minutes
    
    # Assert
    assert avg_1m == 0.3  # (0.2 + 0.3 + 0.4) / 3
    assert avg_3m == 0.25  # (0.1 + 0.2 + 0.3 + 0.4) / 4


def test_get_endpoint_stats_timeframe(metrics_collector):
    """Test getting stats for a specific endpoint in a time frame"""
    # Arrange
    current_time = time.time()
    endpoint = "/api/v1/test"
    method = "GET"
    key = f"{method}:{endpoint}"
    
    # Add some timestamps with different durations and status codes
    metrics_collector._request_times_with_timestamp[key] = [
        (current_time - 120, 0.1, 200),  # 2 minutes ago, ok
        (current_time - 30, 0.2, 500),   # 30 seconds ago, error
        (current_time - 20, 0.3, 200),   # 20 seconds ago, ok
        (current_time - 10, 0.4, 200),   # 10 seconds ago, ok
    ]
    
    # Act
    stats = metrics_collector.get_endpoint_stats_timeframe(endpoint, method, 60)  # Last minute
    
    # Assert
    assert stats["count"] == 3
    assert stats["errors"] == 1
    assert stats["avg_time"] == 0.3  # (0.2 + 0.3 + 0.4) / 3
    assert stats["min_time"] == 0.2
    assert stats["max_time"] == 0.4
    assert stats["error_rate"] == 33.33333333333333  # 1/3 * 100


def test_get_endpoint_stats_timeframe_empty(metrics_collector):
    """Test getting stats for an endpoint with no data"""
    # Act
    stats = metrics_collector.get_endpoint_stats_timeframe("/api/v1/nonexistent", "GET", 60)
    
    # Assert
    assert stats == {"count": 0}


def test_reset_metrics(metrics_collector):
    """Test resetting all metrics"""
    # Arrange - Add some metrics
    metrics_collector.add_request_time("/api/v1/test", "GET", 200, 0.1)
    metrics_collector.add_request_time("/api/v1/test", "GET", 500, 0.6)  # Slow and error
    
    # Verify we have metrics
    assert len(metrics_collector.get_metrics()) > 1
    assert len(metrics_collector.get_slow_requests()) > 0
    
    # Act
    metrics_collector.reset_metrics()
    
    # Assert
    metrics = metrics_collector.get_metrics()
    assert len(metrics) == 1  # Just the _global entry
    assert metrics["_global"]["total_requests"] == 0
    assert len(metrics_collector.get_slow_requests()) == 0


def test_log_metrics(metrics_collector):
    """Test logging metrics summary"""
    # Arrange
    metrics_collector.add_request_time("/api/v1/endpoint1", "GET", 200, 0.1)
    metrics_collector.add_request_time("/api/v1/endpoint2", "POST", 500, 0.6)  # Slow and error
    
    # Act & Assert - Just verify it doesn't raise exceptions
    with patch("logging.Logger.info") as mock_info, \
         patch("logging.Logger.warning") as mock_warning:
        metrics_collector.log_metrics()
        
        # Verify log calls were made
        assert mock_info.call_count >= 2  # At least global + one endpoint
        assert mock_warning.call_count >= 1  # At least one warning for slow requests 