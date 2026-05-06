"""
=====  Agent 编排器 =====

这是整个 SOAR 系统的"大脑"——Agent 编排器（Orchestrator）。

核心思路：
  利用 Agent 框架，模拟一个自动化安全运营（SOAR）剧本。
  Agent 不是单一的 AI 模型，而是一个**编排器**，它协调多个
  安全工具/服务，按照预定义的 playbook 步骤执行自动化响应。

Playbook 流程：
  告警输入 ──▶ 威胁情报查询 ──▶ 风险评估 ──▶ 决策执行
                                                    │
                              ┌─────────────────────┤
                              ▼                     ▼
                          阻断(block)            监控(monitor)
                        (联动防火墙封禁IP)      (记录日志继续观察)

状态机流转：
  queued ──▶ running ──▶ completed
                    └──▶ failed (异常处理)
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any

from ..integrations import firewall, risk_assessor, threat_intel
from ..settings import settings
from .. import storage


def _utc_now() -> str:
    """获取当前 UTC 时间的 ISO 8601 格式字符串"""
    return datetime.now(timezone.utc).isoformat()


def execute_playbook(run_id: int) -> None:
    """
    执行安全响应剧本（Playbook）。

    这是整个系统的核心函数，模拟了安全分析师处理告警的完整流程。
    该函数由 FastAPI 的 BackgroundTasks 异步调用，不会阻塞 API 响应。

    执行步骤：
    1. 加载告警上下文：根据 run_id 获取关联的告警信息
    2. Step 1 - 威胁情报查询（Threat Intelligence Lookup）：
       查询目标 IP 的威胁情报，获取信誉评分和置信度
    3. Step 2 - 风险评估（Risk Assessment）：
       结合告警信息和威胁情报，计算综合风险评分
    4. Step 3 - 决策执行（Decision & Action）：
       根据风险评分决定是否封禁 IP（联动防火墙）

    Args:
        run_id: 运行记录 ID，用于追踪本次执行的全过程
    """
    # ---- 加载上下文 ----
    run = storage.get_run(run_id)
    if not run:
        return  # 运行记录不存在，直接返回

    alert = storage.get_alert(run["alert_id"])
    if not alert:
        # 告警不存在，标记为失败
        storage.update_run(run_id, status="failed", finished_at=_utc_now())
        return

    # 将状态更新为"运行中"
    storage.update_run(run_id, status="running", started_at=_utc_now())

    try:
        # ==========================================
        # Step 1: 威胁情报查询（Threat Intelligence）
        # ==========================================
        # Agent 调用威胁情报服务，查询目标 IP 的信誉信息
        # 模拟真实场景中查询 VirusTotal、AlienVault OTX 等情报源
        step = storage.create_step(run_id, "threat_intel", "running")
        intel = threat_intel.lookup(alert["ip"], settings.simulated_latency_ms)
        storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=intel)

        # ==========================================
        # Step 2: 风险评估（Risk Assessment）
        # ==========================================
        # Agent 结合告警上下文和威胁情报，计算综合风险评分
        # 模拟安全分析师的经验判断过程
        step = storage.create_step(run_id, "risk_assessment", "running")
        risk = risk_assessor.score(alert, intel, settings.simulated_latency_ms)
        storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=risk)

        # ==========================================
        # Step 3: 决策执行（Decision & Action）
        # ==========================================
        # Agent 根据风险评分做出决策：
        # - 高风险（>= threshold）→ 自动封禁 IP（联动防火墙）
        # - 低风险（< threshold）→ 仅监控，记录日志
        decision = {"action": "monitor"}
        action_detail: Dict[str, Any] = {"action": "monitor"}

        if risk["risk_score"] >= settings.risk_block_threshold:
            # ---- 高风险：联动防火墙封禁 IP ----
            # 模拟调用防火墙 API 添加封禁规则
            step = storage.create_step(run_id, "firewall_block", "running")
            action_detail = firewall.block(alert["ip"], risk, settings.simulated_latency_ms)
            storage.update_step(
                step["id"], status="completed", finished_at=_utc_now(), detail=action_detail
            )
            decision = {"action": "block", "detail": action_detail}
        else:
            # ---- 低风险：跳过封禁，仅监控 ----
            step = storage.create_step(run_id, "firewall_block", "skipped")
            storage.update_step(
                step["id"], status="skipped", finished_at=_utc_now(), detail=action_detail
            )
            decision = {"action": "monitor", "detail": action_detail}

        # ---- 更新运行结果 ----
        storage.update_run(
            run_id,
            status="completed",
            finished_at=_utc_now(),
            risk_score=risk["risk_score"],
            decision=decision,
        )

    except Exception as exc:
        # ---- 异常处理 ----
        # 任何步骤失败都会将运行标记为 failed
        storage.update_run(run_id, status="failed", finished_at=_utc_now(), decision=str(exc))