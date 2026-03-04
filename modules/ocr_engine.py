"""
ALIAS_X · OCR Engine
Gemini Vision API — Certificate Data Extraction
"""

import os
import json
import base64
import requests
import time
from dotenv import load_dotenv

load_dotenv(override=True)


def get_empty_data() -> dict:
    return {
        "name":         "Manual Check",
        "university":   "Unknown",
        "degree":       "Unknown",
        "year":         "Unknown",
        "phone_number": "Unknown",
        "email":        "",
    }


def extract_details_from_certificate(image_path: str) -> dict:
    print(f"[*] ALIAS_X Vision: Scanning {image_path}...")

    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        print("[!] Critical: GOOGLE_API_KEY missing.")
        return get_empty_data()

    if not os.path.exists(image_path):
        print("[!] Error: Image not found.")
        return get_empty_data()

    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [
                {"text": (
                    "Extract these details in JSON: name, university, degree, year, "
                    "phone_number, email. If not found, use empty string. Return ONLY JSON."
                )},
                {"inline_data": {
                    "mime_type": "image/png",
                    "data": base64_image
                }}
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
    }

    safe_models = [
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]

    for model in safe_models:
        print(f"    > Attempting model: {model}...")
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={api_key}")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                print(f"    > ✅ Connected to {model}!")
                result = response.json()
                try:
                    raw_text   = result["candidates"][0]["content"]["parts"][0]["text"]
                    clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                    print(f"    > Raw: {clean_json[:200]}")
                    safe_data  = get_empty_data()
                    safe_data.update(json.loads(clean_json))
                    print(f"    > Extracted: {safe_data.get('name')} | {safe_data.get('university')}")
                    return safe_data
                except (KeyError, IndexError):
                    print("    > [!] Empty response. Trying next...")
                    continue
                except json.JSONDecodeError as e:
                    print(f"    > [!] JSON parse failed: {e}")
                    continue

            elif response.status_code == 404:
                print(f"    > ⚠️ {model} not found (404). Skipping...")
                continue
            elif response.status_code == 429:
                print(f"    > ⛔ {model} Quota Exceeded (429). Skipping...")
                time.sleep(1)
                continue
            else:
                print(f"    > [!] API Error {response.status_code}: {response.text[:200]}")
                if response.status_code >= 500:
                    continue
                break

        except Exception as e:
            print(f"    > Error connecting to {model}: {e}")
            continue

    print("[!] All models failed. Defaulting to Manual Check.")
    return get_empty_data()