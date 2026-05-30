"""知识图谱 API（需认证）。"""

from fastapi import APIRouter, Depends, HTTPException

from ..graph.knowledge_graph import graph
from ..graph.populator import populate_from_database, populate_techniques
from ..routes.auth import get_current_user

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
def get_graph(user: dict = Depends(get_current_user)) -> dict:
    if not graph.available:
        raise HTTPException(status_code=503, detail="图谱不可用")
    return graph.to_json()


@router.get("/related/{node_type}/{node_id}")
def get_related(node_type: str, node_id: str, max_depth: int = 2,
                user: dict = Depends(get_current_user)) -> dict:
    if not graph.available:
        raise HTTPException(status_code=503, detail="图谱不可用")
    if max_depth > 5:
        max_depth = 5
    results = graph.find_related(node_type, node_id, max_depth=max_depth)
    return {"node": f"{node_type}:{node_id}", "related": results}


@router.get("/path")
def get_shortest_path(source_ip: str, target_ip: str,
                      user: dict = Depends(get_current_user)) -> dict:
    if not graph.available:
        raise HTTPException(status_code=503, detail="图谱不可用")
    path = graph.shortest_path(source_ip, target_ip)
    return {"source": source_ip, "target": target_ip, "path": path}


@router.get("/clusters")
def get_clusters(min_size: int = 2, user: dict = Depends(get_current_user)) -> dict:
    if not graph.available:
        raise HTTPException(status_code=503, detail="图谱不可用")
    clusters = graph.detect_clusters(min_cluster_size=min_size)
    return {"clusters": clusters, "count": len(clusters)}


@router.get("/techniques")
def get_technique_stats(user: dict = Depends(get_current_user)) -> dict:
    if not graph.available:
        raise HTTPException(status_code=503, detail="图谱不可用")
    stats = graph.get_technique_frequency()
    return {"techniques": stats}


@router.post("/rebuild")
def rebuild_graph(user: dict = Depends(get_current_user)) -> dict:
    if not graph.available:
        raise HTTPException(status_code=503, detail="图谱不可用")
    graph.clear()
    tech_count = populate_techniques(graph)
    alert_count = populate_from_database(graph)
    return {"status": "rebuilt", "techniques_loaded": tech_count, "alerts_ingested": alert_count}
