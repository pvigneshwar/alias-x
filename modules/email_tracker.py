"""
ALIAS_X · Email Tracker
Sends verification email and polls Gmail inbox for registrar reply.
"""

import os
import re
import time
import imaplib
import smtplib
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv(override=True)


# ── Send Email ─────────────────────────────────────────────────
def send_verification_email(to_email: str, data: dict) -> dict:
    """
    Sends a verification request email to the registrar.
    Returns: { "success": bool, "message": str, "ref_id": str }
    """
    smtp_user = os.getenv("SMTP_EMAIL", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()

    if not smtp_user or not smtp_pass:
        return {"success": False, "message": "SMTP credentials not configured.", "ref_id": ""}

    ref_id = f"ALIASX-{int(time.time())}"

    subject = f"[ALIAS_X] Credential Verification Request — {data.get('name','Unknown')} [{ref_id}]"
    body = f"""Dear Registrar,

ALIAS_X Autonomous Verification Protocol is requesting confirmation
of the following academic credentials:

  Reference ID : {ref_id}
  Student Name : {data.get('name', 'N/A')}
  University   : {data.get('university', 'N/A')}
  Degree       : {data.get('degree', 'N/A')}
  Year         : {data.get('year', 'N/A')}

Please REPLY to this email with one of the following:
  ✔ CONFIRMED — credentials are verified
  ✗ DENIED    — credentials could not be verified

Include the Reference ID [{ref_id}] in your reply subject line.

—
ALIAS_X Autonomous Verification Protocol v2.4.1
This is an automated message. Do not forward.
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = smtp_user
    msg["To"]      = to_email
    msg["Reply-To"] = smtp_user
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as s:
            s.login(smtp_user, smtp_pass)
            s.sendmail(smtp_user, to_email, msg.as_string())
        print(f"[EMAIL] ✅ Sent to {to_email} | Ref: {ref_id}")
        return {"success": True, "message": f"Email dispatched to {to_email}", "ref_id": ref_id}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "SMTP auth failed — check credentials.", "ref_id": ""}
    except Exception as e:
        return {"success": False, "message": f"Email error: {e}", "ref_id": ""}


# ── Poll Gmail Inbox for Reply ─────────────────────────────────
def check_email_reply(ref_id: str) -> dict:
    """
    Polls Gmail IMAP inbox for a reply containing the ref_id.
    Returns: { "replied": bool, "verdict": str, "body": str, "from": str, "subject": str }
    """
    smtp_user = os.getenv("SMTP_EMAIL", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()

    if not smtp_user or not smtp_pass:
        return {"replied": False, "verdict": "INCONCLUSIVE",
                "body": "", "from": "", "subject": "SMTP not configured"}

    if not ref_id:
        return {"replied": False, "verdict": "INCONCLUSIVE",
                "body": "", "from": "", "subject": "No ref_id provided"}

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(smtp_user, smtp_pass)
        mail.select("INBOX")

        # Search for emails containing the ref_id
        _, search_data = mail.search(None, f'BODY "{ref_id}"')
        email_ids = search_data[0].split()

        if not email_ids:
            mail.logout()
            return {"replied": False, "verdict": "PENDING",
                    "body": "", "from": "", "subject": "No reply yet"}

        # Get the latest matching email
        latest_id = email_ids[-1]
        _, msg_data = mail.fetch(latest_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email_lib.message_from_bytes(raw_email)

        # Decode subject
        raw_subject = msg.get("Subject", "")
        decoded_subject = ""
        for part, enc in decode_header(raw_subject):
            if isinstance(part, bytes):
                decoded_subject += part.decode(enc or "utf-8", errors="replace")
            else:
                decoded_subject += part

        sender = msg.get("From", "")

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

        mail.logout()

        # Analyse reply for verdict
        verdict = _analyze_email_reply(body, decoded_subject)

        print(f"[EMAIL] Reply found from {sender} | Verdict: {verdict}")
        return {
            "replied":  True,
            "verdict":  verdict,
            "body":     body.strip(),
            "from":     sender,
            "subject":  decoded_subject,
        }

    except imaplib.IMAP4.error as e:
        print(f"[EMAIL] IMAP error: {e}")
        return {"replied": False, "verdict": "INCONCLUSIVE",
                "body": "", "from": "", "subject": f"IMAP error: {e}"}
    except Exception as e:
        print(f"[EMAIL] Check error: {e}")
        return {"replied": False, "verdict": "INCONCLUSIVE",
                "body": "", "from": "", "subject": f"Error: {e}"}


# ── Analyse Reply Text ─────────────────────────────────────────
def _analyze_email_reply(body: str, subject: str) -> str:
    """
    Scans email body/subject for confirmation or denial keywords.
    Falls back to Gemini if ambiguous.
    """
    combined = (body + " " + subject).lower()

    confirm_keywords = ["confirmed", "confirm", "verified", "correct", "valid",
                        "yes", "approved", "accurate", "certify", "certifies"]
    deny_keywords    = ["denied", "deny", "not found", "invalid", "incorrect",
                        "no record", "cannot confirm", "unverified", "false",
                        "does not match", "not enrolled"]

    confirm_score = sum(1 for k in confirm_keywords if k in combined)
    deny_score    = sum(1 for k in deny_keywords    if k in combined)

    if confirm_score > deny_score and confirm_score > 0:
        return "CONFIRMED"
    if deny_score > confirm_score and deny_score > 0:
        return "DENIED"

    # Ambiguous — use Gemini
    return _gemini_email_verdict(body)


def _gemini_email_verdict(body: str) -> str:
    """Uses Gemini to determine verdict from ambiguous email reply."""
    try:
        import requests
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not api_key or not body.strip():
            return "INCONCLUSIVE"

        prompt = (
            "You are an academic verification analyst. "
            "Read this email reply from a university registrar and determine if the student's "
            "credentials were CONFIRMED, DENIED, or if the reply is INCONCLUSIVE.\n\n"
            f"Email body:\n{body[:1000]}\n\n"
            "Return ONLY one word: CONFIRMED, DENIED, or INCONCLUSIVE"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 10},
        }
        headers = {"Content-Type": "application/json"}

        for model in ["gemini-1.5-flash", "gemini-2.5-flash"]:
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{model}:generateContent?key={api_key}")
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            if r.status_code == 200:
                verdict = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip().upper()
                if verdict in ("CONFIRMED", "DENIED", "INCONCLUSIVE"):
                    return verdict
    except Exception as e:
        print(f"[EMAIL] Gemini verdict error: {e}")

    return "INCONCLUSIVE"
