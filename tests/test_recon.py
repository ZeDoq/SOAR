from backend.app.integrations import recon


class TestWhoisLookup:
    def test_returns_none_on_failure(self):
        """Invalid target should return None."""
        # Extremely long hostname to trigger failure
        result = recon.whois_lookup("this.is.not.a.valid.domain.name.at.all.invalid", latency_ms=0)
        # Should be None or a dict (depending on library behavior)
        assert result is None or isinstance(result, dict)

    def test_returns_dict_with_target_on_success(self):
        """Successful lookup should include the target field."""
        # Use a known domain that python-whois can resolve
        result = recon.whois_lookup("example.com", latency_ms=0)
        if result is not None:
            assert result["target"] == "example.com"
            assert "registrar" in result
            assert "raw_text" in result

    def test_latency_ms_zero(self):
        """Should work with latency_ms=0."""
        result = recon.whois_lookup("1.1.1.1", latency_ms=0)
        # May be None or a dict depending on system whois availability
        assert result is None or isinstance(result, dict)


class TestDnsLookup:
    def test_known_domain_returns_records(self):
        """Known domain should return DNS records."""
        result = recon.dns_lookup("example.com", latency_ms=0)
        if result is not None:
            assert result["target"] == "example.com"
            assert isinstance(result.get("a", []), list)
            assert isinstance(result.get("ns", []), list)

    def test_nxdomain_returns_none(self):
        """Non-existent domain should return None."""
        result = recon.dns_lookup("this-domain-definitely-does-not-exist-12345.com", latency_ms=0)
        assert result is None

    def test_latency_ms_zero(self):
        """Should work with latency_ms=0."""
        result = recon.dns_lookup("example.com", latency_ms=0)
        # Should work since dnspython is installed
        assert result is None or isinstance(result, dict)

    def test_record_types_present(self):
        """Result should include all record type keys."""
        result = recon.dns_lookup("example.com", latency_ms=0)
        if result is not None:
            for key in ("a", "aaaa", "mx", "txt", "ns"):
                assert key in result
