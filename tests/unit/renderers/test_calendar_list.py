"""Tests for calendar list renderer."""

import sys
from unittest.mock import patch

import pytest

from calendar_app.renderers.calendar_list import CalendarListTemplateRenderer


class TestCalendarListTemplateRenderer:
    """Tests for the CalendarListTemplateRenderer class."""

    def test_init(self):
        """Test initialization of renderer."""
        # Prepare test data
        calendars_data = {"event_calendars": [], "reminder_calendars": []}

        # Create renderer
        renderer = CalendarListTemplateRenderer(calendars_data)

        # Verify instance attributes
        assert renderer.calendars_data == calendars_data
        assert renderer.template is not None

        # Verify that sort_calendars is in the environment globals
        assert "sort_calendars" in renderer.env.globals

    def test_generate_with_valid_data(self):
        """Test generating markdown with valid calendar data."""
        # Prepare test data
        calendars_data = {
            "event_calendars": [
                {"title": "Work", "color": "#FF0000", "type": "Event"},
                {"title": "Personal", "color": "#00FF00", "type": "Event"},
            ],
            "reminder_calendars": [{"title": "Tasks", "color": "#0000FF", "type": "Reminder"}],
        }

        # Create renderer
        renderer = CalendarListTemplateRenderer(calendars_data)

        # Generate markdown
        markdown = renderer.generate()

        # Verify content (calendars should be sorted by title)
        assert "### Event Calendars" in markdown
        assert "- Personal (#00FF00)" in markdown
        assert "- Work (#FF0000)" in markdown

        assert "### Reminder Calendars" in markdown
        assert "- Tasks (#0000FF)" in markdown

    def test_generate_with_empty_data(self):
        """Test generating markdown with empty calendar data."""
        # Prepare test data
        calendars_data = {"event_calendars": [], "reminder_calendars": []}

        # Create renderer
        renderer = CalendarListTemplateRenderer(calendars_data)

        # Generate markdown
        markdown = renderer.generate()

        # Verify content
        assert "No calendars found or access denied" in markdown

    def test_generate_with_errors(self):
        """Test generating markdown with error messages."""
        # Prepare test data with errors
        calendars_data = {
            "events_error": "Calendar access not authorized",
            "reminders_error": "Reminders access not authorized",
        }

        # Create renderer
        renderer = CalendarListTemplateRenderer(calendars_data)

        # Generate markdown
        markdown = renderer.generate()

        # Verify content
        assert "### Event Calendars" in markdown
        assert "Error: Calendar access not authorized" in markdown

        assert "### Reminder Calendars" in markdown
        assert "Error: Reminders access not authorized" in markdown

    @patch("calendar_app.renderers.calendar_list.print")
    def test_generate_with_render_error(self, mock_print):
        """Test handling errors during template rendering."""
        # Create a mock template that raises an exception
        renderer = CalendarListTemplateRenderer({})

        # Make the template.render method raise an exception
        def mock_render(**kwargs):
            raise ValueError("Test error")

        renderer.template.render = mock_render

        # Generate markdown (should catch the exception)
        markdown = renderer.generate()

        # Verify error message in output
        assert "Error rendering calendar list" in markdown
        assert "Test error" in markdown

        # Verify error was logged
        mock_print.assert_called_once()
        assert "Error rendering template" in mock_print.call_args[0][0]
        assert mock_print.call_args[1]["file"] == sys.stderr
