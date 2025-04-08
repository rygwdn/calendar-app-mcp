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
uvx calendar-app
```

Run as MCP server:
```bash
uvx calendar-app --mcp
```

List all calendars:
```bash
uvx calendar-app --list-calendars
```

View JSON schema:
```bash
uvx calendar-app --schema
```

Output in markdown format:
```bash
uvx calendar-app --format markdown
```

Filter by date range:
```bash
uvx calendar-app --from 2024-12-01 --to 2024-12-31
```
