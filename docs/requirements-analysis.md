# Requirements Analysis: Cadence TPRM Implementation

**Author:** Principal Solutions Architect  
**Source Document:** `Cadence_TPRM_Training.docx` (OneTrust TPRM Training / Optiv Engagement)  
**Date:** September 16, 2026 / October 2026  
**Status:** COMPLETE & AUTHORITATIVE  

---

## 1. Document Scope & Architectural Objective

The source document specifies the enterprise Third-Party Risk Management (TPRM) configuration for **Cadence**, developed in partnership with Optiv. The solution replaces siloed, manual, and fragmented risk processes with a unified, auditable **Integrated Risk Management (IRM)** architecture.

Key structural goals:
1. Standardized vendor classification across 5 vendor categories + Tier-3 low-risk vendors.
2. Automated vendor onboarding and tier-specific routing triggered by contractual events (Ironclad integration).
3. Comprehensive due diligence questionnaires (`Due Diligence Questionnaire T1-2 v1` and `Due Diligence Questionnaire T3 v1`).
4. Automated risk scoring and finding creation based on vendor responses (Appendix E, 68 rules).
5. Cross-functional review workflows across 10 specialized stakeholder groups.
6. Service-Level Agreements (SLAs), notification dispatch, automated renewal, and reassessment schedules.

---

## 2. Detailed Section Analysis

### Section 1: Introduction & Scope
- **Cadence Objective:** Standardized, scalable, automated TPRM framework.
- **Core Pillars:** Workflows, User Roles & Access Management, Vendor Onboarding Attributes, Refreshed DDQ templates.
- **Scope:** Current State Analysis, DDQ Refresh, OneTrust Configuration, Training & Knowledge Transfer.

### Section 2: Enhancements Implemented in OneTrust
- **2.1 Taxonomy Standardization:** Eliminates ambiguity by classifying third parties into:
  1. *Staffing Vendors*
  2. *Service Providers and Vendors*
  3. *Marketing Partners*
  4. *Revenue Partners*
  5. *International Vendors*
  6. *Tier-3 Vendors*
- **2.2 Workflows Configured:** Dedicated workflows for each type, plus Renewal and Offboarding workflows. Integrated with Ironclad contract lifecycle management.
- **2.3 Key Enhancements Delivered:**
  - Refreshed DDQ templates capturing data sensitivity, regulatory compliance, country risk, and geopolitical factors.
  - Risk methodology embedding inherent risk scoring, risk statements, and mitigation recommendations.
  - Reassessment cadences: Tier 1 (Annual, 365 days / 275 day lead trigger); Tier 2 & Tier 3 (Every 24 months / 640 day lead trigger).
  - Role-based access control with distinct privileges for VRM (Full Admin) and operational teams (Edit / Review).

### Section 3: Transition Toward Integrated Risk Management (IRM)
- Transition from Siloed Risk Functions (Legal, Compliance, Security, Procurement in isolation) to Integrated Risk Management with unified visibility.
- Two core risk domains:
  - **Operational Risks:** Legal, Financial, Privacy, and Compliance exposures.
  - **Cyber Risks:** Data protection, access control, incident management, infrastructure security.

### Section 4: Proposed TPRM Approach
- **Table 4 (Third-Party Types):**
  - Defines descriptions, reviewing user groups, and designated approver (`Vendor Risk Management Group`) for all 5 categories.
- **Table 5 (User Groups Details):**
  - Defines 10 user groups, descriptions, permissions (`Admin` or `Edit`), and authoritative member rosters.
- **Workflow Paths:**
  - Automated onboarding FSM evaluating Category + Tier.
  - Tier 1 & 2: Comprehensive 8-section questionnaire, detailed review, manual VRM approval.
  - Tier 3: Simplified questionnaire, automatic approval on favorable responses (`WR.T3.3`).

### Section 5: Final Approach & Attributes
- **5.1 Final Approved Workflow:** Ironclad intake -> Onboarding Workflow -> Category/Tier Workflow -> DDQ Launch -> Review by User Groups -> Approval/Rejection -> Live -> Renewal/Reassessment -> Offboarding -> Closed.
- **5.2 Table 9 (Attributes for Workflow):**
  - `Name` (String): Vendor name.
  - `Type` (Enum): Consulting, Operations, Regulatory, Strategic, Technology, Unknown.
  - `Criticality` (Enum): Critical, High, Medium, Low.
  - `Primary vendor contact` (Email): Vendor contact for questionnaire distribution.
  - `Business Owner` (Email): Internal owner responsible for relationship.
  - `Vendor Tier` (Enum): Tier 1, Tier 2, Tier 3.
  - `Vendor Category` (Enum): Service Provider and Vendor, Revenue Partner, Marketing Partner, Staffing Vendor, International Vendor.
  - `Website` (Domain): Domain URL.

### Section 6: Configuration Details
- **6.1 User Management:** User group creation, member assignment, role assignment, annual review cycle.
- **6.2 Attribute Development:** Attribute management, validation rules, status active/inactive.
- **6.3 Questionnaire Development:**
  - Template versioning and copy/publish lifecycle.
  - Section breakdown: Contracting & Legal, Compliance & Legal, Finance, Data Privacy & Security, IT Systems & Integration, Marketing, Procurement, Resiliency.
  - Show logic configuration (Appendix C: CL.1 to CL.14).
  - Questionnaire automation rules (Appendix E: QR.1 to QR.68).
  - Control linkage (`QRC_*`) and mitigation guidance.
- **6.4 Workflow Development:** Stage progression, triggers, stage rules, workflow rules, cloning, and publishing dependencies.

### Appendices
- **Appendix A (Workflow Rules & Tables 6, 7, 8, 10):**
  - `WR.ON.1` to `WR.ON.6`: Route vendors from `CD_Onboarding Workflow` to specific workflow based on Category and Tier.
  - Category Workflows (`RP`, `MP`, `IV`, `SP`, `SV`): Push to next, Send questionnaire, Approval transition to Live, Rejection transition to Review Reject, Notification dispatches, and 14-day review tasks.
  - `WR.T3.1` to `WR.T3.6`: Tier 3 launch, auto-approval, rejection, notifications.
  - `AR.T1.1`, `AR.T2.1`, `AR.T3.1`: Daily reassessment automation rules with 275-day (Tier 1) and 640-day (Tier 2/3) triggers copying previous assessments.
- **Appendix B (Questionnaire Specifications & Table 11):**
  - `Due Diligence Questionnaire T1-2 v1` & `Due Diligence Questionnaire T3 v1`.
- **Appendix C (Conditional Logic Rules & Table 12):**
  - `CL.1` to `CL.14`: Exact show/hide logic covering corporate ownership, complaints policies, Oracle onboarding forms, data subject scopes, AI usage, MFA exceptions, VPN controls, tenant isolation, pentest remediation, and DLP scopes.
- **Appendix D (SLA Specifications & Table 13):**
  - `SLA.1` (Assessment Completion: 9 days, reminder: 5 days).
  - `SLA.2` (Review Responses: 4 days, reminder: 2 days).
  - `SLA.3` (High Risk Response: 5 + 4 = 9 days, reminder: 3 days).
  - `SLA.4` (Medium Risk Response: 10 + 4 = 14 days, reminder: 7 days).
  - `SLA.5` (Low Risk Response: 15 + 4 = 19 days, reminder: 10 days).
  - `SLA.6` & `SLA.7` (Renewal Reassessment triggers: 275 and 640 days).
- **Appendix E (Questionnaire Risk Scoring & Table 14):**
  - 68 distinct risk scoring rules mapping questions, responses, inherent risks (High, Medium, Low), control identifiers (`QRC_*`), control names, score thresholds, and automatic task assignments for all 9 review groups.
