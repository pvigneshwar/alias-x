"""
ALIAS_X — assets/theme.py
Branded cyber glass theme loader + reusable header
"""

import os
import base64
import streamlit as st


def _file_to_base64(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def inject_css():
    """Inject shared CSS and asset variables into current Streamlit page."""
    asset_dir = os.path.dirname(__file__)

    css_path = os.path.join(asset_dir, "style.css")
    bg_path = os.path.join(asset_dir, "cyber_bg.png")
    logo_path = os.path.join(asset_dir, "aliasX_logo.png")
    font_path = os.path.join(asset_dir, "fonts", "Ethnocentric-Regular.otf")

    bg_b64 = _file_to_base64(bg_path)
    logo_b64 = _file_to_base64(logo_path)
    font_b64 = _file_to_base64(font_path)

    # 1) Inject font + asset variables
    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'Ethnocentric';
            src: url("data:font/otf;base64,{font_b64}") format("opentype");
            font-weight: normal;
            font-style: normal;
        }}

        :root {{
            --ax-bg-image: url("data:image/png;base64,{bg_b64}");
            --ax-logo-image: url("data:image/png;base64,{logo_b64}");
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    # 2) Inject actual CSS file cleanly
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()

        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_header(codename: str | None = None):
    """Render ALIAS_X neon brand header."""
    agent_html = (
        f'<span class="ax-agent-pill">AGENT: {codename.upper()}</span>'
        if codename else ""
    )

    st.markdown(
        f"""
        <div class="ax-header-wrap">
            <div class="ax-brand-left">
                <div class="ax-logo-img"></div>
                <div class="ax-title-wrap">
                    <div class="ax-neon-title">
                        <span class="ax-alias">ALIAS</span><span class="ax-underscore">_</span><span class="ax-x">X</span>
                    </div>
                    <div class="ax-logo-sub">
                        Autonomous Linked Intelligence for Academic Screening &amp; eXecution
                    </div>
                </div>
            </div>
            <div style="margin-left:auto;">{agent_html}</div>
        </div>
        <hr/>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str, colour: str = ""):
    cls = f"ax-section-label {colour}".strip()
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)