from backend.app.integrations import risk_assessor


def _make_alert(description="", tags=None):
    return {"ip": "1.2.3.4", "source": "test", "description": description, "tags": tags or []}


def _make_intel(reputation="benign", signal=10):
    return {"ip": "1.2.3.4", "reputation": reputation, "confidence": 0.5, "signal": signal}


class TestScore:
    def test_base_score(self):
        """Benign intel with no keywords should give base score of 30."""
        result = risk_assessor.score(_make_alert(), _make_intel("benign"), latency_ms=0)
        assert result["risk_score"] == 30

    def test_malicious_adds_50(self):
        result = risk_assessor.score(_make_alert(), _make_intel("malicious"), latency_ms=0)
        assert result["risk_score"] == 80  # 30 + 50

    def test_suspicious_adds_25(self):
        result = risk_assessor.score(_make_alert(), _make_intel("suspicious"), latency_ms=0)
        assert result["risk_score"] == 55  # 30 + 25

    def test_bruteforce_keyword_adds_10(self):
        result = risk_assessor.score(
            _make_alert(description="Bruteforce on admin portal"),
            _make_intel("benign"),
            latency_ms=0,
        )
        assert result["risk_score"] == 40  # 30 + 10

    def test_vpn_tag_adds_5(self):
        result = risk_assessor.score(
            _make_alert(tags=["vpn", "lateral"]),
            _make_intel("benign"),
            latency_ms=0,
        )
        assert result["risk_score"] == 35  # 30 + 5

    def test_max_score_capped_at_100(self):
        """Score should never exceed 100."""
        result = risk_assessor.score(
            _make_alert(description="bruteforce", tags=["vpn"]),
            _make_intel("malicious"),
            latency_ms=0,
        )
        # 30 + 50 + 10 + 5 = 95, capped at 100
        assert result["risk_score"] == 95

    def test_rationale_present(self):
        result = risk_assessor.score(_make_alert(), _make_intel(), latency_ms=0)
        assert "rationale" in result
        assert "signals" in result
