"""
=====  风险评估服务（模拟）  =====

在真实 SOAR 系统中，此模块通常是一个复杂的风险评估引擎，
可能结合以下因素进行评分：
  - 威胁情报信誉分
  - 告警类型和严重等级
  - 资产价值（受影响系统的重要性）
  - 历史行为模式
  - MITRE ATT&CK 攻击技术映射

本实现演示了 Agent 如何将多源信息融合为单一风险评分。
"""

import time
from typing import Dict, Any


def score(alert: Dict[str, Any], intel: Dict[str, Any], latency_ms: int) -> Dict[str, Any]:
    """
    计算综合风险评分。

    评分模型（模拟）：
      基础分: 30 （任何可疑活动都有基本风险）
      + 信誉加成: 恶意 +50, 可疑 +25, 良性 +0
      + 描述匹配: 包含 "bruteforce" 关键词 +10
      + 标签匹配: 包含 "vpn" 标签 +5
      最终得分: min(100, 总分)

    评分等级说明：
      0-30:  低风险（Low）—— 记录日志，持续观察
      31-69: 中风险（Medium）—— 提升监控级别
      70-100: 高风险（High）—— 自动阻断

    Args:
        alert: 原始告警信息（包含 description、tags 等）
        intel: 威胁情报查询结果（包含 reputation、signal 等）
        latency_ms: 模拟计算延迟

    Returns:
        评估结果，包含风险评分和决策依据：
        {
            "risk_score": 0-100 的风险评分,
            "rationale": 评分依据说明,
            "signals": 关键信号摘要
        }
    """
    # 模拟计算延迟
    time.sleep(latency_ms / 1000.0)

    # ---- 评分计算 ----
    base = 30  # 基础分：任何可疑活动都有 30 的基线风险

    # 根据威胁情报信誉等级加权
    reputation = intel.get("reputation")
    if reputation == "malicious":
        base += 50      # 恶意 IP → 高风险
    elif reputation == "suspicious":
        base += 25      # 可疑 IP → 中等附加分

    # 根据告警描述中的关键特征加权
    if "bruteforce" in (alert.get("description") or "").lower():
        base += 10      # 暴力破解尝试 → 额外风险

    # 根据告警标签中的关键特征加权
    if "vpn" in " ".join(alert.get("tags", [])).lower():
        base += 5       # VPN 节点 → 可能是代理攻击

    # 确保评分不超过 100
    risk_score = min(100, base)

    return {
        "risk_score": risk_score,
        "rationale": "simulated scoring",
        "signals": {
            "intel": intel.get("signal"),             # 威胁情报信号值
            "description": alert.get("description"),   # 告警描述摘要
        },
    }