"""
=====  攻击模拟场景定义  =====

预定义攻击场景，用于测试、演示和培训。
每个场景包含中英文双语描述。
"""

from typing import Any, Dict, List

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "brute_force": {
        "name": "SSH 暴力破解攻击",
        "description": "模拟外部 IP 进行大量 SSH 登录失败尝试，最终成功入侵。",
        "attack_type": "brute_force",
        "alerts": [
            {
                "ip": "185.220.101.34",
                "source": "simulator",
                "description": "SSH bruteforce: 150 failed login attempts in 5 minutes",
                "description_zh": "SSH 暴力破解：5 分钟内 150 次登录失败尝试",
                "tags": ["ssh", "bruteforce", "auth"],
            },
            {
                "ip": "185.220.101.35",
                "source": "simulator",
                "description": "SSH bruteforce from different IP, same ASN",
                "description_zh": "来自不同 IP 的 SSH 暴力破解，同一 ASN",
                "tags": ["ssh", "bruteforce", "auth"],
            },
        ],
        "expected_outcome": {
            "action": "block",
            "min_risk_score": 60,
            "techniques": ["T1110"],
        },
    },

    "port_scan": {
        "name": "网络端口扫描",
        "description": "模拟 Nmap 风格的 SYN 扫描，探测多个端口。",
        "attack_type": "port_scan",
        "alerts": [
            {
                "ip": "45.33.32.156",
                "source": "simulator",
                "description": "Port scan detected: SYN packets to ports 22,80,443,3306,5432,8080",
                "description_zh": "检测到端口扫描：SYN 数据包发往端口 22,80,443,3306,5432,8080",
                "tags": ["scan", "port", "nmap", "discovery"],
            },
        ],
        "expected_outcome": {
            "action": "monitor",
            "techniques": ["T1046"],
        },
    },

    "data_exfiltration": {
        "name": "DNS 隧道数据外泄",
        "description": "模拟通过 DNS 隧道进行数据外泄。",
        "attack_type": "data_exfiltration",
        "alerts": [
            {
                "ip": "10.0.5.23",
                "source": "simulator",
                "description": "Unusual DNS query volume: 5000 TXT queries to suspicious domain, possible DNS tunnel exfiltration",
                "description_zh": "异常 DNS 查询量：10 分钟内向可疑域名发送 5000 次 TXT 查询，疑似 DNS 隧道数据外泄",
                "tags": ["dns", "exfiltration", "tunnel", "data"],
            },
        ],
        "expected_outcome": {
            "action": "block",
            "min_risk_score": 50,
            "techniques": ["T1048"],
        },
    },

    "phishing": {
        "name": "钓鱼邮件攻击",
        "description": "模拟针对员工的钓鱼邮件活动。",
        "attack_type": "phishing",
        "alerts": [
            {
                "ip": "192.168.1.50",
                "source": "simulator",
                "description": "Phishing email detected: credential harvesting link to fake Office365 login page",
                "description_zh": "检测到钓鱼邮件：包含指向伪造 Office365 登录页面的凭据收集链接",
                "tags": ["phishing", "email", "credential"],
            },
        ],
        "expected_outcome": {
            "action": "monitor",
            "techniques": ["T1566"],
        },
    },

    "ddos": {
        "name": "DDoS 攻击",
        "description": "模拟大流量 DDoS 攻击。",
        "attack_type": "ddos",
        "alerts": [
            {
                "ip": "203.0.113.50",
                "source": "simulator",
                "description": "DDoS flood detected: 50000 requests/sec from botnet, UDP flood targeting port 80",
                "description_zh": "检测到 DDoS 攻击：僵尸网络发起每秒 50000 次请求的 UDP 洪水攻击，目标端口 80",
                "tags": ["ddos", "flood", "dos"],
            },
            {
                "ip": "198.51.100.23",
                "source": "simulator",
                "description": "DDoS participant: high bandwidth UDP flood",
                "description_zh": "DDoS 参与者：高带宽 UDP 洪水攻击",
                "tags": ["ddos", "flood"],
            },
        ],
        "expected_outcome": {
            "action": "block",
            "min_risk_score": 40,
            "techniques": ["T1498"],
        },
    },

    "lateral_movement": {
        "name": "RDP 横向移动",
        "description": "模拟攻击者通过 RDP 进行内部横向移动。",
        "attack_type": "lateral_movement",
        "alerts": [
            {
                "ip": "10.0.1.15",
                "source": "simulator",
                "description": "RDP lateral movement: connection from compromised workstation to 3 internal servers in 2 minutes",
                "description_zh": "RDP 横向移动：从已入侵工作站 2 分钟内连接 3 台内部服务器",
                "tags": ["rdp", "lateral", "movement", "internal"],
            },
            {
                "ip": "10.0.1.15",
                "source": "simulator",
                "description": "Suspicious PowerShell execution on target server after RDP login",
                "description_zh": "RDP 登录后在目标服务器上执行可疑 PowerShell 命令",
                "tags": ["powershell", "execution", "lateral"],
            },
        ],
        "expected_outcome": {
            "action": "block",
            "min_risk_score": 70,
            "techniques": ["T1021", "T1059"],
        },
    },

    # ---- Module 5: Multi-stage APT scenarios ----
    "apt_lateral_movement": {
        "name": "APT 横向移动攻击链",
        "description": "模拟 APT 攻击的完整横向移动链：端口扫描 → 漏洞利用 → PowerShell 执行 → RDP 横向移动 → 数据外泄",
        "attack_type": "apt_campaign",
        "sequence_delay_seconds": 2,  # Delay between alerts for demo
        "alerts": [
            {
                "ip": "203.0.113.50",
                "source": "simulator",
                "description": "Port scan: SYN packets to ports 445,3389,5985 on internal network",
                "description_zh": "端口扫描：对内网 445,3389,5985 端口发送 SYN 包",
                "tags": ["scan", "port", "discovery"],
            },
            {
                "ip": "203.0.113.50",
                "source": "simulator",
                "description": "Exploit attempt: EternalBlue SMB vulnerability CVE-2017-0144",
                "description_zh": "漏洞利用：永恒之蓝 SMB 漏洞 CVE-2017-0144",
                "tags": ["exploit", "smb", "eternalblue"],
            },
            {
                "ip": "203.0.113.50",
                "source": "simulator",
                "description": "PowerShell encoded command execution: download cradle from remote server",
                "description_zh": "PowerShell 编码命令执行：从远程服务器下载恶意载荷",
                "tags": ["powershell", "execution", "command"],
            },
            {
                "ip": "203.0.113.50",
                "source": "simulator",
                "description": "RDP connection to internal server 10.0.1.15 using stolen credentials",
                "description_zh": "使用窃取的凭据通过 RDP 连接内网服务器 10.0.1.15",
                "tags": ["rdp", "lateral", "remote", "credential"],
            },
            {
                "ip": "203.0.113.50",
                "source": "simulator",
                "description": "DNS tunnel exfiltration: high volume TXT queries to suspicious domain",
                "description_zh": "DNS 隧道外泄：大量 TXT 查询发往可疑域名",
                "tags": ["dns", "exfil", "tunnel", "data"],
            },
        ],
        "expected_outcome": {
            "action": "block",
            "min_risk_score": 80,
            "techniques": ["T1046", "T1190", "T1059", "T1021", "T1048"],
        },
    },

    "supply_chain_attack": {
        "name": "供应链攻击链",
        "description": "模拟供应链攻击：钓鱼邮件 → 凭据窃取 → 内部侦察 → 数据库访问 → DNS 外泄",
        "attack_type": "supply_chain",
        "sequence_delay_seconds": 2,
        "alerts": [
            {
                "ip": "198.51.100.20",
                "source": "simulator",
                "description": "Phishing email with credential harvesting link detected",
                "description_zh": "检测到钓鱼邮件含凭据收集链接",
                "tags": ["phishing", "email", "credential"],
            },
            {
                "ip": "198.51.100.20",
                "source": "simulator",
                "description": "Credential stuffing attack: multiple accounts compromised",
                "description_zh": "凭据填充攻击：多个账户被入侵",
                "tags": ["credential", "account", "auth"],
            },
            {
                "ip": "198.51.100.20",
                "source": "simulator",
                "description": "Internal network reconnaissance: LDAP query for admin accounts",
                "description_zh": "内网侦察：LDAP 查询管理员账户",
                "tags": ["discovery", "ldap", "recon"],
            },
            {
                "ip": "198.51.100.20",
                "source": "simulator",
                "description": "Database access anomaly: bulk SELECT on customer data table",
                "description_zh": "数据库访问异常：对客户数据表的大批量 SELECT 查询",
                "tags": ["database", "collection", "data"],
            },
            {
                "ip": "198.51.100.20",
                "source": "simulator",
                "description": "DNS exfiltration: encoded data in subdomain queries to new domain",
                "description_zh": "DNS 外泄：编码数据通过子域名查询发送到新域名",
                "tags": ["dns", "exfil", "tunnel"],
            },
        ],
        "expected_outcome": {
            "action": "block",
            "min_risk_score": 85,
            "techniques": ["T1566", "T1078", "T1082", "T1005", "T1048"],
        },
    },
}


def get_scenario_names() -> List[str]:
    """返回所有可用场景名称。"""
    return list(SCENARIOS.keys())


def get_scenario(name: str) -> Dict[str, Any]:
    """按名称获取场景。"""
    return SCENARIOS.get(name)
