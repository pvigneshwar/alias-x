"""
╔══════════════════════════════════════════════════════════════╗
║          ALIAS_X · Signup · pages/3_Signup.py                ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import re
import hashlib
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.ui_helpers import inject_global_ui, get_page_icon, _load_image_b64

# ── Page Config ────────────────────────────────────────────────
st.set_page_config(
    page_title="ALIAS_X · Signup",
    page_icon=get_page_icon(),
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Inject global UI ──────────────────────────────────────────
inject_global_ui()

# ── Page-level styles ─────────────────────────────────────────
st.markdown("""<style>
.auth-wrap          { max-width:440px; margin:0 auto; padding:1rem; }
.auth-logo-img      { display:block; margin:0 auto .8rem; width:90px; height:90px;
                      border-radius:50%; border:2px solid rgba(255,0,60,0.55);
                      box-shadow:0 0 20px rgba(255,0,60,0.35); }
.auth-title         { text-align:center; font-family:"Ethnocentric",sans-serif;
                      font-size:1.6rem; color:#ff003c; letter-spacing:.2em;
                      margin:0; text-shadow:0 0 14px rgba(255,0,60,0.45); }
.auth-sub           { text-align:center; color:#5a5a8a; font-size:.64rem;
                      letter-spacing:.3em; margin:.3rem 0 1.6rem; }
.auth-panel         { background:rgba(8,8,15,0.90); border:1px solid rgba(255,0,60,0.3);
                      border-radius:4px; padding:2rem 2.2rem 1.6rem;
                      backdrop-filter:blur(8px); }
.auth-panel h3      { font-family:"Ethnocentric",sans-serif; color:#ff003c;
                      font-size:.82rem; letter-spacing:.2em; margin:0 0 1.2rem;
                      text-align:center; }
.field-label        { color:#8a8aaa; font-size:.72rem; letter-spacing:.08em;
                      margin-bottom:.3rem; }
.policy-note        { background:rgba(0,255,170,0.05); border:1px solid rgba(0,255,170,0.2);
                      border-radius:3px; padding:.7rem .9rem; margin:.8rem 0;
                      color:#6a9a8a; font-size:.68rem; line-height:1.6; }
.policy-note strong { color:#00ffaa; }
.auth-footer-link   { text-align:center; color:#5a5a8a; font-size:.72rem;
                      margin-top:1rem; }
.auth-footer-link a { color:#ff003c; text-decoration:none; }
.auth-footer-link a:hover { text-decoration:underline; }
.pw-rule            { color:#6a6a8a; font-size:.67rem; margin:.1rem 0; }
.pw-rule.ok         { color:#00ffaa; }
.pw-rule.fail       { color:#ff003c; }
</style>""", unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────
if "operator_registry" not in st.session_state:
    st.session_state.operator_registry = {}   # {username: hashed_pw}
if "signup_success" not in st.session_state:
    st.session_state.signup_success = False

# ── Validation helpers ─────────────────────────────────────────
def _valid_username(u: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_]{4,20}$', u))

def _pw_rules(pw: str) -> dict:
    return {
        "min_8":    len(pw) >= 8,
        "upper":    any(c.isupper() for c in pw),
        "digit":    any(c.isdigit() for c in pw),
        "special":  any(c in "!@#$%^&*_-+" for c in pw),
    }

# ── Logo & header ─────────────────────────────────────────────
logo_b64 = _load_image_b64("aliasX_logo.png")
logo_tag  = (f'<img class="auth-logo-img" src="data:image/jpeg;base64,{logo_b64}" alt="AX"/>'
             if logo_b64 else "🔺")

st.markdown(f"""
<div class="auth-wrap">
    {logo_tag}
    <h1 class="auth-title">ALIAS_X</h1>
    <p class="auth-sub">OPERATOR REGISTRATION PORTAL</p>
</div>
""", unsafe_allow_html=True)

# ── Success state ─────────────────────────────────────────────
if st.session_state.signup_success:
    st.markdown("""
<div class="auth-wrap">
    <div class="auth-panel">
        <h3>✔ OPERATOR PROFILE CREATED</h3>
        <p style="color:#00ffaa;text-align:center;font-size:.82rem;margin:.4rem 0;">
            Registration successful. Proceed to authentication.
        </p>
    </div>
</div>""", unsafe_allow_html=True)
    if st.button("⚡ GO TO LOGIN", use_container_width=True):
        st.session_state.signup_success = False
        st.switch_page("pages/2_Login.py")
    st.stop()

# ── Signup form ───────────────────────────────────────────────
st.markdown('<div class="auth-panel"><h3>⬡ CREATE OPERATOR PROFILE</h3>', unsafe_allow_html=True)

with st.form("signup_form", clear_on_submit=False):
    st.markdown('<p class="field-label">▸ FULL NAME</p>', unsafe_allow_html=True)
    full_name = st.text_input("Full Name", placeholder="Enter your full name",
                              label_visibility="collapsed")

    st.markdown('<p class="field-label">▸ EMAIL ADDRESS</p>', unsafe_allow_html=True)
    email = st.text_input("Email", placeholder="operator@domain.com",
                          label_visibility="collapsed")

    st.markdown('<p class="field-label">▸ OPERATOR ID  (4–20 chars, letters/digits/underscore)</p>',
                unsafe_allow_html=True)
    username = st.text_input("Operator ID", placeholder="e.g. op_hawk99",
                             label_visibility="collapsed")

    st.markdown('<p class="field-label">▸ ACCESS CODE</p>', unsafe_allow_html=True)
    password = st.text_input("Access Code", type="password",
                             placeholder="Create access code",
                             label_visibility="collapsed")

    st.markdown('<p class="field-label">▸ CONFIRM ACCESS CODE</p>', unsafe_allow_html=True)
    confirm_pw = st.text_input("Confirm Access Code", type="password",
                               placeholder="Repeat access code",
                               label_visibility="collapsed")

    # Live password-rule preview
    if password:
        rules = _pw_rules(password)
        rule_labels = {
            "min_8":   "Minimum 8 characters",
            "upper":   "At least one uppercase letter",
            "digit":   "At least one number",
            "special": "At least one special character (!@#$%^&*_-+)",
        }
        rules_html = "".join(
            f'<p class="pw-rule {"ok" if ok else "fail"}">'
            f'{"✔" if ok else "✖"} {lbl}</p>'
            for key, lbl in rule_labels.items()
            for ok in [rules[key]]
        )
        st.markdown(rules_html, unsafe_allow_html=True)

    agreed = st.checkbox("I acknowledge this is a demo operator profile for ALIAS_X testing.")

    submitted = st.form_submit_button("⚡ CREATE OPERATOR PROFILE", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)  # close auth-panel

# ── Process signup ────────────────────────────────────────────
if submitted:
    errors = []

    if not full_name.strip():
        errors.append("Full name is required.")
    if not email.strip() or "@" not in email:
        errors.append("A valid email address is required.")
    if not _valid_username(username):
        errors.append("Operator ID must be 4–20 chars (letters, digits, underscore).")
    elif username.lower() in st.session_state.operator_registry:
        errors.append(f"Operator ID '{username}' is already taken.")

    pw_check = _pw_rules(password)
    if not all(pw_check.values()):
        errors.append("Access code does not meet all requirements.")
    elif password != confirm_pw:
        errors.append("Access codes do not match.")

    if not agreed:
        errors.append("You must acknowledge the demo notice.")

    if errors:
        for e in errors:
            st.error(f"⚠ {e}")
    else:
        hashed = hashlib.sha256(password.encode()).hexdigest()
        st.session_state.operator_registry[username.lower()] = hashed
        st.session_state.signup_success = True
        st.rerun()

# ── Policy note ───────────────────────────────────────────────
st.markdown("""
<div class="auth-wrap">
    <div class="policy-note">
        <strong>DEMO ENVIRONMENT NOTICE</strong><br/>
        Operator profiles are stored in session memory only and are not
        persisted between restarts. For production deployments, connect
        to a secure credential store.
    </div>
    <p class="auth-footer-link">
        Already registered? <a href="/2_Login">Authenticate here →</a>
    </p>
</div>
""", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────
st.markdown("""<br/><p style='text-align:center;color:#2a2a3a;font-size:.6rem;
font-family:"Courier New",monospace;letter-spacing:.2em;'>
ALIAS_X · SECURE REGISTRATION LAYER · ALL PROFILES EXPIRE ON SESSION END</p>""",
unsafe_allow_html=True)
