"""反馈与记忆 API 路由（需认证）。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..routes.auth import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    feedback: str  # confirm | false_positive | false_negative | override
    reason: Optional[str] = ""


@router.post("/{run_id}")
def submit_feedback(run_id: int, request: FeedbackRequest,
                    user: dict = Depends(get_current_user)) -> dict:
    """提交分析师对运行结果的反馈。"""
    from ..memory.feedback_loop import submit_feedback as do_submit
    try:
        result = do_submit(run_id, request.feedback, request.reason or "")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
def feedback_stats(user: dict = Depends(get_current_user)) -> dict:
    """获取反馈统计信息。"""
    from ..memory.feedback_loop import get_feedback_stats
    return get_feedback_stats()


@router.get("/run/{run_id}")
def get_run_feedback(run_id: int, user: dict = Depends(get_current_user)) -> dict:
    """获取指定运行的反馈。"""
    from ..memory.feedback_loop import get_feedback_for_run
    fb = get_feedback_for_run(run_id)
    if not fb:
        return {"feedback": None}
    return {"feedback": fb}


@router.get("/memory/similar/{alert_id}")
def get_similar_incidents(alert_id: int,
                          user: dict = Depends(get_current_user)) -> dict:
    """获取与指定告警相似的历史事件。"""
    from .. import storage
    from ..memory.episodic_memory import search_similar_incidents

    alert = storage.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    similar = search_similar_incidents(alert, top_k=5)
    return {"similar_incidents": similar}


@router.get("/memory/stats")
def memory_stats(user: dict = Depends(get_current_user)) -> dict:
    """获取记忆统计信息。"""
    from ..memory.episodic_memory import get_episode_stats
    return get_episode_stats()
