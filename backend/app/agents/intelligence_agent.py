"""
=====  情报 Agent  =====

负责威胁情报查询和网络侦察。
包装 threat_intel.lookup + recon.whois_lookup/dns_lookup。
"""

from .base import BaseAgent
from .context import AgentContext
from ..integrations import recon, threat_intel
from .. import settings as settings_mod


class IntelligenceAgent(BaseAgent):
    name = "intelligence"

    def analyze(self, ctx: AgentContext) -> AgentContext:
        ip = ctx.alert.get("ip", "unknown")
        latency = settings_mod.settings.simulated_latency_ms

        # 威胁情报查询
        intel = threat_intel.lookup(ip, latency)
        ctx.intel = intel
        self._log_decision(ctx,
                           f"威胁情报: reputation={intel.get('reputation')}, "
                           f"confidence={intel.get('confidence')}, "
                           f"sources={intel.get('sources')}",
                           {"ip": ip, "reputation": intel.get("reputation")})

        # 网络侦察
        recon_result = {}
        whois_data = recon.whois_lookup(ip)
        if whois_data:
            recon_result["whois"] = whois_data
            self._log_decision(ctx, f"WHOIS 查询成功: {ip}")
        dns_data = recon.dns_lookup(ip)
        if dns_data:
            recon_result["dns"] = dns_data
            self._log_decision(ctx, f"DNS 查询成功: {ip}")

        ctx.recon_result = recon_result if recon_result else None
        if not recon_result:
            self._log_decision(ctx, "网络侦察无结果或库不可用")

        return ctx
