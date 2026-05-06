"""
=====  剧本执行 API 路由  =====

提供剧本运行（Run）的 RESTful API 接口：
  - POST /runs       → 触发针对某个告警的安全响应剧本
  - GET  /runs       → 获取所有运行记录
  - GET  /runs/{id}  → 获取运行详情（含步骤日志）

核心设计说明：
  使用 FastAPI 的 BackgroundTasks 实现异步执行。
  POST /runs 立即返回 "queued" 状态，实际 playbook 在后台运行，
  前端通过轮询 GET /runs/{id} 获取实时进度。
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..agents.orchestrator import execute_playbook
from ..models import RunRequest
from ..storage import create_run, get_run, list_runs, list_steps

# 创建路由实例，所有运行记录接口以 /runs 为前缀
router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("")
def start_run(request: RunRequest, background_tasks: BackgroundTasks) -> dict:
    """
    触发安全响应剧本执行。

    这是 SOAR 系统的"开关"。用户选择一条告警后调用此接口，
    系统会：
    1. 创建一条运行记录（状态：queued）
    2. 立即返回运行记录 ID
    3. 在后台异步执行完整的安全响应剧本

    后台执行流程：execute_playbook()
      ├── Step 1: 威胁情报查询（Threat Intelligence）
      ├── Step 2: 风险评估（Risk Assessment）
      └── Step 3: 决策执行（联动防火墙封禁 or 仅监控）

    请求示例：
        POST /runs
        {
            "alert_id": 1
        }

    Args:
        request: 包含 alert_id 的请求体
        background_tasks: FastAPI 后台任务（由框架自动注入）

    Returns:
        包含新运行记录信息的响应（status: "queued"）
    """
    run = create_run(request.alert_id, status="queued")
    # 将剧本执行函数注册为后台任务，不阻塞 HTTP 响应
    background_tasks.add_task(execute_playbook, run["id"])
    return {"run": run}


@router.get("")
def get_runs() -> dict:
    """
    获取所有剧本运行记录。

    返回历史执行记录列表，包括每次运行的状态、风险评分和最终决策。
    前端使用此接口展示运行历史。
    """
    return {"runs": list_runs()}


@router.get("/{run_id}")
def get_run_detail(run_id: int) -> dict:
    """
    获取单次运行的详细信息，包括完整的步骤执行日志。

    前端通过轮询此接口（如每 1-2 秒）获取剧本执行进度。

    Args:
        run_id: 运行记录 ID

    Returns:
        包含运行信息和步骤列表的响应：
        {
            "run": { 运行信息 },
            "steps": [
                { "name": "threat_intel", "status": "completed", ... },
                { "name": "risk_assessment", "status": "completed", ... },
                { "name": "firewall_block", "status": "skipped", ... }
            ]
        }

    Raises:
        404: 运行记录不存在
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    steps = list_steps(run_id)
    return {"run": run, "steps": steps}