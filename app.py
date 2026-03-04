"""
╔══════════════════════════════════════════════════════════════╗
║           ALIAS_X — Autonomous Verification Protocol         ║
║                  Main Entry Point · app.py                   ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.ui_helpers import inject_global_ui, get_page_icon

# ── Page Configuration ─────────────────────────────────────────
st.set_page_config(
    page_title="ALIAS_X · Autonomous Verification Protocol",
    page_icon=get_page_icon(),
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Inject: CSS + cyber_bg + overlays ─────────────────────────
inject_global_ui()

# ── Navigation ─────────────────────────────────────────────────
pg = st.navigation([
    st.Page("pages/0_Home.py",      title="Home",      icon="🏠", default=True),
    st.Page("pages/1_About.py",     title="About",     icon="ℹ️"),
    st.Page("pages/2_Login.py",     title="Login",     icon="🔐"),
    st.Page("pages/3_Signup.py",    title="Signup",    icon="📝"),
    st.Page("pages/4_Dashboard.py", title="Dashboard", icon="📊"),
], position="sidebar")

pg.run()