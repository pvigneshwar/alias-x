"""
╔══════════════════════════════════════════════════════════════╗
║           ALIAS_X — Autonomous Verification Protocol         ║
║                  Main Entry Point · app.py                   ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.ui_helpers import inject_global_ui, get_page_icon, _load_image_b64

# ── Page Configuration ─────────────────────────────────────────
st.set_page_config(
    page_title="ALIAS_X · Autonomous Verification Protocol",
    page_icon=get_page_icon(),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Inject: CSS + cyber_bg + overlays ─────────────────────────
inject_global_ui()

# ── Extra boot-screen styles ──────────────────────────────────
st.markdown("""<style>
.boot-screen    { max-width:900px; margin:0 auto; padding:2rem 1rem; }
.boot-logo-img  { display:block; margin:0 auto 1rem; width:130px; height:130px;
                  border-radius:50%; border:2px solid rgba(255,0,60,0.6);
                  box-shadow: 0 0 30px rgba(255,0,60,0.4); }
.boot-title     { text-align:center; font-family:"Ethnocentric",sans-serif;
                  font-size:2.8rem; color:#ff003c; letter-spacing:.25em;
                  margin:0; text-shadow: 0 0 20px rgba(255,0,60,0.5); }
.boot-subtitle  { text-align:center; color:#5a5a8a; font-size:.72rem;
                  letter-spacing:.35em; margin:.4rem 0 1.5rem; }
.boot-divider   { border:none; border-top:1px solid rgba(255,0,60,0.3); margin:1.2rem 0; }
.boot-grid      { display:grid; grid-template-columns:repeat(3,1fr);
                  gap:1rem; margin:1.5rem 0; }
.boot-card      { padding:1.2rem; border-radius:4px; text-align:center; }
.boot-card-icon { font-size:1.8rem; display:block; margin-bottom:.5rem; }
.boot-card h3   { color:#ff003c; font-family:"Ethnocentric",sans-serif;
                  font-size:.85rem; letter-spacing:.15em; margin:.4rem 0; }
.boot-card p    { color:#8a8aaa; font-size:.75rem; line-height:1.5; margin:0; }
.boot-nav       { text-align:center; color:#5a5a7a; font-size:.78rem; letter-spacing:.08em; }
.boot-nav strong{ color:#ff003c; }
.status-badge   { padding:.3rem .6rem; background:rgba(0,0,0,0.5);
                  border:1px solid rgba(255,0,60,0.2); border-radius:3px; text-align:center; }
</style>""", unsafe_allow_html=True)

# ── Logo inline ────────────────────────────────────────────────
logo_b64 = _load_image_b64("aliasX_logo.png")
logo_tag = (
    f'<img class="boot-logo-img" src="data:image/jpeg;base64,{logo_b64}" alt="ALIAS_X"/>'
    if logo_b64 else '<div style="font-size:4rem;text-align:center;">🔺</div>'
)

st.markdown(f"""
<div class="boot-screen">
    {logo_tag}
    <h1 class="boot-title">ALIAS_X</h1>
    <p class="boot-subtitle">AUTONOMOUS VERIFICATION PROTOCOL · v2.4.1</p>
    <hr class="boot-divider"/>
    <div class="boot-grid">
        <div class="boot-card">
            <span class="boot-card-icon">🔍</span>
            <h3>SCAN</h3>
            <p>Upload academic certificates for AI-powered OCR extraction via Google Gemini Vision.</p>
        </div>
        <div class="boot-card">
            <span class="boot-card-icon">✏️</span>
            <h3>VALIDATE</h3>
            <p>Human-in-the-Loop review. Correct extracted contact data before uplink initiation.</p>
        </div>
        <div class="boot-card">
            <span class="boot-card-icon">📡</span>
            <h3>UPLINK</h3>
            <p>Trigger AI voice agent (Bland AI) or encrypted SMTP email to verify credentials.</p>
        </div>
    </div>
    <hr class="boot-divider"/>
    <p class="boot-nav">
        → Navigate using the <strong>sidebar</strong> to access
        <strong>About · Login · Signup · Dashboard</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# ── System Status Bar ──────────────────────────────────────────
st.markdown("<br/>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
env_keys = {
    "GOOGLE_API_KEY": "GEMINI OCR",
    "BLAND_API_KEY":  "BLAND VOICE",
    "SMTP_EMAIL":     "SMTP RELAY",
    "USE_TEST_DATA":  "SIM MODE",
}
for col, (key, label) in zip([col1, col2, col3, col4], env_keys.items()):
    val    = os.getenv(key, "")
    status = "ONLINE"  if val else "OFFLINE"
    color  = "#00ffaa" if val else "#ff003c"
    col.markdown(f"""
<div class="status-badge">
    <span style="color:{color};font-size:.65rem;font-family:'Courier New',monospace;">
        ● {label}: <strong>{status}</strong>
    </span>
</div>""", unsafe_allow_html=True)

st.markdown("""<br/><p style='text-align:center;color:#2a2a3a;font-size:.6rem;
font-family:"Courier New",monospace;letter-spacing:.2em;'>
ALIAS_X · AUTONOMOUS VERIFICATION PROTOCOL · ALL ACTIONS LOGGED</p>""",
unsafe_allow_html=True)
