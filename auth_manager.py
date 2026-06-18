"""
ALIAS_X — auth_manager.py
Authentication Module: SHA-256 credential hashing, agent registration,
session validation, and JSON injection sanitisation.
"""

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone

AGENTS_FILE = "agents.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash(text: str) -> str:
    """Return SHA-256 hex digest of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_agents() -> dict:
    """Load agents.json, returning an empty dict on missing/corrupt file."""
    if not os.path.exists(AGENTS_FILE):
        return {}
    try:
        with open(AGENTS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_agents(agents: dict) -> None:
    """Persist agents dict to agents.json."""
    with open(AGENTS_FILE, "w") as f:
        json.dump(agents, f, indent=2)


def _sanitise_input(value: str) -> str:
    """
    Strip characters commonly used in JSON/script injection attacks.
    Keeps alphanumerics, underscores, hyphens, and spaces only.
    """
    return re.sub(r'[^A-Za-z0-9_\-\s]', '', value).strip()


# ── Public API ────────────────────────────────────────────────────────────────

def validate_login(codename: str, access_key: str) -> dict:
    """
    Validate agent credentials.

    Returns:
        {"success": True,  "agent_id": str}  on match
        {"success": False, "message": str}   on failure
    """
    codename   = _sanitise_input(codename)
    access_key = access_key.strip()          # do NOT sanitise — passwords may include special chars

    if not codename or not access_key:
        return {"success": False, "message": "Codename and Access Key are required."}

    agents = _load_agents()

    # Generic error — never reveal which field is wrong (per AUTH-02/03 test cases)
    agent = agents.get(codename)
    if agent is None or agent.get("key_hash") != _hash(access_key):
        return {"success": False, "message": "ACCESS DENIED — Invalid Codename or Access Key."}

    return {"success": True, "agent_id": agent["agent_id"]}


def register_agent(codename: str, access_key: str) -> dict:
    """
    Register a new agent.

    Returns:
        {"success": True,  "agent_id": str}  on success
        {"success": False, "message": str}   on failure (duplicate, empty fields, etc.)
    """
    codename   = _sanitise_input(codename)
    access_key = access_key.strip()

    if not codename or not access_key:
        return {"success": False, "message": "Codename and Access Key cannot be empty."}

    # Reject JSON injection patterns even after sanitisation (AUTH-05)
    if re.search(r'[{}\[\]"\'\\]', codename):
        return {"success": False, "message": "Invalid characters in Codename."}

    agents = _load_agents()

    # Duplicate check (AUTH-06)
    if codename in agents:
        return {"success": False, "message": f"Codename '{codename}' is already registered."}

    agent_id = str(uuid.uuid4())
    agents[codename] = {
        "agent_id":   agent_id,
        "key_hash":   _hash(access_key),
        "registered": datetime.now(timezone.utc).isoformat(),
    }
    _save_agents(agents)

    return {"success": True, "agent_id": agent_id}


def change_access_key(codename: str, old_key: str, new_key: str) -> dict:
    """Allow an agent to rotate their Access Key."""
    codename = _sanitise_input(codename)
    agents   = _load_agents()

    agent = agents.get(codename)
    if agent is None or agent.get("key_hash") != _hash(old_key.strip()):
        return {"success": False, "message": "Current credentials are invalid."}

    agents[codename]["key_hash"] = _hash(new_key.strip())
    _save_agents(agents)
    return {"success": True, "message": "Access Key updated successfully."}
