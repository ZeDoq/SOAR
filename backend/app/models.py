"""
数据模型定义 — 含输入校验。
"""

import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class AlertCreate(BaseModel):
    """告警创建请求（含 IP 格式校验）。"""
    ip: str
    source: str = "local"
    description: str = ""
    observed_at: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("IP 不能为空")
        if len(v) > 255:
            raise ValueError("IP 长度过长")
        # 允许 IPv4、IPv6、域名格式
        ipv4_re = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        if ipv4_re.match(v):
            parts = v.split(".")
            for p in parts:
                if int(p) > 255:
                    raise ValueError(f"无效的 IPv4 地址: {v}")
            return v
        # IPv6 简单校验
        if ":" in v and len(v) <= 45:
            return v
        # 域名格式
        domain_re = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$")
        if domain_re.match(v) and len(v) <= 253:
            return v
        raise ValueError(f"无效的 IP 地址或域名: {v}")

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        v = v.strip()
        if len(v) > 100:
            raise ValueError("来源名称过长")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if len(v) > 2000:
            return v[:2000]
        return v


class RunRequest(BaseModel):
    """剧本执行请求。"""
    alert_id: int
    mode: str = "classic"
