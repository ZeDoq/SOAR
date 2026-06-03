"""MCP Governance - Agent-to-tool permission policies.

Defines which agents can access which tools, preventing unauthorized
actions (e.g., an analysis agent accidentally triggering firewall blocks).
"""

import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

# Permission categories
PERM_INTEL_QUERY = "intel_query"        # Query threat intelligence
PERM_KNOWLEDGE_QUERY = "knowledge_query"  # Query knowledge base/graph
PERM_NETWORK_RECON = "network_recon"    # WHOIS, DNS lookups
PERM_RESPONSE_ACTION = "response_action"  # Firewall block, notifications
PERM_SYSTEM_ADMIN = "system_admin"      # Full access

# Agent role definitions with permitted permission categories
AGENT_ROLES: Dict[str, Set[str]] = {
    "intelligence_agent": {PERM_INTEL_QUERY, PERM_NETWORK_RECON},
    "analysis_agent": {PERM_KNOWLEDGE_QUERY, PERM_INTEL_QUERY},
    "response_agent": {PERM_RESPONSE_ACTION},
    "supervisor": {PERM_INTEL_QUERY, PERM_KNOWLEDGE_QUERY, PERM_NETWORK_RECON, PERM_RESPONSE_ACTION, PERM_SYSTEM_ADMIN},
    "debate_agent": {PERM_KNOWLEDGE_QUERY, PERM_INTEL_QUERY},
    "moderator": {PERM_KNOWLEDGE_QUERY, PERM_INTEL_QUERY},
}

# Tool to permission mapping
TOOL_PERMISSIONS: Dict[str, str] = {
    "virustotal_lookup": PERM_INTEL_QUERY,
    "abuseipdb_lookup": PERM_INTEL_QUERY,
    "search_knowledge_base": PERM_KNOWLEDGE_QUERY,
    "query_knowledge_graph": PERM_KNOWLEDGE_QUERY,
    "whois_lookup": PERM_NETWORK_RECON,
    "dns_lookup": PERM_NETWORK_RECON,
    "firewall_block": PERM_RESPONSE_ACTION,
    "send_notification": PERM_RESPONSE_ACTION,
    "create_ticket": PERM_RESPONSE_ACTION,
}


def check_permission(agent_role: str, tool_name: str) -> bool:
    """Check if an agent role has permission to use a tool.

    Returns True if permitted, False otherwise.
    """
    required_perm = TOOL_PERMISSIONS.get(tool_name)
    if not required_perm:
        # Tool not in governance map = unrestricted
        return True

    agent_perms = AGENT_ROLES.get(agent_role, set())
    allowed = required_perm in agent_perms

    if not allowed:
        logger.warning("Governance denied: %s -> %s (requires %s)",
                       agent_role, tool_name, required_perm)

    return allowed


def get_agent_permissions(agent_role: str) -> List[str]:
    """Get list of tools an agent role is allowed to use."""
    agent_perms = AGENT_ROLES.get(agent_role, set())
    return [
        tool for tool, perm in TOOL_PERMISSIONS.items()
        if perm in agent_perms
    ]


def get_permission_matrix() -> Dict[str, Dict[str, bool]]:
    """Get the full permission matrix (agents x tools).

    Returns nested dict: {agent_role: {tool_name: allowed}}
    """
    matrix = {}
    for agent_role in AGENT_ROLES:
        matrix[agent_role] = {}
        for tool_name in TOOL_PERMISSIONS:
            matrix[agent_role][tool_name] = check_permission(agent_role, tool_name)
    return matrix
