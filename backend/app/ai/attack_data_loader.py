"""Load MITRE ATT&CK Enterprise matrix into the RAG vector store.

Parses the STIX2 bundle from MITRE's CTI repository and creates
document embeddings for each technique, tactic, and mitigation.
"""

import logging
import os
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

# ATT&CK Enterprise matrix STIX bundle URL
ATTACK_STIX_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
LOCAL_CACHE_PATH = "data/enterprise-attack.json"


def _download_stix_bundle(dest: str) -> bool:
    """Download the ATT&CK STIX bundle if not cached locally."""
    if os.path.exists(dest):
        logger.info("Using cached STIX bundle at %s", dest)
        return True

    try:
        import httpx
        logger.info("Downloading ATT&CK STIX bundle...")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        resp = httpx.get(ATTACK_STIX_URL, timeout=60, follow_redirects=True)
        resp.raise_for_status()
        with open(dest, "w", encoding="utf-8") as f:
            f.write(resp.text)
        logger.info("Downloaded STIX bundle to %s", dest)
        return True
    except Exception as e:
        logger.warning("Failed to download STIX bundle: %s", e)
        return False


def _parse_stix_techniques(bundle_path: str) -> List[dict]:
    """Parse attack-pattern objects from STIX bundle into document dicts."""
    import json

    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    techniques = []
    for obj in bundle.get("objects", []):
        if obj.get("type") != "attack-pattern":
            continue
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue

        # Extract tactic phases
        kill_chain_phases = obj.get("kill_chain_phases", [])
        tactics = [p.get("phase_name", "") for p in kill_chain_phases if p.get("phase_name")]

        # Extract external ID (T-number)
        external_refs = obj.get("external_references", [])
        technique_id = ""
        url = ""
        for ref in external_refs:
            if ref.get("source_name") == "mitre-attack":
                technique_id = ref.get("external_id", "")
                url = ref.get("url", "")
                break

        if not technique_id:
            continue

        name = obj.get("name", "")
        description = obj.get("description", "")
        # Truncate long descriptions
        if len(description) > 2000:
            description = description[:2000] + "..."

        # Build searchable document text
        is_subtechnique = obj.get("x_mitre_is_subtechnique", False)
        doc_text = f"{technique_id} {name}"
        if is_subtechnique:
            doc_text += " (sub-technique)"
        doc_text += f"\nTactics: {', '.join(tactics)}"
        doc_text += f"\n{description}"

        # Platform info
        platforms = obj.get("x_mitre_platforms", [])
        if platforms:
            doc_text += f"\nPlatforms: {', '.join(platforms)}"

        techniques.append({
            "id": technique_id.lower().replace(".", "_"),
            "document": doc_text,
            "metadata": {
                "type": "technique",
                "technique_id": technique_id,
                "name": name,
                "tactics": ",".join(tactics),
                "is_subtechnique": is_subtechnique,
                "platforms": ",".join(platforms) if platforms else "",
                "url": url,
            },
        })

    logger.info("Parsed %d techniques from STIX bundle", len(techniques))
    return techniques


def _parse_stix_tactics(bundle_path: str) -> List[dict]:
    """Parse tactic objects from STIX bundle."""
    import json

    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    tactics = []
    for obj in bundle.get("objects", []):
        if obj.get("type") != "x-mitre-tactic":
            continue
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue

        external_refs = obj.get("external_references", [])
        tactic_id = ""
        url = ""
        for ref in external_refs:
            if ref.get("source_name") == "mitre-attack":
                tactic_id = ref.get("external_id", "")
                url = ref.get("url", "")
                break

        name = obj.get("name", "")
        description = obj.get("description", "")
        shortname = obj.get("x_mitre_shortname", "")

        doc_text = f"{tactic_id} {name} ({shortname})\n{description}"

        tactics.append({
            "id": f"tactic_{shortname}",
            "document": doc_text,
            "metadata": {
                "type": "tactic",
                "tactic_id": tactic_id,
                "name": name,
                "shortname": shortname,
                "url": url,
            },
        })

    logger.info("Parsed %d tactics from STIX bundle", len(tactics))
    return tactics


def load_attack_data(force_reload: bool = False) -> int:
    """Load ATT&CK data into the RAG vector store.

    Returns number of documents loaded. Skips if already populated
    (unless force_reload=True).
    """
    from . import rag_engine

    rag_engine._ensure_initialized()
    stats = rag_engine.get_collection_stats()

    if stats["total_documents"] > 0 and not force_reload:
        logger.info("RAG store already has %d documents, skipping load", stats["total_documents"])
        return stats["total_documents"]

    if force_reload and stats["total_documents"] > 0:
        # Clear and re-populate
        rag_engine._client.delete_collection("attack_knowledge")
        rag_engine.reset()
        rag_engine._ensure_initialized()

    # Download STIX bundle
    bundle_path = LOCAL_CACHE_PATH
    if not _download_stix_bundle(bundle_path):
        # Fall back to embedded minimal knowledge
        logger.warning("STIX bundle unavailable, loading minimal fallback")
        return _load_fallback_techniques()

    # Parse and load
    techniques = _parse_stix_techniques(bundle_path)
    tactics = _parse_stix_tactics(bundle_path)
    all_docs = techniques + tactics

    if not all_docs:
        logger.warning("No ATT&CK data parsed, loading fallback")
        return _load_fallback_techniques()

    documents = [d["document"] for d in all_docs]
    metadatas = [d["metadata"] for d in all_docs]
    ids = [d["id"] for d in all_docs]

    count = rag_engine.add_documents(documents, metadatas, ids)
    logger.info("Loaded %d ATT&CK documents into RAG store", count)
    return count


def _load_fallback_techniques() -> int:
    """Load a minimal set of ATT&CK techniques when STIX bundle is unavailable."""
    from . import rag_engine

    fallback = [
        ("T1110", "Brute Force", "credential-access",
         "Attackers attempt to gain access by trying many passwords."),
        ("T1048", "Exfiltration Over Alternative Protocol", "exfiltration",
         "Data exfiltration using DNS tunneling, ICMP, or other non-standard protocols."),
        ("T1021", "Remote Services", "lateral-movement",
         "Lateral movement via RDP, SSH, SMB, or other remote services."),
        ("T1190", "Exploit Public-Facing Application", "initial-access",
         "Exploiting vulnerabilities in internet-facing applications."),
        ("T1566", "Phishing", "initial-access",
         "Phishing via email with malicious links or attachments."),
        ("T1059", "Command and Scripting Interpreter", "execution",
         "Executing commands via PowerShell, Bash, Python scripts."),
        ("T1498", "Network Denial of Service", "impact",
         "DDoS attacks consuming bandwidth or service resources."),
        ("T1046", "Network Service Discovery", "discovery",
         "Port scanning and network service enumeration."),
        ("T1071", "Application Layer Protocol", "command-and-control",
         "C2 communication over HTTP, HTTPS, or DNS protocols."),
        ("T1078", "Valid Accounts", "defense-evasion",
         "Using stolen legitimate credentials to evade detection."),
        ("T1053", "Scheduled Task/Job", "persistence",
         "Persistence via cron jobs or scheduled tasks."),
        ("T1070", "Indicator Removal", "defense-evasion",
         "Clearing logs and removing traces to avoid detection."),
    ]

    documents = []
    metadatas = []
    ids = []
    for tid, name, tactic, desc in fallback:
        doc_text = f"{tid} {name}\nTactics: {tactic}\n{desc}"
        documents.append(doc_text)
        metadatas.append({
            "type": "technique",
            "technique_id": tid,
            "name": name,
            "tactics": tactic,
            "is_subtechnique": False,
            "platforms": "",
            "url": "",
        })
        ids.append(tid.lower().replace(".", "_"))

    count = rag_engine.add_documents(documents, metadatas, ids)
    logger.info("Loaded %d fallback techniques", count)
    return count
