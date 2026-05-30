"""
=====  响应 Agent  =====

负责执行响应动作（防火墙阻断、通知、报告生成）。
包装 firewall + notify_email + notify_slack + report_generator。
"""

from .base import BaseAgent
from .context import AgentContext
from ..ai import report_generator
from ..integrations import firewall, notify_email, notify_slack
from .. import settings as settings_mod


class ResponseAgent(BaseAgent):
    name = "response"

    def analyze(self, ctx: AgentContext, block_threshold: int = None) -> AgentContext:
        """
        执行响应动作。

        Args:
            ctx: 共享上下文（需已填充 risk）
            block_threshold: 阻断阈值（覆盖默认配置）
        """
        if not ctx.risk:
            self._log_decision(ctx, "无风险数据，跳过响应")
            ctx.decision = {"action": "monitor"}
            return ctx

        threshold = block_threshold or settings_mod.settings.risk_block_threshold
        risk_score = ctx.risk.get("risk_score", 0)
        latency = settings_mod.settings.simulated_latency_ms

        # 防火墙阻断决策
        if risk_score >= threshold:
            action_detail = firewall.block(ctx.alert.get("ip", ""), ctx.risk, latency)
            ctx.decision = {"action": "block", "detail": action_detail}
            self._log_decision(ctx,
                               f"风险 {risk_score} >= 阈值 {threshold}，执行阻断",
                               {"ip": ctx.alert.get("ip"), "ticket": action_detail.get("ticket")})

            # 高风险通知
            email_result = notify_email.send_alert_email(ctx.alert, ctx.risk, ctx.decision)
            if email_result:
                self._log_decision(ctx, "邮件通知已发送")
        else:
            ctx.decision = {"action": "monitor"}
            self._log_decision(ctx,
                               f"风险 {risk_score} < 阈值 {threshold}，继续监控")

        # Slack 通知（始终尝试）
        slack_result = notify_slack.send_slack_alert(ctx.alert, ctx.risk, ctx.decision)
        if slack_result:
            self._log_decision(ctx, "Slack 通知已发送")

        # 报告生成
        try:
            report = report_generator.generate_report(ctx.alert, ctx.intel, ctx.risk, ctx.decision)
            if report:
                ctx.report = report
                self._log_decision(ctx, "事件报告已生成")
            else:
                self._log_decision(ctx, "LLM 不可用，跳过报告生成")
        except Exception as e:
            self._log_decision(ctx, f"报告生成失败: {e}")

        return ctx
