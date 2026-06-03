"""知识库搜索 API（需认证）。"""

from fastapi import APIRouter, Depends

from ..ai import knowledge_base
from ..ai import rag_engine
from ..routes.auth import get_current_user

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search")
def search_knowledge(q: str, top_k: int = 3,
                     user: dict = Depends(get_current_user)) -> dict:
    """搜索安全知识库（需认证）。支持 RAG 语义检索 + 关键词降级。"""
    if top_k > 20:
        top_k = 20
    results = knowledge_base.search(q, top_k=top_k)
    return {"query": q, "results": results}


@router.get("/rag/status")
def rag_status(user: dict = Depends(get_current_user)) -> dict:
    """查询 RAG 引擎状态（文档数量等）。"""
    stats = rag_engine.get_collection_stats()
    return stats


@router.post("/rag/reload")
def rag_reload(user: dict = Depends(get_current_user)) -> dict:
    """重新加载 RAG 知识库数据。"""
    from ..ai.attack_data_loader import load_attack_data
    from ..ai.incident_corpus import load_incident_corpus

    attack_count = load_attack_data(force_reload=True)
    incident_count = load_incident_corpus()
    return {
        "attack_techniques": attack_count,
        "incident_cases": incident_count,
        "total": attack_count + incident_count,
    }


@router.get("/context/{alert_id}")
def get_alert_context(alert_id: int,
                      user: dict = Depends(get_current_user)) -> dict:
    """获取指定告警的 RAG 增强上下文（技术匹配 + 相似事件）。"""
    from .. import storage

    alert = storage.get_alert(alert_id)
    if not alert:
        return {"error": "Alert not found"}

    rich_context = knowledge_base.get_rich_context(alert)
    return rich_context
