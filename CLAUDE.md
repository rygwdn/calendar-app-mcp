# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run calendar app: `uv run calendar-app` or `uvx calendar-app`
- Run as MCP server: `uv run calendar-app mcp`, `uvx calendar-app-mcp` (no args needed), or `uvx calendar-app-mcp mcp`
- List calendars: `uv run calendar-app calendars` or `uvx calendar-app-mcp calendars`
- JSON schema: `uv run calendar-app schema` or `uvx calendar-app-mcp schema`
- Show version: `uv run calendar-app --version`, `uv run calendar-app version` or `uvx calendar-app-mcp --version`
- Format output: Add `--json` flag (default is markdown)
- Run tests: `uv run pytest`
- Run tests with linting: `uv run pytest --black --ruff`
- Generate lock file with PyPI: `UV_NO_CONFIG=1 uv lock`
- Install dependencies with PyPI: `UV_NO_CONFIG=1 uv install`
- Install in development mode: `UV_NO_CONFIG=1 uv pip install -e .[dev]`
## Publishing Process

To publish a new version to PyPI, follow these steps:

1. Update version number in `pyproject.toml`
2. Run tests to make sure everything works: `uv run pytest --black --ruff`
3. Build the package: `UV_NO_CONFIG=1 uv run python -m build`
4. Upload to PyPI:
   ```bash
   UV_NO_CONFIG=1 uv run twine upload dist/calendar_app_mcp-X.Y.Z*
   ```
   Replace X.Y.Z with the actual version number.
5. Verify installation: `uvx calendar-app-mcp@latest --version`
6. Create and push a tag: `git tag vX.Y.Z && git push origin vX.Y.Z`

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