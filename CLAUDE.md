# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run script: `python calendar-events.py` or `./calendar-events.py`
- Run as MCP server: `python calendar-events.py --mcp`
- List calendars: `python calendar-events.py --list-calendars`
- JSON schema: `python calendar-events.py --schema`
- Format output: Add `--format markdown` or `--format json` (default)

## Code Style Guidelines
- **Imports**: Group standard library imports first, followed by third-party imports
- **Formatting**: Use 4-space indentation
- **Type Hints**: Use Python type hints for function parameters where appropriate
- **Error Handling**: Use try/except blocks with specific exceptions
- **Documentation**: Include docstrings for all functions and classes
- **Naming Conventions**: Use snake_case for functions and variables, PascalCase for classes
- **Template Rendering**: Use Jinja2 for templating with proper context

## Architecture
- Main functionality is organized in the CalendarEventStore class
- MCP server setup is in setup_mcp_server function
- Template rendering uses Jinja2 with CalendarTemplateRenderer classes