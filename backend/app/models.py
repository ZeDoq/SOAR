"""
=====  数据模型定义  =====

定义 API 请求/响应的 Pydantic 数据模型。
Pydantic 负责自动进行数据校验和序列化。
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    """
    告警创建请求模型。

    当安全传感器检测到异常活动时，会生成一个告警对象。
    这是整个 SOAR 工作流的触发点。

    Attributes:
        ip: 触发告警的源 IP 地址
        source: 告警来源（如传感器名称、日志源）
        description: 告警描述信息
        observed_at: 观测时间（ISO 8601 格式）
        tags: 标签列表，用于分类和筛选
    """
    ip: str
    source: str = "local"
    description: str = ""
    observed_at: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class RunRequest(BaseModel):
    """
    剧本执行请求模型。

    用户选择一个告警后，通过此模型触发对该告警的安全响应剧本。

    Attributes:
        alert_id: 要处理的告警 ID，关联到 alerts 表中的记录
    """
    alert_id: int