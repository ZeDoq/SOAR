"""MCP Audit - tracks all tool calls for transparency and accountability."""

import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

from .. import storage

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_tool_call(
    agent_role: str,
    tool_name: str,
    arguments: dict,
    result: str = "",
    success: bool = True,
    error: str = "",
) -> int:
    """Log an MCP tool call to the audit trail.

    Returns the audit record ID.
    """
    conn = storage._connect()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO mcp_audit_log
           (agent_role, tool_name, arguments, result, success, error, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            agent_role,
            tool_name,
            json.dumps(arguments, ensure_ascii=False, default=str)[:2000],
            str(result)[:2000] if result else "",
            1 if success else 0,
            error[:1000] if error else "",
            _utc_now(),
        ),
    )
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id


def get_audit_log(
    agent_role: Optional[str] = None,
    tool_name: Optional[str] = None,
    limit: int = 50,
) -> List[dict]:
    """Query the audit log with optional filters."""
    conn = storage._connect()
    cursor = conn.cursor()

    conditions = []
    params = []
    if agent_role:
        conditions.append("agent_role = ?")
        params.append(agent_role)
    if tool_name:
        conditions.append("tool_name = ?")
        params.append(tool_name)

    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    params.append(limit)

    rows = cursor.execute(
        f"SELECT * FROM mcp_audit_log{where} ORDER BY id DESC LIMIT ?",
        params,
    ).fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "agent_role": row["agent_role"],
            "tool_name": row["tool_name"],
            "arguments": json.loads(row["arguments"]) if row["arguments"] else {},
            "success": bool(row["success"]),
            "error": row["error"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def get_audit_stats() -> dict:
    """Get audit log statistics."""
    conn = storage._connect()
    cursor = conn.cursor()
    total = cursor.execute("SELECT COUNT(*) FROM mcp_audit_log").fetchone()[0]

    by_tool = {}
    for row in cursor.execute(
        "SELECT tool_name, COUNT(*) as cnt FROM mcp_audit_log GROUP BY tool_name"
    ).fetchall():
        by_tool[row["tool_name"]] = row["cnt"]

    denied = cursor.execute(
        "SELECT COUNT(*) FROM mcp_audit_log WHERE success = 0"
    ).fetchone()[0]

    conn.close()
    return {
        "total_calls": total,
        "by_tool": by_tool,
        "denied_calls": denied,
    }
