from backend.app.main import app


class TestAuth:
    def test_register_and_login(self, client):
        resp = client.post("/auth/register", json={"username": "alice", "password": "Secret123"})
        assert resp.status_code == 200
        assert resp.json()["user"]["username"] == "alice"

        resp = client.post("/auth/login", json={"username": "alice", "password": "Secret123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_duplicate_register(self, client):
        client.post("/auth/register", json={"username": "bob", "password": "Pass1234"})
        resp = client.post("/auth/register", json={"username": "bob", "password": "Pass1234"})
        assert resp.status_code == 409

    def test_wrong_password(self, client):
        client.post("/auth/register", json={"username": "carol", "password": "Correct1"})
        resp = client.post("/auth/login", json={"username": "carol", "password": "Wrong123"})
        assert resp.status_code == 401

    def test_missing_fields(self, client):
        resp = client.post("/auth/register", json={"username": "dave"})
        assert resp.status_code == 400
        resp = client.post("/auth/login", json={})
        assert resp.status_code == 400

    def test_weak_password_rejected(self, client):
        resp = client.post("/auth/register", json={"username": "weak", "password": "123"})
        assert resp.status_code == 400

    def test_password_no_number_rejected(self, client):
        resp = client.post("/auth/register", json={"username": "nonum", "password": "onlyletters"})
        assert resp.status_code == 400
