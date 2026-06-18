"""
ALIAS_X — test_alias_x.py
Full test suite: 29 test cases across Authentication, Vision Engine,
AI Caller, Integration, and System levels. (IEEE 829 conventions)
Run: pytest test_alias_x.py -v
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# ── Make sure project root is on path ─────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from auth_manager import validate_login, register_agent, _hash
from ocr_engine import extract_certificate_data, _validate, SIMULATION_DATA
from ai_caller import sanitise_phone, initiate_verification_call, _build_prompt


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION — 6 Unit Tests (AUTH-01 … AUTH-06)
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthentication(unittest.TestCase):
    """Unit tests for auth_manager.py"""

    CODENAME = "TestAgent_001"
    KEY      = "SecureKey!99"

    def setUp(self):
        """Register a fresh test agent before each test."""
        # Remove existing entry if present
        self._patch_agents({})
        result = register_agent(self.CODENAME, self.KEY)
        self.assertTrue(result["success"], "setUp: registration failed unexpectedly")
        self.agent_id = result["agent_id"]

    def tearDown(self):
        """Clean up agents.json after each test."""
        self._patch_agents({})

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _patch_agents(data: dict):
        with open("agents.json", "w") as f:
            json.dump(data, f)

    # ── AUTH-01: Valid credentials → access granted ──────────────────────────
    def test_AUTH01_valid_credentials(self):
        result = validate_login(self.CODENAME, self.KEY)
        self.assertTrue(result["success"])
        self.assertIn("agent_id", result)

    # ── AUTH-02: Wrong Access Key → access denied ────────────────────────────
    def test_AUTH02_wrong_access_key(self):
        result = validate_login(self.CODENAME, "WrongKey!")
        self.assertFalse(result["success"])

    # ── AUTH-03: Unknown Codename → access denied ────────────────────────────
    def test_AUTH03_unknown_codename(self):
        result = validate_login("NoSuchAgent", self.KEY)
        self.assertFalse(result["success"])

    # ── AUTH-04: Empty fields → validation error ─────────────────────────────
    def test_AUTH04_empty_fields(self):
        result = validate_login("", "")
        self.assertFalse(result["success"])
        self.assertIn("message", result)

    # ── AUTH-05: JSON injection attempt → sanitised and denied ───────────────
    def test_AUTH05_json_injection(self):
        result = validate_login('{"admin":true}', "anykey")
        self.assertFalse(result["success"])

    # ── AUTH-06: Duplicate Codename registration → rejected ──────────────────
    def test_AUTH06_duplicate_registration(self):
        result = register_agent(self.CODENAME, "AnotherKey")
        self.assertFalse(result["success"])
        self.assertIn("message", result)


# ══════════════════════════════════════════════════════════════════════════════
# VISION ENGINE — 6 Unit Tests (OCR-01 … OCR-06)
# ══════════════════════════════════════════════════════════════════════════════

class TestVisionEngine(unittest.TestCase):
    """Unit tests for ocr_engine.py"""

    def _make_upload(self, content: bytes = b"\xff\xd8\xff" + b"\x00" * 100,
                     name: str = "cert.jpg"):
        """Return a minimal mock UploadedFile."""
        f = MagicMock()
        f.read.return_value = content
        f.name = name
        return f

    # ── OCR-01: Clear digital JPG → all 4 fields extracted ───────────────────
    def test_OCR01_clear_jpg(self):
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "name": "Alice Smith",
            "university": "MIT",
            "degree": "Bachelor of Science",
            "year": "2021",
        })
        with patch("ocr_engine.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
            with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
                result = extract_certificate_data(self._make_upload(), simulation=False)
        self.assertEqual(result["name"], "Alice Smith")
        self.assertEqual(result["university"], "MIT")
        self.assertEqual(result["degree"], "Bachelor of Science")
        self.assertEqual(result["year"], "2021")

    # ── OCR-02: Clear digital PNG → all 4 fields extracted ───────────────────
    def test_OCR02_clear_png(self):
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "name": "Bob Jones",
            "university": "Stanford University",
            "degree": "Master of Engineering",
            "year": "2020",
        })
        with patch("ocr_engine.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
            with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
                result = extract_certificate_data(self._make_upload(name="cert.png"), simulation=False)
        self.assertEqual(result["name"], "Bob Jones")
        self.assertIsNotNone(result["year"])

    # ── OCR-03: Low-quality scan → fields extracted; noisy year flagged ───────
    def test_OCR03_low_quality_scan(self):
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "name": "Carol White",
            "university": "UCL",
            "degree": "PhD Philosophy",
            "year": "20l8",        # OCR noise — letter 'l' instead of '1'
        })
        with patch("ocr_engine.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
            with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
                result = extract_certificate_data(self._make_upload(), simulation=False)
        self.assertIsNone(result["year"])           # flagged as invalid
        self.assertEqual(result["name"], "Carol White")

    # ── OCR-04: Invalid API key → SIMULATION_DATA returned, no crash ─────────
    def test_OCR04_invalid_api_key(self):
        with patch("ocr_engine.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value.generate_content.side_effect = Exception("API key invalid")
            with patch.dict(os.environ, {"GEMINI_API_KEY": "bad-key"}):
                result = extract_certificate_data(self._make_upload(), simulation=False)
        self.assertEqual(result["name"], SIMULATION_DATA["name"])   # fallback returned

    # ── OCR-05: Implausible year (1899) → year = None, flagged ───────────────
    def test_OCR05_implausible_year(self):
        data = {"name": "Dave Brown", "university": "Harvard", "degree": "BA", "year": "1899"}
        result = _validate(data)
        self.assertIsNone(result["year"])

    # ── OCR-06: Non-alphabetic name → name = None, flagged ───────────────────
    def test_OCR06_non_alphabetic_name(self):
        data = {"name": "$$FAKE$$", "university": "Oxford", "degree": "MSc", "year": "2020"}
        result = _validate(data)
        self.assertIsNone(result["name"])


# ══════════════════════════════════════════════════════════════════════════════
# AI CALLER — 6 Unit Tests (CALL-01 … CALL-06)
# ══════════════════════════════════════════════════════════════════════════════

class TestAICaller(unittest.TestCase):
    """Unit tests for ai_caller.py"""

    CERT = {
        "name": "Eve Taylor",
        "university": "Imperial College London",
        "degree": "MEng Electrical Engineering",
        "year": "2023",
    }

    # ── CALL-01: E.164 with spaces → normalised ───────────────────────────────
    def test_CALL01_e164_with_spaces(self):
        result = sanitise_phone("+44 1865 270 000")
        self.assertEqual(result, "+441865270000")

    # ── CALL-02: Dashes in number → normalised ────────────────────────────────
    def test_CALL02_dashes_in_number(self):
        result = sanitise_phone("01865-270-000")
        self.assertEqual(result, "01865270000")

    # ── CALL-03: Non-numeric string → ValueError raised ───────────────────────
    def test_CALL03_non_numeric_raises(self):
        with self.assertRaises(ValueError):
            sanitise_phone("not-a-number")

    # ── CALL-04: Affirmative transcript → VERIFIED ───────────────────────────
    def test_CALL04_affirmative_transcript(self):
        result = initiate_verification_call("+441865270000", self.CERT, simulation=False)
        # Mock a completed call with affirmative transcript
        with patch("ai_caller.requests.post") as mock_post, \
             patch("ai_caller.requests.get") as mock_get, \
             patch("ai_caller.time.sleep"):
            mock_post.return_value.json.return_value = {"call_id": "abc123"}
            mock_post.return_value.raise_for_status = MagicMock()
            mock_get.return_value.json.return_value = {
                "status": "completed",
                "concatenated_transcript": "Yes, we can confirm that record is correct.",
            }
            mock_get.return_value.raise_for_status = MagicMock()
            with patch.dict(os.environ, {"BLAND_AI_KEY": "fake-key"}):
                import ai_caller as ac
                ac.BLAND_KEY = "fake-key"
                result = ac.initiate_verification_call("+441865270000", self.CERT, simulation=False)
        self.assertEqual(result["status"], "VERIFIED")

    # ── CALL-05: Negative transcript → REJECTED ───────────────────────────────
    def test_CALL05_negative_transcript(self):
        with patch("ai_caller.requests.post") as mock_post, \
             patch("ai_caller.requests.get") as mock_get, \
             patch("ai_caller.time.sleep"):
            mock_post.return_value.json.return_value = {"call_id": "xyz789"}
            mock_post.return_value.raise_for_status = MagicMock()
            mock_get.return_value.json.return_value = {
                "status": "completed",
                "concatenated_transcript": "No, no record found in our system.",
            }
            mock_get.return_value.raise_for_status = MagicMock()
            import ai_caller as ac
            ac.BLAND_KEY = "fake-key"
            result = ac.initiate_verification_call("+441865270000", self.CERT, simulation=False)
        self.assertEqual(result["status"], "REJECTED")

    # ── CALL-06: Poll timeout (120 s) → TIMEOUT returned ─────────────────────
    def test_CALL06_poll_timeout(self):
        with patch("ai_caller.requests.post") as mock_post, \
             patch("ai_caller.requests.get") as mock_get, \
             patch("ai_caller.time.sleep"), \
             patch("ai_caller.time.time", side_effect=[0] + [200] * 50):
            mock_post.return_value.json.return_value = {"call_id": "timeout_id"}
            mock_post.return_value.raise_for_status = MagicMock()
            mock_get.return_value.json.return_value = {"status": "in_progress"}
            mock_get.return_value.raise_for_status = MagicMock()
            import ai_caller as ac
            ac.BLAND_KEY = "fake-key"
            result = ac.initiate_verification_call("+441865270000", self.CERT, simulation=False)
        self.assertEqual(result["status"], "TIMEOUT")


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION — 6 Tests (INT-01 … INT-06)
# ══════════════════════════════════════════════════════════════════════════════

class TestIntegration(unittest.TestCase):
    """Module-to-module integration tests."""

    def setUp(self):
        with open("agents.json", "w") as f:
            json.dump({}, f)

    def tearDown(self):
        with open("agents.json", "w") as f:
            json.dump({}, f)

    # ── INT-01: Register → login → get agent_id roundtrip ────────────────────
    def test_INT01_register_then_login(self):
        reg = register_agent("IntAgent", "Pass123!")
        self.assertTrue(reg["success"])
        login = validate_login("IntAgent", "Pass123!")
        self.assertTrue(login["success"])
        self.assertEqual(login["agent_id"], reg["agent_id"])

    # ── INT-02: OCR simulation data passes _validate without None fields ──────
    def test_INT02_simulation_data_valid(self):
        result = _validate(SIMULATION_DATA.copy())
        for field in ("name", "university", "degree", "year"):
            self.assertIsNotNone(result[field], f"Field '{field}' unexpectedly None")

    # ── INT-03: sanitise_phone accepts output of Intel Uplink mock phone ──────
    def test_INT03_uplink_phone_sanitised(self):
        mock_phone = "+44 (0)1865 270-000"
        cleaned = sanitise_phone(mock_phone)
        self.assertTrue(cleaned.startswith("+44") or cleaned.isdigit())

    # ── INT-04: _build_prompt uses all cert fields ────────────────────────────
    def test_INT04_prompt_includes_all_fields(self):
        cert = {"name": "Frank Lee", "university": "UCL",
                "degree": "BSc Physics", "year": "2019"}
        prompt = _build_prompt(cert)
        self.assertIn("Frank Lee", prompt)
        self.assertIn("BSc Physics", prompt)
        self.assertIn("2019", prompt)

    # ── INT-05: Hash consistency — same input always same digest ─────────────
    def test_INT05_hash_consistency(self):
        self.assertEqual(_hash("TestKey"), _hash("TestKey"))
        self.assertNotEqual(_hash("TestKey"), _hash("testkey"))

    # ── INT-06: register_agent rejects empty Codename ────────────────────────
    def test_INT06_register_empty_codename(self):
        result = register_agent("", "SomeKey")
        self.assertFalse(result["success"])


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM — 5 End-to-End Simulation Tests (SYS-01 … SYS-05)
# ══════════════════════════════════════════════════════════════════════════════

class TestSystem(unittest.TestCase):
    """End-to-end pipeline tests using Simulation Mode."""

    CERT = {
        "name": "Grace Hopper",
        "university": "Yale University",
        "degree": "PhD Mathematics",
        "year": "1934",
    }

    # ── SYS-01: Simulation mode → green VERIFIED badge ───────────────────────
    def test_SYS01_simulation_verified(self):
        result = initiate_verification_call("+12125551234", self.CERT, simulation=True)
        self.assertEqual(result["status"], "VERIFIED")
        self.assertIn("transcript", result)

    # ── SYS-02: Name contains 'Test Name' → REJECTED badge ───────────────────
    def test_SYS02_fraud_detection_rejected(self):
        cert = dict(self.CERT, name="Test Name Candidate")
        result = initiate_verification_call("+12125551234", cert, simulation=True)
        self.assertEqual(result["status"], "REJECTED")

    # ── SYS-03: Intel Uplink empty return → no crash, empty strings ──────────
    def test_SYS03_uplink_failure_graceful(self):
        with patch("intel_uplink.gsearch", side_effect=Exception("No network")):
            from intel_uplink import get_registrar_contact
            result = get_registrar_contact("Nonexistent University", simulation=False)
        self.assertIn("phone", result)
        self.assertIn("email", result)
        # No exception raised — graceful degradation confirmed

    # ── SYS-04: Bland AI unreachable → TIMEOUT returned, no crash ────────────
    def test_SYS04_bland_ai_unreachable(self):
        with patch("ai_caller.requests.post", side_effect=Exception("Connection refused")):
            import ai_caller as ac
            ac.BLAND_KEY = "fake-key"
            result = ac.initiate_verification_call("+12125551234", self.CERT, simulation=False)
        self.assertIn(result["status"], ("TIMEOUT", "REJECTED"))
        self.assertIn("transcript", result)

    # ── SYS-05: 50 consecutive simulation runs → 100% consistent, zero crashes
    def test_SYS05_50_consecutive_runs_stable(self):
        errors   = 0
        statuses = set()
        for i in range(50):
            try:
                r = initiate_verification_call("+12125551234", self.CERT, simulation=True)
                statuses.add(r["status"])
            except Exception:
                errors += 1
        self.assertEqual(errors, 0, "Crashes detected in 50-run stability test")
        self.assertEqual(statuses, {"VERIFIED"}, "Inconsistent outcomes in simulation mode")


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
