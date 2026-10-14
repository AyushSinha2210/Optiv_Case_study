"""Integration adapters for Ironclad CLM, OneTrust TPRM, and Torii SaaS Offboarding.

Source Authority: Cadence_TPRM_Training.docx Section 2.2, 3.0, 5.1, 4.2.3.
"""

import json
from typing import Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.cadence_tprm.models.vendor import Vendor, Contract
from src.cadence_tprm.services.vendor_service import VendorService
from src.cadence_tprm.services.audit_service import AuditService

class IntegrationService:

    @staticmethod
    def process_ironclad_webhook(db: Session, payload: dict, actor_email: str = "ironclad-system@cadence.com") -> dict:
        """Processes Ironclad contract creation/execution events and ingests vendor attributes (Table 9)."""
        contract_data = payload.get("contract_data", {})
        vendor_data = payload.get("vendor_data", {})
        contract_ref = contract_data.get("contract_reference") or payload.get("contract_id", "IC-UNASSIGNED")

        vendor_name = vendor_data.get("name")
        if not vendor_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing vendor_data.name in Ironclad payload.")

        # Check if vendor already exists
        vendor = db.query(Vendor).filter_by(name=vendor_name.strip()).first()
        if not vendor:
            # Create new vendor using Table 9 attributes
            create_payload = {
                "name": vendor_name.strip(),
                "type": vendor_data.get("type", "Technology"),
                "criticality": vendor_data.get("criticality", "Medium"),
                "primary_vendor_contact": vendor_data.get("primary_vendor_contact", "pvc@vendor.com"),
                "business_owner": vendor_data.get("business_owner", "business.owner@cadence.com"),
                "vendor_tier": vendor_data.get("vendor_tier", "Tier 2"),
                "vendor_category": vendor_data.get("vendor_category", "Service Provider and Vendor"),
                "website": vendor_data.get("website", ""),
            }
            vendor = VendorService.create_vendor(db, create_payload, actor_email=actor_email)
            action_type = "VENDOR_CREATED_VIA_IRONCLAD"
        else:
            action_type = "VENDOR_UPDATED_VIA_IRONCLAD"

        # Record or update contract
        contract = db.query(Contract).filter_by(contract_reference=contract_ref).first()
        if not contract:
            contract = Contract(
                vendor_id=vendor.id,
                contract_reference=contract_ref,
                title=contract_data.get("title", f"Agreement with {vendor.name}"),
                source="Ironclad",
                status="Executed" if payload.get("event_type") == "contract.executed" else "Draft",
                details=json.dumps({
                    "event_type": payload.get("event_type"),
                    "contract_reference": contract_ref,
                    "source": "Ironclad",
                })
            )
            db.add(contract)
            db.commit()

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action=action_type,
            entity_type="INTEGRATION",
            entity_id=vendor.id,
            details={
                "contract_reference": contract_ref,
                "event_type": payload.get("event_type"),
                "source": "Ironclad",
            }
        )

        return {
            "status": "success",
            "vendor_id": vendor.id,
            "vendor_name": vendor.name,
            "contract_reference": contract_ref,
            "lifecycle_status": vendor.lifecycle_status,
            "current_stage": vendor.current_stage
        }

    @staticmethod
    def sync_to_onetrust(db: Session, vendor_id: str) -> dict:
        """Formats vendor and risk posture payload for OneTrust synchronization."""
        vendor = db.query(Vendor).filter_by(id=vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found.")

        payload = {
            "vendor_name": vendor.name,
            "category": vendor.vendor_category,
            "tier": vendor.vendor_tier,
            "lifecycle_status": vendor.lifecycle_status,
            "stage": vendor.current_stage,
            "primary_contact": vendor.primary_vendor_contact,
            "business_owner": vendor.business_owner,
            "open_findings_count": len([f for f in vendor.findings if f.status == "Open"]),
            "synced_at": datetime.now(timezone.utc).isoformat()
        }

        AuditService.log_event(
            db,
            actor_email="system@cadence.com",
            action="ONETRUST_SYNC",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details=payload
        )

        return {"status": "synced", "onetrust_payload": payload}

    @staticmethod
    def revoke_via_torii(db: Session, vendor_id: str, actor_email: str) -> dict:
        """Simulates Torii asset revocation adapter for offboarding per Section 4.2.3."""
        vendor = db.query(Vendor).filter_by(id=vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found.")

        # Simulate revoking associated SaaS seats and credentials
        revocation_details = {
            "vendor_name": vendor.name,
            "revoked_seats": 5,
            "revoked_tokens": 2,
            "sso_integrations_disabled": ["Okta", "Google Workspace"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "Simulated Adapter (Production Torii API Key Pending)"
        }

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="TORII_ASSET_REVOCATION",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details=revocation_details
        )

        return {"status": "assets_revoked", "details": revocation_details}
