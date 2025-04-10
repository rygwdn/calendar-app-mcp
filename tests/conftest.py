"""Pytest configuration file."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_nsdate():
    """Mock NSDate for testing."""
    with patch("calendar_app.utils.date_utils.NSDate") as mock:
        mock_date = MagicMock()
        mock.dateWithTimeIntervalSince1970_.return_value = mock_date
        yield mock


@pytest.fixture
def mock_event():
    """Create a mock event for testing."""
    event = MagicMock()
    event.title.return_value = "Test Event"
    event.location.return_value = "Test Location"
    event.notes.return_value = "Test Notes"
    event.startDate.return_value.description.return_value = "2023-01-15 10:00:00"
    event.endDate.return_value.description.return_value = "2023-01-15 11:00:00"
    event.isAllDay.return_value = False
    event.calendar().title.return_value = "Test Calendar"
    event.URL.return_value = None
    event.availability.return_value = 1  # EKCalendarEventAvailabilityBusy
    event.hasAttendees.return_value = False
    event.organizer.return_value = None
    return event


@pytest.fixture
def mock_reminder():
    """Create a mock reminder for testing."""
    reminder = MagicMock()
    reminder.title.return_value = "Test Reminder"
    reminder.notes.return_value = "Test Notes"
    reminder.dueDateComponents().date().description.return_value = "2023-01-15 18:00:00"
    reminder.priority.return_value = 1
    reminder.isCompleted.return_value = False
    reminder.calendar().title.return_value = "Test Calendar"
    return reminder


@pytest.fixture
def mock_event_store():
    """Create a mock event store for testing."""
    with patch("calendar_app.models.event_store.CalendarEventStore") as mock_cls:
        mock_store = MagicMock()
        mock_cls.return_value = mock_store

        # Configure default behaviors
        mock_store.event_authorized = True
        mock_store.reminder_authorized = True

        # Sample data for calendars
        mock_store.get_calendars.return_value = {
            "event_calendars": [
                {"title": "Work", "color": "#FF0000", "type": "Event"},
                {"title": "Personal", "color": "#00FF00", "type": "Event"},
            ],
            "reminder_calendars": [{"title": "Tasks", "color": "#0000FF", "type": "Reminder"}],
        }

        # Sample data for events and reminders
        mock_store.get_events_and_reminders.return_value = {
            "events": [
                {
                    "title": "Team Meeting",
                    "location": "Conference Room",
                    "start_time": "2023-01-15 10:00:00",
                    "end_time": "2023-01-15 11:00:00",
                    "all_day": False,
                    "calendar": "Work",
                }
            ],
            "reminders": [
                {
                    "title": "Buy groceries",
                    "due_date": "2023-01-15 18:00:00",
                    "completed": False,
                    "calendar": "Personal",
                }
            ],
        }

        yield mock_store
