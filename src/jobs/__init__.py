"""
Background jobs for the Seleto Industrial SDR Agent.

This package contains scheduled jobs for:
- sync_pending_operations: Retry failed CRM operations (TECH-030)
"""

from src.jobs.sync_pending_operations import (
    process_pending_operations,
    retry_all_failed_operations,
    retry_failed_operation,
)

__all__ = [
    "process_pending_operations",
    "retry_all_failed_operations",
    "retry_failed_operation",
]
