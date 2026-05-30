"""AI-powered report generator."""

import json
import logging
from typing import Any, Dict, Optional

from .llm_client import chat
from .prompts import SYSTEM_ANALYST, build_report_prompt

logger = logging.getLogger(__name__)


def generate_report(
    alert: dict, intel: dict, risk: dict, decision: dict
) -> Optional[str]:
    """Generate a Markdown incident report using LLM. Returns None if unavailable."""
    prompt = build_report_prompt(alert, intel, risk, decision)
    result = chat(SYSTEM_ANALYST, prompt, temperature=0.4)
    if result:
        logger.info("Generated report for IP %s", alert.get("ip"))
    return result or None
