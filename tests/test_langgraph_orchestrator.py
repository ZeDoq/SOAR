"""Tests for LangGraph-based dynamic orchestrator."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.agents.langgraph_orchestrator import (
    get_compiled_graph,
    get_graph_mermaid,
    execute_langgraph_playbook,
)
from backend.app.agents.nodes.supervisor import (
    route_after_gather,
    route_after_analysis,
    synthesize_decision,
)
from backend.app.agents.state import SOARState
from backend.app import storage


def _make_state(**overrides) -> SOARState:
    """Create a test state with sensible defaults."""
    state: SOARState = {
        "run_id": 1,
        "alert": {"ip": "1.2.3.4", "source": "test", "description": "test alert", "tags": []},
        "intel": None,
        "recon_result": None,
        "risk": None,
        "ai_result": None,
        "confidence": 0.0,
        "decision": None,
        "report": None,
        "iteration_count": 0,
        "max_iterations": 3,
        "execution_path": [],
        "step_ids": {},
    }
    state.update(overrides)
    return state


class TestSupervisorRouting:
    def test_route_malicious_high_confidence_fast_track(self):
        state = _make_state(intel={
            "reputation": "malicious",
            "confidence": 0.95,
            "signal": 90,
            "sources": ["virustotal"],
        })
        assert route_after_gather(state) == "fast_response"

    def test_route_benign_high_confidence_fast_track(self):
        state = _make_state(intel={
            "reputation": "benign",
            "confidence": 0.90,
            "signal": 5,
            "sources": ["abuseipdb"],
        })
        assert route_after_gather(state) == "fast_response"

    def test_route_suspicious_goes_to_analyze(self):
        state = _make_state(intel={
            "reputation": "suspicious",
            "confidence": 0.6,
            "signal": 45,
            "sources": [],
        })
        assert route_after_gather(state) == "analyze"

    def test_route_low_confidence_unknown_goes_to_analyze(self):
        state = _make_state(intel={
            "reputation": "unknown",
            "confidence": 0.3,
            "signal": 0,
            "sources": [],
        })
        assert route_after_gather(state) == "analyze"

    def test_route_after_analysis_high_confidence_respond(self):
        state = _make_state(confidence=0.85)
        assert route_after_analysis(state) == "respond"

    def test_route_after_analysis_low_confidence_deepen(self):
        state = _make_state(confidence=0.3, iteration_count=0, max_iterations=3)
        assert route_after_analysis(state) == "deepen"

    def test_route_after_analysis_low_confidence_max_iterations_respond(self):
        state = _make_state(confidence=0.3, iteration_count=3, max_iterations=3)
        assert route_after_analysis(state) == "respond"

    def test_route_after_analysis_medium_confidence_respond(self):
        state = _make_state(confidence=0.6, iteration_count=0, max_iterations=3)
        assert route_after_analysis(state) == "respond"


class TestSynthesizeDecision:
    def test_synthesize_malicious(self):
        state = _make_state(intel={
            "reputation": "malicious",
            "confidence": 0.9,
            "signal": 85,
            "sources": ["vt"],
        })
        result = synthesize_decision(state)
        assert result["risk"]["risk_score"] >= 80
        assert result["confidence"] == 0.9
        assert "synthesize_decision" in result["execution_path"]

    def test_synthesize_benign(self):
        state = _make_state(intel={
            "reputation": "benign",
            "confidence": 0.85,
            "signal": 5,
            "sources": [],
        })
        result = synthesize_decision(state)
        assert result["risk"]["risk_score"] <= 20


class TestLangGraphOrchestrator:
    def test_graph_compiles(self):
        graph = get_compiled_graph()
        assert graph is not None

    def test_graph_mermaid_export(self):
        mermaid = get_graph_mermaid()
        assert isinstance(mermaid, str)
        assert len(mermaid) > 0

    def test_fast_track_execution(self, client):
        """Test that a high-confidence malicious alert takes the fast path."""
        # Create an alert
        resp = client.post("/alerts", json={
            "ip": "10.0.0.1",
            "source": "test",
            "description": "known malicious IP",
            "tags": ["malicious"],
        })
        alert_id = resp.json()["alert"]["id"]

        # Start langgraph run
        with patch("backend.app.integrations.threat_intel.lookup") as mock_intel, \
             patch("backend.app.integrations.firewall.block") as mock_block, \
             patch("backend.app.integrations.notify_slack.send_slack_alert") as mock_slack, \
             patch("backend.app.integrations.notify_email.send_alert_email") as mock_email:

            mock_intel.return_value = {
                "reputation": "malicious",
                "confidence": 0.95,
                "signal": 90,
                "sources": ["virustotal"],
            }
            mock_block.return_value = {"status": "blocked", "ticket": "test-123"}
            mock_slack.return_value = None
            mock_email.return_value = None

            resp = client.post("/runs", json={
                "alert_id": alert_id,
                "mode": "langgraph",
            })
            assert resp.status_code == 200
            run_id = resp.json()["run"]["id"]

            # Wait for completion (poll)
            import time
            for _ in range(20):
                time.sleep(0.5)
                detail = client.get(f"/runs/{run_id}")
                if detail.json()["run"]["status"] in ("completed", "failed"):
                    break

            run_data = detail.json()
            assert run_data["run"]["status"] == "completed"

            decision = run_data["run"]["decision"]
            assert decision.get("orchestrator") == "langgraph"
            assert "execution_path" in decision

    def test_langgraph_graph_endpoint(self, client):
        """Test the graph structure endpoint."""
        resp = client.get("/runs/langgraph/graph")
        assert resp.status_code == 200
        assert "mermaid" in resp.json()
