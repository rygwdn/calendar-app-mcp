"""Tests for markdown renderers."""

import sys
import datetime
from unittest.mock import patch, MagicMock

import pytest
from jinja2 import Environment

from calendar_app.renderers.markdown import CalendarTemplateRenderer, format_as_markdown


class TestCalendarTemplateRenderer:
    """Tests for the CalendarTemplateRenderer class."""

    def test_init(self):
        """Test initialization of renderer."""
        # Prepare test data
        calendar_data = {"events": [], "reminders": []}
        
        # Create renderer
        renderer = CalendarTemplateRenderer(calendar_data)
        
        # Verify instance attributes
        assert renderer.calendar_data == calendar_data
        assert isinstance(renderer.env, Environment)
        assert "datetime" in renderer.env.globals
        assert "format_date" in renderer.env.globals
        assert "format_time_range" in renderer.env.globals
        assert "sort_events" in renderer.env.globals
        assert "sort_reminders" in renderer.env.globals
        assert renderer.template is not None

    def test_format_date(self):
        """Test date formatting."""
        renderer = CalendarTemplateRenderer({})
        
        # Test valid date
        assert renderer.format_date("2023-01-15 00:00:00 +0000") == "2023-01-15"
        
        # Test empty input
        assert renderer.format_date("") == ""
        assert renderer.format_date(None) == ""
        
        # Test fallback to original string
        assert renderer.format_date("not a valid date") == "not a valid date"

    def test_format_time_range(self):
        """Test time range formatting."""
        renderer = CalendarTemplateRenderer({})
        
        # Test valid time range
        assert renderer.format_time_range(
            "2023-01-15 09:30:00 +0000", 
            "2023-01-15 10:45:00 +0000"
        ) == "09:30 - 10:45"
        
        # Test start time only
        assert renderer.format_time_range(
            "2023-01-15 14:00:00 +0000", 
            None
        ) == "14:00"
        
        # Test empty values
        assert renderer.format_time_range("", "") == ""
        assert renderer.format_time_range(None, None) == ""
        
        # Test fallback to original strings
        assert renderer.format_time_range(
            "invalid start", 
            "invalid end"
        ) == "invalid start - invalid end"

    def test_sort_events(self):
        """Test event sorting by start time."""
        renderer = CalendarTemplateRenderer({})
        
        # Create test events
        events = [
            {"title": "Event C", "start_time": "2023-01-15 14:00:00"},
            {"title": "Event A", "start_time": "2023-01-15 09:00:00"},
            {"title": "Event B", "start_time": "2023-01-15 12:30:00"},
            {"title": "Event D", "start_time": None},
        ]
        
        sorted_events = renderer.sort_events(events)
        
        # Verify order (events without start_time should be first since they sort as '')
        assert sorted_events[0]["title"] == "Event D"
        assert sorted_events[1]["title"] == "Event A"
        assert sorted_events[2]["title"] == "Event B"
        assert sorted_events[3]["title"] == "Event C"

    def test_sort_reminders(self):
        """Test reminder sorting by completion status and due date."""
        renderer = CalendarTemplateRenderer({})
        
        # Create test reminders
        reminders = [
            {"title": "Task C", "completed": True, "due_date": "2023-01-20"},
            {"title": "Task A", "completed": False, "due_date": "2023-01-15"},
            {"title": "Task B", "completed": False, "due_date": "2023-01-25"},
            {"title": "Task D", "completed": True, "due_date": "2023-01-10"},
        ]
        
        sorted_reminders = renderer.sort_reminders(reminders)
        
        # Verify order (incomplete first, then by due date)
        assert sorted_reminders[0]["title"] == "Task A"
        assert sorted_reminders[1]["title"] == "Task B"
        assert sorted_reminders[2]["title"] == "Task D"
        assert sorted_reminders[3]["title"] == "Task C"

    def test_generate_with_valid_data(self):
        """Test generating markdown with valid calendar data."""
        # Prepare test data
        calendar_data = {
            "events": [
                {
                    "title": "Team Meeting",
                    "start_time": "2023-01-15 10:00:00",
                    "end_time": "2023-01-15 11:00:00",
                    "location": "Conference Room",
                    "calendar": "Work"
                }
            ],
            "reminders": [
                {
                    "title": "Buy groceries",
                    "due_date": "2023-01-15 18:00:00",
                    "completed": False,
                    "calendar": "Personal"
                }
            ]
        }
        
        # Create renderer
        renderer = CalendarTemplateRenderer(calendar_data)
        
        # Generate markdown
        markdown = renderer.generate()
        
        # Verify content
        assert "### Events" in markdown
        assert "Team Meeting" in markdown
        assert "Conference Room" in markdown
        assert "Work" in markdown
        
        assert "### Reminders" in markdown
        assert "Buy groceries" in markdown
        assert "[ ]" in markdown  # Incomplete task
        assert "Personal" in markdown

    def test_generate_with_empty_data(self):
        """Test generating markdown with empty calendar data."""
        # Prepare test data
        calendar_data = {
            "events": [],
            "reminders": []
        }
        
        # Create renderer
        renderer = CalendarTemplateRenderer(calendar_data)
        
        # Generate markdown
        markdown = renderer.generate()
        
        # Verify content
        assert "No events or reminders found for the specified criteria" in markdown

    @patch("calendar_app.renderers.markdown.print")
    def test_generate_with_error(self, mock_print):
        """Test handling errors during template rendering."""
        # Create a mock template that raises an exception
        renderer = CalendarTemplateRenderer({})
        
        # Make the template.render method raise an exception
        def mock_render(**kwargs):
            raise ValueError("Test error")
        
        renderer.template.render = mock_render
        
        # Generate markdown (should catch the exception)
        markdown = renderer.generate()
        
        # Verify error message in output
        assert "Error rendering calendar data" in markdown
        assert "Test error" in markdown
        
        # Verify error was logged
        mock_print.assert_called_once()
        assert "Error rendering template" in mock_print.call_args[0][0]
        assert mock_print.call_args[1]["file"] == sys.stderr


def test_format_as_markdown():
    """Test the format_as_markdown function."""
    # Create a mock renderer
    mock_renderer = MagicMock()
    mock_renderer.generate.return_value = "Rendered markdown"
    
    # Patch the CalendarTemplateRenderer to return our mock
    with patch("calendar_app.renderers.markdown.CalendarTemplateRenderer", return_value=mock_renderer):
        result = format_as_markdown({"events": []})
        
        # Verify result
        assert result == "Rendered markdown"
        
        # Verify renderer was created with correct data
        mock_renderer.generate.assert_called_once()