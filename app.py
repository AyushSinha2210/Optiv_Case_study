"""PII Guard — Enterprise Document Privacy & AI Governance Interface.

Built with Streamlit for Cadence Financial Group.
Enforces strict release gate barriers: Redacted artifact download is ONLY enabled
if independent post-redaction verification is strictly PASS and release is authorized.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import streamlit as st

from src.pii_guard.orchestration.pipeline import process_document
from src.pii_guard.orchestration.state import PipelineStage
from src.pii_guard.orchestration.artifacts import get_default_artifact_manager
from src.pii_guard.orchestration.errors import sanitize_error_message
from src.pii_guard.reporting.audit import get_global_audit_trail
from src.pii_guard.reporting.report_generator import generate_report, generate_human_readable_summary
from src.pii_guard.reporting.export import export_to_json

# Supported formats and security limits
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".pptx", ".txt", ".text"]
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


def validate_uploaded_file(uploaded_file) -> Tuple[bool, Optional[str]]:
    """Validate file type and size before committing to disk storage."""
    if uploaded_file is None:
        return False, "No file uploaded."

    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file extension '{suffix}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"

    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        return False, f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."

    if uploaded_file.size == 0:
        return False, "Uploaded file is 0 bytes (empty)."

    return True, None


def main():
    st.set_page_config(
        page_title="PII Guard — Cadence Financial Group",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🛡️ PII Guard: AI Governance & Data Protection Pipeline")
    st.caption("Cadence Financial Group — Cyber Strategy & Automated Redaction Release Gate")

    # Sidebar: Policy and Configuration
    with st.sidebar:
        st.header("📋 AI Governance Policy")
        st.markdown(
            """
            **Zero-Leakage Mandate:**
            - All business artifacts must be scanned and redacted before reaching downstream LLMs.
            - Artifact downloads are **blocked** unless independent re-scan verification returns **`PASS`**.
            - Audit logs and reports contain exclusively sanitized metadata.
            """
        )
        st.markdown("---")
        st.subheader("⚙️ Verification Gate Controls")
        sim_leakage = st.checkbox(
            "Simulate Verification Leakage (Test Blocked Gate)",
            value=False,
            help="Simulates finding residual PII during verification to demonstrate fail-closed release blocking.",
        )
        st.markdown("---")
        st.caption("Version: 1.0.0 | Member 5: Tirth & Member 4: Nancy")

    # Document Upload Section
    st.subheader("1. Document Ingestion & Validation")
    uploaded = st.file_uploader(
        "Upload document for PII analysis (PDF, DOCX, PPTX, TXT):",
        type=["pdf", "docx", "pptx", "txt"],
        help="Maximum file size: 50 MB.",
    )

    if uploaded is not None:
        is_valid, validation_err = validate_uploaded_file(uploaded)
        if not is_valid:
            st.error(f"❌ Validation Rejected: {validation_err}")
            return

        st.success(f"File validated: `{uploaded.name}` ({uploaded.size:,} bytes)")

        process_btn = st.button("🚀 Execute Protection Pipeline", type="primary")

        if process_btn:
            progress_bar = st.progress(0, text="Initializing pipeline...")
            status_box = st.empty()

            # Safe temporary file creation with guaranteed cleanup
            suffix = Path(uploaded.name).suffix.lower()
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_file.write(uploaded.getbuffer())

            try:
                progress_bar.progress(20, text="Ingesting & extracting document structure...")
                time_start = st.empty()

                options = {"simulate_verification_failure": sim_leakage}
                result = process_document(str(tmp_path), options=options)

                progress_bar.progress(100, text="Processing complete.")
                st.session_state["latest_result"] = result
                st.session_state["latest_filename"] = uploaded.name

            finally:
                # Guaranteed cleanup of uploaded temporary payload
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass

    # Results Display Section
    if "latest_result" in st.session_state:
        res = st.session_state["latest_result"]
        orig_name = st.session_state.get("latest_filename", "document")
        report = generate_report(res)

        st.markdown("---")
        st.subheader("2. Release Gate Decision & Processing Outcomes")

        # Prominent Release Gate Status Banner
        if res.workflow_status == "success" and res.release_allowed:
            st.success(
                f"### ✅ RELEASE AUTHORIZED\n"
                f"**Verification Status: PASS** — All detected PII was safely masked. Post-redaction re-scan detected 0 residual leaks."
            )
        elif res.workflow_status == "blocked":
            st.error(
                f"### 🛑 RELEASE BLOCKED (DOWNLOAD WITHHELD)\n"
                f"**Verification Status: FAIL** — Independent verification detected residual sensitive tokens or policy exception. "
                f"Client download is strictly disabled."
            )
        else:
            st.warning(
                f"### ⚠️ RELEASE INCOMPLETE\n"
                f"**Status: {res.workflow_status.upper()}** — Pipeline could not establish positive verification clearance."
            )

        # Operational Metrics Row
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Document ID", res.document_id)
        m2.metric("Source Format", (res.source_type or "unknown").upper())
        m3.metric("Pages / Slides", res.pages_count)
        m4.metric("Entities Detected", sum(res.category_counts.values()))
        m5.metric("Redactions Masked", res.redactions_applied)

        # Tabbed Details View
        tab_entities, tab_preview, tab_audit, tab_report = st.tabs(
            ["📊 Detected Categories", "👁️ Redacted Preview", "📜 Sanitized Audit Trail", "📑 Formal Report"]
        )

        with tab_entities:
            st.markdown("#### PII Breakdown by Classification Taxonomy")
            if res.category_counts:
                st.table([{"Category": k, "Count": v} for k, v in sorted(res.category_counts.items())])
            else:
                st.info("No PII entities detected in this document.")

        with tab_preview:
            st.markdown("#### Protected Artifact Content")
            if res.release_allowed and res.artifact_ref:
                art_mgr = get_default_artifact_manager()
                try:
                    content_bytes = art_mgr.read_artifact_bytes(
                        res.artifact_ref, res.document_id, res.release_allowed
                    )
                    st.text_area(
                        "Redacted Text (Masked View)",
                        value=content_bytes.decode("utf-8", errors="replace"),
                        height=280,
                        disabled=True,
                    )
                except Exception as ex:
                    st.error(f"Error loading artifact preview: {sanitize_error_message(str(ex))}")
            else:
                st.warning("⚠️ Preview disabled: Unverified or blocked documents cannot display output artifacts.")

        with tab_audit:
            st.markdown("#### Immutable Sanitized Audit Trail (Zero-Leakage)")
            trail = get_global_audit_trail()
            events = trail.export_sanitized_log(res.document_id)
            if events:
                st.dataframe(events, use_container_width=True)
            else:
                st.info("No audit events recorded.")

        with tab_report:
            st.markdown("#### Executive Summary & Contract D Metadata")
            summary_text = generate_human_readable_summary(report)
            st.code(summary_text, language="text")

        # Download Actions
        st.markdown("---")
        st.subheader("3. Export & Downloads")
        c_rep, c_art = st.columns(2)

        with c_rep:
            json_report = export_to_json(report)
            st.download_button(
                "📥 Download Sanitized Audit Report (JSON)",
                data=json_report,
                file_name=f"pii_guard_report_{res.document_id}.json",
                mime="application/json",
            )

        with c_art:
            if res.release_allowed and res.artifact_ref:
                art_mgr = get_default_artifact_manager()
                try:
                    artifact_data = art_mgr.read_artifact_bytes(
                        res.artifact_ref, res.document_id, res.release_allowed
                    )
                    ext = res.source_type if res.source_type in ("txt", "docx") else "txt"
                    st.download_button(
                        "📥 Download Approved Redacted Artifact",
                        data=artifact_data,
                        file_name=f"redacted_{orig_name}.{ext}",
                        mime="text/plain",
                    )
                except Exception:
                    st.button("📥 Download Approved Redacted Artifact (Unavailable)", disabled=True)
            else:
                st.button("🔒 Download Blocked (Verification Incomplete or Failed)", disabled=True)


if __name__ == "__main__":
    main()
