"""
=====  告警源管理器  =====

统一管理所有告警源监听器的生命周期。
提供启动、停止、状态查询接口。
"""

import logging
from typing import Any, Callable, Dict, List

from .. import settings as settings_mod
from .. import storage

logger = logging.getLogger(__name__)

# 运行中的监听器实例 {name: listener}
_sources: Dict[str, Any] = {}


def _ingest_alert(alert_dict: Dict[str, Any]) -> None:
    """
    所有监听器共用的回调函数。
    将解析后的告警写入数据库。
    """
    try:
        record = storage.create_alert(alert_dict)
        logger.info("告警已接入: IP=%s, source=%s, id=%s",
                     alert_dict.get("ip"), alert_dict.get("source"), record.get("id"))
    except Exception as e:
        logger.warning("告警入库失败: %s", e)


def start_source(name: str) -> Dict[str, Any]:
    """
    启动指定的告警源。

    Args:
        name: 告警源名称 (syslog / wazuh / suricata)

    Returns:
        状态字典
    """
    if name in _sources and _sources[name].is_alive:
        return {"name": name, "status": "already_running"}

    settings = settings_mod.settings

    try:
        if name == "syslog":
            from .syslog_listener import SyslogListener
            listener = SyslogListener(port=settings.syslog_port, on_alert=_ingest_alert)
            listener.start()
            _sources[name] = listener

        elif name == "wazuh":
            if not settings.wazuh_api_url:
                return {"name": name, "status": "error", "reason": "WAZUH_API_URL 未配置"}
            from .wazuh_client import WazuhPoller
            listener = WazuhPoller(
                api_url=settings.wazuh_api_url,
                api_user=settings.wazuh_api_user,
                api_password=settings.wazuh_api_password,
                on_alert=_ingest_alert,
            )
            listener.start()
            _sources[name] = listener

        elif name == "suricata":
            if not settings.suricata_eve_log:
                return {"name": name, "status": "error", "reason": "SURICATA_EVE_LOG 未配置"}
            from .suricata_tail import SuricataTail
            listener = SuricataTail(
                log_path=settings.suricata_eve_log,
                on_alert=_ingest_alert,
            )
            listener.start()
            _sources[name] = listener

        else:
            return {"name": name, "status": "error", "reason": f"未知告警源: {name}"}

        return {"name": name, "status": "started"}

    except Exception as e:
        logger.error("启动告警源 %s 失败: %s", name, e)
        return {"name": name, "status": "error", "reason": str(e)}


def stop_source(name: str) -> Dict[str, Any]:
    """停止指定的告警源。"""
    listener = _sources.get(name)
    if not listener:
        return {"name": name, "status": "not_running"}

    try:
        listener.stop()
        del _sources[name]
        return {"name": name, "status": "stopped"}
    except Exception as e:
        logger.error("停止告警源 %s 失败: %s", name, e)
        return {"name": name, "status": "error", "reason": str(e)}


def get_status() -> List[Dict[str, Any]]:
    """
    获取所有告警源的状态。

    Returns:
        列表，每个元素包含 name/configured/running
    """
    settings = settings_mod.settings
    sources_info = [
        {
            "name": "syslog",
            "configured": True,  # syslog 只需端口，始终视为已配置
            "running": _sources.get("syslog", None) is not None
                       and _sources["syslog"].is_alive,
        },
        {
            "name": "wazuh",
            "configured": bool(settings.wazuh_api_url),
            "running": _sources.get("wazuh", None) is not None
                       and _sources["wazuh"].is_alive,
        },
        {
            "name": "suricata",
            "configured": bool(settings.suricata_eve_log),
            "running": _sources.get("suricata", None) is not None
                       and _sources["suricata"].is_alive,
        },
    ]
    return sources_info


def start_configured_sources() -> None:
    """
    自动启动所有已配置的告警源。
    在应用启动时调用。
    """
    settings = settings_mod.settings

    # Syslog：端口始终有默认值，不自动启动（需要 root/管理员权限）
    # Wazuh：URL 非空则启动
    if settings.wazuh_api_url:
        result = start_source("wazuh")
        logger.info("自动启动 Wazuh: %s", result)

    # Suricata：日志路径非空则启动
    if settings.suricata_eve_log:
        result = start_source("suricata")
        logger.info("自动启动 Suricata: %s", result)


def stop_all_sources() -> None:
    """停止所有运行中的告警源。在应用关闭时调用。"""
    for name in list(_sources.keys()):
        result = stop_source(name)
        logger.info("停止告警源 %s: %s", name, result)
