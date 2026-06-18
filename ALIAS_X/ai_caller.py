"""
ALIAS_X — ai_caller.py
Execution Protocol: Dispatches Bland AI voice calls, polls for completion,
and classifies the transcript to produce VERIFIED / REJECTED / TIMEOUT.

Fallback: If the phone call is interrupted, times out, or fails to connect,
email verification is automatically triggered via email_verifier.py.
"""

import os
import re
import time

import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
BLAND_KEY  = os.getenv("BLAND_AI_KEY", "").strip()
BLAND_URL  = "https://api.bland.ai/v1/calls"
POLL_EVERY = 5
TIMEOUT    = 120

print("BLAND_AI_KEY loaded:", bool(BLAND_KEY))
print("BLAND_AI_KEY preview:", BLAND_KEY[:8] + "..." if BLAND_KEY else "EMPTY")

# ── Keyword classifiers ───────────────────────────────────────────────────────
AFFIRM_KW = [
    "yes", "confirmed", "correct", "that is correct", "that's correct",
    "we can confirm", "i can confirm", "can confirm", "records show",
    "we do have", "on file", "i can verify", "that is right",
    "record is correct", "we have that record", "yes we do",
    "yes that is", "yes i can"
]

REJECT_KW = [
    r"\bno record\b", r"\bnot found\b", r"\bcannot confirm\b",
    r"\bunable to verify\b", r"\bno such student\b", r"\bnot in our system\b",
    r"\bdo not have\b", r"\bdon't have\b", r"\bincorrect\b",
    r"\bcannot find\b", r"\bno we cannot\b", r"\bno i cannot\b",
    r"\bnot able to confirm\b", r"\bno record found\b"
]

# ── Simulation ────────────────────────────────────────────────────────────────
SIMULATION_VERIFIED = {
    "status": "VERIFIED",
    "channel": "phone",
    "transcript": (
        "AI Agent: Hello, I'm calling from a credential verification service. "
        "Could you please confirm whether John Doe graduated with a BSc in "
        "Computer Science in 2022?\n"
        "Registrar: Yes, I can confirm that — we do have that record on file.\n"
        "AI Agent: Thank you very much. Have a great day."
    ),
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def sanitise_phone(raw: str) -> str:
    if not raw:
        raise ValueError("Phone number is empty.")
    cleaned = re.sub(r'[^0-9+]', '', raw.strip())
    if not re.match(r'^\+?[1-9]\d{7,14}$', cleaned):
        raise ValueError(f"Invalid E.164 phone number: {repr(cleaned)}")
    return cleaned


def _build_prompt(data: dict) -> str:
    name       = data.get("name",       "the candidate")
    degree     = data.get("degree",     "their degree")
    year       = data.get("year",       "the year on record")
    university = data.get("university", "your institution")
    return (
        f"Hello, I am calling from a credential verification service. "
        f"I am trying to verify the academic records of {name}. "
        f"Could you please confirm whether {name} graduated from {university} "
        f"with a {degree} in {year}? "
        f"A simple yes or no is sufficient. Thank you."
    )


def _classify_transcript(transcript: str) -> str:
    t         = transcript.lower()
    confirmed = any(kw in t for kw in AFFIRM_KW)
    denied    = any(re.search(p, t) for p in REJECT_KW)
    print(f"[CLASSIFY] confirmed={confirmed}, denied={denied}")
    print(f"[TRANSCRIPT]: {t[:300]}")
    if denied and not confirmed:
        return "REJECTED"
    if confirmed:
        return "VERIFIED"
    return "REJECTED"


def _poll(call_id: str, headers: dict, timeout: int = TIMEOUT) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(POLL_EVERY)
        try:
            resp = requests.get(
                f"{BLAND_URL}/{call_id}",
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            r = resp.json()
            print("[POLL RESPONSE]", r)
        except Exception as e:
            print(f"[WARN] Poll failed: {e}. Retrying…")
            continue

        call_status = r.get("status", "").lower()

        if call_status == "completed":
            transcript = (
                r.get("concatenated_transcript") or
                r.get("transcript") or ""
            )
            return {
                "status":     _classify_transcript(transcript),
                "channel":    "phone",
                "transcript": transcript or "Call completed — no transcript returned.",
            }

        if call_status in ("error", "failed", "cancelled"):
            # Phone call interrupted — signal for email fallback
            return {
                "status":     "INTERRUPTED",
                "channel":    "phone",
                "transcript": f"Call ended with Bland AI status: {call_status}",
            }

    return {
        "status":     "TIMEOUT",
        "channel":    "phone",
        "transcript": f"Call timed out after {TIMEOUT} seconds.",
    }


# ── Public API ────────────────────────────────────────────────────────────────

def initiate_verification_call(phone: str, data: dict,
                                simulation: bool = False,
                                fallback_email: str = "") -> dict:
    """
    Dispatch a Bland AI voice call to verify the candidate's credentials.
    If the call is interrupted or times out, automatically falls back to
    email verification if a registrar email address is provided.

    Args:
        phone          : E.164-formatted phone number
        data           : Certificate dict {name, university, degree, year}
        simulation     : If True, return mock result without calling APIs
        fallback_email : Registrar email for automatic fallback (from Intel Uplink)

    Returns:
        {
          "status":     "VERIFIED" | "REJECTED" | "TIMEOUT",
          "channel":    "phone" | "email" | "simulation",
          "transcript": str,
          "fallback_triggered": bool   (True if email fallback was used)
        }
    """
    if simulation:
        if "test name" in str(data.get("name", "")).lower():
            return {
                "status":             "REJECTED",
                "channel":            "simulation",
                "transcript":         "Registrar: No, I cannot find that record in our system.",
                "fallback_triggered": False,
            }
        result = SIMULATION_VERIFIED.copy()
        result["channel"]            = "simulation"
        result["fallback_triggered"] = False
        return result

    if not BLAND_KEY:
        # No phone key — go straight to email if available
        if fallback_email:
            return _run_email_fallback(fallback_email, data,
                                       reason="BLAND_AI_KEY not configured")
        return {
            "status":             "TIMEOUT",
            "channel":            "phone",
            "transcript":         "BLAND_AI_KEY not configured in .env — unable to place call.",
            "fallback_triggered": False,
        }

    try:
        cleaned_phone = sanitise_phone(phone)
    except ValueError as e:
        if fallback_email:
            return _run_email_fallback(fallback_email, data,
                                       reason=f"Phone validation failed: {e}")
        return {
            "status":             "REJECTED",
            "channel":            "phone",
            "transcript":         f"Phone validation failed: {e}",
            "fallback_triggered": False,
        }

    payload = {
        "phone_number":      cleaned_phone,
        "task":              _build_prompt(data),
        "voice":             "maya",
        "wait_for_greeting": True,
        "record":            True,
        "max_duration":      180,
    }

    # Correct Bland AI auth — no "Bearer" prefix
    headers = {
        "authorization": BLAND_KEY,
        "Content-Type":  "application/json",
    }

    print("[BLAND REQUEST]", payload)

    try:
        resp = requests.post(BLAND_URL, json=payload, headers=headers, timeout=30)
        print("[BLAND STATUS]", resp.status_code)
        print("[BLAND RESPONSE]", resp.text)
        resp.raise_for_status()

        call_id = resp.json().get("call_id")
        if not call_id:
            if fallback_email:
                return _run_email_fallback(
                    fallback_email, data,
                    reason=f"Bland AI response missing call_id: {resp.json()}"
                )
            return {
                "status":             "TIMEOUT",
                "channel":            "phone",
                "transcript":         f"Bland AI response missing call_id: {resp.json()}",
                "fallback_triggered": False,
            }

    except requests.exceptions.HTTPError as e:
        reason = f"Bland AI HTTP {e.response.status_code}: {e.response.text}"
        if fallback_email:
            return _run_email_fallback(fallback_email, data, reason=reason)
        return {
            "status":             "TIMEOUT",
            "channel":            "phone",
            "transcript":         reason,
            "fallback_triggered": False,
        }
    except Exception as e:
        reason = f"Could not connect to Bland AI: {e}"
        if fallback_email:
            return _run_email_fallback(fallback_email, data, reason=reason)
        return {
            "status":             "TIMEOUT",
            "channel":            "phone",
            "transcript":         reason,
            "fallback_triggered": False,
        }

    # ── Poll for result ───────────────────────────────────────────────────────
    phone_result = _poll(call_id, headers)

    # If interrupted or timed out — trigger email fallback
    if phone_result["status"] in ("TIMEOUT", "INTERRUPTED") and fallback_email:
        return _run_email_fallback(
            fallback_email, data,
            reason=f"Phone call {phone_result['status'].lower()}: {phone_result['transcript']}"
        )

    phone_result["fallback_triggered"] = False
    return phone_result


def _run_email_fallback(to_email: str, data: dict, reason: str = "") -> dict:
    """
    Internal: trigger email verification as fallback channel.
    Imports email_verifier lazily to avoid circular dependency.
    """
    print(f"[FALLBACK] Phone failed ({reason}). Triggering email verification → {to_email}")
    try:
        from email_verifier import run_email_verification
        result = run_email_verification(to_email, data)
        result["channel"]            = "email"
        result["fallback_triggered"] = True
        result["fallback_reason"]    = reason
        return result
    except Exception as e:
        return {
            "status":             "TIMEOUT",
            "channel":            "email",
            "transcript":         f"Email fallback also failed: {e}\nOriginal reason: {reason}",
            "fallback_triggered": True,
            "fallback_reason":    reason,
        }