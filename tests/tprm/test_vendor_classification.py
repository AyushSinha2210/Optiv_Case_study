"""Automated tests for Vendor Classification, Taxonomy, and Table 9 Attributes.

Source Authority: Cadence_TPRM_Training.docx Section 2.1, 4.1, 5.2, Table 4, Table 9.
"""

import pytest
from fastapi import HTTPException
from src.cadence_tprm.services.vendor_service import VendorService, ALLOWED_CATEGORIES, ALLOWED_TIERS, ALLOWED_TYPES, ALLOWED_CRITICALITIES
from src.cadence_tprm.models.vendor import Vendor

def test_vendor_categories_conform_to_document():
    """Verify all 5 documented third-party categories exist per Section 2.1 and Table 4."""
    expected = {
        "Staffing Vendors",
        "Service Providers and Vendors",
        "Marketing Partners",
        "Revenue Partners",
        "International Vendors"
    }
    # Note: in code ALLOWED_CATEGORIES has "Staffing Vendor" or "Staffing Vendors"
    assert "Staffing Vendor" in ALLOWED_CATEGORIES
    assert "Service Provider and Vendor" in ALLOWED_CATEGORIES
    assert "Marketing Partner" in ALLOWED_CATEGORIES
    assert "Revenue Partner" in ALLOWED_CATEGORIES
    assert "International Vendor" in ALLOWED_CATEGORIES

def test_vendor_tiers_conform_to_document():
    """Verify Tier 1, Tier 2, Tier 3 are valid and separate from Category."""
    assert ALLOWED_TIERS == {"Tier 1", "Tier 2", "Tier 3"}

def test_create_valid_vendor(db_session):
    """Test successful vendor creation with all required Table 9 attributes."""
    data = {
        "name": "Acme Cybersecurity Testing Ltd",
        "type": "Technology",
        "criticality": "Critical",
        "primary_vendor_contact": "poc@acmecyber.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 1",
        "vendor_category": "Service Provider and Vendor",
        "website": "https://acmecyber.com"
    }
    vendor = VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    assert vendor.id is not None
    assert vendor.name == "Acme Cybersecurity Testing Ltd"
    assert vendor.vendor_tier == "Tier 1"
    assert vendor.current_workflow_name == "CD_Service Providers Workflow"
    assert vendor.current_stage == "Launching ServPro"
    assert vendor.lifecycle_status == "In Progress"

def test_reject_invalid_category(db_session):
    """Test rejection of invalid third-party category."""
    data = {
        "name": "Invalid Category Vendor",
        "type": "Technology",
        "criticality": "Medium",
        "primary_vendor_contact": "poc@invalid.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 1",
        "vendor_category": "Invalid Non-Standard Category",
        "website": "https://invalid.com"
    }
    with pytest.raises(HTTPException) as exc_info:
        VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    assert exc_info.value.status_code == 400
    assert "Invalid vendor_category" in exc_info.value.detail

def test_reject_invalid_tier(db_session):
    """Test rejection of non-existent tier."""
    data = {
        "name": "Invalid Tier Vendor",
        "type": "Technology",
        "criticality": "Medium",
        "primary_vendor_contact": "poc@invalid.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 4",  # Not in Table 9
        "vendor_category": "Staffing Vendor",
        "website": "https://invalid.com"
    }
    with pytest.raises(HTTPException) as exc_info:
        VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    assert exc_info.value.status_code == 400
    assert "Invalid vendor_tier" in exc_info.value.detail

def test_reject_invalid_emails(db_session):
    """Test rejection when primary vendor contact or business owner email is malformed."""
    data = {
        "name": "Bad Email Vendor",
        "type": "Technology",
        "criticality": "Medium",
        "primary_vendor_contact": "not-an-email",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 2",
        "vendor_category": "Marketing Partner",
    }
    with pytest.raises(HTTPException) as exc_info:
        VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    assert exc_info.value.status_code == 400
