from backend.app.simulator.scenarios import get_scenario, get_scenario_names, SCENARIOS
from backend.app.simulator.runner import run_scenario, run_all_scenarios
from backend.app import storage


class TestScenarios:
    def test_get_scenario_names(self):
        names = get_scenario_names()
        assert "brute_force" in names
        assert "ddos" in names
        assert len(names) == 8

    def test_get_scenario(self):
        s = get_scenario("brute_force")
        assert s is not None
        assert s["name"] == "SSH 暴力破解攻击"
        assert len(s["alerts"]) >= 1

    def test_get_scenario_unknown(self):
        assert get_scenario("nonexistent") is None

    def test_all_scenarios_have_required_fields(self):
        for name, scenario in SCENARIOS.items():
            assert "name" in scenario, f"{name} missing 'name'"
            assert "description" in scenario, f"{name} missing 'description'"
            assert "alerts" in scenario, f"{name} missing 'alerts'"
            assert "expected_outcome" in scenario, f"{name} missing 'expected_outcome'"
            assert "attack_type" in scenario, f"{name} missing 'attack_type'"


class TestRunner:
    def test_run_scenario(self):
        result = run_scenario("brute_force")
        assert "error" not in result
        assert result["scenario"] == "brute_force"
        assert len(result["alerts_created"]) >= 1
        # Verify alerts are in the database
        for alert_info in result["alerts_created"]:
            alert = storage.get_alert(alert_info["id"])
            assert alert is not None

    def test_run_scenario_unknown(self):
        result = run_scenario("nonexistent")
        assert "error" in result

    def test_run_scenario_with_auto_run(self):
        result = run_scenario("port_scan", auto_run=True)
        assert "runs_created" in result
        assert len(result["runs_created"]) >= 1

    def test_run_all_scenarios(self):
        result = run_all_scenarios()
        assert result["scenarios_run"] == 8
        assert "brute_force" in result["results"]
        assert "ddos" in result["results"]


class TestSimulatorRoutes:
    def test_list_scenarios(self, client):
        resp = client.get("/simulator/scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert "scenarios" in data
        assert len(data["scenarios"]) == 8

    def test_trigger_scenario(self, client):
        resp = client.post("/simulator/run/brute_force?auto_run=false")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario"] == "brute_force"
        assert len(data["alerts_created"]) >= 1

    def test_trigger_unknown_scenario(self, client):
        resp = client.post("/simulator/run/nonexistent?auto_run=false")
        assert resp.status_code == 404
