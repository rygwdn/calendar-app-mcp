"""Command-line interface for calendar events and reminders."""

import argparse
import json
import sys

from calendar_app.models.event_store import CalendarEventStore
from calendar_app.models.formatters import get_json_schema
from calendar_app.utils.date_utils import parse_date
from calendar_app.renderers.markdown import format_as_markdown
from calendar_app.renderers.calendar_list import CalendarListTemplateRenderer
from calendar_app.tools.mcp_server import setup_mcp_server


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
    parser.add_argument("--format", choices=['json', 'markdown'], default='json', help="Output format (default: json)")
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