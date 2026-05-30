"""
=====  Agent 基类  =====

所有专业化 Agent 的抽象基类。
"""

import logging
from abc import ABC, abstractmethod

from .context import AgentContext


class BaseAgent(ABC):
    """Agent 抽象基类，定义统一的分析接口。"""

    name: str = "base"

    def __init__(self):
        self.logger = logging.getLogger(f"agent.{self.name}")

    @abstractmethod
    def analyze(self, ctx: AgentContext) -> AgentContext:
        """执行本 Agent 的职责，修改并返回上下文。"""
        ...

    def _log_decision(self, ctx: AgentContext, message: str, data: dict = None) -> None:
        """同时写入 Python 日志和上下文日志。"""
        self.logger.info("[%s] %s", self.name, message)
        ctx.log(self.name, message, data)
