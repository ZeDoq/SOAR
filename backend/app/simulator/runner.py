"""
=====  攻击模拟器执行器  =====

创建真实告警并可选触发 Playbook 执行。
支持中英文告警描述。
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .. import storage

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _localize_alert(alert_data: dict, lang: str) -> dict:
    """根据语言选择告警描述。"""
    data = dict(alert_data)
    if lang == "zh" and data.get("description_zh"):
        data["description"] = data["description_zh"]
    data.pop("description_zh", None)
    return data


def run_scenario(scenario_name: str, auto_run: bool = False, lang: str = "en") -> Dict[str, Any]:
    """
    执行模拟场景。

    Args:
        scenario_name: 场景名称
        auto_run: 是否自动创建 run 记录
        lang: 语言 ("zh" 或 "en")
    """
    from .scenarios import get_scenario

    scenario = get_scenario(scenario_name)
    if not scenario:
        return {"error": f"未知场景: {scenario_name}"}

    created_alerts = []
    created_runs = []

    for alert_data in scenario["alerts"]:
        data = _localize_alert(alert_data, lang)
        if not data.get("observed_at"):
            data["observed_at"] = _utc_now()

        record = storage.create_alert(data)
        created_alerts.append({"id": record["id"], "ip": record["ip"]})

        if auto_run:
            run = storage.create_run(record["id"], status="queued")
            created_runs.append({"id": run["id"], "alert_id": record["id"]})

    result = {
        "scenario": scenario_name,
        "name": scenario["name"],
        "description": scenario["description"],
        "alerts_created": created_alerts,
        "expected_outcome": scenario["expected_outcome"],
    }

    if auto_run:
        result["runs_created"] = created_runs

    logger.info("模拟 '%s': 创建 %d 条告警", scenario_name, len(created_alerts))
    return result


def run_all_scenarios(auto_run: bool = False, lang: str = "en") -> Dict[str, Any]:
    """执行所有场景。"""
    from .scenarios import get_scenario_names

    results = {}
    for name in get_scenario_names():
        results[name] = run_scenario(name, auto_run=auto_run, lang=lang)

    return {"scenarios_run": len(results), "results": results}
