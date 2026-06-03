"""Tests for MCP tool protocol, governance, and audit system."""

import pytest

from backend.app.mcp import tool_registry, governance, audit, server


@pytest.fixture(autouse=True)
def _reset_mcp():
    """Reset MCP state for each test."""
    tool_registry.reset()
    yield
    tool_registry.reset()


class TestToolRegistry:
    def test_register_and_list_tools(self):
        tool_registry.register_tool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
            handler=lambda: "ok",
            category="test",
        )
        tools = tool_registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

    def test_get_tool(self):
        tool_registry.register_tool(
            name="my_tool",
            description="My tool",
            input_schema={},
            handler=lambda x: x,
        )
        tool = tool_registry.get_tool("my_tool")
        assert tool is not None
        assert tool["name"] == "my_tool"

    def test_get_missing_tool(self):
        assert tool_registry.get_tool("nonexistent") is None

    def test_call_tool(self):
        tool_registry.register_tool(
            name="adder",
            description="Add two numbers",
            input_schema={},
            handler=lambda a, b: a + b,
        )
        result = tool_registry.call_tool("adder", {"a": 3, "b": 4})
        assert result == 7

    def test_call_missing_tool_raises(self):
        with pytest.raises(KeyError):
            tool_registry.call_tool("nonexistent", {})

    def test_list_by_category(self):
        tool_registry.register_tool("tool_a", "A", {}, lambda: "a", category="intel")
        tool_registry.register_tool("tool_b", "B", {}, lambda: "b", category="response")
        intel_tools = tool_registry.list_tools_by_category("intel")
        assert len(intel_tools) == 1
        assert intel_tools[0]["name"] == "tool_a"

    def test_reset(self):
        tool_registry.register_tool("tool_1", "T1", {}, lambda: None)
        assert tool_registry.get_tool_count() == 1
        tool_registry.reset()
        assert tool_registry.get_tool_count() == 0


class TestGovernance:
    def test_intel_agent_can_query_intel(self):
        assert governance.check_permission("intelligence_agent", "virustotal_lookup") is True
        assert governance.check_permission("intelligence_agent", "abuseipdb_lookup") is True

    def test_intel_agent_cannot_block(self):
        assert governance.check_permission("intelligence_agent", "firewall_block") is False

    def test_analysis_agent_can_search_kb(self):
        assert governance.check_permission("analysis_agent", "search_knowledge_base") is True

    def test_analysis_agent_cannot_block(self):
        assert governance.check_permission("analysis_agent", "firewall_block") is False

    def test_response_agent_can_block(self):
        assert governance.check_permission("response_agent", "firewall_block") is True

    def test_response_agent_cannot_query_intel(self):
        assert governance.check_permission("response_agent", "virustotal_lookup") is False

    def test_supervisor_can_do_everything(self):
        for tool in governance.TOOL_PERMISSIONS:
            assert governance.check_permission("supervisor", tool) is True

    def test_unknown_tool_allowed(self):
        """Tools not in governance map should be unrestricted."""
        assert governance.check_permission("analysis_agent", "unknown_tool") is True

    def test_permission_matrix(self):
        matrix = governance.get_permission_matrix()
        assert "intelligence_agent" in matrix
        assert "virustotal_lookup" in matrix["intelligence_agent"]
        assert matrix["intelligence_agent"]["virustotal_lookup"] is True
        assert matrix["intelligence_agent"]["firewall_block"] is False


class TestAudit:
    def test_log_and_retrieve(self):
        record_id = audit.log_tool_call(
            agent_role="intelligence_agent",
            tool_name="virustotal_lookup",
            arguments={"ip": "1.2.3.4"},
            result="malicious",
            success=True,
        )
        assert record_id > 0

        logs = audit.get_audit_log()
        assert len(logs) >= 1
        assert logs[0]["tool_name"] == "virustotal_lookup"

    def test_log_denied_call(self):
        audit.log_tool_call(
            agent_role="analysis_agent",
            tool_name="firewall_block",
            arguments={"ip": "1.2.3.4"},
            success=False,
            error="Governance denied",
        )
        logs = audit.get_audit_log(tool_name="firewall_block")
        assert len(logs) >= 1
        assert logs[0]["success"] is False

    def test_audit_stats(self):
        audit.log_tool_call("agent", "tool_a", {}, success=True)
        audit.log_tool_call("agent", "tool_b", {}, success=False, error="denied")
        stats = audit.get_audit_stats()
        assert stats["total_calls"] >= 2
        assert stats["denied_calls"] >= 1


class TestMCPServer:
    def test_execute_with_permission(self):
        tool_registry.register_tool(
            name="test_query",
            description="Test query tool",
            input_schema={},
            handler=lambda: "result",
            category="analysis",
        )
        # Override governance for this test
        governance.TOOL_PERMISSIONS["test_query"] = governance.PERM_KNOWLEDGE_QUERY

        result = server.execute_tool("test_query", {}, agent_role="analysis_agent")
        assert result["success"] is True
        assert result["result"] == "result"

    def test_execute_denied_by_governance(self):
        tool_registry.register_tool(
            name="dangerous_tool",
            description="Dangerous",
            input_schema={},
            handler=lambda: "boom",
            category="response",
        )
        governance.TOOL_PERMISSIONS["dangerous_tool"] = governance.PERM_RESPONSE_ACTION

        result = server.execute_tool("dangerous_tool", {}, agent_role="analysis_agent")
        assert result["success"] is False
        assert "Governance denied" in result["error"]


class TestMCPAPI:
    def test_list_tools_endpoint(self, client):
        resp = client.get("/mcp/tools")
        assert resp.status_code == 200
        assert "tools" in resp.json()
        assert "count" in resp.json()

    def test_governance_endpoint(self, client):
        resp = client.get("/mcp/governance")
        assert resp.status_code == 200
        data = resp.json()
        assert "matrix" in data
        assert "roles" in data
        assert "intelligence_agent" in data["roles"]

    def test_audit_endpoint(self, client):
        resp = client.get("/mcp/audit")
        assert resp.status_code == 200
        assert "audit_log" in resp.json()

    def test_audit_stats_endpoint(self, client):
        resp = client.get("/mcp/audit/stats")
        assert resp.status_code == 200
        assert "total_calls" in resp.json()
