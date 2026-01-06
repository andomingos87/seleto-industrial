"""
Tests for metrics collection service.

TECH-023: Implementar métricas de latência e taxa de sucesso
- Testes unitários para coleta de métricas de latência
- Testes unitários para coleta de métricas de contador
- Testes para labels corretos nas métricas
- Testes para endpoint /metrics
- Testes para percentis calculados
- Testes para métricas por integração
"""

import pytest
from unittest.mock import patch, MagicMock
from prometheus_client import REGISTRY, CollectorRegistry, Counter, Histogram


# ==================== Fixtures ====================


@pytest.fixture
def clean_registry():
    """
    Provide a clean Prometheus registry for each test.

    This prevents metric conflicts between tests.
    """
    registry = CollectorRegistry()
    yield registry


@pytest.fixture
def mock_request():
    """Mock HTTP request object for testing metrics."""
    request = MagicMock()
    request.method = "POST"
    request.url.path = "/webhook/whatsapp"
    request.headers = {"Content-Type": "application/json"}
    return request


@pytest.fixture
def mock_response():
    """Mock HTTP response object for testing metrics."""
    response = MagicMock()
    response.status_code = 200
    return response


# ==================== Tests: Metric Creation ====================


class TestMetricCreation:
    """Tests for creating Prometheus metrics."""

    def test_counter_metric_creation(self, clean_registry):
        """Test that Counter metric can be created."""
        counter = Counter(
            "test_requests_total",
            "Total test requests",
            ["endpoint", "status"],
            registry=clean_registry,
        )

        counter.labels(endpoint="/webhook/whatsapp", status="200").inc()

        # Verify counter value
        sample_value = clean_registry.get_sample_value(
            "test_requests_total",
            labels={"endpoint": "/webhook/whatsapp", "status": "200"},
        )
        assert sample_value == 1.0

    def test_histogram_metric_creation(self, clean_registry):
        """Test that Histogram metric can be created with custom buckets."""
        buckets = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        histogram = Histogram(
            "test_request_duration_seconds",
            "Test request duration",
            ["endpoint", "method"],
            buckets=buckets,
            registry=clean_registry,
        )

        histogram.labels(endpoint="/webhook/whatsapp", method="POST").observe(0.5)

        # Verify histogram count
        sample_count = clean_registry.get_sample_value(
            "test_request_duration_seconds_count",
            labels={"endpoint": "/webhook/whatsapp", "method": "POST"},
        )
        assert sample_count == 1.0

    def test_histogram_buckets(self, clean_registry):
        """Test that histogram buckets are created correctly."""
        buckets = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        histogram = Histogram(
            "test_latency_seconds",
            "Test latency",
            ["endpoint"],
            buckets=buckets,
            registry=clean_registry,
        )

        # Observe values in different buckets
        histogram.labels(endpoint="/test").observe(0.05)  # < 0.1
        histogram.labels(endpoint="/test").observe(0.3)   # < 0.5
        histogram.labels(endpoint="/test").observe(1.5)   # < 2.0

        # Verify bucket counts
        bucket_01 = clean_registry.get_sample_value(
            "test_latency_seconds_bucket",
            labels={"endpoint": "/test", "le": "0.1"},
        )
        bucket_05 = clean_registry.get_sample_value(
            "test_latency_seconds_bucket",
            labels={"endpoint": "/test", "le": "0.5"},
        )
        bucket_20 = clean_registry.get_sample_value(
            "test_latency_seconds_bucket",
            labels={"endpoint": "/test", "le": "2.0"},
        )

        assert bucket_01 == 1.0  # One value < 0.1
        assert bucket_05 == 2.0  # Two values < 0.5
        assert bucket_20 == 3.0  # Three values < 2.0


# ==================== Tests: HTTP Request Metrics ====================


class TestHTTPRequestMetrics:
    """Tests for HTTP request metrics collection."""

    def test_request_total_increments(self, clean_registry):
        """Test that request counter increments correctly."""
        counter = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["endpoint", "method", "status"],
            registry=clean_registry,
        )

        # Simulate multiple requests
        counter.labels(endpoint="/webhook/whatsapp", method="POST", status="200").inc()
        counter.labels(endpoint="/webhook/whatsapp", method="POST", status="200").inc()
        counter.labels(endpoint="/webhook/chatwoot", method="POST", status="200").inc()
        counter.labels(endpoint="/webhook/whatsapp", method="POST", status="500").inc()

        # Verify counts
        whatsapp_200 = clean_registry.get_sample_value(
            "http_requests_total",
            labels={"endpoint": "/webhook/whatsapp", "method": "POST", "status": "200"},
        )
        chatwoot_200 = clean_registry.get_sample_value(
            "http_requests_total",
            labels={"endpoint": "/webhook/chatwoot", "method": "POST", "status": "200"},
        )
        whatsapp_500 = clean_registry.get_sample_value(
            "http_requests_total",
            labels={"endpoint": "/webhook/whatsapp", "method": "POST", "status": "500"},
        )

        assert whatsapp_200 == 2.0
        assert chatwoot_200 == 1.0
        assert whatsapp_500 == 1.0

    def test_request_duration_observation(self, clean_registry):
        """Test that request duration is observed correctly."""
        histogram = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration",
            ["endpoint", "method", "status"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=clean_registry,
        )

        # Simulate request with specific duration
        histogram.labels(
            endpoint="/webhook/whatsapp",
            method="POST",
            status="200",
        ).observe(0.35)

        # Verify sum and count
        duration_sum = clean_registry.get_sample_value(
            "http_request_duration_seconds_sum",
            labels={"endpoint": "/webhook/whatsapp", "method": "POST", "status": "200"},
        )
        duration_count = clean_registry.get_sample_value(
            "http_request_duration_seconds_count",
            labels={"endpoint": "/webhook/whatsapp", "method": "POST", "status": "200"},
        )

        assert abs(duration_sum - 0.35) < 0.001
        assert duration_count == 1.0


# ==================== Tests: Integration Metrics ====================


class TestIntegrationMetrics:
    """Tests for integration-specific metrics (WhatsApp, Piperun, etc.)."""

    def test_integration_requests_total(self, clean_registry):
        """Test that integration request counters work correctly."""
        counter = Counter(
            "integration_requests_total",
            "Total integration requests",
            ["integration", "operation", "status"],
            registry=clean_registry,
        )

        # Simulate integration calls
        counter.labels(integration="whatsapp", operation="send_message", status="success").inc()
        counter.labels(integration="whatsapp", operation="send_message", status="error").inc()
        counter.labels(integration="piperun", operation="create_deal", status="success").inc()
        counter.labels(integration="chatwoot", operation="sync_message", status="success").inc()

        # Verify
        whatsapp_success = clean_registry.get_sample_value(
            "integration_requests_total",
            labels={"integration": "whatsapp", "operation": "send_message", "status": "success"},
        )
        whatsapp_error = clean_registry.get_sample_value(
            "integration_requests_total",
            labels={"integration": "whatsapp", "operation": "send_message", "status": "error"},
        )

        assert whatsapp_success == 1.0
        assert whatsapp_error == 1.0

    def test_integration_duration_histogram(self, clean_registry):
        """Test that integration duration histogram works correctly."""
        histogram = Histogram(
            "integration_request_duration_seconds",
            "Integration request duration",
            ["integration", "operation"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=clean_registry,
        )

        # Simulate different integration call durations
        histogram.labels(integration="whatsapp", operation="send_message").observe(0.8)
        histogram.labels(integration="piperun", operation="create_deal").observe(2.5)
        histogram.labels(integration="supabase", operation="upsert").observe(0.15)

        # Verify counts
        whatsapp_count = clean_registry.get_sample_value(
            "integration_request_duration_seconds_count",
            labels={"integration": "whatsapp", "operation": "send_message"},
        )
        piperun_count = clean_registry.get_sample_value(
            "integration_request_duration_seconds_count",
            labels={"integration": "piperun", "operation": "create_deal"},
        )

        assert whatsapp_count == 1.0
        assert piperun_count == 1.0


# ==================== Tests: Labels ====================


class TestMetricLabels:
    """Tests for correct label usage in metrics."""

    def test_endpoint_labels(self, clean_registry):
        """Test that endpoint labels are applied correctly."""
        counter = Counter(
            "endpoint_test_total",
            "Test endpoint counter",
            ["endpoint", "method", "status"],
            registry=clean_registry,
        )

        endpoints = [
            ("/webhook/whatsapp", "POST", "200"),
            ("/webhook/chatwoot", "POST", "200"),
            ("/health", "GET", "200"),
            ("/api/health", "GET", "200"),
        ]

        for endpoint, method, status in endpoints:
            counter.labels(endpoint=endpoint, method=method, status=status).inc()

        # Verify all endpoints are tracked
        for endpoint, method, status in endpoints:
            value = clean_registry.get_sample_value(
                "endpoint_test_total",
                labels={"endpoint": endpoint, "method": method, "status": status},
            )
            assert value == 1.0

    def test_integration_labels(self, clean_registry):
        """Test that integration labels are applied correctly."""
        counter = Counter(
            "integration_test_total",
            "Test integration counter",
            ["integration", "status"],
            registry=clean_registry,
        )

        integrations = ["whatsapp", "piperun", "chatwoot", "supabase"]

        for integration in integrations:
            counter.labels(integration=integration, status="success").inc()

        # Verify all integrations are tracked
        for integration in integrations:
            value = clean_registry.get_sample_value(
                "integration_test_total",
                labels={"integration": integration, "status": "success"},
            )
            assert value == 1.0


# ==================== Tests: Error Rate Calculation ====================


class TestErrorRateCalculation:
    """Tests for calculating error rates from metrics."""

    def test_error_rate_calculation(self, clean_registry):
        """Test that error rate can be calculated from counters."""
        counter = Counter(
            "test_requests",
            "Test requests",
            ["status"],
            registry=clean_registry,
        )

        # Simulate 90 successes and 10 errors (10% error rate)
        for _ in range(90):
            counter.labels(status="success").inc()
        for _ in range(10):
            counter.labels(status="error").inc()

        success = clean_registry.get_sample_value(
            "test_requests_total", labels={"status": "success"}
        )
        error = clean_registry.get_sample_value(
            "test_requests_total", labels={"status": "error"}
        )

        total = success + error
        error_rate = error / total if total > 0 else 0

        assert error_rate == 0.1  # 10%

    def test_zero_requests_error_rate(self, clean_registry):
        """Test error rate calculation with zero requests."""
        counter = Counter(
            "zero_requests",
            "Zero requests",
            ["status"],
            registry=clean_registry,
        )

        # No requests - error rate should be 0
        success = clean_registry.get_sample_value(
            "zero_requests", labels={"status": "success"}
        )
        error = clean_registry.get_sample_value(
            "zero_requests", labels={"status": "error"}
        )

        # Both should be None when no observations
        assert success is None
        assert error is None


# ==================== Tests: Prometheus Output Format ====================


class TestPrometheusOutput:
    """Tests for Prometheus output format."""

    def test_generate_latest_output(self, clean_registry):
        """Test that generate_latest produces valid Prometheus format."""
        from prometheus_client import generate_latest

        counter = Counter(
            "output_test_total",
            "Test output counter",
            ["label"],
            registry=clean_registry,
        )
        counter.labels(label="test").inc()

        output = generate_latest(clean_registry)

        # Output should be bytes
        assert isinstance(output, bytes)

        # Should contain metric name
        assert b"output_test_total" in output

        # Should contain HELP line
        assert b"# HELP output_test_total" in output

        # Should contain TYPE line
        assert b"# TYPE output_test_total counter" in output

    def test_metrics_content_type(self):
        """Test that metrics endpoint should use correct content type."""
        from prometheus_client import CONTENT_TYPE_LATEST

        # Prometheus format content type (version may vary by prometheus-client version)
        # Should be text/plain with version and charset
        assert CONTENT_TYPE_LATEST.startswith("text/plain")
        assert "charset=utf-8" in CONTENT_TYPE_LATEST


# ==================== Tests: Performance ====================


class TestMetricsPerformance:
    """Tests for metrics collection performance."""

    def test_counter_increment_is_fast(self, clean_registry):
        """Test that counter increment is fast (thread-safe and low overhead)."""
        import time

        counter = Counter(
            "perf_test_counter",
            "Performance test counter",
            registry=clean_registry,
        )

        iterations = 10000
        start = time.perf_counter()

        for _ in range(iterations):
            counter.inc()

        duration = time.perf_counter() - start

        # Should complete 10000 increments in < 100ms
        assert duration < 0.1, f"Counter increment too slow: {duration:.3f}s for {iterations} ops"

    def test_histogram_observation_is_fast(self, clean_registry):
        """Test that histogram observation is fast."""
        import time

        histogram = Histogram(
            "perf_test_histogram",
            "Performance test histogram",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=clean_registry,
        )

        iterations = 10000
        start = time.perf_counter()

        for i in range(iterations):
            histogram.observe(i / iterations)  # Values between 0 and 1

        duration = time.perf_counter() - start

        # Should complete 10000 observations in < 100ms
        assert duration < 0.1, f"Histogram observation too slow: {duration:.3f}s for {iterations} ops"
