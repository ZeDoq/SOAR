from backend.app import storage
from backend.app.agents.orchestrator import execute_playbook


class TestExecutePlaybook:
    def _create_alert(self):
        return storage.create_alert(
            {
                "ip": "1.2.3.4",
                "source": "test",
                "description": "test alert",
                "tags": [],
            }
        )

    def test_high_risk_blocks_ip(self):
        """A high-risk alert should result in a block decision."""
        alert = self._create_alert()
        # 200.200.200.70: sum=670, signal=70 -> malicious -> score=80 -> block
        storage.create_alert(
            {"ip": "200.200.200.70", "source": "test", "description": "bruteforce", "tags": ["vpn"]}
        )
        # We need to use the alert we created; override IP for high signal
        # 185.199.109.153: sum=646, signal=46 -> suspicious -> score=55 -> monitor
        # Let's use an IP that yields malicious: signal >= 70
        # 90.90.90.90: sum=360, signal=60 -> suspicious
        # 99.99.99.99: sum=396, signal=96 -> malicious -> score=80 -> block
        alert2 = storage.create_alert(
            {"ip": "99.99.99.99", "source": "test", "description": "test", "tags": []}
        )
        run = storage.create_run(alert2["id"])
        execute_playbook(run["id"])

        run = storage.get_run(run["id"])
        assert run["status"] == "completed"
        assert run["risk_score"] >= 70
        decision = run["decision"]
        assert decision["action"] == "block"

    def test_low_risk_monitors(self):
        """A low-risk alert should result in a monitor decision."""
        # 1.1.1.1: sum=4, signal=4 -> benign -> score=30 -> monitor
        alert = storage.create_alert(
            {"ip": "1.1.1.1", "source": "test", "description": "test", "tags": []}
        )
        run = storage.create_run(alert["id"])
        execute_playbook(run["id"])

        run = storage.get_run(run["id"])
        assert run["status"] == "completed"
        assert run["risk_score"] < 70
        decision = run["decision"]
        assert decision["action"] == "monitor"

    def test_creates_eight_steps(self):
        """Each playbook run should create 8 steps."""
        alert = storage.create_alert(
            {"ip": "1.1.1.1", "source": "test", "description": "test", "tags": []}
        )
        run = storage.create_run(alert["id"])
        execute_playbook(run["id"])

        steps = storage.list_steps(run["id"])
        assert len(steps) == 8
        names = [s["name"] for s in steps]
        assert names == [
            "threat_intel", "risk_assessment", "ai_analysis",
            "network_recon", "firewall_block",
            "notify_email", "notify_slack",
            "report_generation",
        ]

    def test_failed_on_missing_alert(self):
        """Run with invalid alert_id should be marked failed."""
        run = storage.create_run(99999, status="queued")
        execute_playbook(run["id"])

        run = storage.get_run(run["id"])
        assert run["status"] == "failed"

    def test_network_recon_step_runs(self):
        """Network recon step should appear even if libraries unavailable."""
        alert = storage.create_alert(
            {"ip": "8.8.8.8", "source": "test", "description": "test", "tags": []}
        )
        run = storage.create_run(alert["id"])
        execute_playbook(run["id"])

        steps = storage.list_steps(run["id"])
        recon_step = [s for s in steps if s["name"] == "network_recon"][0]
        assert recon_step["status"] in ("completed", "skipped")

    def test_notification_steps_always_present(self):
        """Notification steps should always be created (skipped if not configured)."""
        alert = storage.create_alert(
            {"ip": "1.1.1.1", "source": "test", "description": "test", "tags": []}
        )
        run = storage.create_run(alert["id"])
        execute_playbook(run["id"])

        steps = storage.list_steps(run["id"])
        email_step = [s for s in steps if s["name"] == "notify_email"][0]
        slack_step = [s for s in steps if s["name"] == "notify_slack"][0]
        # Both should be skipped since SMTP and Slack are not configured
        assert email_step["status"] == "skipped"
        assert slack_step["status"] == "skipped"
