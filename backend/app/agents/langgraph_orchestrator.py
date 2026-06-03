"""LangGraph-based dynamic orchestrator for SOAR.

Replaces the rigid sequential pipeline with a state machine that enables:
- Conditional branching based on threat confidence
- Iterative deep analysis when confidence is low
- Fast-track response for high-confidence intel
- Full execution path tracking for visualization
"""

import logging
from datetime import datetime, timezone

from langgraph.graph import StateGraph, START, END

from .state import SOARState
from .nodes.gather_intel import gather_intel
from .nodes.deep_analysis import analyze_threat, deep_analysis
from .nodes.response_executor import execute_response
from .nodes.supervisor import route_after_gather, route_after_analysis, synthesize_decision
from .. import storage

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_graph() -> StateGraph:
    """Build the LangGraph state machine for SOAR orchestration."""

    graph = StateGraph(SOARState)

    # Add nodes
    graph.add_node("gather_intel", gather_intel)
    graph.add_node("analyze_threat", analyze_threat)
    graph.add_node("deep_analysis", deep_analysis)
    graph.add_node("synthesize_decision", synthesize_decision)
    graph.add_node("execute_response", execute_response)

    # Entry: always start with intel gathering
    graph.add_edge(START, "gather_intel")

    # After intel: fast-track or analyze
    graph.add_conditional_edges(
        "gather_intel",
        route_after_gather,
        {
            "fast_response": "synthesize_decision",
            "analyze": "analyze_threat",
        },
    )

    # After analysis: respond or deepen
    graph.add_conditional_edges(
        "analyze_threat",
        route_after_analysis,
        {
            "respond": "execute_response",
            "deepen": "deep_analysis",
        },
    )

    # After deep analysis: re-evaluate
    graph.add_conditional_edges(
        "deep_analysis",
        route_after_analysis,
        {
            "respond": "execute_response",
            "deepen": "deep_analysis",
        },
    )

    # After synthesize (fast-track): go to response
    graph.add_edge("synthesize_decision", "execute_response")

    # After response: end
    graph.add_edge("execute_response", END)

    return graph


# Compile the graph once at module level
_compiled_graph = None


def get_compiled_graph():
    """Get or compile the LangGraph state machine."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph().compile()
    return _compiled_graph


def get_graph_mermaid() -> str:
    """Export the graph as a Mermaid diagram string for frontend visualization."""
    graph = _build_graph()
    compiled = graph.compile()
    try:
        return compiled.get_graph().draw_mermaid()
    except Exception:
        return "graph TD\n  A[gather_intel] --> B[analyze_threat]\n  B --> C[execute_response]"


def execute_langgraph_playbook(run_id: int) -> None:
    """Execute the LangGraph-based dynamic playbook.

    This is the main entry point called from the API route.
    """
    run = storage.get_run(run_id)
    if not run:
        return

    alert = storage.get_alert(run["alert_id"])
    if not alert:
        storage.update_run(run_id, status="failed", finished_at=_utc_now())
        return

    storage.update_run(run_id, status="running", started_at=_utc_now())
    logger.info("Starting LangGraph playbook for run %d, IP: %s", run_id, alert["ip"])

    # Initial state
    initial_state: SOARState = {
        "run_id": run_id,
        "alert": alert,
        "intel": None,
        "recon_result": None,
        "risk": None,
        "ai_result": None,
        "confidence": 0.0,
        "decision": None,
        "report": None,
        "iteration_count": 0,
        "max_iterations": 3,
        "execution_path": [],
        "step_ids": {},
    }

    try:
        compiled = get_compiled_graph()
        final_state = compiled.invoke(initial_state)

        # Extract final results
        risk = final_state.get("risk", {"risk_score": 0})
        decision = final_state.get("decision", {"action": "monitor"})
        execution_path = final_state.get("execution_path", [])

        # Store execution path in decision for frontend visualization
        decision["execution_path"] = execution_path
        decision["orchestrator"] = "langgraph"

        storage.update_run(
            run_id,
            status="completed",
            finished_at=_utc_now(),
            risk_score=risk.get("risk_score", 0),
            decision=decision,
        )
        logger.info("LangGraph playbook completed for run %d: path=%s, risk=%d, action=%s",
                     run_id, " -> ".join(execution_path),
                     risk.get("risk_score", 0), decision.get("action", "unknown"))

    except Exception as exc:
        logger.error("LangGraph playbook failed for run %d: %s", run_id, exc)
        storage.update_run(run_id, status="failed", finished_at=_utc_now(),
                           decision={"error": str(exc), "orchestrator": "langgraph"})
