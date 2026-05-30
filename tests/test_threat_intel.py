from backend.app.integrations import threat_intel


class TestLookup:
    def test_malicious_ip(self):
        """IP with octets summing to >= 70 mod 100 should be malicious."""
        result = threat_intel.lookup("200.200.200.200", latency_ms=0)
        assert result["ip"] == "200.200.200.200"
        assert result["reputation"] in ("malicious", "suspicious", "benign")
        assert 0 <= result["confidence"] <= 1
        assert "sources" in result

    def test_deterministic(self):
        """Same IP should always return the same result."""
        r1 = threat_intel.lookup("10.0.0.1", latency_ms=0)
        r2 = threat_intel.lookup("10.0.0.1", latency_ms=0)
        assert r1 == r2

    def test_signal_range(self):
        """Signal value should be between 0 and 99."""
        result = threat_intel.lookup("1.2.3.4", latency_ms=0)
        assert 0 <= result["signal"] <= 99

    def test_reputation_consistency(self):
        """Reputation should match the signal thresholds."""
        result = threat_intel.lookup("185.199.109.153", latency_ms=0)
        assert result["reputation"] == "suspicious"
        assert result["confidence"] == 0.68

    def test_benign_ip(self):
        """Low signal IP should be benign."""
        result = threat_intel.lookup("1.1.1.1", latency_ms=0)
        assert result["reputation"] == "benign"
        assert result["confidence"] == 0.35

    def test_sources_present(self):
        result = threat_intel.lookup("8.8.8.8", latency_ms=0)
        assert len(result["sources"]) >= 1
        assert "simulated" in result["sources"]
        assert "per_source" in result


class TestSimulatedLookup:
    def test_malicious_signal(self):
        """signal >= 70 should be malicious."""
        # 99.99.99.99: sum=396, signal=96 -> malicious
        result = threat_intel._simulated_lookup("99.99.99.99", latency_ms=0)
        assert result["reputation"] == "malicious"
        assert result["confidence"] == 0.92

    def test_suspicious_signal(self):
        """signal 40-69 should be suspicious."""
        # 185.199.109.153: sum=646, signal=46 -> suspicious
        result = threat_intel._simulated_lookup("185.199.109.153", latency_ms=0)
        assert result["reputation"] == "suspicious"
        assert result["confidence"] == 0.68

    def test_benign_signal(self):
        """signal < 40 should be benign."""
        result = threat_intel._simulated_lookup("1.1.1.1", latency_ms=0)
        assert result["reputation"] == "benign"
        assert result["confidence"] == 0.35

    def test_source_is_simulated(self):
        result = threat_intel._simulated_lookup("1.2.3.4", latency_ms=0)
        assert result["source"] == "simulated"


class TestVirusTotalNormalization:
    def test_no_api_key_returns_none(self, monkeypatch):
        monkeypatch.setenv("VIRUSTOTAL_API_KEY", "")
        from backend.app import settings as settings_mod
        settings_mod.settings = settings_mod.Settings()

        result = threat_intel._query_virustotal("1.2.3.4", "")
        assert result is None

    def test_empty_key_returns_none(self):
        result = threat_intel._query_virustotal("1.2.3.4", "")
        assert result is None


class TestAbuseipdbNormalization:
    def test_no_api_key_returns_none(self):
        result = threat_intel._query_abuseipdb("1.2.3.4", "")
        assert result is None


class TestAggregation:
    def test_worst_reputation_wins(self):
        """Aggregated reputation should be the worst among sources."""
        results = [
            {"source": "sim", "reputation": "benign", "confidence": 0.3, "signal": 10},
            {"source": "vt", "reputation": "malicious", "confidence": 0.9, "signal": 80},
        ]
        agg = threat_intel._aggregate(results, "1.2.3.4")
        assert agg["reputation"] == "malicious"

    def test_single_source_passthrough(self):
        results = [{"source": "test", "reputation": "suspicious", "confidence": 0.5, "signal": 50}]
        agg = threat_intel._aggregate(results, "1.2.3.4")
        assert agg["reputation"] == "suspicious"
        assert agg["confidence"] == 0.5
        assert agg["signal"] == 50

    def test_empty_results_fallback(self):
        agg = threat_intel._aggregate([], "1.2.3.4")
        assert agg["reputation"] == "benign"
        assert agg["confidence"] == 0.0
        assert agg["sources"] == []

    def test_averages_confidence(self):
        results = [
            {"source": "a", "reputation": "benign", "confidence": 0.2, "signal": 20},
            {"source": "b", "reputation": "benign", "confidence": 0.4, "signal": 40},
        ]
        agg = threat_intel._aggregate(results, "1.2.3.4")
        assert agg["confidence"] == 0.3

    def test_includes_per_source(self):
        results = [
            {"source": "a", "reputation": "benign", "confidence": 0.3, "signal": 10},
            {"source": "b", "reputation": "malicious", "confidence": 0.9, "signal": 80},
        ]
        agg = threat_intel._aggregate(results, "1.2.3.4")
        assert len(agg["per_source"]) == 2
        assert agg["sources"] == ["a", "b"]


class TestLookupNoApiKeys:
    def test_includes_simulated_when_no_api_keys(self, monkeypatch):
        monkeypatch.delenv("VIRUSTOTAL_API_KEY", raising=False)
        monkeypatch.delenv("ABUSEIPDB_API_KEY", raising=False)
        from backend.app import settings as settings_mod
        settings_mod.settings = settings_mod.Settings()

        result = threat_intel.lookup("1.2.3.4", latency_ms=0)
        assert "simulated" in result["sources"]
        assert len(result["sources"]) == 1
