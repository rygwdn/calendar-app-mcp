"""MCP server for calendar events and reminders."""

import datetime
from mcp.server.fastmcp import FastMCP

from calendar_app.utils.date_utils import parse_date
from calendar_app.renderers.markdown import format_as_markdown
from calendar_app.renderers.calendar_list import CalendarListTemplateRenderer


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
            return format_as_markdown(final_result)
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