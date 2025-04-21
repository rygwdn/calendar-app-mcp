"""Tests for timezone utilities in date_utils module."""

import datetime
from unittest.mock import patch, MagicMock

import pytest
import pytz

from calendar_app.utils.date_utils import (
    get_current_datetime,
    convert_timezone,
    list_common_timezones,
)


class TestGetCurrentDatetime:
    """Tests for get_current_datetime function."""

    def test_get_current_datetime_basic(self):
        """Test that get_current_datetime returns the expected structure."""
        result = get_current_datetime()

        # Check the structure of the result
        assert "date" in result
        assert "year" in result["date"]
        assert "month" in result["date"]
        assert "day" in result["date"]
        assert "weekday" in result["date"]
        assert "iso_date" in result["date"]

        assert "time" in result
        assert "hour" in result["time"]
        assert "minute" in result["time"]
        assert "second" in result["time"]
        assert "iso_time" in result["time"]

        assert "timezone" in result
        assert "name" in result["timezone"]
        assert "utc_offset" in result["timezone"]
        assert "utc_offset_hours" in result["timezone"]

        assert "iso_datetime" in result
        assert "unix_timestamp" in result

    def test_get_current_datetime_with_timezone(self):
        """Test get_current_datetime with a specific timezone."""
        # Use a well-known timezone
        timezone = "UTC"
        result = get_current_datetime(timezone)

        # Check that the timezone info is correct
        assert "timezone" in result
        assert result["timezone"]["name"] == timezone

        # UTC offset should be +0000 for UTC
        assert result["timezone"]["utc_offset"] == "+0000"
        assert result["timezone"]["utc_offset_hours"] == 0.0

    def test_get_current_datetime_invalid_timezone(self):
        """Test get_current_datetime with an invalid timezone."""
        result = get_current_datetime("Invalid/Timezone")

        # Should return an error result
        assert "error" in result
        assert "Invalid timezone" in result["error"]
        assert "valid_format" in result


class TestConvertTimezone:
    """Tests for convert_timezone function."""

    def test_convert_timezone_basic(self):
        """Test basic timezone conversion."""
        # Use fixed date and well-known timezones for a reliable test
        dt_str = "2023-01-01 12:00:00"
        from_tz = "UTC"
        to_tz = "UTC"  # Same timezone for simplicity

        result = convert_timezone(dt_str, from_tz, to_tz)

        # Check result structure
        assert "original" in result
        assert "converted" in result
        assert "offset_hours" in result

        # Original data
        assert result["original"]["datetime"] == dt_str
        assert result["original"]["timezone"] == from_tz

        # Converted data - should be the same as original for UTC to UTC
        assert result["converted"]["datetime"] == dt_str
        assert result["converted"]["timezone"] == to_tz
        assert result["converted"]["date"] == "2023-01-01"
        assert result["converted"]["time"] == "12:00:00"

        # Offset should be 0 for same timezone
        assert result["offset_hours"] == 0.0

    def test_convert_timezone_different_zones(self):
        """Test conversion between different timezones."""
        dt_str = "2023-01-01 12:00:00"
        from_tz = "UTC"
        to_tz = "America/New_York"  # UTC-5 in January (standard time)

        result = convert_timezone(dt_str, from_tz, to_tz)

        # Basic structure checks
        assert "converted" in result
        assert "datetime" in result["converted"]

        # Specific behavior depends on exact library implementation and timezone rules,
        # but we can check that the timezone names are correct
        assert result["original"]["timezone"] == from_tz
        assert result["converted"]["timezone"] == to_tz

        # For UTC to NY in January, offset should typically be -5 hours
        # (though this can vary with DST, legislation changes, etc.)
        expected_hour = 7  # 12:00 UTC -> 07:00 EST
        assert result["converted"]["datetime"].startswith("2023-01-01 07:00:00") or (
            "offset_hours" in result and abs(result["offset_hours"] + 5) < 0.1
        )

    def test_convert_timezone_custom_format(self):
        """Test timezone conversion with a custom datetime format."""
        # Use a different format
        dt_str = "01/01/2023 12:00"
        dt_format = "%d/%m/%Y %H:%M"
        from_tz = "UTC"
        to_tz = "UTC"

        result = convert_timezone(dt_str, from_tz, to_tz, dt_format)

        # Check that the format was properly interpreted
        assert result["original"]["datetime"] == dt_str
        # Return format will be the same as input format
        assert result["converted"]["datetime"] == dt_str

    def test_convert_timezone_invalid_format(self):
        """Test conversion with invalid datetime format."""
        dt_str = "not-a-date"
        from_tz = "UTC"
        to_tz = "UTC"

        result = convert_timezone(dt_str, from_tz, to_tz)

        # Should return an error
        assert "error" in result
        assert "Invalid datetime format" in result["error"]
        assert "valid_format" in result

    def test_convert_timezone_invalid_source_timezone(self):
        """Test conversion with invalid source timezone."""
        dt_str = "2023-01-01 12:00:00"
        from_tz = "Invalid/Timezone"
        to_tz = "UTC"

        result = convert_timezone(dt_str, from_tz, to_tz)

        # Should return an error
        assert "error" in result
        assert "Invalid source timezone" in result["error"]
        assert "valid_format" in result

    def test_convert_timezone_invalid_target_timezone(self):
        """Test conversion with invalid target timezone."""
        dt_str = "2023-01-01 12:00:00"
        from_tz = "UTC"
        to_tz = "Invalid/Timezone"

        result = convert_timezone(dt_str, from_tz, to_tz)

        # Should return an error
        assert "error" in result
        assert "Invalid target timezone" in result["error"]
        assert "valid_format" in result


class TestListCommonTimezones:
    """Tests for list_common_timezones function."""

    def test_list_common_timezones_structure(self):
        """Test that list_common_timezones returns the expected structure."""
        result = list_common_timezones()

        # Check basic structure
        assert "regions" in result
        assert "timezones_by_region" in result
        assert "total_count" in result

        # There should be some regions
        assert len(result["regions"]) > 0
        assert len(result["timezones_by_region"]) > 0
        assert result["total_count"] > 0

        # Check that each region has timezone entries
        for region in result["regions"]:
            assert region in result["timezones_by_region"]
            assert len(result["timezones_by_region"][region]) > 0

            # Check structure of a timezone entry
            tz_info = result["timezones_by_region"][region][0]
            assert "name" in tz_info
            assert "utc_offset" in tz_info
            assert "utc_offset_hours" in tz_info
            assert "current_time" in tz_info

    def test_list_common_timezones_major_regions(self):
        """Test that list_common_timezones includes major regions."""
        result = list_common_timezones()

        # Major timezone regions that should be present
        major_regions = ["America", "Europe", "Asia", "Africa", "Pacific"]
        for region in major_regions:
            assert region in result["regions"], f"Expected region '{region}' not found"
