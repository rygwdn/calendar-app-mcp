"""Tests for MCP server setup."""

from unittest.mock import MagicMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from calendar_app.tools.mcp_server import setup_mcp_server


@patch("calendar_app.tools.mcp_server.FastMCP")
def test_setup_mcp_server(mock_fastmcp):
    """Test setting up the MCP server."""
    # Mock FastMCP instance
    mock_mcp = MagicMock()
    mock_fastmcp.return_value = mock_mcp

    # Create mock event store
    mock_event_store = MagicMock()

    # Call function
    result = setup_mcp_server(mock_event_store)

    # Verify FastMCP was created with the correct name
    mock_fastmcp.assert_called_once_with("Calendar Events")

    # Verify that tools were registered
    assert mock_mcp.tool.call_count >= 5  # We have at least 5 tools

    # Verify that the prompt function was registered
    assert mock_mcp.prompt.call_count >= 1  # We have at least 1 prompt

    # Verify result
    assert result == mock_mcp


def test_mcp_tools_registered():
    """Test that all expected MCP tools are registered when setup_mcp_server is called."""
    # Create mock objects
    mock_mcp = MagicMock()
    mock_event_store = MagicMock()

    # Create a list to capture registered function names
    registered_functions = []

    # Define a side effect to capture function names
    def capture_tool(func=None):
        if func is not None:
            registered_functions.append(func.__name__)
        return lambda f: registered_functions.append(f.__name__)

    # Configure the mock MCP
    mock_mcp.tool = capture_tool
    mock_mcp.prompt = lambda func=None: (lambda f: None) if func is None else None

    # Mock FastMCP
    with patch("calendar_app.tools.mcp_server.FastMCP", return_value=mock_mcp):
        # Call function
        setup_mcp_server(mock_event_store)

    # Verify that all expected tools were registered
    expected_tools = [
        "get_events",
        "get_reminders",
        "list_calendars",
        "get_today_summary",
        "search",
    ]

    for tool in expected_tools:
        assert (
            tool in registered_functions
        ), f"Expected tool {tool} not found in registered functions"
