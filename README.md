# Calendar App MCP

A modern calendar application that integrates with macOS Calendar and provides data through an MCP interface.

## Features

- Access macOS Calendar events and reminders
- Filter by date range, calendar names, and other criteria
- Format output as JSON or Markdown
- Run as an MCP server for Claude integration

## Installation

```bash
uv install .
```

## Usage

Run as standalone script:
```bash
# Using the executable script
./calendar-app

# Using python module
python -m calendar_app.cli

# Using the installed script
calendar-app
```

Run as MCP server:
```bash
./calendar-app --mcp
```

List all calendars:
```bash
./calendar-app --list-calendars
```

View JSON schema:
```bash
./calendar-app --schema
```

Output in markdown format:
```bash
./calendar-app --format markdown
```

Filter by date range:
```bash
./calendar-app --from 2024-12-01 --to 2024-12-31
```
