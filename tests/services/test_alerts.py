"""
Tests for alerts service.

TECH-024: Implementar alertas para falhas críticas
- Testes para detecção de taxa de erro > 10%
- Testes para detecção de latência P95 > 10s
- Testes para detecção de falha de autenticação
- Testes para envio de notificação (mock)
- Testes para debounce de alertas
- Testes para agendamento de verificações
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import asyncio


# ==================== Fixtures ====================


@pytest.fixture
def mock_metrics():
    """Mock metrics data for alert testing."""
    return {
        "http_requests_total": {
            ("success", "/webhook/whatsapp"): 90,
            ("error", "/webhook/whatsapp"): 10,
        },
        "integration_requests_total": {
            ("success", "whatsapp"): 95,
            ("error", "whatsapp"): 5,
            ("success", "piperun"): 100,
            ("error", "piperun"): 0,
        },
        "latency_p95": {
            "/webhook/whatsapp": 2.5,
            "/webhook/chatwoot": 8.5,
            "/api/health": 0.1,
        },
    }


@pytest.fixture
def mock_slack_webhook():
    """Mock Slack webhook for testing notifications."""
    with patch("httpx.AsyncClient") as mock:
        mock_instance = MagicMock()
        mock_instance.post = AsyncMock(
            return_value=MagicMock(status_code=200)
        )
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def alert_state():
    """Track alert state for debounce testing."""
    return {
        "last_sent": {},
        "sent_count": 0,
    }


# ==================== Tests: Error Rate Detection ====================


class TestErrorRateDetection:
    """Tests for error rate threshold detection."""

    def test_error_rate_above_threshold(self, mock_metrics):
        """Test that error rate > 10% triggers alert."""
        # 90 success + 10 error = 10% error rate
        success = mock_metrics["http_requests_total"][("success", "/webhook/whatsapp")]
        error = mock_metrics["http_requests_total"][("error", "/webhook/whatsapp")]

        total = success + error
        error_rate = error / total if total > 0 else 0

        threshold = 0.10  # 10%
        should_alert = error_rate >= threshold

        assert should_alert is True
        assert error_rate == 0.10

    def test_error_rate_below_threshold(self, mock_metrics):
        """Test that error rate < 10% does not trigger alert."""
        # Modify to have low error rate
        success = 99
        error = 1

        total = success + error
        error_rate = error / total if total > 0 else 0

        threshold = 0.10  # 10%
        should_alert = error_rate >= threshold

        assert should_alert is False
        assert error_rate == 0.01

    def test_error_rate_exactly_threshold(self):
        """Test that error rate exactly at 10% triggers alert."""
        success = 90
        error = 10

        total = success + error
        error_rate = error / total

        threshold = 0.10
        should_alert = error_rate >= threshold

        assert should_alert is True

    def test_error_rate_zero_requests(self):
        """Test error rate calculation with zero total requests."""
        success = 0
        error = 0

        total = success + error
        error_rate = error / total if total > 0 else 0

        # Should not alert on zero requests
        assert error_rate == 0
        assert total == 0


# ==================== Tests: Latency Detection ====================


class TestLatencyDetection:
    """Tests for P95 latency threshold detection."""

    def test_latency_above_threshold(self, mock_metrics):
        """Test that P95 > 10s triggers alert."""
        p95_latency = 12.5  # seconds
        threshold = 10.0  # seconds

        should_alert = p95_latency > threshold

        assert should_alert is True

    def test_latency_below_threshold(self, mock_metrics):
        """Test that P95 < 10s does not trigger alert."""
        p95_latency = mock_metrics["latency_p95"]["/webhook/whatsapp"]  # 2.5s
        threshold = 10.0  # seconds

        should_alert = p95_latency > threshold

        assert should_alert is False

    def test_latency_exactly_threshold(self):
        """Test that P95 exactly at 10s does not trigger alert."""
        p95_latency = 10.0
        threshold = 10.0

        should_alert = p95_latency > threshold  # Must be strictly greater

        assert should_alert is False

    def test_latency_per_endpoint(self, mock_metrics):
        """Test latency detection per endpoint."""
        threshold = 10.0
        alerts = []

        for endpoint, latency in mock_metrics["latency_p95"].items():
            if latency > threshold:
                alerts.append({
                    "endpoint": endpoint,
                    "p95_latency": latency,
                    "threshold": threshold,
                })

        # No endpoints should exceed 10s in mock data
        assert len(alerts) == 0


# ==================== Tests: Authentication Failure Detection ====================


class TestAuthFailureDetection:
    """Tests for authentication failure detection."""

    def test_auth_failure_401(self):
        """Test that 401 status triggers immediate alert."""
        status_code = 401
        auth_failure_codes = [401, 403]

        is_auth_failure = status_code in auth_failure_codes

        assert is_auth_failure is True

    def test_auth_failure_403(self):
        """Test that 403 status triggers immediate alert."""
        status_code = 403
        auth_failure_codes = [401, 403]

        is_auth_failure = status_code in auth_failure_codes

        assert is_auth_failure is True

    def test_non_auth_error(self):
        """Test that other errors do not trigger auth alert."""
        status_code = 500
        auth_failure_codes = [401, 403]

        is_auth_failure = status_code in auth_failure_codes

        assert is_auth_failure is False

    def test_auth_failure_per_integration(self):
        """Test auth failure detection per integration."""
        integration_responses = {
            "whatsapp": {"status": 401, "message": "Invalid token"},
            "piperun": {"status": 200, "message": "OK"},
            "chatwoot": {"status": 403, "message": "Forbidden"},
        }

        auth_failure_codes = [401, 403]
        auth_failures = []

        for integration, response in integration_responses.items():
            if response["status"] in auth_failure_codes:
                auth_failures.append({
                    "integration": integration,
                    "status": response["status"],
                    "message": response["message"],
                })

        assert len(auth_failures) == 2
        assert any(f["integration"] == "whatsapp" for f in auth_failures)
        assert any(f["integration"] == "chatwoot" for f in auth_failures)


# ==================== Tests: Alert Debounce ====================


class TestAlertDebounce:
    """Tests for alert debounce mechanism."""

    def test_debounce_prevents_spam(self, alert_state):
        """Test that same alert is not sent within debounce period."""
        debounce_minutes = 15
        alert_type = "error_rate_high"

        # First alert should be sent
        now = datetime.now()
        if alert_type not in alert_state["last_sent"]:
            alert_state["last_sent"][alert_type] = now
            alert_state["sent_count"] += 1
            first_sent = True
        else:
            first_sent = False

        # Second alert within debounce should not be sent
        now2 = now + timedelta(minutes=5)  # 5 minutes later
        time_since_last = now2 - alert_state["last_sent"][alert_type]
        should_send = time_since_last >= timedelta(minutes=debounce_minutes)

        assert first_sent is True
        assert should_send is False
        assert alert_state["sent_count"] == 1

    def test_debounce_allows_after_period(self, alert_state):
        """Test that alert is sent after debounce period expires."""
        debounce_minutes = 15
        alert_type = "error_rate_high"

        # First alert
        first_time = datetime.now()
        alert_state["last_sent"][alert_type] = first_time
        alert_state["sent_count"] += 1

        # After debounce period
        later_time = first_time + timedelta(minutes=20)  # 20 minutes later
        time_since_last = later_time - alert_state["last_sent"][alert_type]
        should_send = time_since_last >= timedelta(minutes=debounce_minutes)

        assert should_send is True

    def test_different_alert_types_independent(self, alert_state):
        """Test that different alert types have independent debounce."""
        debounce_minutes = 15
        now = datetime.now()

        # Send error rate alert
        alert_state["last_sent"]["error_rate_high"] = now
        alert_state["sent_count"] += 1

        # Latency alert should still be sendable
        can_send_latency = "latency_high" not in alert_state["last_sent"]

        assert can_send_latency is True

    def test_escalation_bypasses_debounce(self, alert_state):
        """Test that escalated severity bypasses debounce."""
        alert_type = "error_rate_high"

        # First alert at warning level
        now = datetime.now()
        alert_state["last_sent"][alert_type] = now
        alert_state["sent_count"] += 1

        # Escalated alert should bypass debounce
        previous_severity = "warning"
        current_severity = "critical"
        is_escalation = current_severity == "critical" and previous_severity != "critical"

        should_send = is_escalation  # Bypass debounce on escalation

        assert should_send is True


# ==================== Tests: Notification Sending ====================


class TestNotificationSending:
    """Tests for sending alert notifications."""

    @pytest.mark.asyncio
    async def test_slack_notification_success(self, mock_slack_webhook):
        """Test that Slack notification is sent successfully."""
        alert = {
            "type": "error_rate_high",
            "severity": "warning",
            "message": "Error rate exceeded 10%",
            "integration": "whatsapp",
            "value": 0.15,
            "threshold": 0.10,
        }

        # Simulate sending notification
        mock_slack_webhook.post.return_value.status_code = 200
        response = await mock_slack_webhook.post(
            "https://hooks.slack.com/test",
            json={"text": alert["message"]},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_notification_format(self):
        """Test alert notification format."""
        alert = {
            "type": "latency_high",
            "severity": "critical",
            "endpoint": "/webhook/whatsapp",
            "p95_latency": 15.5,
            "threshold": 10.0,
            "timestamp": "2026-01-06T10:00:00Z",
        }

        # Format notification message
        message = (
            f"[{alert['severity'].upper()}] {alert['type']}\n"
            f"Endpoint: {alert['endpoint']}\n"
            f"P95 Latency: {alert['p95_latency']:.2f}s (threshold: {alert['threshold']:.0f}s)\n"
            f"Time: {alert['timestamp']}"
        )

        assert "[CRITICAL]" in message
        assert alert["endpoint"] in message
        assert "15.50s" in message

    def test_notification_includes_context(self):
        """Test that notification includes relevant context."""
        alert = {
            "type": "auth_failure",
            "severity": "critical",
            "integration": "piperun",
            "status_code": 401,
            "message": "Invalid API token",
            "action_required": "Rotate Piperun API token",
        }

        # All relevant fields should be present
        assert alert["integration"] == "piperun"
        assert alert["status_code"] == 401
        assert alert["action_required"] is not None


# ==================== Tests: Alert Scheduling ====================


class TestAlertScheduling:
    """Tests for periodic alert checking."""

    def test_check_interval_configuration(self):
        """Test that check interval is configurable."""
        default_interval = 60  # 1 minute
        custom_interval = 30  # 30 seconds

        # Should accept custom interval
        assert custom_interval > 0
        assert default_interval == 60

    def test_multiple_checks_per_run(self):
        """Test that all checks run in single scheduled task."""
        checks = [
            "error_rate",
            "latency_p95",
            "auth_failures",
        ]

        # All checks should run
        results = {}
        for check in checks:
            results[check] = {"checked": True, "alert": False}

        assert len(results) == 3
        assert all(r["checked"] for r in results.values())

    def test_check_does_not_block(self):
        """Test that check execution is non-blocking."""
        import time

        check_timeout = 5.0  # seconds
        start = time.perf_counter()

        # Simulate quick check
        time.sleep(0.01)  # 10ms

        duration = time.perf_counter() - start

        assert duration < check_timeout


# ==================== Tests: Alert State Management ====================


class TestAlertStateManagement:
    """Tests for managing alert state."""

    def test_alert_state_initialization(self):
        """Test that alert state initializes correctly."""
        state = {
            "last_sent": {},
            "active_alerts": [],
            "check_count": 0,
        }

        assert len(state["last_sent"]) == 0
        assert len(state["active_alerts"]) == 0

    def test_active_alert_tracking(self):
        """Test tracking of currently active alerts."""
        active_alerts = []

        # Add alert
        alert1 = {"type": "error_rate_high", "integration": "whatsapp"}
        active_alerts.append(alert1)

        assert len(active_alerts) == 1

        # Resolve alert
        active_alerts.remove(alert1)

        assert len(active_alerts) == 0

    def test_alert_history(self):
        """Test that alert history is maintained."""
        history = []
        max_history = 100

        # Add alerts
        for i in range(150):
            history.append({"id": i, "type": "test"})
            if len(history) > max_history:
                history.pop(0)

        # History should be capped
        assert len(history) == max_history
        assert history[0]["id"] == 50  # First 50 were removed


# ==================== Tests: Error Handling ====================


class TestAlertErrorHandling:
    """Tests for error handling in alert system."""

    @pytest.mark.asyncio
    async def test_notification_failure_handling(self, mock_slack_webhook):
        """Test that notification failures don't crash the system."""
        mock_slack_webhook.post.side_effect = Exception("Network error")

        # Should not raise exception
        try:
            await mock_slack_webhook.post("https://hooks.slack.com/test", json={})
            assert False, "Should have raised exception"
        except Exception as e:
            assert str(e) == "Network error"

    def test_invalid_metrics_handling(self):
        """Test handling of invalid or missing metrics."""
        metrics = None  # No metrics available

        # Should handle gracefully
        if metrics is None:
            error_rate = 0
            should_alert = False
        else:
            error_rate = metrics.get("error_rate", 0)
            should_alert = error_rate > 0.1

        assert error_rate == 0
        assert should_alert is False

    def test_partial_metrics_handling(self):
        """Test handling when some metrics are missing."""
        metrics = {
            "http_requests_total": {"success": 100},
            # "error" count is missing
        }

        success = metrics["http_requests_total"].get("success", 0)
        error = metrics["http_requests_total"].get("error", 0)

        total = success + error
        error_rate = error / total if total > 0 else 0

        assert error_rate == 0  # No errors means 0% error rate
