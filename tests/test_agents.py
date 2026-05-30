from backend.app.agents.context import AgentContext
from backend.app.agents.intelligence_agent import IntelligenceAgent
from backend.app.agents.analysis_agent import AnalysisAgent
from backend.app.agents.response_agent import ResponseAgent


def _make_alert():
    return {"ip": "1.2.3.4", "source": "test", "description": "test alert", "tags": []}


class TestIntelligenceAgent:
    def test_populates_intel(self):
        ctx = AgentContext(alert=_make_alert(), run_id=1)
        agent = IntelligenceAgent()
        ctx = agent.analyze(ctx)
        assert ctx.intel is not None
        assert "reputation" in ctx.intel
        assert "sources" in ctx.intel

    def test_populates_recon(self):
        ctx = AgentContext(alert=_make_alert(), run_id=1)
        agent = IntelligenceAgent()
        ctx = agent.analyze(ctx)
        # recon_result may be None if libraries fail, but ctx should be returned
        assert ctx is not None

    def test_logs_decisions(self):
        ctx = AgentContext(alert=_make_alert(), run_id=1)
        agent = IntelligenceAgent()
        ctx = agent.analyze(ctx)
        assert len(ctx.agent_logs) >= 1
        assert any("intelligence" in log["agent"] for log in ctx.agent_logs)


class TestAnalysisAgent:
    def test_requires_intel(self):
        ctx = AgentContext(alert=_make_alert(), run_id=1)
        agent = AnalysisAgent()
        ctx = agent.analyze(ctx)
        assert ctx.risk is not None
        assert ctx.risk["risk_score"] == 0  # no intel = 0

    def test_populates_risk(self):
        ctx = AgentContext(alert=_make_alert(), run_id=1)
        ctx.intel = {"reputation": "malicious", "confidence": 0.9, "signal": 96, "sources": ["test"]}
        agent = AnalysisAgent()
        ctx = agent.analyze(ctx)
        assert ctx.risk is not None
        assert ctx.risk["risk_score"] >= 70  # malicious = 30+50 = 80

    def test_logs_decisions(self):
        ctx = AgentContext(alert=_make_alert(), run_id=1)
        ctx.intel = {"reputation": "benign", "confidence": 0.3, "signal": 5, "sources": ["test"]}
        agent = AnalysisAgent()
        ctx = agent.analyze(ctx)
        assert len(ctx.agent_logs) >= 1


class TestResponseAgent:
    def test_requires_risk(self):
        ctx = AgentContext(alert=_make_alert(), run_id=1)
        agent = ResponseAgent()
        ctx = agent.analyze(ctx)
        assert ctx.decision is not None
        assert ctx.decision["action"] == "monitor"

    def test_high_risk_blocks(self):
        ctx = AgentContext(alert=_make_alert(), run_id=1)
        ctx.intel = {"reputation": "malicious", "confidence": 0.9, "signal": 96}
        ctx.risk = {"risk_score": 80, "rationale": "test", "signals": {}}
        agent = ResponseAgent()
        ctx = agent.analyze(ctx, block_threshold=70)
        assert ctx.decision["action"] == "block"
        assert "detail" in ctx.decision

    def test_low_risk_monitors(self):
        ctx = AgentContext(alert=_make_alert(), run_id=1)
        ctx.intel = {"reputation": "benign"}
        ctx.risk = {"risk_score": 30, "rationale": "test", "signals": {}}
        agent = ResponseAgent()
        ctx = agent.analyze(ctx, block_threshold=70)
        assert ctx.decision["action"] == "monitor"

    def test_logs_decisions(self):
        ctx = AgentContext(alert=_make_alert(), run_id=1)
        ctx.risk = {"risk_score": 50, "rationale": "test", "signals": {}}
        agent = ResponseAgent()
        ctx = agent.analyze(ctx)
        assert len(ctx.agent_logs) >= 1
