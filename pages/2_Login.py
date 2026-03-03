"""
╔══════════════════════════════════════════════════════════════╗
║          ALIAS_X · Login · pages/2_Login.py                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import hashlib
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.ui_helpers import inject_global_ui, get_page_icon, _load_image_b64

# ── Page Config ────────────────────────────────────────────────
st.set_page_config(
    page_title="ALIAS_X · Login",
    page_icon=get_page_icon(),
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Inject global UI ──────────────────────────────────────────
inject_global_ui()

# ── Page-level styles ─────────────────────────────────────────
st.markdown("""<style>
.auth-wrap         { max-width:420px; margin:0 auto; padding:1rem; }
.auth-logo-img     { display:block; margin:0 auto .8rem; width:90px; height:90px;
                     border-radius:50%; border:2px solid rgba(255,0,60,0.55);
                     box-shadow:0 0 20px rgba(255,0,60,0.35); }
.auth-title        { text-align:center; font-family:"Ethnocentric",sans-serif;
                     font-size:1.6rem; color:#ff003c; letter-spacing:.2em;
                     margin:0; text-shadow:0 0 14px rgba(255,0,60,0.45); }
.auth-sub          { text-align:center; color:#5a5a8a; font-size:.64rem;
                     letter-spacing:.3em; margin:.3rem 0 1.6rem; }
.auth-panel        { background:rgba(8,8,15,0.90); border:1px solid rgba(255,0,60,0.3);
                     border-radius:4px; padding:2rem 2.2rem 1.6rem;
                     backdrop-filter:blur(8px); }
.auth-panel h3     { font-family:"Ethnocentric",sans-serif; color:#ff003c;
                     font-size:.82rem; letter-spacing:.2em; margin:0 0 1.2rem;
                     text-align:center; }
.auth-footer-link  { text-align:center; color:#5a5a8a; font-size:.72rem;
                     margin-top:1rem; }
.auth-footer-link a{ color:#ff003c; text-decoration:none; }
.auth-footer-link a:hover { text-decoration:underline; }
.field-label       { color:#8a8aaa; font-size:.72rem; letter-spacing:.08em;
                     margin-bottom:.3rem; }
.demo-hint         { background:rgba(255,0,60,0.06); border:1px solid rgba(255,0,60,0.2);
                     border-radius:3px; padding:.7rem .9rem; margin-top:1.2rem;
                     color:#7a7aaa; font-size:.68rem; line-height:1.6; }
.demo-hint strong  { color:#ff003c; }
</style>""", unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in   = False
if "operator_id" not in st.session_state:
    st.session_state.operator_id = None

# ── Already logged in ─────────────────────────────────────────
if st.session_state.logged_in:
    logo_b64 = _load_image_b64("aliasX_logo.png")
    logo_tag = (f'<img class="auth-logo-img" src="data:image/jpeg;base64,{logo_b64}" alt="AX"/>'
                if logo_b64 else "🔺")
    st.markdown(f"""
<div class="auth-wrap">
    {logo_tag}
    <h1 class="auth-title">ALIAS_X</h1>
    <p class="auth-sub">SESSION ACTIVE</p>
    <div class="auth-panel">
        <h3>✔ ACCESS GRANTED</h3>
        <p style="color:#00ffaa;text-align:center;font-size:.82rem;margin:.4rem 0;">
            Operator: <strong>{st.session_state.operator_id}</strong>
        </p>
        <p style="color:#7a7a9a;text-align:center;font-size:.75rem;margin:.6rem 0 1.2rem;">
            Your session is active. Navigate to the Dashboard to begin verification.
        </p>
    </div>
</div>""", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("⚡ GO TO DASHBOARD", use_container_width=True):
            st.switch_page("pages/4_Dashboard.py")
    with col_b:
        if st.button("⬡ LOGOUT", use_container_width=True):
            st.session_state.logged_in   = False
            st.session_state.operator_id = None
            st.rerun()
    st.stop()

# ── Demo credentials (hashed) ──────────────────────────────────
_DEMO_USERS = {
    "operator": hashlib.sha256("alias2024".encode()).hexdigest(),
    "admin":    hashlib.sha256("adminX99".encode()).hexdigest(),
}

def _check_credentials(username: str, password: str) -> bool:
    h = hashlib.sha256(password.encode()).hexdigest()
    return _DEMO_USERS.get(username.strip().lower()) == h

# ── Login form ─────────────────────────────────────────────────
logo_b64 = _load_image_b64("aliasX_logo.png")
logo_tag  = (f'<img class="auth-logo-img" src="data:image/jpeg;base64,{logo_b64}" alt="AX"/>'
             if logo_b64 else "🔺")

st.markdown(f"""
<div class="auth-wrap">
    {logo_tag}
    <h1 class="auth-title">ALIAS_X</h1>
    <p class="auth-sub">OPERATOR AUTHENTICATION PORTAL</p>
</div>
""", unsafe_allow_html=True)

# Panel wrapper
st.markdown('<div class="auth-panel"><h3>⬡ OPERATOR LOGIN</h3>', unsafe_allow_html=True)

with st.form("login_form", clear_on_submit=False):
    st.markdown('<p class="field-label">▸ OPERATOR ID</p>', unsafe_allow_html=True)
    username = st.text_input(
        label       = "Operator ID",
        placeholder = "Enter operator ID",
        label_visibility = "collapsed",
    )
    st.markdown('<p class="field-label">▸ ACCESS CODE</p>', unsafe_allow_html=True)
    password = st.text_input(
        label       = "Access Code",
        type        = "password",
        placeholder = "Enter access code",
        label_visibility = "collapsed",
    )
    submitted = st.form_submit_button(
        "⚡ AUTHENTICATE",
        use_container_width=True,
    )

if submitted:
    if not username or not password:
        st.error("⚠ AUTHENTICATION FAILED — Operator ID and Access Code are required.")
    elif _check_credentials(username, password):
        st.session_state.logged_in   = True
        st.session_state.operator_id = username.strip().lower()
        st.success(f"✔ ACCESS GRANTED — Welcome, {st.session_state.operator_id.upper()}")
        st.balloons()
        st.rerun()
    else:
        st.error("⚠ AUTHENTICATION FAILED — Invalid credentials. Access denied.")

st.markdown('</div>', unsafe_allow_html=True)  # close auth-panel

# ── Demo hint ─────────────────────────────────────────────────
st.markdown("""
<div class="auth-wrap">
    <div class="demo-hint">
        <strong>DEMO CREDENTIALS</strong><br/>
        Operator ID: <strong>operator</strong> · Access Code: <strong>alias2024</strong><br/>
        Admin ID: <strong>admin</strong> · Access Code: <strong>adminX99</strong>
    </div>
    <p class="auth-footer-link">
        No account? <a href="/3_Signup">Create operator profile →</a>
    </p>
</div>
""", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────
st.markdown("""<br/><p style='text-align:center;color:#2a2a3a;font-size:.6rem;
font-family:"Courier New",monospace;letter-spacing:.2em;'>
ALIAS_X · SECURE AUTHENTICATION LAYER · ALL ACCESS ATTEMPTS LOGGED</p>""",
unsafe_allow_html=True)
