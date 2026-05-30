"""告警源管理 API（需认证）。"""

from fastapi import APIRouter, Depends, HTTPException

from ..ingestion import manager
from ..routes.auth import get_current_user

router = APIRouter(prefix="/sources", tags=["sources"])

VALID_SOURCES = {"syslog", "wazuh", "suricata"}


@router.get("")
def list_sources(user: dict = Depends(get_current_user)) -> dict:
    return {"sources": manager.get_status()}


@router.post("/{name}/start")
def start(name: str, user: dict = Depends(get_current_user)) -> dict:
    if name not in VALID_SOURCES:
        raise HTTPException(status_code=400, detail=f"未知告警源: {name}")
    result = manager.start_source(name)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("reason", "启动失败"))
    return result


@router.post("/{name}/stop")
def stop(name: str, user: dict = Depends(get_current_user)) -> dict:
    if name not in VALID_SOURCES:
        raise HTTPException(status_code=400, detail=f"未知告警源: {name}")
    return manager.stop_source(name)
