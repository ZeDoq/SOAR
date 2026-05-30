"""
=====  Suricata EVE JSON 日志接入  =====

tail -f 方式监听 Suricata 的 EVE JSON 日志文件，
自动解析 alert 类型事件并转换为 SOAR 告警。
"""

import json
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


def parse_suricata_alert(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    将 Suricata EVE JSON 告警事件转换为 SOAR 告警格式。

    仅处理 event_type == "alert" 的条目。

    字段映射:
      - src_ip → ip
      - alert.signature → description
      - alert.category → tags
      - timestamp → observed_at
    """
    if raw.get("event_type") != "alert":
        return None

    ip = raw.get("src_ip")
    if not ip:
        return None

    alert_info = raw.get("alert", {})
    signature = alert_info.get("signature", "Suricata alert")
    category = alert_info.get("category", "")
    severity = alert_info.get("severity", 0)

    tags = ["suricata"]
    if category:
        tags.append(category.lower())
    tags.append(f"severity-{severity}")

    return {
        "ip": ip,
        "source": "suricata",
        "description": f"{signature} (severity: {severity})"[:500],
        "tags": tags,
    }


class SuricataTail:
    """
    Suricata EVE JSON 日志 tail 监听器（后台线程）。

    启动时 seek 到文件末尾，仅处理新增内容。

    用法:
        tail = SuricataTail("/var/log/suricata/eve.json", on_alert=my_callback)
        tail.start()
        # ... 运行中 ...
        tail.stop()
    """

    def __init__(self, log_path: str, on_alert: Callable[[Dict[str, Any]], None]):
        self.log_path = log_path
        self.on_alert = on_alert
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """启动 tail 线程。"""
        if self._thread and self._thread.is_alive():
            logger.warning("Suricata tail 已在运行")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._tail_loop, daemon=True)
        self._thread.start()
        logger.info("Suricata tail 已启动，监听 %s", self.log_path)

    def stop(self) -> None:
        """停止 tail。"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Suricata tail 已停止")

    @property
    def is_alive(self) -> bool:
        """tail 线程是否在运行。"""
        return self._thread is not None and self._thread.is_alive()

    def _tail_loop(self) -> None:
        """线程主循环：tail 日志文件，解析 JSON。"""
        try:
            f = open(self.log_path, "r", encoding="utf-8", errors="replace")
            f.seek(0, 2)  # seek 到文件末尾
        except FileNotFoundError:
            logger.error("Suricata 日志文件不存在: %s", self.log_path)
            return
        except Exception as e:
            logger.error("无法打开 Suricata 日志: %s", e)
            return

        try:
            while not self._stop_event.is_set():
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue

                line = line.strip()
                if not line:
                    continue

                try:
                    raw = json.loads(line)
                except json.JSONDecodeError:
                    continue

                alert = parse_suricata_alert(raw)
                if alert:
                    try:
                        self.on_alert(alert)
                    except Exception as e:
                        logger.warning("Suricata 告警处理失败: %s", e)
        finally:
            f.close()
