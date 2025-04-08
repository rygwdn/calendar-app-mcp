"""Calendar list template renderer."""

import sys
from jinja2 import Environment, BaseLoader, StrictUndefined


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