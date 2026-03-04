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


def get_empty_data() -> dict:
    return {"name": "", "university": "", "degree": "",
            "year": "", "phone_number": "", "email": ""}


def _encode_image_to_base64(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_mime_type(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".webp": "image/webp", ".bmp": "image/bmp",
            ".tiff": "image/tiff", ".tif": "image/tiff"}.get(ext, "image/jpeg")


def _parse_json_from_response(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {}


def extract_details_from_certificate(image_path: str) -> dict:
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        print("[OCR] ERROR: GOOGLE_API_KEY not set.")
        return get_empty_data()

    try:
        image_b64 = _encode_image_to_base64(image_path)
        mime_type = _get_mime_type(image_path)
    except FileNotFoundError as e:
        print(f"[OCR] ERROR: {e}")
        return get_empty_data()

    prompt = (
        "Analyze this academic certificate image and extract the following fields. "
        "Return ONLY a valid JSON object with exactly these keys, no markdown, no explanation:\n"
        '{"name": "", "university": "", "degree": "", "year": "", '
        '"phone_number": "", "email": ""}\n'
        "Use empty string for any field not visible in the image."
    )

    payload = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": mime_type, "data": image_b64}},
            {"text": prompt}
        ]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
    }

    # Try models in order until one works
    models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro-vision"]
    
    for model in models:
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
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
            print(f"[OCR] SUCCESS with model: {model}")
            break
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            print(f"[OCR] HTTP {e.code} with {model}: {err[:300]}")
            response_body = None
            continue
        except Exception as e:
            print(f"[OCR] ERROR with {model}: {e}")
            response_body = None
            continue
    else:
        print("[OCR] All models failed.")
        return get_empty_data()

    if not response_body:
        return get_empty_data()

    try:
        candidates = response_body.get("candidates", [])
        if not candidates:
            print(f"[OCR] No candidates. Full response: {json.dumps(response_body)[:500]}")
            return get_empty_data()

        raw_text = candidates[0]["content"]["parts"][0]["text"]
        print(f"[OCR] Raw response: {raw_text[:300]}")
        parsed = _parse_json_from_response(raw_text)

        if not parsed:
            print(f"[OCR] Could not parse JSON from: {raw_text[:200]}")
            return get_empty_data()

        defaults = get_empty_data()
        for key in defaults:
            parsed[key] = str(parsed.get(key, "")).strip()

        print(f"[OCR] Extracted: name={parsed.get('name')} | uni={parsed.get('university')}")
        return parsed

    except Exception as e:
        print(f"[OCR] Parse error: {e} | Response: {json.dumps(response_body)[:300]}")
        return get_empty_data()