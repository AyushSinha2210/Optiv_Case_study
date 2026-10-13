"""Integration endpoints for Ironclad, OneTrust, and Torii."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.services.integration_service import IntegrationService
from src.cadence_tprm.services.auth_service import get_current_user, require_tprm_admin

router = APIRouter(prefix="/integrations", tags=["Integrations"])

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
