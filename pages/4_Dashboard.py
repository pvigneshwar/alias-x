"""
╔══════════════════════════════════════════════════════════════╗
║    ALIAS_X · Uplink Terminal Dashboard · pages/4_Dashboard.py ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import smtplib
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.ocr_engine import extract_details_from_certificate, get_empty_data
from modules.ai_caller  import make_real_ai_call, get_call_status, analyze_transcript_verdict
from modules.ui_helpers import inject_global_ui, get_page_icon, _load_image_b64

load_dotenv(ROOT / ".env")

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
.section-num     { color:#ff003c; font-family:"Ethnocentric",sans-serif;
                   font-size:.7rem; letter-spacing:.2em; }
.channel-ready   { color:#00ffaa; font-size:.72rem; }
.channel-offline { color:#ff003c; font-size:.72rem; }
.verdict-box     { padding:1.2rem; border-radius:4px; text-align:center;
                   margin:1rem 0; backdrop-filter:blur(6px); }
.verdict-confirmed { border:2px solid #00ffaa; background:rgba(0,255,170,0.08); }
.verdict-denied    { border:2px solid #ff003c; background:rgba(255,0,60,0.08); }
.verdict-inconclusive { border:2px solid #ffaa00; background:rgba(255,170,0,0.08); }
.verdict-label   { font-family:"Ethnocentric",sans-serif; font-size:1.4rem;
                   letter-spacing:.2em; margin:0; }
.transcript-box  { background:rgba(0,0,0,0.6); border:1px solid rgba(255,0,60,0.2);
                   border-radius:4px; padding:1rem; font-family:"Courier New",monospace;
                   font-size:.75rem; line-height:1.7; color:#ccccdd;
                   max-height:300px; overflow-y:auto; white-space:pre-wrap; }
</style>""", unsafe_allow_html=True)

# ── Auth Guard ─────────────────────────────────────────────────
if not st.session_state.get("logged_in", False):
    logo_b64 = _load_image_b64("aliasX_logo.png")
    logo_tag = (f'<img style="display:block;margin:0 auto;width:80px;border-radius:50%;" '
                f'src="data:image/png;base64,{logo_b64}" alt="AX"/>' if logo_b64 else "🔺")
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
for k, v in {
    "ocr_data":      get_empty_data(),
    "ph":            "",
    "uplink_sent":   False,
    "call_id":       None,
    "call_result":   None,
    "email_result":  None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ────────────────────────────────────────────────────
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
        return False, f"Email error: {e}"

def verdict_color(verdict: str) -> str:
    return {"CONFIRMED": "#00ffaa", "DENIED": "#ff003c"}.get(verdict, "#ffaa00")

def verdict_css_class(verdict: str) -> str:
    return {"CONFIRMED": "verdict-confirmed", "DENIED": "verdict-denied"}.get(
        verdict, "verdict-inconclusive")

# ── Header ─────────────────────────────────────────────────────
op = st.session_state.get("operator_id", "OPERATOR").upper()
col_hdr, col_op = st.columns([3, 1])
with col_hdr:
    st.markdown("""
<div style="margin-bottom:1.5rem;">
    <h1 style="font-family:'Ethnocentric',sans-serif;color:#ff003c;
               font-size:1.6rem;letter-spacing:.2em;margin:0;">▲ ALIAS_X UPLINK TERMINAL</h1>
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
    st.session_state.ocr_data    = get_empty_data()
    st.session_state.ph          = ""
    st.session_state.uplink_sent = False
    st.session_state.call_id     = None
    st.session_state.call_result = None
    st.session_state.email_result = None
else:
    if st.button("⚡ INITIATE EXTRACTION PROTOCOL", use_container_width=True):
        suffix = Path(uploaded_file.name).suffix or ".jpg"
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
        st.session_state.call_id     = None
        st.session_state.call_result = None
        st.session_state.email_result = None
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
    st.text_input("▸ YEAR",         value=data.get("year", ""),       disabled=True)
st.text_input("▸ DEGREE PROGRAM",   value=data.get("degree", ""),     disabled=True)

# ══════════════════════════════════════════════════════════════
#  SECTION 03 — INTELLIGENCE UPLINK CONTACTS
# ══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-num">03 · INTELLIGENCE UPLINK</p>', unsafe_allow_html=True)
st.markdown('<p style="color:#5a5a7a;font-size:.78rem;">Correct extracted contacts before uplink.</p>', unsafe_allow_html=True)

col4, col5 = st.columns(2)
with col4:
    edited_phone = st.text_input("▸ REGISTRAR PHONE",
                                 value=st.session_state.ph,
                                 placeholder="+91XXXXXXXXXX", key="input_phone")
    voice_ready = False
    if edited_phone and edited_phone not in ("Unknown", "Manual Check"):
        clean = edited_phone.lstrip("+")
        if clean.isdigit() and len(clean) >= 7:
            voice_ready = True
            st.session_state.ph = edited_phone
        else:
            st.error("⚠ Phone must be digits only (min 7), optional leading +")

with col5:
    edited_email = st.text_input("▸ REGISTRAR EMAIL",
                                 value=data.get("email", ""),
                                 placeholder="registrar@university.ac.in",
                                 key="input_email")
    digital_ready = False
    if edited_email and edited_email not in ("Unknown", "Manual Check"):
        if edited_email.lower().endswith((".ac", ".in", ".edu", ".college")):
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
    st.checkbox("VOICE CHANNEL · BLAND AI AGENT", value=voice_ready, disabled=True)
    st.markdown(f'<span class="{"channel-ready" if voice_ready else "channel-offline"}">'
                f'{"● READY — Voice uplink armed." if voice_ready else "○ OFFLINE — Provide valid phone."}'
                f'</span>', unsafe_allow_html=True)
with col7:
    st.checkbox("EMAIL CHANNEL · ENCRYPTED SMTP", value=digital_ready, disabled=True)
    st.markdown(f'<span class="{"channel-ready" if digital_ready else "channel-offline"}">'
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

    # Voice call
    if voice_ready:
        with st.status("📡 Initiating voice uplink...", expanded=True) as status:
            st.write(f"▸ Dialling → `{target_phone}`")
            st.write("▸ Connecting to Bland AI execution agent...")
            result = make_real_ai_call(target_phone, data)
            if result["success"]:
                st.session_state.call_id = result["call_id"]
                st.write(f"▸ ✔ Call dispatched. ID: `{result['call_id']}`")
                st.write("▸ Call is live — transcript will be available after completion.")
                status.update(label="🎙️ VOICE UPLINK ESTABLISHED — Awaiting completion",
                              state="complete", expanded=False)
            else:
                st.write(f"▸ ✖ {result['error']}")
                status.update(label="⚠ VOICE UPLINK FAILED", state="error", expanded=False)
            st.session_state.call_result = result

    # Email
    if digital_ready:
        with st.status("📧 Initiating email uplink...", expanded=True) as status:
            st.write(f"▸ Dispatching to → `{target_email}`")
            ok, msg = send_verification_email(target_email, data)
            st.write(f"▸ {'✔' if ok else '✖'} {msg}")
            status.update(
                label="📧 EMAIL UPLINK ESTABLISHED" if ok else "⚠ EMAIL UPLINK FAILED",
                state="complete" if ok else "error", expanded=False)
            st.session_state.email_result = {"success": ok, "message": msg}

elif st.session_state.uplink_sent:
    st.success("✔ UPLINK DISPATCHED — See results below.", icon="✔")

# ══════════════════════════════════════════════════════════════
#  SECTION 06 — CALL RESULTS & TRANSCRIPT
# ══════════════════════════════════════════════════════════════
if st.session_state.call_id:
    st.markdown("---")
    st.markdown('<p class="section-num">06 · VERIFICATION RESULT</p>', unsafe_allow_html=True)

    call_id = st.session_state.call_id

    col_refresh, col_status = st.columns([1, 3])
    with col_refresh:
        check_btn = st.button("🔄 CHECK CALL STATUS", use_container_width=True)
    with col_status:
        st.markdown(f'<p style="color:#5a5a7a;font-size:.78rem;padding-top:.7rem;">'
                    f'Call ID: <code style="color:#ff003c;">{call_id}</code> — '
                    f'Click "CHECK CALL STATUS" to fetch transcript & verdict.</p>',
                    unsafe_allow_html=True)

    if check_btn:
        with st.spinner("📡 Fetching call data from Bland AI..."):
            call_data = get_call_status(call_id)

        status_val = call_data.get("status", "unknown")
        completed  = call_data.get("completed", False)
        transcript = call_data.get("transcript", "")
        recording  = call_data.get("recording_url", "")

        st.markdown(f'<p style="color:#5a5a7a;font-size:.78rem;">Call Status: '
                    f'<strong style="color:#fff;">{status_val.upper()}</strong></p>',
                    unsafe_allow_html=True)

        if not completed:
            st.warning("⏳ Call is still in progress. Check again in a moment.", icon="⏳")

        else:
            # Show transcript
            if transcript:
                st.markdown('<p class="section-num" style="font-size:.65rem;">CALL TRANSCRIPT</p>',
                            unsafe_allow_html=True)
                st.markdown(f'<div class="transcript-box">{transcript}</div>',
                            unsafe_allow_html=True)
            else:
                st.info("No transcript available (voicemail or no answer).")

            # Recording link
            if recording:
                st.markdown(f'<p style="font-size:.75rem;margin-top:.5rem;">'
                            f'🎙️ <a href="{recording}" target="_blank" '
                            f'style="color:#ff003c;">Listen to Recording</a></p>',
                            unsafe_allow_html=True)

            # Gemini verdict
            if transcript:
                with st.spinner("🧠 Analysing transcript via Gemini..."):
                    verdict_data = analyze_transcript_verdict(transcript, data)

                verdict    = verdict_data.get("verdict", "INCONCLUSIVE")
                reason     = verdict_data.get("reason", "")
                confidence = verdict_data.get("confidence", 0)
                color      = verdict_color(verdict)
                css_class  = verdict_css_class(verdict)

                verdict_icon = {"CONFIRMED": "✅", "DENIED": "❌"}.get(verdict, "⚠️")

                st.markdown(f"""
<div class="verdict-box {css_class}">
    <p class="verdict-label" style="color:{color};">{verdict_icon} {verdict}</p>
    <p style="color:#aaaacc;font-size:.8rem;margin:.5rem 0 0;">{reason}</p>
    <p style="color:#5a5a7a;font-size:.7rem;margin:.3rem 0 0;">
        Confidence: <strong style="color:{color};">{confidence}%</strong>
    </p>
</div>""", unsafe_allow_html=True)

            else:
                # No transcript — show call outcome directly
                verdict_map = {
                    "no-answer": ("INCONCLUSIVE", "#ffaa00", "⚠️", "No answer — try email fallback."),
                    "voicemail": ("INCONCLUSIVE", "#ffaa00", "⚠️", "Reached voicemail."),
                    "busy":      ("INCONCLUSIVE", "#ffaa00", "⚠️", "Line was busy."),
                    "failed":    ("FAILED",        "#ff003c", "❌", "Call failed to connect."),
                }
                v, c, icon, reason = verdict_map.get(
                    status_val, ("INCONCLUSIVE", "#ffaa00", "⚠️", "No response obtained."))
                st.markdown(f"""
<div class="verdict-box verdict-inconclusive">
    <p class="verdict-label" style="color:{c};">{icon} {v}</p>
    <p style="color:#aaaacc;font-size:.8rem;margin:.5rem 0 0;">{reason}</p>
</div>""", unsafe_allow_html=True)

# ── Email Result ───────────────────────────────────────────────
if st.session_state.email_result:
    res = st.session_state.email_result
    if res["success"]:
        st.success(f"📧 {res['message']}", icon="📧")
    else:
        st.error(f"📧 {res['message']}")

# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""<p style='text-align:center;color:#2a2a3a;font-size:.65rem;
font-family:"Courier New",monospace;letter-spacing:.2em;'>
ALIAS_X · AUTONOMOUS VERIFICATION PROTOCOL · ALL ACTIONS LOGGED</p>""",
unsafe_allow_html=True)