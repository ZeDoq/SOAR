"""Curated security incident corpus for RAG retrieval.

Contains real-world attack patterns and incident case studies
that help the system recognize similar events.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

INCIDENTS: List[dict] = [
    {
        "id": "case_ssh_bruteforce_001",
        "document": (
            "SSH 暴力破解攻击案例：攻击者对公网服务器发起大规模 SSH 暴力破解，"
            "使用常见用户名(root, admin, ubuntu)和弱密码字典。特征：短时间内大量"
            "SSH登录失败事件，来源IP集中在东欧地区。处置：封锁源IP，启用fail2ban，"
            "强制使用密钥认证禁用密码登录。ATT&CK: T1110 Brute Force"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "brute_force",
            "severity": "high",
            "techniques": "T1110",
            "tactic": "credential-access",
            "outcome": "blocked",
        },
    },
    {
        "id": "case_dns_tunnel_exfil_002",
        "document": (
            "DNS隧道数据窃取案例：攻击者在内网渗透后，通过DNS查询将窃取的数据库"
            "内容编码在子域名中逐步外传。特征：大量异常长DNS查询请求(子域名>50字符)，"
            "查询频率异常高，目标域名为新注册的低信誉域名。处置：在DNS代理层检测并"
            "阻断异常长域名查询，监控DNS流量异常。ATT&CK: T1048 Exfiltration Over "
            "Alternative Protocol, T1071 Application Layer Protocol"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "data_exfiltration",
            "severity": "critical",
            "techniques": "T1048,T1071",
            "tactic": "exfiltration",
            "outcome": "blocked",
        },
    },
    {
        "id": "case_rdp_lateral_003",
        "document": (
            "RDP横向移动攻击案例：攻击者利用窃取的域管理员凭据，通过RDP从一台"
            "受控主机横向移动到域内其他关键服务器。特征：非工作时间的RDP连接，"
            "来源为内网非管理段IP，伴随PowerShell异常执行。处置：立即隔离受控主机，"
            "重置所有域管理员密码，启用NLA网络级认证。ATT&CK: T1021 Remote Services, "
            "T1059 Command and Scripting Interpreter"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "lateral_movement",
            "severity": "critical",
            "techniques": "T1021,T1059",
            "tactic": "lateral-movement",
            "outcome": "contained",
        },
    },
    {
        "id": "case_phishing_credential_004",
        "document": (
            "钓鱼邮件窃取凭据案例：攻击者伪装为IT部门发送钓鱼邮件，诱导员工点击"
            "链接登录假冒的Office 365页面。特征：发件人域名与公司域名相似(替换字母)，"
            "钓鱼页面使用SSL证书但域名不匹配。处置：封锁钓鱼域名，强制所有受影响"
            "用户重置MFA令牌，邮箱规则过滤类似邮件。ATT&CK: T1566 Phishing, "
            "T1078 Valid Accounts"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "phishing",
            "severity": "high",
            "techniques": "T1566,T1078",
            "tactic": "initial-access",
            "outcome": "remediated",
        },
    },
    {
        "id": "case_ddos_amplification_005",
        "document": (
            "DDoS放大攻击案例：目标遭受DNS放大攻击，入站流量峰值达20Gbps。"
            "特征：UDP源端口53的大量入站流量，数据包大小接近DNS最大响应长度，"
            "源IP为开放DNS解析器。处置：上游ISP启用流量清洗，配置反向路径验证，"
            "部署DDoS防护服务。ATT&CK: T1498 Network Denial of Service"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "ddos",
            "severity": "critical",
            "techniques": "T1498",
            "tactic": "impact",
            "outcome": "mitigated",
        },
    },
    {
        "id": "case_port_scan_recon_006",
        "document": (
            "端口扫描侦察案例：外部IP对目标网络进行全面端口扫描，先进行SYN扫描"
            "识别开放端口，然后对发现的服务进行版本探测。特征：短时间内大量不同端口"
            "的连接尝试，TTL值一致，TCP标志位异常(SYN-only)。处置：监控并记录，"
            "更新IDS签名，检查防火墙规则是否需要收紧。ATT&CK: T1046 Network "
            "Service Discovery"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "port_scan",
            "severity": "medium",
            "techniques": "T1046",
            "tactic": "discovery",
            "outcome": "monitored",
        },
    },
    {
        "id": "case_apt_campaign_007",
        "document": (
            "APT多阶段攻击活动案例：攻击者通过水坑攻击植入Web Shell(初始访问)，"
            "使用PowerShell下载Cobalt Strike Beacon(执行)，创建计划任务实现"
            "持久化，利用Mimikatz提取凭据(凭证访问)，通过PsExec横向移动到文件"
            "服务器，最终通过HTTPS加密通道外传压缩数据(数据窃取)。整个攻击链"
            "横跨2周，涉及多个ATT&CK战术阶段。处置：全面网络取证，隔离受影响"
            "系统，重置所有凭据，部署EDR加强监控。"
            "ATT&CK: T1190→T1059→T1053→T1003→T1021→T1041"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "apt_campaign",
            "severity": "critical",
            "techniques": "T1190,T1059,T1053,T1003,T1021,T1041",
            "tactic": "initial-access,execution,persistence,credential-access,lateral-movement,exfiltration",
            "outcome": "contained",
        },
    },
    {
        "id": "case_web_vuln_exploit_008",
        "document": (
            "Web应用漏洞利用案例：攻击者利用未修补的Log4j漏洞(CVE-2021-44228)"
            "在公网Web服务器上执行远程代码。特征：HTTP请求头包含JNDI注入字符串"
            "(${jndi:ldap://...})，后续LDAP出站连接异常。处置：立即修补Log4j，"
            "检查服务器是否已被植入后门，WAF添加JNDI注入规则。ATT&CK: T1190 "
            "Exploit Public-Facing Application"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "exploit",
            "severity": "critical",
            "techniques": "T1190",
            "tactic": "initial-access",
            "outcome": "remediated",
        },
    },
    {
        "id": "case_false_positive_scan_009",
        "document": (
            "误报案例-合法安全扫描：企业内部漏洞扫描器(Nessus)定期对全网进行"
            "扫描，产生大量端口扫描和暴力破解告警。特征：来源IP为已知内部扫描器，"
            "扫描时间固定(每周日凌晨2-4点)，扫描模式规律(按IP段顺序)。处置：将"
            "扫描器IP加入白名单，建立扫描时间窗口策略。此类告警为合法安全评估活动"
            "产生的误报，不应触发阻断响应。"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "false_positive",
            "severity": "low",
            "techniques": "T1046,T1110",
            "tactic": "discovery",
            "outcome": "false_positive",
        },
    },
    {
        "id": "case_cryptominer_010",
        "document": (
            "加密货币挖矿木马案例：服务器被植入XMRig挖矿程序，CPU使用率持续"
            "100%。特征：异常高CPU使用率，与矿池域名的DNS连接(stratum+tcp://)，"
            "进程隐藏技术(修改进程名)。处置：终止挖矿进程，检查初始入侵途径"
            "(通常为未修补的Web漏洞或弱SSH密码)，部署进程白名单策略。"
            "ATT&CK: T1059 Command and Scripting Interpreter"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "malware",
            "severity": "medium",
            "techniques": "T1059",
            "tactic": "execution",
            "outcome": "remediated",
        },
    },
    {
        "id": "case_supply_chain_011",
        "document": (
            "供应链攻击案例：第三方软件供应商的更新服务器被入侵，恶意代码被注入"
            "到合法软件更新包中(类似SolarWinds攻击模式)。特征：合法签名的软件更新"
            "中包含异常网络连接行为，连接到新建C2域名。处置：断开受影响系统网络，"
            "回滚软件版本，审计供应链安全。ATT&CK: T1195 Supply Chain Compromise"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "supply_chain",
            "severity": "critical",
            "techniques": "T1195",
            "tactic": "initial-access",
            "outcome": "contained",
        },
    },
    {
        "id": "case_ransomware_012",
        "document": (
            "勒索软件攻击案例：勒索软件通过RDP弱密码进入内网，利用PsExec和WMI"
            "在域内快速传播，加密文件服务器和数据库服务器。特征：大量文件扩展名"
            "被修改，勒索信文本文件，卷影副本被删除(vssadmin delete shadows)。"
            "处置：隔离受感染网段，从备份恢复数据，修补RDP暴露面，部署EDR。"
            "ATT&CK: T1486 Data Encrypted for Impact, T1021 Remote Services"
        ),
        "metadata": {
            "type": "incident",
            "attack_type": "ransomware",
            "severity": "critical",
            "techniques": "T1486,T1021",
            "tactic": "impact",
            "outcome": "recovered",
        },
    },
]


def load_incident_corpus() -> int:
    """Load curated incident cases into the RAG vector store.

    Returns number of incidents loaded.
    """
    from . import rag_engine

    rag_engine._ensure_initialized()

    documents = [inc["document"] for inc in INCIDENTS]
    metadatas = [inc["metadata"] for inc in INCIDENTS]
    ids = [inc["id"] for inc in INCIDENTS]

    count = rag_engine.add_documents(documents, metadatas, ids)
    logger.info("Loaded %d incident cases into RAG store", count)
    return count
