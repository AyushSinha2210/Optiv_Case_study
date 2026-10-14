"""Integration endpoints for Ironclad, OneTrust, and Torii."""

import hashlib
import hmac
import json
import os
import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.cadence_tprm.config import settings
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
    contracts_count = db.query(Contract).count()
    return {
        "integrations": [
            {
                "id": "ironclad",
                "name": "Ironclad CLM Contract & Vendor Intake",
                "mode": "Live Webhook Configured" if settings.IRONCLAD_WEBHOOK_SECRET else "Unconfigured",
                "status": "Configured" if settings.IRONCLAD_WEBHOOK_SECRET else "Blocked: webhook secret missing",
                "synced_records": contracts_count,
                "endpoint": "POST /api/tprm/v1/integrations/ironclad/webhook",
            },
            {
                "id": "onetrust",
                "name": "OneTrust TPRM Configuration & Third-Party Exchange",
                "mode": "Live API Connected" if os.getenv("ONETRUST_API_KEY") else "Internal Adapter",
                "status": "Configured" if os.getenv("ONETRUST_API_KEY") else "Adapter only",
                "synced_records": contracts_count,
                "endpoint": "POST /api/tprm/v1/integrations/onetrust/sync/{vendor_id}",
            },
            {
                "id": "torii",
                "name": "Torii SaaS Deprovisioning & Asset Revocation",
                "mode": "Live API Connected" if settings.TORII_API_KEY else "Adapter only",
                "status": "Configured" if settings.TORII_API_KEY else "Blocked: API key missing",
                "synced_records": 0,
                "endpoint": "POST /api/tprm/v1/integrations/torii/revoke/{vendor_id}",
            },
        ]
    }


def _verify_ironclad_signature(body: bytes, signature: Optional[str], timestamp: Optional[str]) -> None:
    """Verify a fresh timestamped HMAC-SHA256 webhook signature."""
    secret = os.getenv("IRONCLAD_WEBHOOK_SECRET") or settings.IRONCLAD_WEBHOOK_SECRET
    if not secret:
        raise HTTPException(status_code=503, detail="Ironclad webhook is not configured.")
    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="Missing webhook signature.")
    try:
        timestamp_int = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid webhook timestamp.") from exc
    if abs(int(time.time()) - timestamp_int) > 300:
        raise HTTPException(status_code=401, detail="Expired webhook signature.")

    signed_payload = f"{timestamp}.".encode("utf-8") + body
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    provided = signature.removeprefix("sha256=")
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")


@router.post("/ironclad/webhook")
async def ironclad_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_ironclad_signature: Optional[str] = Header(None),
    x_ironclad_timestamp: Optional[str] = Header(None),
):
    """Receive only fresh, HMAC-authenticated Ironclad events."""
    body = await request.body()
    _verify_ironclad_signature(body, x_ironclad_signature, x_ironclad_timestamp)
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Webhook body must be valid JSON.") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook body must be a JSON object.")
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
