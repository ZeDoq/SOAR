"""攻击链 API 路由（需认证）。"""

from fastapi import APIRouter, Depends, HTTPException

from ..routes.auth import get_current_user

router = APIRouter(prefix="/chains", tags=["chains"])


@router.get("")
def list_chains(user: dict = Depends(get_current_user)) -> dict:
    """获取所有检测到的攻击链。"""
    from ..graph.chain_detector import get_all_chains, format_chain_for_display
    chains = get_all_chains()
    return {"chains": [format_chain_for_display(c) for c in chains]}


@router.get("/{ip}")
def get_chain_for_ip(ip: str, user: dict = Depends(get_current_user)) -> dict:
    """获取指定 IP 的攻击链。"""
    from ..graph.chain_detector import get_chain_for_ip, format_chain_for_display
    chain = get_chain_for_ip(ip)
    if not chain:
        raise HTTPException(status_code=404, detail="No attack chain found for this IP")
    return {"chain": format_chain_for_display(chain)}
