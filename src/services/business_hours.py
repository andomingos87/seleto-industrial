"""
Business Hours Service for SDR Agent.

This module provides functions to check if the current time is within
configured business hours. This is used to determine:
- Whether the SDR agent should auto-resume after being paused
- Whether to require explicit /retomar command from SDR

Configuration is loaded from config/business_hours.yaml with optional
environment variable overrides.
"""

from datetime import datetime, time
from pathlib import Path
from typing import Optional

import yaml
from zoneinfo import ZoneInfo

from src.config.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default configuration
DEFAULT_TIMEZONE = "America/Sao_Paulo"
DEFAULT_SCHEDULE = {
    "monday": {"start": "08:00", "end": "18:00"},
    "tuesday": {"start": "08:00", "end": "18:00"},
    "wednesday": {"start": "08:00", "end": "18:00"},
    "thursday": {"start": "08:00", "end": "18:00"},
    "friday": {"start": "08:00", "end": "18:00"},
    "saturday": None,
    "sunday": None,
}

# Day name mapping (Python weekday() to config key)
DAY_NAMES = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

# Cached configuration
_config: Optional[dict] = None


def _get_config_path() -> Path:
    """Get the path to the business hours configuration file."""
    # Try relative to project root
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "config" / "business_hours.yaml"
    return config_path


def _load_config() -> dict:
    """
    Load business hours configuration from YAML file with env overrides.

    Priority:
    1. Environment variables (BUSINESS_HOURS_*)
    2. YAML config file (config/business_hours.yaml)
    3. Default values

    Returns:
        Configuration dictionary with timezone and schedule
    """
    global _config

    if _config is not None:
        return _config

    config_path = _get_config_path()

    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                _config = yaml.safe_load(f)
                logger.info(
                    "Business hours configuration loaded",
                    extra={"path": str(config_path)},
                )
        else:
            logger.warning(
                "Business hours config file not found, using defaults",
                extra={"path": str(config_path)},
            )
            _config = {
                "timezone": DEFAULT_TIMEZONE,
                "schedule": DEFAULT_SCHEDULE.copy(),
            }
    except Exception as e:
        logger.error(
            "Failed to load business hours config, using defaults",
            extra={"error": str(e), "path": str(config_path)},
        )
        _config = {
            "timezone": DEFAULT_TIMEZONE,
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

    # Validate and apply defaults for missing fields
    if "timezone" not in _config:
        _config["timezone"] = DEFAULT_TIMEZONE
    if "schedule" not in _config:
        _config["schedule"] = DEFAULT_SCHEDULE.copy()

    # Apply environment variable overrides
    if settings.BUSINESS_HOURS_TIMEZONE:
        _config["timezone"] = settings.BUSINESS_HOURS_TIMEZONE
        logger.info(
            "Business hours timezone overridden by env var",
            extra={"timezone": settings.BUSINESS_HOURS_TIMEZONE},
        )

    # Apply start/end time overrides to all weekdays
    if settings.BUSINESS_HOURS_START or settings.BUSINESS_HOURS_END:
        start = settings.BUSINESS_HOURS_START or "08:00"
        end = settings.BUSINESS_HOURS_END or "18:00"

        for day in DAY_NAMES[:5]:  # Monday to Friday
            if _config["schedule"].get(day) is not None:
                _config["schedule"][day] = {"start": start, "end": end}

        logger.info(
            "Business hours times overridden by env vars",
            extra={"start": start, "end": end},
        )

    return _config


def reload_config() -> dict:
    """
    Force reload the business hours configuration.

    Useful for testing or when config file changes.

    Returns:
        Reloaded configuration dictionary
    """
    global _config
    _config = None
    return _load_config()


def get_timezone() -> ZoneInfo:
    """
    Get the configured timezone.

    Returns:
        ZoneInfo object for the configured timezone
    """
    config = _load_config()
    timezone_str = config.get("timezone", DEFAULT_TIMEZONE)

    try:
        return ZoneInfo(timezone_str)
    except Exception as e:
        logger.warning(
            f"Invalid timezone '{timezone_str}', using default",
            extra={"error": str(e), "default": DEFAULT_TIMEZONE},
        )
        return ZoneInfo(DEFAULT_TIMEZONE)


def _parse_time(time_str: str) -> time:
    """
    Parse time string in HH:MM format.

    Args:
        time_str: Time string in HH:MM format

    Returns:
        datetime.time object

    Raises:
        ValueError: If time string is invalid
    """
    parts = time_str.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {time_str}")

    hours = int(parts[0])
    minutes = int(parts[1])

    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError(f"Invalid time values: {time_str}")

    return time(hours, minutes)


def get_schedule_for_day(day_name: str) -> Optional[dict]:
    """
    Get the schedule for a specific day.

    Args:
        day_name: Day name (monday, tuesday, etc.)

    Returns:
        Dictionary with start/end times, or None if closed
    """
    config = _load_config()
    schedule = config.get("schedule", DEFAULT_SCHEDULE)
    return schedule.get(day_name.lower())


def is_business_hours(check_time: Optional[datetime] = None) -> bool:
    """
    Check if the given time (or current time) is within business hours.

    Args:
        check_time: Optional datetime to check. If None, uses current time.
                   If naive (no timezone), assumes configured timezone.

    Returns:
        True if within business hours, False otherwise
    """
    tz = get_timezone()

    # Get current time if not provided
    if check_time is None:
        check_time = datetime.now(tz)
    elif check_time.tzinfo is None:
        # Assume configured timezone for naive datetimes
        check_time = check_time.replace(tzinfo=tz)
    else:
        # Convert to configured timezone
        check_time = check_time.astimezone(tz)

    # Get day of week
    day_index = check_time.weekday()  # 0 = Monday
    day_name = DAY_NAMES[day_index]

    # Get schedule for this day
    day_schedule = get_schedule_for_day(day_name)

    # If no schedule (None), the day is closed
    if day_schedule is None:
        logger.debug(
            "Outside business hours - day is closed",
            extra={"day": day_name, "time": check_time.isoformat()},
        )
        return False

    try:
        start_time = _parse_time(day_schedule["start"])
        end_time = _parse_time(day_schedule["end"])
    except (KeyError, ValueError) as e:
        logger.warning(
            f"Invalid schedule for {day_name}, treating as closed",
            extra={"error": str(e), "schedule": day_schedule},
        )
        return False

    # Get just the time component
    current_time = check_time.time()

    # Check if within hours
    is_within = start_time <= current_time <= end_time

    logger.debug(
        "Business hours check",
        extra={
            "day": day_name,
            "current_time": current_time.isoformat(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "is_within": is_within,
        },
    )

    return is_within


def should_auto_resume() -> bool:
    """
    Check if the agent should auto-resume after being paused.

    According to PRD:
    - During business hours: SDR must use /retomar command (no auto-resume)
    - Outside business hours: Agent auto-resumes when lead sends new message

    Returns:
        True if agent should auto-resume (outside business hours)
        False if SDR must use command (during business hours)
    """
    return not is_business_hours()


def get_current_schedule_status() -> dict:
    """
    Get the current schedule status for debugging/logging.

    Returns:
        Dictionary with current status information
    """
    tz = get_timezone()
    now = datetime.now(tz)
    day_name = DAY_NAMES[now.weekday()]
    day_schedule = get_schedule_for_day(day_name)

    return {
        "timezone": str(tz),
        "current_time": now.isoformat(),
        "day": day_name,
        "day_schedule": day_schedule,
        "is_business_hours": is_business_hours(now),
        "should_auto_resume": should_auto_resume(),
    }
