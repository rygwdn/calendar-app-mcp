# Calendar App MCP

An MCP (Model Context Protocol) server that provides access to macOS Calendar.app events and reminders for use with Claude and other AI assistants.

## MCP Integration

This package can be run as an MCP server to integrate with Claude and other AI assistants supporting the MCP protocol, enabling them to access and interact with your macOS calendar data.

```bash
# Run as MCP server for AI assistant integration
uv run calendar-app mcp
```

Once running, Claude can interact with your calendar data through the MCP protocol, allowing it to:
- Check your upcoming events
- Find free time slots
- View event details
- Access reminders
- Filter events by calendar, date range, and more

## Features

- Access macOS Calendar.app events and reminders
- Filter by date range, calendar names, and all-day/busy status
- Format output as JSON or Markdown
- Secure, local access to calendar data

## Installation

```bash
# Install uv package manager if not already installed
# https://github.com/astral-sh/uv

# Install the package
uv install -e .

# Install with development dependencies (for testing)
uv install -e '.[dev]'
```

## CLI Usage

In addition to functioning as an MCP server, this package can be used as a command-line tool to access calendar data directly:

```bash
# List available calendars
uv run calendar-app calendars

# Get today's events and reminders
uv run calendar-app today

# Get only events
uv run calendar-app events

# Get only reminders
uv run calendar-app reminders

# Get both events and reminders
uv run calendar-app all

# Show JSON schema
uv run calendar-app schema
```

### Command Options

Most subcommands accept these options:

```bash
# Output in JSON format (default is markdown)
uv run calendar-app events --json

# Filter by date range
uv run calendar-app events --from 2024-12-01 --to 2024-12-31

# Filter by specific calendars
uv run calendar-app events --calendars "Work" "Personal"

# Only show all-day events
uv run calendar-app events --all-day-only

# Only show busy events
uv run calendar-app events --busy-only

# Include completed reminders
uv run calendar-app reminders --include-completed
```

## Development

### Using UV with Public PyPI Registry

To ensure UV uses the public PyPI registry rather than any locally configured repositories:

```bash
# Generate a lock file using only PyPI
UV_NO_CONFIG=1 uv lock

# Install dependencies using only PyPI
UV_NO_CONFIG=1 uv install
```

The `UV_NO_CONFIG=1` environment variable tells UV to ignore any system-level configuration and use only the public PyPI registry.

### Running Tests

Run all tests:
```bash
python -m pytest
```

Run tests with coverage report:
```bash
python -m pytest --cov=calendar_app
```

Run specific test file:
```bash
python -m pytest tests/unit/utils/test_date_utils.py
```

Run specific test:
```bash
python -m pytest tests/unit/utils/test_date_utils.py::TestParseDate::test_valid_date
```
