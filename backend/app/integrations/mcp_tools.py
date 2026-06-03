"""MCP tool wrappers for existing SOAR integrations.

Wraps threat_intel, firewall, recon, knowledge_base, etc.
as MCP-compatible tools with standardized schemas.
"""

from typing import Any


def _virustotal_lookup(ip: str, **kwargs) -> Any:
    from ..integrations import threat_intel
    from .. import settings as settings_mod
    result = threat_intel._lookup_virustotal(ip, settings_mod.settings.virustotal_api_key)
    return result


def _abuseipdb_lookup(ip: str, **kwargs) -> Any:
    from ..integrations import threat_intel
    from .. import settings as settings_mod
    result = threat_intel._lookup_abuseipdb(ip, settings_mod.settings.abuseipdb_api_key)
    return result


def _whois_lookup(ip: str, **kwargs) -> Any:
    from ..integrations import recon
    return recon.whois_lookup(ip)


def _dns_lookup(ip: str, **kwargs) -> Any:
    from ..integrations import recon
    return recon.dns_lookup(ip)


def _firewall_block(ip: str, reason: str = "", **kwargs) -> Any:
    from ..integrations import firewall
    from .. import settings as settings_mod
    risk = {"risk_score": 100, "rationale": reason}
    return firewall.block(ip, risk, settings_mod.settings.simulated_latency_ms)


def _search_knowledge_base(query: str, top_k: int = 5, **kwargs) -> Any:
    from ..ai import knowledge_base
    return knowledge_base.search(query, top_k=top_k)


def _query_knowledge_graph(query: str, **kwargs) -> Any:
    from ..graph.knowledge_graph import graph
    return graph.find_related("ip", query, max_depth=2)


def register_all_tools() -> None:
    """Register all SOAR integration tools with the MCP registry."""
    from .tool_registry import register_tool

    register_tool(
        name="virustotal_lookup",
        description="查询 VirusTotal 获取 IP 信誉评分",
        input_schema={
            "type": "object",
            "properties": {"ip": {"type": "string", "description": "IP 地址"}},
            "required": ["ip"],
        },
        handler=_virustotal_lookup,
        category="intel",
    )

    register_tool(
        name="abuseipdb_lookup",
        description="查询 AbuseIPDB 获取 IP 滥用评分",
        input_schema={
            "type": "object",
            "properties": {"ip": {"type": "string", "description": "IP 地址"}},
            "required": ["ip"],
        },
        handler=_abuseipdb_lookup,
        category="intel",
    )

    register_tool(
        name="whois_lookup",
        description="查询 IP 的 WHOIS 注册信息",
        input_schema={
            "type": "object",
            "properties": {"ip": {"type": "string", "description": "IP 地址"}},
            "required": ["ip"],
        },
        handler=_whois_lookup,
        category="intel",
    )

    register_tool(
        name="dns_lookup",
        description="查询 IP 的 DNS 记录",
        input_schema={
            "type": "object",
            "properties": {"ip": {"type": "string", "description": "IP/域名"}},
            "required": ["ip"],
        },
        handler=_dns_lookup,
        category="intel",
    )

    register_tool(
        name="firewall_block",
        description="封锁指定 IP（需高权限）",
        input_schema={
            "type": "object",
            "properties": {
                "ip": {"type": "string", "description": "要封锁的 IP"},
                "reason": {"type": "string", "description": "封锁原因"},
            },
            "required": ["ip"],
        },
        handler=_firewall_block,
        category="response",
    )

    register_tool(
        name="search_knowledge_base",
        description="搜索 MITRE ATT&CK 安全知识库",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "top_k": {"type": "integer", "description": "返回数量", "default": 5},
            },
            "required": ["query"],
        },
        handler=_search_knowledge_base,
        category="analysis",
    )

    register_tool(
        name="query_knowledge_graph",
        description="查询知识图谱中与 IP 相关的实体",
        input_schema={
            "type": "object",
            "properties": {"ip": {"type": "string", "description": "IP 地址"}},
            "required": ["ip"],
        },
        handler=_query_knowledge_graph,
        category="analysis",
    )
