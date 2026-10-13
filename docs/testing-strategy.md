# Testing Strategy Specification: Cadence TPRM Application

**Test Frameworks:** pytest (Backend), Vitest/Playwright & React Testing Library (Frontend)  
**Objective:** Complete coverage of business logic, rules, workflow FSM, permissions, and edge cases.  

---

## 1. Test Pyramid & Scope

1. **Unit Tests (`tests/tprm/unit/`):**
   - **Vendor Classification:** Validation of Table 9 attributes (Type, Criticality, Category, Tier, PVC, Business Owner).
   - **Conditional Show Logic (`CL.1` to `CL.14`):** Dynamic visibility toggling for dependent questions.
   - **Risk Scoring Rules (`QR.1` to `QR.90`):** Accurate inherent risk scoring, Control ID mappings (`QRC_*`), and score averaging.
   - **SLA & Date Math:** Correct calculation of 9d, 4d, 5+4=9d, 10+4=14d, 15+4=19d, 275d (Tier 1), and 640d (Tier 2/3).
   - **RBAC & Authorization:** Least-privilege validation, ensuring only TPRM Admin can approve/reject.

2. **Integration Tests (`tests/tprm/integration/`):**
   - **Workflow Engine FSM:**
     - Onboarding routing to all 5 categories (`WR.ON.1` to `WR.ON.5`) and Tier 3 (`WR.ON.6`).
     - State transitions: `New` -> `Launching` -> `In Review` -> `Live` / `Review Reject` -> `Closed`.
     - Invalid / unauthorized transitions blocked with HTTP 400 / 403.
     - Tier 3 auto-approval (`WR.T3.3` / `QR.73`) verified end-to-end.
   - **Questionnaire Submission & Findings:** Persistence of responses, generation of `risk_findings`, and assignment of department-specific tasks.
   - **Reassessment Daily Job:** Simulation of date boundaries (275d and 640d) triggering new assessment generation and copying prior responses.
   - **Ironclad Webhook Ingestion:** Idempotent processing of contract intake payloads.

3. **Frontend UI Tests & Production Build:**
   - Production Vite TypeScript compilation (`tsc -b && vite build`).
   - Linting with zero syntax or import errors.
   - Real interactive rendering of all major views.
