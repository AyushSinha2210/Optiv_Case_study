"""End-to-End API Integration Tests for Cadence TPRM Endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.cadence_tprm.main import app
from src.cadence_tprm.database import SessionLocal, Base, engine
from src.cadence_tprm.seed.seed_data import seed_database

client = TestClient(app)

def test_health_check_endpoints():
    res1 = client.get("/health")
    assert res1.status_code == 200
    assert res1.json()["status"] == "healthy"

    res2 = client.get("/api/health")
    assert res2.status_code == 200
    assert res2.json()["status"] == "healthy"

def test_auth_login_and_me():
    res = client.post("/api/tprm/v1/auth/login", json={"email": "daniela.figueroa@cadence.com"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["is_admin"] is True
    assert "Vendor Risk Management Group" in data["user"]["groups"]

    token = data["access_token"]
    me_res = client.get("/api/tprm/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == "daniela.figueroa@cadence.com"

def test_vendor_lifecycle_api_flow():
    # 1. Create a new vendor
    payload = {
        "name": "Integration Test Vendor Corp",
        "type": "Technology",
        "criticality": "Critical",
        "primary_vendor_contact": "poc@integtestcorp.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 1",
        "vendor_category": "Service Provider and Vendor",
        "website": "https://integtestcorp.com"
    }
    create_res = client.post("/api/tprm/v1/vendors", json=payload, headers={"X-User-Email": "daniela.figueroa@cadence.com"})
    assert create_res.status_code == 201
    v_data = create_res.json()
    vendor_id = v_data["vendor_id"]
    assert v_data["workflow"] == "CD_Service Providers Workflow"
    assert v_data["stage"] == "Launching ServPro"

    # 2. Retrieve vendor details
    get_res = client.get(f"/api/tprm/v1/vendors/{vendor_id}", headers={"X-User-Email": "daniela.figueroa@cadence.com"})
    assert get_res.status_code == 200
    details = get_res.json()
    assert len(details["assessments"]) >= 1
    assessment_id = details["assessments"][0]["id"]

    # 3. Save draft responses
    draft_res = client.post(
        f"/api/tprm/v1/assessments/{assessment_id}/responses",
        json={"responses": {"1.3": "Yes", "4.18": "Yes"}},
        headers={"X-User-Email": "poc@integtestcorp.com"}
    )
    assert draft_res.status_code == 200

    # 4. Departmental review by Security Group
    rev_res = client.post(
        f"/api/tprm/v1/assessments/{assessment_id}/reviews",
        json={"group_name": "Security Group", "notes": "Security posture verified.", "status": "Approved"},
        headers={"X-User-Email": "chris.ott@cadence.com"}
    )
    assert rev_res.status_code == 200

    # 5. Non-admin cannot approve (tamika.oliver is Edit only)
    unauth_approve = client.post(
        f"/api/tprm/v1/assessments/{assessment_id}/approve",
        json={"decision_reason": "Attempting unauthorized approval"},
        headers={"X-User-Email": "tamika.oliver@cadence.com"}
    )
    assert unauth_approve.status_code == 403

    # 6. Admin approves vendor (daniela.figueroa is Admin)
    approve_res = client.post(
        f"/api/tprm/v1/assessments/{assessment_id}/approve",
        json={"decision_reason": "Approved after comprehensive risk review"},
        headers={"X-User-Email": "daniela.figueroa@cadence.com"}
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["lifecycle_status"] == "Live"

def test_dashboard_reporting_endpoint():
    res = client.get("/api/tprm/v1/reports/summary", headers={"X-User-Email": "daniela.figueroa@cadence.com"})
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["total_vendors"] >= 1
    assert "assessments" in metrics
    assert "risk_findings" in metrics
    assert "vendors_by_category" in metrics

def test_ironclad_webhook_ingestion():
    webhook_payload = {
        "event_type": "contract.executed",
        "contract_id": "IC-TEST-2026-001",
        "contract_data": {
            "title": "MSA - Cloudflare Enterprise",
            "contract_reference": "IC-TEST-2026-001"
        },
        "vendor_data": {
            "name": "Cloudflare Global Services",
            "type": "Technology",
            "criticality": "Critical",
            "primary_vendor_contact": "enterprise@cloudflare.com",
            "business_owner": "rob.tilney@cadence.com",
            "vendor_tier": "Tier 1",
            "vendor_category": "Service Provider and Vendor",
            "website": "https://cloudflare.com"
        }
    }
    wh_res = client.post("/api/tprm/v1/integrations/ironclad/webhook", json=webhook_payload)
    assert wh_res.status_code == 200
    res_json = wh_res.json()
    assert res_json["status"] == "success"
    assert res_json["vendor_name"] == "Cloudflare Global Services"
