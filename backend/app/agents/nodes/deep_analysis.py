"""Deep analysis node - RAG-enhanced AI analysis with risk assessment."""

import logging
from datetime import datetime, timezone

from ..state import SOARState
from ...ai import analyzer, knowledge_base
from ...integrations import risk_assessor
from ... import settings as settings_mod
from ... import storage

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def analyze_threat(state: SOARState) -> dict:
    """Perform threat analysis with RAG-enhanced context."""
    alert = state["alert"]
    intel = state.get("intel", {})
    run_id = state["run_id"]

    step = storage.create_step(run_id, "lg_analyze_threat", "running")

    try:
        # Rule-based risk assessment
        risk = risk_assessor.score(alert, intel, settings_mod.settings.simulated_latency_ms)

        # RAG-enhanced AI analysis
        ai_result = analyzer.analyze(alert, intel)
        confidence = 0.0

        if ai_result:
            ai_risk = analyzer.compute_ai_risk_score(ai_result)
            confidence = ai_result.get("confidence", 0.0)

            if confidence > 0.6:
                risk["risk_score"] = ai_risk
                risk["ai_analysis"] = ai_result
                risk["rationale"] = ai_result.get("reasoning", risk["rationale"])

        detail = {
            "risk_score": risk["risk_score"],
            "confidence": confidence,
            "ai_result": ai_result,
        }
        storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=detail)

        path = state.get("execution_path", [])
        path.append("analyze_threat")

        return {
            "risk": risk,
            "ai_result": ai_result,
            "confidence": confidence,
            "step_ids": {**state.get("step_ids", {}), "analyze_threat": step["id"]},
            "execution_path": path,
        }
    except Exception as e:
        logger.error("Analysis failed: %s", e)
        storage.update_step(step["id"], status="failed", finished_at=_utc_now(),
                            detail={"error": str(e)})
        path = state.get("execution_path", [])
        path.append("analyze_threat")
        return {
            "risk": {"risk_score": 50, "rationale": f"分析失败: {e}"},
            "confidence": 0.0,
            "execution_path": path,
        }


def deep_analysis(state: SOARState) -> dict:
    """Deep analysis with additional context when initial confidence is low."""
    alert = state["alert"]
    intel = state.get("intel", {})
    run_id = state["run_id"]
    iteration = state.get("iteration_count", 0)

    step = storage.create_step(run_id, f"lg_deep_analysis_{iteration}", "running")

    try:
        # Get richer context from RAG
        rich_context = knowledge_base.get_rich_context(alert)
        context_text = rich_context.get("context_text", "")

        # Re-analyze with richer context
        ai_result = analyzer.analyze(alert, intel, context_text)
        confidence = state.get("confidence", 0.0)
        risk = state.get("risk", {"risk_score": 50})

        if ai_result:
            new_confidence = ai_result.get("confidence", 0.0)
            if new_confidence > confidence:
                confidence = new_confidence
                ai_risk = analyzer.compute_ai_risk_score(ai_result)
                risk["risk_score"] = ai_risk
                risk["ai_analysis"] = ai_result
                risk["rationale"] = ai_result.get("reasoning", risk.get("rationale", ""))

        detail = {
            "iteration": iteration,
            "confidence_before": state.get("confidence", 0),
            "confidence_after": confidence,
            "techniques_found": len(rich_context.get("techniques", [])),
            "incidents_found": len(rich_context.get("incidents", [])),
        }
        storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail=detail)

        path = state.get("execution_path", [])
        path.append(f"deep_analysis_{iteration}")

        return {
            "risk": risk,
            "ai_result": ai_result,
            "confidence": confidence,
            "iteration_count": iteration + 1,
            "step_ids": {**state.get("step_ids", {}), f"deep_analysis_{iteration}": step["id"]},
            "execution_path": path,
        }
    except Exception as e:
        logger.error("Deep analysis failed: %s", e)
        storage.update_step(step["id"], status="failed", finished_at=_utc_now(),
                            detail={"error": str(e)})
        path = state.get("execution_path", [])
        path.append(f"deep_analysis_{iteration}")
        return {
            "iteration_count": iteration + 1,
            "execution_path": path,
        }
