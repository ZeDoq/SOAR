import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _test_db(tmp_path, monkeypatch):
    """Each test gets an isolated temporary SQLite database."""
    db_file = tmp_path / "test_soar.db"
    monkeypatch.setenv("SOAR_DB_PATH", str(db_file))

    from backend.app import settings as settings_mod

    settings_mod.settings = settings_mod.Settings()

    from backend.app import storage

    storage.init_db()
    yield


@pytest.fixture
def client(_test_db):
    """Create a fresh app with the test database and authenticated user."""
    from backend.app.main import create_app
    from backend.app.routes.auth import _login_attempts

    # 清除限速状态（跨测试隔离）
    _login_attempts.clear()

    app = create_app()
    c = TestClient(app, raise_server_exceptions=False)

    # 注册测试用户并获取 token
    c.post("/auth/register", json={"username": "testuser", "password": "Test1234"})
    resp = c.post("/auth/login", json={"username": "testuser", "password": "Test1234"})
    token = resp.json().get("access_token", "")

    # 设置默认认证头
    c.headers["Authorization"] = f"Bearer {token}"
    return c
