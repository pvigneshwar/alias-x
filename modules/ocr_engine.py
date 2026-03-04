"""
ALIAS_X · OCR Engine
Gemini Vision API — Certificate Data Extraction
"""

import base64
import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# Default Fallback Data
# ──────────────────────────────────────────────────────────────
def get_empty_data() -> dict:
    return {
        "name": "",
        "university": "",
        "degree": "",
        "year": "",
        "phone_number": "",
        "email": "",
    }


# ──────────────────────────────────────────────────────────────
# Image Encoding
# ──────────────────────────────────────────────────────────────
def _encode_image_to_base64(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_mime_type(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }
    return mime_map.get(ext, "image/jpeg")


# ──────────────────────────────────────────────────────────────
# Robust JSON Parsing
# ──────────────────────────────────────────────────────────────
def _parse_json_from_response(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                return {}
    return {}


# ──────────────────────────────────────────────────────────────
# MAIN OCR FUNCTION
# ──────────────────────────────────────────────────────────────
def extract_details_from_certificate(image_path: str) -> dict:

    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

    if not api_key:
        print("GOOGLE_API_KEY not set.")
        return get_empty_data()

    try:
        image_b64 = _encode_image_to_base64(image_path)
        mime_type = _get_mime_type(image_path)
    except FileNotFoundError:
        return get_empty_data()

    extraction_prompt = """
Extract the following fields from the academic certificate image.
Return ONLY valid JSON with these keys:

{
  "name": "",
  "university": "",
  "degree": "",
  "year": "",
  "phone_number": "",
  "email": ""
}

Rules:
- No explanations.
- No markdown.
- Do not guess values.
- Use empty string if not visible.
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64,
                        }
                    },
                    {"text": extraction_prompt},
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 512,
        },
    }

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={api_key}"
    )

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_body = json.loads(resp.read().decode("utf-8"))
    except:
        return get_empty_data()

    try:
        candidates = response_body.get("candidates", [])
        if not candidates:
            return get_empty_data()

        raw_text = candidates[0]["content"]["parts"][0]["text"]
        parsed = _parse_json_from_response(raw_text)

        defaults = get_empty_data()
        for key in defaults:
            parsed[key] = str(parsed.get(key, "")).strip()

        return parsed
    except:
        return get_empty_data()