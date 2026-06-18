"""
ALIAS_X — ocr_engine.py
Vision Engine: Submits certificate images to Google Gemini 1.5 Pro Vision
for structured JSON extraction of Name, University, Degree, and Year.

Improvements v2:
- Stronger prompt tuned for Indian universities (bilingual Tamil/English layouts)
- Detailed error logging shown in Streamlit UI via _error key
- Supports JPEG, PNG, WEBP
- Falls back to SIMULATION_DATA only as last resort
"""

import base64
import json
import os
import re

import google.generativeai as genai

# ── Simulation fallback ───────────────────────────────────────────────────────
SIMULATION_DATA = {
    "name":       "John Alexander Doe",
    "university": "University of Oxford",
    "degree":     "Bachelor of Science in Computer Science",
    "year":       "2022",
}

# ── Prompt tuned for Indian bilingual certificates ────────────────────────────
PROMPT = """You are an expert OCR assistant specialised in reading Indian and
international academic degree certificates. These certificates often contain
BOTH English text AND regional language script (Tamil, Telugu, Hindi, Kannada,
Malayalam, etc.). Read ONLY the English text.

From the certificate image, extract these four fields:

1. name       — The student's full name as printed in English.
                Usually appears after words like: "that", "certify that",
                "This is to certify", or on a line by itself in bold/caps.
                Example: "SAVIDHA P"

2. university — The full name of the university or institution in English.
                Usually the largest heading at the top.
                Example: "University of Madras"

3. degree     — The complete degree title in English.
                Look for "DEGREE OF...", "Bachelor of...", "Master of...", etc.
                Include the full specialisation.
                Example: "Bachelor of Commerce in Corporate Secretaryship"

4. year       — The 4-digit year of the examination or conferral.
                Look for phrases like: "held in APRIL 2021", "examination held in",
                "20XX", or a standalone year number near the date section.
                Example: "2021"

OUTPUT RULES — follow exactly:
- Return ONLY a raw JSON object. No markdown. No backticks. No explanation.
- Use JSON null (not the string "null") for any field you cannot find.
- Year must be a 4-digit string e.g. "2021", not a number.
- Do NOT include titles (Mr/Ms/Dr) in the name.
- Do NOT include Tamil or regional script in any field.

Return exactly:
{"name": "<value or null>", "university": "<value or null>", "degree": "<value or null>", "year": "<value or null>"}"""


# ── Validation ────────────────────────────────────────────────────────────────

def _validate(data: dict) -> dict:
    """Nullify fields that fail basic sanity checks."""

    # Year: 1950–2029
    year = str(data.get("year") or "")
    if not re.match(r'^(19[5-9]\d|20[0-2]\d)$', year):
        data["year"] = None

    # Name: only letters, spaces, hyphens, dots — min 2 chars
    name = str(data.get("name") or "")
    if not re.match(r'^[A-Za-z\s\-\.]{2,100}$', name):
        data["name"] = None

    for key in ("name", "university", "degree", "year"):
        data.setdefault(key, None)

    return data


# ── Public API ────────────────────────────────────────────────────────────────

def extract_certificate_data(uploaded_file, simulation: bool = False) -> dict:
    """
    Extract structured fields from a certificate image using Gemini 2.5 Pro Vision.

    Returns a dict with keys: name, university, degree, year
    On any failure, also includes '_error' with a human-readable explanation.
    """
    if simulation:
        return SIMULATION_DATA.copy()

    # ── API key check ─────────────────────────────────────────────────────────
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        result = SIMULATION_DATA.copy()
        result["_error"] = (
            "GEMINI_API_KEY missing in .env — showing simulation data.\n"
            "Get a free key at https://aistudio.google.com → Get API Key."
        )
        return result

    # ── Read file ─────────────────────────────────────────────────────────────
    try:
        raw_bytes = uploaded_file.read()
    except Exception as e:
        result = SIMULATION_DATA.copy()
        result["_error"] = f"Could not read uploaded file: {e}"
        return result

    if not raw_bytes:
        result = SIMULATION_DATA.copy()
        result["_error"] = "Uploaded file is empty."
        return result

    b64_data = base64.b64encode(raw_bytes).decode("utf-8")

    fname = getattr(uploaded_file, "name", "cert.jpg").lower()
    if fname.endswith(".png"):
        mime = "image/png"
    elif fname.endswith(".webp"):
        mime = "image/webp"
    else:
        mime = "image/jpeg"

    # ── Gemini call ───────────────────────────────────────────────────────────
    try:
        genai.configure(api_key=api_key)
        model    = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            PROMPT,
            {"mime_type": mime, "data": b64_data},
        ])
        raw_text = response.text.strip()
    except Exception as e:
        result = SIMULATION_DATA.copy()
        result["_error"] = (
            f"Gemini API error: {e}\n\n"
            "Possible causes:\n"
            "• Wrong API key — double-check .env\n"
            "• Gemini API not enabled — visit https://aistudio.google.com\n"
            "• No internet connection"
        )
        return result

    # ── Parse response ────────────────────────────────────────────────────────
    # Strip markdown fences if present
    clean = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
    clean = re.sub(r"\s*```$", "", clean).strip()

    # Extract first JSON object if surrounded by text
    match = re.search(r'\{.*?\}', clean, re.DOTALL)
    if match:
        clean = match.group(0)

    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError as e:
        result = SIMULATION_DATA.copy()
        result["_error"] = (
            f"Could not parse Gemini response as JSON.\n"
            f"Error: {e}\n"
            f"Raw response:\n{raw_text[:400]}"
        )
        return result

    validated = _validate(parsed)
    validated.pop("_error", None)
    return validated