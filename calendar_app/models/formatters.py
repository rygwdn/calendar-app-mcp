"""Formatters for converting EventKit objects to dictionaries."""

import re
import sys

from EventKit import EKCalendarEventAvailabilityBusy


def get_human_readable_status(status_code):
    """Convert EKParticipantStatus constants to human-readable strings."""
    # Based on Apple's documentation for EKParticipantStatus
    status_map = {
        0: "unknown",  # EKParticipantStatusUnknown
        1: "pending",  # EKParticipantStatusPending
        2: "accepted",  # EKParticipantStatusAccepted
        3: "declined",  # EKParticipantStatusDeclined
        4: "tentative",  # EKParticipantStatusTentative
        5: "delegated",  # EKParticipantStatusDelegated
        6: "completed",  # EKParticipantStatusCompleted
        7: "in-process",  # EKParticipantStatusInProcess
    }
    # Convert to int in case we get an NSNumber or other object type
    try:
        int_code = int(status_code)
        return status_map.get(int_code, "unknown")
    except (ValueError, TypeError):
        return "unknown"


def format_event(event):
    """Format an EKEvent as a dictionary."""
    # Format participants if available
    participants = []
    if event.hasAttendees():
        for attendee in event.attendees():
            participant = {
                "name": attendee.name() if attendee.name() else "Unknown",
                "email": attendee.emailAddress() if attendee.emailAddress() else None,
                "status": get_human_readable_status(attendee.participantStatus()),
                "type": {
                    0: "unknown",  # EKParticipantTypeUnknown
                    1: "person",  # EKParticipantTypePerson
                    2: "room",  # EKParticipantTypeRoom
                    3: "resource",  # EKParticipantTypeResource
                    4: "group",  # EKParticipantTypeGroup
                }.get(
                    (
                        int(attendee.participantType())
                        if attendee.participantType() is not None
                        else 0
                    ),
                    "unknown",
                ),
                "role": {
                    0: "unknown",  # EKParticipantRoleUnknown
                    1: "required",  # EKParticipantRoleRequired
                    2: "optional",  # EKParticipantRoleOptional
                    3: "chair",  # EKParticipantRoleChair
                    4: "non-participant",  # EKParticipantRoleNonParticipant
                }.get(
                    (
                        int(attendee.participantRole())
                        if attendee.participantRole() is not None
                        else 0
                    ),
                    "unknown",
                ),
                "is_organizer": (
                    bool(event.organizer() and attendee.isEqual_(event.organizer()))
                ),
            }
            participants.append(participant)

    # Check for conference URL in notes or URL
    conference_url = None
    notes = event.notes()
    url_obj = event.URL()

    # Safe string conversion for URL
    url_str = None
    if url_obj is not None:
        try:
            # Handle string URLs
            if isinstance(url_obj, str):
                url_str = url_obj
            # Handle NSURLs and other URL objects
            elif hasattr(url_obj, "absoluteString"):
                url_str = url_obj.absoluteString()
            # Handle tuples or lists
            elif isinstance(url_obj, tuple | list) and len(url_obj) > 0:
                # Try to get the first element if it's a tuple/list
                first_element = url_obj[0]
                if hasattr(first_element, "absoluteString"):
                    url_str = first_element.absoluteString()
                else:
                    url_str = str(first_element)
            # Fallback
            else:
                url_str = str(url_obj)
        except Exception as e:
            print(f"Error converting URL: {e}", file=sys.stderr)
            url_str = None

    # First check if the main URL is a conference URL
    if url_str and any(
        domain in url_str.lower()
        for domain in ["zoom.us", "meet.google", "teams.microsoft", "webex", "bluejeans"]
    ):
        conference_url = url_str
    # Then check notes for URLs if no conference URL found
    elif notes:
        # Look for common video conferencing URLs in notes
        zoom_pattern = r'https?://[a-zA-Z0-9.-]+\.zoom\.us/[^\s<>"]+'
        meet_pattern = r'https?://meet\.google\.com/[^\s<>"]+'
        teams_pattern = r'https?://teams\.microsoft\.com/[^\s<>"]+'
        webex_pattern = r'https?://[a-zA-Z0-9.-]+\.webex\.com/[^\s<>"]+'

        # Check for each pattern
        for pattern in [zoom_pattern, meet_pattern, teams_pattern, webex_pattern]:
            match = re.search(pattern, notes)
            if match:
                conference_url = match.group(0)
                break

    # Get the location, or use conference URL if location is empty
    location = event.location()
    if not location and conference_url:
        location = conference_url

    return {
        "title": event.title(),
        "location": location,
        "notes": event.notes() if event.notes() else None,
        "start_time": event.startDate().description() if event.startDate() else None,
        "end_time": event.endDate().description() if event.endDate() else None,
        "all_day": event.isAllDay(),
        "calendar": event.calendar().title(),
        "url": url_str,
        "availability": (
            "busy" if event.availability() == EKCalendarEventAvailabilityBusy else "free"
        ),
        "conference_url": conference_url,
        "participants": participants,
        "has_organizer": event.organizer() is not None,
        "organizer": (
            {
                "name": (
                    event.organizer().name()
                    if event.organizer() and event.organizer().name()
                    else None
                ),
                "email": (
                    event.organizer().emailAddress()
                    if event.organizer() and event.organizer().emailAddress()
                    else None
                ),
            }
            if event.organizer()
            else None
        ),
    }


def format_reminder(reminder):
    """Format an EKReminder as a dictionary."""
    return {
        "title": reminder.title(),
        "notes": reminder.notes() if reminder.notes() else None,
        "due_date": (
            reminder.dueDateComponents().date().description()
            if reminder.dueDateComponents()
            else None
        ),
        "priority": reminder.priority(),
        "completed": reminder.isCompleted(),
        "calendar": reminder.calendar().title(),
    }


def get_json_schema():
    """Return the JSON schema for the output."""
    return {
        "type": "object",
        "properties": {
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "location": {"type": ["string", "null"]},
                        "notes": {"type": ["string", "null"]},
                        "start_time": {"type": ["string", "null"]},
                        "end_time": {"type": ["string", "null"]},
                        "all_day": {"type": "boolean"},
                        "calendar": {"type": "string"},
                        "url": {"type": ["string", "null"]},
                        "availability": {"type": "string", "enum": ["busy", "free"]},
                        "conference_url": {"type": ["string", "null"]},
                        "participants": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": ["string", "null"]},
                                    "status": {"type": "string"},
                                    "type": {"type": "string"},
                                    "role": {"type": "string"},
                                    "is_organizer": {"type": "boolean"},
                                },
                                "required": ["name", "status", "type", "role", "is_organizer"],
                            },
                        },
                        "has_organizer": {"type": "boolean"},
                        "organizer": {
                            "type": "object",
                            "properties": {
                                "name": {"type": ["string", "null"]},
                                "email": {"type": ["string", "null"]},
                            },
                        },
                    },
                    "required": ["title", "all_day", "calendar"],
                },
            },
            "reminders": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "notes": {"type": ["string", "null"]},
                        "due_date": {"type": ["string", "null"]},
                        "priority": {"type": "integer"},
                        "completed": {"type": "boolean"},
                        "calendar": {"type": "string"},
                    },
                    "required": ["title", "completed", "calendar"],
                },
            },
            "events_error": {"type": "string"},
            "reminders_error": {"type": "string"},
        },
    }
