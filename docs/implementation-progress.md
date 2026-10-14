# Implementation Progress & Git Commit Log: Cadence TPRM Platform

**Branch:** `feature/tprm-enterprise-implementation`  
**Source Authority:** `Cadence_TPRM_Training.docx` (Opportunity Number: OP-4545941, Version 1.0)  
**Test Suite Verification:** `38 passed, 0 failed` (`tests/tprm/`)  

---

## Granular Conventional Git Commit History

```text
700f1c7 docs(tprm): populate complete 45-rule Appendix A, 14-rule Appendix C, 7-SLA Appendix D, and 90-rule Appendix E traceability matrices
eebd75d feat(ui): export hierarchical LoginView portal from Header module and wire into App shell
1b25bdb feat(ui): connect OrganizationAdminView and AuditLedgerView to live Table 5 roster, Attribute Manager, Integrations, and Audit CSV export
025c305 feat(ui): connect TasksApprovalsView, ReassessmentsView, and WorkflowsView to live backend payloads and Appendix A/D tables
806e70c feat(ui): fix QuestionnaireRunnerView choice inputs and connect RiskFindingsView to persistent PUT endpoint and CL/QR rule inspector
ac092b8 feat(ui): connect VendorDirectoryView and OnboardingWizardView to live lifecycle, renewal, offboarding, and Ironclad webhook APIs
0f2c12e feat(ui): add authorized CSV exports and live scheduler trigger to DashboardView
d48e588 feat(ui): upgrade enterprise shell with Light/Dark theme switcher, collapsible navigation, and live notifications
5c8c2f8 feat(ui): update TypeScript interfaces for Appendix A rules, Appendix D SLAs, and RBAC hierarchy
faef605 style(ui): implement Light and Dark Enterprise design system tokens and complete layout rules
6544c9c test(tprm): expand unit and E2E test suites to verify all 14 CL rules, all 90 QR rules, RBAC hierarchy, versioning, and full vendor lifecycle
5aab2ac fix(db): restore standard sqlalchemy imports in database.py and include orm_compat fallback
de6ede9 feat(api): unify response schemas across tasks, reports, audit logs, and integration status endpoints
3cf78db feat(api): add questionnaire template creation, Method A/B versioning, and CSV export endpoints
d0e0fdb feat(auth): resolve granular role and permission grants in user profile
02e18c4 feat(api): add organization hierarchy, user group creation, membership assignment, and user status endpoints
79141e6 feat(api): add workflow rule catalog, SLA definitions, cloning, and transition endpoints
4768d76 feat(api): add vendor attribute manager inventory, renewal decision, and archive endpoints
1b8f1b9 feat(api): add assessment list, launch, and persistent risk finding update endpoints
9f96f7b feat(vendors): add vendor attribute updates, renewal decision records, and transition history queries
2a2dfe0 feat(questionnaires): implement Method A and Method B template versioning, CSV export, and full CL/QR rule inspection
2f38b38 fix(reports): fix SQLite date math in dashboard summary and add audited CSV report exports
4da42d0 feat(workflows): enforce exact Appendix A stage names, rule codes, SLA.1 task dispatch, and manual closure/archiving
260607b feat(risk): implement documented average scoring (QR.58/QR.72), SLA.3-5 response tasks, QR.73 auto-approval, and QR.74-90 departmental tasks
14c0454 feat(seed): populate all 90 Appendix E rules, 14 Appendix C rules, 45 Appendix A rules, 7 SLAs, and Table 5 RBAC hierarchy
4307053 feat(models): add WorkflowRuleSpec, SLAConfig, and complete Appendix B/C/E rule metadata fields
993fff3 feat(vendors): add VendorAttributeDefinition and RenewalDecision models with archive state
6d5b7d4 feat(rbac): add Role and Permission models to complete Organization-Department-Group-User-Role hierarchy
07e9ba6 feat(db): add dual SQLAlchemy 2.0 and native SQLite3 relational ORM engine with foreign key enforcement
e02da6d chore(baseline): import initial Optiv Case Study repository state
```

---

## Defects Discovered in Baseline Archive & Repaired

1. **`ReportingService.get_dashboard_summary` SQL Crash (`TypeError`):** Fixed invalid `now + func.datetime('now', '+90 days')` expression to `now + timedelta(days=90)` (`commit 2f38b38`).
2. **Pydantic v1 / v2 Incompatibility (`req.model_dump()`):** Updated `vendors.py` to support both Pydantic v1 and v2 via `getattr(req, "model_dump", req.dict)()` (`commit 4768d76`).
3. **Missing Appendix E Rules in Database (`QR.56–58`, `QR.70–90`):** Seeded all 90 `QR.1`–`QR.90` rules into `risk_rules`, all 45 Appendix A rules into `workflow_rule_specs`, and all 7 SLAs into `sla_configs` (`commit 14c0454`).
4. **Non-Standard Assessment Scoring (`QR.58` & `QR.72`):** Replaced arbitrary penalty subtraction (`100 - 15*High - 7*Medium`) with documented Average Scoring over Yes/No questions and Question `1.8` (`0-5`, `5-10`, `10+`) (`commit 260607b`).
5. **Exact Tier 3 Auto-Approval Comment (`QR.73`):** Enforced exact documented result comment `"The third-party is Approved"` when all required Tier 3 questions are answered favorably (`commit 260607b`, `commit 1b8f1b9`).
6. **Missing Department-Specific & IT Task Rules (`QR.74–90`):** Implemented `QR.74–80`, `QR.81` (`Q5.6 == No` -> `IT Risk Identified for Third-Party`), `QR.82` (`Q5.1 == Yes` -> `IT Requirement Identified for Third-Party`), and `QR.83–90` (`_T3` variants) (`commit 260607b`).
7. **Incorrect Reject Stage Names (`WR.*.4`):** Fixed `WorkflowEngine.reject_vendor` to transition to exact Appendix A stage names (`Review Reject RevPart`, `Review Reject MarPart`, `Review Reject IntVen`, `Review Reject ServPro`, `Review Reject StafVen`, `Review Reject Tier3`) (`commit 4da42d0`).
8. **Missing Risk Response SLA Tasks (`SLA.3`, `SLA.4`, `SLA.5`):** Added distinct Risk Response acknowledgment/analysis tasks (9d, 14d, 19d) separate from remediation plans (`commit 260607b`).
9. **Broken Frontend/Backend API Key Contracts:** Unified `/audit` (`items` & `logs`), `/tasks` (`items` & `tasks`), `/workflows` (`items` & `workflows`), and added `GET /assessments`, `POST /assessments`, `GET /assessments/findings/all`, and `PUT /assessments/findings/{id}` (`commit 1b8f1b9`, `commit 79141e6`, `commit de6ede9`).
10. **Broken Frontend Choice Question Rendering:** Fixed `QuestionnaireRunnerView.tsx` checking `'Yes/No'` / `'Single Choice'` against seeded `'YesNo'` / `'SingleChoice'` types (`commit 806e70c`).
11. **Static Finding Mitigation Save:** Connected `RiskFindingsView.tsx` to `PUT /api/tprm/v1/assessments/findings/{id}` for real database persistence and audit logging (`commit 806e70c`).
12. **Hardcoded Fictional Users in `OrganizationAdminView.tsx`:** Replaced fictional names with live database queries against Table 5 roster, plus Create User Group, User Activation Toggle, Attribute Manager, and Integration Status tabs (`commit 1b25bdb`).
13. **Invisible White Headings & Missing Utility Classes in CSS:** Removed global `h1-h6 { color: #fff }` conflict in `index.css` and built complete Light Enterprise (`theme-light`) and Dark Enterprise (`theme-dark`) token and layout classes in `tprm.css` (`commit faef605`).
14. **Missing Hierarchical Login Portal:** Added AWS IAM-inspired `LoginView` supporting Organization -> Departments -> Groups -> Users -> Roles -> Permissions selection (`commit eebd75d`).
15. **Missing Authorized CSV Exports:** Added audited CSV export endpoints for Vendors, Assessments, Risk Findings, Audit Logs, and Questionnaire Templates (`commit 2f38b38`, `commit 3cf78db`, `commit de6ede9`).
