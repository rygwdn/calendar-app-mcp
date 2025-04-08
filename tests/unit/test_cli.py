"""Tests for CLI module."""

import argparse
import json
import sys
from unittest.mock import patch, MagicMock, call

import pytest

from calendar_app.cli import main


@patch("calendar_app.cli.CalendarEventStore")
@patch("calendar_app.cli.argparse.ArgumentParser.parse_args")
def test_help_output_when_no_command(mock_parse_args, mock_event_store):
    """Test CLI shows help when no command is provided."""
    # Setup mock without the 'func' attribute to simulate no command
    mock_args = MagicMock(spec=[])
    mock_parse_args.return_value = mock_args
    
    # Mock ArgumentParser for help
    with patch("calendar_app.cli.argparse.ArgumentParser.print_help") as mock_print_help:
        # Call main function
        main()
        
        # Verify behavior
        mock_print_help.assert_called_once()
        # Verify event store was not created
        mock_event_store.assert_not_called()


@patch("calendar_app.cli.CalendarEventStore")
@patch("calendar_app.cli.get_json_schema")
@patch("calendar_app.cli.argparse.ArgumentParser.parse_args")
@patch("calendar_app.cli.print")
def test_schema_subcommand(mock_print, mock_parse_args, mock_get_schema, mock_event_store):
    """Test CLI outputs schema with 'schema' subcommand."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.func = MagicMock()  # This simulates having a subcommand
    mock_parse_args.return_value = mock_args
    
    mock_schema = {"type": "object", "properties": {}}
    mock_get_schema.return_value = mock_schema
    
    # Create event store mock
    mock_event_store_instance = MagicMock()
    mock_event_store.return_value = mock_event_store_instance
    
    # Call the cmd_schema function directly
    from calendar_app.cli import cmd_schema
    cmd_schema(mock_args, mock_event_store_instance)
    
    # Verify behavior
    mock_get_schema.assert_called_once()
    mock_print.assert_called_once_with(json.dumps(mock_schema, indent=2))


@patch("calendar_app.cli.CalendarEventStore")
@patch("calendar_app.cli.setup_mcp_server")
@patch("calendar_app.cli.argparse.ArgumentParser.parse_args")
@patch("calendar_app.cli.print")
def test_mcp_subcommand(mock_print, mock_parse_args, mock_setup_mcp, mock_event_store):
    """Test CLI runs MCP server with 'mcp' subcommand."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.func = MagicMock()  # This simulates having a subcommand
    mock_parse_args.return_value = mock_args
    
    mock_mcp = MagicMock()
    mock_setup_mcp.return_value = mock_mcp
    
    mock_event_store_instance = MagicMock()
    mock_event_store.return_value = mock_event_store_instance
    
    # Call the cmd_mcp function directly
    from calendar_app.cli import cmd_mcp
    cmd_mcp(mock_args, mock_event_store_instance)
    
    # Verify behavior
    mock_setup_mcp.assert_called_once_with(mock_event_store_instance)
    mock_mcp.run.assert_called_once_with('stdio')
    
    # Verify print messages
    assert mock_print.call_count >= 2
    assert any("Starting MCP server" in call[0][0] for call in mock_print.call_args_list)
    assert all(call[1]["file"] == sys.stderr for call in mock_print.call_args_list)


@patch("calendar_app.cli.CalendarEventStore")
@patch("calendar_app.cli.CalendarListTemplateRenderer")
@patch("calendar_app.cli.argparse.ArgumentParser.parse_args")
@patch("calendar_app.cli.print")
def test_calendars_subcommand(mock_print, mock_parse_args, mock_renderer, mock_event_store):
    """Test CLI lists calendars with 'calendars' subcommand."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.format = 'markdown'
    mock_parse_args.return_value = mock_args
    
    mock_event_store_instance = MagicMock()
    mock_calendars = {"event_calendars": [{"title": "Work"}]}
    mock_event_store_instance.get_calendars.return_value = mock_calendars
    mock_event_store.return_value = mock_event_store_instance
    
    mock_renderer_instance = MagicMock()
    mock_renderer_instance.generate.return_value = "Calendar List Markdown"
    mock_renderer.return_value = mock_renderer_instance
    
    # Call the cmd_calendars function directly
    from calendar_app.cli import cmd_calendars
    cmd_calendars(mock_args, mock_event_store_instance)
    
    # Verify behavior
    mock_event_store_instance.get_calendars.assert_called_once()
    mock_renderer.assert_called_once_with(mock_calendars)
    mock_renderer_instance.generate.assert_called_once()
    mock_print.assert_called_once_with("Calendar List Markdown")


@patch("calendar_app.cli.format_as_markdown")
@patch("calendar_app.cli.print")
def test_events_subcommand_markdown(mock_print, mock_format):
    """Test 'events' subcommand with markdown format."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.from_date = None
    mock_args.to_date = None
    mock_args.calendars = None
    mock_args.all_day_only = False
    mock_args.busy_only = False
    mock_args.format = 'markdown'
    
    mock_event_store = MagicMock()
    mock_events = {"events": [{"title": "Meeting"}], "reminders": []}
    mock_event_store.get_events_and_reminders.return_value = mock_events
    
    mock_format.return_value = "Events Markdown"
    
    # Call the cmd_events function directly
    from calendar_app.cli import cmd_events
    cmd_events(mock_args, mock_event_store)
    
    # Verify behavior
    mock_event_store.get_events_and_reminders.assert_called_once_with(
        from_date=None,
        to_date=None,
        calendars=None,
        all_day_only=False,
        busy_only=False
    )
    # Verify that only the events part is passed to format_as_markdown
    expected_events_only = {"events": [{"title": "Meeting"}], "events_error": None}
    mock_format.assert_called_once()
    # Check that the call contains the events but not reminders
    call_args = mock_format.call_args[0][0]
    assert "events" in call_args
    assert "reminders" not in call_args
    
    mock_print.assert_called_once_with("Events Markdown")


@patch("calendar_app.cli.json.dumps")
@patch("calendar_app.cli.print")
def test_reminders_subcommand_json(mock_print, mock_json_dumps):
    """Test 'reminders' subcommand with json format."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.from_date = None
    mock_args.to_date = None
    mock_args.calendars = None
    mock_args.include_completed = True
    mock_args.format = 'json'
    
    mock_event_store = MagicMock()
    mock_result = {"events": [], "reminders": [{"title": "Task"}]}
    mock_event_store.get_events_and_reminders.return_value = mock_result
    
    expected_reminders_only = {"reminders": [{"title": "Task"}], "reminders_error": None}
    mock_json_dumps.return_value = '{"reminders":[{"title":"Task"}]}'
    
    # Call the cmd_reminders function directly
    from calendar_app.cli import cmd_reminders
    cmd_reminders(mock_args, mock_event_store)
    
    # Verify behavior
    mock_event_store.get_events_and_reminders.assert_called_once_with(
        from_date=None,
        to_date=None,
        calendars=None,
        include_completed=True
    )
    # Check json.dumps was called with only reminders and not events
    mock_json_dumps.assert_called_once()
    call_args = mock_json_dumps.call_args[0][0]
    assert "reminders" in call_args
    assert "events" not in call_args
    
    mock_print.assert_called_once_with('{"reminders":[{"title":"Task"}]}')


@patch("calendar_app.cli.format_as_markdown")
@patch("calendar_app.cli.print")
def test_today_subcommand(mock_print, mock_format):
    """Test 'today' subcommand."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.calendars = ["Work"]
    mock_args.include_completed = False
    mock_args.all_day_only = True
    mock_args.busy_only = False
    mock_args.format = 'markdown'
    
    mock_event_store = MagicMock()
    mock_result = {"events": [{"title": "Meeting"}], "reminders": []}
    mock_event_store.get_events_and_reminders.return_value = mock_result
    
    mock_format.return_value = "Today's Events Markdown"
    
    # Call the cmd_today function directly
    from calendar_app.cli import cmd_today
    cmd_today(mock_args, mock_event_store)
    
    # Verify behavior
    mock_event_store.get_events_and_reminders.assert_called_once_with(
        calendars=["Work"],
        include_completed=False,
        all_day_only=True,
        busy_only=False
    )
    # Verify that the full result is passed to format_as_markdown
    mock_format.assert_called_once_with(mock_result)
    mock_print.assert_called_once_with("Today's Events Markdown")


@patch("calendar_app.cli.format_as_markdown")
@patch("calendar_app.cli.print")
def test_all_subcommand(mock_print, mock_format):
    """Test 'all' subcommand."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.from_date = "2023-01-01"
    mock_args.to_date = "2023-01-31"
    mock_args.calendars = ["Work", "Personal"]
    mock_args.include_completed = True
    mock_args.all_day_only = False
    mock_args.busy_only = True
    mock_args.format = 'markdown'
    
    mock_event_store = MagicMock()
    mock_result = {"events": [{"title": "Meeting"}], "reminders": [{"title": "Task"}]}
    mock_event_store.get_events_and_reminders.return_value = mock_result
    
    mock_format.return_value = "All Events and Reminders Markdown"
    
    # Call the cmd_all function directly
    from calendar_app.cli import cmd_all
    cmd_all(mock_args, mock_event_store)
    
    # Verify behavior
    mock_event_store.get_events_and_reminders.assert_called_once_with(
        from_date="2023-01-01",
        to_date="2023-01-31",
        calendars=["Work", "Personal"],
        include_completed=True,
        all_day_only=False,
        busy_only=True
    )
    mock_format.assert_called_once_with(mock_result)
    mock_print.assert_called_once_with("All Events and Reminders Markdown")


def test_setup_common_parser():
    """Test that setup_common_parser adds expected arguments."""
    from calendar_app.cli import setup_common_parser
    parser = argparse.ArgumentParser()
    
    # Mock the add_argument method
    original_add_argument = parser.add_argument
    mock_calls = []
    
    def mock_add_argument(*args, **kwargs):
        mock_calls.append((args, kwargs))
        return original_add_argument(*args, **kwargs)
    
    parser.add_argument = mock_add_argument
    
    # Call setup_common_parser
    setup_common_parser(parser)
    
    # Check that required arguments were added
    argument_flags = []
    for args, _ in mock_calls:
        argument_flags.extend([arg for arg in args if arg.startswith('-')])
    
    assert "--from" in argument_flags
    assert "--to" in argument_flags
    assert "--calendars" in argument_flags or "-c" in argument_flags
    assert "--format" in argument_flags


@patch("calendar_app.cli.argparse.ArgumentParser")
def test_subparsers_creation(mock_argparser):
    """Test that all expected subparsers are created."""
    # Mock ArgumentParser and subparsers
    mock_parser = MagicMock()
    mock_argparser.return_value = mock_parser
    
    mock_subparsers = MagicMock()
    mock_parser.add_subparsers.return_value = mock_subparsers
    
    mock_subparser = MagicMock()
    mock_subparsers.add_parser.return_value = mock_subparser
    
    # Create a dict to track function assignments
    mock_funcs = {}
    
    def track_func_assignment(func):
        mock_funcs[func.__name__] = func
    
    mock_subparser.set_defaults.side_effect = track_func_assignment
    
    # Prevent actual execution by mocking other components
    with patch("calendar_app.cli.CalendarEventStore"), \
         patch("calendar_app.cli.setup_common_parser", return_value=mock_subparser):
        
        # Call main with argparse mocked
        with patch("calendar_app.cli.argparse.ArgumentParser.parse_args", 
                  side_effect=SystemExit):
            try:
                main()
            except SystemExit:
                pass
    
    # Check that all expected subparsers were created
    expected_commands = ["events", "reminders", "all", "calendars", "today", "schema", "mcp"]
    
    # Get actual commands (subparser names)
    actual_commands = []
    for call_args in mock_subparsers.add_parser.call_args_list:
        args, _ = call_args
        actual_commands.append(args[0])
    
    for cmd in expected_commands:
        assert cmd in actual_commands, f"Subparser for '{cmd}' not created"