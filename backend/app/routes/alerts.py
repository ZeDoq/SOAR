"""
=====  告警 API 路由  =====

提供告警（Alert）的 RESTful API 接口：
  - POST /alerts      → 接收新告警（告警接收器）
  - GET  /alerts      → 获取告警列表
  - GET  /alerts/{id}  → 获取告警详情

这是 SOAR 系统的"入口"，安全设备/传感器通过此接口上报异常事件。
"""

from fastapi import APIRouter, HTTPException

from ..models import AlertCreate
from ..storage import create_alert, get_alert, list_alerts

# 创建路由实例，所有告警接口以 /alerts 为前缀
router = APIRouter(prefix="/alerts", tags=["alerts"])


def _model_to_dict(model: AlertCreate) -> dict:
    """
    Pydantic v1/v2 兼容转换函数。

    Pydantic v2 使用 model_dump()，v1 使用 dict()，
    此函数统一调用方式，兼容不同环境。
    """
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


@router.post("")
def ingest_alert(alert: AlertCreate) -> dict:
    """
    接收并存储新告警。

    这是 SOAR 管道的数据入口。安全传感器或 SIEM 系统将检测到的
    异常事件以告警形式发送到此接口，系统将其持久化到数据库，
    等待用户触发安全响应剧本。

    请求示例：
        POST /alerts
        {
            "ip": "185.199.109.153",
            "source": "sensor-alpha",
            "description": "Repeated login failures from new ASN",
            "tags": ["auth", "bruteforce"]
        }

    Args:
        alert: 告警数据，包含 IP、来源、描述、标签等信息

    Returns:
        包含新告警完整信息的响应
    """
    record = create_alert(_model_to_dict(alert))
    return {"alert": record}


@router.get("")
def get_alerts() -> dict:
    """
    获取所有告警列表。

    返回系统中存储的全部告警记录，按时间倒序排列。
    前端页面使用此接口展示告警列表。
    """
    return {"alerts": list_alerts()}


@router.get("/{alert_id}")
def get_alert_by_id(alert_id: int) -> dict:
    """
    根据 ID 获取单条告警详情。

    Args:
        alert_id: 告警 ID

    Returns:
        告警详情

    Raises:
        404: 告警不存在
    """
    record = get_alert(alert_id)
    if not record:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert": record}