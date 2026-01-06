"""
Data retention job for LGPD compliance (TECH-031).

This job runs the data retention functions periodically to:
- Anonymize expired conversation messages (daily)
- Anonymize expired conversation context (daily)
- Anonymize inactive leads (weekly)
- Cleanup completed pending operations (daily)

Can be run:
1. Via cron job: python -m src.jobs.data_retention_job
2. Via API endpoint: POST /api/lgpd/run-retention-jobs
3. Via scheduled task (APScheduler, Celery, etc.)
"""

import sys
from datetime import datetime

from src.services.data_retention import (
    anonymize_expired_context,
    anonymize_expired_messages,
    anonymize_inactive_leads,
    cleanup_completed_operations,
    run_all_retention_jobs,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


def run_daily_jobs() -> dict:
    """
    Run daily retention jobs.

    Jobs:
    - anonymize_expired_messages
    - anonymize_expired_context
    - cleanup_completed_operations

    Returns:
        Dictionary with results from each job
    """
    logger.info("Starting daily retention jobs")
    start_time = datetime.utcnow()

    results = {
        "messages": anonymize_expired_messages(),
        "context": anonymize_expired_context(),
        "operations": cleanup_completed_operations(),
    }

    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        "Daily retention jobs completed",
        extra={
            "duration_seconds": duration,
            "results": results,
        },
    )

    return results


def run_weekly_jobs() -> dict:
    """
    Run weekly retention jobs.

    Jobs:
    - anonymize_inactive_leads

    Returns:
        Dictionary with results from each job
    """
    logger.info("Starting weekly retention jobs")
    start_time = datetime.utcnow()

    results = {
        "leads": anonymize_inactive_leads(),
    }

    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        "Weekly retention jobs completed",
        extra={
            "duration_seconds": duration,
            "results": results,
        },
    )

    return results


def main():
    """
    Main entry point for running retention jobs from command line.

    Usage:
        python -m src.jobs.data_retention_job [--daily|--weekly|--all]

    Options:
        --daily: Run daily jobs only
        --weekly: Run weekly jobs only
        --all: Run all jobs (default)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Run LGPD data retention jobs",
    )
    parser.add_argument(
        "--daily",
        action="store_true",
        help="Run daily jobs only",
    )
    parser.add_argument(
        "--weekly",
        action="store_true",
        help="Run weekly jobs only",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all jobs (default)",
    )

    args = parser.parse_args()

    if args.daily:
        results = run_daily_jobs()
    elif args.weekly:
        results = run_weekly_jobs()
    else:
        # Default: run all jobs
        results = run_all_retention_jobs()

    # Print summary
    print("\n=== Data Retention Job Results ===")
    for job_name, stats in results.items():
        print(f"\n{job_name.upper()}:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    # Exit with error code if any errors occurred
    total_errors = sum(
        stats.get("errors", 0) for stats in results.values()
    )
    if total_errors > 0:
        print(f"\nCompleted with {total_errors} error(s)")
        sys.exit(1)
    else:
        print("\nAll jobs completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
