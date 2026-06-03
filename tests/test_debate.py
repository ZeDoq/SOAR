"""Tests for multi-agent debate system."""

import pytest

from backend.app.agents.debate.personas import PERSONAS, VERDICT_SEVERITY
from backend.app.agents.debate.consensus import compute_consensus


class TestPersonas:
    def test_all_personas_defined(self):
        assert "threat_hunter" in PERSONAS
        assert "skeptic" in PERSONAS
        assert "context_specialist" in PERSONAS

    def test_persona_has_required_fields(self):
        for key, persona in PERSONAS.items():
            assert "name" in persona, f"{key} missing name"
            assert "system_prompt" in persona, f"{key} missing system_prompt"
            assert "icon" in persona, f"{key} missing icon"
            assert "color" in persona, f"{key} missing color"

    def test_verdict_severity_ordering(self):
        assert VERDICT_SEVERITY["malicious"] > VERDICT_SEVERITY["suspicious"]
        assert VERDICT_SEVERITY["suspicious"] > VERDICT_SEVERITY["benign"]
        assert VERDICT_SEVERITY["benign"] > VERDICT_SEVERITY["false_positive"]


class TestConsensus:
    def test_unanimous_malicious(self):
        verdicts = [
            {"agent_name": "威胁猎人", "verdict": "malicious", "confidence": 0.9},
            {"agent_name": "怀疑分析师", "verdict": "malicious", "confidence": 0.8},
            {"agent_name": "上下文专家", "verdict": "malicious", "confidence": 0.85},
        ]
        result = compute_consensus(verdicts)
        assert result["is_unanimous"] is True
        assert result["consensus_verdict"] == "malicious"
        assert result["agreement_score"] == 1.0
        assert result["needs_human_review"] is False
        assert len(result["disagreements"]) == 0

    def test_split_verdict(self):
        verdicts = [
            {"agent_name": "威胁猎人", "verdict": "malicious", "confidence": 0.9},
            {"agent_name": "怀疑分析师", "verdict": "benign", "confidence": 0.7},
            {"agent_name": "上下文专家", "verdict": "suspicious", "confidence": 0.6},
        ]
        result = compute_consensus(verdicts)
        assert result["is_unanimous"] is False
        assert result["agreement_score"] < 1.0
        # malicious vs benign = severity spread 4 - 1 = 3
        assert result["needs_human_review"] is True

    def test_two_agree_one_disagrees(self):
        verdicts = [
            {"agent_name": "威胁猎人", "verdict": "suspicious", "confidence": 0.7},
            {"agent_name": "怀疑分析师", "verdict": "suspicious", "confidence": 0.65},
            {"agent_name": "上下文专家", "verdict": "benign", "confidence": 0.8},
        ]
        result = compute_consensus(verdicts)
        assert result["consensus_verdict"] == "suspicious"
        assert result["agreement_score"] == pytest.approx(2 / 3, abs=0.01)
        assert len(result["disagreements"]) == 1
        assert result["disagreements"][0]["agent"] == "上下文专家"

    def test_empty_verdicts(self):
        result = compute_consensus([])
        assert result["consensus_verdict"] == "unknown"
        assert result["needs_human_review"] is True

    def test_single_verdict(self):
        verdicts = [
            {"agent_name": "威胁猎人", "verdict": "malicious", "confidence": 0.9},
        ]
        result = compute_consensus(verdicts)
        assert result["is_unanimous"] is True
        assert result["consensus_verdict"] == "malicious"


class TestDebateAPI:
    def test_list_debates_empty(self, client):
        resp = client.get("/debates")
        assert resp.status_code == 200
        assert resp.json()["debates"] == []

    def test_run_debate_endpoint(self, client):
        """Test debate execution via API (without LLM)."""
        from unittest.mock import patch

        # Create alert
        resp = client.post("/alerts", json={
            "ip": "192.168.1.100",
            "source": "test",
            "description": "suspicious activity",
            "tags": ["scan"],
        })
        alert_id = resp.json()["alert"]["id"]

        # Run debate with mocked LLM
        with patch("backend.app.agents.debate.debate_engine.chat_json") as mock_llm, \
             patch("backend.app.agents.debate.moderator.chat_json") as mock_mod:

            # Each persona returns a verdict
            mock_llm.side_effect = [
                {"verdict": "suspicious", "confidence": 0.7, "reasoning": "可疑扫描"},
                {"verdict": "benign", "confidence": 0.6, "reasoning": "可能是合法扫描"},
                {"verdict": "suspicious", "confidence": 0.65, "reasoning": "需要关注"},
                # Round 2
                {"verdict": "suspicious", "confidence": 0.75, "reasoning": "维持判断"},
                {"verdict": "suspicious", "confidence": 0.6, "reasoning": "被说服"},
                {"verdict": "suspicious", "confidence": 0.7, "reasoning": "维持判断"},
            ]
            mock_mod.return_value = {
                "final_verdict": "suspicious",
                "final_confidence": 0.7,
                "final_reasoning": "多数认为可疑",
            }

            resp = client.post(f"/debates/run/{alert_id}")
            assert resp.status_code == 200
            debate = resp.json()["debate"]
            assert len(debate["rounds"]) == 2
            assert debate["consensus"]["consensus_verdict"] == "suspicious"
