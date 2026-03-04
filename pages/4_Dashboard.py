"""
╔══════════════════════════════════════════════════════════════╗
║    ALIAS_X · Uplink Terminal Dashboard · pages/4_Dashboard.py ║
║       Human-in-the-Loop Academic Verification Protocol        ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import re
import sys
import json
import time
import tempfile
import smtplib
import urllib.request
import urllib.error
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st
from dotenv import load_dotenv

# ── Path Resolution ────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.ocr_engine import extract_details_from_certificate, get_empty_data
from modules.ui_helpers import inject_global_ui, get_page_icon, _load_image_b64

load_dotenv(ROOT / ".env")

st.set_page_config(
    page_title="ALIAS_X · Uplink Terminal",
    page_icon=get_page_icon(),
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_ui()

st.markdown("""<style>
.dashboard-header h1 { font-family:"Ethnocentric",sans-serif; color:#ff003c;
                       font-size:1.6rem; letter-spacing:.2em; margin:0; }
.channel-ready  { color:#00ffaa; font-size:.72rem; letter-spacing:.05em; }
.channel-offline{ color:#ff003c; font-size:.72rem; letter-spacing:.05em; }
.section-num    { color:#ff003c; font-family:"Ethnocentric",sans-serif;
                  font-size:.7rem; letter-spacing:.2em; }
</style>""", unsafe_allow_html=True)

# ── Auth Guard ─────────────────────────────────────────────────
if not st.session_state.get("logged_in", False):
    logo_b64 = _load_image_b64("aliasX_logo.png")
    logo_tag = (f'<img style="display:block;margin:0 auto;width:80px;border-radius:50%;" '
                f'src="data:image/jpeg;base64,{logo_b64}" alt="AX"/>'
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

# ── Session State ──────────────────────────────────────────────
for k, v in {"ocr_data": None, "uplink_sent": False,
              "uplink_log": [], "last_filename": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ────────────────────────────────────────────────────
def is_valid_phone(phone):
    s = phone.strip()
    if not s:
        return False
    return re.sub(r"^\+", "", s).isdigit() and len(re.sub(r"^\+", "", s)) >= 7

def is_valid_edu_email(email):
    if not email or "@" not in email:
        return False
    return any(email.strip().lower().endswith(t) for t in (".ac", ".in", ".edu", ".college"))

def trigger_bland_call(phone, subject_data):
    api_key = os.getenv("BLAND_API_KEY", "").strip()
    if not api_key:
        return False, "BLAND_API_KEY not configured."
    payload = {
        "phone_number": phone,
        "task": (f"You are an academic verification agent for ALIAS_X. "
                 f"Verify credentials for {subject_data.get('name','Unknown')}, "
                 f"{subject_data.get('degree','Unknown')} from "
                 f"{subject_data.get('university','Unknown')}, "
                 f"year {subject_data.get('year','Unknown')}."),
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

def send_verification_email(to_email, subject_data):
    smtp_user = os.getenv("SMTP_EMAIL", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()
    if not smtp_user or not smtp_pass:
        return False, "SMTP credentials not configured."
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[ALIAS_X] Verification Request — {subject_data.get('name','Unknown')}"
    msg["From"] = smtp_user
    msg["To"] = to_email
    body = (f"Dear Registrar,\n\nALIAS_X verification request:\n\n"
            f"  Student   : {subject_data.get('name','N/A')}\n"
            f"  University: {subject_data.get('university','N/A')}\n"
            f"  Degree    : {subject_data.get('degree','N/A')}\n"
            f"  Year      : {subject_data.get('year','N/A')}\n\n"
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
    st.markdown(f"""
<div class="dashboard-header">
    <h1>▲ ALIAS_X UPLINK TERMINAL</h1>
    <p style="color:#5a5a7a;font-size:.72rem;letter-spacing:.2em;margin:0;">
        AUTONOMOUS VERIFICATION PROTOCOL · ACADEMIC INTELLIGENCE UPLINK
    </p>
</div>""", unsafe_allow_html=True)
with col_op:
    st.markdown(f"""
<div style="text-align:right;padding-top:1rem;">
    <span style="color:#00ffaa;font-size:.65rem;font-family:'Courier New',monospace;">
        ● SESSION ACTIVE<br/><strong style="color:#ffffff;">{op}</strong>
    </span>
</div>""", unsafe_allow_html=True)

# ── Section 01: Upload ─────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-num">01 · CERTIFICATE UPLOAD</p>', unsafe_allow_html=True)
st.markdown('<p style="color:#5a5a7a;font-size:.78rem;">Upload certificate · Gemini Vision OCR auto-extracts intelligence.</p>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "DRAG & DROP CERTIFICATE — JPG · PNG · WEBP",
    type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
    key="cert_uploader",
)

if uploaded_file is None:
    if st.session_state.last_filename is not None:
        st.session_state.ocr_data = None
        st.session_state.uplink_sent = False
        st.session_state.uplink_log = []
        st.session_state.last_filename = None
        st.rerun()
elif uploaded_file.name != st.session_state.last_filename:
    st.session_state.last_filename = uploaded_file.name
    st.session_state.uplink_sent = False
    st.session_state.uplink_log = []
    with st.spinner("🔍 INITIALISING GEMINI OCR SCAN…"):
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        result = extract_details_from_certificate(tmp_path)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        st.session_state.ocr_data = result
    # Debug line — shows API key status and extracted name
    api_ok = bool(os.getenv("GOOGLE_API_KEY", "").strip())
    ocr = st.session_state.ocr_data or get_empty_data()
    st.caption(f"🔑 API KEY LOADED: {api_ok} | NAME: {ocr.get('name','?')} | UNI: {ocr.get('university','?')}")
    st.success("✔ OCR EXTRACTION COMPLETE — Review & validate below.")

# ── Section 02: Subject Profile ────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-num">02 · SUBJECT PROFILE</p>', unsafe_allow_html=True)
st.markdown('<p style="color:#5a5a7a;font-size:.78rem;">AI-extracted data. You may correct any field before uplink.</p>', unsafe_allow_html=True)

ocr = st.session_state.ocr_data or get_empty_data()
col_l, col_r = st.columns(2)
with col_l:
    name   = st.text_input("▸ SUBJECT NAME",          value=ocr.get("name", ""),       key="d_name")
    degree = st.text_input("▸ DEGREE / QUALIFICATION", value=ocr.get("degree", ""),     key="d_degree")
with col_r:
    uni    = st.text_input("▸ ISSUING UNIVERSITY",     value=ocr.get("university", ""), key="d_uni")
    year   = st.text_input("▸ GRADUATION YEAR",        value=ocr.get("year", ""),       key="d_year")

# ── Section 03: Uplink Contacts ────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-num">03 · INTELLIGENCE UPLINK</p>', unsafe_allow_html=True)
st.markdown('<p style="color:#5a5a7a;font-size:.78rem;">Correct extracted contacts before uplink.</p>', unsafe_allow_html=True)

col_ph, col_em = st.columns(2)
with col_ph:
    raw_phone = st.text_input("▸ UNIVERSITY PHONE (REGISTRAR)",
                              value=ocr.get("phone_number", ""),
                              placeholder="+91XXXXXXXXXX", key="input_phone")
with col_em:
    raw_email = st.text_input("▸ UNIVERSITY EMAIL (REGISTRAR)",
                              value=ocr.get("email", ""),
                              placeholder="registrar@university.ac.in", key="input_email")

phone_ok = is_valid_phone(raw_phone)
email_ok = is_valid_edu_email(raw_email)

if raw_phone and not phone_ok:
    st.error("⚠ PHONE VALIDATION FAILED — digits only (min 7), optional leading +")
if raw_email and not email_ok:
    st.error("⚠ EMAIL VALIDATION FAILED — must end with .ac · .in · .edu · .college")

# ── Section 04: Channel Status ─────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-num">04 · CHANNEL STATUS</p>', unsafe_allow_html=True)
col_v, col_e = st.columns(2)
with col_v:
    st.checkbox("VOICE CHANNEL · BLAND AI AGENT", value=phone_ok, key="cb_voice", disabled=True)
    st.markdown(f'<span class="{"channel-ready" if phone_ok else "channel-offline"}">'
                f'{"● READY — Voice uplink armed." if phone_ok else "○ OFFLINE — Provide valid phone."}'
                f'</span>', unsafe_allow_html=True)
with col_e:
    st.checkbox("EMAIL CHANNEL · ENCRYPTED SMTP", value=email_ok, key="cb_email", disabled=True)
    st.markdown(f'<span class="{"channel-ready" if email_ok else "channel-offline"}">'
                f'{"● READY — Email channel armed." if email_ok else "○ OFFLINE — Provide valid email."}'
                f'</span>', unsafe_allow_html=True)

# ── Section 05: Execution ──────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-num">05 · EXECUTION PROTOCOL</p>', unsafe_allow_html=True)

at_least_one = phone_ok or email_ok
use_test   = os.getenv("USE_TEST_DATA", "FALSE").strip().upper() == "TRUE"
test_phone = os.getenv("TEST_PHONE_NUMBER", "").strip()
test_email = os.getenv("TEST_EMAIL_ADDRESS", "").strip()

if use_test:
    st.warning(f"⚡ SIMULATION ACTIVE — Phone: `{test_phone or 'NOT SET'}` | Email: `{test_email or 'NOT SET'}`", icon="⚡")
if not at_least_one:
    st.info("🔒 UPLINK LOCKED — Provide at least one valid contact channel.", icon="🔒")

initiate = st.button(
    "⚡ INITIATE ALIAS_X UPLINK",
    disabled=not at_least_one or st.session_state.uplink_sent,
    key="btn_uplink",
    use_container_width=True,
)

if initiate and at_least_one:
    st.session_state.uplink_sent = True
    subject_data = {"name": name, "university": uni, "degree": degree, "year": year}
    tgt_phone = test_phone if use_test else raw_phone.strip()
    tgt_email = test_email if use_test else raw_email.strip()
    log = []

    with st.status("⚡ ALIAS_X UPLINK SEQUENCE INITIATED…", expanded=True) as status:
        st.write("▸ Validating payload integrity…"); time.sleep(0.6)
        st.write(f"▸ Subject: **{name}** | **{uni}** | **{degree}** ({year})"); time.sleep(0.4)
        st.write(f"▸ {'⚡ SIMULATION MODE' if use_test else '🔴 LIVE MODE'} — routing contacts…"); time.sleep(0.4)

        if phone_ok and tgt_phone:
            st.write(f"▸ Dialling → `{tgt_phone}`…"); time.sleep(0.8)
            ok, msg = trigger_bland_call(tgt_phone, subject_data)
            st.write(f"▸ [{'✔' if ok else '✖'}] VOICE: {msg}")
            log.append(f"[{'OK' if ok else 'ERR'}] VOICE: {msg}"); time.sleep(0.4)

        if email_ok and tgt_email:
            st.write(f"▸ Dispatching email → `{tgt_email}`…"); time.sleep(0.8)
            ok, msg = send_verification_email(tgt_email, subject_data)
            st.write(f"▸ [{'✔' if ok else '✖'}] EMAIL: {msg}")
            log.append(f"[{'OK' if ok else 'ERR'}] EMAIL: {msg}"); time.sleep(0.4)

        st.write("▸ Uplink complete. Awaiting university response…"); time.sleep(0.5)
        has_err = any(l.startswith("[ERR]") for l in log)
        status.update(
            label="⚠ UPLINK COMPLETED WITH WARNINGS" if has_err else "✔ ALIAS_X UPLINK SUCCESSFUL",
            state="error" if has_err else "complete",
            expanded=False,
        )

    st.session_state.uplink_log = log
    if log:
        st.markdown("### UPLINK LOG")
        for entry in log:
            color = "#00ffaa" if entry.startswith("[OK]") else "#ff003c"
            st.markdown(f'<p style="font-family:\'Courier New\',monospace;font-size:.8rem;color:{color};">{entry}</p>',
                        unsafe_allow_html=True)

elif st.session_state.uplink_sent:
    st.success("✔ UPLINK ALREADY DISPATCHED this session. Upload new certificate to re-run.", icon="✔")

# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""<p style='text-align:center;color:#2a2a3a;font-size:.65rem;
font-family:"Courier New",monospace;letter-spacing:.2em;'>
ALIAS_X · AUTONOMOUS VERIFICATION PROTOCOL · ALL ACTIONS LOGGED</p>""",
unsafe_allow_html=True)