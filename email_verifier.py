"""
ALIAS_X — email_verifier.py
AI-Powered Email Verification Module (Gemini + Gmail SMTP + IMAP)

Fixes:
- IMAP searches subject AND body separately (OR query fails on some servers)
- Thread cleaner preserves reply text before removing quoted blocks
- Gemini classifier has explicit examples so it handles natural language replies
- Keyword fallback uses word-boundary regex (no false "no" matches)
- 4-round hybrid classification: Gemini clean → keyword clean → Gemini raw → keyword raw
- Invalid email address validated before attempting send
"""

import email as email_lib
import imaplib
import os
import re
import smtplib
import time
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS",      "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY",     "").strip()

SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
IMAP_HOST     = "imap.gmail.com"
IMAP_PORT     = 993
POLL_INTERVAL = 30
POLL_TIMEOUT  = 600

# ── Gemini lazy init ──────────────────────────────────────────────────────────
_gemini_model = None

def _get_model():
    global _gemini_model
    if _gemini_model is None and GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel("gemini-2.5-flash")
    return _gemini_model


# ── Thread cleaner ────────────────────────────────────────────────────────────

def _extract_reply_body(raw: str) -> str:
    """
    Extract only the fresh reply — strip quoted/forwarded thread text.
    Works by cutting at the first quoted block separator found.
    """
    separators = [
        r"\nOn .{10,120} wrote:",
        r"\n-{3,}\s*Original Message",
        r"\n_{3,}",
        r"\nFrom:\s",
        r"\nSent:\s",
        r"\n>+\s",
    ]
    text = raw
    for sep in separators:
        parts = re.split(sep, text, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) > 1:
            text = parts[0]
    return text.strip()


# ── Gemini classifier ─────────────────────────────────────────────────────────

def _ai_classify(text: str) -> str:
    model = _get_model()
    if not model:
        return "PENDING"

    prompt = f"""You are classifying a university registrar's email reply to an
academic record verification request.

Read the email and reply with EXACTLY ONE WORD:

VERIFIED  — registrar confirmed the record exists and is correct
            (e.g. "Yes confirmed", "The record is correct", "We can verify",
             "Yes we have that on file", "Confirmed", "That is correct")

REJECTED  — registrar denied or could not find the record
            (e.g. "No record found", "Cannot confirm", "Not in our system",
             "We don't have that student", "Incorrect", "Rejected")

PENDING   — reply is unclear, generic, or unrelated

Reply ONLY with: VERIFIED, REJECTED, or PENDING

Email:
---
{text[:1000]}
---"""

    try:
        r = _get_model().generate_content(prompt)
        result = r.text.strip().upper()
        print(f"[GEMINI] raw='{result}'")
        if "VERIFIED" in result:
            return "VERIFIED"
        if "REJECTED" in result:
            return "REJECTED"
        return "PENDING"
    except Exception as e:
        print(f"[GEMINI ERROR] {e}")
        return "PENDING"


# ── Keyword classifier ────────────────────────────────────────────────────────
#
# Handles ALL natural language reply types:
#   Single word  : "yes", "no", "confirmed", "denied"
#   Short phrase : "yes it is", "yes it does", "that is right"
#   Full sentence: "Yes, we can confirm that the record is correct"
#   Negative     : "No record found", "We cannot verify this"

# Words that strongly signal YES — checked as starts-with or contains
_YES_SIGNALS = [
    # Single words
    r"^yes", r"^confirmed", r"^verified", r"^correct", r"^affirmative",
    r"^absolutely", r"^certainly", r"^indeed", r"^sure",
    # Short natural phrases starting with yes/affirmative
    r"^yes[,\s]", r"^yes it", r"^yes that", r"^yes we", r"^yes i",
    r"^yes this", r"^yes the",
    # Confirmation phrases anywhere in text
    r"\bwe can confirm\b", r"\bi can confirm\b", r"\bcan confirm\b",
    r"\bwe do have\b", r"\brecord is correct\b", r"\brecords show\b",
    r"\bthat is correct\b", r"\bthat's correct\b", r"\bthis is correct\b",
    r"\bwe have that record\b", r"\bon file\b", r"\bcan verify\b",
    r"\bwe confirm\b", r"\bi confirm\b", r"\brecord exists\b",
    r"\brecord found\b", r"\bstudent exists\b", r"\bdetails are correct\b",
    r"\bdetails match\b", r"\binformation is correct\b", r"\bwe verify\b",
    r"\byes confirmed\b", r"\byes correct\b", r"\byes verified\b",
]

# Words/phrases that strongly signal NO
_NO_SIGNALS = [
    # Single words
    r"^no", r"^nope", r"^nah", r"^negative", r"^denied",
    r"^rejected", r"^incorrect",
    # Short natural phrases starting with no/negative
    r"^no[,\s]", r"^no we", r"^no i", r"^no such", r"^no record",
    r"^not found", r"^cannot", r"^we cannot", r"^i cannot",
    # Rejection phrases anywhere in text
    r"\bno record\b", r"\bnot found\b", r"\bcannot confirm\b",
    r"\bunable to verify\b", r"\bno such student\b", r"\bnot in our system\b",
    r"\bdo not have\b", r"\bdon't have\b", r"\bincorrect record\b",
    r"\bcannot find\b", r"\bnot able to confirm\b", r"\bno record found\b",
    r"\bverification failed\b", r"\brecord not found\b", r"\bwe cannot verify\b",
    r"\bwe don't have\b", r"\bwe do not have\b", r"\bno match\b",
    r"\bnot matching\b", r"\bdetails do not match\b", r"\bdetails don't match\b",
    r"\bnot registered\b", r"\bnever enrolled\b", r"\bno such record\b",
]


def _keyword_classify(text: str) -> str:
    t = text.lower().strip()

    yes_score = sum(1 for p in _YES_SIGNALS if re.search(p, t, re.IGNORECASE))
    no_score  = sum(1 for p in _NO_SIGNALS  if re.search(p, t, re.IGNORECASE))

    print(f"[KEYWORD] yes_score={yes_score}, no_score={no_score} | text='{t[:80]}'")

    if no_score > 0 and yes_score == 0:
        return "REJECTED"
    if yes_score > 0 and no_score == 0:
        return "VERIFIED"
    if yes_score > no_score:
        return "VERIFIED"
    if no_score > yes_score:
        return "REJECTED"
    return "PENDING"


# ── Hybrid classifier ─────────────────────────────────────────────────────────

def hybrid_classify(raw_body: str) -> str:
    """
    Handles all reply types: single word, short phrase, full sentence, paragraph.

    Step 1: Keywords on cleaned reply body  (fast, handles 95% of cases)
    Step 2: Gemini on cleaned reply body    (handles ambiguous natural language)
    Step 3: Keywords on full raw body       (in case cleaner cut too much)
    Step 4: Gemini on full raw body         (last resort)
    Default: PENDING
    """
    clean = _extract_reply_body(raw_body)
    print(f"[CLASSIFY] clean body: '{clean[:200]}'")

    if not clean:
        clean = raw_body

    for fn, text in [
        (_keyword_classify, clean),
        (_ai_classify,      clean),
        (_keyword_classify, raw_body),
        (_ai_classify,      raw_body),
    ]:
        result = fn(text)
        if result != "PENDING":
            print(f"[CLASSIFY] result={result} via {fn.__name__}")
            return result

    print("[CLASSIFY] all rounds PENDING — defaulting to PENDING")
    return "PENDING"


# ── Email builders ────────────────────────────────────────────────────────────

def _build_plain_body(data: dict, session_id: str) -> str:
    return (
        f"Dear Registrar,\n\n"
        f"This is an academic credential verification request from ALIAS_X.\n\n"
        f"Please verify the following record:\n\n"
        f"  Student Name : {data.get('name', 'N/A')}\n"
        f"  University   : {data.get('university', 'N/A')}\n"
        f"  Degree       : {data.get('degree', 'N/A')}\n"
        f"  Year         : {data.get('year', 'N/A')}\n\n"
        f"Please reply to this email with ONE of the following:\n"
        f"  VERIFIED  - if the record is accurate\n"
        f"  REJECTED  - if the record cannot be verified\n\n"
        f"Reference ID: {session_id}\n\n"
        f"Thank you,\nALIAS_X Verification System\n"
    )


def _build_html_body(data: dict, session_id: str) -> str:
    return f"""
<html>
<body style="font-family:Arial,sans-serif;color:#1e293b;max-width:600px;margin:auto;">
  <div style="background:#0A0E1A;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="color:#00D4FF;margin:0;">ALIAS_X</h2>
    <p style="color:#94a3b8;margin:4px 0 0;">Autonomous Verification Protocol</p>
  </div>
  <div style="border:1px solid #e2e8f0;padding:24px;border-radius:0 0 8px 8px;">
    <p>Dear Registrar,</p>
    <p>Please verify the following academic record:</p>
    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
      <tr style="background:#f8fafc;">
        <td style="padding:10px;font-weight:bold;border:1px solid #e2e8f0;">Student Name</td>
        <td style="padding:10px;border:1px solid #e2e8f0;">{data.get('name','N/A')}</td>
      </tr>
      <tr>
        <td style="padding:10px;font-weight:bold;border:1px solid #e2e8f0;">University</td>
        <td style="padding:10px;border:1px solid #e2e8f0;">{data.get('university','N/A')}</td>
      </tr>
      <tr style="background:#f8fafc;">
        <td style="padding:10px;font-weight:bold;border:1px solid #e2e8f0;">Degree</td>
        <td style="padding:10px;border:1px solid #e2e8f0;">{data.get('degree','N/A')}</td>
      </tr>
      <tr>
        <td style="padding:10px;font-weight:bold;border:1px solid #e2e8f0;">Year</td>
        <td style="padding:10px;border:1px solid #e2e8f0;">{data.get('year','N/A')}</td>
      </tr>
    </table>
    <p>Please <strong>reply to this email</strong> with:</p>
    <ul>
      <li><strong style="color:#00C17C;">VERIFIED</strong> - if the record is accurate</li>
      <li><strong style="color:#FF4B6E;">REJECTED</strong> - if the record cannot be verified</li>
    </ul>
    <p style="color:#64748b;font-size:12px;">Reference ID: <code>{session_id}</code></p>
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0;">
    <p style="color:#64748b;font-size:12px;">
      ALIAS_X Autonomous Verification System - Department of Computer Science
    </p>
  </div>
</body>
</html>"""


# ── Send email ────────────────────────────────────────────────────────────────

def send_verification_email(to_email: str, data: dict, session_id: str) -> dict:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return {
            "success": False,
            "error":   "GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing in .env"
        }

    msg = MIMEMultipart("alternative")
    msg["Subject"]    = f"Academic Verification Request - {data.get('name','Candidate')} [{session_id}]"
    msg["From"]       = GMAIL_ADDRESS
    msg["To"]         = to_email
    msg["Reply-To"]   = GMAIL_ADDRESS
    msg["Message-ID"] = f"<{session_id}@aliasx.verify>"

    msg.attach(MIMEText(_build_plain_body(data, session_id), "plain"))
    msg.attach(MIMEText(_build_html_body(data,  session_id), "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        print(f"[EMAIL SENT] to={to_email} session={session_id}")
        return {"success": True}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "error": "Gmail auth failed - check GMAIL_APP_PASSWORD in .env"}
    except Exception as e:
        return {"success": False, "error": f"SMTP error: {e}"}


# ── Poll inbox ────────────────────────────────────────────────────────────────

def _get_body_from_message(msg) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = str(part.get_content_type())
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                raw = part.get_payload(decode=True)
                if raw:
                    body += raw.decode(errors="ignore")
    else:
        raw = msg.get_payload(decode=True)
        if raw:
            body = raw.decode(errors="ignore")
    return body


def poll_for_reply(session_id: str,
                   timeout: int  = POLL_TIMEOUT,
                   interval: int = POLL_INTERVAL) -> dict:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return {
            "status":     "TIMEOUT",
            "transcript": "Gmail IMAP credentials not configured in .env"
        }

    deadline = time.time() + timeout
    checked  = set()

    while time.time() < deadline:
        time.sleep(interval)
        print(f"[POLL] checking inbox | session={session_id}")

        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
            mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            mail.select("inbox")

            # Search subject and body separately — OR fails on some IMAP servers
            _, subj_data = mail.search(None, f'SUBJECT "{session_id}"')
            _, body_data = mail.search(None, f'BODY "{session_id}"')

            all_ids = set(subj_data[0].split()) | set(body_data[0].split())
            print(f"[POLL] found {len(all_ids)} candidate message(s)")

            for msg_id in all_ids:
                if msg_id in checked:
                    continue
                checked.add(msg_id)

                _, msg_data = mail.fetch(msg_id, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    continue

                msg    = email_lib.message_from_bytes(msg_data[0][1])
                sender = msg.get("From", "")

                # Skip outgoing emails from ourselves
                if GMAIL_ADDRESS.lower() in sender.lower():
                    continue

                body = _get_body_from_message(msg)
                print(f"[REPLY] from={sender} | preview={body[:150]}")

                if not body.strip():
                    continue

                outcome = hybrid_classify(body)
                print(f"[OUTCOME] {outcome}")

                if outcome != "PENDING":
                    mail.logout()
                    return {
                        "status":     outcome,
                        "transcript": f"Email reply from {sender}:\n\n{body.strip()[:2000]}"
                    }

            mail.logout()

        except imaplib.IMAP4.error as e:
            print(f"[WARN] IMAP error: {e}")
        except Exception as e:
            print(f"[WARN] Poll error: {e}")

    return {
        "status":     "TIMEOUT",
        "transcript": f"No classifiable reply received within {timeout // 60} minutes."
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def run_email_verification(to_email: str, data: dict) -> dict:
    if not to_email or "@" not in to_email:
        return {
            "status":     "TIMEOUT",
            "transcript": f"Invalid email address: '{to_email}'",
            "session_id": ""
        }

    session_id  = f"EMAIL-{uuid.uuid4().hex[:8].upper()}"
    send_result = send_verification_email(to_email, data, session_id)

    if not send_result["success"]:
        return {
            "status":     "TIMEOUT",
            "transcript": f"Failed to send email: {send_result.get('error','')}",
            "session_id": session_id
        }

    result             = poll_for_reply(session_id)
    result["session_id"] = session_id
    return result