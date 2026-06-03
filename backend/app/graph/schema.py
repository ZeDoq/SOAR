"""
=====  知识图谱 Schema 定义  =====

定义图中节点类型、边类型及其属性规范。
"""

# ---- 节点类型 ----
NODE_IP = "ip"
NODE_DOMAIN = "domain"
NODE_ALERT = "alert"
NODE_TECHNIQUE = "technique"
NODE_RISK_LEVEL = "risk_level"

# ---- 边类型 ----
EDGE_ASSOCIATED_WITH = "associated_with"   # alert <-> ip
EDGE_USES_TECHNIQUE = "uses_technique"     # alert -> technique
EDGE_HAS_RISK = "has_risk"                 # alert -> risk_level
EDGE_CONNECTED_TO = "connected_to"         # ip <-> ip（共享技术或关联告警）
EDGE_RESOLVES_TO = "resolves_to"           # domain -> ip
EDGE_REPORTED_BY = "reported_by"           # alert -> source

# ---- 攻击链相关类型 (Module 5) ----
NODE_ATTACK_CHAIN = "attack_chain"          # 攻击链节点
EDGE_PART_OF_CHAIN = "part_of_chain"       # alert -> chain
EDGE_TEMPORAL_SUCCESSOR = "temporal_successor"  # alert -> alert (时间序列)


def make_node_id(node_type: str, value: str) -> str:
    """生成带类型前缀的节点 ID，避免不同类型之间的冲突。"""
    return f"{node_type}:{value}"
