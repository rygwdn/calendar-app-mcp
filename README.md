# Calendar App MCP

A modern calendar application that integrates with macOS Calendar and provides data through an MCP interface.

## Features

- Access macOS Calendar events and reminders
- Filter by date range, calendar names, and other criteria
- Format output as JSON or Markdown
- Run as an MCP server for Claude integration

## Installation

```bash
# Install uv package manager if not already installed
# https://github.com/astral-sh/uv

# Install the package in development mode
uv install -e .

# Install with development dependencies (for testing)
uv install -e '.[dev]'
```

## Usage

This application is designed to be run with the `uv run` command and uses subcommands for different functionality:

```bash
# Show help and available subcommands
uv run calendar-app

# Get today's events and reminders
uv run calendar-app today

# Get only events
uv run calendar-app events

# Get only reminders
uv run calendar-app reminders

# Get both events and reminders
uv run calendar-app all

# List available calendars
uv run calendar-app calendars

# Show JSON schema
uv run calendar-app schema

# Run as MCP server
uv run calendar-app mcp
```

### Common Options

Most subcommands accept these options:

```bash
# Output in markdown format
uv run calendar-app events --format markdown

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
