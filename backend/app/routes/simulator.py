"""攻击模拟器 API（需认证）。"""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException

from ..agents.orchestrator import execute_playbook
from ..agents.adaptive_orchestrator import execute_adaptive_playbook
from ..routes.auth import get_current_user
from ..simulator import scenarios, runner
from .. import storage

router = APIRouter(prefix="/simulator", tags=["simulator"])


def _get_lang(accept_language: Optional[str] = Header(None)) -> str:
    if accept_language and "zh" in accept_language.lower():
        return "zh"
    return "en"


@router.get("/scenarios")
def list_scenarios(accept_language: Optional[str] = Header(None),
                   user: dict = Depends(get_current_user)) -> dict:
    lang = _get_lang(accept_language)
    result = []
    for name in scenarios.get_scenario_names():
        s = scenarios.get_scenario(name)
        result.append({
            "name": name, "display_name": s["name"], "description": s["description"],
            "alert_count": len(s["alerts"]), "attack_type": s.get("attack_type", "unknown"),
        })
    return {"scenarios": result}


@router.post("/run/{scenario_name}")
def trigger_scenario(
    scenario_name: str, background_tasks: BackgroundTasks,
    auto_run: bool = True, mode: str = "adaptive",
    accept_language: Optional[str] = Header(None),
    user: dict = Depends(get_current_user),
) -> dict:
    lang = _get_lang(accept_language)
    result = runner.run_scenario(scenario_name, auto_run=False, lang=lang)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    if auto_run:
        runs_created = []
        for alert_info in result["alerts_created"]:
            run = storage.create_run(alert_info["id"], status="queued")
            runs_created.append({"id": run["id"], "alert_id": alert_info["id"]})
            if mode == "adaptive":
                background_tasks.add_task(execute_adaptive_playbook, run["id"])
            else:
                background_tasks.add_task(execute_playbook, run["id"])
        result["runs_created"] = runs_created
    return result


@router.post("/run-all")
def trigger_all(
    background_tasks: BackgroundTasks, auto_run: bool = True, mode: str = "adaptive",
    accept_language: Optional[str] = Header(None),
    user: dict = Depends(get_current_user),
) -> dict:
    lang = _get_lang(accept_language)
    result = runner.run_all_scenarios(auto_run=False, lang=lang)
    if auto_run:
        for scenario_result in result["results"].values():
            for alert_info in scenario_result.get("alerts_created", []):
                run = storage.create_run(alert_info["id"], status="queued")
                if mode == "adaptive":
                    background_tasks.add_task(execute_adaptive_playbook, run["id"])
                else:
                    background_tasks.add_task(execute_playbook, run["id"])
    return result
