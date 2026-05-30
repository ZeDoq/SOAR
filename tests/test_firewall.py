from backend.app.integrations import firewall


class TestBlock:
    def test_returns_blocked_action(self):
        risk = {"risk_score": 85}
        result = firewall.block("192.168.1.1", risk, latency_ms=0)
        assert result["action"] == "blocked"
        assert result["ip"] == "192.168.1.1"

    def test_ticket_format(self):
        risk = {"risk_score": 90}
        result = firewall.block("10.0.0.1", risk, latency_ms=0)
        assert result["ticket"].startswith("FW-")
        assert result["ticket"][3:].isdigit()

    def test_reason_contains_risk_score(self):
        risk = {"risk_score": 75}
        result = firewall.block("172.16.0.1", risk, latency_ms=0)
        assert "75" in result["reason"]

    def test_deterministic_ticket(self):
        """Same IP should produce the same ticket number."""
        risk = {"risk_score": 80}
        r1 = firewall.block("8.8.8.8", risk, latency_ms=0)
        r2 = firewall.block("8.8.8.8", risk, latency_ms=0)
        assert r1["ticket"] == r2["ticket"]
