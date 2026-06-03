"""Gather intelligence node - collects threat intel and basic recon."""

import logging
from typing import Any, Dict

from ..state import SOARState
from ...integrations import threat_intel, recon
from ... import settings as settings_mod
from ... import storage
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def gather_intel(state: SOARState) -> dict:
    """Collect threat intelligence for the alert IP."""
    alert = state["alert"]
    run_id = state["run_id"]

    step = storage.create_step(run_id, "lg_gather_intel", "running")

    try:
        intel = threat_intel.lookup(alert["ip"], settings_mod.settings.simulated_latency_ms)

        # Basic recon
        recon_result: Dict[str, Any] = {}
        try:
            whois_data = recon.whois_lookup(alert["ip"])
            if whois_data:
                recon_result["whois"] = whois_data
            dns_data = recon.dns_lookup(alert["ip"])
            if dns_data:
                recon_result["dns"] = dns_data
        except Exception as e:
            logger.warning("Recon failed: %s", e)

        storage.update_step(step["id"], status="completed", finished_at=_utc_now(), detail={
            "intel": intel, "recon": recon_result
        })

        path = state.get("execution_path", [])
        path.append("gather_intel")

        return {
            "intel": intel,
            "recon_result": recon_result,
            "step_ids": {**state.get("step_ids", {}), "gather_intel": step["id"]},
            "execution_path": path,
        }
    except Exception as e:
        logger.error("Intel gathering failed: %s", e)
        storage.update_step(step["id"], status="failed", finished_at=_utc_now(),
                            detail={"error": str(e)})
        path = state.get("execution_path", [])
        path.append("gather_intel")
        return {
            "intel": {},
            "recon_result": {},
            "execution_path": path,
        }
