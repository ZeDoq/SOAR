"""
=====  自适应编排器  =====

根据告警特征自动选择 Playbook 模板，使用多 Agent 系统执行。
与经典编排器（orchestrator.py）并存，通过 mode 参数切换。
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .context import AgentContext
from .intelligence_agent import IntelligenceAgent
from .analysis_agent import AnalysisAgent
from .response_agent import ResponseAgent
from .playbook_selector import select_playbook
from .. import settings as settings_mod
from .. import storage

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_adaptive_playbook(run_id: int) -> None:
    """
    执行自适应 Playbook。

    流程：
    1. 加载告警，选择模板
    2. 依次执行 IntelligenceAgent → AnalysisAgent → ResponseAgent
    3. 根据模板决定跳过哪些步骤
    4. 存储步骤与经典编排器兼容（8 步同名）
    """
    run = storage.get_run(run_id)
    if not run:
        return

    alert = storage.get_alert(run["alert_id"])
    if not alert:
        storage.update_run(run_id, status="failed", finished_at=_utc_now())
        return

    storage.update_run(run_id, status="running", started_at=_utc_now())

    template = select_playbook(alert)
    logger.info("自适应 Playbook: 选择 '%s'（run %d）", template["template_name"], run_id)

    ctx = AgentContext(alert=alert, run_id=run_id)

    try:
        # ---- Step 1: 威胁情报（始终执行）----
        step = storage.create_step(run_id, "threat_intel", "running")
        intel_agent = IntelligenceAgent()
        ctx = intel_agent.analyze(ctx)
        storage.update_step(step["id"], status="completed",
                            finished_at=_utc_now(), detail=ctx.intel)

        # 侦察步骤
        step = storage.create_step(run_id, "network_recon", "running")
        if template.get("skip_recon"):
            storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                detail={"reason": f"模板 '{template['template_name']}' 跳过侦察"})
        elif ctx.recon_result:
            storage.update_step(step["id"], status="completed",
                                finished_at=_utc_now(), detail=ctx.recon_result)
        else:
            storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                detail={"reason": "侦察无结果"})

        # ---- Step 2: 分析（条件执行）----
        if "analysis" in template["steps"]:
            step = storage.create_step(run_id, "risk_assessment", "running")
            analysis_agent = AnalysisAgent()
            ctx = analysis_agent.analyze(ctx)
            storage.update_step(step["id"], status="completed",
                                finished_at=_utc_now(), detail=ctx.risk)

            step = storage.create_step(run_id, "ai_analysis", "running")
            if ctx.ai_result:
                storage.update_step(step["id"], status="completed",
                                    finished_at=_utc_now(), detail=ctx.ai_result)
            else:
                storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                    detail={"reason": "LLM 不可用"})
        else:
            for name in ["risk_assessment", "ai_analysis"]:
                step = storage.create_step(run_id, name, "skipped")
                storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                    detail={"reason": "模板未包含此步骤"})

        # ---- Step 3: 响应 ----
        response_agent = ResponseAgent()
        ctx = response_agent.analyze(
            ctx, block_threshold=template.get("risk_block_threshold", 70))

        # 防火墙步骤
        step = storage.create_step(run_id, "firewall_block", "running")
        if "firewall_block" in template["steps"]:
            if ctx.decision and ctx.decision.get("action") == "block":
                storage.update_step(step["id"], status="completed",
                                    finished_at=_utc_now(), detail=ctx.decision.get("detail"))
            else:
                storage.update_step(step["id"], status="skipped",
                                    finished_at=_utc_now(), detail={"action": "monitor"})
        else:
            storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                detail={"reason": "模板未包含此步骤"})

        # 通知步骤
        for notify_name in ["notify_email", "notify_slack"]:
            step = storage.create_step(run_id, notify_name, "running")
            if notify_name in template["steps"]:
                storage.update_step(step["id"], status="completed",
                                    finished_at=_utc_now(), detail={})
            else:
                storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                    detail={"reason": "模板未包含此步骤"})

        # 报告生成
        step = storage.create_step(run_id, "report_generation", "running")
        if "report_generation" in template["steps"] and ctx.report:
            storage.update_step(step["id"], status="completed",
                                finished_at=_utc_now(), detail={"report": ctx.report})
        else:
            storage.update_step(step["id"], status="skipped", finished_at=_utc_now(),
                                detail={"reason": "模板未包含或 LLM 不可用"})

        # ---- 最终状态 ----
        decision = ctx.decision or {"action": "monitor"}
        decision["template"] = template["template_name"]
        decision["agent_reasoning"] = ctx.agent_logs
        risk_score = ctx.risk.get("risk_score", 0) if ctx.risk else 0

        storage.update_run(
            run_id, status="completed", finished_at=_utc_now(),
            risk_score=risk_score, decision=decision,
        )
        logger.info("自适应 Playbook 完成: run %d, risk=%d, action=%s, template=%s",
                     run_id, risk_score, decision["action"], template["template_name"])

    except Exception as exc:
        logger.error("自适应 Playbook 失败 (run %d): %s", run_id, exc)
        storage.update_run(run_id, status="failed", finished_at=_utc_now(), decision=str(exc))
