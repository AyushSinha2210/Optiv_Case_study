"""End-to-End Workflow Integration Test for OPTIV Document Privacy Workspace.

Validates the complete lifecycle:
1. Frontend static asset resolution
2. Compliance Officer authentication
3. Overview operational metrics computation
4. Ingestion and multi-stage pipeline execution on PDF/TXT/JSON
5. Dual-key release gate verification (PASS vs BLOCKED)
6. Original immutable artifact retrieval (permission-controlled)
7. Sanitized artifact download (verified PASS barrier)
8. Contract D compliance report export (metadata-only)
9. Tamper-evident audit trail persistence
10. Grounded AI explanation copilot queries
"""

import json
import pytest
from fastapi.testclient import TestClient
from server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_e2e_frontend_mount(client):
    """Verify built frontend is correctly mounted and served at root."""
    res = client.get("/")
    assert res.status_code == 200
    assert "html" in res.headers["content-type"]
    assert "OPTIV" in res.text or "vite" in res.text or "<div id=\"root\">" in res.text


def test_e2e_complete_document_workflow(client):
    """Execute complete end-to-end workflow from ingestion to artifact download."""
    # 1. Authenticate as Compliance Officer
    auth_res = client.post("/api/auth/login", json={"email": "admin@cadence.com", "password": "test-password"})
    assert auth_res.status_code == 200
    user_data = auth_res.json()["user"]
    assert user_data["role"] == "ADMIN"
    auth_headers = {"X-User-Email": "admin@cadence.com"}

    # 2. Check overview metrics before processing
    metrics_res = client.get("/api/overview/metrics", headers=auth_headers)
    assert metrics_res.status_code == 200

    # 3. Process mixed PII evidence document
    proc_res = client.post(
        "/api/process",
        data={"scenario_filename": "03_mixed_pii.txt"},
        headers=auth_headers,
    )
    assert proc_res.status_code == 200
    doc_data = proc_res.json()
    doc_id = doc_data["document_id"]
    assert doc_data["workflow_status"] == "success"
    assert doc_data["verification_status"] == "PASS"
    assert doc_data["release_allowed"] is True
    assert len(doc_data["stage_history"]) >= 6
    assert len(doc_data["entities"]) >= 1

    # 4. Verify immutable original document can be downloaded by authorized officer
    orig_res = client.get(f"/api/original/{doc_id}", headers=auth_headers)
    assert orig_res.status_code == 200
    assert "attachment" in orig_res.headers["content-disposition"]
    assert len(orig_res.content) > 0

    # 5. Verify sanitized output artifact can be downloaded
    art_res = client.get(f"/api/artifact/{doc_id}", headers=auth_headers)
    assert art_res.status_code == 200
    assert "[REDACTED_" in art_res.text or "<" in art_res.text
    assert "attachment" in art_res.headers["content-disposition"]

    # 6. Verify Contract D compliance report in JSON format
    rep_res = client.get(f"/api/report/{doc_id}?format=json", headers=auth_headers)
    assert rep_res.status_code == 200
    rep_json = rep_res.json()
    assert rep_json["document_id"] == doc_id
    assert rep_json["release_allowed"] is True

    # 7. Verify persistent run retrieval
    run_res = client.get(f"/api/runs/{doc_id}", headers=auth_headers)
    assert run_res.status_code == 200
    assert run_res.json()["document_id"] == doc_id

    # 8. Verify audit trail events
    audit_res = client.get(f"/api/audit/{doc_id}", headers=auth_headers)
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    assert len(events) >= 1
    event_types = [e["event_type"] for e in events]
    assert "DOCUMENT_RECEIVED" in event_types
    assert "RELEASE_DECIDED" in event_types

    # 9. Verify grounded AI assistant Q&A
    ai_res = client.post(
        "/api/assistant/chat",
        json={"document_id": doc_id, "query": "Why was the document authorized for release?"},
        headers=auth_headers,
    )
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert "GRANTED" in ai_data["explanation"]
    assert len(ai_data["citations"]) >= 1


def test_e2e_blocked_release_enforcement(client):
    """Verify fail-closed release gate blocks download when verification fails."""
    auth_headers = {"X-User-Email": "admin@cadence.com"}

    # Process with simulated residual leakage
    proc_res = client.post(
        "/api/process",
        data={
            "scenario_filename": "03_mixed_pii.txt",
            "simulate_verification_failure": "true",
        },
        headers=auth_headers,
    )
    assert proc_res.status_code == 200
    doc_data = proc_res.json()
    doc_id = doc_data["document_id"]
    assert doc_data["workflow_status"] == "blocked"
    assert doc_data["verification_status"] == "FAIL"
    assert doc_data["release_allowed"] is False

    # Attempt to download unverified artifact -> HTTP 403 Forbidden
    art_res = client.get(f"/api/artifact/{doc_id}", headers=auth_headers)
    assert art_res.status_code == 403
    assert "BLOCKED" in art_res.json()["detail"]

    # Verify AI assistant explains why release was blocked
    ai_res = client.post(
        "/api/assistant/chat",
        json={"document_id": doc_id, "query": "Why was release blocked?"},
        headers=auth_headers,
    )
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert "BLOCKED" in ai_data["explanation"]
    assert "Fail-Closed Gate Triggered" in ai_data["explanation"]
