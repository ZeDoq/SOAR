"""
=====  分析 Agent  =====

负责风险评估和 AI 分析。
包装 risk_assessor.score + analyzer.analyze + knowledge_base。
"""

from .base import BaseAgent
from .context import AgentContext
from ..ai import analyzer, knowledge_base
from ..integrations import risk_assessor
from .. import settings as settings_mod


class AnalysisAgent(BaseAgent):
    name = "analysis"

    def analyze(self, ctx: AgentContext) -> AgentContext:
        if not ctx.intel:
            self._log_decision(ctx, "无威胁情报数据，跳过分析")
            ctx.risk = {"risk_score": 0, "rationale": "无情报数据", "signals": {}}
            return ctx

        latency = settings_mod.settings.simulated_latency_ms

        # 规则引擎风险评估
        risk = risk_assessor.score(ctx.alert, ctx.intel, latency)
        ctx.risk = risk
        self._log_decision(ctx,
                           f"风险评分: {risk['risk_score']}/100 - {risk['rationale']}",
                           {"risk_score": risk["risk_score"]})

        # AI 增强分析
        try:
            context = knowledge_base.get_context_for_alert(ctx.alert)
            ai_result = analyzer.analyze(ctx.alert, ctx.intel, context)
            if ai_result:
                ai_risk = analyzer.compute_ai_risk_score(ai_result)
                ctx.ai_result = ai_result

                if ai_result.get("confidence", 0) > 0.6:
                    ctx.risk["risk_score"] = ai_risk
                    ctx.risk["ai_analysis"] = ai_result
                    ctx.risk["rationale"] = ai_result.get("reasoning", risk["rationale"])
                    self._log_decision(ctx,
                                       f"AI 分析置信度 > 0.6，风险评分更新为 {ai_risk}",
                                       {"ai_risk": ai_risk, "confidence": ai_result.get("confidence")})
                else:
                    ctx.risk["ai_analysis"] = ai_result
                    self._log_decision(ctx,
                                       f"AI 分析置信度 {ai_result.get('confidence', 0):.2f} <= 0.6，保留规则评分")
            else:
                self._log_decision(ctx, "LLM 不可用，使用规则引擎评分")
        except Exception as e:
            self._log_decision(ctx, f"AI 分析失败: {e}")

        return ctx
