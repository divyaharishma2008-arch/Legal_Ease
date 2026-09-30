"""
LegalEase Frontend (Streamlit)
==============================
Web UI for the LegalEase document generator.

Flow:
    1. The user fills in the document form.
    2. The app sends the details to the FastAPI backend (POST /generate).
    3. The generated draft is shown as a preview and in an editable box.
    4. The user downloads the (edited) text as TXT, DOCX or PDF.

Run:
    streamlit run app.py

Environment:
    BACKEND_URL  Base URL of the FastAPI backend (default http://127.0.0.1:8000)
"""

import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

from utils.exporters import format_docx, format_html_preview, format_pdf, format_txt

load_dotenv()  # Reads BACKEND_URL (and other settings) from .env

# --- Page configuration ------------------------------------------------------
st.set_page_config(
    page_title="LegalEase",
    page_icon="⚖️",
    layout="wide",
)

# Backend base URL; trailing slash removed so f"{BACKEND_URL}/generate" is clean.
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"  # Optional logo

# --- Styling -----------------------------------------------------------------
st.markdown(
    """
    <style>
    .main-title { text-align:center; font-size:42px; font-weight:700; margin-bottom:4px; }
    .subtitle { text-align:center; color:#9ca3af; margin-bottom:28px; }
    .stButton > button { width:100%; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header ------------------------------------------------------------------
if LOGO_PATH.exists():
    left, center, right = st.columns([1, 1, 1])
    with center:
        st.image(str(LOGO_PATH), width=100)

st.markdown('<div class="main-title">LegalEase</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-Powered Legal Document Generator</div>',
    unsafe_allow_html=True,
)

# Legal disclaimer shown on every page load.
st.info(
    "LegalEase creates editable AI-generated legal drafts. "
    "Review the final document with a qualified legal professional before signing or relying on it."
)

# --- Input form --------------------------------------------------------------
with st.form("document_form"):
    st.subheader("Document details")

    document_type = st.text_input(
        "Document Type",
        placeholder="Example: Freelance Work Contract",
    )

    parties = st.text_area(
        "Parties Involved",
        placeholder="Example: Jane Doe (Service Provider), TechNova Inc. (Client)",
        height=110,
    )

    terms = st.text_area(
        "Terms & Conditions",
        placeholder=(
            "Use semicolons between clauses. Example: Payment within 30 days; "
            "Confidentiality must be maintained; Either party may terminate with 15 days notice"
        ),
        height=160,
    )

    dates = st.text_input(
        "Effective Date",
        placeholder="Example: 10/04/2025",
    )

    submitted = st.form_submit_button("Generate Document", type="primary")

# --- Submit handling ---------------------------------------------------------
if submitted:
    # Client-side check: list every empty field in one message.
    missing = []
    if not document_type.strip():
        missing.append("Document Type")
    if not parties.strip():
        missing.append("Parties Involved")
    if not terms.strip():
        missing.append("Terms & Conditions")
    if not dates.strip():
        missing.append("Effective Date")

    if missing:
        st.error("Please fill in: " + ", ".join(missing))
    else:
        # Field names match the DocumentRequest model in routes.py.
        payload = {
            "document_type": document_type.strip(),
            "parties": parties.strip(),
            "terms": terms.strip(),
            "dates": dates.strip(),
        }

        with st.spinner("Generating your document..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/generate",
                    json=payload,
                    timeout=180,  # LLM calls can be slow
                )
                if response.ok:
                    data = response.json()
                    # Keep results in session state so they survive reruns.
                    st.session_state["document_text"] = data["content"]
                    st.session_state["document_type"] = document_type.strip()
                    st.success("Document generated successfully.")
                else:
                    # Show the backend's "detail" message when available.
                    try:
                        detail = response.json().get("detail", response.text)
                    except Exception:
                        detail = response.text
                    st.error(f"Backend error ({response.status_code}): {detail}")
            except requests.RequestException as exc:
                # Backend not running, network error or timeout.
                st.error(
                    "Could not connect to FastAPI. Start the backend first with "
                    "`uvicorn main:app --reload`. Details: " + str(exc)
                )

# --- Preview, editing and downloads -----------------------------------------
if "document_text" in st.session_state:
    st.divider()
    st.subheader("Document Preview")

    # Rendered as HTML by the helper in utils/exporters.py.
    st.markdown(
        format_html_preview(st.session_state["document_text"]),
        unsafe_allow_html=True,
    )

    st.subheader("Edit Document")
    edited_text = st.text_area(
        "Click here to edit the generated document",
        value=st.session_state["document_text"],
        height=500,
        label_visibility="collapsed",
    )
    st.session_state["document_text"] = edited_text  # Downloads use the edited text

    current_text = st.session_state["document_text"]
    current_type = st.session_state.get("document_type", "Legal Document")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "Download TXT",
            data=format_txt(current_text),
            file_name="legalease_document.txt",
            mime="text/plain",
        )

    with col2:
        st.download_button(
            "Download DOCX",
            data=format_docx(
                current_text,
                current_type,
                str(LOGO_PATH) if LOGO_PATH.exists() else None,
            ),
            file_name="legalease_document.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    with col3:
        st.download_button(
            "Download PDF",
            data=format_pdf(
                current_text,
                current_type,
                str(LOGO_PATH) if LOGO_PATH.exists() else None,
            ),
            file_name="legalease_document.pdf",
            mime="application/pdf",
        )

# Shows which backend the UI is talking to (useful when debugging deployments).
st.caption(f"Backend: {BACKEND_URL}")
