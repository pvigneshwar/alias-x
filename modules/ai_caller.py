"""
ALIAS_X · AI Caller
Bland AI voice call + transcript polling + Gemini verdict analysis
"""

import os
import json
import time
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv(override=True)

BLAND_BASE = "https://api.bland.ai/v1"


# ── Initiate Call ──────────────────────────────────────────────
def make_real_ai_call(phone: str, data: dict) -> dict:
    """
    Initiates a Bland AI verification call.
    Returns: { "success": bool, "call_id": str, "error": str }
    """
    api_key = os.getenv("BLAND_API_KEY", "").strip()
    if not api_key:
        return {"success": False, "call_id": None, "error": "BLAND_API_KEY not set."}

    name       = data.get("name", "Unknown")
    university = data.get("university", "Unknown")
    degree     = data.get("degree", "Unknown")
    year       = data.get("year", "Unknown")

    payload = {
        "phone_number":        phone,
        "voice":               "maya",
        "reduce_latency":      True,
        "record":              True,
        "max_duration":        5,
        "answered_by_enabled": True,
        "task": (
            f"You are an academic verification agent calling on behalf of ALIAS_X. "
            f"You are verifying the credentials of {name}, who claims to hold a "
            f"{degree} from {university}, graduating in {year}. "
            f"Ask the registrar to confirm or deny these credentials. "
            f"Be polite and professional. If confirmed say so clearly. "
            f"If denied or cannot confirm, state that clearly."
        ),
    }

    req = urllib.request.Request(
        url=f"{BLAND_BASE}/calls",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "authorization": api_key},
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read().decode("utf-8"))
            call_id = result.get("call_id")
            print(f"[AI_CALLER] ✅ Call dispatched. ID: {call_id}")
            return {"success": True, "call_id": call_id, "error": None}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"[AI_CALLER] HTTP {e.code}: {err[:300]}")
        return {"success": False, "call_id": None, "error": f"HTTP {e.code}: {err[:200]}"}
    except Exception as e:
        print(f"[AI_CALLER] Error: {e}")
        return {"success": False, "call_id": None, "error": str(e)}


# ── Poll Call Status ───────────────────────────────────────────
def get_call_status(call_id: str) -> dict:
    """
    Polls Bland AI for the current status of a call.
    Returns: { "status": str, "completed": bool, "transcript": str, "recording_url": str }
    """
    api_key = os.getenv("BLAND_API_KEY", "").strip()
    if not api_key:
        return {"status": "error", "completed": False, "transcript": "", "recording_url": ""}

    req = urllib.request.Request(
        url=f"{BLAND_BASE}/calls/{call_id}",
        method="GET",
        headers={"authorization": api_key},
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))

        status        = data.get("status", "unknown")
        completed     = status in ("complete", "completed", "failed", "no-answer", "busy", "voicemail")
        transcript    = data.get("transcripts", [])
        recording_url = data.get("recording_url", "")

        # Build readable transcript string
        if isinstance(transcript, list):
            lines = []
            for t in transcript:
                speaker = "AGENT"   if t.get("user") == "assistant" else "REGISTRAR"
                text    = t.get("text", "").strip()
                if text:
                    lines.append(f"{speaker}: {text}")
            transcript_text = "\n".join(lines)
        else:
            transcript_text = str(transcript)

        return {
            "status":        status,
            "completed":     completed,
            "transcript":    transcript_text,
            "recording_url": recording_url,
            "raw":           data,
        }

    except Exception as e:
        print(f"[AI_CALLER] Poll error: {e}")
        return {"status": "error", "completed": False, "transcript": "", "recording_url": ""}


# ── Gemini Verdict Analysis ────────────────────────────────────
def analyze_transcript_verdict(transcript: str, student_data: dict) -> dict:
    """
    Sends transcript to Gemini to determine verification verdict.
    Returns: { "verdict": "CONFIRMED"|"DENIED"|"INCONCLUSIVE", "reason": str, "confidence": int }
    """
    import requests as req_lib

    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key or not transcript.strip():
        return {"verdict": "INCONCLUSIVE", "reason": "No transcript available.", "confidence": 0}

    name       = student_data.get("name", "Unknown")
    university = student_data.get("university", "Unknown")
    degree     = student_data.get("degree", "Unknown")
    year       = student_data.get("year", "Unknown")

    prompt = f"""You are an academic verification analyst for ALIAS_X.

A phone call was made to the registrar of {university} to verify the following student:
- Name: {name}
- Degree: {degree}
- Year: {year}

Here is the call transcript:
---
{transcript}
---

Analyze the transcript and determine the verification verdict.
Return ONLY a valid JSON object with these exact keys:
{{
  "verdict": "CONFIRMED" or "DENIED" or "INCONCLUSIVE",
  "reason": "one sentence explanation",
  "confidence": 0-100
}}

Rules:
- CONFIRMED: registrar clearly confirmed the student's credentials
- DENIED: registrar clearly denied or said credentials don't match
- INCONCLUSIVE: unclear, voicemail, no answer, or ambiguous response
- Return ONLY the JSON, no markdown, no explanation
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 256},
    }

    models  = ["gemini-2.5-flash", "gemini-1.5-flash"]
    headers = {"Content-Type": "application/json"}

    for model in models:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={api_key}")
        try:
            response = req_lib.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                raw  = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                clean = raw.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean)
                print(f"[AI_CALLER] Verdict: {parsed.get('verdict')} ({parsed.get('confidence')}%)")
                return parsed
        except Exception as e:
            print(f"[AI_CALLER] Gemini verdict error: {e}")
            continue

    return {"verdict": "INCONCLUSIVE", "reason": "Could not analyze transcript.", "confidence": 0}


# ── Wait & Resolve (blocking, for CLI use) ────────────────────
def wait_for_result(call_id: str, student_data: dict,
                    max_wait: int = 300, poll_interval: int = 10) -> dict:
    """
    Polls until call completes (or timeout), then returns verdict.
    Use get_call_status() + analyze_transcript_verdict() directly in Streamlit.
    """
    print(f"[AI_CALLER] Waiting for call {call_id} to complete...")
    elapsed = 0
    while elapsed < max_wait:
        status_data = get_call_status(call_id)
        print(f"[AI_CALLER] Status: {status_data['status']} ({elapsed}s)")
        if status_data["completed"]:
            verdict = analyze_transcript_verdict(status_data["transcript"], student_data)
            return {**status_data, **verdict}
        time.sleep(poll_interval)
        elapsed += poll_interval

    return {
        "status": "timeout", "completed": False,
        "transcript": "", "recording_url": "",
        "verdict": "INCONCLUSIVE", "reason": "Call timed out.", "confidence": 0,
    }
