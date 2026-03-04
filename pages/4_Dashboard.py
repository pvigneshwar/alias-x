# ══════════════════════════════════════════════════════════════
#  SECTION 02 — STUDENT PROFILE (Editable)
# ══════════════════════════════════════════════════════════════
from turtle import st

from modules.ocr_engine import get_empty_data


st.markdown("---")
st.markdown('<p class="section-num">02 · STUDENT PROFILE</p>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:#5a5a7a;font-size:.78rem;">AI-extracted data (editable). '
    'You may correct any incorrect field.</p>',
    unsafe_allow_html=True
)

ocr = st.session_state.ocr_data or get_empty_data()

# Load fresh OCR data only when new file uploaded
if "profile_loaded" not in st.session_state:
    st.session_state.profile_loaded = False

if not st.session_state.profile_loaded:
    st.session_state.d_name   = ocr.get("name", "")
    st.session_state.d_degree = ocr.get("degree", "")
    st.session_state.d_uni    = ocr.get("university", "")
    st.session_state.d_year   = ocr.get("year", "")
    st.session_state.profile_loaded = True

col_l, col_r = st.columns(2)

with col_l:
    st.text_input("▸ STUDENT NAME", key="d_name")
    st.text_input("▸ DEGREE / QUALIFICATION", key="d_degree")

with col_r:
    st.text_input("▸ ISSUING UNIVERSITY", key="d_uni")
    st.text_input("▸ GRADUATION YEAR", key="d_year")