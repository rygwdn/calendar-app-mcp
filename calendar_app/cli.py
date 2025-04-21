"""Command-line interface for calendar events and reminders."""

import argparse
import importlib.metadata
import json
import sys

from calendar_app.models.event_store import CalendarEventStore
from calendar_app.models.formatters import get_json_schema
from calendar_app.renderers.calendar_list import CalendarListTemplateRenderer
from calendar_app.renderers.markdown import format_as_markdown
from calendar_app.tools.mcp_server import setup_mcp_server
from calendar_app.utils.date_utils import parse_date

# Get version from package metadata
try:
    __version__ = importlib.metadata.version("calendar-app-mcp")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


def setup_common_parser(parser):
    """Setup common arguments for parsers."""
    parser.add_argument(
        "--from",
        dest="from_date",
        type=parse_date,
        help="Start date (YYYY-MM-DD, defaults to today)",
    )
    parser.add_argument(
        "--to", dest="to_date", type=parse_date, help="End date (YYYY-MM-DD, defaults to from_date)"
    )
    parser.add_argument(
        "--calendars", "-c", nargs="+", help="Filter by calendar names (space separated)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output in JSON format (default: markdown)"
    )
    return parser


def cmd_events(args, event_store) -> None:
    """Command handler for 'events' subcommand."""
    result = event_store.get_events_and_reminders(
        from_date=args.from_date,
        to_date=args.to_date,
        calendars=args.calendars,
        all_day_only=args.all_day_only,
        busy_only=args.busy_only,
    )

    # Keep only events from result
    events_only = {"events": result.get("events", []), "events_error": result.get("events_error")}

    # Output as JSON or Markdown (default)
    if args.json:
        print(json.dumps(events_only, indent=2))
    else:
        print(format_as_markdown(events_only))


def cmd_reminders(args, event_store) -> None:
    """Command handler for 'reminders' subcommand."""
    result = event_store.get_events_and_reminders(
        from_date=args.from_date,
        to_date=args.to_date,
        calendars=args.calendars,
        include_completed=args.include_completed,
    )

    # Keep only reminders from result
    reminders_only = {
        "reminders": result.get("reminders", []),
        "reminders_error": result.get("reminders_error"),
    }

    # Output as JSON or Markdown (default)
    if args.json:
        print(json.dumps(reminders_only, indent=2))
    else:
        print(format_as_markdown(reminders_only))


def cmd_all(args, event_store) -> None:
    """Command handler for 'all' subcommand."""
    result = event_store.get_events_and_reminders(
        from_date=args.from_date,
        to_date=args.to_date,
        calendars=args.calendars,
        include_completed=args.include_completed,
        all_day_only=args.all_day_only,
        busy_only=args.busy_only,
    )

    # Output as JSON or Markdown (default)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_as_markdown(result))


def cmd_calendars(args, event_store) -> None:
    """Command handler for 'calendars' subcommand."""
    result = event_store.get_calendars()

    # Handle format (default to markdown)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        renderer = CalendarListTemplateRenderer(result)
        print(renderer.generate())


def cmd_today(args, event_store) -> None:
    """Command handler for 'today' subcommand."""
    # No dates needed - will default to today
    result = event_store.get_events_and_reminders(
        calendars=args.calendars,
        include_completed=args.include_completed,
        all_day_only=args.all_day_only,
        busy_only=args.busy_only,
    )

    # Output as JSON or Markdown (default)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_as_markdown(result))


def cmd_schema(args, event_store) -> None:
    """Command handler for 'schema' subcommand."""
    print(json.dumps(get_json_schema(), indent=2))


def cmd_version(args, event_store) -> None:
    """Command handler for 'version' subcommand."""
    print(f"calendar-app-mcp version {__version__}")


def cmd_mcp(args, event_store, quiet=False) -> None:
    """Command handler for 'mcp' subcommand."""
    # Set up and run the MCP server using stdio
    mcp = setup_mcp_server(event_store)
    if not quiet:
        print("Starting MCP server using stdin/stdout...", file=sys.stderr)
        print("Connect Claude Desktop to this process", file=sys.stderr)
    mcp.run("stdio")


def main() -> None:
    """Main function to get and display calendar events and reminders."""
    # Check which command was used to invoke the script
    import os

    program_name = os.path.basename(sys.argv[0])
    mcp_default = program_name == "calendar-app-mcp"

    # Create main parser
    parser = argparse.ArgumentParser(
        description=f"Calendar app for events and reminders (v{__version__})",
        epilog=f"Calendar-app-mcp version {__version__}",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Create subparsers
    subparsers = parser.add_subparsers(
        title="commands", description="valid subcommands", dest="command", help="command to execute"
    )

    # 'events' subcommand
    events_parser = subparsers.add_parser("events", help="Get calendar events")
    events_parser = setup_common_parser(events_parser)
    events_parser.add_argument(
        "--all-day-only", action="store_true", help="Only include all-day events"
    )
    events_parser.add_argument("--busy-only", action="store_true", help="Only include busy events")
    events_parser.set_defaults(func=cmd_events)

    # 'reminders' subcommand
    reminders_parser = subparsers.add_parser("reminders", help="Get reminders")
    reminders_parser = setup_common_parser(reminders_parser)
    reminders_parser.add_argument(
        "--include-completed", action="store_true", help="Include completed reminders"
    )
    reminders_parser.set_defaults(func=cmd_reminders)

    # 'all' subcommand - both events and reminders
    all_parser = subparsers.add_parser("all", help="Get both events and reminders")
    all_parser = setup_common_parser(all_parser)
    all_parser.add_argument(
        "--include-completed", action="store_true", help="Include completed reminders"
    )
    all_parser.add_argument(
        "--all-day-only", action="store_true", help="Only include all-day events"
    )
    all_parser.add_argument("--busy-only", action="store_true", help="Only include busy events")
    all_parser.set_defaults(func=cmd_all)

    # 'calendars' subcommand
    calendars_parser = subparsers.add_parser("calendars", help="List available calendars")
    calendars_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format (default: markdown)"
    )
    calendars_parser.set_defaults(func=cmd_calendars)

    # 'today' subcommand - shortcuts to today's events and reminders
    today_parser = subparsers.add_parser("today", help="Get today's events and reminders")
    today_parser.add_argument(
        "--calendars", "-c", nargs="+", help="Filter by calendar names (space separated)"
    )
    today_parser.add_argument(
        "--include-completed", action="store_true", help="Include completed reminders"
    )
    today_parser.add_argument(
        "--all-day-only", action="store_true", help="Only include all-day events"
    )
    today_parser.add_argument("--busy-only", action="store_true", help="Only include busy events")
    today_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format (default: markdown)"
    )
    today_parser.set_defaults(func=cmd_today)

    # 'schema' subcommand
    schema_parser = subparsers.add_parser("schema", help="Show the JSON schema for the output")
    schema_parser.set_defaults(func=cmd_schema)

    # 'version' subcommand
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.set_defaults(func=cmd_version)

    # 'mcp' subcommand
    mcp_parser = subparsers.add_parser("mcp", help="Run as an MCP server")
    mcp_parser.set_defaults(func=cmd_mcp)

    # Parse arguments
    args = parser.parse_args()

    # Get quiet flag for mcp
    quiet = mcp_default and not hasattr(args, "func")

    # Create event store with quiet flag for MCP mode
    event_store = CalendarEventStore(quiet=quiet)

    # If no command is provided, check which tool was used
    if not hasattr(args, "func"):
        if mcp_default:
            # Run MCP in quiet mode
            cmd_mcp(args, event_store, quiet=True)
        else:
            parser.print_help()
        return

    # Call the appropriate function with arguments
    args.func(args, event_store)


if __name__ == "__main__":
    main()
