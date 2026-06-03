"""Temporal reasoning for attack chain detection.

Provides ATT&CK tactic ordering and temporal correlation analysis
to detect multi-stage attack progressions.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

# MITRE ATT&CK Enterprise tactical ordering (kill chain progression)
TACTIC_ORDER = [
    "reconnaissance",
    "resource-development",
    "initial-access",
    "execution",
    "persistence",
    "privilege-escalation",
    "defense-evasion",
    "credential-access",
    "discovery",
    "lateral-movement",
    "collection",
    "command-and-control",
    "exfiltration",
    "impact",
]

TACTIC_INDEX = {t: i for i, t in enumerate(TACTIC_ORDER)}

# Maps technique IDs to their primary tactic
TECHNIQUE_TACTIC_MAP = {
    "T1110": "credential-access",
    "T1071": "command-and-control",
    "T1048": "exfiltration",
    "T1021": "lateral-movement",
    "T1190": "initial-access",
    "T1566": "initial-access",
    "T1059": "execution",
    "T1053": "persistence",
    "T1078": "defense-evasion",
    "T1498": "impact",
    "T1046": "discovery",
    "T1070": "defense-evasion",
    "T1003": "credential-access",
    "T1041": "exfiltration",
    "T1486": "impact",
    "T1195": "initial-access",
    "T1068": "execution",
    "T1547": "persistence",
    "T1543": "persistence",
    "T1055": "privilege-escalation",
    "T1218": "defense-evasion",
    "T1082": "discovery",
    "T1083": "discovery",
    "T1057": "discovery",
    "T1018": "discovery",
    "T1569": "execution",
}


def get_tactic_for_technique(technique_id: str) -> Optional[str]:
    """Get the primary ATT&CK tactic for a technique ID."""
    return TECHNIQUE_TACTIC_MAP.get(technique_id.upper())


def compute_tactic_progression_score(tactics: List[str]) -> float:
    """Score how well a sequence of tactics follows a valid attack progression.

    A valid progression should have monotonically increasing tactic indices
    (or at least non-decreasing), representing the natural flow of an attack.

    Returns 0.0-1.0 where 1.0 = perfect progression.
    """
    if len(tactics) < 2:
        return 1.0

    indices = [TACTIC_INDEX.get(t, -1) for t in tactics]
    valid_indices = [i for i in indices if i >= 0]

    if len(valid_indices) < 2:
        return 0.5

    # Count forward progressions vs backward jumps
    forward = 0
    total_pairs = len(valid_indices) - 1
    for i in range(total_pairs):
        if valid_indices[i + 1] >= valid_indices[i]:
            forward += 1

    return forward / total_pairs if total_pairs > 0 else 0.0


def compute_temporal_proximity(
    timestamps: List[str],
    max_window_hours: int = 72,
) -> float:
    """Score temporal proximity of events.

    Events within a shorter window get higher scores.
    Returns 0.0-1.0 where 1.0 = events are very close in time.
    """
    if len(timestamps) < 2:
        return 1.0

    try:
        times = []
        for ts in timestamps:
            if isinstance(ts, str):
                try:
                    times.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
                except (ValueError, AttributeError):
                    continue
        if len(times) < 2:
            return 0.5

        times.sort()
        span = (times[-1] - times[0]).total_seconds() / 3600  # hours

        if span <= 0:
            return 1.0
        if span >= max_window_hours:
            return 0.0

        return max(0.0, 1.0 - (span / max_window_hours))
    except Exception:
        return 0.5


def detect_attack_chain_from_alerts(alerts: List[dict]) -> List[dict]:
    """Detect attack chains from a list of related alerts.

    Groups alerts by IP, orders temporally, maps to tactics,
    and validates progression.

    Returns list of detected chains with confidence scores.
    """
    if len(alerts) < 2:
        return []

    # Group by source IP
    ip_groups: Dict[str, List[dict]] = {}
    for alert in alerts:
        ip = alert.get("ip", "unknown")
        if ip not in ip_groups:
            ip_groups[ip] = []
        ip_groups[ip].append(alert)

    chains = []

    for ip, group in ip_groups.items():
        if len(group) < 2:
            continue

        # Sort by time
        group.sort(key=lambda a: a.get("observed_at", ""))

        # Extract tactics from tags and descriptions
        tactics = []
        techniques = []
        for alert in group:
            tags = alert.get("tags", [])
            desc = alert.get("description", "").lower()

            # Try to match technique from tags
            for tag in tags:
                tag_upper = tag.upper()
                if tag_upper.startswith("T") and tag_upper[1:].isdigit():
                    tactic = get_tactic_for_technique(tag_upper)
                    if tactic:
                        tactics.append(tactic)
                        techniques.append(tag_upper)
                        break

            # If no technique found from tags, infer from keywords
            if not tactics or len(tactics) < len(group):
                from ..ai.knowledge_base import _keyword_search
                results = _keyword_search(desc + " " + " ".join(tags), top_k=1)
                if results:
                    tactic = results[0].get("tactic", "")
                    if tactic and tactic not in tactics:
                        tactics.append(tactic)

        # Compute chain confidence
        progression_score = compute_tactic_progression_score(tactics)
        timestamps = [a.get("observed_at", "") for a in group]
        temporal_score = compute_temporal_proximity(timestamps)

        # Combined confidence
        confidence = 0.6 * progression_score + 0.4 * temporal_score

        if confidence > 0.3:  # Minimum threshold for chain detection
            chains.append({
                "ip": ip,
                "alert_count": len(group),
                "alert_ids": [a.get("id") for a in group],
                "tactics": tactics,
                "techniques": list(set(techniques)),
                "progression_score": round(progression_score, 2),
                "temporal_score": round(temporal_score, 2),
                "confidence": round(confidence, 2),
                "first_seen": group[0].get("observed_at", ""),
                "last_seen": group[-1].get("observed_at", ""),
            })

    chains.sort(key=lambda c: -c["confidence"])
    return chains
