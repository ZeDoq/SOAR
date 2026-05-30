"""Lightweight security knowledge base using keyword matching.

Uses built-in ATT&CK knowledge with simple keyword-based search.
Falls back gracefully when external vector DB is unavailable.
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

ATTACK_KNOWLEDGE = [
    {"id": "T1110", "name": "Brute Force", "tactic": "credential-access",
     "description": "暴力破解：攻击者尝试通过穷举密码来获取账户访问权限。包括在线暴力破解、密码喷洒和凭据填充。",
     "keywords": ["brute", "force", "bruteforce", "password", "login", "auth", "暴力", "密码"]},
    {"id": "T1071", "name": "Application Layer Protocol", "tactic": "command-and-control",
     "description": "应用层协议：攻击者使用常见的应用层协议（HTTP/HTTPS/DNS）进行C2通信以规避检测。",
     "keywords": ["c2", "http", "https", "dns", "protocol", "tunnel", "隧道"]},
    {"id": "T1048", "name": "Exfiltration Over Alternative Protocol", "tactic": "exfiltration",
     "description": "数据外泄：攻击者使用替代协议（如DNS隧道、ICMP）将窃取的数据传输到外部。",
     "keywords": ["exfil", "exfiltration", "dns", "tunnel", "data", "外泄", "窃取"]},
    {"id": "T1021", "name": "Remote Services", "tactic": "lateral-movement",
     "description": "远程服务横向移动：攻击者利用远程服务（RDP、SSH、SMB）在网络内部进行横向移动。",
     "keywords": ["rdp", "ssh", "smb", "lateral", "remote", "横向", "移动", "vpn"]},
    {"id": "T1190", "name": "Exploit Public-Facing Application", "tactic": "initial-access",
     "description": "利用面向公众的应用：攻击者利用互联网可达的应用系统漏洞获取初始访问权限。",
     "keywords": ["exploit", "vulnerability", "web", "application", "漏洞", "利用"]},
    {"id": "T1566", "name": "Phishing", "tactic": "initial-access",
     "description": "钓鱼攻击：攻击者通过发送包含恶意链接或附件的电子邮件来诱骗用户。",
     "keywords": ["phishing", "email", "mail", "钓鱼", "邮件", "恶意"]},
    {"id": "T1059", "name": "Command and Scripting Interpreter", "tactic": "execution",
     "description": "命令和脚本解释器：攻击者利用PowerShell、Bash、Python等脚本环境执行恶意命令。",
     "keywords": ["powershell", "bash", "cmd", "script", "command", "命令", "脚本"]},
    {"id": "T1053", "name": "Scheduled Task/Job", "tactic": "persistence",
     "description": "计划任务：攻击者利用计划任务/作业功能实现持久化，定期执行恶意代码。",
     "keywords": ["cron", "scheduled", "task", "persistence", "持久", "计划"]},
    {"id": "T1078", "name": "Valid Accounts", "tactic": "defense-evasion",
     "description": "合法账户：攻击者使用已泄露的合法账户凭据来规避检测并维持访问。",
     "keywords": ["account", "credential", "valid", "stolen", "凭据", "账户", "合法"]},
    {"id": "T1498", "name": "Network Denial of Service", "tactic": "impact",
     "description": "网络拒绝服务：攻击者通过消耗带宽或服务资源使目标系统不可用。",
     "keywords": ["ddos", "dos", "denial", "flood", "拒绝服务", "流量"]},
    {"id": "T1046", "name": "Network Service Discovery", "tactic": "discovery",
     "description": "网络服务发现：攻击者扫描网络以发现可用的服务和端口。",
     "keywords": ["scan", "port", "nmap", "discovery", "扫描", "端口"]},
    {"id": "T1070", "name": "Indicator Removal", "tactic": "defense-evasion",
     "description": "指标移除：攻击者删除日志、清除痕迹以避免被检测。",
     "keywords": ["log", "clear", "delete", "evasion", "日志", "清除", "痕迹"]},
]


def _tokenize(text: str) -> set:
    """Simple tokenizer: lowercase, split on non-alphanumeric."""
    return set(re.findall(r'[a-z0-9一-鿿]+', text.lower()))


def search(query: str, top_k: int = 3) -> List[dict]:
    """Search knowledge base using keyword matching."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    scored = []
    for entry in ATTACK_KNOWLEDGE:
        entry_tokens = set(entry["keywords"])
        overlap = query_tokens & entry_tokens
        if overlap:
            score = len(overlap) / max(len(query_tokens), 1)
            scored.append((score, entry))

    scored.sort(key=lambda x: -x[0])
    results = []
    for score, entry in scored[:top_k]:
        results.append({
            "id": entry["id"],
            "name": entry["name"],
            "tactic": entry["tactic"],
            "description": entry["description"],
            "relevance": round(score, 2),
        })
    return results


def get_context_for_alert(alert: dict) -> str:
    """Get relevant knowledge context for an alert."""
    query_parts = [alert.get("description", "")]
    query_parts.extend(alert.get("tags", []))
    query = " ".join(query_parts)
    if not query.strip():
        return ""
    results = search(query, top_k=3)
    if not results:
        return ""
    return "\n".join(f"- [{r['id']}] {r['name']} ({r['tactic']}): {r['description']}" for r in results)
