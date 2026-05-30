"""
=====  安全知识图谱  =====

基于 networkx 的内存图结构，用于表示安全实体之间的关联关系。
支持节点/边的增删查改，以及路径查找、聚类检测等高级查询。
"""

import logging
from typing import Any, Dict, List, Optional

from .schema import (
    EDGE_ASSOCIATED_WITH, EDGE_CONNECTED_TO, EDGE_HAS_RISK,
    EDGE_REPORTED_BY, EDGE_RESOLVES_TO, EDGE_USES_TECHNIQUE,
    NODE_ALERT, NODE_DOMAIN, NODE_IP, NODE_RISK_LEVEL, NODE_TECHNIQUE,
    make_node_id,
)

logger = logging.getLogger(__name__)


def _get_nx():
    try:
        import networkx as nx
        return nx
    except ImportError:
        logger.warning("networkx 未安装，知识图谱不可用")
        return None


class KnowledgeGraph:
    """安全知识图谱（基于 networkx 有向图）。"""

    def __init__(self):
        nx = _get_nx()
        self._graph = nx.DiGraph() if nx else None

    @property
    def available(self) -> bool:
        return self._graph is not None

    # ---- 节点管理 ----

    def add_ip_node(self, ip: str, reputation: str = "unknown", signal: int = 0) -> str:
        """添加或更新 IP 节点。返回节点 ID。"""
        nid = make_node_id(NODE_IP, ip)
        self._graph.add_node(nid, node_type=NODE_IP, ip=ip,
                             reputation=reputation, signal=signal)
        return nid

    def add_alert_node(self, alert: dict) -> str:
        """添加告警节点。返回节点 ID。"""
        alert_id = alert.get("id", 0)
        nid = make_node_id(NODE_ALERT, str(alert_id))
        self._graph.add_node(nid, node_type=NODE_ALERT, alert_id=alert_id,
                             description=alert.get("description", ""),
                             source=alert.get("source", ""),
                             observed_at=alert.get("observed_at", ""))
        return nid

    def add_technique_node(self, technique_id: str, name: str, tactic: str) -> str:
        """添加 ATT&CK 技术节点。返回节点 ID。"""
        nid = make_node_id(NODE_TECHNIQUE, technique_id)
        self._graph.add_node(nid, node_type=NODE_TECHNIQUE,
                             technique_id=technique_id, name=name, tactic=tactic)
        return nid

    def add_risk_level_node(self, level: str) -> str:
        """添加风险等级节点（low/medium/high）。返回节点 ID。"""
        nid = make_node_id(NODE_RISK_LEVEL, level)
        ranges = {"low": "0-39", "medium": "40-69", "high": "70-100"}
        self._graph.add_node(nid, node_type=NODE_RISK_LEVEL,
                             level=level, score_range=ranges.get(level, ""))
        return nid

    def add_domain_node(self, domain: str) -> str:
        """添加域名节点。返回节点 ID。"""
        nid = make_node_id(NODE_DOMAIN, domain)
        self._graph.add_node(nid, node_type=NODE_DOMAIN, domain=domain)
        return nid

    def add_edge(self, source_id: str, target_id: str,
                 edge_type: str, **attrs) -> None:
        """添加带类型的边。"""
        self._graph.add_edge(source_id, target_id, edge_type=edge_type, **attrs)

    # ---- 批量填充 ----

    def ingest_alert(self, alert: dict, intel: dict = None,
                     risk: dict = None, techniques: list = None) -> None:
        """将一条告警及其分析结果导入图谱。"""
        alert_nid = self.add_alert_node(alert)
        ip_nid = self.add_ip_node(
            alert.get("ip", "unknown"),
            reputation=intel.get("reputation", "unknown") if intel else "unknown",
            signal=intel.get("signal", 0) if intel else 0,
        )
        self.add_edge(alert_nid, ip_nid, EDGE_ASSOCIATED_WITH)

        self.add_edge(alert_nid,
                      make_node_id(NODE_REPORTED_BY := "source", alert.get("source", "unknown")),
                      EDGE_REPORTED_BY)

        if risk:
            score = risk.get("risk_score", 0)
            if score >= 70:
                level = "high"
            elif score >= 40:
                level = "medium"
            else:
                level = "low"
            risk_nid = self.add_risk_level_node(level)
            self.add_edge(alert_nid, risk_nid, EDGE_HAS_RISK, score=score)

        if techniques:
            for tech in techniques:
                tech_nid = self.add_technique_node(
                    tech.get("id", ""), tech.get("name", ""), tech.get("tactic", ""))
                self.add_edge(alert_nid, tech_nid, EDGE_USES_TECHNIQUE,
                              relevance=tech.get("relevance", 0))

    def ingest_from_database(self) -> int:
        """从数据库重建图谱。返回处理的告警数量。"""
        from .. import storage
        from ..ai.knowledge_base import search as kb_search

        alerts = storage.list_alerts()
        for alert in alerts:
            techniques = kb_search(
                alert.get("description", "") + " " + " ".join(alert.get("tags", [])),
                top_k=3,
            )
            self.ingest_alert(alert, techniques=techniques)

        self._connect_shared_techniques()
        logger.info("知识图谱已从 %d 条告警重建", len(alerts))
        return len(alerts)

    def ingest_from_knowledge_base(self) -> int:
        """导入所有 ATT&CK 技术节点。返回数量。"""
        from ..ai.knowledge_base import ATTACK_KNOWLEDGE
        for tech in ATTACK_KNOWLEDGE:
            self.add_technique_node(tech["id"], tech["name"], tech["tactic"])
        return len(ATTACK_KNOWLEDGE)

    def _connect_shared_techniques(self) -> None:
        """连接共享相同技术的 IP 节点。"""
        nx = _get_nx()
        if not nx:
            return

        # 找到所有 IP -> technique 的边
        ip_techniques: Dict[str, set] = {}
        for u, v, data in self._graph.edges(data=True):
            if data.get("edge_type") == EDGE_ASSOCIATED_WITH:
                # u=alert, v=ip
                ip_id = v
            else:
                continue
            # 找到该 alert 关联的 technique
            for _, t, tdata in self._graph.edges(u, data=True):
                if tdata.get("edge_type") == EDGE_USES_TECHNIQUE:
                    if ip_id not in ip_techniques:
                        ip_techniques[ip_id] = set()
                    ip_techniques[ip_id].add(t)

        # 共享技术的 IP 之间建立连接
        ip_ids = list(ip_techniques.keys())
        for i in range(len(ip_ids)):
            for j in range(i + 1, len(ip_ids)):
                shared = ip_techniques[ip_ids[i]] & ip_techniques[ip_ids[j]]
                if shared:
                    self.add_edge(ip_ids[i], ip_ids[j], EDGE_CONNECTED_TO,
                                  shared_techniques=list(shared))

    # ---- 查询 ----

    def find_related(self, node_type: str, node_id: str,
                     max_depth: int = 2) -> List[Dict[str, Any]]:
        """查找给定节点 max_depth 跳内的所有关联实体。"""
        nx = _get_nx()
        if not nx:
            return []

        full_id = make_node_id(node_type, node_id)
        if full_id not in self._graph:
            return []

        results = []
        visited = set()
        queue = [(full_id, 0)]

        while queue:
            current, depth = queue.pop(0)
            if current in visited or depth > max_depth:
                continue
            visited.add(current)

            if current != full_id:
                attrs = dict(self._graph.nodes[current])
                results.append({
                    "node_id": current,
                    "node_type": attrs.get("node_type", "unknown"),
                    "attrs": attrs,
                    "depth": depth,
                })

            if depth < max_depth:
                for neighbor in self._graph.neighbors(current):
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))
                for neighbor in self._graph.predecessors(current):
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))

        return results

    def shortest_path(self, source_ip: str, target_ip: str) -> Optional[List[str]]:
        """查找两个 IP 之间的最短路径。"""
        nx = _get_nx()
        if not nx:
            return None

        src = make_node_id(NODE_IP, source_ip)
        tgt = make_node_id(NODE_IP, target_ip)

        try:
            path = nx.shortest_path(self._graph, src, tgt)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def detect_clusters(self, min_cluster_size: int = 2) -> List[List[str]]:
        """检测通过共享技术关联的 IP 聚类。"""
        nx = _get_nx()
        if not nx:
            return []

        # 提取 IP 子图
        ip_nodes = [n for n, d in self._graph.nodes(data=True)
                    if d.get("node_type") == NODE_IP]
        ip_subgraph = self._graph.subgraph(ip_nodes).to_undirected()

        clusters = []
        for component in nx.connected_components(ip_subgraph):
            if len(component) >= min_cluster_size:
                ips = [n.split(":", 1)[1] for n in component]
                clusters.append(ips)

        return clusters

    def get_technique_frequency(self) -> List[Dict[str, Any]]:
        """获取各 ATT&CK 技术的使用频率。"""
        counts: Dict[str, int] = {}
        names: Dict[str, str] = {}

        for u, v, data in self._graph.edges(data=True):
            if data.get("edge_type") == EDGE_USES_TECHNIQUE:
                tech_id = v.split(":", 1)[1] if ":" in v else v
                counts[tech_id] = counts.get(tech_id, 0) + 1
                node_data = self._graph.nodes[v]
                names[tech_id] = node_data.get("name", tech_id)

        result = [{"technique_id": tid, "name": names.get(tid, tid), "count": c}
                  for tid, c in counts.items()]
        return sorted(result, key=lambda x: x["count"], reverse=True)

    def get_ip_neighbors(self, ip: str) -> Dict[str, List[str]]:
        """获取 IP 节点的所有邻居，按关系类型分组。"""
        nid = make_node_id(NODE_IP, ip)
        if nid not in self._graph:
            return {"associated_alerts": [], "connected_ips": [], "techniques": []}

        result: Dict[str, List[str]] = {
            "associated_alerts": [],
            "connected_ips": [],
            "techniques": [],
        }

        for _, v, data in self._graph.edges(nid, data=True):
            etype = data.get("edge_type")
            if etype == EDGE_CONNECTED_TO:
                result["connected_ips"].append(v.split(":", 1)[1])

        for u, _, data in self._graph.in_edges(nid, data=True):
            etype = data.get("edge_type")
            if etype == EDGE_ASSOCIATED_WITH:
                result["associated_alerts"].append(u.split(":", 1)[1])

        # 通过关联告警找技术
        for alert_nid in result["associated_alerts"]:
            alert_full = make_node_id(NODE_ALERT, alert_nid)
            if alert_full in self._graph:
                for _, t, tdata in self._graph.edges(alert_full, data=True):
                    if tdata.get("edge_type") == EDGE_USES_TECHNIQUE:
                        tech_id = t.split(":", 1)[1]
                        if tech_id not in result["techniques"]:
                            result["techniques"].append(tech_id)

        return result

    def to_json(self) -> dict:
        """序列化图为 JSON（用于 API 响应）。"""
        nodes = []
        for nid, attrs in self._graph.nodes(data=True):
            nodes.append({"id": nid, **attrs})

        edges = []
        for u, v, attrs in self._graph.edges(data=True):
            edges.append({"source": u, "target": v, **attrs})

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": self._graph.number_of_nodes(),
                "edge_count": self._graph.number_of_edges(),
            },
        }

    def clear(self) -> None:
        """清空图谱。"""
        if self._graph:
            self._graph.clear()


# 模块级单例
graph = KnowledgeGraph()
