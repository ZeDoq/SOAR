"""MCP Tool Registry - registers security tools as MCP-compatible tool definitions.

Each tool has: name, description, input_schema, handler function, and required permissions.
"""

import logging
from typing import Callable, Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Tool registry storage
_tools: Dict[str, dict] = {}


def register_tool(
    name: str,
    description: str,
    input_schema: dict,
    handler: Callable,
    category: str = "general",
    permissions: List[str] = None,
) -> None:
    """Register a security tool as an MCP tool definition.

    Args:
        name: Unique tool name (e.g., 'virustotal_lookup')
        description: Human-readable description
        input_schema: JSON Schema for the tool's input parameters
        handler: Async or sync function that executes the tool
        category: Tool category (intel, analysis, response, general)
        permissions: Required permissions to use this tool
    """
    _tools[name] = {
        "name": name,
        "description": description,
        "input_schema": input_schema,
        "handler": handler,
        "category": category,
        "permissions": permissions or [],
    }
    logger.info("Registered MCP tool: %s (%s)", name, category)


def get_tool(name: str) -> Optional[dict]:
    """Get a registered tool by name."""
    return _tools.get(name)


def list_tools() -> List[dict]:
    """List all registered tools (without handler references)."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
            "category": t["category"],
            "permissions": t["permissions"],
        }
        for t in _tools.values()
    ]


def list_tools_by_category(category: str) -> List[dict]:
    """List tools filtered by category."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
            "category": t["category"],
            "permissions": t["permissions"],
        }
        for t in _tools.values()
        if t["category"] == category
    ]


def call_tool(name: str, arguments: dict) -> Any:
    """Execute a registered tool with the given arguments.

    Returns the tool's output. Raises KeyError if tool not found.
    """
    tool = _tools.get(name)
    if not tool:
        raise KeyError(f"Tool not found: {name}")

    handler = tool["handler"]
    return handler(**arguments)


def get_tool_count() -> int:
    """Get the number of registered tools."""
    return len(_tools)


def reset():
    """Clear all registered tools (for testing)."""
    _tools.clear()
