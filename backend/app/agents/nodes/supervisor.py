"""Supervisor node - routing decisions for the LangGraph orchestrator."""

import logging
from ..state import SOARState

logger = logging.getLogger(__name__)

# Confidence thresholds for routing
HIGH_CONFIDENCE = 0.8
LOW_CONFIDENCE = 0.5


def route_after_gather(state: SOARState) -> str:
    """Route after initial intelligence gathering.

    - If intel is clearly malicious/benign with high signal -> fast-track to response
    - Otherwise -> analyze
    """
    intel = state.get("intel", {})
    reputation = intel.get("reputation", "unknown")
    confidence = intel.get("confidence", 0.0)

    # High-confidence intel signals can skip deep analysis
    if reputation in ("malicious", "benign") and confidence > 0.85:
        logger.info("High-confidence intel (%s, %.2f), fast-tracking to response",
                     reputation, confidence)
        return "fast_response"

    return "analyze"


def route_after_analysis(state: SOARState) -> str:
    """Route after threat analysis based on confidence level.

    - confidence >= HIGH_CONFIDENCE: proceed to response
    - confidence < LOW_CONFIDENCE and iterations < max: loop back for deep analysis
    - otherwise: proceed to response
    """
    confidence = state.get("confidence", 0.0)
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 3)

    if confidence >= HIGH_CONFIDENCE:
        logger.info("High confidence (%.2f), proceeding to response", confidence)
        return "respond"

    if confidence < LOW_CONFIDENCE and iteration < max_iter:
        logger.info("Low confidence (%.2f), iteration %d/%d, deepening analysis",
                     confidence, iteration + 1, max_iter)
        return "deepen"

    logger.info("Confidence %.2f after %d iterations, proceeding to response",
                confidence, iteration)
    return "respond"


def synthesize_decision(state: SOARState) -> dict:
    """Synthesize final decision from fast-track intel signals."""
    intel = state.get("intel", {})
    reputation = intel.get("reputation", "unknown")
    confidence = intel.get("confidence", 0.0)

    # Create a synthetic risk assessment from intel alone
    risk_score = {
        "malicious": 85,
        "suspicious": 55,
        "benign": 15,
        "unknown": 50,
    }.get(reputation, 50)

    risk = {
        "risk_score": risk_score,
        "rationale": f"基于威胁情报快速判定: {reputation} (置信度: {confidence:.2f})",
        "signals": intel,
    }

    path = state.get("execution_path", [])
    path.append("synthesize_decision")

    return {
        "risk": risk,
        "confidence": confidence,
        "execution_path": path,
    }
