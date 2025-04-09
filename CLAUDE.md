# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run calendar app: `uv run calendar-app`
- Run as MCP server: `uv run calendar-app mcp`
- List calendars: `uv run calendar-app calendars`
- JSON schema: `uv run calendar-app schema`
- Format output: Add `--json` flag (default is markdown)
- Run tests: `uv run pytest`
- Run tests with linting: `uv run pytest --black --ruff`

## Code Style Guidelines
- **Imports**: Group standard library imports first, followed by third-party imports
- **Formatting**: Use Black code formatter with 100 character line length
- **Linting**: Use Ruff for code linting
- **Type Hints**: Use Python type hints for function parameters where appropriate
- **Error Handling**: Use try/except blocks with specific exceptions
- **Documentation**: Include docstrings for all functions and classes
- **Naming Conventions**: Use snake_case for functions and variables, PascalCase for classes
- **Template Rendering**: Use Jinja2 for templating with proper context

## Architecture
- Main functionality is organized in the CalendarEventStore class
- MCP server setup is in setup_mcp_server function
- Template rendering uses Jinja2 with CalendarTemplateRenderer classes