"""AI-powered threat analysis engine with fallback to rule-based scoring."""

import logging
from typing import Any, Dict, Optional

from .llm_client import chat_json
from .prompts import SYSTEM_ANALYST, build_analysis_prompt

logger = logging.getLogger(__name__)


def analyze(alert: dict, intel: dict, context: str = "") -> Optional[Dict[str, Any]]:
    """
    Use LLM to analyze a security event. Returns None if LLM unavailable.
    """
    prompt = build_analysis_prompt(alert, intel, context)
    result = chat_json(SYSTEM_ANALYST, prompt)
    if result:
        logger.info("AI analysis completed for IP %s", alert.get("ip"))
    return result


def compute_ai_risk_score(ai_result: dict) -> int:
    """Convert AI threat_level to a risk score (0-100)."""
    level_scores = {
        "malicious": 90,
        "suspicious": 60,
        "benign": 20,
        "false_positive": 5,
    }
    base = level_scores.get(ai_result.get("threat_level", ""), 50)
    confidence = ai_result.get("confidence", 0.5)
    return min(100, int(base * confidence + 50 * (1 - confidence)))
