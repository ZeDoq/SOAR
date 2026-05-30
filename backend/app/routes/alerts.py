"""
=====  告警 API 路由  =====

POST /alerts 保持开放（传感器推数据），其他端点需要认证。
"""

from fastapi import APIRouter, Depends, HTTPException

from ..models import AlertCreate
from ..routes.auth import get_current_user
from ..storage import create_alert, get_alert, list_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _model_to_dict(model: AlertCreate) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


@router.post("")
def ingest_alert(alert: AlertCreate) -> dict:
    """接收新告警（传感器接口，无需认证）。"""
    record = create_alert(_model_to_dict(alert))
    return {"alert": record}


@router.get("")
def get_alerts(user: dict = Depends(get_current_user)) -> dict:
    """获取告警列表（需认证）。"""
    return {"alerts": list_alerts()}


@router.get("/{alert_id}")
def get_alert_by_id(alert_id: int, user: dict = Depends(get_current_user)) -> dict:
    """获取告警详情（需认证）。"""
    record = get_alert(alert_id)
    if not record:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert": record}
