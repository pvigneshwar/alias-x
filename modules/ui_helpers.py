"""
╔══════════════════════════════════════════════════════════════╗
║         ALIAS_X · Shared UI Helpers · modules/ui_helpers.py  ║
║    Centralised injector: CSS + cyber_bg + aliasX page icon   ║
╚══════════════════════════════════════════════════════════════╝
"""

import base64
import sys
import streamlit as st
from pathlib import Path

# ── Project Root ──────────────────────────────────────────────
ROOT = Path(__file__).parent.parent


# ══════════════════════════════════════════════════════════════
#  ASSET LOADERS
# ══════════════════════════════════════════════════════════════

def _load_image_b64(filename: str) -> str:
    """Return a base64-encoded string for the given image file."""
    path = ROOT / filename
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _load_css() -> str:
    """Read style.css from project root."""
    css_path = ROOT / "style.css"
    if not css_path.exists():
        return ""
    with open(css_path, "r", encoding="utf-8") as f:
        return f.read()


def get_page_icon():
    """
    Return aliasX_logo.png as a PIL Image for st.set_page_config(page_icon=...).
    Falls back to emoji string if PIL / image not available.
    """
    try:
        from PIL import Image as PILImage
        logo_path = ROOT / "aliasX_logo.png"
        if logo_path.exists():
            return PILImage.open(logo_path)
    except Exception:
        pass
    return "🔺"


# ══════════════════════════════════════════════════════════════
#  MAIN INJECTOR — call this AFTER st.set_page_config()
# ══════════════════════════════════════════════════════════════

def inject_global_ui():
    """
    Injects into every page:
      1. style.css  (fonts, colors, button styles, input overrides)
      2. cyber_bg.png  as a fixed CSS background via base64 data-URI
      3. Dark overlay + scanline animation on top of background
      4. Glassmorphism panel treatment

    Call once, right after st.set_page_config().
    """

    # ── 1. User's style.css ────────────────────────────────────
    user_css = _load_css()

    # ── 2. Background image (base64) ──────────────────────────
    bg_b64 = _load_image_b64("cyber_bg.png")
    bg_css_rule = ""
    if bg_b64:
        mime = "image/png"
        bg_css_rule = f"""
[data-testid="stApp"] {{
    background-image: url("data:{mime};base64,{bg_b64}") !important;
    background-attachment: fixed !important;
    background-size: cover !important;
    background-position: center top !important;
    background-repeat: no-repeat !important;
}}"""

    # ── 3. Overlay, scanlines, layout extras ──────────────────
    overlay_css = """
/* ─── Dark overlay over background for readability ─── */
[data-testid="stApp"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background: linear-gradient(
        135deg,
        rgba(0, 0, 0, 0.83) 0%,
        rgba(3, 0, 10, 0.80) 40%,
        rgba(8, 0, 18, 0.86) 100%
    );
    pointer-events: none;
    z-index: 0;
}

/* ─── Scanline animation ─── */
[data-testid="stApp"]::after {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 3px,
        rgba(0, 255, 170, 0.012) 3px,
        rgba(0, 255, 170, 0.012) 4px
    );
    pointer-events: none;
    z-index: 1;
    animation: alias_scan 12s linear infinite;
}

@keyframes alias_scan {
    0%   { background-position: 0 0;     }
    100% { background-position: 0 160px; }
}

/* ─── Ensure content sits above overlay layers ─── */
[data-testid="stAppViewContainer"] > * {
    position: relative;
    z-index: 2;
}
section[data-testid="stSidebar"] > div:first-child {
    background-color: rgba(3, 3, 10, 0.94) !important;
    border-right: 1px solid rgba(255, 0, 60, 0.45) !important;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

/* ─── Main block transparent so bg shows ─── */
.main .block-container {
    background-color: transparent !important;
    padding-top: 1.5rem;
}

/* ─── Cards / panels glass treatment ─── */
[data-testid="stVerticalBlock"] > [style*="border"],
.boot-card,
.section-panel,
.ax-card {
    background-color: rgba(8, 8, 15, 0.88) !important;
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    border: 1px solid rgba(255, 0, 60, 0.35) !important;
    border-radius: 4px;
}

/* ─── Sidebar nav links ─── */
[data-testid="stSidebarNav"] a {
    color: #ffffff !important;
    font-family: "Ethnocentric", sans-serif;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
}
[data-testid="stSidebarNav"] a:hover {
    color: #ff003c !important;
}

/* ─── Form / input container backgrounds ─── */
[data-testid="stForm"] {
    background-color: rgba(8, 8, 15, 0.85) !important;
    border: 1px solid rgba(255, 0, 60, 0.3) !important;
    border-radius: 4px;
    padding: 1.2rem 1.5rem;
    backdrop-filter: blur(6px);
}

/* ─── Metric cards ─── */
[data-testid="stMetric"] {
    background-color: rgba(10, 10, 18, 0.90) !important;
    border: 1px solid rgba(255, 0, 60, 0.25) !important;
    border-radius: 4px;
    padding: 0.8rem;
}

/* ─── Divider lines ─── */
hr {
    border-color: rgba(255, 0, 60, 0.3) !important;
}

/* ─── Page icon in browser tab (handled by PIL in set_page_config) ─── */
"""

    # ── Combine & inject ──────────────────────────────────────
    full_css = user_css + "\n" + bg_css_rule + "\n" + overlay_css
    st.markdown(f"<style>{full_css}</style>", unsafe_allow_html=True)
