from backend.app.agents.context import AgentContext


class TestAgentContext:
    def test_creation(self):
        alert = {"ip": "1.2.3.4", "source": "test", "description": "test", "tags": []}
        ctx = AgentContext(alert=alert, run_id=1)
        assert ctx.alert == alert
        assert ctx.run_id == 1
        assert ctx.intel is None
        assert ctx.risk is None
        assert ctx.agent_logs == []

    def test_log(self):
        ctx = AgentContext(alert={}, run_id=1)
        ctx.log("test_agent", "test message", {"key": "value"})
        assert len(ctx.agent_logs) == 1
        assert ctx.agent_logs[0]["agent"] == "test_agent"
        assert ctx.agent_logs[0]["message"] == "test message"
        assert ctx.agent_logs[0]["data"] == {"key": "value"}

    def test_log_without_data(self):
        ctx = AgentContext(alert={}, run_id=1)
        ctx.log("agent", "message")
        assert len(ctx.agent_logs) == 1
        assert "data" not in ctx.agent_logs[0]

    def test_to_dict(self):
        alert = {"ip": "1.2.3.4"}
        ctx = AgentContext(alert=alert, run_id=42)
        ctx.intel = {"reputation": "malicious"}
        ctx.log("test", "did something")
        d = ctx.to_dict()
        assert d["alert"] == alert
        assert d["run_id"] == 42
        assert d["intel"]["reputation"] == "malicious"
        assert len(d["agent_logs"]) == 1
