"""Attack chain detector - correlates alerts into multi-stage attack chains.

Uses temporal reasoning and ATT&CK tactic progression analysis
to identify which discrete alerts are likely stages of the same campaign.
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from .. import storage
from .temporal_reasoning import (
    detect_attack_chain_from_alerts,
    compute_tactic_progression_score,
    get_tactic_for_technique,
    TACTIC_ORDER,
)

logger = logging.getLogger(__name__)


def detect_chains(
    time_window_hours: int = 72,
    min_alerts: int = 2,
    min_confidence: float = 0.3,
) -> List[dict]:
    """Detect attack chains from recent alerts.

    1. Fetch recent alerts within time window
    2. Group by source IP
    3. Detect multi-stage progressions
    4. Return chains sorted by confidence
    """
    # Get recent alerts
    all_alerts = storage.list_alerts()

    if len(all_alerts) < min_alerts:
        return []

    # Detect chains
    chains = detect_attack_chain_from_alerts(all_alerts)

    # Filter by minimum confidence
    chains = [c for c in chains if c["confidence"] >= min_confidence]

    return chains


def get_chain_for_ip(ip: str) -> Optional[dict]:
    """Get the attack chain for a specific IP."""
    alerts = storage.list_alerts()
    ip_alerts = [a for a in alerts if a.get("ip") == ip]

    if len(ip_alerts) < 2:
        return None

    chains = detect_attack_chain_from_alerts(ip_alerts)
    return chains[0] if chains else None


def get_all_chains() -> List[dict]:
    """Get all detected attack chains."""
    return detect_chains()


def format_chain_for_display(chain: dict) -> dict:
    """Format an attack chain for frontend display with timeline data."""
    tactics = chain.get("tactics", [])
    techniques = chain.get("techniques", [])
    alert_ids = chain.get("alert_ids", [])

    # Build timeline stages
    stages = []
    for i, tactic in enumerate(tactics):
        stage = {
            "stage": i + 1,
            "tactic": tactic,
            "tactic_name": tactic.replace("-", " ").title(),
            "order": TACTIC_ORDER.index(tactic) if tactic in TACTIC_ORDER else -1,
        }
        if i < len(techniques):
            stage["technique"] = techniques[i]
        stages.append(stage)

    # Sort by tactic order
    stages.sort(key=lambda s: s["order"])

    return {
        "ip": chain.get("ip"),
        "confidence": chain.get("confidence"),
        "alert_count": chain.get("alert_count"),
        "alert_ids": alert_ids,
        "stages": stages,
        "first_seen": chain.get("first_seen"),
        "last_seen": chain.get("last_seen"),
        "progression_score": chain.get("progression_score"),
        "temporal_score": chain.get("temporal_score"),
    }
