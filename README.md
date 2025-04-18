# Calendar App MCP

An MCP (Model Context Protocol) server that provides access to macOS Calendar.app events and reminders for use with Claude and other AI assistants.

## MCP Integration

This package can be run as an MCP server to integrate with Claude and other AI assistants supporting the MCP protocol, enabling them to access and interact with your macOS calendar data.

```bash
# Run as MCP server for AI assistant integration
uvx calendar-app-mcp   # Automatically runs as MCP server with no arguments
uvx calendar-app-mcp mcp   # Explicitly runs the MCP server
```

Once running, Claude can interact with your calendar data through the MCP protocol, allowing it to:
- Check your upcoming events
- Find free time slots
- View event details
- Access reminders
- Filter events by calendar, date range, and more

### MCP Tools and Resources

This package provides several MCP tools and resources:

#### Tools
- `get_events`: Retrieve events for a specific date range
- `get_reminders`: Retrieve reminders for a specific date range
- `list_calendars`: List all available calendars
- `get_today_summary`: Get a summary of today's events and reminders
- `search`: Search for events and reminders containing a specific term
- `get_current_time`: Get the current date and time in any timezone
- `convert_time`: Convert a time from one timezone to another
- `list_timezones`: List available timezones, optionally filtered by region

#### Resources
- `calendar://events/{date}`: Access events for a specific date
- `calendar://calendars`: Access the list of available calendars
- `datetime://current/{timezone}`: Get the current time in a specific timezone

#### Prompts
- `daily_agenda`: Generate a prompt for reviewing your daily schedule

## Features

- Access macOS Calendar.app events and reminders
- Filter by date range, calendar names, and all-day/busy status
- Format output as JSON or Markdown
- Secure, local access to calendar data

## Installation

```bash
# Install from PyPI
pip install calendar-app-mcp

# Using uv
uv pip install calendar-app-mcp

# Using uvx (direct execution without installation)
uvx calendar-app-mcp calendars
uvx calendar-app-mcp mcp
```

### Available Command Names

After installation, the package provides two command-line executables:

```bash
# General-purpose calendar app tool - shows help when run without arguments
calendar-app

# MCP-focused variant - defaults to running the MCP server when no arguments are provided
calendar-app-mcp
```

Both commands support the same subcommands, but `calendar-app-mcp` is optimized for use as an MCP server.

### Development Installation

```bash
# Clone the repository
git clone https://github.com/rygwdn/calendar-app-mcp.git
cd calendar-app-mcp

# Install uv package manager if not already installed
# https://github.com/astral-sh/uv

# Install the package in development mode
uv install -e .

# Install with development dependencies (for testing)
uv install -e '.[dev]'
```

## CLI Usage

In addition to functioning as an MCP server, this package can be used as a command-line tool to access calendar data directly:

```bash
# List available calendars
uvx calendar-app-mcp calendars

# Get today's events and reminders
uvx calendar-app-mcp today

# Get only events
uvx calendar-app-mcp events

# Get only reminders
uvx calendar-app-mcp reminders

# Get both events and reminders
uvx calendar-app-mcp all

# Show JSON schema
uvx calendar-app-mcp schema

# Check version
uvx calendar-app-mcp --version
# or 
uvx calendar-app-mcp version
```

### Command Options

Most subcommands accept these options:

```bash
# Output in JSON format (default is markdown)
uvx calendar-app-mcp events --json

# Filter by date range
uvx calendar-app-mcp events --from 2024-12-01 --to 2024-12-31

# Filter by specific calendars
uvx calendar-app-mcp events --calendars "Work" "Personal"

# Only show all-day events
uvx calendar-app-mcp events --all-day-only

# Only show busy events
uvx calendar-app-mcp events --busy-only

# Include completed reminders
uvx calendar-app-mcp reminders --include-completed
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
