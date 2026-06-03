"""Tests for attack chain detection and temporal reasoning."""

import pytest

from backend.app.graph.temporal_reasoning import (
    get_tactic_for_technique,
    compute_tactic_progression_score,
    compute_temporal_proximity,
    detect_attack_chain_from_alerts,
    TACTIC_ORDER,
)


class TestTemporalReasoning:
    def test_tactic_mapping(self):
        assert get_tactic_for_technique("T1190") == "initial-access"
        assert get_tactic_for_technique("T1059") == "execution"
        assert get_tactic_for_technique("T1021") == "lateral-movement"
        assert get_tactic_for_technique("T1048") == "exfiltration"
        assert get_tactic_for_technique("T1498") == "impact"
        assert get_tactic_for_technique("T99999") is None

    def test_progression_score_perfect(self):
        """Attack progressing through valid kill chain stages."""
        tactics = ["initial-access", "execution", "persistence", "lateral-movement", "exfiltration"]
        score = compute_tactic_progression_score(tactics)
        assert score == 1.0

    def test_progression_score_backward(self):
        """Attack with backward jumps scores lower."""
        tactics = ["exfiltration", "initial-access", "impact"]
        score = compute_tactic_progression_score(tactics)
        assert score <= 0.5  # 1/2 pairs are forward

    def test_progression_score_single(self):
        score = compute_tactic_progression_score(["initial-access"])
        assert score == 1.0

    def test_progression_score_empty(self):
        score = compute_tactic_progression_score([])
        assert score == 1.0

    def test_temporal_proximity_close_events(self):
        """Events within hours should score high."""
        timestamps = [
            "2025-01-01T10:00:00+00:00",
            "2025-01-01T11:00:00+00:00",
            "2025-01-01T12:00:00+00:00",
        ]
        score = compute_temporal_proximity(timestamps)
        assert score > 0.9

    def test_temporal_proximity_far_events(self):
        """Events days apart should score low."""
        timestamps = [
            "2025-01-01T10:00:00+00:00",
            "2025-01-10T10:00:00+00:00",
        ]
        score = compute_temporal_proximity(timestamps, max_window_hours=72)
        assert score < 0.1

    def test_detect_chain_apt_progression(self):
        """Test detection of a multi-stage APT attack chain."""
        alerts = [
            {"id": 1, "ip": "1.2.3.4", "description": "port scan", "tags": ["scan", "T1046"],
             "observed_at": "2025-01-01T10:00:00+00:00"},
            {"id": 2, "ip": "1.2.3.4", "description": "exploit SMB", "tags": ["exploit", "T1190"],
             "observed_at": "2025-01-01T10:30:00+00:00"},
            {"id": 3, "ip": "1.2.3.4", "description": "powershell execution", "tags": ["powershell", "T1059"],
             "observed_at": "2025-01-01T11:00:00+00:00"},
            {"id": 4, "ip": "1.2.3.4", "description": "RDP lateral movement", "tags": ["rdp", "T1021"],
             "observed_at": "2025-01-01T12:00:00+00:00"},
            {"id": 5, "ip": "1.2.3.4", "description": "DNS exfiltration", "tags": ["exfil", "T1048"],
             "observed_at": "2025-01-01T13:00:00+00:00"},
        ]
        chains = detect_attack_chain_from_alerts(alerts)
        assert len(chains) > 0
        chain = chains[0]
        assert chain["ip"] == "1.2.3.4"
        assert chain["alert_count"] == 5
        assert chain["confidence"] > 0.5

    def test_detect_chain_single_alert(self):
        """Single alert should not form a chain."""
        alerts = [{"id": 1, "ip": "1.2.3.4", "description": "scan", "tags": ["scan"],
                    "observed_at": "2025-01-01T10:00:00"}]
        chains = detect_attack_chain_from_alerts(alerts)
        assert len(chains) == 0


class TestChainDetector:
    def test_chain_api_endpoint(self, client):
        """Test the chains API returns properly."""
        resp = client.get("/chains")
        assert resp.status_code == 200
        assert "chains" in resp.json()

    def test_chain_for_unknown_ip(self, client):
        resp = client.get("/chains/1.2.3.4")
        assert resp.status_code == 404

    def test_apt_scenario_in_simulator(self, client):
        """Test that APT scenarios are available in the simulator."""
        resp = client.get("/simulator/scenarios")
        assert resp.status_code == 200
        scenarios = resp.json()["scenarios"]
        scenario_names = [s["name"] for s in scenarios]
        assert "apt_lateral_movement" in scenario_names
        assert "supply_chain_attack" in scenario_names
        # Check alert counts
        apt = next(s for s in scenarios if s["name"] == "apt_lateral_movement")
        assert apt["alert_count"] == 5
