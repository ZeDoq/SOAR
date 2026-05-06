"""
=====  防火墙联动服务（模拟）  =====

在真实 SOAR 系统中，此模块会集成企业防火墙设备/软件的 API，例如：
  - iptables / nftables（Linux 防火墙）
  - pfSense / OPNsense API
  - Cisco ASA / Firepower API
  - Palo Alto Networks PAN-OS API
  - Fortinet FortiGate API
  - 云防火墙：AWS WAF / Security Group、Azure NSG、GCP Cloud Armor

本实现模拟了 Agent 联动防火墙封禁恶意 IP 的过程。
"""

import time
from typing import Dict, Any


def block(ip: str, risk: Dict[str, Any], latency_ms: int) -> Dict[str, Any]:
    """
    在防火墙上封禁指定的恶意 IP 地址。

    模拟流程：
    1. 收到封禁指令（包含目标 IP 和风险评分）
    2. 向防火墙设备发送封禁规则（模拟网络延迟）
    3. 返回执行结果（包含工单号供追溯）

    Args:
        ip: 要封禁的目标 IP 地址
        risk: 风险评估结果（包含 risk_score）
        latency_ms: 模拟 API 调用延迟（毫秒）

    Returns:
        封禁操作结果，包含：
        {
            "action": "blocked",           -- 执行动作
            "ip": 目标 IP 地址,              -- 被封禁的 IP
            "reason": "risk_score=XX",     -- 封禁原因（风险评分）
            "ticket": "FW-XXXXX"           -- 工单号，用于事件追溯
        }
    """
    # 模拟防火墙 API 调用延迟
    time.sleep(latency_ms / 1000.0)

    # 生成工单号：使用 IP 哈希值确保同一 IP 生成相同的工单号
    ticket_number = abs(hash(ip)) % 100000

    return {
        "action": "blocked",
        "ip": ip,
        "reason": f"risk_score={risk.get('risk_score')}",
        "ticket": f"FW-{ticket_number}",
    }