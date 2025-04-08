#!/opt/homebrew/bin/uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyobjc-framework-EventKit",
#     "fastmcp",
#     "jinja2>=3.1.2",
# ]
# ///

import datetime
import json
import sys
import time
import argparse
import re # Added import for regex in markdown formatting
from Foundation import NSDate, NSRunLoop, NSDefaultRunLoopMode
from EventKit import EKEventStore, EKEntityTypeEvent, EKEntityTypeReminder, EKCalendarEventAvailabilityBusy

# Import FastMCP for MCP server functionality
from mcp.server.fastmcp import FastMCP
# Import Jinja2 for template rendering
from jinja2 import Environment, BaseLoader, StrictUndefined

def parse_date(date_str):
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD.")

def get_date_range(from_date, to_date):
    """Get the start and end dates for the specified range."""
    # If no dates provided, use today
    if not from_date:
        from_date = datetime.datetime.now()
        from_date = datetime.datetime(from_date.year, from_date.month, from_date.day, 0, 0, 0)
    else:
        from_date = datetime.datetime(from_date.year, from_date.month, from_date.day, 0, 0, 0)

    if not to_date:
        to_date = from_date
        to_date = datetime.datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59)
    else:
        to_date = datetime.datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59)

    # Convert to NSDate
    start_date = NSDate.dateWithTimeIntervalSince1970_(from_date.timestamp())
    end_date = NSDate.dateWithTimeIntervalSince1970_(to_date.timestamp())

    return start_date, end_date

def format_event(event):
    """Format an EKEvent as a dictionary."""

    # Function to convert participant status codes to human-readable format
    def get_human_readable_status(status_code):
        """Convert EKParticipantStatus constants to human-readable strings."""
        # Based on Apple's documentation for EKParticipantStatus
        status_map = {
            0: "unknown",         # EKParticipantStatusUnknown
            1: "pending",         # EKParticipantStatusPending
            2: "accepted",        # EKParticipantStatusAccepted
            3: "declined",        # EKParticipantStatusDeclined
            4: "tentative",       # EKParticipantStatusTentative
            5: "delegated",       # EKParticipantStatusDelegated
            6: "completed",       # EKParticipantStatusCompleted
            7: "in-process"       # EKParticipantStatusInProcess
        }
        # Convert to int in case we get an NSNumber or other object type
        try:
            int_code = int(status_code)
            return status_map.get(int_code, "unknown")
        except (ValueError, TypeError):
            return "unknown"

    # Format participants if available
    participants = []
    if event.hasAttendees():
        for attendee in event.attendees():
            participant = {
                "name": attendee.name() if attendee.name() else "Unknown",
                "email": attendee.emailAddress() if attendee.emailAddress() else None,
                "status": get_human_readable_status(attendee.participantStatus()),
                "type": {
                    0: "unknown",   # EKParticipantTypeUnknown
                    1: "person",    # EKParticipantTypePerson
                    2: "room",      # EKParticipantTypeRoom
                    3: "resource",  # EKParticipantTypeResource
                    4: "group"      # EKParticipantTypeGroup
                }.get(int(attendee.participantType()) if attendee.participantType() is not None else 0, "unknown"),
                "role": {
                    0: "unknown",         # EKParticipantRoleUnknown
                    1: "required",        # EKParticipantRoleRequired
                    2: "optional",        # EKParticipantRoleOptional
                    3: "chair",           # EKParticipantRoleChair
                    4: "non-participant"  # EKParticipantRoleNonParticipant
                }.get(int(attendee.participantRole()) if attendee.participantRole() is not None else 0, "unknown"),
                "is_organizer": True if event.organizer() and attendee.isEqual_(event.organizer()) else False
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
            elif hasattr(url_obj, 'absoluteString'):
                url_str = url_obj.absoluteString()
            # Handle tuples or lists
            elif isinstance(url_obj, (tuple, list)) and len(url_obj) > 0:
                # Try to get the first element if it's a tuple/list
                first_element = url_obj[0]
                if hasattr(first_element, 'absoluteString'):
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
    if url_str and any(domain in url_str.lower() for domain in ["zoom.us", "meet.google", "teams.microsoft", "webex", "bluejeans"]):
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
        "availability": "busy" if event.availability() == EKCalendarEventAvailabilityBusy else "free",
        "conference_url": conference_url,
        "participants": participants,
        "has_organizer": event.organizer() is not None,
        "organizer": {
            "name": event.organizer().name() if event.organizer() and event.organizer().name() else None,
            "email": event.organizer().emailAddress() if event.organizer() and event.organizer().emailAddress() else None
        } if event.organizer() else None
    }

def format_reminder(reminder):
    """Format an EKReminder as a dictionary."""
    return {
        "title": reminder.title(),
        "notes": reminder.notes() if reminder.notes() else None,
        "due_date": reminder.dueDateComponents().date().description() if reminder.dueDateComponents() else None,
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
                                    "is_organizer": {"type": "boolean"}
                                },
                                "required": ["name", "status", "type", "role", "is_organizer"]
                            }
                        },
                        "has_organizer": {"type": "boolean"},
                        "organizer": {
                            "type": "object",
                            "properties": {
                                "name": {"type": ["string", "null"]},
                                "email": {"type": ["string", "null"]}
                            }
                        }
                    },
                    "required": ["title", "all_day", "calendar"]
                }
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
                        "calendar": {"type": "string"}
                    },
                    "required": ["title", "completed", "calendar"]
                }
            },
            "events_error": {"type": "string"},
            "reminders_error": {"type": "string"}
        }
    }

def filter_by_calendars(items, calendar_names):
    """Filter items by calendar names."""
    if not calendar_names:
        return items

    return [item for item in items if item.calendar().title() in calendar_names]

class CalendarEventStore:
    """Class to handle calendar event store operations."""

    def __init__(self):
        # Create event store
        self.event_store = EKEventStore.alloc().init()
        self.event_authorized = False
        self.reminder_authorized = False
        self.request_authorization()

    def request_authorization(self):
        """Request access to calendars and reminders."""
        # Authorization result holders
        event_result = {"authorized": False, "complete": False}
        reminder_result = {"authorized": False, "complete": False}

        print("Requesting access to your calendars and reminders...", file=sys.stderr)

        # Define callbacks
        def event_callback(granted, error):
            event_result["authorized"] = granted
            event_result["complete"] = True
            if error:
                print(f"Event authorization error: {error}", file=sys.stderr)

        def reminder_callback(granted, error):
            reminder_result["authorized"] = granted
            reminder_result["complete"] = True
            if error:
                print(f"Reminder authorization error: {error}", file=sys.stderr)

        # Request access to calendars
        self.event_store.requestAccessToEntityType_completion_(EKEntityTypeEvent, event_callback)
        # Request access to reminders
        self.event_store.requestAccessToEntityType_completion_(EKEntityTypeReminder, reminder_callback)

        # Wait for authorization callbacks to complete
        timeout = 10  # seconds
        start_time = time.time()

        print("Waiting for authorization responses...", file=sys.stderr)
        while not (event_result["complete"] and reminder_result["complete"]):
            # Run the run loop for a short time to process callbacks
            NSRunLoop.currentRunLoop().runMode_beforeDate_(
                NSDefaultRunLoopMode,
                NSDate.dateWithTimeIntervalSinceNow_(0.1)
            )

            # Check for timeout
            if time.time() - start_time > timeout:
                print("Timed out waiting for authorization", file=sys.stderr)
                break

        self.event_authorized = event_result["authorized"]
        self.reminder_authorized = reminder_result["authorized"]

        if self.event_authorized:
            print("Calendar access authorized", file=sys.stderr)

        if self.reminder_authorized:
            print("Reminders access authorized", file=sys.stderr)

    def get_calendars(self):
        """Get all available calendars."""
        result = {"event_calendars": [], "reminder_calendars": []}

        if self.event_authorized:
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
            for calendar in calendars:
                result["event_calendars"].append({
                    "title": calendar.title(),
                    "color": f"#{int(calendar.color().redComponent() * 255):02x}{int(calendar.color().greenComponent() * 255):02x}{int(calendar.color().blueComponent() * 255):02x}",
                    "type": "Event"
                })
        else:
            result["events_error"] = "Calendar access not authorized"

        if self.reminder_authorized:
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeReminder)
            for calendar in calendars:
                result["reminder_calendars"].append({
                    "title": calendar.title(),
                    "color": f"#{int(calendar.color().redComponent() * 255):02x}{int(calendar.color().greenComponent() * 255):02x}{int(calendar.color().blueComponent() * 255):02x}",
                    "type": "Reminder"
                })
        else:
            result["reminders_error"] = "Reminders access not authorized"

        return result

    def get_events_and_reminders(self, from_date=None, to_date=None, calendars=None, include_completed=False, all_day_only=False, busy_only=False):
        """Get events and reminders for the specified date range."""
        # Get date range
        start_date, end_date = get_date_range(from_date, to_date)

        # Initialize results
        result = {
            "events": [],
            "reminders": []
        }

        # Get calendar events
        if self.event_authorized:
            # Get calendars for filtering
            all_calendars = None
            if calendars:
                all_cal = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
                filtered_calendars = [c for c in all_cal if c.title() in calendars]
                if filtered_calendars:
                    all_calendars = filtered_calendars

            # Create predicate for events between start and end dates
            predicate = self.event_store.predicateForEventsWithStartDate_endDate_calendars_(start_date, end_date, all_calendars)
            events = self.event_store.eventsMatchingPredicate_(predicate)

            # Filter events
            filtered_events = []
            for event in events:
                if all_day_only and not event.isAllDay():
                    continue
                if busy_only and event.availability() != EKCalendarEventAvailabilityBusy:
                    continue
                filtered_events.append(event)

            # Format events
            for event in filtered_events:
                result["events"].append(format_event(event))
        else:
            result["events_error"] = "Calendar access not authorized"

        # Get reminders
        if self.reminder_authorized:
            # Get calendars for filtering
            reminder_calendars = self.event_store.calendarsForEntityType_(EKEntityTypeReminder)
            if calendars:
                reminder_calendars = [c for c in reminder_calendars if c.title() in calendars]

            if reminder_calendars:
                # Create predicate for reminders
                if include_completed:
                    predicate = self.event_store.predicateForRemindersWithDueDateStarting_ending_calendars_(
                        start_date, end_date, reminder_calendars
                    )
                else:
                    predicate = self.event_store.predicateForIncompleteRemindersWithDueDateStarting_ending_calendars_(
                        start_date, end_date, reminder_calendars
                    )

                # Fetch reminders with completion handler
                reminders_result = {"reminders": None, "complete": False}

                def reminders_callback(fetchedReminders):
                    reminders_result["reminders"] = fetchedReminders
                    reminders_result["complete"] = True

                # Fetch reminders
                self.event_store.fetchRemindersMatchingPredicate_completion_(predicate, reminders_callback)

                # Wait for reminders fetch to complete
                start_time = time.time()
                timeout = 10  # seconds
                while not reminders_result["complete"]:
                    NSRunLoop.currentRunLoop().runMode_beforeDate_(
                        NSDefaultRunLoopMode,
                        NSDate.dateWithTimeIntervalSinceNow_(0.1)
                    )

                    # Check for timeout
                    if time.time() - start_time > timeout:
                        print("Timed out waiting for reminders", file=sys.stderr)
                        break

                # Format reminders
                if reminders_result["reminders"]:
                    for reminder in reminders_result["reminders"]:
                        result["reminders"].append(format_reminder(reminder))
        else:
            result["reminders_error"] = "Reminders access not authorized"

        return result

def format_as_markdown(result):
    """Format the events and reminders result dictionary as Markdown."""
    # Create a renderer and generate the markdown
    renderer = CalendarTemplateRenderer(result)
    return renderer.generate()

class CalendarTemplateRenderer:
    """Render calendar data using Jinja2 templates."""

    # Define the main template as a class variable
    TEMPLATE = """
{%- macro render_event(event) -%}
    {%- set title = event.title|default("No Title") -%}
    {%- set start_time_str = event.start_time|default("") -%}
    {%- set end_time_str = event.end_time|default("") -%}
    {%- set location = event.location|default("") -%}
    {%- set conference_url = event.conference_url|default("") -%}
    {%- set all_day = event.all_day|default(false) -%}
    {%- set calendar = event.calendar|default("Unknown Calendar") -%}

    {%- if all_day -%}
        {%- set time_str = "All Day" -%}
    {%- else -%}
        {%- set time_str = format_time_range(start_time_str, end_time_str) -%}
    {%- endif -%}

    {%- if location and conference_url and location == conference_url -%}
        {%- set loc_str = " ([Join](" + conference_url + "))" -%}
    {%- elif conference_url -%}
        {%- set loc_str = " (" + location + " / [Join](" + conference_url + "))" -%}
    {%- elif location -%}
        {%- set loc_str = " (" + location + ")" -%}
    {%- else -%}
        {%- set loc_str = "" -%}
    {%- endif -%}

    - **{{ title }}** ({{ time_str }}{{ loc_str }}) _{{ calendar }}_
{%- endmacro -%}

{%- macro render_reminder(reminder) -%}
    {%- set title = reminder.title|default("No Title") -%}
    {%- set due_date_str = reminder.due_date|default("") -%}
    {%- set completed = reminder.completed|default(false) -%}
    {%- set calendar = reminder.calendar|default("Unknown Calendar") -%}

    {%- set due_str = "" -%}
    {%- if due_date_str -%}
        {%- set due_str = " (Due: " + format_date(due_date_str) + ")" -%}
    {%- endif -%}

    {%- set status = "[x]" if completed else "[ ]" -%}

    - {{ status }} **{{ title }}**{{ due_str }} _{{ calendar }}_
{%- endmacro -%}

{% if events %}
### Events
{% for event in sort_events(events) %}
{{ render_event(event) }}
{% endfor %}
{% elif events_error %}
### Events
Error: {{ events_error }}
{% endif %}

{% if reminders %}
### Reminders
{% for reminder in sort_reminders(reminders) %}
{{ render_reminder(reminder) }}
{% endfor %}
{% elif reminders_error %}
### Reminders
Error: {{ reminders_error }}
{% endif %}

{% if not events and not reminders and not events_error and not reminders_error %}
No events or reminders found for the specified criteria.
{% endif %}
"""

    def __init__(self, calendar_data):
        self.calendar_data = calendar_data

        # Create a Jinja2 environment
        self.env = Environment(loader=BaseLoader(), undefined=StrictUndefined)

        # Add template functions
        self.env.globals.update({
            'datetime': datetime,
            'format_date': self.format_date,
            'format_time_range': self.format_time_range,
            'sort_events': self.sort_events,
            'sort_reminders': self.sort_reminders,
        })

        self.template = self.env.from_string(self.TEMPLATE)

    def format_date(self, date_str):
        """Format a date string as YYYY-MM-DD."""
        if not date_str:
            return ''
        try:
            dt = datetime.datetime.fromisoformat(date_str.replace(" +0000", "+00:00"))
            return dt.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            return date_str

    def format_time_range(self, start_time_str, end_time_str):
        """Format a time range from start and end time strings."""
        if not start_time_str:
            return ''

        try:
            # Parse the ISO format dates
            start_dt = datetime.datetime.fromisoformat(start_time_str.replace(" +0000", "+00:00")) if start_time_str else None
            end_dt = datetime.datetime.fromisoformat(end_time_str.replace(" +0000", "+00:00")) if end_time_str else None

            # Format times
            start_fmt = start_dt.strftime("%H:%M") if start_dt else ""
            end_fmt = end_dt.strftime("%H:%M") if end_dt else ""

            if start_fmt and end_fmt:
                return f"{start_fmt} - {end_fmt}"
            elif start_fmt:
                return start_fmt
            else:
                return ''
        except (ValueError, AttributeError):
            # Fallback to original strings if parsing fails
            return f"{start_time_str} - {end_time_str}".strip(" -")

    def sort_events(self, events):
        """Sort events by start time."""
        return sorted(events, key=lambda x: x.get('start_time') or '')

    def sort_reminders(self, reminders):
        """Sort reminders by completion status and due date."""
        return sorted(reminders, key=lambda x: (x.get('completed', False), x.get('due_date') or ''))

    def generate(self):
        """Generate complete Markdown report using templates."""
        # Prepare the template context
        context = {
            'events': self.calendar_data.get('events', []),
            'reminders': self.calendar_data.get('reminders', []),
            'events_error': self.calendar_data.get('events_error'),
            'reminders_error': self.calendar_data.get('reminders_error'),
        }

        # Render the template
        try:
            return self.template.render(**context).strip()
        except Exception as e:
            print(f"Error rendering template: {str(e)}", file=sys.stderr)
            return f"Error rendering calendar data: {str(e)}"

# Calendar list template for displaying calendar information
class CalendarListTemplateRenderer:
    """Render calendar list using Jinja2 templates."""

    TEMPLATE = """
{%- if event_calendars %}
### Event Calendars
{% for calendar in sort_calendars(event_calendars) %}
- {{ calendar.title }} ({{ calendar.color }})
{% endfor %}
{% elif events_error %}
### Event Calendars
Error: {{ events_error }}
{% endif %}

{%- if reminder_calendars %}
### Reminder Calendars
{% for calendar in sort_calendars(reminder_calendars) %}
- {{ calendar.title }} ({{ calendar.color }})
{% endfor %}
{% elif reminders_error %}
### Reminder Calendars
Error: {{ reminders_error }}
{% endif %}

{% if not event_calendars and not reminder_calendars and not events_error and not reminders_error %}
No calendars found or access denied.
{% endif %}
"""

    def __init__(self, calendars_data):
        self.calendars_data = calendars_data

        # Create a Jinja2 environment
        self.env = Environment(loader=BaseLoader(), undefined=StrictUndefined)

        # Add template functions
        self.env.globals.update({
            'sort_calendars': lambda calendars: sorted(calendars, key=lambda x: x.get('title', ''))
        })

        self.template = self.env.from_string(self.TEMPLATE)

    def generate(self):
        """Generate complete Markdown report using templates."""
        # Prepare the template context
        context = {
            'event_calendars': self.calendars_data.get('event_calendars', []),
            'reminder_calendars': self.calendars_data.get('reminder_calendars', []),
            'events_error': self.calendars_data.get('events_error'),
            'reminders_error': self.calendars_data.get('reminders_error'),
        }

        # Render the template
        try:
            return self.template.render(**context).strip()
        except Exception as e:
            print(f"Error rendering template: {str(e)}", file=sys.stderr)
            return f"Error rendering calendar list: {str(e)}"

def setup_mcp_server(event_store):
    """Set up the MCP server for calendar events and reminders."""
    mcp = FastMCP("Calendar Events")

    @mcp.tool()
    def get_events(from_date: str = None, to_date: str = None, calendars: list = None,
                  all_day_only: bool = False, busy_only: bool = False, format: str = "markdown"):
        """
        Get calendar events for the specified date range.

        Args:
            from_date: Start date in YYYY-MM-DD format (defaults to today)
            to_date: End date in YYYY-MM-DD format (defaults to from_date)
            calendars: List of calendar names to include (defaults to all)
            all_day_only: Only include all-day events
            busy_only: Only include busy events
            format: Output format ('json' or 'markdown', defaults to 'markdown')

        Returns:
            List of calendar events (json) or a Markdown formatted string.
        """
        from_date_obj = parse_date(from_date) if from_date else None
        to_date_obj = parse_date(to_date) if to_date else None

        # Fetch potentially both, as the underlying method gets both
        result = event_store.get_events_and_reminders(
            from_date=from_date_obj,
            to_date=to_date_obj,
            calendars=calendars,
            all_day_only=all_day_only, # This filtering happens inside get_events_and_reminders
            busy_only=busy_only        # This filtering happens inside get_events_and_reminders
        )

        events_only_result = {"events": result.get("events", []), "events_error": result.get("events_error")}

        if format.lower() == "markdown":
            return format_as_markdown(events_only_result)
        elif format.lower() == "json":
            return events_only_result.get("events", []) # Return only the events list for json
        else:
            raise ValueError("Invalid format specified. Use 'json' or 'markdown'.")

    @mcp.tool()
    def get_reminders(from_date: str = None, to_date: str = None, calendars: list = None,
                     include_completed: bool = False, format: str = "markdown"):
        """
        Get reminders for the specified date range.

        Args:
            from_date: Start date in YYYY-MM-DD format (defaults to today)
            to_date: End date in YYYY-MM-DD format (defaults to from_date)
            calendars: List of calendar names to include (defaults to all)
            include_completed: Whether to include completed reminders
            format: Output format ('json' or 'markdown', defaults to 'markdown')

        Returns:
            List of reminders (json) or a Markdown formatted string.
        """
        from_date_obj = parse_date(from_date) if from_date else None
        to_date_obj = parse_date(to_date) if to_date else None

        # Fetch potentially both, as the underlying method gets both
        result = event_store.get_events_and_reminders(
            from_date=from_date_obj,
            to_date=to_date_obj,
            calendars=calendars,
            include_completed=include_completed # Filtering happens inside get_events_and_reminders
        )

        reminders_only_result = {"reminders": result.get("reminders", []), "reminders_error": result.get("reminders_error")}

        if format.lower() == "markdown":
            return format_as_markdown(reminders_only_result)
        elif format.lower() == "json":
            return reminders_only_result.get("reminders", []) # Return only the reminders list for json
        else:
            raise ValueError("Invalid format specified. Use 'json' or 'markdown'.")

    @mcp.tool()
    def list_calendars(format: str = "json"): # Default to json for listing calendars
        """
        List all available calendars.

        Args:
            format: Output format ('json' or 'markdown', defaults to 'json')

        Returns:
            Dictionary containing event and reminder calendars (json) or a Markdown list.
        """
        calendars_data = event_store.get_calendars()
        if format.lower() == "markdown":
            renderer = CalendarListTemplateRenderer(calendars_data)
            return renderer.generate()
        elif format.lower() == "json":
            return calendars_data
        else:
             raise ValueError("Invalid format specified. Use 'json' or 'markdown'.")


    @mcp.tool()
    def get_today_summary(format: str = "markdown"):
        """
        Get a summary of today's events and reminders.

        Args:
            format: Output format ('json' or 'markdown', defaults to 'markdown')

        Returns:
            Dictionary containing today's events and reminders (json) or a Markdown summary.
        """
        result = event_store.get_events_and_reminders() # Gets today by default
        if format.lower() == "markdown":
            return format_as_markdown(result)
        elif format.lower() == "json":
            return result
        else:
            raise ValueError("Invalid format specified. Use 'json' or 'markdown'.")

    @mcp.tool()
    def search(search_term: str, from_date: str = None, to_date: str = None, calendars: list = None, format: str = "markdown"):
        """
        Search events and reminders within a date range based on a search term.

        Args:
            search_term: The term to search for (case-insensitive) in titles, notes, and locations.
            from_date: Start date in YYYY-MM-DD format (defaults to today)
            to_date: End date in YYYY-MM-DD format (defaults to from_date)
            calendars: List of calendar names to include (defaults to all)
            format: Output format ('json' or 'markdown', defaults to 'markdown')

        Returns:
            Filtered list of events and reminders (json) or a Markdown summary.
        """
        if not search_term:
            raise ValueError("Search term cannot be empty.")

        from_date_obj = parse_date(from_date) if from_date else None
        to_date_obj = parse_date(to_date) if to_date else None

        # Fetch all events/reminders for the range first
        all_results = event_store.get_events_and_reminders(
            from_date=from_date_obj,
            to_date=to_date_obj,
            calendars=calendars
        )

        # Filter results based on search term (case-insensitive)
        search_term_lower = search_term.lower()
        filtered_events = []
        if "events" in all_results:
            for event in all_results["events"]:
                title = (event.get("title") or "").lower()
                notes = (event.get("notes") or "").lower()
                location = (event.get("location") or "").lower()
                if (search_term_lower in title or
                    search_term_lower in notes or
                    search_term_lower in location):
                    filtered_events.append(event)

        filtered_reminders = []
        if "reminders" in all_results:
            for reminder in all_results["reminders"]:
                title = (reminder.get("title") or "").lower()
                notes = (reminder.get("notes") or "").lower()
                if (search_term_lower in title or
                    search_term_lower in notes):
                    filtered_reminders.append(reminder)

        # Prepare the final result structure, including potential errors
        final_result = {
            "events": filtered_events,
            "reminders": filtered_reminders,
            "events_error": all_results.get("events_error"),
            "reminders_error": all_results.get("reminders_error")
        }

        if format.lower() == "markdown":
            # Reuse the existing markdown renderer
            renderer = CalendarTemplateRenderer(final_result)
            output = renderer.generate()
            # Add a header indicating the search term
            return f"## Search Results for \"{search_term}\"\n\n{output}"
        elif format.lower() == "json":
            # Return only the filtered lists for JSON output
            return {"events": filtered_events, "reminders": filtered_reminders}
        else:
            raise ValueError("Invalid format specified. Use 'json' or 'markdown'.")

    @mcp.prompt()
    def daily_agenda(date: str = None):
        """
        Create a prompt for showing the daily agenda.

        Args:
            date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            A prompt string
        """
        date_obj = parse_date(date) if date else datetime.datetime.now()
        date_str = date_obj.strftime("%Y-%m-%d")

        result = event_store.get_events_and_reminders(
            from_date=date_obj,
            to_date=date_obj
        )

        events_str = ""
        for event in result["events"]:
            start_time = event.get("start_time", "All day")
            end_time = event.get("end_time", "")
            time_str = f"{start_time} - {end_time}" if end_time else start_time
            events_str += f"- {event['title']} ({time_str})\n"

        reminders_str = ""
        for reminder in result["reminders"]:
            due_date = reminder.get("due_date", "No due date")
            status = "Completed" if reminder.get("completed", False) else "Incomplete"
            reminders_str += f"- {reminder['title']} ({due_date}, {status})\n"

        return f"""
Please help me understand my schedule for {date_str}.

Events:
{events_str if events_str else "No events scheduled for today."}

Reminders:
{reminders_str if reminders_str else "No reminders due today."}

What should I focus on today? Any conflicts or tight schedules to be aware of?
"""

    return mcp

def main():
    """Main function to get and display calendar events and reminders."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Fetch calendar events and reminders")
    parser.add_argument("--schema", "-s", action="store_true", help="Output the JSON schema instead of actual data")
    parser.add_argument("--from", dest="from_date", type=parse_date, help="Start date (YYYY-MM-DD, defaults to today)")
    parser.add_argument("--to", dest="to_date", type=parse_date, help="End date (YYYY-MM-DD, defaults to from_date)")
    parser.add_argument("--calendars", "-c", nargs="+", help="Filter by calendar names (space separated)")
    parser.add_argument("--include-completed", action="store_true", help="Include completed reminders")
    parser.add_argument("--all-day-only", action="store_true", help="Only include all-day events")
    parser.add_argument("--busy-only", action="store_true", help="Only include busy events")
    parser.add_argument("--list-calendars", action="store_true", help="List available calendars and exit")
    parser.add_argument("--mcp", action="store_true", help="Run as an MCP server using stdin/stdout")
    parser.add_argument("--format", choices=['json', 'markdown'], default='json', help="Output format (default: json)") # Added format argument
    args = parser.parse_args()

    # If --schema flag is provided, output the schema and exit
    if args.schema:
        print(json.dumps(get_json_schema(), indent=2))
        return

    # Create event store
    event_store = CalendarEventStore()

    # If mcp flag is provided, run as MCP server using stdio
    if args.mcp:
        # Set up and run the MCP server using stdio
        mcp = setup_mcp_server(event_store)
        print("Starting MCP server using stdin/stdout...", file=sys.stderr)
        print("Connect Claude Desktop to this process", file=sys.stderr)
        # The MCP SDK should handle stdio serving automatically when run directly.
        mcp.run('stdio')
        return

    # If list-calendars flag is provided, list calendars and exit
    if args.list_calendars:
        result = event_store.get_calendars()
        # Handle format for list_calendars CLI output
        if args.format == 'markdown':
            # Use the template renderer
            renderer = CalendarListTemplateRenderer(result)
            print(renderer.generate())
        else:
            print(json.dumps(result, indent=2)) # Default JSON
        return

    # Get events and reminders
    result = event_store.get_events_and_reminders(
        from_date=args.from_date,
        to_date=args.to_date,
        calendars=args.calendars,
        include_completed=args.include_completed,
        all_day_only=args.all_day_only,
        busy_only=args.busy_only
    )

    # Output as JSON or Markdown based on --format
    if args.format == 'markdown':
        print(format_as_markdown(result))
    else:
        # Default to JSON
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
