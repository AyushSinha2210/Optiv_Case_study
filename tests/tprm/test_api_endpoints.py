"""End-to-End API Integration Tests for Cadence TPRM Endpoints (Lifecycle A through V)."""

import pytest
from fastapi.testclient import TestClient
from src.cadence_tprm.main import app

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

def test_organization_hierarchy_and_attribute_manager_endpoints():
    # Verify Organization -> Departments -> Groups -> Users -> Roles -> Permissions
    h_res = client.get("/api/tprm/v1/auth/hierarchy", headers={"X-User-Email": "daniela.figueroa@cadence.com"})
    assert h_res.status_code == 200
    h_data = h_res.json()
    assert h_data["organization"]["name"] == "Cadence Design Systems"
    assert len(h_data["departments"]) >= 9
    assert len(h_data["groups"]) >= 9
    assert len(h_data["roles"]) >= 4

    # Verify Attribute Manager inventory & protection against deactivating workflow driver attributes
    attr_res = client.get("/api/tprm/v1/vendors/attributes/inventory", headers={"X-User-Email": "daniela.figueroa@cadence.com"})
    assert attr_res.status_code == 200
    attrs = attr_res.json()["items"]
    assert len(attrs) >= 8
    tier_attr = next(a for a in attrs if a["key_name"] == "Vendor Tier")

    # Attempting to deactivate Vendor Tier (workflow driver) must fail with 400
    deact_res = client.put(
        f"/api/tprm/v1/vendors/attributes/inventory/{tier_attr['id']}",
        json={"is_active": False},
        headers={"X-User-Email": "daniela.figueroa@cadence.com"}
    )
    assert deact_res.status_code == 400

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

    # 7. Record renewal decision
    ren_res = client.post(
        f"/api/tprm/v1/vendors/{vendor_id}/renew",
        json={"decision": "Renewed", "rationale": "Annual reassessment satisfactory."},
        headers={"X-User-Email": "daniela.figueroa@cadence.com"}
    )
    assert ren_res.status_code == 200

    # 8. Offboard -> Close -> Archive lifecycle
    off_res = client.post(
        f"/api/tprm/v1/vendors/{vendor_id}/offboard",
        json={"reason": "Contract completed."},
        headers={"X-User-Email": "daniela.figueroa@cadence.com"}
    )
    assert off_res.status_code == 200

    close_res = client.post(
        f"/api/tprm/v1/vendors/{vendor_id}/close",
        headers={"X-User-Email": "daniela.figueroa@cadence.com"}
    )
    assert close_res.status_code == 200
    assert close_res.json()["stage"] == "Closed"

    arch_res = client.post(
        f"/api/tprm/v1/vendors/{vendor_id}/archive",
        headers={"X-User-Email": "daniela.figueroa@cadence.com"}
    )
    assert arch_res.status_code == 200
    assert arch_res.json()["is_archived"] is True

def test_questionnaire_versioning_and_csv_export():
    # Method B versioning
    ver_res = client.post(
        "/api/tprm/v1/questionnaires/templates/T1-2_v1/version",
        json={"method": "B"},
        headers={"X-User-Email": "daniela.figueroa@cadence.com"}
    )
    assert ver_res.status_code == 200
    assert ver_res.json()["version"] >= 2

    # CSV export
    csv_res = client.get(
        "/api/tprm/v1/questionnaires/templates/T1-2_v1/export-csv",
        headers={"X-User-Email": "daniela.figueroa@cadence.com"}
    )
    assert csv_res.status_code == 200
    assert "Contracting and Legal" in csv_res.text

def test_dashboard_reporting_and_export_endpoint():
    res = client.get("/api/tprm/v1/reports/summary", headers={"X-User-Email": "daniela.figueroa@cadence.com"})
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["total_vendors"] >= 1
    assert "assessments" in metrics
    assert "risk_findings" in metrics
    assert "vendors_by_category" in metrics

    exp_res = client.get("/api/tprm/v1/reports/export/vendors", headers={"X-User-Email": "daniela.figueroa@cadence.com"})
    assert exp_res.status_code == 200
    assert "Apex Cloud Infrastructure Ltd" in exp_res.text

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
