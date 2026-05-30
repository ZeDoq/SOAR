from backend.app import storage
from backend.app.agents.adaptive_orchestrator import execute_adaptive_playbook


class TestAdaptivePlaybook:
    def _create_alert(self, ip="1.2.3.4", desc="test", tags=None):
        return storage.create_alert({
            "ip": ip, "source": "test", "description": desc,
            "tags": tags or [],
        })

    def test_brute_force_selects_correct_template(self):
        alert = self._create_alert(desc="SSH bruteforce attack", tags=["ssh"])
        run = storage.create_run(alert["id"])
        execute_adaptive_playbook(run["id"])

        run = storage.get_run(run["id"])
        assert run["status"] == "completed"
        decision = run["decision"]
        assert decision.get("template") == "brute_force"

    def test_creates_eight_steps(self):
        alert = self._create_alert()
        run = storage.create_run(alert["id"])
        execute_adaptive_playbook(run["id"])

        steps = storage.list_steps(run["id"])
        assert len(steps) == 8
        names = [s["name"] for s in steps]
        assert names == [
            "threat_intel", "network_recon", "risk_assessment", "ai_analysis",
            "firewall_block", "notify_email", "notify_slack", "report_generation",
        ]

    def test_high_risk_blocks(self):
        # 99.99.99.99 → signal=96 → malicious → risk=80
        alert = self._create_alert(ip="99.99.99.99")
        run = storage.create_run(alert["id"])
        execute_adaptive_playbook(run["id"])

        run = storage.get_run(run["id"])
        assert run["status"] == "completed"
        assert run["risk_score"] >= 60  # brute_force template uses threshold 60

    def test_low_risk_monitors(self):
        # 1.1.1.1 → signal=4 → benign → risk=30
        alert = self._create_alert(ip="1.1.1.1")
        run = storage.create_run(alert["id"])
        execute_adaptive_playbook(run["id"])

        run = storage.get_run(run["id"])
        assert run["status"] == "completed"
        decision = run["decision"]
        assert decision["action"] == "monitor"

    def test_agent_reasoning_logged(self):
        alert = self._create_alert()
        run = storage.create_run(alert["id"])
        execute_adaptive_playbook(run["id"])

        run = storage.get_run(run["id"])
        decision = run["decision"]
        assert "agent_reasoning" in decision
        assert isinstance(decision["agent_reasoning"], list)
        assert len(decision["agent_reasoning"]) >= 1

    def test_failed_on_missing_alert(self):
        run = storage.create_run(99999, status="queued")
        execute_adaptive_playbook(run["id"])
        run = storage.get_run(run["id"])
        assert run["status"] == "failed"

    def test_ddos_low_threshold(self):
        alert = self._create_alert(desc="DDoS flood attack", tags=["ddos"])
        run = storage.create_run(alert["id"])
        execute_adaptive_playbook(run["id"])

        run = storage.get_run(run["id"])
        assert run["status"] == "completed"
        decision = run["decision"]
        assert decision.get("template") == "ddos"

    def test_phishing_skips_firewall(self):
        alert = self._create_alert(desc="Phishing email", tags=["phishing"])
        run = storage.create_run(alert["id"])
        execute_adaptive_playbook(run["id"])

        steps = storage.list_steps(run["id"])
        fw_step = [s for s in steps if s["name"] == "firewall_block"][0]
        assert fw_step["status"] == "skipped"
