"""
=====  网络侦察工具  =====

提供 WHOIS 和 DNS 查询功能，用于安全调查中的目标信息收集。
所有函数遵循项目的优雅降级模式：失败时返回 None。
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 输入校验：仅允许合法 IP 和域名字符
_SAFE_TARGET_RE = re.compile(r"^[a-zA-Z0-9\.\-:]+$")


def _validate_target(target: str) -> bool:
    """验证 target 是否为合法 IP 或域名（防止命令注入）。"""
    if not target or len(target) > 255:
        return False
    return bool(_SAFE_TARGET_RE.match(target))


def whois_lookup(target: str, latency_ms: int = 0) -> Optional[Dict[str, Any]]:
    """
    对域名或 IP 执行 WHOIS 查询。

    优先使用 python-whois 库，失败时回退到 subprocess 调用系统 whois 命令。

    Args:
        target: 域名或 IP 地址
        latency_ms: 模拟延迟（测试兼容）

    Returns:
        包含注册信息的字典，失败返回 None
    """
    if latency_ms > 0:
        time.sleep(latency_ms / 1000.0)

    if not _validate_target(target):
        logger.warning("WHOIS 查询目标格式不合法: %s", target[:50])
        return None

    # 尝试 python-whois 库
    try:
        import whois as whois_lib
        w = whois_lib.whois(target)
        return {
            "target": target,
            "registrar": w.registrar,
            "creation_date": str(w.creation_date) if w.creation_date else None,
            "expiration_date": str(w.expiration_date) if w.expiration_date else None,
            "name_servers": list(w.name_servers) if w.name_servers else [],
            "org": w.org,
            "country": w.country,
            "raw_text": str(w)[:2000],
        }
    except ImportError:
        logger.debug("python-whois 未安装，尝试 subprocess")
    except Exception as e:
        logger.debug("python-whois 查询失败: %s，尝试 subprocess", e)

    # 回退到 subprocess
    try:
        import subprocess
        result = subprocess.run(
            ["whois", target],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            raw = result.stdout[:2000]
            return {
                "target": target,
                "registrar": None,
                "creation_date": None,
                "expiration_date": None,
                "name_servers": [],
                "org": None,
                "country": None,
                "raw_text": raw,
            }
    except Exception as e:
        logger.debug("subprocess whois 失败: %s", e)

    return None


def dns_lookup(target: str, latency_ms: int = 0) -> Optional[Dict[str, Any]]:
    """
    对域名执行 DNS 记录查询（A, AAAA, MX, TXT, NS）。

    使用 dnspython 库。每种记录类型独立查询，部分失败仍返回已有结果。

    Args:
        target: 域名
        latency_ms: 模拟延迟（测试兼容）

    Returns:
        包含各类 DNS 记录的字典，全部失败返回 None
    """
    if latency_ms > 0:
        time.sleep(latency_ms / 1000.0)

    try:
        import dns.resolver
    except ImportError:
        logger.warning("dnspython 未安装，无法执行 DNS 查询")
        return None

    record_types = ["A", "AAAA", "MX", "TXT", "NS"]
    result: Dict[str, Any] = {"target": target}
    has_any = False

    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(target, rtype)
            if rtype == "MX":
                records = [str(r.exchange).rstrip(".") for r in answers]
            else:
                records = [str(r) for r in answers]
            result[rtype.lower()] = records
            if records:
                has_any = True
        except Exception:
            result[rtype.lower()] = []

    return result if has_any else None
