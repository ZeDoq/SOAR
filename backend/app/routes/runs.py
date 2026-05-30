"""剧本执行 API 路由（需认证）。"""

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from ..agents.orchestrator import execute_playbook
from ..routes.auth import get_current_user
from ..storage import create_run, get_run, list_runs, list_steps

router = APIRouter(prefix="/runs", tags=["runs"])


class RunRequest(BaseModel):
    alert_id: int
    mode: Literal["classic", "adaptive"] = "classic"


@router.post("")
def start_run(request: RunRequest, background_tasks: BackgroundTasks,
              user: dict = Depends(get_current_user)) -> dict:
    """触发安全响应剧本执行（需认证）。"""
    run = create_run(request.alert_id, status="queued")
    if request.mode == "adaptive":
        from ..agents.adaptive_orchestrator import execute_adaptive_playbook
        background_tasks.add_task(execute_adaptive_playbook, run["id"])
    else:
        background_tasks.add_task(execute_playbook, run["id"])
    return {"run": run}


@router.get("")
def get_runs(user: dict = Depends(get_current_user)) -> dict:
    """获取所有执行记录（需认证）。"""
    return {"runs": list_runs()}


@router.get("/{run_id}")
def get_run_detail(run_id: int, user: dict = Depends(get_current_user)) -> dict:
    """获取执行详情（需认证）。"""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    steps = list_steps(run_id)
    return {"run": run, "steps": steps}
