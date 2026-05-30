import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


class TestHealth:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestAlertsAPI:
    def test_create_alert(self, client):
        resp = client.post(
            "/alerts",
            json={
                "ip": "10.0.0.1",
                "source": "test",
                "description": "unit test",
                "tags": ["test"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["alert"]["ip"] == "10.0.0.1"
        assert data["alert"]["id"] is not None

    def test_list_alerts(self, client):
        client.post("/alerts", json={"ip": "1.1.1.1", "source": "test", "description": "a"})
        client.post("/alerts", json={"ip": "2.2.2.2", "source": "test", "description": "b"})
        resp = client.get("/alerts")
        assert resp.status_code == 200
        assert len(resp.json()["alerts"]) >= 2

    def test_get_alert_by_id(self, client):
        create_resp = client.post(
            "/alerts", json={"ip": "3.3.3.3", "source": "test", "description": "c"}
        )
        alert_id = create_resp.json()["alert"]["id"]
        resp = client.get(f"/alerts/{alert_id}")
        assert resp.status_code == 200
        assert resp.json()["alert"]["ip"] == "3.3.3.3"

    def test_get_alert_not_found(self, client):
        resp = client.get("/alerts/99999")
        assert resp.status_code == 404


class TestRunsAPI:
    def _create_alert(self, client):
        resp = client.post(
            "/alerts", json={"ip": "1.1.1.1", "source": "test", "description": "test"}
        )
        return resp.json()["alert"]["id"]

    def test_start_run(self, client):
        alert_id = self._create_alert(client)
        resp = client.post("/runs", json={"alert_id": alert_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["run"]["status"] == "queued"
        assert data["run"]["alert_id"] == alert_id

    def test_list_runs(self, client):
        alert_id = self._create_alert(client)
        client.post("/runs", json={"alert_id": alert_id})
        resp = client.get("/runs")
        assert resp.status_code == 200
        assert len(resp.json()["runs"]) >= 1

    def test_get_run_detail(self, client):
        alert_id = self._create_alert(client)
        create_resp = client.post("/runs", json={"alert_id": alert_id})
        run_id = create_resp.json()["run"]["id"]
        resp = client.get(f"/runs/{run_id}")
        assert resp.status_code == 200
        assert "run" in resp.json()
        assert "steps" in resp.json()

    def test_get_run_not_found(self, client):
        resp = client.get("/runs/99999")
        assert resp.status_code == 404


class TestSourcesAPI:
    def test_list_sources(self, client):
        resp = client.get("/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data
        names = [s["name"] for s in data["sources"]]
        assert "syslog" in names
        assert "wazuh" in names
        assert "suricata" in names

    def test_start_unknown_source(self, client):
        resp = client.post("/sources/unknown/start")
        assert resp.status_code == 400

    def test_stop_unknown_source(self, client):
        resp = client.post("/sources/unknown/stop")
        assert resp.status_code == 400
