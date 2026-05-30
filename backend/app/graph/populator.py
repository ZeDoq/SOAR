"""
=====  知识图谱填充器  =====

从数据库和知识库中提取数据，填充知识图谱。
与 knowledge_graph.py 分离以避免循环导入。
"""

import logging
from typing import Optional

from .knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


def populate_from_alert(graph: KnowledgeGraph, alert: dict,
                        intel: dict = None, risk: dict = None) -> None:
    """从单条告警及其分析结果填充图谱。"""
    from ..ai.knowledge_base import search as kb_search

    query = alert.get("description", "") + " " + " ".join(alert.get("tags", []))
    techniques = kb_search(query, top_k=3) if query.strip() else None
    graph.ingest_alert(alert, intel=intel, risk=risk, techniques=techniques)


def populate_from_database(graph: KnowledgeGraph) -> int:
    """从数据库重建图谱。返回处理的告警数量。"""
    return graph.ingest_from_database()


def populate_techniques(graph: KnowledgeGraph) -> int:
    """导入所有 ATT&CK 技术节点。返回数量。"""
    return graph.ingest_from_knowledge_base()
