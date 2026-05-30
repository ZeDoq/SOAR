"""
=====  Syslog 告警接入  =====

监听 UDP 端口接收 syslog 消息（RFC 3164 格式），
自动解析并转换为 SOAR 告警存入数据库。
"""

import logging
import re
import socket
import threading
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# RFC 3164 格式: <priority>timestamp hostname app[pid]: message
_SYSLOG_RE = re.compile(
    r"^<(\d+)>"
    r"(\w{3}\s+\d+\s+[\d:]+)\s+"
    r"(\S+)\s+"
    r"(\S+?)(?:\[(\d+)\])?:\s+"
    r"(.+)$"
)

_IP_RE = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")


def _extract_ip(text: str) -> Optional[str]:
    """从文本中提取第一个 IPv4 地址。"""
    match = _IP_RE.search(text)
    if match:
        return match.group(1)
    return None


def parse_syslog(raw: str) -> Optional[Dict[str, Any]]:
    """
    解析原始 syslog 消息为 SOAR 告警格式。

    优先从消息体提取 IP，找不到则使用 hostname 字段。

    Returns:
        SOAR 告警字典，解析失败返回 None
    """
    raw = raw.strip()
    if not raw:
        return None

    match = _SYSLOG_RE.match(raw)
    if match:
        hostname = match.group(3)
        app_name = match.group(4)
        message = match.group(6)
        description = f"[{app_name}] {message}" if app_name else message
    else:
        # 无法匹配标准格式，将整条消息作为描述
        hostname = "unknown"
        description = raw

    # 提取 IP：优先从消息体中找
    ip = _extract_ip(description)
    if not ip:
        ip = _extract_ip(hostname)
    if not ip:
        # hostname 本身可能是 IP
        ip = hostname if _extract_ip(hostname) else None
    if not ip:
        return None

    return {
        "ip": ip,
        "source": "syslog",
        "description": description[:500],
        "tags": ["syslog"],
    }


class SyslogListener:
    """
    UDP Syslog 监听器（后台线程）。

    用法:
        listener = SyslogListener(port=514, on_alert=my_callback)
        listener.start()
        # ... 运行中 ...
        listener.stop()
    """

    def __init__(self, port: int, on_alert: Callable[[Dict[str, Any]], None]):
        self.port = port
        self.on_alert = on_alert
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._socket: Optional[socket.socket] = None

    def start(self) -> None:
        """绑定 UDP socket 并启动接收线程。"""
        if self._thread and self._thread.is_alive():
            logger.warning("Syslog 监听器已在运行")
            return

        self._stop_event.clear()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(1.0)
        self._socket.bind(("0.0.0.0", self.port))

        self._thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._thread.start()
        logger.info("Syslog 监听器已启动，端口 %d", self.port)

    def stop(self) -> None:
        """停止监听器。"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        if self._socket:
            self._socket.close()
            self._socket = None
        logger.info("Syslog 监听器已停止")

    @property
    def is_alive(self) -> bool:
        """监听线程是否在运行。"""
        return self._thread is not None and self._thread.is_alive()

    def _receive_loop(self) -> None:
        """线程主循环：接收 UDP 数据包，解析并回调。"""
        while not self._stop_event.is_set():
            try:
                data, addr = self._socket.recvfrom(4096)
                raw = data.decode("utf-8", errors="replace")
                alert = parse_syslog(raw)
                if alert:
                    try:
                        self.on_alert(alert)
                    except Exception as e:
                        logger.warning("Syslog 告警处理失败: %s", e)
            except socket.timeout:
                continue
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.warning("Syslog 接收错误: %s", e)
