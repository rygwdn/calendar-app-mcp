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

This application is designed to be run with the `uv run` command:

```bash
# Run the app with default options (today's events in JSON format)
uv run calendar-app

# Run as MCP server
uv run calendar-app --mcp

# List all calendars
uv run calendar-app --list-calendars

# View JSON schema
uv run calendar-app --schema

# Output in markdown format
uv run calendar-app --format markdown

# Filter by date range
uv run calendar-app --from 2024-12-01 --to 2024-12-31
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
