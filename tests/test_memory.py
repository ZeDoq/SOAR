"""Tests for agent memory and feedback loop system."""

import pytest

from backend.app.memory.episodic_memory import store_episode, search_similar_incidents, get_episode_stats
from backend.app.memory.feedback_loop import submit_feedback, get_feedback_for_run, get_feedback_stats


class TestEpisodicMemory:
    def test_store_episode(self):
        from backend.app import storage
        storage.init_db()

        alert = {"id": 1, "ip": "1.2.3.4", "description": "brute force", "tags": ["auth"]}
        episode_id = store_episode(
            alert=alert, run_id=1, verdict="malicious",
            confidence=0.9, risk_score=85, reasoning="clear brute force pattern",
        )
        assert episode_id > 0

    def test_search_similar(self):
        from backend.app import storage
        storage.init_db()

        # Store some episodes
        for i, (desc, verdict) in enumerate([
            ("SSH brute force attack", "malicious"),
            ("DNS tunnel exfiltration", "suspicious"),
            ("Port scan from internal scanner", "false_positive"),
        ]):
            alert = {"id": i + 1, "ip": f"10.0.0.{i}", "description": desc, "tags": []}
            store_episode(alert=alert, run_id=i + 1, verdict=verdict,
                          confidence=0.8, risk_score=70)

        # Search for similar to brute force (use IP match as fallback)
        alert = {"ip": "10.0.0.0", "description": "SSH login attempt", "tags": ["auth"]}
        results = search_similar_incidents(alert, top_k=3)
        assert len(results) > 0

    def test_episode_stats(self):
        from backend.app import storage
        storage.init_db()

        alert = {"id": 1, "ip": "1.2.3.4", "description": "test", "tags": []}
        store_episode(alert=alert, run_id=1, verdict="malicious", confidence=0.9, risk_score=80)
        store_episode(alert=alert, run_id=2, verdict="benign", confidence=0.7, risk_score=20)

        stats = get_episode_stats()
        assert stats["total_episodes"] >= 2


class TestFeedbackLoop:
    def test_submit_confirm_feedback(self, client):
        # Create alert and run
        resp = client.post("/alerts", json={
            "ip": "10.0.0.1", "source": "test",
            "description": "test", "tags": [],
        })
        alert_id = resp.json()["alert"]["id"]

        resp = client.post("/runs", json={"alert_id": alert_id, "mode": "classic"})
        # Don't wait for run to complete, just submit feedback
        from backend.app import storage
        run_id = resp.json()["run"]["id"]

        result = submit_feedback(run_id, "confirm", "Looks correct")
        assert result["feedback"] == "confirm"

    def test_submit_false_positive_feedback(self, client):
        from backend.app import storage

        resp = client.post("/alerts", json={
            "ip": "10.0.0.2", "source": "test",
            "description": "test", "tags": [],
        })
        alert_id = resp.json()["alert"]["id"]

        resp = client.post("/runs", json={"alert_id": alert_id, "mode": "classic"})
        run_id = resp.json()["run"]["id"]

        result = submit_feedback(run_id, "false_positive", "This was a scan from our Nessus")
        assert result["feedback"] == "false_positive"

    def test_invalid_feedback_raises(self):
        with pytest.raises(ValueError):
            submit_feedback(999, "invalid_type")

    def test_get_feedback_stats(self, client):
        stats = get_feedback_stats()
        assert "total_feedback" in stats
        assert "false_positive_rate" in stats

    def test_feedback_api_endpoint(self, client):
        resp = client.get("/feedback/stats")
        assert resp.status_code == 200
        assert "total_feedback" in resp.json()

    def test_memory_stats_endpoint(self, client):
        resp = client.get("/feedback/memory/stats")
        assert resp.status_code == 200
        assert "total_episodes" in resp.json()
