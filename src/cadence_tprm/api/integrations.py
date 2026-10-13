"""Integration endpoints for Ironclad, OneTrust, and Torii."""

import os
from typing import Dict, Any
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.vendor import Contract
from src.cadence_tprm.services.integration_service import IntegrationService
from src.cadence_tprm.services.auth_service import get_current_user, require_tprm_admin

router = APIRouter(prefix="/integrations", tags=["Integrations"])

@router.get("/status")
def get_integrations_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Returns transparent status of external integrations vs local development adapters (Section 1.3-1.5, 21)."""
    contracts_count = db.query(Contract).count()
    return {
        "integrations": [
            {
                "id": "ironclad",
                "name": "Ironclad CLM Contract & Vendor Intake",
                "role": "Primary entry point for New Vendor Request Form and Contract Submission Form (Section 1.4, 5.1)",
                "direction": "Inbound: Ironclad -> Cadence TPRM (Table 9 Attributes)",
                "mode": "Live Webhook Configured" if os.getenv("IRONCLAD_WEBHOOK_SECRET") else "Development Adapter (Local Webhook Active)",
                "status": "Operational (Local Adapter)",
                "synced_records": contracts_count,
                "endpoint": "POST /api/tprm/v1/integrations/ironclad/webhook",
            },
            {
                "id": "onetrust",
                "name": "OneTrust TPRM Configuration & Third-Party Exchange",
                "role": "Authoritative workflow, DDQ, SLA, and risk rule specification engine (Section 1.3, 6.0)",
                "direction": "Internal Workflow Engine + Outbound Sync Adapter",
                "mode": "Live API Connected" if os.getenv("ONETRUST_API_KEY") else "Internal Standalone Engine + Local Sync Adapter",
                "status": "Operational (Internal Engine)",
                "synced_records": contracts_count,
                "endpoint": "POST /api/tprm/v1/integrations/onetrust/sync/{vendor_id}",
            },
            {
                "id": "torii",
                "name": "Torii SaaS Deprovisioning & Asset Revocation",
                "role": "Proposed future enhancement for API-triggered deprovisioning during offboarding (Section 1.5, 4.2.3)",
                "direction": "Outbound: Cadence TPRM -> Torii API",
                "mode": "Live API Connected" if os.getenv("TORII_API_KEY") else "Simulated Future Capability Adapter (Pending Production API Key)",
                "status": "Pending Future Capability (Simulated Adapter)",
                "synced_records": 0,
                "endpoint": "POST /api/tprm/v1/integrations/torii/revoke/{vendor_id}",
            },
            {
                "id": "email_smtp",
                "name": "External Email Delivery (SMTP / SendGrid)",
                "role": "Dispatches 'Vendor Upcoming Re-Assessment' and SLA reminder emails (Section 17, 20)",
                "direction": "Outbound Email",
                "mode": "Live SMTP Connected" if os.getenv("SMTP_HOST") else "In-App Notification Center Active (External SMTP Unconfigured)",
                "status": "In-App Active (SMTP Unconfigured)",
                "synced_records": 0,
                "endpoint": "GET /api/tprm/v1/tasks/notifications",
            },
        ]
    }

@router.post("/ironclad/webhook")
def ironclad_webhook(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Public or HMAC-gated webhook receiver for Ironclad contract lifecycle events."""
    return IntegrationService.process_ironclad_webhook(db, payload)

@router.post("/onetrust/sync/{vendor_id}")
def sync_onetrust(
    vendor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    return IntegrationService.sync_to_onetrust(db, vendor_id)

@router.post("/torii/revoke/{vendor_id}")
def torii_revoke(
    vendor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    return IntegrationService.revoke_via_torii(db, vendor_id, actor_email=current_user["email"])
