"""PII Guard — Enterprise Document Privacy & AI Governance Interface.

Built with Streamlit for Cadence Financial Group.
Enforces strict release gate barriers: Redacted artifact download is ONLY enabled
if independent post-redaction verification is strictly PASS and release is authorized.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

try:
    import streamlit as st
except ImportError:
    st = None

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

# Pre-configured demonstration scenarios mapped to repo fixtures
DEMO_FIXTURES_DIR = Path(__file__).resolve().parent / "demo_samples" / "fixtures"

DEMO_SCENARIOS = {
    "1. Single Category PII (Email Notice)": {
        "file": "01_synthetic_email.txt",
        "description": "Customer notice containing a single synthetic EMAIL_ADDRESS entity.",
        "expected": "PASS / RELEASED (1 Email masked)",
    },
    "2. Multi-Category PII (Wire Transfer & Loan)": {
        "file": "03_mixed_pii.txt",
        "description": "Cadence Financial document containing mixed SSN, Email, Phone, Credit Card, and IP address.",
        "expected": "PASS / RELEASED (Multi-category entities masked)",
    },
    "3. Benign Document (Clean / Zero PII)": {
        "file": "04_clean_no_pii.txt",
        "description": "Public financial market commentary with zero detectable PII entities.",
        "expected": "PASS / RELEASED (0 PII detected, 0 redactions)",
    },
    "4. Repeated Entities (Recurring SSNs & Names)": {
        "file": "05_repeated_entities.txt",
        "description": "Audit document containing repeated occurrences of the same SSN and account tokens.",
        "expected": "PASS / RELEASED (All occurrences masked right-to-left)",
    },
    "5. Complex Layout DOCX (Mortgage Application)": {
        "file": "06_multi_category.docx",
        "description": "Word DOCX format document with interleaved paragraphs and sensitive data.",
        "expected": "PASS / RELEASED (DOCX adapter layout preserved)",
    },
    "6. International & Unicode Formats": {
        "file": "07_unicode_international.txt",
        "description": "Multilingual document containing Indian PAN cards, international phones, and Unicode accents.",
        "expected": "PASS / RELEASED (NFC-normalized unicode preservation)",
    },
    "7. Security Boundary: Empty Document (0 Bytes)": {
        "file": "08_empty_document.txt",
        "description": "Zero-byte file payload to validate fail-closed input rejection.",
        "expected": "VALIDATION REJECTED (Zero bytes)",
    },
    "8. Security Boundary: Unsupported Binary (.xyz)": {
        "file": "10_malformed_binary.xyz",
        "description": "Arbitrary unsupported binary file to test extension sniffing and validation.",
        "expected": "VALIDATION REJECTED (Unsupported extension)",
    },
    "9. Quarterly Client Briefing (PowerPoint PPTX)": {
        "file": "11_quarterly_briefing.pptx",
        "description": "PowerPoint presentation with slides, tables, and speaker notes containing synthetic PII.",
        "expected": "PASS / RELEASED (PPTX slides, tables, and notes parsed)",
    },
    "10. Wealth Management Statement (Digital PDF)": {
        "file": "13_wealth_management_portfolio.pdf",
        "description": "Multi-page digital PDF statement with customer details, taxpayer IDs, and compliance officer contacts.",
        "expected": "PASS / RELEASED (PDF layout, tables, and PII masked)",
    },
    "11. Commercial Credit Agreement (Rich DOCX)": {
        "file": "16_commercial_loan_agreement.docx",
        "description": "Multi-section Word credit agreement with borrower SSN and guarantor contact tables.",
        "expected": "PASS / RELEASED (DOCX multi-section document redacted)",
    },
    "12. Clean Architecture Presentation (PPTX - 0 PII)": {
        "file": "12_clean_presentation.pptx",
        "description": "Clean technical presentation with zero personal identifiers.",
        "expected": "PASS / RELEASED (0 PII detected, 0 redactions)",
    },
    "13. Clean Governance Whitepaper (PDF - 0 PII)": {
        "file": "14_clean_whitepaper.pdf",
        "description": "Clean multi-page PDF whitepaper with zero personal identifiers.",
        "expected": "PASS / RELEASED (0 PII detected, 0 redactions)",
    },
}


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
    if st is None:
        raise ImportError("Streamlit is required to launch the interactive UI: pip install streamlit")

    st.set_page_config(
        page_title="PII Guard — Cadence Financial Group",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🛡️ PII Guard: AI Governance & Data Protection Pipeline")
    st.caption("Cadence Financial Group — Cyber Strategy & Automated Redaction Release Gate")

    # Sidebar: Policy, Mode Selection, and Controls
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
        st.subheader("🎯 Execution Mode")
        input_mode = st.radio(
            "Select input source:",
            ["🧪 Pre-built Demo Scenarios", "📁 Custom File Upload"],
            index=0,
        )

        st.markdown("---")
        st.subheader("⚙️ Verification Gate Controls")
        sim_leakage = st.checkbox(
            "Simulate Verification Leakage (Test Blocked Gate)",
            value=False,
            help="Simulates finding residual PII during verification to demonstrate fail-closed release blocking.",
        )
        st.markdown("---")
        st.caption("Version: 1.0.0 | Enterprise Security Integration | Cadence Financial Group")

    # Document Selection & Input Processing
    file_bytes: Optional[bytes] = None
    file_name: Optional[str] = None

    if input_mode == "🧪 Pre-built Demo Scenarios":
        st.subheader("1. Deterministic Demonstration Scenario")
        selected_scenario_name = st.selectbox(
            "Choose a certified demonstration scenario:",
            list(DEMO_SCENARIOS.keys()),
            index=1,  # Default to mixed PII
        )
        scenario_meta = DEMO_SCENARIOS[selected_scenario_name]
        fixture_path = DEMO_FIXTURES_DIR / scenario_meta["file"]

        st.info(
            f"**Scenario:** {scenario_meta['description']}\n\n"
            f"**Fixture File:** `{scenario_meta['file']}` | **Expected Outcome:** {scenario_meta['expected']}"
        )

        if fixture_path.exists():
            file_bytes = fixture_path.read_bytes()
            file_name = scenario_meta["file"]
        else:
            st.error(f"Fixture file not found: `{fixture_path}`")

    else:
        st.subheader("1. Document Ingestion & Validation")
        uploaded = st.file_uploader(
            "Upload document for PII analysis (PDF, DOCX, PPTX, TXT):",
            type=["pdf", "docx", "pptx", "txt"],
            help="Maximum file size: 50 MB.",
        )
        if uploaded is not None:
            file_bytes = uploaded.getvalue()
            file_name = uploaded.name

    if file_bytes is not None and file_name is not None:
        # Mock uploaded file object for validate_uploaded_file compatibility
        class _UploadProxy:
            def __init__(self, name: str, size: int):
                self.name = name
                self.size = size

        proxy = _UploadProxy(file_name, len(file_bytes))
        is_valid, validation_err = validate_uploaded_file(proxy)

        if not is_valid:
            st.error(f"❌ Input Validation Failed (Security Boundary): {validation_err}")
            st.caption("The fail-closed ingestion gate halted execution before processing.")
            return

        st.success(f"File validated: `{file_name}` ({len(file_bytes):,} bytes)")

        process_btn = st.button("🚀 Execute Protection Pipeline", type="primary")

        if process_btn:
            progress_bar = st.progress(0, text="Initializing pipeline...")

            # Safe temporary file creation with guaranteed cleanup
            suffix = Path(file_name).suffix.lower()
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_file.write(file_bytes)

            try:
                progress_bar.progress(20, text="Ingesting & extracting document structure...")
                options = {"simulate_verification_failure": sim_leakage}
                result = process_document(str(tmp_path), options=options)

                progress_bar.progress(100, text="Processing complete.")
                st.session_state["latest_result"] = result
                st.session_state["latest_filename"] = file_name

            finally:
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
        m1.metric("Document ID", res.document_id[:8] + "...")
        m2.metric("Source Format", (res.source_type or "unknown").upper())
        m3.metric("Pages / Slides", res.pages_count)
        m4.metric("Entities Detected", sum(res.category_counts.values()))
        m5.metric("Redactions Masked", res.redactions_applied)

        # Tabbed Details View
        tab_timeline, tab_entities, tab_preview, tab_audit, tab_report = st.tabs(
            [
                "⏱️ Stage Execution Timeline",
                "📊 Detected Categories",
                "👁️ Redacted Preview",
                "📜 Sanitized Audit Trail",
                "📑 Formal Report",
            ]
        )

        with tab_timeline:
            st.markdown("#### Real Pipeline Stage Transitions & Durations")
            st.caption("Recorded in real-time by `PipelineStateManager` across all 7 lifecycle stages.")

            if res.stage_history:
                timeline_rows = []
                prev_time = res.started_at
                for idx, t in enumerate(res.stage_history):
                    step_dt = t.timestamp
                    duration_s = max(0.0, (step_dt - prev_time).total_seconds())
                    timeline_rows.append({
                        "Step": idx + 1,
                        "From Stage": t.from_stage.value if t.from_stage else "INITIAL",
                        "To Stage": t.to_stage.value,
                        "Timestamp (UTC)": step_dt.strftime("%H:%M:%S.%f")[:-3],
                        "Stage Duration": f"{duration_s:.3f}s",
                        "Message": t.message or "Stage completed",
                    })
                    prev_time = step_dt

                st.table(timeline_rows)
            else:
                st.info("No stage transition records available.")

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
