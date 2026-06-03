"""Feedback loop and risk calibration based on analyst feedback.

Tracks false positive rates and auto-adjusts playbook thresholds
to improve accuracy over time.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from .. import storage

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def submit_feedback(
    run_id: int,
    feedback: str,
    reason: str = "",
) -> dict:
    """Submit analyst feedback on a run's verdict.

    Args:
        run_id: The run to provide feedback on
        feedback: 'confirm' | 'false_positive' | 'false_negative' | 'override'
        reason: Explanation for the feedback

    Returns dict with the feedback record.
    """
    if feedback not in ("confirm", "false_positive", "false_negative", "override"):
        raise ValueError(f"Invalid feedback: {feedback}")

    conn = storage._connect()
    cursor = conn.cursor()

    # Check if feedback already exists for this run
    existing = cursor.execute(
        "SELECT id FROM feedback WHERE run_id = ?", (run_id,)
    ).fetchone()

    if existing:
        # Update existing feedback
        cursor.execute(
            """UPDATE feedback SET feedback = ?, reason = ?, created_at = ?
               WHERE run_id = ?""",
            (feedback, reason, _utc_now(), run_id),
        )
    else:
        cursor.execute(
            """INSERT INTO feedback (run_id, feedback, reason, created_at)
               VALUES (?, ?, ?, ?)""",
            (run_id, feedback, reason, _utc_now()),
        )

    # Also update the episode if it exists
    cursor.execute(
        "UPDATE episodes SET feedback = ?, feedback_reason = ? WHERE run_id = ?",
        (feedback, reason, run_id),
    )

    conn.commit()
    conn.close()

    logger.info("Feedback submitted for run %d: %s", run_id, feedback)

    # Recalibrate thresholds
    _recalibrate_thresholds()

    return {"run_id": run_id, "feedback": feedback, "reason": reason}


def get_feedback_for_run(run_id: int) -> Optional[dict]:
    """Get feedback for a specific run."""
    conn = storage._connect()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT * FROM feedback WHERE run_id = ?", (run_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "run_id": row["run_id"],
        "feedback": row["feedback"],
        "reason": row["reason"],
        "created_at": row["created_at"],
    }


def get_feedback_stats() -> dict:
    """Get overall feedback statistics."""
    conn = storage._connect()
    cursor = conn.cursor()
    total = cursor.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    by_type = {}
    for row in cursor.execute(
        "SELECT feedback, COUNT(*) as cnt FROM feedback GROUP BY feedback"
    ).fetchall():
        by_type[row["feedback"]] = row["cnt"]
    conn.close()

    fp_count = by_type.get("false_positive", 0)
    fn_count = by_type.get("false_negative", 0)
    confirm_count = by_type.get("confirm", 0)
    total_with_feedback = fp_count + fn_count + confirm_count

    return {
        "total_feedback": total,
        "by_type": by_type,
        "false_positive_rate": round(fp_count / max(total_with_feedback, 1), 2),
        "false_negative_rate": round(fn_count / max(total_with_feedback, 1), 2),
        "confirmation_rate": round(confirm_count / max(total_with_feedback, 1), 2),
    }


def _recalibrate_thresholds() -> None:
    """Recalibrate playbook selection thresholds based on feedback.

    If a playbook type has a high false positive rate, raise its threshold.
    If it has a high false negative rate, lower its threshold.
    """
    conn = storage._connect()
    cursor = conn.cursor()

    # Get feedback grouped by attack type (from run decisions)
    rows = cursor.execute(
        """SELECT f.feedback, r.decision
           FROM feedback f
           JOIN runs r ON f.run_id = r.id
           WHERE r.decision IS NOT NULL"""
    ).fetchall()
    conn.close()

    # Count FP/FN by attack type
    type_stats = {}
    for row in rows:
        try:
            decision = json.loads(row["decision"]) if row["decision"] else {}
        except (json.JSONDecodeError, TypeError):
            continue

        # Extract attack type from decision
        template = decision.get("template", "full_investigation")
        if template not in type_stats:
            type_stats[template] = {"fp": 0, "fn": 0, "confirm": 0, "total": 0}
        type_stats[template]["total"] += 1
        fb = row["feedback"]
        if fb == "false_positive":
            type_stats[template]["fp"] += 1
        elif fb == "false_negative":
            type_stats[template]["fn"] += 1
        elif fb == "confirm":
            type_stats[template]["confirm"] += 1

    # Store calibration results
    calibration = {}
    for attack_type, stats in type_stats.items():
        if stats["total"] < 3:
            continue  # Need minimum samples
        fp_rate = stats["fp"] / stats["total"]
        fn_rate = stats["fn"] / stats["total"]

        adjustment = 0
        if fp_rate > 0.3:
            adjustment = min(10, int(fp_rate * 15))  # Raise threshold
        elif fn_rate > 0.3:
            adjustment = -min(10, int(fn_rate * 15))  # Lower threshold

        calibration[attack_type] = {
            "fp_rate": round(fp_rate, 2),
            "fn_rate": round(fn_rate, 2),
            "threshold_adjustment": adjustment,
            "sample_count": stats["total"],
        }

    logger.info("Threshold calibration: %s", calibration)
    return calibration


def get_calibrated_threshold(attack_type: str, base_threshold: int) -> int:
    """Get the calibrated threshold for an attack type.

    Returns the base threshold adjusted by feedback history.
    """
    calibration = _recalibrate_thresholds()
    if attack_type in calibration:
        adjustment = calibration[attack_type].get("threshold_adjustment", 0)
        return max(10, min(100, base_threshold + adjustment))
    return base_threshold
