"""Response execution node - handles blocking, notifications, and reporting."""

import logging
from datetime import datetime, timezone

from ..state import SOARState
from ...ai import report_generator
from ...integrations import firewall, notify_email, notify_slack
from ... import settings as settings_mod
from ... import storage

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_response(state: SOARState) -> dict:
    """Execute response actions based on risk assessment."""
    alert = state["alert"]
    risk = state.get("risk", {"risk_score": 0})
    intel = state.get("intel", {})
    run_id = state["run_id"]
    threshold = settings_mod.settings.risk_block_threshold

    decision = {"action": "monitor"}

    # Firewall blocking
    if risk["risk_score"] >= threshold:
        step = storage.create_step(run_id, "lg_firewall_block", "running")
        try:
            action_detail = firewall.block(alert["ip"], risk, settings_mod.settings.simulated_latency_ms)
            decision = {"action": "block", "detail": action_detail}
            storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=action_detail)
        except Exception as e:
            logger.warning("Firewall block failed: %s", e)
            storage.update_step(step["id"], status="failed", finished_at=_utc_now(),
                                detail={"error": str(e)})
    else:
        step = storage.create_step(run_id, "lg_firewall_block", "skipped")
        storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                            detail={"reason": f"风险 {risk['risk_score']} < 阈值 {threshold}"})

    # Email notification
    step = storage.create_step(run_id, "lg_notify_email", "running")
    try:
        if risk["risk_score"] >= threshold:
            result = notify_email.send_alert_email(alert, risk, decision)
            status = "completed" if result else "skipped"
            storage.update_step(step["id"], status=status, finished_at=_utc_now(),
                                detail=result or {"reason": "SMTP 未配置"})
        else:
            storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                detail={"reason": "风险低于通知阈值"})
    except Exception as e:
        storage.update_step(step["id"], status="failed", finished_at=_utc_now(),
                            detail={"error": str(e)})

    # Slack notification
    step = storage.create_step(run_id, "lg_notify_slack", "running")
    try:
        result = notify_slack.send_slack_alert(alert, risk, decision)
        status = "completed" if result else "skipped"
        storage.update_step(step["id"], status=status, finished_at=_utc_now(),
                            detail=result or {"reason": "Slack 未配置"})
    except Exception as e:
        storage.update_step(step["id"], status="failed", finished_at=_utc_now(),
                            detail={"error": str(e)})

    # Report generation
    step = storage.create_step(run_id, "lg_report", "running")
    report = None
    try:
        report = report_generator.generate_report(alert, intel, risk, decision)
        storage.update_step(step["id"], status="completed" if report else "skipped",
                            finished_at=_utc_now(),
                            detail={"report": report} if report else {"reason": "LLM unavailable"})
    except Exception as e:
        storage.update_step(step["id"], status="failed", finished_at=_utc_now(),
                            detail={"error": str(e)})

    path = state.get("execution_path", [])
    path.append("execute_response")

    return {
        "decision": decision,
        "report": report,
        "execution_path": path,
    }
