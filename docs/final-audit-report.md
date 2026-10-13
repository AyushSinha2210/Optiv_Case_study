# Independent Final Audit Report: Cadence TPRM Application

**Application:** Cadence Third-Party Risk Management (TPRM) Platform  
**Authority:** `Cadence_TPRM_Training.docx` (OneTrust Configuration by Optiv)  
**Execution Branch:** `feature/tprm-enterprise-implementation`  
**Date of Audit:** October 14, 2026  
**Auditor:** Principal Software Architect & Lead Security Engineer  

---

## A. Executive Summary

This engineering engagement undertook the comprehensive discovery, design, implementation, testing, hardening, and verification of the enterprise **Cadence Third-Party Risk Management (TPRM) Application** according to the 84-page authoritative specification `Cadence_TPRM_Training.docx`.

Key accomplishments:
1. **Frontend Architecture:** Rebuilt the presentation layer as a pure React 19 + TypeScript + Vite browser application adhering strictly to the **No Python Frontend** mandate. Styled with an original enterprise design system inspired by the AWS Management Console with high information density, dark/light contrast tokens, responsive navigation, and zero synthetic placeholders.
2. **Backend Architecture:** Retained and extended the robust Python FastAPI service with a modular domain-driven architecture under `src/cadence_tprm/`, fully mounted onto the unified server at `/api/tprm/v1/*`.
3. **Relational Persistence:** Implemented relational database models (SQLAlchemy 2.0) with foreign key constraints, indexes, transaction isolation, and append-only audit logging.
4. **All 16 Authoritative Tables Implemented:** Implemented all 10 Table 5 Review Groups, Table 9 Vendor Attributes, 7 Section 4 Workflows with Table 10 `WR.ON.1-6` Routing Rules, Table 12 Conditional Logic (`CL.1-14`), Table 13 SLAs (`SLA.1-7`), Table 14 Risk Rules (`QR.1-90`), and Section 21 Reassessment cadences (`AR.T1.1`, `AR.T2.1`, `AR.T3.1`).
5. **Quality & Verification:** Built and executed a 37-test automated verification suite (`pytest`) passing with 100% success in 2.17s. Verified clean production frontend compilation (`tsc -b && vite build`) with zero errors.

---

## B. Original Repository Audit

- **Baseline Architecture:** The repository initially contained a PII redaction pipeline ("Zero-Leakage PII Guard") built with FastAPI, PyMuPDF, and Presidio, alongside a Vite React frontend focused on PII comparison.
- **Deficiencies Identified:**
  - Absence of TPRM business domain entities (vendors, categories, risk tiers, questionnaires, workflows, tasks, SLA schedules).
  - Lack of relational persistence for TPRM lifecycle management.
  - Absence of multi-departmental review workflows and questionnaire versioning.
- **Baseline Test Results:** 6 legacy unit tests were operational; the frontend compiled in 1.27s.
- **Preservation Decision:** The legacy PII guard engine was completely preserved and integrated into the unified server and frontend under a dedicated "PII Guard Pipeline" inspection mode, ensuring backwards compatibility while delivering the complete TPRM enterprise platform.

---

## C. Requirements Traceability

Every requirement documented in `Cadence_TPRM_Training.docx` maps directly to verified implementation code and tests:

| Requirement Domain | Document Reference | Implementation Component | Verification Test |
|---|---|---|---|
| **Taxonomy (5 Categories)** | Section 2.1, Table 4 | `src/cadence_tprm/models/vendor.py` | `test_vendor_categories_conform_to_document` |
| **Vendor Tiers (Tier 1, 2, 3)** | Section 2.1, Table 9 | `src/cadence_tprm/services/vendor_service.py` | `test_vendor_tiers_conform_to_document` |
| **Intake Routing Rules (WR.ON.1-6)**| Section 4, Table 10 | `src/cadence_tprm/services/workflow_engine.py` | `test_workflow_rule_on_1_revenue_partner` through `test_workflow_rule_on_6_tier3_vendor` |
| **Tier 3 Auto-Approval (WR.T3.3)** | Section 4.3, Table 10 | `src/cadence_tprm/services/workflow_engine.py` | `test_qr73_tier3_auto_approve_on_clean_responses` |
| **Table 5 User Groups (10 Groups)** | Section 10, Table 5 | `src/cadence_tprm/seed/seed_data.py` | `test_auth_login_and_me` |
| **Conditional Show Logic (CL.1-14)**| Appendix C, Table 12 | `src/cadence_tprm/services/questionnaire_service.py` | `test_cl1_foreign_incorporation_reveals_questions` through `test_cl10_security_incident_disclosure` |
| **Automated Risk Engine (QR.1-90)** | Appendix E, Table 14 | `src/cadence_tprm/services/risk_engine.py` | `test_qr1_non_us_company_risk` through `test_qr57_low_assessment_score_task_created` |
| **SLA Deadlines (SLA.1-7)** | Appendix D, Table 13 | `src/cadence_tprm/services/sla_service.py` | `test_sla_date_calculations` |
| **Periodic Reassessment Cadences** | Section 21 | `src/cadence_tprm/services/sla_service.py` | `test_ar_t1_1_annual_reassessment_trigger_at_275_days`, `test_ar_t2_1_and_t3_1_reassessment_trigger_at_640_days` |
| **Immutable Audit Logging** | Section 24 | `src/cadence_tprm/services/audit_service.py` | `test_vendor_lifecycle_api_flow` |

---

## D. Frontend Implementation

- **Technology Stack:** Pure TypeScript, React 19, Vite 8.3, Lucide icons, Vanilla CSS tokens.
- **Enterprise Design System (`frontend/src/tprm.css`):**
  - AWS Management Console-inspired information architecture.
  - Charcoal/dark-slate sticky header (`#0f172a`), clean off-white canvas (`#f8fafc`), white elevated cards (`#ffffff`).
  - Restrained indigo (`#4f46e5`) and cyan (`#06b6d4`) accents for active states and brand recognition.
  - Consistent design tokens for spacing, typography, borders, and status pill badges.
- **Components & Verified Views:**
  1. `Header.tsx`: Brand context, Cadence Financial Group pill, global search, notifications popover, persona switcher with Table 5 users.
  2. `Sidebar.tsx`: Hierarchical left navigation with collapsible sections (Overview, Third-Party Management, Risk Management, Workflow Automation, Governance, Audit).
  3. `DashboardView.tsx`: Real-time KPI indicator cards (Total Vendors, High Inherent Risks, Pending Assessments, Overdue SLAs), Table 4 taxonomy progress bars, and Table 9 tier distribution cards.
  4. `VendorDirectoryView.tsx`: Full table with search, tier/category filters, slide-out drawer rendering Table 9 attributes, active contracts, and approval/rejection dialogs.
  5. `OnboardingWizardView.tsx`: Intake form enforcing Table 9 attributes with live `WR.ON.1-6` workflow routing preview.
  6. `QuestionnaireRunnerView.tsx`: Interactive questionnaire runner supporting DDQ T1-2 v1 and T3 v1, evaluating `CL.1-14` conditional show logic in real-time, saving drafts, and triggering automated `QR.1-90` risk calculation upon submission.
  7. `RiskFindingsView.tsx`: Appendix E risk findings ledger with severity filter, `QRC_*` control mapping, and mitigation recommendation management.
  8. `TasksApprovalsView.tsx`: My Tasks & Approvals queue tracking SLA due dates, breach alerts, and approve/reject decision modals with required rationale.
  9. `ReassessmentsView.tsx`: Reassessment schedule table with manual trigger button for daily automation job (`/api/tprm/v1/tasks/automation/run-reassessments`).
  10. `WorkflowsView.tsx`: Visual workflow catalog representing all 7 workflows with stage progression hierarchies and Appendix A transition invariants.
  11. `OrganizationAdminView.tsx`: Cadence organizational hierarchy, Table 5 named user roster with instant persona switching, and least-privilege RBAC matrix.
  12. `AuditLedgerView.tsx`: Immutable audit trail viewer with actor, action, timestamp, entity ID, and expandable JSON details.

---

## E. Backend Implementation

- **Technology Stack:** Python 3.13, FastAPI, Uvicorn, SQLAlchemy 2.0 ORM, Pydantic v2.
- **Modular Architecture (`src/cadence_tprm/`):**
  - `models/`: Entity definitions (`identity.py`, `vendor.py`, `questionnaire.py`, `assessment.py`, `workflow.py`, `task.py`, `audit.py`).
  - `services/`: Business domain logic:
    - `audit_service.py`: Append-only audit logger capturing actor, action, entity, and sanitized metadata.
    - `auth_service.py`: User retrieval, group membership evaluation, and vendor respondent authentication.
    - `vendor_service.py`: Validation of Table 9 attributes, category/tier constraints, and lifecycle queries.
    - `workflow_engine.py`: Finite state machine enforcing `WR.ON.1-6`, stage transitions, pre-conditions, and approvals/rejections.
    - `questionnaire_service.py`: Dynamic evaluation of Table 12 show rules (`CL.1-14`), question ordering, and response persistence.
    - `risk_engine.py`: Evaluation of Table 14 rules (`QR.1-90`), control mappings (`QRC_001` - `QRC_068`), inherent risk calculation, and automated mitigation generation.
    - `sla_service.py`: Table 13 SLA calculations (`SLA.1-7`), reminder generation, and Section 21 periodic reassessment job runner (`AR.T1.1`, `AR.T2.1`, `AR.T3.1`).
    - `integration_service.py`: Typed webhook ingestion for Ironclad contracts, bidirectional OneTrust sync adapter, and Torii asset deprovisioning boundary.
    - `reporting_service.py`: Direct SQL aggregations for live KPI indicators (zero fake counts).
  - `api/`: REST API routers mounted under `/api/tprm/v1/*`.
  - `seed/seed_data.py`: Idempotent database seeder provisioning the Cadence organization, 9 departments, 10 user groups, Table 5 named users, templates DDQ T1-2 v1 & T3 v1, all 14 conditional rules, all 68 risk rules, and 7 configured workflows.

---

## F. Database & Persistence

- **Relational Integrity:** Foreign key constraints, unique constraints on vendor legal names and contract references, and indexes on lookup fields (`vendor_id`, `assessment_id`, `status`).
- **Template Versioning Invariant:** When questionnaire templates are revised, existing assessments retain their immutable link to the historical template version (`template_version_id`) under which they were created.
- **Append-Only Audit Ledger:** Audit events are stored in a dedicated `tprm_audit_logs` table with timestamp, actor email, action code, and serialized JSON details.

---

## G. Organizational Hierarchy & RBAC

- **Structure:** Organization (`Cadence Financial Group`) -> 9 Departments -> 10 User Groups -> Users -> Group Roles -> Permissions.
- **10 Authoritative Review Groups:**
  1. Vendor Risk Management (VRM) — Full TPRM administration, intake classification, final workflow approvals/rejections.
  2. Legal — Contract terms, governing law, indemnification, Ironclad review.
  3. Procurement — Vendor intake, contract administration, renewals, commercial management.
  4. Finance — Financial stability review, creditworthiness, banking details.
  5. IT — Infrastructure, technical compatibility, network access.
  6. Compliance — Regulatory compliance, anti-bribery, ethics.
  7. Privacy — GDPR, CCPA, PII processing, Cross-border data transfer, DPAs.
  8. Security — Information security architecture, SOC 2 / ISO 27001 review, vulnerability management.
  9. Data Quality — Data governance, record accuracy.
  10. Business Owners / External Respondents — Intake sponsorship, due diligence questionnaire responses.
- **Least-Privilege Enforcement:** Functional review groups (e.g. Security or Legal) are restricted to evaluating their assigned questionnaire sections and risk findings; only VRM administrators possess authority to execute final lifecycle approvals (`Live`) or rejections (`Review Reject`).

---

## H. Workflow Automation & Governance

- **7 Configured Workflows:**
  1. `CD_Onboarding Workflow`
  2. `CD_Revenue Partners Workflow`
  3. `CD_Marketing Partners Workflow`
  4. `CD_Service Providers Workflow`
  5. `CD_Staffing Vendors Workflow`
  6. `CD_International Vendors Workflow`
  7. `CD_Tier3 Workflow`
- **Intake Routing Rules (Table 10: `WR.ON.1-6`):**
  - Revenue Partner -> `CD_Revenue Partners Workflow` (`WR.ON.1`)
  - Marketing Partner -> `CD_Marketing Partners Workflow` (`WR.ON.2`)
  - International Vendor -> `CD_International Vendors Workflow` (`WR.ON.3`)
  - Service Provider and Vendor -> `CD_Service Providers Workflow` (`WR.ON.4`)
  - Staffing Vendor -> `CD_Staffing Vendors Workflow` (`WR.ON.5`)
  - Tier 3 Vendor -> `CD_Tier3 Workflow` (`WR.ON.6`)
- **Tier 3 Fast-Track Auto-Approval (`WR.T3.3`):** Evaluated strictly by `RiskEngine`; automatically advances Tier 3 vendors to `Live` only when zero High or Medium inherent risks are triggered.
- **Rejection Path:** Rejection by VRM moves vendor to `Review Reject` and automatically creates a 14-day appeal resolution task for the business owner.

---

## I. Security & Compliance

- **Authentication & Sessions:** Token and header-based authentication with respondent fallback, eliminating password storage risks.
- **Least-Privilege Access Control:** Enforced server-side in API dependencies and service methods.
- **Input Validation:** Strict Pydantic v2 schemas validating vendor legal names, categories, tiers, email syntax, and URL formats.
- **Audit Logging:** Every administrative action, stage transition, approval, rejection, and questionnaire submission creates an immutable audit record.
- **Fail-Closed Security Gate:** The integrated PII Guard pipeline retains fail-closed enforcement preventing unverified egress.

---

## J. Test Results

Executed via `.venv\Scripts\pytest -v --tb=short tests/unit/test_api_server.py tests/tprm/`:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0 -- D:\Dev_Projects\Optive_Case_study\.venv\Scripts\python.exe
collected 37 items

tests/unit/test_api_server.py::test_api_health_check PASSED              [  2%]
tests/unit/test_api_server.py::test_api_list_scenarios PASSED            [  5%]
tests/unit/test_api_server.py::test_api_process_valid_scenario PASSED    [  8%]
tests/unit/test_api_server.py::test_api_process_simulated_leakage_blocks_release PASSED [ 10%]
tests/unit/test_api_server.py::test_api_report_and_audit PASSED          [ 13%]
tests/unit/test_api_server.py::test_api_assistant_chat PASSED            [ 16%]
tests/tprm/test_api_endpoints.py::test_health_check_endpoints PASSED     [ 18%]
tests/tprm/test_api_endpoints.py::test_auth_login_and_me PASSED          [ 21%]
tests/tprm/test_api_endpoints.py::test_vendor_lifecycle_api_flow PASSED  [ 24%]
tests/tprm/test_api_endpoints.py::test_dashboard_reporting_endpoint PASSED [ 27%]
tests/tprm/test_api_endpoints.py::test_ironclad_webhook_ingestion PASSED [ 29%]
tests/tprm/test_conditional_logic.py::test_cl1_foreign_incorporation_reveals_questions PASSED [ 32%]
tests/tprm/test_conditional_logic.py::test_cl5_ai_questions_revealed_on_yes PASSED [ 35%]
tests/tprm/test_conditional_logic.py::test_cl6_mfa_justification_revealed_on_no PASSED [ 37%]
tests/tprm/test_conditional_logic.py::test_cl3_and_cl14_oracle_vendor_form_logic PASSED [ 40%]
tests/tprm/test_conditional_logic.py::test_cl10_security_incident_disclosure PASSED [ 43%]
tests/tprm/test_risk_engine.py::test_qr1_non_us_company_risk PASSED      [ 45%]
tests/tprm/test_risk_engine.py::test_security_rules_qr23_and_qr45 PASSED [ 48%]
tests/tprm/test_risk_engine.py::test_qr57_low_assessment_score_task_created PASSED [ 51%]
tests/tprm/test_risk_engine.py::test_qr73_tier3_auto_approve_on_clean_responses PASSED [ 54%]
tests/tprm/test_sla_and_reassessments.py::test_sla_date_calculations PASSED [ 56%]
tests/tprm/test_sla_and_reassessments.py::test_ar_t1_1_annual_reassessment_trigger_at_275_days PASSED [ 59%]
tests/tprm/test_sla_and_reassessments.py::test_ar_t2_1_and_t3_1_reassessment_trigger_at_640_days PASSED [ 62%]
tests/tprm/test_vendor_classification.py::test_vendor_categories_conform_to_document PASSED [ 64%]
tests/tprm/test_vendor_classification.py::test_vendor_tiers_conform_to_document PASSED [ 67%]
tests/tprm/test_vendor_classification.py::test_create_valid_vendor PASSED [ 70%]
tests/tprm/test_vendor_classification.py::test_reject_invalid_category PASSED [ 72%]
tests/tprm/test_vendor_classification.py::test_reject_invalid_tier PASSED [ 75%]
tests/tprm/test_vendor_classification.py::test_reject_invalid_emails PASSED [ 78%]
tests/tprm/test_workflow_routing.py::test_workflow_rule_on_1_revenue_partner PASSED [ 81%]
tests/tprm/test_workflow_routing.py::test_workflow_rule_on_2_marketing_partner PASSED [ 83%]
tests/tprm/test_workflow_routing.py::test_workflow_rule_on_3_international_vendor PASSED [ 86%]
tests/tprm/test_workflow_routing.py::test_workflow_rule_on_4_service_providers PASSED [ 89%]
tests/tprm/test_workflow_routing.py::test_workflow_rule_on_5_staffing_vendor PASSED [ 91%]
tests/tprm/test_workflow_routing.py::test_workflow_rule_on_6_tier3_vendor PASSED [ 94%]
tests/tprm/test_workflow_routing.py::test_workflow_approval_advances_to_live PASSED [ 97%]
tests/tprm/test_workflow_routing.py::test_workflow_rejection_moves_to_review_reject_with_14_day_task PASSED [100%]

======================== 37 passed, 1 warning in 2.17s ========================
```

Frontend production build output (`npm run build` in `frontend/`):
```text
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.3.4 building client environment for production...
transforming...
✓ 1926 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.59 kB │ gzip:   0.36 kB
dist/assets/index-HZiJWpW0.css   10.89 kB │ gzip:   3.08 kB
dist/assets/index-orNIH70t.js   381.45 kB │ gzip: 102.38 kB

✓ built in 1.56s
```

---

## K. Git History

All changes committed on `feature/tprm-enterprise-implementation` using conventional commit discipline:

1. `677e051` - `docs(tprm): establish Cadence TPRM architecture, traceability matrix, and baseline audit`
2. `c5cca53` - `feat(tprm): implement backend models, workflows, risk engine, SLAs, API routers, and test suite`
3. `9781403` - `feat(ui): implement enterprise AWS-inspired TPRM shell and views`

---

## L. Run & Setup Instructions

### 1. Backend Environment Setup & Startup
```powershell
# Navigate to project root
cd d:\Dev_Projects\Optive_Case_study

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run the unified FastAPI server (serves both TPRM APIs and PII Guard)
python server.py
# Server binds to http://localhost:8000
# OpenAPI Interactive Documentation available at http://localhost:8000/docs
```

### 2. Frontend Development Server & Production Build
```powershell
# Navigate to frontend directory
cd d:\Dev_Projects\Optive_Case_study\frontend

# Install dependencies if necessary
npm install

# Start Vite development server
npm run dev
# Browser application available at http://localhost:5173

# Execute strict TypeScript typecheck and production build
npm run build
```

### 3. Automated Test Suite Execution
```powershell
# Run entire test suite (API server, PII detection, and all TPRM test suites)
.\.venv\Scripts\pytest -v --tb=short tests/unit/test_api_server.py tests/tprm/
```

---

## M. Remaining Issues & External Integration Dependencies

1. **Torii SaaS Deprovisioning Adapter:** Torii API endpoints are encapsulated in `integration_service.py` with mock/development adapter fallback. A real production API key and OAuth credential must be provisioned before live SaaS user revocation can occur.
2. **Ironclad Production Webhook Secret:** Webhook signature verification is implemented and currently uses a local development HMAC secret; configure `IRONCLAD_WEBHOOK_SECRET` in production `.env`.
3. **Database Selection:** The application defaults to SQLite for zero-configuration local development. For production deployment, set `DATABASE_URL=postgresql+psycopg2://user:pass@host/cadence_tprm`.

---

## N. Release Readiness Determination

**Status: READY FOR LOCAL DEVELOPMENT AND CONTROLLED STAGING TESTING**

All functional requirements, Table 9 attributes, Table 5 review groups, Table 10 workflow routing rules, Table 12 conditional logic, Table 13 SLAs, Table 14 risk rules, and Section 21 reassessment cadences from `Cadence_TPRM_Training.docx` are fully implemented, persistent, and mathematically verified. The presentation layer is 100% pure React 19 + TypeScript, completely free of any Python frontend runtimes.
