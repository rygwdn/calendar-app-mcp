"""Tests for date_utils module."""

import datetime
import pytest
from unittest.mock import patch, MagicMock
from argparse import ArgumentTypeError

from calendar_app.utils.date_utils import parse_date, get_date_range


class TestParseDate:
    """Tests for parse_date function."""

    def test_valid_date(self):
        """Test parsing a valid date string."""
        result = parse_date("2023-01-15")
        assert isinstance(result, datetime.datetime)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_invalid_date_format(self):
        """Test parsing an invalid date format raises error."""
        with pytest.raises(ArgumentTypeError) as exc_info:
            parse_date("15/01/2023")
        assert "Invalid date format" in str(exc_info.value)

    def test_invalid_date_value(self):
        """Test parsing an invalid date value raises error."""
        with pytest.raises(ArgumentTypeError) as exc_info:
            parse_date("2023-13-45")
        assert "Invalid date format" in str(exc_info.value)


class TestGetDateRange:
    """Tests for get_date_range function."""

    @patch("calendar_app.utils.date_utils.NSDate")
    def test_specific_date_range(self, mock_nsdate):
        """Test get_date_range with specific from and to dates."""
        # Setup mock
        mock_start_date = "mocked_start_date"
        mock_end_date = "mocked_end_date"
        mock_nsdate.dateWithTimeIntervalSince1970_.side_effect = [mock_start_date, mock_end_date]

        # Call function
        from_date = datetime.datetime(2023, 1, 15)
        to_date = datetime.datetime(2023, 1, 20)
        start_date, end_date = get_date_range(from_date, to_date)

        # Verify
        assert start_date == mock_start_date
        assert end_date == mock_end_date

        # Check timestamps passed to NSDate
        call_args = mock_nsdate.dateWithTimeIntervalSince1970_.call_args_list
        assert len(call_args) == 2

    @patch("calendar_app.utils.date_utils.NSDate")
    @patch("calendar_app.utils.date_utils.datetime")
    def test_default_date_range(self, mock_datetime_module, mock_nsdate):
        """Test get_date_range with default parameters (today)."""
        # Setup mocks for datetime module
        now = datetime.datetime(2023, 1, 15, 12, 30, 45)
        mock_datetime_module.datetime.now.return_value = now

        # Create real datetime objects (not mocked) for the function to use
        start_datetime = datetime.datetime(2023, 1, 15, 0, 0, 0)
        end_datetime = datetime.datetime(2023, 1, 15, 23, 59, 59)

        # Make the datetime constructor return our predefined objects
        def mock_datetime_init(year, month, day, hour=0, minute=0, second=0):
            if hour == 0 and minute == 0 and second == 0:
                return start_datetime
            else:
                return end_datetime

        # Apply the mock implementation
        mock_datetime_module.datetime.side_effect = mock_datetime_init

        # Mock NSDate
        mock_start_date = "mocked_start_date"
        mock_end_date = "mocked_end_date"
        mock_nsdate.dateWithTimeIntervalSince1970_.side_effect = [mock_start_date, mock_end_date]

        # Call function with defaults
        start_date, end_date = get_date_range(None, None)

        # Verify
        assert start_date == mock_start_date
        assert end_date == mock_end_date
