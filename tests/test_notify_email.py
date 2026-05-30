from unittest.mock import MagicMock, patch

from backend.app.integrations import notify_email


def _sample_data():
    alert = {"ip": "10.0.0.1", "source": "test", "description": "test alert", "tags": ["test"]}
    risk = {"risk_score": 85, "rationale": "high risk", "signals": {}}
    decision = {"action": "block"}
    return alert, risk, decision


class TestSendAlertEmail:
    def test_returns_none_when_smtp_not_configured(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "")
        from backend.app import settings as settings_mod
        settings_mod.settings = settings_mod.Settings()

        alert, risk, decision = _sample_data()
        result = notify_email.send_alert_email(alert, risk, decision)
        assert result is None

    def test_returns_none_when_no_recipients(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "localhost")
        monkeypatch.setenv("SMTP_TO", "")
        from backend.app import settings as settings_mod
        settings_mod.settings = settings_mod.Settings()

        alert, risk, decision = _sample_data()
        result = notify_email.send_alert_email(alert, risk, decision)
        assert result is None

    def test_constructs_email_with_alert_details(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "localhost")
        monkeypatch.setenv("SMTP_PORT", "25")
        monkeypatch.setenv("SMTP_FROM", "soar@test.com")
        monkeypatch.setenv("SMTP_TO", "admin@test.com")
        from backend.app import settings as settings_mod
        settings_mod.settings = settings_mod.Settings()

        mock_server = MagicMock()
        with patch("backend.app.integrations.notify_email.smtplib.SMTP", return_value=MagicMock()) as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

            alert, risk, decision = _sample_data()
            result = notify_email.send_alert_email(alert, risk, decision)
            assert result is not None
            assert result["channel"] == "email"
            assert result["status"] == "sent"
            assert "admin@test.com" in result["recipients"]

    def test_parse_recipients(self):
        result = notify_email._parse_recipients("a@test.com, b@test.com, c@test.com")
        assert result == ["a@test.com", "b@test.com", "c@test.com"]

    def test_parse_recipients_empty(self):
        assert notify_email._parse_recipients("") == []
        assert notify_email._parse_recipients("   ") == []
