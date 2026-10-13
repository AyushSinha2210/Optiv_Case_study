"""Unit tests for FastAPI HTTP API server adapter (server.py)."""

import pytest
from fastapi.testclient import TestClient
from server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_health_check(client):
    """GET /api/health returns healthy service status and pipeline stages."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "pipeline_stages" in data
    assert "RECEIVED" in data["pipeline_stages"]
    assert "RELEASED" in data["pipeline_stages"]


def test_api_list_scenarios(client):
    """GET /api/scenarios returns list of certified deterministic demo scenarios."""
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) >= 7
    first = data["scenarios"][0]
    assert "filename" in first
    assert "file_type" in first


def test_api_process_valid_scenario(client):
    """POST /api/process executes pipeline and returns full telemetry and entities."""
    res = client.post("/api/process", data={"scenario_filename": "03_mixed_pii.txt"})
    assert res.status_code == 200
    data = res.json()
    assert data["workflow_status"] == "success"
    assert data["verification_status"] == "PASS"
    assert data["release_allowed"] is True
    assert len(data["stage_history"]) >= 6
    assert len(data["entities"]) >= 1
    assert data["artifact_ref"] is not None

    # Test downloading approved artifact
    doc_id = data["document_id"]
    art_res = client.get(f"/api/artifact/{doc_id}")
    assert art_res.status_code == 200
    assert "[REDACTED_" in art_res.text or "<" in art_res.text


def test_api_process_simulated_leakage_blocks_release(client):
    """POST /api/process with simulate_verification_failure returns blocked release gate."""
    res = client.post(
        "/api/process",
        data={
            "scenario_filename": "03_mixed_pii.txt",
            "simulate_verification_failure": "true",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["workflow_status"] == "blocked"
    assert data["verification_status"] == "FAIL"
    assert data["release_allowed"] is False
    assert data["safe_error"] is not None

    # Test downloading blocked artifact returns 403 Forbidden
    doc_id = data["document_id"]
    art_res = client.get(f"/api/artifact/{doc_id}")
    assert art_res.status_code == 403
    assert "BLOCKED" in art_res.json()["detail"]


def test_api_report_and_audit(client):
    """GET /api/report and /api/audit return compliant metadata-only exports."""
    # First process a document
    res = client.post("/api/process", data={"scenario_filename": "01_synthetic_email.txt"})
    doc_id = res.json()["document_id"]

    # Test JSON report
    rep_res = client.get(f"/api/report/{doc_id}?format=json")
    assert rep_res.status_code == 200
    assert rep_res.headers["content-type"] == "application/json"

    # Test summary report
    sum_res = client.get(f"/api/report/{doc_id}?format=summary")
    assert sum_res.status_code == 200
    assert "CADENCE FINANCIAL GROUP" in sum_res.text

    # Test audit ledger
    aud_res = client.get(f"/api/audit/{doc_id}")
    assert aud_res.status_code == 200
    events = aud_res.json()["events"]
    assert len(events) >= 1


def test_api_assistant_chat(client):
    """POST /api/assistant/chat returns dynamic contextual security explanations."""
    res = client.post("/api/process", data={"scenario_filename": "03_mixed_pii.txt"})
    doc_id = res.json()["document_id"]

    chat_res = client.post(
        "/api/assistant/chat",
        json={"document_id": doc_id, "query": "Why was release authorized?"},
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "explanation" in chat_data
    assert len(chat_data["citations"]) >= 1
