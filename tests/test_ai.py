"""Tests for AI module (no LLM API key required)."""

import pytest
from fastapi.testclient import TestClient

from backend.app.ai import analyzer, knowledge_base, llm_client, prompts
from backend.app import storage


class TestLLMClient:
    def test_chat_returns_empty_without_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        llm_client._client = None
        result = llm_client.chat("system", "user")
        assert result == ""

    def test_chat_json_returns_none_without_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        llm_client._client = None
        result = llm_client.chat_json("system", "user")
        assert result is None


class TestPrompts:
    def test_analysis_prompt_contains_alert_info(self):
        alert = {"ip": "1.2.3.4", "source": "test", "description": "scan", "tags": ["scan"]}
        intel = {"reputation": "suspicious", "confidence": 0.68, "signal": 45, "sources": []}
        prompt = prompts.build_analysis_prompt(alert, intel)
        assert "1.2.3.4" in prompt
        assert "suspicious" in prompt
        assert "JSON" in prompt

    def test_analysis_prompt_with_context(self):
        alert = {"ip": "1.2.3.4", "source": "test", "description": "test", "tags": []}
        intel = {"reputation": "benign", "confidence": 0.35, "signal": 10, "sources": []}
        prompt = prompts.build_analysis_prompt(alert, intel, context="Similar case found")
        assert "Similar case found" in prompt

    def test_report_prompt_structure(self):
        alert = {"ip": "1.2.3.4", "source": "test", "description": "test", "tags": []}
        intel = {"reputation": "malicious", "confidence": 0.92}
        risk = {"risk_score": 80, "rationale": "high risk"}
        decision = {"action": "block", "detail": {}}
        prompt = prompts.build_report_prompt(alert, intel, risk, decision)
        assert "Markdown" in prompt
        assert "80" in prompt


class TestAnalyzer:
    def test_analyze_returns_none_without_llm(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        llm_client._client = None
        alert = {"ip": "1.2.3.4", "source": "test", "description": "test", "tags": []}
        intel = {"reputation": "benign", "confidence": 0.35, "signal": 10, "sources": []}
        result = analyzer.analyze(alert, intel)
        assert result is None

    def test_compute_ai_risk_score_malicious(self):
        result = analyzer.compute_ai_risk_score({"threat_level": "malicious", "confidence": 0.9})
        assert result >= 80

    def test_compute_ai_risk_score_benign(self):
        result = analyzer.compute_ai_risk_score({"threat_level": "benign", "confidence": 0.8})
        assert result < 40

    def test_compute_ai_risk_score_false_positive(self):
        result = analyzer.compute_ai_risk_score({"threat_level": "false_positive", "confidence": 0.9})
        assert result < 20


class TestKnowledgeBase:
    def test_search_returns_results(self):
        results = knowledge_base.search("brute force password")
        assert isinstance(results, list)

    def test_get_context_for_alert(self):
        alert = {"description": "bruteforce attack", "tags": ["auth"]}
        context = knowledge_base.get_context_for_alert(alert)
        assert isinstance(context, str)

    def test_get_context_empty_alert(self):
        alert = {"description": "", "tags": []}
        context = knowledge_base.get_context_for_alert(alert)
        assert context == ""


class TestKnowledgeAPI:
    def test_search_endpoint(self, client):
        resp = client.get("/knowledge/search", params={"q": "brute force"})
        assert resp.status_code == 200
        assert "results" in resp.json()
