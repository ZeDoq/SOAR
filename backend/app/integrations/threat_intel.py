"""
=====  威胁情报查询服务（模拟）  =====

在真实 SOAR 系统中，此模块会集成外部威胁情报 API 如：
  - VirusTotal：文件/URL/IP 信誉查询
  - AlienVault OTX：开放威胁情报
  - IBM X-Force Exchange：安全威胁情报
  - MISP（Malware Information Sharing Platform）

本实现使用模拟数据，通过 IP 地址的数值特征计算"信誉评分"，
演示了 Agent 如何调用外部情报源获取上下文信息。
"""

import time
from typing import Dict


def lookup(ip: str, latency_ms: int) -> Dict[str, object]:
    """
    查询指定 IP 地址的威胁情报信息。

    计算逻辑：
      1. 将 IP 地址的每个段（如 192.168.1.1 的 192, 168, 1, 1）求和
      2. 对 100 取模得到一个 0-99 的信号值（signal）
      3. 根据信号值判断信誉等级：
         - signal >= 70: 恶意（malicious），置信度 0.92
         - signal >= 40: 可疑（suspicious），置信度 0.68
         - signal <  40: 良性（benign），置信度 0.35

    这种模拟方式虽然简单，但保证了：
      - 同一 IP 总是返回相同结果（确定性）
      - 不同 IP 有不同的信誉值（区分度）

    Args:
        ip: 要查询的目标 IP 地址
        latency_ms: 模拟网络延迟（毫秒），使模拟更真实

    Returns:
        包含 IP 信誉信息的字典：
        {
            "ip": 目标 IP,
            "reputation": 信誉等级（malicious/suspicious/benign）,
            "confidence": 置信度（0-1）,
            "signal": 原始信号值（0-99）,
            "sources": 情报来源列表
        }
    """
    # 模拟 API 调用延迟
    time.sleep(latency_ms / 1000.0)

    # 使用 IP 地址的数字特征生成"信号"值
    parts = [int(part) for part in ip.split(".") if part.isdigit()]
    signal = sum(parts) % 100

    # 根据信号值判定信誉等级
    if signal >= 70:
        reputation = "malicious"      # 恶意
        confidence = 0.92
    elif signal >= 40:
        reputation = "suspicious"     # 可疑
        confidence = 0.68
    else:
        reputation = "benign"         # 良性
        confidence = 0.35

    return {
        "ip": ip,
        "reputation": reputation,
        "confidence": confidence,
        "signal": signal,
        "sources": ["sim_feed_alpha", "sim_feed_beta"],  # 模拟情报来源
    }