"""
╔══════════════════════════════════════════════════════════════╗
║          ALIAS_X · About · pages/1_About.py                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.ui_helpers import inject_global_ui, get_page_icon, _load_image_b64

# ── Page Config ────────────────────────────────────────────────
st.set_page_config(
    page_title="ALIAS_X · About",
    page_icon=get_page_icon(),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Inject global UI (CSS + cyber_bg + overlays) ──────────────
inject_global_ui()

# ── Page-level styles ─────────────────────────────────────────
st.markdown("""<style>
.about-header      { max-width:860px; margin:0 auto 2rem; text-align:center; }
.about-logo-img    { display:block; margin:0 auto .8rem; width:110px; height:110px;
                     border-radius:50%; border:2px solid rgba(255,0,60,0.55);
                     box-shadow:0 0 24px rgba(255,0,60,0.35); }
.about-title       { font-family:"Ethnocentric",sans-serif; font-size:2.2rem;
                     color:#ff003c; letter-spacing:.25em; margin:0;
                     text-shadow:0 0 16px rgba(255,0,60,0.45); }
.about-tagline     { color:#5a5a8a; font-size:.68rem; letter-spacing:.35em; margin:.3rem 0 0; }
.about-section     { max-width:860px; margin:0 auto 1.8rem;
                     background:rgba(8,8,15,0.88); border:1px solid rgba(255,0,60,0.28);
                     border-radius:4px; padding:1.4rem 1.8rem;
                     backdrop-filter:blur(6px); }
.about-section h2  { font-family:"Ethnocentric",sans-serif; color:#ff003c;
                     font-size:.95rem; letter-spacing:.2em; margin:0 0 .8rem; }
.about-section p   { color:#b0b0c8; font-size:.82rem; line-height:1.7; margin:.4rem 0; }
.about-section ul  { color:#b0b0c8; font-size:.82rem; line-height:1.9;
                     padding-left:1.2rem; margin:.4rem 0; }
.about-section li  { margin:.2rem 0; }
.tag               { display:inline-block; padding:.15rem .55rem;
                     background:rgba(255,0,60,0.12); border:1px solid rgba(255,0,60,0.4);
                     border-radius:3px; color:#ff003c; font-size:.65rem;
                     letter-spacing:.1em; margin:.2rem .3rem .2rem 0; }
.tech-grid         { display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem; margin:.8rem 0; }
.tech-item         { background:rgba(255,0,60,0.07); border:1px solid rgba(255,0,60,0.2);
                     border-radius:4px; padding:.7rem; text-align:center; }
.tech-item .t-icon { font-size:1.4rem; display:block; margin-bottom:.3rem; }
.tech-item .t-name { color:#ff003c; font-family:"Ethnocentric",sans-serif;
                     font-size:.68rem; letter-spacing:.12em; }
.tech-item .t-desc { color:#7a7a9a; font-size:.68rem; margin-top:.2rem; }
.ax-timeline       { border-left:2px solid rgba(255,0,60,0.4);
                     padding-left:1.2rem; margin:.8rem 0; }
.ax-timeline-item  { position:relative; margin-bottom:1rem; }
.ax-timeline-item::before {
    content:''; position:absolute; left:-1.45rem; top:.35rem;
    width:8px; height:8px; border-radius:50%;
    background:#ff003c; box-shadow:0 0 6px rgba(255,0,60,0.7);
}
.ax-timeline-item .tl-label { color:#ff003c; font-size:.7rem;
                               letter-spacing:.1em; font-family:"Ethnocentric",sans-serif; }
.ax-timeline-item .tl-text  { color:#9090b0; font-size:.78rem;
                               line-height:1.5; margin-top:.2rem; }
</style>""", unsafe_allow_html=True)

# ── Logo ───────────────────────────────────────────────────────
logo_b64 = _load_image_b64("aliasX_logo.png")
logo_tag = (
    f'<img class="about-logo-img" src="data:image/jpeg;base64,{logo_b64}" alt="ALIAS_X"/>'
    if logo_b64 else '<div style="font-size:3rem;text-align:center;">🔺</div>'
)

# ── Header ─────────────────────────────────────────────────────
st.markdown(f"""
<div class="about-header">
    {logo_tag}
    <h1 class="about-title">ALIAS_X</h1>
    <p class="about-tagline">AUTONOMOUS VERIFICATION PROTOCOL · v2.4.1</p>
</div>
""", unsafe_allow_html=True)

# ── Section 1: Mission ─────────────────────────────────────────
st.markdown("""
<div class="about-section">
    <h2>⬡ MISSION STATEMENT</h2>
    <p>
        ALIAS_X is an <strong style="color:#ffffff;">AI-powered academic credential
        verification system</strong> designed for the modern intelligence workflow.
        Built on a Human-in-the-Loop (HITL) architecture, it combines the precision
        of Google Gemini Vision OCR with the reach of autonomous voice and email
        uplink channels.
    </p>
    <p>
        The system eliminates manual verification delays by automatically extracting
        certificate data, validating institutional contact points, and triggering
        multi-channel verification uplinks — all within a single unified terminal.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Section 2: Technology Stack ────────────────────────────────
st.markdown("""
<div class="about-section">
    <h2>⬡ TECHNOLOGY STACK</h2>
    <div class="tech-grid">
        <div class="tech-item">
            <span class="t-icon">🔬</span>
            <div class="t-name">GEMINI 2.5 FLASH</div>
            <div class="t-desc">Google Vision OCR · Certificate Intelligence Extraction</div>
        </div>
        <div class="tech-item">
            <span class="t-icon">🎙️</span>
            <div class="t-name">BLAND AI</div>
            <div class="t-desc">Autonomous Voice Agent · AI Phone Verification</div>
        </div>
        <div class="tech-item">
            <span class="t-icon">📧</span>
            <div class="t-name">SMTP TLS</div>
            <div class="t-desc">Encrypted Email Channel · Institutional Uplink</div>
        </div>
        <div class="tech-item">
            <span class="t-icon">🐍</span>
            <div class="t-name">STREAMLIT</div>
            <div class="t-desc">Real-Time UI · Human-in-the-Loop Interface</div>
        </div>
        <div class="tech-item">
            <span class="t-icon">🧠</span>
            <div class="t-name">HITL ARCH.</div>
            <div class="t-desc">Human Oversight Layer · Manual Contact Correction</div>
        </div>
        <div class="tech-item">
            <span class="t-icon">🔐</span>
            <div class="t-name">ENV VAULT</div>
            <div class="t-desc">Dotenv Secrets · Simulation Mode Toggle</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Section 3: How It Works ────────────────────────────────────
st.markdown("""
<div class="about-section">
    <h2>⬡ PROTOCOL SEQUENCE</h2>
    <div class="ax-timeline">
        <div class="ax-timeline-item">
            <div class="tl-label">01 · UPLOAD</div>
            <div class="tl-text">Operator uploads an academic certificate image (JPG, PNG, WEBP, BMP, TIFF).
            The certificate is passed to the Gemini 2.5 Flash Vision API for deep-scan extraction.</div>
        </div>
        <div class="ax-timeline-item">
            <div class="tl-label">02 · EXTRACT</div>
            <div class="tl-text">AI extracts: Subject Name, University, Degree, Graduation Year,
            Registrar Phone Number, and Registrar Email — returning structured JSON.</div>
        </div>
        <div class="ax-timeline-item">
            <div class="tl-label">03 · VALIDATE</div>
            <div class="tl-text">Operator reviews OCR output. Profile fields (name/degree) are locked
            as neon-green read-only. Contact fields (phone/email) are editable for human correction.</div>
        </div>
        <div class="ax-timeline-item">
            <div class="tl-label">04 · ARM</div>
            <div class="tl-text">Channel Status panel shows Voice (Bland AI) and Email (SMTP) readiness.
            Channels auto-arm when valid contact data is detected.</div>
        </div>
        <div class="ax-timeline-item">
            <div class="tl-label">05 · UPLINK</div>
            <div class="tl-text">Operator fires the uplink. ALIAS_X simultaneously initiates a
            Bland AI voice call and dispatches an encrypted SMTP verification email to the university
            registrar.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Section 4: Features ────────────────────────────────────────
st.markdown("""
<div class="about-section">
    <h2>⬡ SYSTEM CAPABILITIES</h2>
    <ul>
        <li>🔺 Multi-format certificate OCR (JPG · PNG · WEBP · BMP · TIFF)</li>
        <li>🔺 Dual-channel uplink: Voice (Bland AI) + Email (SMTP TLS)</li>
        <li>🔺 Simulation mode for safe testing without live API calls</li>
        <li>🔺 Session-scoped Human-in-the-Loop contact correction</li>
        <li>🔺 Real-time uplink log with status codes [OK] / [ERR]</li>
        <li>🔺 Duplicate-submission lock (one uplink per certificate session)</li>
        <li>🔺 Institutional email validation (.ac · .in · .edu · .college)</li>
        <li>🔺 International phone format support (E.164 with + prefix)</li>
    </ul>
    <br/>
    <span class="tag">OCR</span>
    <span class="tag">HITL</span>
    <span class="tag">VOICE AI</span>
    <span class="tag">SMTP</span>
    <span class="tag">GEMINI</span>
    <span class="tag">BLAND AI</span>
    <span class="tag">CYBERPUNK</span>
    <span class="tag">STREAMLIT</span>
</div>
""", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────
st.markdown("""<br/><p style='text-align:center;color:#2a2a3a;font-size:.6rem;
font-family:"Courier New",monospace;letter-spacing:.2em;'>
ALIAS_X · AUTONOMOUS VERIFICATION PROTOCOL · ALL ACTIONS LOGGED</p>""",
unsafe_allow_html=True)
