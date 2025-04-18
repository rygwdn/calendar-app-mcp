"""Tests for time-related MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

from calendar_app.utils.date_utils import (
    get_current_datetime,
    convert_timezone,
    list_common_timezones,
)


class TestMcpTimeTools:
    """Tests for MCP time-related functions."""

    def test_get_current_datetime(self):
        """Test that get_current_datetime returns the expected structure."""
        result = get_current_datetime()
        
        # Check that the result is well structured
        assert isinstance(result, dict)
        assert "date" in result
        assert "time" in result
        assert "timezone" in result
        assert "iso_datetime" in result
        assert "unix_timestamp" in result
        
        # Verify timezone data
        assert "name" in result["timezone"]
        assert "utc_offset" in result["timezone"]
        assert "utc_offset_hours" in result["timezone"]
        
        # Make sure values are of the right type
        assert isinstance(result["date"]["year"], int)
        assert isinstance(result["date"]["month"], int)
        assert isinstance(result["date"]["day"], int)
        assert isinstance(result["date"]["weekday"], str)
        assert isinstance(result["date"]["iso_date"], str)
        assert isinstance(result["time"]["hour"], int)
        assert isinstance(result["time"]["minute"], int)
        assert isinstance(result["time"]["second"], int)
        assert isinstance(result["time"]["iso_time"], str)
        assert isinstance(result["iso_datetime"], str)
        assert isinstance(result["unix_timestamp"], int)
    
    def test_convert_timezone(self):
        """Test basic timezone conversion."""
        # Use fixed date and well-known timezones for a reliable test
        dt_str = "2023-01-01 12:00:00"
        from_tz = "UTC"
        to_tz = "UTC"  # Same timezone for simplicity
        
        result = convert_timezone(dt_str, from_tz, to_tz)
        
        # Check result structure
        assert isinstance(result, dict)
        assert "original" in result
        assert "converted" in result
        assert "offset_hours" in result
        
        # Verify original data
        assert result["original"]["datetime"] == dt_str
        assert result["original"]["timezone"] == from_tz
        assert "iso_datetime" in result["original"]
        
        # Verify converted data
        assert "datetime" in result["converted"]
        assert result["converted"]["timezone"] == to_tz
        assert "iso_datetime" in result["converted"]
        assert "date" in result["converted"]
        assert "time" in result["converted"]
        
        # Verify data types
        assert isinstance(result["offset_hours"], float)
        
    def test_list_common_timezones(self):
        """Test that list_common_timezones returns timezones grouped by region."""
        result = list_common_timezones()
        
        # Verify structure
        assert isinstance(result, dict)
        assert "regions" in result
        assert "timezones_by_region" in result
        assert "total_count" in result
        
        # Verify that we have regions
        assert len(result["regions"]) > 0
        assert len(result["timezones_by_region"]) > 0
        assert result["total_count"] > 0
        
        # Check data for a region
        first_region = result["regions"][0]
        region_data = result["timezones_by_region"][first_region]
        assert len(region_data) > 0
        
        # Check timezone data
        first_tz = region_data[0]
        assert "name" in first_tz
        assert "utc_offset" in first_tz
        assert "utc_offset_hours" in first_tz
        assert "current_time" in first_tz