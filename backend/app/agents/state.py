"""Shared state definition for LangGraph-based SOAR orchestrator."""

from typing import TypedDict, Optional, List, Any


class SOARState(TypedDict):
    """State passed between nodes in the LangGraph execution graph."""

    # Input
    run_id: int
    alert: dict

    # Intelligence gathering results
    intel: Optional[dict]
    recon_result: Optional[dict]

    # Analysis results
    risk: Optional[dict]
    ai_result: Optional[dict]
    confidence: float  # 0.0 - 1.0

    # Decision
    decision: Optional[dict]
    report: Optional[str]

    # Control flow
    iteration_count: int
    max_iterations: int
    execution_path: List[str]  # Track which nodes were visited

    # Storage step IDs for DB updates
    step_ids: dict  # node_name -> step_id
