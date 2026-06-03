"""Consensus scoring and disagreement detection for the debate system."""

from typing import List, Dict, Any
from .personas import VERDICT_SEVERITY


def compute_consensus(verdicts: List[dict]) -> dict:
    """Compute consensus metrics from a list of agent verdicts.

    Each verdict dict should have: agent_name, verdict, confidence.

    Returns:
        dict with keys: agreement_score, consensus_verdict, is_unanimous,
        disagreements, needs_human_review
    """
    if not verdicts:
        return {
            "agreement_score": 0.0,
            "consensus_verdict": "unknown",
            "is_unanimous": False,
            "disagreements": [],
            "needs_human_review": True,
        }

    # Extract verdicts and confidences
    verdict_list = [v.get("verdict", "unknown") for v in verdicts]
    confidence_list = [v.get("confidence", 0.5) for v in verdicts]

    # Count verdict distribution
    verdict_counts: Dict[str, int] = {}
    for v in verdict_list:
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    # Most common verdict
    consensus_verdict = max(verdict_counts, key=verdict_counts.get)
    consensus_count = verdict_counts[consensus_verdict]
    total = len(verdict_list)

    # Agreement score: fraction of agents agreeing on the consensus verdict
    agreement_score = consensus_count / total

    # Check if unanimous
    is_unanimous = len(verdict_counts) == 1

    # Identify disagreements
    disagreements = []
    for v in verdicts:
        if v.get("verdict") != consensus_verdict:
            disagreements.append({
                "agent": v.get("agent_name", "unknown"),
                "verdict": v.get("verdict"),
                "vs_consensus": consensus_verdict,
            })

    # Average confidence weighted by agreement
    avg_confidence = sum(confidence_list) / len(confidence_list)

    # Needs human review if agents strongly disagree
    # (e.g., one says malicious, another says benign)
    severity_values = [VERDICT_SEVERITY.get(v, 2) for v in verdict_list]
    severity_spread = max(severity_values) - min(severity_values) if severity_values else 0
    needs_human_review = severity_spread >= 3 or agreement_score < 0.5

    return {
        "agreement_score": round(agreement_score, 2),
        "consensus_verdict": consensus_verdict,
        "consensus_confidence": round(avg_confidence * agreement_score, 2),
        "is_unanimous": is_unanimous,
        "verdict_distribution": verdict_counts,
        "disagreements": disagreements,
        "needs_human_review": needs_human_review,
        "severity_spread": severity_spread,
    }
