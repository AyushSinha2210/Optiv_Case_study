"""Unit tests for OPTIV Document Privacy & PII Protection Workspace endpoints."""

import json
import pytest
from fastapi.testclient import TestClient
from server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_overview_metrics(client):
    """GET /api/overview/metrics returns real computed metrics."""
    res = client.get("/api/overview/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "documents_received" in data
    assert "findings_detected" in data
    assert "verification_failures" in data
    assert "documents_approved_for_release" in data
    assert isinstance(data["documents_received"], int)


def test_auth_workflow(client):
    """Test user login, current user profile, and logout."""
    login_res = client.post("/api/auth/login", json={"email": "admin@cadence.com", "password": "test-password"})
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "token" in login_data
    assert login_data["user"]["role"] == "ADMIN"

    me_res = client.get("/api/auth/me", headers={"X-User-Email": "admin@cadence.com"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == "admin@cadence.com"

    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200


def test_settings_endpoints(client):
    """GET and POST /api/settings for governance configuration."""
    get_res = client.get("/api/settings")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["zero_leakage_mandate"] is True
    assert "supported_formats" in data

    post_res = client.post("/api/settings", json={"confidence_threshold": 0.55})
    assert post_res.status_code == 200
    assert post_res.json()["settings"]["confidence_threshold"] == 0.55


def test_json_document_processing(client, tmp_path):
    """Upload and process a synthetic JSON document."""
    json_content = {
        "account_id": "ACC-9921",
        "customer": {
            "name": "Evelyn Reed",
            "email": "evelyn.reed@cadence.com",
            "phone": "+1-212-555-0199",
            "ssn": "123-45-6789",
        },
        "status": "active"
    }
    json_file = tmp_path / "customer_record.json"
    json_file.write_text(json.dumps(json_content), encoding="utf-8")

    with open(json_file, "rb") as f:
        res = client.post(
            "/api/process",
            files={"file": ("customer_record.json", f, "application/json")},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["workflow_status"] == "success"
    assert data["verification_status"] == "PASS"
    assert data["release_allowed"] is True
    assert len(data["entities"]) >= 1

    doc_id = data["document_id"]

    # Verify run is persisted and retrievable via /api/runs/{doc_id}
    run_res = client.get(f"/api/runs/{doc_id}")
    assert run_res.status_code == 200
    assert run_res.json()["document_id"] == doc_id

    # Verify findings are queryable via /api/findings
    findings_res = client.get(f"/api/findings?document_id={doc_id}")
    assert findings_res.status_code == 200
    findings = findings_res.json()["findings"]
    assert len(findings) >= 1

    # Verify reviewing a finding
    f_id = findings[0]["id"]
    rev_res = client.post(f"/api/findings/{f_id}/review", json={"status": "MANUAL_REVIEW", "notes": "Audited"})
    assert rev_res.status_code == 200
    assert rev_res.json()["finding"]["status"] == "MANUAL_REVIEW"


def test_runs_and_audit_queries(client):
    """Test querying runs list and global audit ledger."""
    runs_res = client.get("/api/runs?limit=10")
    assert runs_res.status_code == 200
    assert "runs" in runs_res.json()

    audit_res = client.get("/api/audit?limit=20")
    assert audit_res.status_code == 200
    assert "events" in audit_res.json()
