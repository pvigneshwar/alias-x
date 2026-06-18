"""
ALIAS_X - report_generator.py
Generates A4 PDF verification certificates using fpdf2.
Fixed: uses only Latin-1 safe characters (no unicode checkmarks/crosses).
"""

from datetime import datetime


def generate_pdf_certificate(session: dict) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError:
        raise RuntimeError("fpdf2 is not installed. Run: pip install fpdf2")

    outcome   = session.get("outcome", "UNKNOWN")
    candidate = session.get("candidate") or {}
    registrar = session.get("registrar") or {}
    channel   = session.get("channel", "phone")

    outcome_color = {
        "VERIFIED": (0, 193, 124),
        "REJECTED": (255, 75, 110),
    }.get(outcome, (100, 100, 100))

    # -- Latin-1 safe outcome label (no unicode symbols) -----------------------
    outcome_label = {
        "VERIFIED": "[ VERIFIED ]",
        "REJECTED": "[ REJECTED ]",
    }.get(outcome, f"[ {outcome} ]")

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # -- Header bar ------------------------------------------------------------
    pdf.set_fill_color(0, 212, 255)
    pdf.rect(0, 0, 210, 6, style="F")

    # -- Letterhead ------------------------------------------------------------
    pdf.set_y(12)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 12, "ALIAS_X", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6,
             "Autonomous Linked Intelligence for Academic Screening and eXecution",
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5,
             "Department of Computer Science  |  Autonomous Verification Protocol",
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.set_draw_color(0, 212, 255)
    pdf.set_line_width(0.4)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)

    # -- Outcome badge ---------------------------------------------------------
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*outcome_color)
    pdf.cell(0, 12, outcome_label, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6,
             f"Verification Channel: {channel.upper()}",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # -- Section helper --------------------------------------------------------
    def section_header(title: str):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(0, 212, 255)
        pdf.set_fill_color(17, 24, 39)
        pdf.cell(0, 7, f"  {title.upper()}", fill=True,
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def _safe(text) -> str:
        if not text:
            return "N/A"
        return str(text).encode("latin-1", errors="replace").decode("latin-1")

    def row(label: str, value: str):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(55, 6, _safe(label) + ":", new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 41, 59)
        pdf.multi_cell(0, 6, _safe(value),
                       new_x="LMARGIN", new_y="NEXT")

    # -- Session info ----------------------------------------------------------
    section_header("Session Information")
    row("Session ID",  session.get("session_id", ""))
    row("Agent",       f"{session.get('codename', '')}  ({session.get('agent_id', '')})")
    row("Timestamp",   session.get("timestamp", ""))
    row("Channel",     channel.upper())
    pdf.ln(3)

    # -- Candidate -------------------------------------------------------------
    section_header("Candidate Details")
    row("Student Name", candidate.get("name", ""))
    row("University",   candidate.get("university", ""))
    row("Degree",       candidate.get("degree", ""))
    row("Year",         str(candidate.get("year", "")))
    pdf.ln(3)

    # -- Registrar -------------------------------------------------------------
    section_header("Registrar Contact Used")
    row("Phone",  registrar.get("phone", ""))
    row("Email",  registrar.get("email", ""))
    row("Source", registrar.get("source", ""))
    pdf.ln(3)

    # -- Outcome ---------------------------------------------------------------
    section_header("Verification Outcome")
    row("Result",  outcome)
    pdf.ln(3)

    # -- Transcript ------------------------------------------------------------
    transcript = session.get("transcript") or "No transcript recorded."
    # Strip non-latin-1 characters to avoid font errors
    transcript = transcript.encode("latin-1", errors="replace").decode("latin-1")

    section_header("Transcript")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(0, 5, transcript, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # -- Footer ----------------------------------------------------------------
    pdf.set_draw_color(0, 212, 255)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(
        0, 5,
        f"ALIAS_X Verification Certificate  |  "
        f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  |  "
        f"Session {session.get('session_id', '')}",
        align="C"
    )

    # -- Bottom bar ------------------------------------------------------------
    pdf.set_fill_color(124, 58, 237)
    pdf.rect(0, 291, 210, 6, style="F")

    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, bytearray) else out.encode("latin-1")