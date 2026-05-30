from unittest.mock import MagicMock, patch

from backend.app.integrations import notify_slack


def _sample_data():
    alert = {"ip": "10.0.0.1", "source": "test", "description": "test alert", "tags": ["test"]}
    risk = {"risk_score": 85, "rationale": "high risk", "signals": {}}
    decision = {"action": "block"}
    return alert, risk, decision


class TestSendSlackAlert:
    def test_returns_none_when_webhook_not_configured(self, monkeypatch):
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "")
        from backend.app import settings as settings_mod
        settings_mod.settings = settings_mod.Settings()

        alert, risk, decision = _sample_data()
        result = notify_slack.send_slack_alert(alert, risk, decision)
        assert result is None

    def test_sends_correct_payload(self, monkeypatch):
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/test")
        from backend.app import settings as settings_mod
        settings_mod.settings = settings_mod.Settings()

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            alert, risk, decision = _sample_data()
            result = notify_slack.send_slack_alert(alert, risk, decision)

            assert result is not None
            assert result["channel"] == "slack"
            assert result["status"] == "sent"

            # Verify payload structure
            call_args = mock_post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")
            assert "attachments" in payload
            assert payload["attachments"][0]["color"] == "#ff0000"  # high risk = red

    def test_color_coding_by_risk(self, monkeypatch):
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/test")
        from backend.app import settings as settings_mod
        settings_mod.settings = settings_mod.Settings()

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()

        alert = {"ip": "1.1.1.1", "source": "test", "description": "low risk"}
        decision = {"action": "monitor"}

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            # Low risk -> green
            notify_slack.send_slack_alert(alert, {"risk_score": 20}, decision)
            payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
            assert payload["attachments"][0]["color"] == "#00ff00"

            # Medium risk -> yellow
            notify_slack.send_slack_alert(alert, {"risk_score": 50}, decision)
            payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
            assert payload["attachments"][0]["color"] == "#ffaa00"

    def test_handles_http_error(self, monkeypatch):
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/test")
        from backend.app import settings as settings_mod
        settings_mod.settings = settings_mod.Settings()

        with patch("httpx.post", side_effect=Exception("connection refused")):
            alert, risk, decision = _sample_data()
            result = notify_slack.send_slack_alert(alert, risk, decision)
            assert result is None
