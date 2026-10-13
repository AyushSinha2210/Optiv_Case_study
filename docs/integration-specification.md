# Integration Specification: Cadence TPRM Application

**Authority:** `Cadence_TPRM_Training.docx` Sections 2.2, 3.0, 5.1, 4.2.3  

---

## 1. External System Integrations Overview

The Cadence TPRM architecture interfaces with three enterprise platforms:

```
[ Ironclad CLM ]               [ OneTrust TPRM ]              [ Torii SaaS Mgmt ]
Contract Execution            Central Risk Posture           Deprovisioning
       |                              |                              |
       v (Webhook)                    v (Sync API)                   v (Adapter)
+--------------------------------------------------------------------------------+
|                           CADENCE TPRM PLATFORM                                |
|  - Ingestion Webhook         - OneTrust State Sync         - Offboarding Deprov|
+--------------------------------------------------------------------------------+
```

---

## 2. Ironclad Contract Lifecycle Management (CLM) Integration

### Purpose
Contract creation and execution in Ironclad triggers vendor onboarding and due diligence workflows in Cadence TPRM automatically.

### Ingestion Contract (Table 9 Mapping)
```json
{
  "event_type": "contract.executed",
  "contract_id": "IC-CAD-2026-9941",
  "contract_name": "Master Services Agreement - Global Tech",
  "vendor_data": {
    "name": "Global Tech Services Inc",
    "type": "Technology",
    "criticality": "Critical",
    "primary_vendor_contact": "poc@globaltech.com",
    "business_owner": "owner@cadence.com",
    "vendor_tier": "Tier 1",
    "vendor_category": "Service Provider and Vendor",
    "website": "https://globaltech.com"
  }
}
```

### Ingestion Pipeline Logic
1. Webhook endpoint `/api/tprm/v1/integrations/ironclad/webhook` receives payload.
2. Validates HMAC signature (if secret configured) or development token.
3. Checks for existing vendor by name / primary contact / contract ID (idempotent upsert).
4. Inserts `contracts` record.
5. Fires `Vendor Created` event into `CD_Onboarding Workflow`.
6. Evaluates `WR.ON.*` rules to assign specific category workflow and launch assessment.

---

## 3. OneTrust TPRM State Synchronization

### Purpose
Allows bidirectional metadata exchange and alignment between Cadence internal operations and OneTrust cloud instances.

### Payload Schema
```json
{
  "vendor_id": "v-1",
  "onetrust_inventory_id": "OT-INV-84920",
  "risk_tier": "Tier 1",
  "assessment_status": "In Review",
  "overall_score": 78.5,
  "high_risks_count": 2,
  "last_synced_at": "2026-09-16T12:00:00Z"
}
```

---

## 4. Torii Offboarding & Asset Revocation Adapter

### Purpose
Section 4.2.3 notes: *"For future iterations, Cadence may consider expanding automation by developing an integration with Torii to streamline the offboarding workflow through API-triggered deprovisioning and asset revocation."*

### Implementation & Boundary
- Implemented as a clean adapter pattern `ToriiDeprovisioningAdapter`.
- When a vendor transitions to `Offboarding` and offboarding approval tasks complete, Cadence TPRM invokes `torii_adapter.revoke_vendor_assets(vendor_id)`.
- If production Torii credentials are not present in the local environment, the adapter executes in mock/development mode, logging clear audit events: *"Torii deprovisioning simulated for vendor [ID]: 4 assets queued for revocation"*, without fabricating external connectivity.
