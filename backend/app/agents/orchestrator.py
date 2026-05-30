"""
Agent Orchestrator - now with AI-powered analysis.

Flow: alert → threat intel → AI analysis + risk assessment → decision
Falls back to rule-based scoring when LLM is unavailable.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from ..ai import analyzer, knowledge_base, report_generator
from ..integrations import firewall, notify_email, notify_slack, recon, risk_assessor, threat_intel
from .. import settings as settings_mod
from .. import storage

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_playbook(run_id: int) -> None:
    """Execute security response playbook with AI-enhanced analysis."""
    run = storage.get_run(run_id)
    if not run:
        return

    alert = storage.get_alert(run["alert_id"])
    if not alert:
        storage.update_run(run_id, status="failed", finished_at=_utc_now())
        return

    storage.update_run(run_id, status="running", started_at=_utc_now())
    logger.info("Starting playbook for run %d, IP: %s", run_id, alert["ip"])

    try:
        # Step 1: Threat Intelligence
        step = storage.create_step(run_id, "threat_intel", "running")
        intel = threat_intel.lookup(alert["ip"], settings_mod.settings.simulated_latency_ms)
        storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=intel)

        # Step 2: Risk Assessment (rule-based)
        step = storage.create_step(run_id, "risk_assessment", "running")
        risk = risk_assessor.score(alert, intel, settings_mod.settings.simulated_latency_ms)
        storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=risk)

        # Step 2.5: AI Analysis (enhancement layer)
        ai_result = None
        step = storage.create_step(run_id, "ai_analysis", "running")
        try:
            context = knowledge_base.get_context_for_alert(alert)
            ai_result = analyzer.analyze(alert, intel, context)
            if ai_result:
                ai_risk = analyzer.compute_ai_risk_score(ai_result)
                # Blend: use AI score if confidence > 0.6, otherwise keep rule-based
                if ai_result.get("confidence", 0) > 0.6:
                    risk["risk_score"] = ai_risk
                    risk["ai_analysis"] = ai_result
                    risk["rationale"] = ai_result.get("reasoning", risk["rationale"])
                else:
                    risk["ai_analysis"] = ai_result
                storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=ai_result)
            else:
                storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                    detail={"reason": "LLM unavailable, using rule-based scoring"})
        except Exception as e:
            logger.warning("AI analysis failed: %s", e)
            storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                detail={"reason": str(e)})

        # Step 2.6: Network Reconnaissance (enrichment)
        step = storage.create_step(run_id, "network_recon", "running")
        try:
            recon_result: Dict[str, Any] = {}
            whois_data = recon.whois_lookup(alert["ip"])
            if whois_data:
                recon_result["whois"] = whois_data
            dns_data = recon.dns_lookup(alert["ip"])
            if dns_data:
                recon_result["dns"] = dns_data
            if recon_result:
                storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=recon_result)
            else:
                storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                    detail={"reason": "侦察库不可用或查询失败"})
        except Exception as e:
            logger.warning("Network recon failed: %s", e)
            storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                detail={"reason": str(e)})

        # Step 3: Decision & Action
        decision = {"action": "monitor"}
        if risk["risk_score"] >= settings_mod.settings.risk_block_threshold:
            step = storage.create_step(run_id, "firewall_block", "running")
            action_detail = firewall.block(alert["ip"], risk, settings_mod.settings.simulated_latency_ms)
            storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=action_detail)
            decision = {"action": "block", "detail": action_detail}
        else:
            step = storage.create_step(run_id, "firewall_block", "skipped")
            storage.update_step(step["id"], status="skipped", finished_at=_utc_now(), detail={"action": "monitor"})
            decision = {"action": "monitor"}

        # Step 3.5: Email Notification (high-risk events)
        step = storage.create_step(run_id, "notify_email", "running")
        try:
            if risk["risk_score"] >= settings_mod.settings.risk_block_threshold:
                email_result = notify_email.send_alert_email(alert, risk, decision)
                if email_result:
                    storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=email_result)
                else:
                    storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                        detail={"reason": "SMTP 未配置或发送失败"})
            else:
                storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                    detail={"reason": "风险低于通知阈值"})
        except Exception as e:
            logger.warning("Email notification failed: %s", e)
            storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                detail={"reason": str(e)})

        # Step 3.6: Slack Notification
        step = storage.create_step(run_id, "notify_slack", "running")
        try:
            slack_result = notify_slack.send_slack_alert(alert, risk, decision)
            if slack_result:
                storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=slack_result)
            else:
                storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                    detail={"reason": "Slack Webhook 未配置或发送失败"})
        except Exception as e:
            logger.warning("Slack notification failed: %s", e)
            storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                detail={"reason": str(e)})

        # Step 4: Auto Report Generation
        step = storage.create_step(run_id, "report_generation", "running")
        try:
            report = report_generator.generate_report(alert, intel, risk, decision)
            if report:
                storage.update_step(step["id"], status="completed", finished_at=_utc_now(),
                                    detail={"report": report})
            else:
                storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                    detail={"reason": "LLM unavailable"})
        except Exception as e:
            logger.warning("Report generation failed: %s", e)
            storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                detail={"reason": str(e)})

        storage.update_run(
            run_id, status="completed", finished_at=_utc_now(),
            risk_score=risk["risk_score"], decision=decision,
        )
        logger.info("Playbook completed for run %d, risk=%d, action=%s",
                     run_id, risk["risk_score"], decision["action"])

    except Exception as exc:
        logger.error("Playbook failed for run %d: %s", run_id, exc)
        storage.update_run(run_id, status="failed", finished_at=_utc_now(), decision=str(exc))
