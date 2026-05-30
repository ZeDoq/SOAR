"""
=====  Slack 通知服务  =====

通过 Slack Incoming Webhook 发送安全事件通知。
使用 httpx 发送 HTTP POST（延迟导入）。
Webhook URL 未配置时自动跳过。
"""

import logging
from typing import Any, Dict, Optional

from .. import settings as settings_mod

logger = logging.getLogger(__name__)


def send_slack_alert(
    alert: Dict[str, Any],
    risk: Dict[str, Any],
    decision: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    发送 Slack 安全事件通知。

    使用 Block Kit 格式，按风险分数着色：
      - >= 70: 红色（高风险）
      - >= 40: 黄色（中风险）
      - < 40:  绿色（低风险）

    Args:
        alert: 告警信息字典
        risk: 风险评估结果
        decision: 处置决策

    Returns:
        成功返回 {"channel": "slack", "status": "sent"},
        未配置或失败返回 None
    """
    settings = settings_mod.settings

    if not settings.slack_webhook_url:
        logger.debug("Slack Webhook 未配置，跳过通知")
        return None

    try:
        import httpx
    except ImportError:
        logger.warning("httpx 未安装，无法发送 Slack 通知")
        return None

    score = risk.get("risk_score", 0)
    if score >= 70:
        color = "#ff0000"
    elif score >= 40:
        color = "#ffaa00"
    else:
        color = "#00ff00"

    ip = alert.get("ip", "unknown")
    payload = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"SOAR Alert: {ip}",
                        },
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Risk Score:*\n{score}/100",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Decision:*\n{decision.get('action', 'unknown')}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Source:*\n{alert.get('source', 'N/A')}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Description:*\n{alert.get('description', '')[:200]}",
                            },
                        ],
                    },
                ],
            }
        ]
    }

    try:
        resp = httpx.post(
            settings.slack_webhook_url,
            json=payload,
            timeout=10.0,
        )
        resp.raise_for_status()
        logger.info("Slack 通知已发送 (IP: %s)", ip)
        return {"channel": "slack", "status": "sent"}
    except Exception as e:
        logger.warning("Slack 通知发送失败: %s", e)
        return None
