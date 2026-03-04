"""
╔══════════════════════════════════════════════════════════════╗
║         ALIAS_X · OCR Engine · modules/ocr_engine.py         ║
║   Gemini 2.5 Flash Vision API — Certificate Data Extraction  ║
╚══════════════════════════════════════════════════════════════╝
"""

import base64
import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path


# ── Fallback Data ──────────────────────────────────────────────
def get_empty_data() -> dict:
    """
    Returns a safe default payload when OCR fails, quota is hit,
    or no image is uploaded. All fields signal 'Manual Check'.
    """
    return {
        "name":         "Unknown Subject",
        "university":   "Manual Check Required",
        "degree":       "Manual Check Required",
        "year":         "Unknown",
        "phone_number": "",
        "email":        "",
    }


# ── Image Encoder ──────────────────────────────────────────────
def _encode_image_to_base64(image_path: str) -> str:
    """Reads a local image file and returns its Base64-encoded string."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_mime_type(image_path: str) -> str:
    """Infer MIME type from file extension."""
    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png":  "image/png",
        ".webp": "image/webp",
        ".gif":  "image/gif",
        ".bmp":  "image/bmp",
        ".tiff": "image/tiff",
        ".tif":  "image/tiff",
    }
    return mime_map.get(ext, "image/jpeg")


# ── JSON Extractor ─────────────────────────────────────────────
def _parse_json_from_response(text: str) -> dict:
    """
    Robustly extract JSON from Gemini's response text.
    Handles markdown code fences and trailing prose.
    """
    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()
    cleaned = cleaned.replace("```", "").strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Find first {...} block
    match = re.search(r"\{.*?\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {}


# ── Main OCR Function ──────────────────────────────────────────
def extract_details_from_certificate(image_path: str) -> dict:
    """
    Sends a certificate image to Google Gemini 2.5 Flash via REST API.

    Extracts:
        name, university, degree, year, phone_number, email

    Args:
        image_path: Absolute or relative path to a local image file.

    Returns:
        dict with extracted fields, or get_empty_data() on failure.
    """
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        print("[OCR_ENGINE] ⚠ GOOGLE_API_KEY not set — returning empty data.")
        return get_empty_data()

    # ── Build Gemini REST Payload ──────────────────────────────
    try:
        image_b64   = _encode_image_to_base64(image_path)
        mime_type   = _get_mime_type(image_path)
    except FileNotFoundError as e:
        print(f"[OCR_ENGINE] ⚠ {e} — returning empty data.")
        return get_empty_data()

    extraction_prompt = """
You are an expert document analysis AI. Your task is to analyze the academic certificate
or degree document in this image and extract specific information.

Extract the following fields and return ONLY a valid JSON object with these exact keys:
{
  "name":         "Full name of the certificate holder (string)",
  "university":   "Full official name of the issuing institution (string)",
  "degree":       "Degree title and field of study (string)",
  "year":         "Year of graduation or issuance (string, 4-digit year)",
  "phone_number": "Phone number of the university registrar's office if visible, else empty string",
  "email":        "Official email address of the university registrar or contact if visible, else empty string"
}

Rules:
- Return ONLY the JSON object. No markdown, no explanation, no preamble.
- If a field is not visible or cannot be determined, use an empty string "".
- For phone_number: include country code with + if identifiable.
- For email: must be an institutional email (contains .edu, .ac, .in, etc.).
- Do NOT invent or guess values — only extract what is visibly present.
""".strip()

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data":      image_b64,
                        }
                    },
                    {
                        "text": extraction_prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature":     0.1,   # Low temperature for factual extraction
            "topK":            1,
            "topP":            0.95,
            "maxOutputTokens": 512,
        }
    }

    # ── Send REST Request ──────────────────────────────────────
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )

    body_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url     = endpoint,
        data    = body_bytes,
        method  = "POST",
        headers = {"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"[OCR_ENGINE] ✖ HTTP {e.code}: {err_body[:300]}")
        # 429 = quota exceeded, 400 = bad request
        return get_empty_data()
    except urllib.error.URLError as e:
        print(f"[OCR_ENGINE] ✖ Network error: {e.reason}")
        return get_empty_data()
    except Exception as e:
        print(f"[OCR_ENGINE] ✖ Unexpected error: {e}")
        return get_empty_data()

    # ── Parse Gemini Response ──────────────────────────────────
    try:
        candidates = response_body.get("candidates", [])
        if not candidates:
            print("[OCR_ENGINE] ⚠ No candidates in response.")
            return get_empty_data()

        content_parts = candidates[0].get("content", {}).get("parts", [])
        if not content_parts:
            print("[OCR_ENGINE] ⚠ Empty content parts.")
            return get_empty_data()

        raw_text    = content_parts[0].get("text", "")
        parsed_data = _parse_json_from_response(raw_text)

        if not parsed_data:
            print(f"[OCR_ENGINE] ⚠ Could not parse JSON from: {raw_text[:200]}")
            return get_empty_data()

        # ── Merge with defaults to ensure all keys exist ───────
        defaults = get_empty_data()
        for key in defaults:
            if key not in parsed_data or parsed_data[key] is None:
                parsed_data[key] = defaults[key]
            parsed_data[key] = str(parsed_data[key]).strip()

        print(f"[OCR_ENGINE] ✔ Extracted: {parsed_data.get('name')} | {parsed_data.get('university')}")
        return parsed_data

    except (KeyError, IndexError, TypeError) as e:
        print(f"[OCR_ENGINE] ✖ Parse error: {e}")
        return get_empty_data()