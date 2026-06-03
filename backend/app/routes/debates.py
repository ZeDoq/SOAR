"""辩论系统 API 路由（需认证）。"""

from fastapi import APIRouter, Depends, HTTPException

from ..routes.auth import get_current_user
from .. import storage

router = APIRouter(prefix="/debates", tags=["debates"])


@router.get("")
def list_debates(user: dict = Depends(get_current_user)) -> dict:
    """获取所有辩论记录。"""
    conn = storage._connect()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT * FROM debates ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    debates = []
    for row in rows:
        import json
        debates.append({
            "id": row["id"],
            "run_id": row["run_id"],
            "alert_id": row["alert_id"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "consensus": json.loads(row["consensus"]) if row["consensus"] else {},
            "moderator_verdict": json.loads(row["moderator_verdict"]) if row["moderator_verdict"] else {},
        })
    return {"debates": debates}


@router.get("/{debate_id}")
def get_debate(debate_id: int, user: dict = Depends(get_current_user)) -> dict:
    """获取辩论详情。"""
    import json
    conn = storage._connect()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT * FROM debates WHERE id = ?", (debate_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Debate not found")
    return {
        "debate": {
            "id": row["id"],
            "run_id": row["run_id"],
            "alert_id": row["alert_id"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "rounds": json.loads(row["rounds"]) if row["rounds"] else [],
            "verdicts": json.loads(row["verdicts"]) if row["verdicts"] else [],
            "consensus": json.loads(row["consensus"]) if row["consensus"] else {},
            "moderator_verdict": json.loads(row["moderator_verdict"]) if row["moderator_verdict"] else {},
        }
    }


@router.post("/run/{alert_id}")
def run_debate(alert_id: int, user: dict = Depends(get_current_user)) -> dict:
    """对指定告警执行多 Agent 辩论。"""
    alert = storage.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    from ..integrations import threat_intel
    from .. import settings as settings_mod

    intel = threat_intel.lookup(alert["ip"], settings_mod.settings.simulated_latency_ms)

    from ..agents.debate.debate_engine import run_debate as execute_debate
    transcript = execute_debate(alert, intel)

    return {"debate": transcript}
