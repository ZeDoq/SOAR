"""Tests for RAG engine, data loader, and knowledge base integration."""

import pytest

from backend.app.ai import rag_engine, knowledge_base


@pytest.fixture(autouse=True)
def _reset_rag(tmp_path, monkeypatch):
    """Reset RAG engine state and use temp ChromaDB path for each test."""
    rag_engine.reset()
    monkeypatch.setenv("CHROMADB_PATH", str(tmp_path / "chromadb"))
    # Reload settings
    from backend.app import settings as settings_mod
    settings_mod.settings = settings_mod.Settings()
    yield
    rag_engine.reset()


class TestRAGEngine:
    def test_add_and_query_documents(self):
        docs = [
            "Brute force attack using password guessing against SSH",
            "DNS tunnel data exfiltration using encoded subdomains",
            "Port scanning with nmap SYN scan technique",
        ]
        metas = [
            {"type": "technique", "technique_id": "T1110"},
            {"type": "technique", "technique_id": "T1048"},
            {"type": "technique", "technique_id": "T1046"},
        ]
        ids = ["t1110", "t1048", "t1046"]

        count = rag_engine.add_documents(docs, metas, ids)
        assert count == 3

        stats = rag_engine.get_collection_stats()
        assert stats["total_documents"] == 3

    def test_query_returns_results(self):
        rag_engine.add_documents(
            ["SSH brute force password attack"],
            [{"type": "technique"}],
            ["test1"],
        )
        results = rag_engine.query("brute force SSH", top_k=1)
        assert len(results) == 1
        assert results[0]["id"] == "test1"
        assert results[0]["distance"] < 1.0

    def test_hybrid_search(self):
        rag_engine.add_documents(
            [
                "Brute force SSH password attack",
                "DNS tunnel exfiltration",
                "Port scan nmap discovery",
            ],
            [
                {"type": "technique", "technique_id": "T1110"},
                {"type": "technique", "technique_id": "T1048"},
                {"type": "technique", "technique_id": "T1046"},
            ],
            ["t1110", "t1048", "t1046"],
        )
        results = rag_engine.hybrid_search("SSH brute force attack", top_k=3)
        assert len(results) > 0
        # SSH brute force should be the top result
        assert results[0]["id"] == "t1110"
        assert "relevance" in results[0]

    def test_query_empty_collection(self):
        results = rag_engine.query("anything", top_k=5)
        assert results == []

    def test_collection_stats_empty(self):
        stats = rag_engine.get_collection_stats()
        assert stats["total_documents"] == 0


class TestAttackDataLoader:
    def test_load_fallback_techniques(self):
        from backend.app.ai.attack_data_loader import _load_fallback_techniques
        count = _load_fallback_techniques()
        assert count >= 12  # At least the 12 fallback techniques

        stats = rag_engine.get_collection_stats()
        assert stats["total_documents"] >= 12

    def test_load_attack_data_skips_if_populated(self):
        from backend.app.ai.attack_data_loader import _load_fallback_techniques, load_attack_data
        _load_fallback_techniques()
        # Should skip since already populated
        count = load_attack_data(force_reload=False)
        assert count >= 12


class TestIncidentCorpus:
    def test_load_incident_corpus(self):
        from backend.app.ai.incident_corpus import load_incident_corpus
        count = load_incident_corpus()
        assert count >= 10  # At least 10 curated incidents

    def test_search_incidents(self):
        from backend.app.ai.incident_corpus import load_incident_corpus
        load_incident_corpus()
        results = rag_engine.hybrid_search(
            "SSH brute force attack", top_k=3, where={"type": "incident"}
        )
        assert len(results) > 0


class TestKnowledgeBase:
    def test_search_keyword_fallback(self):
        """Search should work even without RAG (keyword fallback)."""
        results = knowledge_base.search("brute force password")
        assert len(results) > 0
        # Should find T1110
        ids = [r["id"] for r in results]
        assert "T1110" in ids

    def test_search_rag_enhanced(self):
        """Search should use RAG when available."""
        from backend.app.ai.incident_corpus import load_incident_corpus
        from backend.app.ai.attack_data_loader import _load_fallback_techniques
        _load_fallback_techniques()
        load_incident_corpus()

        results = knowledge_base.search("SSH brute force password attack")
        assert len(results) > 0
        # Results should have RAG source
        sources = [r.get("source") for r in results]
        assert "rag" in sources

    def test_get_context_for_alert(self):
        alert = {"description": "bruteforce attack", "tags": ["auth"]}
        context = knowledge_base.get_context_for_alert(alert)
        assert isinstance(context, str)

    def test_get_context_empty_alert(self):
        alert = {"description": "", "tags": []}
        context = knowledge_base.get_context_for_alert(alert)
        assert context == ""

    def test_get_rich_context(self):
        """Rich context should return techniques and incidents when RAG available."""
        from backend.app.ai.incident_corpus import load_incident_corpus
        from backend.app.ai.attack_data_loader import _load_fallback_techniques
        _load_fallback_techniques()
        load_incident_corpus()

        alert = {"description": "SSH brute force attack", "tags": ["auth", "brute"]}
        ctx = knowledge_base.get_rich_context(alert)

        assert "techniques" in ctx
        assert "incidents" in ctx
        assert "context_text" in ctx
        assert len(ctx["techniques"]) > 0

    def test_get_rich_context_without_rag(self):
        """Should return empty context when RAG unavailable."""
        alert = {"description": "test", "tags": []}
        ctx = knowledge_base.get_rich_context(alert)
        assert ctx["techniques"] == []
        assert ctx["incidents"] == []


class TestKnowledgeAPI:
    def test_search_endpoint(self, client):
        resp = client.get("/knowledge/search", params={"q": "brute force"})
        assert resp.status_code == 200
        assert "results" in resp.json()

    def test_rag_status_endpoint(self, client):
        resp = client.get("/knowledge/rag/status")
        assert resp.status_code == 200
        assert "total_documents" in resp.json()

    def test_rag_reload_endpoint(self, client):
        resp = client.post("/knowledge/rag/reload")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
