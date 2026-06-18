"""
ALIAS_X — app.py  (single-page, user-facing)
"""

import os
import sys
import uuid
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv, set_key

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ENV_PATH   = os.path.join(BASE_DIR, ".env")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, ASSETS_DIR)

from theme import inject_css, render_header, section_label
load_dotenv(ENV_PATH)

logo_path = os.path.join(ASSETS_DIR, "aliasX_logo.png")
st.set_page_config(page_title="ALIAS_X", layout="wide", page_icon=logo_path)
inject_css()

st.markdown("<style>[data-testid='stSidebarNav']{display:none!important;}</style>",
            unsafe_allow_html=True)

_DEFAULTS = dict(
    authenticated=False, codename=None, agent_id=None,
    room_data=[], nav="home",
    vfy_stage="upload", vfy_ocr=None, vfy_registrar=None, vfy_result=None,
)
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

SIMULATION = os.getenv("SIMULATION_MODE", "ON").upper() == "ON"


def _reset_pipeline():
    st.session_state.update(vfy_stage="upload", vfy_ocr=None,
                            vfy_registrar=None, vfy_result=None)


# ══════════════════════════════════════════════════════════════
# LOGIN WALL
# ══════════════════════════════════════════════════════════════
if not st.session_state["authenticated"]:
    render_header()
    st.markdown("""<div class="ax-panel ax-panel-purple">
        <h2>AGENT AUTHENTICATION</h2>
        <p>Identify yourself before accessing mission systems.</p>
    </div>""", unsafe_allow_html=True)

    tab_login, tab_reg = st.tabs(["🔐  LOGIN", "📋  REGISTER"])
    with tab_login:
        section_label("AGENT LOGIN")
        cn = st.text_input("Agent Codename", key="li_cn")
        ak = st.text_input("Access Key", type="password", key="li_ak")
        if st.button("ACCESS ALIAS_X", use_container_width=True):
            if not cn or not ak:
                st.error("Both fields are required.")
            else:
                from auth_manager import validate_login
                res = validate_login(cn.strip(), ak)
                if res["success"]:
                    st.session_state.update(authenticated=True,
                                            codename=cn.strip().upper(),
                                            agent_id=res["agent_id"], nav="home")
                    st.rerun()
                else:
                    st.error(res.get("message", "ACCESS DENIED"))

    with tab_reg:
        section_label("NEW AGENT REGISTRATION")
        nc  = st.text_input("Choose a Codename",    key="reg_cn")
        nk  = st.text_input("Choose an Access Key", type="password", key="reg_k1")
        nk2 = st.text_input("Confirm Access Key",   type="password", key="reg_k2")
        if st.button("REGISTER AGENT", use_container_width=True):
            if not nc or not nk:
                st.error("All fields are required.")
            elif nk != nk2:
                st.error("Keys do not match.")
            else:
                from auth_manager import register_agent
                res = register_agent(nc.strip(), nk)
                st.success(f"Agent {nc.upper()} registered. You can now log in.") \
                    if res["success"] else st.error(res.get("message"))
    st.stop()


# ══════════════════════════════════════════════════════════════
# SIDEBAR — nav + logout only
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ALIAS_X")
    st.markdown(f"**Agent:** {st.session_state['codename']}")
    st.markdown("---")
    for icon, key, label in [
        ("🏠", "home",     "Mission Control"),
        ("🔍", "verify",   "Verify Certificate"),
        ("📊", "admin",    "Results"),
        ("⚙️", "settings", "Account"),
    ]:
        active = st.session_state["nav"] == key
        if st.button(f"{'▶ ' if active else ''}{icon}  {label}",
                     use_container_width=True, key=f"nav_{key}"):
            st.session_state["nav"] = key
            st.rerun()
    st.markdown("---")
    if st.button("🚪  LOG OUT", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.caption("ALIAS_X © Cyber Operations Interface")


render_header(st.session_state.get("codename"))


# ══════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════
if st.session_state["nav"] == "home":
    st.markdown("""<div class="ax-panel ax-panel-purple">
        <h2>MISSION CONTROL</h2>
        <p>Welcome back. Use the modules below to verify candidate credentials,
        review past results, or update your account.</p>
    </div>""", unsafe_allow_html=True)

    # Stats — only what the agent cares about
    try:
        from db_manager import summary_stats
        stats = summary_stats()
    except Exception:
        stats = {"total": 0, "verified": 0, "rejected": 0}

    section_label("YOUR ACTIVITY")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Verifications", stats.get("total", 0))
    c2.metric("✅ Verified",         stats.get("verified", 0))
    c3.metric("❌ Rejected",         stats.get("rejected", 0))

    st.markdown("---")
    section_label("QUICK START", "green")
    q1, q2, q3 = st.columns(3)
    with q1:
        st.markdown('<div class="ax-panel ax-panel-green"><h3>🔍 VERIFY</h3>'
                    '<p>Upload a degree certificate and run the full verification pipeline.</p></div>',
                    unsafe_allow_html=True)
        if st.button("START VERIFICATION", use_container_width=True, key="qs_v"):
            st.session_state["nav"] = "verify"; st.rerun()
    with q2:
        st.markdown('<div class="ax-panel ax-panel-purple"><h3>📊 RESULTS</h3>'
                    '<p>View all past verifications and download reports.</p></div>',
                    unsafe_allow_html=True)
        if st.button("VIEW RESULTS", use_container_width=True, key="qs_a"):
            st.session_state["nav"] = "admin"; st.rerun()
    with q3:
        st.markdown('<div class="ax-panel ax-panel-amber"><h3>⚙️ ACCOUNT</h3>'
                    '<p>Update your codename or change your access key.</p></div>',
                    unsafe_allow_html=True)
        if st.button("ACCOUNT SETTINGS", use_container_width=True, key="qs_s"):
            st.session_state["nav"] = "settings"; st.rerun()

    # Recent activity — clean, no technical columns
    try:
        from db_manager import load_log
        import pandas as pd
        recent = load_log()[-5:][::-1]
        if recent:
            st.markdown("---")
            section_label("RECENT VERIFICATIONS")
            df = pd.DataFrame([{
                "Date":       r.get("timestamp", "")[:10],
                "Candidate":  (r.get("candidate") or {}).get("name", "—"),
                "University": (r.get("candidate") or {}).get("university", "—"),
                "Outcome":    r.get("outcome", "—"),
            } for r in recent])
            st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
# VERIFY PIPELINE
# ══════════════════════════════════════════════════════════════
elif st.session_state["nav"] == "verify":
    st.markdown("""<div class="ax-panel ax-panel-purple">
        <h2>VERIFICATION PIPELINE</h2>
        <p>Upload a degree certificate to begin the autonomous verification sequence.</p>
    </div>""", unsafe_allow_html=True)

    # Progress strip
    STAGES    = ["Upload", "Review Details", "Find Registrar", "Confirm", "Verify", "Result"]
    STAGE_IDX = {"upload": 0, "ocr_done": 1, "uplink_done": 2,
                 "hitl_approved": 3, "call_done": 4}
    cur = STAGE_IDX.get(st.session_state["vfy_stage"], 0)
    prog = "".join(
        f'<div style="background:{"#00c17c" if i<cur else "#00D4FF" if i==cur else "#1f2937"};'
        f'color:{"#fff" if i<cur else "#0A0E1A" if i==cur else "#6b7280"};'
        f'padding:6px 14px;border-radius:20px;font-size:.78rem;font-weight:700;">'
        f'{i+1}. {lbl}</div>'
        for i, lbl in enumerate(STAGES)
    )
    st.markdown(f'<div style="display:flex;gap:6px;margin-bottom:20px;flex-wrap:wrap;">{prog}</div>',
                unsafe_allow_html=True)

    # ── Step 1: Upload ─────────────────────────────────────
    if st.session_state["vfy_stage"] == "upload":
        section_label("STEP 1 — UPLOAD CERTIFICATE")
        up = st.file_uploader("Upload degree certificate (JPG / PNG / WEBP)",
                              type=["jpg", "jpeg", "png", "webp"])
        if up:
            st.image(up, caption="Certificate preview", use_container_width=True)
            if st.button("▶  EXTRACT DETAILS", use_container_width=True):
                with st.spinner("Reading certificate…"):
                    from ocr_engine import extract_certificate_data
                    data = extract_certificate_data(up, simulation=SIMULATION)
                data.pop("_error", None)
                st.session_state.update(vfy_ocr=data, vfy_stage="ocr_done")
                st.rerun()

    # ── Step 2: Review extracted details ──────────────────
    elif st.session_state["vfy_stage"] == "ocr_done":
        section_label("STEP 2 — REVIEW DETAILS")
        ocr = st.session_state["vfy_ocr"]
        st.info("Check the details below and correct anything before continuing.")
        ca, cb = st.columns(2)
        with ca:
            name = st.text_input("Student Name", value=ocr.get("name") or "")
            uni  = st.text_input("University",   value=ocr.get("university") or "")
        with cb:
            deg  = st.text_input("Degree",       value=ocr.get("degree") or "")
            year = st.text_input("Year",         value=ocr.get("year") or "")
        st.session_state["vfy_ocr"].update(
            name=name or None, university=uni or None,
            degree=deg or None, year=year or None)
        ca, cb = st.columns([3, 1])
        with ca:
            if st.button("▶  FIND REGISTRAR CONTACT", use_container_width=True,
                         disabled=not uni):
                with st.spinner("Locating registrar contact details…"):
                    from intel_uplink import get_registrar_contact
                    contact = get_registrar_contact(uni, simulation=SIMULATION)
                st.session_state.update(vfy_registrar=contact, vfy_stage="uplink_done")
                st.rerun()
        with cb:
            if st.button("↩ RESTART", use_container_width=True):
                _reset_pipeline(); st.rerun()

    # ── Step 3: Confirm registrar contact ─────────────────
    elif st.session_state["vfy_stage"] == "uplink_done":
        section_label("STEP 3 — REGISTRAR CONTACT")
        reg = st.session_state.get("vfy_registrar", {})
        found = reg.get("phone") or reg.get("email")
        if found:
            st.success("Contact details found. Review and confirm before proceeding.")
        else:
            st.warning("No contact found automatically — please enter the details manually.")
        ca, cb = st.columns(2)
        with ca:
            phone = st.text_input("Phone Number", value=reg.get("phone") or "",
                                  placeholder="+91XXXXXXXXXX")
        with cb:
            email = st.text_input("Email Address", value=reg.get("email") or "")
        st.session_state["vfy_registrar"].update(
            phone=phone or None, email=email or None)
        ca, cb = st.columns([3, 1])
        with ca:
            if st.button("▶  CONFIRM & REVIEW", use_container_width=True):
                st.session_state["vfy_stage"] = "hitl_approved"; st.rerun()
        with cb:
            if st.button("↩ BACK", use_container_width=True):
                st.session_state["vfy_stage"] = "ocr_done"; st.rerun()

    # ── Step 4: Final review before call ──────────────────
    elif st.session_state["vfy_stage"] == "hitl_approved":
        section_label("STEP 4 — FINAL REVIEW")
        ocr = st.session_state["vfy_ocr"]
        reg = st.session_state["vfy_registrar"]
        st.warning("Review all details carefully before authorising the verification call.")
        ca, cb = st.columns(2)
        with ca:
            st.markdown("**🎓 Candidate**")
            for l, v in [("Name", ocr.get("name")), ("University", ocr.get("university")),
                         ("Degree", ocr.get("degree")), ("Year", ocr.get("year"))]:
                st.write(f"- **{l}:** {v or 'N/A'}")
        with cb:
            st.markdown("**📞 Registrar**")
            for l, v in [("Phone", reg.get("phone")), ("Email", reg.get("email"))]:
                st.write(f"- **{l}:** {v or 'N/A'}")
        st.markdown("---")
        ca, cb, cc = st.columns(3)
        with ca:
            auth_btn   = st.button("✅  AUTHORISE VERIFICATION", use_container_width=True)
        with cb:
            reject_btn = st.button("❌  REJECT",                use_container_width=True)
        with cc:
            if st.button("↩ BACK", use_container_width=True):
                st.session_state["vfy_stage"] = "uplink_done"; st.rerun()

        if auth_btn:
            with st.spinner("Placing verification call… this may take up to 2 minutes."):
                from ai_caller import initiate_verification_call, SIMULATION_VERIFIED
                result = (SIMULATION_VERIFIED.copy() if SIMULATION else
                          initiate_verification_call(
                              phone=reg.get("phone") or "", data=ocr,
                              simulation=False, fallback_email=reg.get("email") or ""))
            st.session_state.update(vfy_result=result, vfy_stage="call_done")
            st.rerun()
        if reject_btn:
            st.session_state.update(
                vfy_result={"status": "REJECTED", "channel": "manual",
                            "transcript": "Manually rejected by agent."},
                vfy_stage="call_done"); st.rerun()

    # ── Step 5: Result ─────────────────────────────────────
    elif st.session_state["vfy_stage"] == "call_done":
        ocr    = st.session_state.get("vfy_ocr")        or {}
        reg    = st.session_state.get("vfy_registrar")  or {}
        result = st.session_state.get("vfy_result")     or {}
        outcome = result.get("status", "UNKNOWN")
        channel = result.get("channel", "phone")

        badge_cls = {"VERIFIED": "ax-badge-verified", "REJECTED": "ax-badge-rejected",
                     "TIMEOUT":  "ax-badge-timeout"}.get(outcome, "ax-badge-timeout")
        icon = {"VERIFIED": "✅", "REJECTED": "❌", "TIMEOUT": "⏱"}.get(outcome, "❓")

        st.markdown(f'<div style="text-align:center;padding:28px 0;">'
                    f'<span class="{badge_cls}">{icon}  {outcome}</span></div>',
                    unsafe_allow_html=True)

        # Candidate summary card
        st.markdown(f"""
        <div class="ax-panel">
            <strong>{ocr.get("name","—")}</strong><br>
            {ocr.get("degree","—")} · {ocr.get("university","—")} · {ocr.get("year","—")}
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📋 View Call Transcript"):
            st.text(result.get("transcript", "No transcript available."))

        # Persist
        sid = str(uuid.uuid4())[:8].upper()
        ts  = datetime.now(timezone.utc).isoformat()
        rec = dict(session_id=sid, agent_id=st.session_state.get("agent_id", ""),
                   codename=st.session_state.get("codename", ""), timestamp=ts,
                   candidate={k: ocr.get(k) for k in ("name","university","degree","year")},
                   registrar={k: reg.get(k) for k in ("phone","email","source")},
                   outcome=outcome, channel=channel, transcript=result.get("transcript"))
        try:
            from db_manager import append_session; append_session(rec)
        except Exception: pass
        flat = dict(session_id=sid, timestamp=ts, codename=rec["codename"],
                    name=ocr.get("name","N/A"), university=ocr.get("university","N/A"),
                    degree=ocr.get("degree","N/A"), year=ocr.get("year","N/A"),
                    phone=reg.get("phone","N/A"), result=outcome, channel=channel)
        rd = st.session_state.setdefault("room_data", [])
        if not any(r.get("session_id") == sid for r in rd):
            rd.append(flat)

        # PDF
        try:
            from report_generator import generate_pdf_certificate
            st.download_button("⬇  DOWNLOAD VERIFICATION CERTIFICATE",
                               data=generate_pdf_certificate(rec),
                               file_name=f"ALIASX_{sid}.pdf",
                               mime="application/pdf", use_container_width=True)
        except Exception as ex:
            st.error(f"Could not generate PDF: {ex}")

        st.markdown("---")
        ca, cb = st.columns(2)
        with ca:
            if st.button("▶  VERIFY ANOTHER CANDIDATE", use_container_width=True):
                _reset_pipeline(); st.rerun()
        with cb:
            if st.button("📊  VIEW ALL RESULTS", use_container_width=True):
                st.session_state["nav"] = "admin"; st.rerun()


# ══════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════
elif st.session_state["nav"] == "admin":
    import pandas as pd
    st.markdown("""<div class="ax-panel ax-panel-purple">
        <h2>RESULTS</h2>
        <p>All candidate verifications and outcomes.</p>
    </div>""", unsafe_allow_html=True)

    try:
        from db_manager import load_log, summary_stats
        stats   = summary_stats()
        records = load_log()
    except Exception:
        stats, records = {}, []

    section_label("SUMMARY")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total",       stats.get("total", 0))
    c2.metric("✅ Verified", stats.get("verified", 0))
    c3.metric("❌ Rejected", stats.get("rejected", 0))

    if not records:
        st.info("No verifications yet.")
        if st.button("▶  START A VERIFICATION"):
            st.session_state["nav"] = "verify"; st.rerun()
    else:
        rows = [{
            "Date":       r.get("timestamp", "")[:10],
            "Name":       (r.get("candidate") or {}).get("name", "—"),
            "University": (r.get("candidate") or {}).get("university", "—"),
            "Degree":     (r.get("candidate") or {}).get("degree", "—"),
            "Year":       (r.get("candidate") or {}).get("year", "—"),
            "Outcome":    r.get("outcome", "—"),
        } for r in records]
        df = pd.DataFrame(rows)

        section_label("OUTCOME BREAKDOWN", "green")
        st.bar_chart(df["Outcome"].value_counts())

        section_label("ALL VERIFICATIONS")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("⬇  EXPORT AS CSV",
                           df.to_csv(index=False).encode(),
                           "aliasx_results.csv", "text/csv")


# ══════════════════════════════════════════════════════════════
# ACCOUNT SETTINGS
# ══════════════════════════════════════════════════════════════
elif st.session_state["nav"] == "settings":
    st.markdown("""<div class="ax-panel ax-panel-purple">
        <h2>ACCOUNT</h2>
        <p>Update your agent identity and access credentials.</p>
    </div>""", unsafe_allow_html=True)

    section_label("AGENT IDENTITY")
    codename = st.text_input("Your Codename",
                             value=st.session_state.get("codename", ""))
    if st.button("UPDATE CODENAME", use_container_width=True):
        if codename.strip():
            st.session_state["codename"] = codename.strip().upper()
            st.success("Codename updated.")
        else:
            st.error("Codename cannot be empty.")

    st.markdown("---")
    section_label("CHANGE ACCESS KEY", "green")
    old_key = st.text_input("Current Access Key", type="password", key="ck_old")
    new_key = st.text_input("New Access Key",     type="password", key="ck_new")
    cnf_key = st.text_input("Confirm New Key",    type="password", key="ck_cnf")
    if st.button("CHANGE ACCESS KEY", use_container_width=True):
        if not old_key or not new_key:
            st.error("All fields are required.")
        elif new_key != cnf_key:
            st.error("New keys do not match.")
        else:
            from auth_manager import change_access_key
            res = change_access_key(st.session_state["codename"], old_key, new_key)
            (st.success if res["success"] else st.error)(res["message"])
