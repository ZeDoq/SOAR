"""知识库搜索 API（需认证）。"""

from fastapi import APIRouter, Depends

from ..ai import knowledge_base
from ..routes.auth import get_current_user

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search")
def search_knowledge(q: str, top_k: int = 3,
                     user: dict = Depends(get_current_user)) -> dict:
    """搜索安全知识库（需认证）。"""
    if top_k > 20:
        top_k = 20
    results = knowledge_base.search(q, top_k=top_k)
    return {"query": q, "results": results}
