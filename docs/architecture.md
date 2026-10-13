# Enterprise Architecture Specification: Cadence TPRM Application

**System:** Cadence Third-Party Risk Management (TPRM) Platform  
**Target Enterprise:** Cadence Financial Group / Cadence Design Systems  
**Author:** Principal Software Architect  
**Authority:** `Cadence_TPRM_Training.docx`  

---

## 1. System Vision & Architecture Paradigm

The Cadence TPRM Application transitions Cadence from siloed, manual risk reviews into an **Integrated Risk Management (IRM)** paradigm. It connects contract intake (Ironclad) with vendor risk classification, automated questionnaire distribution, multi-disciplinary review, inherent risk scoring, departmental mitigations, and automated reassessments.

```
+---------------------------------------------------------------------------------------------------+
|                                      CADENCE TPRM PLATFORM                                        |
+---------------------------------------------------------------------------------------------------+
|  PRESENTATION TIER (React 19 + TypeScript + Vite)                                                 |
|  - AWS Management Console Information Architecture (Global Header, Collapsible Sidebar, Context)   |
|  - Real Views: Vendor Directory, Onboarding Wizard, Questionnaire Engine, Risk Findings, Reviews  |
+---------------------------------------------------------------------------------------------------+
                                              |  HTTPS / REST / JSON Contracts
                                              v
+---------------------------------------------------------------------------------------------------+
|  APPLICATION SERVICES TIER (Python 3.13 + FastAPI + Pydantic v2)                                   |
|  - Auth & RBAC Security Layer (10 User Groups, Section-Specific Edit & Review Grants)             |
|  - Vendor Management Service (5 Categories, Tier 1/2/3, Table 9 Attributes)                       |
|  - Workflow State Machine Engine (Onboarding, Category FSMs, Tier 3 Auto-Approval)                 |
|  - Questionnaire Engine (DDQ T1-2 v1 & T3 v1, Appendix C Conditional Logic CL.1-CL.14)            |
|  - Risk Scoring & Controls Engine (Appendix E QR.1-QR.90, Inherent Risk & QRC_* Controls)         |
|  - SLA & Task Notification Dispatcher (SLA.1-SLA.7, 9d/4d/9d/14d/19d Timelines)                  |
|  - Reassessment & Renewal Scheduler (AR.T1.1 at 275d, AR.T2.1/T3.1 at 640d)                       |
|  - Integration Adapters (Ironclad Ingestion Webhook, OneTrust Sync, Torii Offboarding)            |
+---------------------------------------------------------------------------------------------------+
                                              |  SQLAlchemy 2.0 ORM
                                              v
+---------------------------------------------------------------------------------------------------+
|  PERSISTENCE TIER (Relational Database - SQLite / PostgreSQL)                                     |
|  - Strict Foreign Keys, Unique Indexes, Relational Integrity & Concurrency Controls               |
|  - Append-Only Tamper-Evident Audit Event Trail                                                   |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Core Subsystems

### 2.1 Identity, Organizations & RBAC Subsystem
- **Organizations:** Multi-tenant boundary (`Cadence Corporate`).
- **Departments & Groups:** 10 User Groups defined in Table 5:
  1. *Vendor Risk Management Group* (`TPRM_ADMIN` & `VRM_REVIEWER`)
  2. *Legal Group*
  3. *Procurement Group*
  4. *Finance Group*
  5. *IT Group*
  6. *Compliance Group*
  7. *Privacy Group*
  8. *Security Group*
  9. *Data Quality Group*
- **Access Model:** Least-privilege role-based access. Approvals are strictly restricted to the `Vendor Risk Management Group`. Section reviews are granted to designated operational groups.

### 2.2 Vendor Lifecycle & Workflow Engine
- **State Machine Stages:**
  - `New Third Party` (Onboarding Intake)
  - `Launching` (Assessment Initiated & Dispatched)
  - `In Review` (Cross-Departmental Review by User Groups)
  - `Live` (Approved & Active)
  - `Review Reject` (Rejected by VRM; Rejection Notification & 14-day Task Created)
  - `Offboarding` (Initiated Offboarding Review)
  - `Closed` (Completed Offboarding & Archival)
- **Routing Decision Engine:**
  - Table 10 rules: `WR.ON.1` to `WR.ON.6` dynamically route by `Vendor Category` and `Vendor Tier`.
  - Tier 3 vendors route directly to `CD_Tier3 Workflow` with automated approval triggers (`WR.T3.3`).

### 2.3 Questionnaire & Risk Evaluation Engine
- **Templates:**
  - `Due Diligence Questionnaire T1-2 v1` (8 Sections: Contracting, Compliance, Finance, Privacy & Security, IT, Marketing, Procurement, Resiliency).
  - `Due Diligence Questionnaire T3 v1` (Simplified for low-risk vendors).
- **Conditional Logic (Show Logic):**
  - Appendix C rules `CL.1` to `CL.14` dynamically reveal dependent questions in real-time and validate on submission.
- **Risk Scoring & Controls (Appendix E):**
  - 68+ rules (`QR.1` to `QR.90`) evaluate responses, trigger inherent risk levels (`High`, `Medium`, `Low`), map to controls (`QRC_*`), and generate department-specific remediation tasks.
  - Overall assessment score calculation based on percentage of favorable answers. Scores below 40 trigger `Low Assessment Score` escalation tasks.

### 2.4 SLA, Notification & Reassessment Engine
- SLA calculation based on Table 13:
  - Assessment Completion: 9 days (Reminder at 5 days).
  - Review Responses: 4 days (Reminder at 2 days).
  - High Risk Response: 5 + 4 = 9 days (Reminder at 3 days).
  - Medium Risk Response: 10 + 4 = 14 days (Reminder at 7 days).
  - Low Risk Response: 15 + 4 = 19 days (Reminder at 10 days).
- Automation Rules (`AR.T1.1`, `AR.T2.1`, `AR.T3.1`):
  - Daily scheduler checks vendor `last_assessment_completion_date`.
  - At 275 days for Tier 1: Auto-initiates reassessment copying prior answers and alerts Business Owner.
  - At 640 days for Tier 2 and Tier 3: Auto-initiates reassessment copying prior answers and alerts Business Owner.

### 2.5 Integration Boundaries
- **Ironclad:** Webhook intake for new vendor records and contract status.
- **OneTrust:** Synchronization endpoint for external risk status.
- **Torii:** Deprovisioning and access revocation adapter for offboarding.
