from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

from services.exporters import (
    format_docx,
    format_html_preview,
    format_pdf,
    format_txt,
    sanitize_text,
)


# --------------------------------------------------
# PATHS AND ENVIRONMENT
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

LOGO_PATH = BASE_DIR / "assets" / "legalese_logo.png"

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="LegalEase",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
    .legal-card {
        background: #111827;
        border: 1px solid #374151;
        border-radius: 14px;
        padding: 22px;
        max-height: 560px;
        overflow-y: auto;
        color: #f9fafb;
    }

    .legal-card p {
        line-height: 1.65;
    }

    .legal-card .legal-heading {
        color: #93c5fd;
        margin-top: 20px;
    }

    .small-note {
        color: #6b7280;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""

if "model" not in st.session_state:
    st.session_state.model = ""

if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    # Show logo only if it is a valid image.
    try:
        if LOGO_PATH.is_file():
            st.image(
                str(LOGO_PATH),
                width=180,
            )
        else:
            st.markdown("## ⚖️ LegalEase")

    except Exception:
        st.markdown("## ⚖️ LegalEase")

    st.markdown("### LegalEase")

    st.caption(
        "AI-powered legal document drafting"
    )

    st.info(
        "Drafts are for informational and "
        "drafting purposes. Review important "
        "documents with a qualified legal "
        "professional."
    )


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    """
    <h1 style="text-align:center;">
        LegalEase
    </h1>

    <p style="text-align:center;">
        AI Legal Document Generator
    </p>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# INPUT FORM
# --------------------------------------------------

with st.form("document_form"):

    document_type = st.selectbox(
        "Document Type",
        [
            "Employment Contract",
            "Non-Disclosure Agreement",
            "Lease Agreement",
            "Freelance Work Contract",
            "Service Agreement",
            "General Agreement",
        ],
    )

    parties = st.text_area(
        "Parties Involved",
        placeholder=(
            "Jane Doe (Service Provider), "
            "TechNova Inc. (Client)"
        ),
        height=100,
    )

    terms = st.text_area(
        "Terms & Conditions",
        placeholder=(
            "Payment to be made within "
            "30 days of invoice; "
            "Confidentiality must be maintained; "
            "Either party may terminate "
            "with 15 days notice"
        ),
        height=150,
    )

    dates = st.text_input(
        "Effective Date",
        value=date.today().isoformat(),
    )

    submitted = st.form_submit_button(
        "✨ Generate Document",
        use_container_width=True,
        type="primary",
    )


# --------------------------------------------------
# GENERATE DOCUMENT
# --------------------------------------------------

if submitted:

    if (
        not parties.strip()
        or not terms.strip()
        or not dates.strip()
    ):

        st.error(
            "Please complete Parties, "
            "Terms & Conditions, "
            "and Effective Date."
        )

    else:

        payload = {
            "document_type": document_type,
            "parties": parties.strip(),
            "terms": terms.strip(),
            "dates": dates.strip(),
        }

        with st.spinner(
            "Generating your document..."
        ):

            try:

                response = requests.post(
                    f"{BACKEND_URL}/generate",
                    json=payload,
                    timeout=180,
                )

                if response.ok:

                    data = response.json()

                    st.session_state.generated_text = (
                        data["document"]
                    )

                    st.session_state.model = (
                        data.get("model", "")
                    )

                    st.session_state.demo_mode = (
                        data.get("demo_mode", False)
                    )

                    st.success(
                        "Document generated successfully."
                    )

                else:

                    try:
                        detail = (
                            response.json().get(
                                "detail",
                                response.text,
                            )
                        )

                    except Exception:
                        detail = response.text

                    st.error(
                        f"Backend error "
                        f"({response.status_code}): "
                        f"{detail}"
                    )

            except requests.RequestException as exc:

                st.error(
                    f"Could not connect to the "
                    f"FastAPI backend at "
                    f"{BACKEND_URL}. "
                    f"Details: {exc}"
                )


# --------------------------------------------------
# DOCUMENT PREVIEW
# --------------------------------------------------

if st.session_state.generated_text:

    st.divider()

    st.subheader("Document Generated")

    if st.session_state.demo_mode:

        st.warning(
            "Demo mode is active. "
            "This draft was not generated by Gemini."
        )

    st.caption(
        f"Model: "
        f"{st.session_state.model or 'unknown'}"
    )

    preview = format_html_preview(
        st.session_state.generated_text
    )

    st.markdown(
        f"""
        <div class="legal-card">
            {preview}
        </div>
        """,
        unsafe_allow_html=True,
    )


    # --------------------------------------------------
    # EDIT DOCUMENT
    # --------------------------------------------------

    st.subheader("Edit Document")

    edited_text = st.text_area(
        "Edit the generated document below:",
        value=st.session_state.generated_text,
        height=500,
        key="edited_document",
    )

    st.session_state.generated_text = (
        sanitize_text(edited_text)
    )


    # --------------------------------------------------
    # DOWNLOADS
    # --------------------------------------------------

    st.subheader("Download")

    col1, col2, col3 = st.columns(3)

    safe_name = "".join(
        c.lower() if c.isalnum() else "_"
        for c in document_type
    ).strip("_")

    if not safe_name:
        safe_name = "legal_document"


    with col1:

        st.download_button(
            "⬇️ Download TXT",
            data=format_txt(
                st.session_state.generated_text
            ),
            file_name=f"{safe_name}.txt",
            mime="text/plain",
            use_container_width=True,
        )


    with col2:

        st.download_button(
            "⬇️ Download DOCX",
            data=format_docx(
                st.session_state.generated_text,
                document_type,
            ),
            file_name=f"{safe_name}.docx",
            mime=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            use_container_width=True,
        )


    with col3:

        st.download_button(
            "⬇️ Download PDF",
            data=format_pdf(
                st.session_state.generated_text,
                document_type,
            ),
            file_name=f"{safe_name}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown(
    """
    <p class="small-note">
        LegalEase does not provide legal advice.
        Verify names, dates, amounts, jurisdiction,
        and all clauses before use.
    </p>
    """,
    unsafe_allow_html=True,
)