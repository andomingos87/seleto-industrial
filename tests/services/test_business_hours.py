"""
Tests for business hours service.

This module tests the business hours configuration and verification,
including timezone handling, day-of-week rules, and start/end times.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo

from src.services.business_hours import (
    is_business_hours,
    should_auto_resume,
    get_timezone,
    get_schedule_for_day,
    get_current_schedule_status,
    reload_config,
    _parse_time,
    DEFAULT_TIMEZONE,
    DEFAULT_SCHEDULE,
    DAY_NAMES,
)


# Fixtures for business hours configuration
@pytest.fixture
def default_business_hours_config():
    """Default business hours configuration (Mon-Fri, 08:00-18:00, Sao Paulo)."""
    return {
        "timezone": "America/Sao_Paulo",
        "schedule": {
            "monday": {"start": "08:00", "end": "18:00"},
            "tuesday": {"start": "08:00", "end": "18:00"},
            "wednesday": {"start": "08:00", "end": "18:00"},
            "thursday": {"start": "08:00", "end": "18:00"},
            "friday": {"start": "08:00", "end": "18:00"},
            "saturday": None,
            "sunday": None,
        },
    }


@pytest.fixture
def extended_hours_config():
    """Extended business hours including Saturday morning."""
    return {
        "timezone": "America/Sao_Paulo",
        "schedule": {
            "monday": {"start": "07:00", "end": "19:00"},
            "tuesday": {"start": "07:00", "end": "19:00"},
            "wednesday": {"start": "07:00", "end": "19:00"},
            "thursday": {"start": "07:00", "end": "19:00"},
            "friday": {"start": "07:00", "end": "19:00"},
            "saturday": {"start": "08:00", "end": "12:00"},
            "sunday": None,
        },
    }


@pytest.fixture
def reset_config():
    """Reset config cache before and after test."""
    import src.services.business_hours as bh
    bh._config = None
    yield
    bh._config = None


class TestParseTime:
    """Tests for _parse_time helper function."""

    def test_parses_valid_time(self):
        """Test that valid time strings are parsed correctly."""
        result = _parse_time("08:00")
        assert result.hour == 8
        assert result.minute == 0

    def test_parses_time_with_minutes(self):
        """Test parsing time with non-zero minutes."""
        result = _parse_time("14:30")
        assert result.hour == 14
        assert result.minute == 30

    def test_parses_midnight(self):
        """Test parsing midnight."""
        result = _parse_time("00:00")
        assert result.hour == 0
        assert result.minute == 0

    def test_parses_end_of_day(self):
        """Test parsing end of day."""
        result = _parse_time("23:59")
        assert result.hour == 23
        assert result.minute == 59

    def test_raises_on_invalid_format(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError):
            _parse_time("8:00:00")

    def test_raises_on_invalid_hours(self):
        """Test that invalid hours raise ValueError."""
        with pytest.raises(ValueError):
            _parse_time("25:00")

    def test_raises_on_invalid_minutes(self):
        """Test that invalid minutes raise ValueError."""
        with pytest.raises(ValueError):
            _parse_time("08:60")


class TestGetTimezone:
    """Tests for get_timezone function."""

    def test_returns_default_timezone(self, reset_config):
        """Test that default timezone is returned."""
        with patch("src.services.business_hours._get_config_path") as mock_path:
            mock_path.return_value = MagicMock(exists=lambda: False)
            tz = get_timezone()
            assert str(tz) == DEFAULT_TIMEZONE

    def test_returns_configured_timezone(self, reset_config):
        """Test that configured timezone is returned."""
        import src.services.business_hours as bh
        bh._config = {"timezone": "America/New_York", "schedule": DEFAULT_SCHEDULE}

        tz = get_timezone()
        assert str(tz) == "America/New_York"

    def test_falls_back_on_invalid_timezone(self, reset_config):
        """Test that invalid timezone falls back to default."""
        import src.services.business_hours as bh
        bh._config = {"timezone": "Invalid/Timezone", "schedule": DEFAULT_SCHEDULE}

        tz = get_timezone()
        assert str(tz) == DEFAULT_TIMEZONE


class TestGetScheduleForDay:
    """Tests for get_schedule_for_day function."""

    def test_returns_schedule_for_weekday(self, reset_config):
        """Test that schedule is returned for a weekday."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": DEFAULT_TIMEZONE,
            "schedule": {"monday": {"start": "09:00", "end": "17:00"}},
        }

        schedule = get_schedule_for_day("monday")
        assert schedule == {"start": "09:00", "end": "17:00"}

    def test_returns_none_for_closed_day(self, reset_config):
        """Test that None is returned for closed day."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": DEFAULT_TIMEZONE,
            "schedule": {"saturday": None},
        }

        schedule = get_schedule_for_day("saturday")
        assert schedule is None

    def test_handles_case_insensitive_day(self, reset_config):
        """Test that day name is case insensitive."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": DEFAULT_TIMEZONE,
            "schedule": {"monday": {"start": "08:00", "end": "18:00"}},
        }

        schedule = get_schedule_for_day("MONDAY")
        assert schedule == {"start": "08:00", "end": "18:00"}


class TestIsBusinessHours:
    """Tests for is_business_hours() function."""

    def test_returns_true_within_business_hours(self, reset_config):
        """Test that True is returned during business hours."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": "America/Sao_Paulo",
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

        # Wednesday 10:00 AM Sao Paulo time
        check_time = datetime(2026, 1, 7, 10, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
        assert is_business_hours(check_time) is True

    def test_returns_false_outside_business_hours(self, reset_config):
        """Test that False is returned outside business hours."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": "America/Sao_Paulo",
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

        # Wednesday 8:00 PM Sao Paulo time (after 18:00)
        check_time = datetime(2026, 1, 7, 20, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
        assert is_business_hours(check_time) is False

    def test_returns_false_on_weekend(self, reset_config):
        """Test that False is returned on weekend (when closed)."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": "America/Sao_Paulo",
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

        # Saturday 10:00 AM Sao Paulo time
        check_time = datetime(2026, 1, 10, 10, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
        assert is_business_hours(check_time) is False

    def test_returns_true_at_start_time(self, reset_config):
        """Test that True is returned exactly at start time."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": "America/Sao_Paulo",
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

        # Wednesday 8:00 AM exactly
        check_time = datetime(2026, 1, 7, 8, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
        assert is_business_hours(check_time) is True

    def test_returns_true_at_end_time(self, reset_config):
        """Test that True is returned exactly at end time."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": "America/Sao_Paulo",
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

        # Wednesday 6:00 PM exactly
        check_time = datetime(2026, 1, 7, 18, 0, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
        assert is_business_hours(check_time) is True

    def test_returns_false_before_start_time(self, reset_config):
        """Test that False is returned before start time."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": "America/Sao_Paulo",
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

        # Wednesday 7:59 AM
        check_time = datetime(2026, 1, 7, 7, 59, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
        assert is_business_hours(check_time) is False

    def test_handles_naive_datetime(self, reset_config):
        """Test that naive datetime is handled correctly."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": "America/Sao_Paulo",
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

        # Naive datetime (no timezone) - should assume configured timezone
        check_time = datetime(2026, 1, 7, 10, 0, 0)  # Wednesday 10:00 AM
        assert is_business_hours(check_time) is True

    def test_converts_different_timezone(self, reset_config):
        """Test that different timezone is converted correctly."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": "America/Sao_Paulo",
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

        # UTC time that is 10:00 AM in Sao Paulo (UTC-3)
        # 10:00 Sao Paulo = 13:00 UTC
        check_time = datetime(2026, 1, 7, 13, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert is_business_hours(check_time) is True


class TestShouldAutoResume:
    """Tests for should_auto_resume() function."""

    def test_returns_false_during_business_hours(self, reset_config):
        """Test that auto-resume is not allowed during business hours."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": "America/Sao_Paulo",
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

        # Mock current time to be during business hours
        with patch("src.services.business_hours.is_business_hours", return_value=True):
            assert should_auto_resume() is False

    def test_returns_true_outside_business_hours(self, reset_config):
        """Test that auto-resume is allowed outside business hours."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": "America/Sao_Paulo",
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

        # Mock current time to be outside business hours
        with patch("src.services.business_hours.is_business_hours", return_value=False):
            assert should_auto_resume() is True


class TestGetCurrentScheduleStatus:
    """Tests for get_current_schedule_status function."""

    def test_returns_status_dict(self, reset_config):
        """Test that status dictionary is returned."""
        import src.services.business_hours as bh
        bh._config = {
            "timezone": "America/Sao_Paulo",
            "schedule": DEFAULT_SCHEDULE.copy(),
        }

        status = get_current_schedule_status()

        assert "timezone" in status
        assert "current_time" in status
        assert "day" in status
        assert "day_schedule" in status
        assert "is_business_hours" in status
        assert "should_auto_resume" in status


class TestReloadConfig:
    """Tests for reload_config function."""

    def test_clears_cache(self, reset_config):
        """Test that reload clears the config cache."""
        import src.services.business_hours as bh

        # Set initial config
        bh._config = {"timezone": "America/New_York", "schedule": {}}

        # Reload should clear and reload
        with patch("src.services.business_hours._get_config_path") as mock_path:
            mock_path.return_value = MagicMock(exists=lambda: False)
            reload_config()

        # Should now have default config
        assert bh._config["timezone"] == DEFAULT_TIMEZONE


class TestEnvOverrides:
    """Tests for environment variable overrides."""

    def test_timezone_override(self, reset_config):
        """Test that BUSINESS_HOURS_TIMEZONE overrides config."""
        import src.services.business_hours as bh

        with patch.object(
            bh.settings, "BUSINESS_HOURS_TIMEZONE", "America/New_York"
        ):
            with patch("src.services.business_hours._get_config_path") as mock_path:
                mock_path.return_value = MagicMock(exists=lambda: False)
                bh._config = None
                config = bh._load_config()

        assert config["timezone"] == "America/New_York"

    def test_time_override(self, reset_config):
        """Test that BUSINESS_HOURS_START/END override config."""
        import src.services.business_hours as bh

        with patch.object(bh.settings, "BUSINESS_HOURS_START", "09:00"):
            with patch.object(bh.settings, "BUSINESS_HOURS_END", "17:00"):
                with patch("src.services.business_hours._get_config_path") as mock_path:
                    mock_path.return_value = MagicMock(exists=lambda: False)
                    bh._config = None
                    config = bh._load_config()

        # Check that weekdays have overridden times
        assert config["schedule"]["monday"]["start"] == "09:00"
        assert config["schedule"]["monday"]["end"] == "17:00"
        assert config["schedule"]["friday"]["start"] == "09:00"
        assert config["schedule"]["friday"]["end"] == "17:00"


class TestDayNames:
    """Tests for DAY_NAMES constant."""

    def test_day_names_order(self):
        """Test that DAY_NAMES is in correct order (Monday=0)."""
        assert DAY_NAMES[0] == "monday"
        assert DAY_NAMES[6] == "sunday"
        assert len(DAY_NAMES) == 7
