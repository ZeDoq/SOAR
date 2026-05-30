"""
=====  Playbook 模板选择器  =====

根据告警特征自动选择最合适的 Playbook 模板。
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

TEMPLATES: Dict[str, Dict[str, Any]] = {
    "full_investigation": {
        "description": "完整调查（所有步骤）",
        "steps": ["intelligence", "analysis", "firewall_block",
                  "notify_email", "notify_slack", "report_generation"],
        "risk_block_threshold": 70,
    },
    "brute_force": {
        "description": "暴力破解响应（跳过侦察，降低阈值）",
        "steps": ["intelligence", "analysis", "firewall_block",
                  "notify_email", "notify_slack", "report_generation"],
        "skip_recon": True,
        "risk_block_threshold": 60,
    },
    "port_scan": {
        "description": "端口扫描响应（仅 Slack 通知）",
        "steps": ["intelligence", "analysis", "firewall_block", "notify_slack"],
        "risk_block_threshold": 75,
    },
    "data_exfiltration": {
        "description": "数据外泄响应（激进阻断）",
        "steps": ["intelligence", "analysis", "firewall_block",
                  "notify_email", "notify_slack", "report_generation"],
        "risk_block_threshold": 50,
    },
    "phishing": {
        "description": "钓鱼响应（不阻断防火墙，重点报告）",
        "steps": ["intelligence", "analysis",
                  "notify_email", "notify_slack", "report_generation"],
        "risk_block_threshold": 70,
    },
    "ddos": {
        "description": "DDoS 响应（快速阻断，低阈值）",
        "steps": ["intelligence", "firewall_block", "notify_email", "notify_slack"],
        "risk_block_threshold": 40,
    },
    "low_priority": {
        "description": "低优先级（最少步骤）",
        "steps": ["intelligence", "analysis"],
        "risk_block_threshold": 90,
    },
}

_TYPE_KEYWORDS = {
    "brute_force": ["brute", "bruteforce", "password", "login fail", "暴力"],
    "port_scan": ["scan", "port", "nmap", "discovery", "扫描"],
    "data_exfiltration": ["exfil", "data transfer", "dns tunnel", "外泄", "泄露"],
    "phishing": ["phish", "email", "钓鱼"],
    "ddos": ["ddos", "dos", "flood", "拒绝服务"],
}

_TYPE_TO_TEMPLATE = {
    "brute_force": "brute_force",
    "port_scan": "port_scan",
    "data_exfiltration": "data_exfiltration",
    "phishing": "phishing",
    "ddos": "ddos",
}


def detect_attack_type(alert: dict) -> str:
    """从告警描述和标签中检测攻击类型。"""
    description = (alert.get("description") or "").lower()
    tags = [t.lower() for t in alert.get("tags", [])]
    combined = description + " " + " ".join(tags)

    for attack_type, keywords in _TYPE_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            return attack_type

    return "unknown"


def select_playbook(alert: dict, intel: dict = None) -> Dict[str, Any]:
    """
    根据告警特征选择 Playbook 模板。

    选择逻辑：
    1. 检测攻击类型
    2. 匹配到模板则使用
    3. 未知类型 + intel 为 benign → low_priority
    4. 其他 → full_investigation
    """
    attack_type = detect_attack_type(alert)
    template_name = _TYPE_TO_TEMPLATE.get(attack_type)

    if not template_name:
        if intel and intel.get("reputation") == "benign":
            template_name = "low_priority"
        else:
            template_name = "full_investigation"

    template = dict(TEMPLATES[template_name])
    template["template_name"] = template_name
    template["detected_attack_type"] = attack_type

    logger.info("选择 Playbook '%s'（attack_type=%s）", template_name, attack_type)
    return template
