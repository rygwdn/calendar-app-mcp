"""Markdown template renderers for calendar events and reminders."""

import datetime
import sys

from jinja2 import BaseLoader, Environment, StrictUndefined


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

    def __init__(self, calendar_data) -> None:
        self.calendar_data = calendar_data

        # Create a Jinja2 environment
        self.env = Environment(loader=BaseLoader(), undefined=StrictUndefined)

        # Add template functions
        self.env.globals.update(
            {
                "datetime": datetime,
                "format_date": self.format_date,
                "format_time_range": self.format_time_range,
                "sort_events": self.sort_events,
                "sort_reminders": self.sort_reminders,
            }
        )

        self.template = self.env.from_string(self.TEMPLATE)

    def format_date(self, date_str):
        """Format a date string as YYYY-MM-DD."""
        if not date_str:
            return ""
        try:
            dt = datetime.datetime.fromisoformat(date_str.replace(" +0000", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return date_str

    def format_time_range(self, start_time_str, end_time_str):
        """Format a time range from start and end time strings."""
        if not start_time_str:
            return ""

        try:
            # Parse the ISO format dates
            start_dt = (
                datetime.datetime.fromisoformat(start_time_str.replace(" +0000", "+00:00"))
                if start_time_str
                else None
            )
            end_dt = (
                datetime.datetime.fromisoformat(end_time_str.replace(" +0000", "+00:00"))
                if end_time_str
                else None
            )

            # Format times
            start_fmt = start_dt.strftime("%H:%M") if start_dt else ""
            end_fmt = end_dt.strftime("%H:%M") if end_dt else ""

            if start_fmt and end_fmt:
                return f"{start_fmt} - {end_fmt}"
            elif start_fmt:
                return start_fmt
            else:
                return ""
        except (ValueError, AttributeError):
            # Fallback to original strings if parsing fails
            return f"{start_time_str} - {end_time_str}".strip(" -")

    def sort_events(self, events):
        """Sort events by start time."""
        return sorted(events, key=lambda x: x.get("start_time") or "")

    def sort_reminders(self, reminders):
        """Sort reminders by completion status and due date."""
        return sorted(reminders, key=lambda x: (x.get("completed", False), x.get("due_date") or ""))

    def generate(self):
        """Generate complete Markdown report using templates."""
        # Prepare the template context
        context = {
            "events": self.calendar_data.get("events", []),
            "reminders": self.calendar_data.get("reminders", []),
            "events_error": self.calendar_data.get("events_error"),
            "reminders_error": self.calendar_data.get("reminders_error"),
        }

        # Render the template
        try:
            return self.template.render(**context).strip()
        except Exception as e:
            print(f"Error rendering template: {e!s}", file=sys.stderr)
            return f"Error rendering calendar data: {e!s}"
