from backend.app.graph.knowledge_graph import KnowledgeGraph
from backend.app.graph.schema import (
    NODE_IP, NODE_ALERT, NODE_TECHNIQUE, NODE_RISK_LEVEL,
    EDGE_ASSOCIATED_WITH, EDGE_USES_TECHNIQUE, EDGE_HAS_RISK,
    make_node_id,
)


class TestKnowledgeGraph:
    def _make_graph(self):
        return KnowledgeGraph()

    def test_available(self):
        g = self._make_graph()
        assert g.available is True

    def test_add_ip_node(self):
        g = self._make_graph()
        nid = g.add_ip_node("1.2.3.4", reputation="malicious", signal=90)
        assert nid == "ip:1.2.3.4"
        assert g._graph.nodes[nid]["reputation"] == "malicious"

    def test_add_alert_node(self):
        g = self._make_graph()
        alert = {"id": 42, "description": "test", "source": "sensor", "observed_at": "2024-01-01"}
        nid = g.add_alert_node(alert)
        assert nid == "alert:42"
        assert g._graph.nodes[nid]["description"] == "test"

    def test_add_technique_node(self):
        g = self._make_graph()
        nid = g.add_technique_node("T1110", "Brute Force", "credential-access")
        assert nid == "technique:T1110"
        assert g._graph.nodes[nid]["name"] == "Brute Force"

    def test_add_risk_level_node(self):
        g = self._make_graph()
        nid = g.add_risk_level_node("high")
        assert nid == "risk_level:high"
        assert g._graph.nodes[nid]["score_range"] == "70-100"

    def test_add_edge(self):
        g = self._make_graph()
        g.add_ip_node("1.2.3.4")
        g.add_alert_node({"id": 1})
        g.add_edge("alert:1", "ip:1.2.3.4", EDGE_ASSOCIATED_WITH)
        assert g._graph.has_edge("alert:1", "ip:1.2.3.4")

    def test_ingest_alert(self):
        g = self._make_graph()
        alert = {"id": 1, "ip": "10.0.0.1", "description": "test", "source": "sensor"}
        intel = {"reputation": "malicious", "signal": 80}
        risk = {"risk_score": 85}
        techniques = [{"id": "T1110", "name": "Brute Force", "tactic": "credential-access"}]

        g.ingest_alert(alert, intel=intel, risk=risk, techniques=techniques)

        assert g._graph.has_node("alert:1")
        assert g._graph.has_node("ip:10.0.0.1")
        assert g._graph.has_node("risk_level:high")
        assert g._graph.has_node("technique:T1110")
        assert g._graph.has_edge("alert:1", "ip:10.0.0.1")

    def test_to_json(self):
        g = self._make_graph()
        g.add_ip_node("1.2.3.4")
        g.add_alert_node({"id": 1})
        g.add_edge("alert:1", "ip:1.2.3.4", EDGE_ASSOCIATED_WITH)

        data = g.to_json()
        assert data["stats"]["node_count"] == 2
        assert data["stats"]["edge_count"] == 1
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_clear(self):
        g = self._make_graph()
        g.add_ip_node("1.2.3.4")
        g.clear()
        assert g._graph.number_of_nodes() == 0

    def test_find_related(self):
        g = self._make_graph()
        g.add_ip_node("1.2.3.4")
        g.add_alert_node({"id": 1})
        g.add_edge("alert:1", "ip:1.2.3.4", EDGE_ASSOCIATED_WITH)

        related = g.find_related("ip", "1.2.3.4")
        assert len(related) >= 1
        assert any(r["node_id"] == "alert:1" for r in related)

    def test_find_related_not_found(self):
        g = self._make_graph()
        related = g.find_related("ip", "99.99.99.99")
        assert related == []

    def test_shortest_path(self):
        g = self._make_graph()
        g.add_ip_node("1.1.1.1")
        g.add_ip_node("2.2.2.2")
        g.add_alert_node({"id": 1})
        g.add_edge("ip:1.1.1.1", "alert:1", EDGE_ASSOCIATED_WITH)
        g.add_edge("alert:1", "ip:2.2.2.2", EDGE_ASSOCIATED_WITH)

        path = g.shortest_path("1.1.1.1", "2.2.2.2")
        assert path is not None
        assert len(path) == 3  # ip1 -> alert -> ip2

    def test_shortest_path_no_path(self):
        g = self._make_graph()
        g.add_ip_node("1.1.1.1")
        g.add_ip_node("2.2.2.2")
        path = g.shortest_path("1.1.1.1", "2.2.2.2")
        assert path is None

    def test_get_technique_frequency(self):
        g = self._make_graph()
        g.add_alert_node({"id": 1})
        g.add_alert_node({"id": 2})
        g.add_technique_node("T1110", "Brute Force", "credential-access")
        g.add_edge("alert:1", "technique:T1110", EDGE_USES_TECHNIQUE)
        g.add_edge("alert:2", "technique:T1110", EDGE_USES_TECHNIQUE)

        freq = g.get_technique_frequency()
        assert len(freq) == 1
        assert freq[0]["count"] == 2

    def test_get_ip_neighbors(self):
        g = self._make_graph()
        g.add_ip_node("1.2.3.4")
        g.add_alert_node({"id": 1})
        g.add_edge("alert:1", "ip:1.2.3.4", EDGE_ASSOCIATED_WITH)

        neighbors = g.get_ip_neighbors("1.2.3.4")
        assert "1" in neighbors["associated_alerts"]

    def test_detect_clusters(self):
        g = self._make_graph()
        g.add_ip_node("1.1.1.1")
        g.add_ip_node("2.2.2.2")
        g.add_edge("ip:1.1.1.1", "ip:2.2.2.2", "connected_to")
        clusters = g.detect_clusters(min_cluster_size=2)
        assert len(clusters) == 1

    def test_ingest_from_knowledge_base(self):
        g = self._make_graph()
        count = g.ingest_from_knowledge_base()
        assert count == 12  # 12 ATT&CK techniques
        assert g._graph.has_node("technique:T1110")
