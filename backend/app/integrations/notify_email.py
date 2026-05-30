"""
=====  邮件通知服务  =====

当高风险安全事件发生时，通过 SMTP 发送邮件通知。
使用 Python 内置 smtplib，无需额外依赖。
SMTP 未配置时自动跳过。
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from .. import settings as settings_mod

logger = logging.getLogger(__name__)


def _parse_recipients(csv: str) -> List[str]:
    """解析逗号分隔的邮箱地址列表。"""
    if not csv:
        return []
    return [addr.strip() for addr in csv.split(",") if addr.strip()]


def send_alert_email(
    alert: Dict[str, Any],
    risk: Dict[str, Any],
    decision: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    发送安全事件邮件通知。

    Args:
        alert: 告警信息字典
        risk: 风险评估结果
        decision: 处置决策

    Returns:
        成功返回 {"channel": "email", "status": "sent", "recipients": [...]},
        未配置或失败返回 None
    """
    settings = settings_mod.settings

    if not settings.smtp_host:
        logger.debug("SMTP 未配置，跳过邮件通知")
        return None

    recipients = _parse_recipients(settings.smtp_to)
    if not recipients:
        logger.warning("SMTP_TO 为空，无收件人")
        return None

    ip = alert.get("ip", "unknown")
    score = risk.get("risk_score", 0)
    action = decision.get("action", "unknown")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[SOAR] 高风险告警: {ip} - 风险评分 {score}"
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = ", ".join(recipients)

    html = f"""
    <h2>SOAR 安全事件通知</h2>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
      <tr style="background:#1a1a2e;color:white;">
        <th colspan="2">事件详情</th>
      </tr>
      <tr><td><b>IP 地址</b></td><td>{ip}</td></tr>
      <tr><td><b>告警来源</b></td><td>{alert.get('source', 'N/A')}</td></tr>
      <tr><td><b>描述</b></td><td>{alert.get('description', 'N/A')}</td></tr>
      <tr><td><b>风险评分</b></td><td>{score}/100</td></tr>
      <tr><td><b>处置决策</b></td><td>{action}</td></tr>
      <tr><td><b>标签</b></td><td>{', '.join(alert.get('tags', []))}</td></tr>
    </table>
    <p style="color:#666;font-size:12px;">此邮件由 SOAR 系统自动发送</p>
    """

    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_user and settings.smtp_password:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(
                settings.smtp_from or settings.smtp_user,
                recipients,
                msg.as_string(),
            )
        logger.info("邮件通知已发送至 %s", recipients)
        return {
            "channel": "email",
            "status": "sent",
            "recipients": recipients,
        }
    except Exception as e:
        logger.warning("邮件发送失败: %s", e)
        return None
