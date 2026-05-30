"""
=====  Agent 共享上下文  =====

在多个 Agent 之间传递数据和决策日志。
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class AgentContext:
    """Agent 协作时的共享上下文对象。"""

    def __init__(self, alert: dict, run_id: int):
        self.alert: dict = alert
        self.run_id: int = run_id
        self.intel: Optional[dict] = None
        self.risk: Optional[dict] = None
        self.ai_result: Optional[dict] = None
        self.recon_result: Optional[dict] = None
        self.decision: Optional[dict] = None
        self.report: Optional[str] = None
        self.agent_logs: List[dict] = []

    def log(self, agent_name: str, message: str, data: dict = None) -> None:
        """记录一条 Agent 决策日志。"""
        entry = {
            "agent": agent_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if data:
            entry["data"] = data
        self.agent_logs.append(entry)

    def to_dict(self) -> dict:
        """序列化上下文（用于存储/调试）。"""
        return {
            "alert": self.alert,
            "run_id": self.run_id,
            "intel": self.intel,
            "risk": self.risk,
            "ai_result": self.ai_result,
            "recon_result": self.recon_result,
            "decision": self.decision,
            "report": self.report,
            "agent_logs": self.agent_logs,
        }
