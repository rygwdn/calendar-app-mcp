"""Tests for CLI module."""

import argparse
import json
import sys
from unittest.mock import patch, MagicMock

import pytest

from calendar_app.cli import main


@patch("calendar_app.cli.CalendarEventStore")
@patch("calendar_app.cli.get_json_schema")
@patch("calendar_app.cli.argparse.ArgumentParser.parse_args")
@patch("calendar_app.cli.print")
def test_schema_output(mock_print, mock_parse_args, mock_get_schema, mock_event_store):
    """Test CLI outputs schema when --schema flag is provided."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.schema = True
    mock_parse_args.return_value = mock_args
    
    mock_schema = {"type": "object", "properties": {}}
    mock_get_schema.return_value = mock_schema
    
    # Call main function
    main()
    
    # Verify behavior
    mock_get_schema.assert_called_once()
    mock_print.assert_called_once_with(json.dumps(mock_schema, indent=2))
    # Verify event store was not created
    mock_event_store.assert_not_called()


@patch("calendar_app.cli.CalendarEventStore")
@patch("calendar_app.cli.setup_mcp_server")
@patch("calendar_app.cli.argparse.ArgumentParser.parse_args")
@patch("calendar_app.cli.print")
def test_mcp_server(mock_print, mock_parse_args, mock_setup_mcp, mock_event_store):
    """Test CLI runs MCP server when --mcp flag is provided."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.schema = False
    mock_args.mcp = True
    mock_parse_args.return_value = mock_args
    
    mock_mcp = MagicMock()
    mock_setup_mcp.return_value = mock_mcp
    
    mock_event_store_instance = MagicMock()
    mock_event_store.return_value = mock_event_store_instance
    
    # Call main function
    main()
    
    # Verify behavior
    mock_event_store.assert_called_once()
    mock_setup_mcp.assert_called_once_with(mock_event_store_instance)
    mock_mcp.run.assert_called_once_with('stdio')
    
    # Verify print messages
    assert mock_print.call_count >= 2
    assert any("Starting MCP server" in call[0][0] for call in mock_print.call_args_list)
    assert all(call[1]["file"] == sys.stderr for call in mock_print.call_args_list)


@patch("calendar_app.cli.CalendarEventStore")
@patch("calendar_app.cli.format_as_markdown")
@patch("calendar_app.cli.CalendarListTemplateRenderer")
@patch("calendar_app.cli.argparse.ArgumentParser.parse_args")
@patch("calendar_app.cli.print")
def test_list_calendars(mock_print, mock_parse_args, mock_renderer, mock_format, mock_event_store):
    """Test CLI lists calendars when --list-calendars flag is provided."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.schema = False
    mock_args.mcp = False
    mock_args.list_calendars = True
    mock_args.format = 'markdown'
    mock_parse_args.return_value = mock_args
    
    mock_event_store_instance = MagicMock()
    mock_calendars = {"event_calendars": [{"title": "Work"}]}
    mock_event_store_instance.get_calendars.return_value = mock_calendars
    mock_event_store.return_value = mock_event_store_instance
    
    mock_renderer_instance = MagicMock()
    mock_renderer_instance.generate.return_value = "Calendar List Markdown"
    mock_renderer.return_value = mock_renderer_instance
    
    # Call main function
    main()
    
    # Verify behavior
    mock_event_store.assert_called_once()
    mock_event_store_instance.get_calendars.assert_called_once()
    mock_renderer.assert_called_once_with(mock_calendars)
    mock_renderer_instance.generate.assert_called_once()
    mock_print.assert_called_once_with("Calendar List Markdown")


@patch("calendar_app.cli.CalendarEventStore")
@patch("calendar_app.cli.format_as_markdown")
@patch("calendar_app.cli.argparse.ArgumentParser.parse_args")
@patch("calendar_app.cli.print")
def test_get_events_and_reminders_markdown(mock_print, mock_parse_args, mock_format, mock_event_store):
    """Test CLI gets events in markdown format by default."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.schema = False
    mock_args.mcp = False
    mock_args.list_calendars = False
    mock_args.from_date = None
    mock_args.to_date = None
    mock_args.calendars = None
    mock_args.include_completed = False
    mock_args.all_day_only = False
    mock_args.busy_only = False
    mock_args.format = 'markdown'
    mock_parse_args.return_value = mock_args
    
    mock_event_store_instance = MagicMock()
    mock_events = {"events": [{"title": "Meeting"}]}
    mock_event_store_instance.get_events_and_reminders.return_value = mock_events
    mock_event_store.return_value = mock_event_store_instance
    
    mock_format.return_value = "Events Markdown"
    
    # Call main function
    main()
    
    # Verify behavior
    mock_event_store.assert_called_once()
    mock_event_store_instance.get_events_and_reminders.assert_called_once_with(
        from_date=None,
        to_date=None,
        calendars=None,
        include_completed=False,
        all_day_only=False,
        busy_only=False
    )
    mock_format.assert_called_once_with(mock_events)
    mock_print.assert_called_once_with("Events Markdown")


@patch("calendar_app.cli.CalendarEventStore")
@patch("calendar_app.cli.argparse.ArgumentParser.parse_args")
@patch("calendar_app.cli.print")
@patch("calendar_app.cli.json.dumps")
def test_get_events_and_reminders_json(mock_json_dumps, mock_print, mock_parse_args, mock_event_store):
    """Test CLI gets events in json format when specified."""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.schema = False
    mock_args.mcp = False
    mock_args.list_calendars = False
    mock_args.from_date = None
    mock_args.to_date = None
    mock_args.calendars = None
    mock_args.include_completed = False
    mock_args.all_day_only = False
    mock_args.busy_only = False
    mock_args.format = 'json'
    mock_parse_args.return_value = mock_args
    
    mock_event_store_instance = MagicMock()
    mock_events = {"events": [{"title": "Meeting"}]}
    mock_event_store_instance.get_events_and_reminders.return_value = mock_events
    mock_event_store.return_value = mock_event_store_instance
    
    mock_json_dumps.return_value = '{"events":[{"title":"Meeting"}]}'
    
    # Call main function
    main()
    
    # Verify behavior
    mock_event_store.assert_called_once()
    mock_event_store_instance.get_events_and_reminders.assert_called_once_with(
        from_date=None,
        to_date=None,
        calendars=None,
        include_completed=False,
        all_day_only=False,
        busy_only=False
    )
    mock_json_dumps.assert_called_once_with(mock_events, indent=2)
    mock_print.assert_called_once_with('{"events":[{"title":"Meeting"}]}')


@patch("calendar_app.cli.argparse.ArgumentParser.parse_args")
def test_parse_arguments(mock_parse_args):
    """Test argument parsing in CLI."""
    with patch("calendar_app.cli.argparse.ArgumentParser.add_argument") as mock_add_argument:
        # Setup mock
        mock_args = MagicMock()
        mock_parse_args.return_value = mock_args
        
        # Call main function with some dummy patching to prevent actual execution
        with patch("calendar_app.cli.CalendarEventStore"), \
             patch("calendar_app.cli.print"), \
             patch("calendar_app.cli.get_json_schema", side_effect=Exception("Stop")):
            try:
                main()
            except Exception as e:
                if str(e) != "Stop":
                    raise
        
        # Verify all expected arguments were added
        argument_calls = mock_add_argument.call_args_list
        argument_flags = [call[0][0] for call in argument_calls if call[0]]
        
        # Verify required arguments
        assert "--schema" in argument_flags or "-s" in argument_flags
        assert "--from" in argument_flags
        assert "--to" in argument_flags
        assert "--calendars" in argument_flags or "-c" in argument_flags
        assert "--include-completed" in argument_flags
        assert "--all-day-only" in argument_flags
        assert "--busy-only" in argument_flags
        assert "--list-calendars" in argument_flags
        assert "--mcp" in argument_flags
        assert "--format" in argument_flags