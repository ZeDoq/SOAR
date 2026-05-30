"""
=====  威胁情报查询服务  =====

支持多源情报聚合查询：
  - VirusTotal：IP 信誉查询（真实 API，需 API Key）
  - AbuseIPDB：IP 滥用信誉查询（真实 API，需 API Key）
  - 模拟引擎：内置确定性模拟数据（始终可用作为兜底）

当没有配置任何 API Key 时，系统自动降级为纯模拟模式，
保证在任何环境下都能正常运行。
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .. import settings as settings_mod

logger = logging.getLogger(__name__)

# 信誉等级优先级（越大越危险）
_REPUTATION_RANK = {"benign": 0, "suspicious": 1, "malicious": 2}


def _simulated_lookup(ip: str, latency_ms: int) -> Dict[str, Any]:
    """
    模拟威胁情报查询（原有逻辑）。

    使用 IP 地址的数字特征生成确定性"信誉评分"。
    """
    time.sleep(latency_ms / 1000.0)

    parts = [int(part) for part in ip.split(".") if part.isdigit()]
    signal = sum(parts) % 100

    if signal >= 70:
        reputation = "malicious"
        confidence = 0.92
    elif signal >= 40:
        reputation = "suspicious"
        confidence = 0.68
    else:
        reputation = "benign"
        confidence = 0.35

    return {
        "source": "simulated",
        "reputation": reputation,
        "confidence": confidence,
        "signal": signal,
    }


def _query_virustotal(ip: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    查询 VirusTotal v3 API 获取 IP 信誉。

    归一化逻辑：
      - malicious > 0  → malicious，置信度 = malicious / total
      - suspicious > 0 → suspicious，置信度 = suspicious / total
      - 其他           → benign，置信度 = 0.3
    """
    if not api_key:
        return None

    try:
        import httpx
    except ImportError:
        logger.warning("httpx 未安装，无法查询 VirusTotal")
        return None

    try:
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
        headers = {"x-apikey": api_key}
        resp = httpx.get(url, headers=headers, timeout=15.0)
        resp.raise_for_status()

        data = resp.json()
        stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        total = sum(stats.values()) if stats else 1

        if malicious > 0:
            reputation = "malicious"
            confidence = round(malicious / total, 2)
        elif suspicious > 0:
            reputation = "suspicious"
            confidence = round(suspicious / total, 2)
        else:
            reputation = "benign"
            confidence = 0.3

        signal = min(100, int((malicious + suspicious) / total * 100)) if total > 0 else 0

        return {
            "source": "virustotal",
            "reputation": reputation,
            "confidence": confidence,
            "signal": signal,
        }
    except Exception as e:
        logger.warning("VirusTotal 查询失败 (%s): %s", ip, e)
        return None


def _query_abuseipdb(ip: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    查询 AbuseIPDB v2 API 获取 IP 滥用信誉。

    归一化逻辑：
      - abuseConfidenceScore >= 50 → malicious
      - abuseConfidenceScore >= 10 → suspicious
      - 其他                       → benign
    """
    if not api_key:
        return None

    try:
        import httpx
    except ImportError:
        logger.warning("httpx 未安装，无法查询 AbuseIPDB")
        return None

    try:
        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {"Key": api_key, "Accept": "application/json"}
        params = {"ipAddress": ip, "maxAgeInDays": "90"}
        resp = httpx.get(url, headers=headers, params=params, timeout=15.0)
        resp.raise_for_status()

        data = resp.json().get("data", {})
        score = data.get("abuseConfidenceScore", 0)

        if score >= 50:
            reputation = "malicious"
        elif score >= 10:
            reputation = "suspicious"
        else:
            reputation = "benign"

        return {
            "source": "abuseipdb",
            "reputation": reputation,
            "confidence": round(score / 100, 2),
            "signal": score,
        }
    except Exception as e:
        logger.warning("AbuseIPDB 查询失败 (%s): %s", ip, e)
        return None


def _aggregate(results: List[Dict[str, Any]], ip: str) -> Dict[str, Any]:
    """
    聚合多个情报源结果。

    策略：
      - reputation：取最危险的（malicious > suspicious > benign）
      - confidence：所有来源的平均值
      - signal：所有来源的平均值
      - sources：来源名称列表
      - per_source：各来源详细结果
    """
    if not results:
        return {
            "ip": ip,
            "reputation": "benign",
            "confidence": 0.0,
            "signal": 0,
            "sources": [],
            "per_source": [],
        }

    # 取最危险的信誉等级
    worst = max(results, key=lambda r: _REPUTATION_RANK.get(r.get("reputation", "benign"), 0))

    avg_confidence = round(sum(r.get("confidence", 0) for r in results) / len(results), 2)
    avg_signal = round(sum(r.get("signal", 0) for r in results) / len(results))
    source_names = [r.get("source", "unknown") for r in results]

    return {
        "ip": ip,
        "reputation": worst["reputation"],
        "confidence": avg_confidence,
        "signal": avg_signal,
        "sources": source_names,
        "per_source": results,
    }


def lookup(ip: str, latency_ms: int) -> Dict[str, Any]:
    """
    查询指定 IP 的威胁情报信息（多源聚合）。

    保持与旧版完全相同的函数签名和返回格式，确保向后兼容。
    新增 per_source 字段提供各来源的详细结果。

    Args:
        ip: 目标 IP 地址
        latency_ms: 模拟延迟（仅对模拟数据生效）

    Returns:
        聚合后的威胁情报字典
    """
    settings = settings_mod.settings
    results: List[Dict[str, Any]] = []

    # 1. 查询 VirusTotal
    vt_result = _query_virustotal(ip, settings.virustotal_api_key)
    if vt_result:
        results.append(vt_result)

    # 2. 查询 AbuseIPDB
    ab_result = _query_abuseipdb(ip, settings.abuseipdb_api_key)
    if ab_result:
        results.append(ab_result)

    # 3. 始终包含模拟数据作为基线
    sim_result = _simulated_lookup(ip, latency_ms)
    results.append(sim_result)

    # 4. 聚合所有结果
    return _aggregate(results, ip)
