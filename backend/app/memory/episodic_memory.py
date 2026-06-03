"""Episodic memory for learning from past security incidents.

Stores completed incidents with embeddings for similarity search,
enabling the system to recall relevant past experiences.
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

from .. import storage

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def store_episode(
    alert: dict,
    run_id: int,
    verdict: str,
    confidence: float,
    risk_score: int,
    reasoning: str = "",
    feedback: str = "",
    feedback_reason: str = "",
) -> int:
    """Store a completed incident as an episodic memory.

    Returns the episode ID.
    """
    # Build searchable text for embedding
    parts = [
        alert.get("description", ""),
        alert.get("ip", ""),
        " ".join(alert.get("tags", [])),
        verdict,
        reasoning[:500],
    ]
    searchable_text = " ".join(filter(None, parts))

    conn = storage._connect()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO episodes
           (alert_id, run_id, ip, description, tags, verdict, confidence,
            risk_score, reasoning, feedback, feedback_reason, searchable_text, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            alert.get("id"),
            run_id,
            alert.get("ip", ""),
            alert.get("description", ""),
            json.dumps(alert.get("tags", []), ensure_ascii=False),
            verdict,
            confidence,
            risk_score,
            reasoning,
            feedback,
            feedback_reason,
            searchable_text,
            _utc_now(),
        ),
    )
    episode_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info("Stored episode %d for IP %s, verdict=%s", episode_id, alert.get("ip"), verdict)
    return episode_id


def search_similar_incidents(alert: dict, top_k: int = 3) -> List[dict]:
    """Search for similar past incidents using text similarity.

    Returns list of similar episodes with their outcomes.
    """
    query_parts = [
        alert.get("description", ""),
        alert.get("ip", ""),
        " ".join(alert.get("tags", [])),
    ]
    query_text = " ".join(filter(None, query_parts))
    if not query_text.strip():
        return []

    # Try RAG-based search first
    try:
        from ..ai import rag_engine
        results = rag_engine.hybrid_search(
            query_text, top_k=top_k, where={"type": "episode"}
        )
        if results:
            return [
                {
                    "id": r["id"],
                    "description": r["document"][:300],
                    "relevance": r["relevance"],
                    "metadata": r["metadata"],
                }
                for r in results
            ]
    except Exception:
        pass

    # Fallback: SQL-based search using LIKE
    conn = storage._connect()
    cursor = conn.cursor()
    ip = alert.get("ip", "")
    desc = alert.get("description", "")[:50]
    rows = cursor.execute(
        """SELECT * FROM episodes
           WHERE ip LIKE ? OR description LIKE ? OR tags LIKE ?
           ORDER BY created_at DESC LIMIT ?""",
        (f"%{ip}%", f"%{desc}%",
         f"%{''.join(alert.get('tags', []))[:30]}%",
         top_k),
    ).fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "ip": row["ip"],
            "description": row["description"],
            "verdict": row["verdict"],
            "confidence": row["confidence"],
            "risk_score": row["risk_score"],
            "feedback": row["feedback"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def get_episode_stats() -> dict:
    """Get statistics about stored episodes."""
    conn = storage._connect()
    cursor = conn.cursor()
    total = cursor.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
    by_verdict = {}
    for row in cursor.execute(
        "SELECT verdict, COUNT(*) as cnt FROM episodes GROUP BY verdict"
    ).fetchall():
        by_verdict[row["verdict"]] = row["cnt"]
    by_feedback = {}
    for row in cursor.execute(
        "SELECT feedback, COUNT(*) as cnt FROM episodes WHERE feedback != '' GROUP BY feedback"
    ).fetchall():
        by_feedback[row["feedback"]] = row["cnt"]
    conn.close()
    return {
        "total_episodes": total,
        "by_verdict": by_verdict,
        "by_feedback": by_feedback,
    }
