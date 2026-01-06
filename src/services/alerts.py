"""
Alerts service for critical failure detection and notification.

TECH-024: Implementar alertas para falhas críticas
- Alerta quando taxa de erro > 10% em janela de 5 minutos
- Alerta quando latência P95 > 10s
- Alerta quando autenticação falhar em qualquer integração
- Notificação via canal configurado (Slack, email, webhook)
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

import httpx

from src.config.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


# ==================== Alert Types and Severity ====================


class AlertType(str, Enum):
    """Types of alerts."""

    ERROR_RATE_HIGH = "error_rate_high"
    LATENCY_HIGH = "latency_high"
    AUTH_FAILURE = "auth_failure"
    INTEGRATION_DOWN = "integration_down"


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Available notification channels."""

    SLACK = "slack"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    """Represents an alert to be sent."""

    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    integration: Optional[str] = None
    endpoint: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert alert to dictionary."""
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "integration": self.integration,
            "endpoint": self.endpoint,
            "value": self.value,
            "threshold": self.threshold,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


# ==================== Alert State Management ====================


class AlertState:
    """Manages alert state for debounce and tracking."""

    def __init__(self, debounce_minutes: int = 15):
        self.debounce_minutes = debounce_minutes
        self._last_sent: dict[str, datetime] = {}
        self._active_alerts: list[Alert] = []
        self._alert_history: list[Alert] = []
        self._max_history = 100

    def _get_alert_key(self, alert: Alert) -> str:
        """Generate unique key for alert deduplication."""
        parts = [alert.alert_type.value]
        if alert.integration:
            parts.append(alert.integration)
        if alert.endpoint:
            parts.append(alert.endpoint)
        return ":".join(parts)

    def should_send(self, alert: Alert) -> bool:
        """
        Check if alert should be sent based on debounce rules.

        Args:
            alert: Alert to check

        Returns:
            True if alert should be sent, False if debounced
        """
        key = self._get_alert_key(alert)
        now = datetime.utcnow()

        # Critical alerts bypass debounce if escalating
        if alert.severity == AlertSeverity.CRITICAL:
            last_sent = self._last_sent.get(key)
            if last_sent:
                # Check if last alert was not critical (escalation)
                for prev_alert in reversed(self._alert_history):
                    if self._get_alert_key(prev_alert) == key:
                        if prev_alert.severity != AlertSeverity.CRITICAL:
                            return True  # Escalation bypasses debounce
                        break

        # Check debounce period
        if key in self._last_sent:
            time_since_last = now - self._last_sent[key]
            if time_since_last < timedelta(minutes=self.debounce_minutes):
                logger.debug(
                    "Alert debounced",
                    extra={
                        "alert_type": alert.alert_type.value,
                        "key": key,
                        "time_since_last_minutes": time_since_last.total_seconds() / 60,
                    },
                )
                return False

        return True

    def record_sent(self, alert: Alert) -> None:
        """Record that an alert was sent."""
        key = self._get_alert_key(alert)
        self._last_sent[key] = datetime.utcnow()
        self._active_alerts.append(alert)
        self._alert_history.append(alert)

        # Trim history if needed
        if len(self._alert_history) > self._max_history:
            self._alert_history = self._alert_history[-self._max_history :]

    def resolve_alert(self, alert_type: AlertType, integration: Optional[str] = None) -> None:
        """Mark an alert type as resolved."""
        self._active_alerts = [
            a
            for a in self._active_alerts
            if not (a.alert_type == alert_type and a.integration == integration)
        ]

    def get_active_alerts(self) -> list[Alert]:
        """Get list of currently active alerts."""
        return self._active_alerts.copy()


# Global alert state
_alert_state = AlertState()


# ==================== Notification Senders ====================


async def send_slack_notification(alert: Alert, webhook_url: str) -> bool:
    """
    Send alert notification to Slack.

    Args:
        alert: Alert to send
        webhook_url: Slack webhook URL

    Returns:
        True if sent successfully, False otherwise
    """
    # Format message with emoji based on severity
    severity_emoji = {
        AlertSeverity.INFO: ":information_source:",
        AlertSeverity.WARNING: ":warning:",
        AlertSeverity.CRITICAL: ":rotating_light:",
    }

    emoji = severity_emoji.get(alert.severity, ":bell:")

    # Build message blocks
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {alert.title}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": alert.message,
            },
        },
    ]

    # Add context fields
    context_elements = []
    if alert.integration:
        context_elements.append({"type": "mrkdwn", "text": f"*Integration:* {alert.integration}"})
    if alert.endpoint:
        context_elements.append({"type": "mrkdwn", "text": f"*Endpoint:* {alert.endpoint}"})
    if alert.value is not None and alert.threshold is not None:
        context_elements.append(
            {"type": "mrkdwn", "text": f"*Value:* {alert.value:.2f} (threshold: {alert.threshold:.2f})"}
        )
    context_elements.append({"type": "mrkdwn", "text": f"*Time:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"})

    if context_elements:
        blocks.append({"type": "context", "elements": context_elements})

    payload = {
        "text": f"[{alert.severity.value.upper()}] {alert.title}",
        "blocks": blocks,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code == 200:
                logger.info(
                    "Slack notification sent",
                    extra={"alert_type": alert.alert_type.value, "severity": alert.severity.value},
                )
                return True
            else:
                logger.error(
                    "Failed to send Slack notification",
                    extra={"status_code": response.status_code, "response": response.text[:200]},
                )
                return False
    except Exception as e:
        logger.error(
            "Error sending Slack notification",
            extra={"error": str(e)},
            exc_info=True,
        )
        return False


async def send_email_notification(alert: Alert) -> bool:
    """
    Send alert notification via email.

    Args:
        alert: Alert to send

    Returns:
        True if sent successfully, False otherwise
    """
    # Check if email is configured
    smtp_host = getattr(settings, "ALERT_EMAIL_SMTP_HOST", None)
    if not smtp_host:
        logger.debug("Email alerts not configured - skipping")
        return False

    # Email sending would require smtplib or aiosmtplib
    # This is a placeholder for future implementation
    logger.warning("Email notification not implemented yet")
    return False


async def send_webhook_notification(alert: Alert, webhook_url: str) -> bool:
    """
    Send alert notification to a generic webhook.

    Args:
        alert: Alert to send
        webhook_url: Webhook URL

    Returns:
        True if sent successfully, False otherwise
    """
    payload = alert.to_dict()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code in (200, 201, 202, 204):
                logger.info(
                    "Webhook notification sent",
                    extra={"alert_type": alert.alert_type.value, "url": webhook_url[:50]},
                )
                return True
            else:
                logger.error(
                    "Failed to send webhook notification",
                    extra={"status_code": response.status_code, "response": response.text[:200]},
                )
                return False
    except Exception as e:
        logger.error(
            "Error sending webhook notification",
            extra={"error": str(e)},
            exc_info=True,
        )
        return False


# ==================== Alert Sending ====================


async def send_alert(alert: Alert) -> bool:
    """
    Send an alert through configured channels.

    Respects debounce rules to prevent alert spam.

    Args:
        alert: Alert to send

    Returns:
        True if alert was sent (or debounced), False on error
    """
    # Check debounce
    if not _alert_state.should_send(alert):
        return True  # Successfully debounced

    # Log alert
    logger.warning(
        f"Alert triggered: {alert.title}",
        extra={
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "integration": alert.integration,
            "endpoint": alert.endpoint,
            "value": alert.value,
            "threshold": alert.threshold,
        },
    )

    sent = False

    # Send to Slack
    slack_webhook = getattr(settings, "ALERT_SLACK_WEBHOOK_URL", None)
    if slack_webhook:
        if await send_slack_notification(alert, slack_webhook):
            sent = True

    # Send to generic webhook
    webhook_url = getattr(settings, "ALERT_WEBHOOK_URL", None)
    if webhook_url:
        if await send_webhook_notification(alert, webhook_url):
            sent = True

    # Send email (if configured)
    if await send_email_notification(alert):
        sent = True

    # Record alert as sent
    if sent:
        _alert_state.record_sent(alert)

    return sent


# ==================== Alert Checks ====================


def check_error_rate(
    success_count: int,
    error_count: int,
    threshold: float = 0.10,
    integration: Optional[str] = None,
) -> Optional[Alert]:
    """
    Check if error rate exceeds threshold.

    Args:
        success_count: Number of successful requests
        error_count: Number of failed requests
        threshold: Error rate threshold (default 10%)
        integration: Integration name (optional)

    Returns:
        Alert if threshold exceeded, None otherwise
    """
    total = success_count + error_count
    if total == 0:
        return None

    error_rate = error_count / total

    if error_rate >= threshold:
        severity = AlertSeverity.CRITICAL if error_rate >= 0.25 else AlertSeverity.WARNING

        return Alert(
            alert_type=AlertType.ERROR_RATE_HIGH,
            severity=severity,
            title=f"High Error Rate{f' - {integration}' if integration else ''}",
            message=f"Error rate is {error_rate:.1%} ({error_count}/{total} requests failed)",
            integration=integration,
            value=error_rate,
            threshold=threshold,
            metadata={"success_count": success_count, "error_count": error_count},
        )

    return None


def check_latency_p95(
    p95_seconds: float,
    threshold_seconds: float = 10.0,
    endpoint: Optional[str] = None,
) -> Optional[Alert]:
    """
    Check if P95 latency exceeds threshold.

    Args:
        p95_seconds: P95 latency in seconds
        threshold_seconds: Threshold in seconds (default 10s)
        endpoint: Endpoint path (optional)

    Returns:
        Alert if threshold exceeded, None otherwise
    """
    if p95_seconds <= threshold_seconds:
        return None

    severity = AlertSeverity.CRITICAL if p95_seconds >= threshold_seconds * 2 else AlertSeverity.WARNING

    return Alert(
        alert_type=AlertType.LATENCY_HIGH,
        severity=severity,
        title=f"High Latency{f' - {endpoint}' if endpoint else ''}",
        message=f"P95 latency is {p95_seconds:.2f}s (threshold: {threshold_seconds:.0f}s)",
        endpoint=endpoint,
        value=p95_seconds,
        threshold=threshold_seconds,
    )


def check_auth_failure(
    integration: str,
    status_code: int,
    error_message: Optional[str] = None,
) -> Optional[Alert]:
    """
    Check if an authentication failure occurred.

    Args:
        integration: Integration name
        status_code: HTTP status code
        error_message: Optional error message

    Returns:
        Alert if auth failure detected, None otherwise
    """
    auth_failure_codes = [401, 403]

    if status_code not in auth_failure_codes:
        return None

    return Alert(
        alert_type=AlertType.AUTH_FAILURE,
        severity=AlertSeverity.CRITICAL,
        title=f"Authentication Failure - {integration}",
        message=f"Authentication failed with status {status_code}. {error_message or 'Check credentials.'}",
        integration=integration,
        metadata={"status_code": status_code, "error_message": error_message},
    )


# ==================== Alert Monitoring ====================


class AlertMonitor:
    """
    Background monitor for checking alert conditions.

    Runs periodic checks for error rates, latency, etc.
    """

    def __init__(
        self,
        check_interval_seconds: int = 60,
        error_rate_threshold: float = 0.10,
        latency_threshold_seconds: float = 10.0,
    ):
        self.check_interval_seconds = check_interval_seconds
        self.error_rate_threshold = error_rate_threshold
        self.latency_threshold_seconds = latency_threshold_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Metrics tracking for window-based calculations
        self._metrics_window: dict[str, list[tuple[datetime, bool]]] = {}
        self._window_minutes = 5

    def record_request(self, integration: str, success: bool) -> None:
        """
        Record a request result for error rate tracking.

        Args:
            integration: Integration name
            success: Whether request was successful
        """
        now = datetime.utcnow()
        if integration not in self._metrics_window:
            self._metrics_window[integration] = []

        self._metrics_window[integration].append((now, success))

        # Clean old entries
        cutoff = now - timedelta(minutes=self._window_minutes)
        self._metrics_window[integration] = [
            (ts, s) for ts, s in self._metrics_window[integration] if ts >= cutoff
        ]

    def _calculate_error_rate(self, integration: str) -> tuple[int, int]:
        """Calculate success/error counts for an integration."""
        if integration not in self._metrics_window:
            return 0, 0

        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=self._window_minutes)
        recent = [(ts, s) for ts, s in self._metrics_window[integration] if ts >= cutoff]

        success_count = sum(1 for _, s in recent if s)
        error_count = sum(1 for _, s in recent if not s)

        return success_count, error_count

    async def _run_checks(self) -> None:
        """Run all alert checks."""
        logger.debug("Running alert checks")

        # Check error rates for all tracked integrations
        for integration in list(self._metrics_window.keys()):
            success_count, error_count = self._calculate_error_rate(integration)

            alert = check_error_rate(
                success_count,
                error_count,
                threshold=self.error_rate_threshold,
                integration=integration,
            )

            if alert:
                await send_alert(alert)
            else:
                # Resolve any active error rate alerts for this integration
                _alert_state.resolve_alert(AlertType.ERROR_RATE_HIGH, integration)

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self._run_checks()
            except Exception as e:
                logger.error(
                    "Error in alert monitor loop",
                    extra={"error": str(e)},
                    exc_info=True,
                )

            await asyncio.sleep(self.check_interval_seconds)

    def start(self) -> None:
        """Start the alert monitor."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(
            "Alert monitor started",
            extra={"check_interval_seconds": self.check_interval_seconds},
        )

    def stop(self) -> None:
        """Stop the alert monitor."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Alert monitor stopped")


# Global alert monitor instance
_alert_monitor: Optional[AlertMonitor] = None


def get_alert_monitor() -> AlertMonitor:
    """Get or create the global alert monitor."""
    global _alert_monitor
    if _alert_monitor is None:
        _alert_monitor = AlertMonitor()
    return _alert_monitor


def start_alert_monitor() -> None:
    """Start the global alert monitor."""
    monitor = get_alert_monitor()
    monitor.start()


def stop_alert_monitor() -> None:
    """Stop the global alert monitor."""
    global _alert_monitor
    if _alert_monitor:
        _alert_monitor.stop()


# ==================== Integration with Metrics ====================


async def check_and_alert_auth_failure(
    integration: str,
    status_code: int,
    error_message: Optional[str] = None,
) -> None:
    """
    Check for auth failure and send alert immediately.

    This should be called when an integration returns 401/403.

    Args:
        integration: Integration name
        status_code: HTTP status code
        error_message: Optional error message
    """
    alert = check_auth_failure(integration, status_code, error_message)
    if alert:
        await send_alert(alert)


def record_integration_result(integration: str, success: bool) -> None:
    """
    Record an integration request result for monitoring.

    Args:
        integration: Integration name
        success: Whether request was successful
    """
    monitor = get_alert_monitor()
    monitor.record_request(integration, success)


# ==================== Utility Functions ====================


def get_active_alerts() -> list[dict]:
    """Get list of currently active alerts as dictionaries."""
    return [a.to_dict() for a in _alert_state.get_active_alerts()]


def get_alert_state() -> AlertState:
    """Get the global alert state instance."""
    return _alert_state
