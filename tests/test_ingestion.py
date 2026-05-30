from backend.app.ingestion.syslog_listener import parse_syslog
from backend.app.ingestion.wazuh_client import parse_wazuh_alert
from backend.app.ingestion.suricata_tail import parse_suricata_alert
from backend.app.ingestion import manager


class TestParseSyslog:
    def test_parses_standard_syslog(self):
        raw = "<34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8 from 192.168.1.100"
        result = parse_syslog(raw)
        assert result is not None
        assert result["ip"] == "192.168.1.100"
        assert result["source"] == "syslog"
        assert "syslog" in result["tags"]

    def test_returns_none_for_empty(self):
        assert parse_syslog("") is None
        assert parse_syslog("   ") is None

    def test_fallback_parsing(self):
        """Non-standard format should still try to extract IP."""
        raw = "Connection from 10.0.0.5 blocked"
        result = parse_syslog(raw)
        assert result is not None
        assert result["ip"] == "10.0.0.5"

    def test_returns_none_without_ip(self):
        """Message without IP should return None."""
        raw = "System rebooted"
        result = parse_syslog(raw)
        assert result is None

    def test_tags_include_syslog(self):
        raw = "<34>Oct 11 22:14:15 host app: msg from 1.2.3.4"
        result = parse_syslog(raw)
        assert result is not None
        assert "syslog" in result["tags"]


class TestParseWazuhAlert:
    def test_maps_srcip(self):
        raw = {
            "data": {"srcip": "10.0.0.5"},
            "rule": {"description": "Test alert", "groups": ["auth", "ssh"]},
            "agent": {"name": "web-server-01"},
        }
        result = parse_wazuh_alert(raw)
        assert result is not None
        assert result["ip"] == "10.0.0.5"
        assert "web-server-01" in result["description"]
        assert "wazuh" in result["tags"]

    def test_returns_none_for_missing_srcip(self):
        raw = {"data": {}, "rule": {"description": "No IP"}}
        result = parse_wazuh_alert(raw)
        assert result is None

    def test_groups_in_tags(self):
        raw = {
            "data": {"srcip": "10.0.0.1"},
            "rule": {"description": "Test", "groups": ["auth", "ssh", "attack"]},
        }
        result = parse_wazuh_alert(raw)
        assert "auth" in result["tags"]
        assert "ssh" in result["tags"]
        assert "wazuh" in result["tags"]


class TestParseSuricataAlert:
    def test_parses_alert_event(self):
        raw = {
            "event_type": "alert",
            "src_ip": "172.16.0.1",
            "alert": {
                "signature": "ET MALWARE Suspicious outbound connection",
                "severity": 1,
                "category": "trojan",
            },
        }
        result = parse_suricata_alert(raw)
        assert result is not None
        assert result["ip"] == "172.16.0.1"
        assert "suricata" in result["tags"]
        assert "trojan" in result["tags"]

    def test_ignores_non_alert_events(self):
        raw = {"event_type": "http", "src_ip": "10.0.0.1"}
        result = parse_suricata_alert(raw)
        assert result is None

    def test_returns_none_without_src_ip(self):
        raw = {"event_type": "alert", "alert": {"signature": "test"}}
        result = parse_suricata_alert(raw)
        assert result is None


class TestManager:
    def test_get_status_returns_all_sources(self):
        status = manager.get_status()
        names = [s["name"] for s in status]
        assert "syslog" in names
        assert "wazuh" in names
        assert "suricata" in names

    def test_start_unknown_source_returns_error(self):
        result = manager.start_source("unknown_source")
        assert result["status"] == "error"

    def test_stop_non_running_source(self):
        result = manager.stop_source("nonexistent")
        assert result["status"] == "not_running"

    def test_ingest_alert_creates_in_storage(self):
        alert_dict = {
            "ip": "10.0.0.1",
            "source": "test",
            "description": "test alert",
            "tags": ["test"],
        }
        # Should not raise
        manager._ingest_alert(alert_dict)

    def test_wazuh_not_configured_returns_error(self, monkeypatch):
        monkeypatch.setenv("WAZUH_API_URL", "")
        from backend.app import settings as settings_mod
        settings_mod.settings = settings_mod.Settings()

        result = manager.start_source("wazuh")
        assert result["status"] == "error"

    def test_suricata_not_configured_returns_error(self, monkeypatch):
        monkeypatch.setenv("SURICATA_EVE_LOG", "")
        from backend.app import settings as settings_mod
        settings_mod.settings = settings_mod.Settings()

        result = manager.start_source("suricata")
        assert result["status"] == "error"
