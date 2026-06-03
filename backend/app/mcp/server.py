"""MCP Server - exposes security tools via MCP-compatible API.

Provides tool discovery, governed tool execution, and audit logging.
"""

import json
import logging
from typing import Any, Dict, List

from .tool_registry import list_tools, call_tool, get_tool
from .governance import check_permission
from .audit import log_tool_call

logger = logging.getLogger(__name__)


def discover_tools() -> List[dict]:
    """Discover all available MCP tools."""
    return list_tools()


def execute_tool(
    tool_name: str,
    arguments: dict,
    agent_role: str = "supervisor",
) -> Dict[str, Any]:
    """Execute a tool with governance checks and audit logging.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool input arguments
        agent_role: Role of the calling agent (for governance)

    Returns dict with: success, result, error (if any)
    """
    # Check governance
    if not check_permission(agent_role, tool_name):
        error_msg = f"Governance denied: {agent_role} cannot use {tool_name}"
        log_tool_call(agent_role, tool_name, arguments, success=False, error=error_msg)
        return {"success": False, "error": error_msg}

    # Execute tool
    try:
        result = call_tool(tool_name, arguments)
        log_tool_call(agent_role, tool_name, arguments,
                      result=str(result)[:500], success=True)
        return {"success": True, "result": result}
    except KeyError:
        error_msg = f"Tool not found: {tool_name}"
        log_tool_call(agent_role, tool_name, arguments, success=False, error=error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Tool execution failed: {e}"
        log_tool_call(agent_role, tool_name, arguments, success=False, error=error_msg)
        return {"success": False, "error": error_msg}
