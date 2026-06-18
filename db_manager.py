"""
ALIAS_X — db_manager.py
JSON audit log schema enforcement and optional SQLite migration.

Default storage: verification_log.json (flat JSON array)
Optional upgrade: SQLite via migrate_to_sqlite()
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

LOG_FILE = "verification_log.json"
DB_FILE  = "alias_x.db"

# ── JSON Schema ───────────────────────────────────────────────────────────────
VERIFICATION_SCHEMA = {
    "session_id":  str,
    "agent_id":    str,
    "codename":    str,
    "timestamp":   str,
    "candidate": {
        "name":       (str, type(None)),
        "university": (str, type(None)),
        "degree":     (str, type(None)),
        "year":       (str, type(None)),
    },
    "registrar": {
        "phone":  (str, type(None)),
        "email":  (str, type(None)),
        "source": (str, type(None)),
    },
    "outcome":    str,
    "transcript": (str, type(None)),
}


# ── JSON Log Helpers ──────────────────────────────────────────────────────────

def load_log() -> list:
    """Load the JSON verification log. Returns [] on missing or corrupt file."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def append_session(session: dict) -> None:
    """Append a validated session record to the JSON audit log."""
    records = load_log()
    # Ensure timestamp
    if not session.get("timestamp"):
        session["timestamp"] = datetime.now(timezone.utc).isoformat()
    records.append(session)
    with open(LOG_FILE, "w") as f:
        json.dump(records, f, indent=2)


def get_sessions_by_agent(codename: str) -> list:
    """Return all sessions for a given agent codename."""
    return [s for s in load_log() if s.get("codename") == codename]


def get_session_by_id(session_id: str) -> Optional[dict]:
    """Return a single session by session_id, or None if not found."""
    for s in load_log():
        if s.get("session_id") == session_id:
            return s
    return None


def summary_stats() -> dict:
    """Return aggregate stats across all sessions."""
    records   = load_log()
    total     = len(records)
    verified  = sum(1 for r in records if r.get("outcome") == "VERIFIED")
    rejected  = sum(1 for r in records if r.get("outcome") == "REJECTED")
    timeout   = sum(1 for r in records if r.get("outcome") == "TIMEOUT")
    return {
        "total":    total,
        "verified": verified,
        "rejected": rejected,
        "timeout":  timeout,
        "pass_rate": f"{(verified / total * 100):.1f}%" if total else "N/A",
    }


# ── SQLite Migration (optional upgrade) ──────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_sqlite() -> None:
    """Create SQLite schema if it doesn't exist."""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id   TEXT PRIMARY KEY,
            agent_id     TEXT NOT NULL,
            codename     TEXT NOT NULL,
            timestamp    TEXT NOT NULL,
            cand_name    TEXT,
            cand_uni     TEXT,
            cand_degree  TEXT,
            cand_year    TEXT,
            reg_phone    TEXT,
            reg_email    TEXT,
            reg_source   TEXT,
            outcome      TEXT NOT NULL,
            transcript   TEXT
        )
    """)
    conn.commit()
    conn.close()


def migrate_to_sqlite() -> int:
    """
    Migrate all records from verification_log.json into SQLite.
    Returns number of records migrated.
    """
    init_sqlite()
    records = load_log()
    conn    = _get_connection()
    count   = 0

    for r in records:
        c = r.get("candidate") or {}
        g = r.get("registrar")  or {}
        try:
            conn.execute("""
                INSERT OR IGNORE INTO sessions VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                r.get("session_id"),
                r.get("agent_id"),
                r.get("codename"),
                r.get("timestamp"),
                c.get("name"),
                c.get("university"),
                c.get("degree"),
                c.get("year"),
                g.get("phone"),
                g.get("email"),
                g.get("source"),
                r.get("outcome"),
                r.get("transcript"),
            ))
            count += 1
        except sqlite3.Error:
            pass

    conn.commit()
    conn.close()
    return count


def sqlite_summary() -> dict:
    """Query summary stats directly from SQLite (faster than JSON for large logs)."""
    init_sqlite()
    conn = _get_connection()
    row  = conn.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(outcome = 'VERIFIED') AS verified,
            SUM(outcome = 'REJECTED') AS rejected,
            SUM(outcome = 'TIMEOUT')  AS timeout
        FROM sessions
    """).fetchone()
    conn.close()
    total = row["total"] or 0
    return {
        "total":    total,
        "verified": row["verified"] or 0,
        "rejected": row["rejected"] or 0,
        "timeout":  row["timeout"]  or 0,
        "pass_rate": f"{(row['verified'] / total * 100):.1f}%" if total else "N/A",
    }
