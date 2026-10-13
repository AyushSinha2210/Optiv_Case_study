# REST API Contracts Specification: Cadence TPRM Application

**Base URL:** `/api/tprm/v1`  
**Content-Type:** `application/json`  
**Authentication:** Bearer JWT or Secure Session Header (`X-User-Email`)  

---

## 1. Authentication & Session Endpoints

### `POST /api/tprm/v1/auth/login`
- **Request:**
  ```json
  { "email": "daniela.figueroa@cadence.com", "password": "optional_local_bootstrap" }
  ```
- **Response (200 OK):**
  ```json
  {
    "user": {
      "id": "usr-1",
      "email": "daniela.figueroa@cadence.com",
      "full_name": "Daniela Figueroa",
      "groups": ["Vendor Risk Management Group", "Finance Group", "Data Quality Group"],
      "roles": ["TPRM_ADMIN", "FINANCE_REVIEWER", "DATA_QUALITY_REVIEWER"],
      "is_admin": true
    },
    "access_token": "jwt_token_string",
    "token_type": "bearer"
  }
  ```

### `GET /api/tprm/v1/auth/me`
- **Response (200 OK):** Current session user object with groups, roles, and assigned tasks count.

---

## 2. Vendor Management Endpoints

### `GET /api/tprm/v1/vendors`
- **Query Params:** `category`, `tier`, `status`, `search`, `page`, `page_size`, `sort_by`, `sort_desc`.
- **Response (200 OK):**
  ```json
  {
    "items": [
      {
        "id": "v-1",
        "name": "Global Tech Services Inc",
        "type": "Technology",
        "criticality": "Critical",
        "primary_vendor_contact": "pvc@globaltech.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 1",
        "vendor_category": "Service Provider and Vendor",
        "website": "https://globaltech.com",
        "lifecycle_status": "Assessment",
        "current_stage": "Launching ServPro",
        "assessment_id": "asm-1",
        "created_at": "2026-09-16T10:00:00Z"
      }
    ],
    "total": 45,
    "page": 1,
    "page_size": 10
  }
  ```

### `POST /api/tprm/v1/vendors`
- **Request:**
  ```json
  {
    "name": "Acme Marketing Global",
    "type": "Operations",
    "criticality": "High",
    "primary_vendor_contact": "contact@acmemarketing.com",
    "business_owner": "shimane.smith@cadence.com",
    "vendor_tier": "Tier 2",
    "vendor_category": "Marketing Partner",
    "website": "https://acmemarketing.com"
  }
  ```
- **Response (201 Created):** Creates vendor record, auto-triggers `CD_Onboarding Workflow`, evaluates `WR.ON.2`, auto-assigns `CD_Marketing Partners Workflow` in stage `Launching MarPart`, dispatches assessment.

### `GET /api/tprm/v1/vendors/{id}`
- **Response (200 OK):** Vendor details, current workflow state, assessments history, contracts, risk findings, and tasks.

---

## 3. Questionnaire & Assessment Endpoints

### `GET /api/tprm/v1/questionnaires/templates/{code}`
- Returns template metadata, all 8 sections, question definitions, and conditional display rules (`CL.1` to `CL.14`).

### `GET /api/tprm/v1/assessments/{id}`
- Returns assessment status, assigned template, responses, calculated score, triggered risk findings, and reviews.

### `POST /api/tprm/v1/assessments/{id}/responses`
- **Request:**
  ```json
  {
    "responses": {
      "1.3": "No",
      "4.10": "Yes",
      "4.11": "AI customer support chatbot interacting with client logs",
      "4.18": "No",
      "4.19": "Legacy mainframe API without MFA support"
    }
  }
  ```
- **Response (200 OK):** Saves draft responses.

### `POST /api/tprm/v1/assessments/{id}/submit`
- **Response (200 OK):**
  - Validates required answers and active conditional rules.
  - Executes Risk Rules (`QR.1` to `QR.90`).
  - Generates Inherent Risk findings and maps `QRC_*` controls.
  - If Tier 3 and all clean (`QR.73`), auto-approves assessment (`WR.T3.3`).
  - Otherwise, marks status as `In Review`, generates `Assessment Submitted` task for approvers and review groups, and calculates SLAs.

---

## 4. Reviews & Approval Workflow Endpoints

### `POST /api/tprm/v1/assessments/{id}/reviews`
- **Request:**
  ```json
  {
    "group_name": "Security Group",
    "notes": "Reviewed SOC 2 report and pentest findings. High risk finding QRC_Sec_4.12 requires compensating IP whitelist control.",
    "status": "Approved"
  }
  ```

### `POST /api/tprm/v1/assessments/{id}/approve`
- **Authorization:** `Vendor Risk Management Group` (Admin) only.
- **Request:**
  ```json
  { "decision_reason": "All operational risks accepted and mitigations agreed." }
  ```
- **Effect:** Executes `WR.*.3` -> Advances vendor to `Live`, dispatches approval notification (`WR.*.6`), records audit log.

### `POST /api/tprm/v1/assessments/{id}/reject`
- **Authorization:** `Vendor Risk Management Group` (Admin) only.
- **Request:**
  ```json
  { "decision_reason": "Vendor failed financial audit and lacks cyber insurance." }
  ```
- **Effect:** Executes `WR.*.4` -> Advances vendor to `Review Reject`, dispatches rejection notification and creates 14-day task for Business Owner (`WR.*.5`).

---

## 5. Tasks, SLA & Reassessment Endpoints

### `GET /api/tprm/v1/tasks`
- Returns user's assigned and group-collaborated tasks, with due dates, reminder dates, and SLA compliance status.

### `POST /api/tprm/v1/automation/run-reassessments`
- Simulates daily automation run for `AR.T1.1`, `AR.T2.1`, and `AR.T3.1`.
- Finds vendors due for reassessment (>=275 days for Tier 1; >=640 days for Tier 2/3), creates new assessment copying prior answers, and alerts Business Owner.

---

## 6. Integration Endpoints

### `POST /api/tprm/v1/integrations/ironclad/webhook`
- Receives Contract Creation or Contract Execution events from Ironclad.
- Automatically maps Table 9 attributes (`Name`, `Type`, `Criticality`, `Primary vendor contact`, `Business Owner`, `Vendor Tier`, `Vendor Category`, `Website`).
- Idempotently creates/updates vendor and initiates onboarding workflow.

### `POST /api/tprm/v1/integrations/torii/deprovision`
- Adapter for Torii offboarding: revokes SaaS access and logs asset closure.
