"""MCP 工具协议 API 路由（需认证）。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..routes.auth import get_current_user

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/tools")
def list_tools(user: dict = Depends(get_current_user)) -> dict:
    """列出所有已注册的 MCP 工具。"""
    from ..mcp.tool_registry import list_tools as get_tools
    return {"tools": get_tools(), "count": len(get_tools())}


@router.get("/tools/{category}")
def list_tools_by_category(category: str,
                           user: dict = Depends(get_current_user)) -> dict:
    """按类别列出 MCP 工具。"""
    from ..mcp.tool_registry import list_tools_by_category
    return {"tools": list_tools_by_category(category)}


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict = {}
    agent_role: str = "supervisor"


@router.post("/call")
def call_mcp_tool(request: ToolCallRequest,
                  user: dict = Depends(get_current_user)) -> dict:
    """执行一个 MCP 工具（带权限检查和审计日志）。"""
    from ..mcp.server import execute_tool
    result = execute_tool(
        request.tool_name,
        request.arguments,
        agent_role=request.agent_role,
    )
    return result


@router.get("/governance")
def get_governance_matrix(user: dict = Depends(get_current_user)) -> dict:
    """获取 Agent-工具权限矩阵。"""
    from ..mcp.governance import get_permission_matrix, AGENT_ROLES
    return {
        "matrix": get_permission_matrix(),
        "roles": list(AGENT_ROLES.keys()),
    }


@router.get("/audit")
def get_audit_log(agent_role: Optional[str] = None,
                  tool_name: Optional[str] = None,
                  user: dict = Depends(get_current_user)) -> dict:
    """查询 MCP 工具调用审计日志。"""
    from ..mcp.audit import get_audit_log
    return {"audit_log": get_audit_log(agent_role, tool_name)}


@router.get("/audit/stats")
def get_audit_stats(user: dict = Depends(get_current_user)) -> dict:
    """获取审计统计信息。"""
    from ..mcp.audit import get_audit_stats
    return get_audit_stats()
