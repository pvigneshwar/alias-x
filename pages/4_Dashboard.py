"""
╔══════════════════════════════════════════════════════════════╗
║    ALIAS_X · Uplink Terminal Dashboard · pages/4_Dashboard.py ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import base64
import smtplib
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st
from dotenv import load_dotenv

# ── Path & Imports ─────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.ocr_engine import extract_details_from_certificate, get_empty_data
from modules.ui_helpers import inject_global_ui, get_page_icon, _load_image_b64

load_dotenv(ROOT / ".env")

# ── Simulation Config ──────────────────────────────────────────
SIMULATION_MODE = os.getenv("USE_TEST_DATA", "FALSE").strip().upper() == "TRUE"
TEST_PHONE      = os.getenv("TEST_PHONE_NUMBER", "").strip()
TEST_EMAIL      = os.getenv("TEST_EMAIL_ADDRESS", "").strip()

# ── Page Config ────────────────────────────────────────────────
st.set_page_config(
    page_title="ALIAS_X · Uplink Terminal",
    page_icon=get_page_icon(),
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_ui()

st.markdown("""<style>
.section-num { color:#ff003c; font-family:"Ethnocentric",sans-serif;
               font-size:.7rem; letter-spacing:.2em; }
.channel-ready   { color:#00ffaa; font-size:.72rem; letter-spacing:.05em; }
.channel-offline { color:#ff003c; font-size:.72rem; letter-spacing:.05em; }
</style>""", unsafe_allow_html=True)

# ── Auth Guard ─────────────────────────────────────────────────
if not st.session_state.get("logged_in", False):
    logo_b64 = _load_image_b64("aliasX_logo.png")
    logo_tag = (f'<img style="display:block;margin:0 auto;width:80px;border-radius:50%;" '
                f'src="data:image/png;base64,{logo_b64}" alt="AX"/>'
                if logo_b64 else "🔺")
    st.markdown(f"""
<div style="max-width:400px;margin:3rem auto;text-align:center;
            background:rgba(8,8,15,0.9);border:1px solid rgba(255,0,60,0.3);
            border-radius:4px;padding:2rem;">
    {logo_tag}
    <h2 style="font-family:'Ethnocentric',sans-serif;color:#ff003c;
               font-size:1rem;letter-spacing:.2em;margin:1rem 0 .5rem;">
        ACCESS RESTRICTED
    </h2>
    <p style="color:#7a7a9a;font-size:.78rem;line-height:1.6;margin:.5rem 0 1.2rem;">
        Uplink Terminal requires operator authentication.<br/>Please login to proceed.
    </p>
</div>""", unsafe_allow_html=True)
    if st.button("⚡ GO TO LOGIN"):
        st.switch_page("pages/2_Login.py")
    st.stop()

# ── Session State Init ─────────────────────────────────────────
if "ocr_data" not in st.session_state:
    st.session_state.ocr_data = get_empty_data()
if "ph" not in st.session_state:
    st.session_state.ph = ""
if "uplink_sent" not in st.session_state:
    st.session_state.uplink_sent = False

# ── Helpers ────────────────────────────────────────────────────
def trigger_bland_call(phone: str, data: dict) -> tuple:
    api_key = os.getenv("BLAND_API_KEY", "").strip()
    if not api_key:
        return False, "BLAND_API_KEY not configured."
    payload = {
        "phone_number": phone,
        "task": (f"You are an academic verification agent for ALIAS_X. "
                 f"Verify credentials for {data.get('name','Unknown')}, "
                 f"{data.get('degree','Unknown')} from "
                 f"{data.get('university','Unknown')}, year {data.get('year','Unknown')}."),
        "voice": "maya", "reduce_latency": True, "record": True, "max_duration": 4,
    }
    req = urllib.request.Request(
        url="https://api.bland.ai/v1/calls",
        data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "authorization": api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read().decode("utf-8"))
            return True, f"Voice call initiated. Call ID: {result.get('call_id','N/A')}"
    except urllib.error.HTTPError as e:
        return False, f"Bland AI HTTP {e.code}: {e.read().decode('utf-8','replace')[:200]}"
    except Exception as e:
        return False, f"Voice uplink error: {e}"

def send_verification_email(to_email: str, data: dict) -> tuple:
    smtp_user = os.getenv("SMTP_EMAIL", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()
    if not smtp_user or not smtp_pass:
        return False, "SMTP credentials not configured."
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[ALIAS_X] Verification Request — {data.get('name','Unknown')}"
    msg["From"]    = smtp_user
    msg["To"]      = to_email
    body = (f"Dear Registrar,\n\nALIAS_X verification request:\n\n"
            f"  Student   : {data.get('name','N/A')}\n"
            f"  University: {data.get('university','N/A')}\n"
            f"  Degree    : {data.get('degree','N/A')}\n"
            f"  Year      : {data.get('year','N/A')}\n\n"
            f"Ref: ALIAS_X-{int(time.time())}\n—\nALIAS_X Autonomous Verification Protocol")
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as s:
            s.login(smtp_user, smtp_pass)
            s.sendmail(smtp_user, to_email, msg.as_string())
        return True, f"Email dispatched to {to_email}"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP auth failed — check SMTP_EMAIL / SMTP_PASSWORD."
    except Exception as e:
        return False, f"Email uplink error: {e}"

# ── Header ─────────────────────────────────────────────────────
op = st.session_state.get("operator_id", "OPERATOR").upper()
col_hdr, col_op = st.columns([3, 1])
with col_hdr:
    st.markdown("""
<div style="margin-bottom:1.5rem;">
    <h1 style="font-family:'Ethnocentric',sans-serif;color:#ff003c;
               font-size:1.6rem;letter-spacing:.2em;margin:0;
               text-shadow:0 0 14px rgba(255,0,60,0.4);">
        ▲ ALIAS_X UPLINK TERMINAL
    </h1>
    <p style="color:#5a5a7a;font-size:.72rem;letter-spacing:.2em;margin:0;">
        AUTONOMOUS VERIFICATION PROTOCOL · ACADEMIC INTELLIGENCE UPLINK
    </p>
</div>""", unsafe_allow_html=True)
with col_op:
    st.markdown(f"""
<div style="text-align:right;padding-top:1rem;">
    <span style="color:#00ffaa;font-size:.65rem;font-family:'Courier New',monospace;">
        ● SESSION ACTIVE<br/><strong style="color:#fff;">{op}</strong>
    </span>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  SECTION 01 — CERTIFICATE UPLOAD
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-num">01 · CERTIFICATE UPLOAD</p>', unsafe_allow_html=True)
st.markdown('<p style="color:#5a5a7a;font-size:.78rem;">Upload certificate · Gemini Vision OCR auto-extracts intelligence.</p>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "UPLOAD CERTIFICATE SCANS",
    type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"],
    key="cert_uploader",
)

if uploaded_file is None:
    # Clear everything when file is removed
    st.session_state.ocr_data   = get_empty_data()
    st.session_state.ph         = ""
    st.session_state.uplink_sent = False
else:
    if st.button("⚡ INITIATE EXTRACTION PROTOCOL", use_container_width=True):
        suffix   = Path(uploaded_file.name).suffix or ".jpg"
        tmp_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        with st.spinner("🔍 Scanning document via ALIAS_X Vision..."):
            extracted = extract_details_from_certificate(tmp_path)
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        st.session_state.ocr_data    = extracted
        st.session_state.ph          = extracted.get("phone_number", "")
        st.session_state.uplink_sent = False
        st.success("✔ EXTRACTION COMPLETE — Review & validate below.")

# ══════════════════════════════════════════════════════════════
#  SECTION 02 — SUBJECT PROFILE
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-num">02 · SUBJECT PROFILE</p>', unsafe_allow_html=True)
st.markdown('<p style="color:#5a5a7a;font-size:.78rem;">AI-extracted data. Correct any field before uplink.</p>', unsafe_allow_html=True)

data = st.session_state.ocr_data

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.text_input("▸ FULL NAME",    value=data.get("name", ""),       disabled=True)
with col2:
    st.text_input("▸ UNIVERSITY",   value=data.get("university", ""), disabled=True)
with col3:
    st.text_input("▸ YEAR",         value=data.get("year", ""),        disabled=True)

st.text_input("▸ DEGREE PROGRAM",  value=data.get("degree", ""),      disabled=True)

# ══════════════════════════════════════════════════════════════
#  SECTION 03 — INTELLIGENCE UPLINK
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-num">03 · INTELLIGENCE UPLINK</p>', unsafe_allow_html=True)
st.markdown('<p style="color:#5a5a7a;font-size:.78rem;">Correct extracted contacts before uplink.</p>', unsafe_allow_html=True)

col4, col5 = st.columns(2)

with col4:
    edited_phone = st.text_input(
        "▸ REGISTRAR PHONE (DIGITS ONLY)",
        value=st.session_state.ph,
        placeholder="+91XXXXXXXXXX",
        key="input_phone",
    )
    voice_ready = False
    if edited_phone and edited_phone not in ["Unknown", "Manual Check"]:
        clean = edited_phone.lstrip("+")
        if clean.isdigit() and len(clean) >= 7:
            voice_ready = True
            st.session_state.ph = edited_phone
        else:
            st.error("⚠ Phone must contain digits only (min 7), optional leading +")

with col5:
    edited_email = st.text_input(
        "▸ REGISTRAR EMAIL",
        value=data.get("email", ""),
        placeholder="registrar@university.ac.in",
        key="input_email",
    )
    digital_ready = False
    if edited_email and edited_email not in ["Unknown", "Manual Check"]:
        valid_domains = (".ac", ".in", ".edu", ".college")
        if edited_email.lower().endswith(valid_domains):
            digital_ready = True
            st.session_state.ocr_data["email"] = edited_email
        else:
            st.error("⚠ Email must end in .ac · .in · .edu · .college")

# ══════════════════════════════════════════════════════════════
#  SECTION 04 — CHANNEL STATUS
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-num">04 · CHANNEL STATUS</p>', unsafe_allow_html=True)

col6, col7 = st.columns(2)
with col6:
    st.checkbox("VOICE CHANNEL · BLAND AI AGENT",  value=voice_ready,   disabled=True)
    st.markdown(
        f'<span class="{"channel-ready" if voice_ready else "channel-offline"}">'
        f'{"● READY — Voice uplink armed." if voice_ready else "○ OFFLINE — Provide valid phone."}'
        f'</span>', unsafe_allow_html=True)
with col7:
    st.checkbox("EMAIL CHANNEL · ENCRYPTED SMTP",  value=digital_ready, disabled=True)
    st.markdown(
        f'<span class="{"channel-ready" if digital_ready else "channel-offline"}">'
        f'{"● READY — Email channel armed." if digital_ready else "○ OFFLINE — Provide valid email."}'
        f'</span>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  SECTION 05 — EXECUTION PROTOCOL
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-num">05 · EXECUTION PROTOCOL</p>', unsafe_allow_html=True)

system_ready = voice_ready or digital_ready

if SIMULATION_MODE:
    st.warning(f"⚡ SIMULATION ACTIVE — Phone: `{TEST_PHONE or 'NOT SET'}` | Email: `{TEST_EMAIL or 'NOT SET'}`", icon="⚡")
if not system_ready:
    st.info("🔒 UPLINK LOCKED — Provide at least one valid contact channel.", icon="🔒")

if st.button("⚡ INITIATE ALIAS_X UPLINK",
             use_container_width=True,
             disabled=not system_ready or st.session_state.uplink_sent):

    st.session_state.uplink_sent = True
    target_phone = TEST_PHONE if SIMULATION_MODE else edited_phone
    target_email = TEST_EMAIL if SIMULATION_MODE else edited_email

    st.markdown("### 🌐 UPLINK STATUS LOG")

    if voice_ready:
        with st.status("Initiating Voice Protocol...", expanded=True) as status:
            st.write(f"[*] Locking target coordinates: {target_phone}")
            st.write("[*] Bridging connection to Bland AI Execution Agent...")
            ok, msg = trigger_bland_call(target_phone, data)
            st.write(f"[{'✔' if ok else '✖'}] {msg}")
            status.update(
                label="🎙️ VOICE UPLINK ESTABLISHED" if ok else "⚠ VOICE UPLINK FAILED",
                state="complete" if ok else "error", expanded=False)
        if ok:
            st.success("Verification Agent is currently on the line.")

    if digital_ready:
        with st.status("Initiating Digital Protocol...", expanded=True) as status:
            st.write(f"[*] Routing to {target_email}...")
            st.write("[*] Authenticating SMTP Server...")
            ok, msg = send_verification_email(target_email, data)
            st.write(f"[{'✔' if ok else '✖'}] {msg}")
            status.update(
                label="📧 DIGITAL UPLINK ESTABLISHED" if ok else "⚠ EMAIL UPLINK FAILED",
                state="complete" if ok else "error", expanded=False)
        if ok:
            st.success("Verification payload delivered to registrar.")

elif st.session_state.uplink_sent:
    st.success("✔ UPLINK ALREADY DISPATCHED this session. Upload new certificate to re-run.", icon="✔")

# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""<p style='text-align:center;color:#2a2a3a;font-size:.65rem;
font-family:"Courier New",monospace;letter-spacing:.2em;'>
ALIAS_X · AUTONOMOUS VERIFICATION PROTOCOL · ALL ACTIONS LOGGED</p>""",
unsafe_allow_html=True)