"""
=====  Wazuh 告警接入  =====

轮询 Wazuh Manager API 获取新告警，
自动转换为 SOAR 告警格式存入数据库。
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_wazuh_alert(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    将 Wazuh API 告警转换为 SOAR 告警格式。

    字段映射:
      - data.srcip → ip
      - rule.description → description
      - rule.groups → tags
      - timestamp → observed_at
    """
    data = raw.get("data", {})
    rule = raw.get("rule", {})

    ip = data.get("srcip") or data.get("srcip")
    if not ip:
        return None

    description = rule.get("description", "Wazuh alert")
    agent_name = raw.get("agent", {}).get("name")
    if agent_name:
        description = f"[{agent_name}] {description}"

    groups = rule.get("groups", [])
    tags = ["wazuh"] + groups[:5]  # 最多取 5 个分组标签

    return {
        "ip": ip,
        "source": "wazuh",
        "description": description[:500],
        "tags": tags,
    }


def fetch_recent_alerts(
    api_url: str,
    api_user: str,
    api_password: str,
    since: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    从 Wazuh API 获取最近的告警。

    使用延迟导入 httpx，verify=False（Wazuh 常用自签名证书）。
    """
    try:
        import httpx
    except ImportError:
        logger.warning("httpx 未安装，无法查询 Wazuh API")
        return []

    try:
        url = f"{api_url.rstrip('/')}/alerts"
        params: Dict[str, Any] = {"limit": limit, "sort": "-timestamp"}
        if since:
            params["date"] = f"{since}..now"

        resp = httpx.get(
            url,
            params=params,
            auth=(api_user, api_password),
            verify=False,
            timeout=30.0,
        )
        resp.raise_for_status()

        data = resp.json()
        return data.get("data", {}).get("affected_items", [])
    except Exception as e:
        logger.warning("Wazuh API 查询失败: %s", e)
        return []


class WazuhPoller:
    """
    Wazuh 后台轮询器（后台线程）。

    用法:
        poller = WazuhPoller(api_url, user, pwd, on_alert=my_callback)
        poller.start()
        # ... 运行中 ...
        poller.stop()
    """

    def __init__(
        self,
        api_url: str,
        api_user: str,
        api_password: str,
        on_alert: Callable[[Dict[str, Any]], None],
        poll_interval: int = 60,
    ):
        self.api_url = api_url
        self.api_user = api_user
        self.api_password = api_password
        self.on_alert = on_alert
        self.poll_interval = poll_interval
        self._stop_event = __import__("threading").Event()
        self._thread: Optional[Any] = None
        self._last_poll: Optional[str] = None

    def start(self) -> None:
        """启动轮询线程。"""
        import threading

        if self._thread and self._thread.is_alive():
            logger.warning("Wazuh 轮询器已在运行")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info("Wazuh 轮询器已启动，间隔 %ds", self.poll_interval)

    def stop(self) -> None:
        """停止轮询器。"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.poll_interval + 5)
        logger.info("Wazuh 轮询器已停止")

    @property
    def is_alive(self) -> bool:
        """轮询线程是否在运行。"""
        return self._thread is not None and self._thread.is_alive()

    def _poll_loop(self) -> None:
        """线程主循环：定时拉取告警。"""
        while not self._stop_event.is_set():
            try:
                alerts = fetch_recent_alerts(
                    self.api_url,
                    self.api_user,
                    self.api_password,
                    since=self._last_poll,
                    limit=50,
                )
                for raw in alerts:
                    alert = parse_wazuh_alert(raw)
                    if alert:
                        try:
                            self.on_alert(alert)
                        except Exception as e:
                            logger.warning("Wazuh 告警处理失败: %s", e)

                self._last_poll = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                logger.warning("Wazuh 轮询失败: %s", e)

            self._stop_event.wait(self.poll_interval)
