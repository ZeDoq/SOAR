"""Debate engine - orchestrates multi-agent debate rounds."""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from .personas import PERSONAS
from .consensus import compute_consensus
from .moderator import synthesize
from ...ai.llm_client import chat_json
from ... import storage

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_persona_analysis(
    persona_key: str,
    alert: dict,
    intel: dict,
    context: str = "",
    previous_verdicts: Optional[List[dict]] = None,
) -> dict:
    """Run a single persona's analysis on an alert.

    Args:
        persona_key: Key in PERSONAS dict
        alert: Alert data
        intel: Threat intelligence
        context: Additional context (RAG results, etc.)
        previous_verdicts: Other agents' verdicts for cross-examination
    """
    persona = PERSONAS[persona_key]

    prompt = f"""请分析以下安全事件：

## 告警信息
- IP: {alert.get('ip')}
- 来源: {alert.get('source')}
- 描述: {alert.get('description')}
- 标签: {', '.join(alert.get('tags', []))}

## 威胁情报
- 信誉: {intel.get('reputation', 'unknown')}
- 置信度: {intel.get('confidence', 0)}
- 信号值: {intel.get('signal', 0)}
"""

    if context:
        prompt += f"\n## 知识库上下文\n{context}\n"

    # Cross-examination: show previous verdicts
    if previous_verdicts:
        prompt += "\n## 其他分析师的观点（请交叉验证）\n"
        for v in previous_verdicts:
            prompt += f"- {v.get('agent_name', 'Unknown')}: {v.get('verdict')} "
            prompt += f"(置信度: {v.get('confidence', 0)}) - {v.get('reasoning', '')[:200]}\n"

    result = chat_json(persona["system_prompt"], prompt)
    if result:
        result["agent_name"] = persona["name"]
        result["persona"] = persona_key
        result["icon"] = persona["icon"]
        result["color"] = persona["color"]
    return result


def run_debate(
    alert: dict,
    intel: dict,
    run_id: Optional[int] = None,
    context: str = "",
) -> dict:
    """Run a full multi-agent debate on a security alert.

    Protocol:
    1. Round 1: Independent analysis (all 3 agents in parallel conceptually)
    2. Round 2: Cross-examination (agents see others' reasoning)
    3. Round 3: Moderator synthesis

    Returns dict with: rounds, verdicts, consensus, moderator_verdict, transcript_id
    """
    debate_start = _utc_now()
    transcript = {
        "alert_id": alert.get("id"),
        "run_id": run_id,
        "started_at": debate_start,
        "rounds": [],
        "verdicts": [],
        "consensus": None,
        "moderator_verdict": None,
    }

    # Get RAG context if not provided
    if not context:
        try:
            from ...ai import knowledge_base
            rich_ctx = knowledge_base.get_rich_context(alert)
            context = rich_ctx.get("context_text", "")
        except Exception:
            pass

    # === Round 1: Independent Analysis ===
    round1_verdicts = []
    for persona_key in PERSONAS:
        try:
            result = _run_persona_analysis(persona_key, alert, intel, context)
            if result:
                round1_verdicts.append(result)
                logger.info("[Debate R1] %s: %s (confidence: %.2f)",
                            persona_key, result.get("verdict"), result.get("confidence", 0))
        except Exception as e:
            logger.warning("[Debate R1] %s failed: %s", persona_key, e)

    transcript["rounds"].append({
        "round": 1,
        "name": "独立分析",
        "verdicts": round1_verdicts,
    })

    # === Round 2: Cross-Examination ===
    round2_verdicts = []
    for persona_key in PERSONAS:
        try:
            # Each agent sees the others' Round 1 verdicts
            others = [v for v in round1_verdicts if v.get("persona") != persona_key]
            result = _run_persona_analysis(
                persona_key, alert, intel, context,
                previous_verdicts=others,
            )
            if result:
                round2_verdicts.append(result)
                logger.info("[Debate R2] %s: %s (confidence: %.2f)",
                            persona_key, result.get("verdict"), result.get("confidence", 0))
        except Exception as e:
            logger.warning("[Debate R2] %s failed: %s", persona_key, e)

    transcript["rounds"].append({
        "round": 2,
        "name": "交叉质疑",
        "verdicts": round2_verdicts,
    })

    # Use Round 2 verdicts as final (agents may have updated their views)
    final_verdicts = round2_verdicts if round2_verdicts else round1_verdicts
    transcript["verdicts"] = final_verdicts

    # === Consensus Scoring ===
    consensus = compute_consensus(final_verdicts)
    transcript["consensus"] = consensus

    # === Round 3: Moderator Synthesis ===
    try:
        moderator_result = synthesize(alert, intel, final_verdicts, consensus)
        if moderator_result:
            transcript["moderator_verdict"] = moderator_result
            logger.info("[Debate Moderator] Final: %s (confidence: %.2f)",
                        moderator_result.get("final_verdict"),
                        moderator_result.get("final_confidence", 0))
    except Exception as e:
        logger.warning("[Debate Moderator] Synthesis failed: %s", e)

    transcript["finished_at"] = _utc_now()

    # Store in database
    if run_id:
        _store_debate(transcript)

    return transcript


def _store_debate(transcript: dict) -> None:
    """Store debate transcript in the database."""
    try:
        conn = storage._connect()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO debates (run_id, alert_id, started_at, finished_at,
               rounds, verdicts, consensus, moderator_verdict)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                transcript.get("run_id"),
                transcript.get("alert_id"),
                transcript.get("started_at"),
                transcript.get("finished_at"),
                json.dumps(transcript.get("rounds", []), ensure_ascii=False),
                json.dumps(transcript.get("verdicts", []), ensure_ascii=False),
                json.dumps(transcript.get("consensus", {}), ensure_ascii=False),
                json.dumps(transcript.get("moderator_verdict", {}), ensure_ascii=False),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Failed to store debate: %s", e)
