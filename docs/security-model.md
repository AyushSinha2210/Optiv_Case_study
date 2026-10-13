# Security Model Specification: Cadence TPRM Application

**Authority:** `Cadence_TPRM_Training.docx` Section 2.3, Section 6.1  

---

## 1. Threat Model & Security Posture

The TPRM application manages confidential enterprise vendor contracts, financial disclosures, cybersecurity posture reviews, and regulatory compliance records.

Key Invariants:
1. **Zero Client-Side Permission Trust:** The browser UI can hide buttons for convenience, but the FastAPI backend enforces strict authentication, role checks, and group membership validation on every single mutating endpoint.
2. **Immutable Audit Trail:** All state transitions (approval, rejection, risk creation, vendor status updates, offboarding) emit persistent audit records with actor email, timestamp, IP/session context, and structured payloads.
3. **No Credential or Sensitive Data Leakage:** Passwords (if local auth used) are hashed with salted bcrypt. Audit logs never store raw credentials or full sensitive file blobs.
4. **IDOR & Parameter Tampering Prevention:** Access to assessments and vendor updates verifies that the actor either belongs to `Vendor Risk Management Group` (Admin) or is the authorized business owner / reviewer group.

---

## 2. Authentication & Session Strategy

- **Tokens:** Signed JWT tokens or Secure Session identifiers containing `user_id`, `email`, and `organization_id`.
- **Roster Validation:** On each protected request, the security dependency resolves the user's active group memberships from the database.
- **CSRF & Origin Protection:** Strict CORS allowlist and JSON POST request barriers against cross-site exploitation.

---

## 3. Defense Against OWASP Top 10

- **A01: Broken Access Control:** Enforced via `require_tprm_admin`, `require_group_membership`, and `require_vendor_reviewer` dependencies. Approvals require `TPRM_ADMIN`.
- **A02: Cryptographic Failures:** Passwords hashed; SSL/TLS enforced for all external webhook interactions.
- **A03: Injection:** 100% parameterized queries via SQLAlchemy 2.0 ORM.
- **A04: Insecure Design:** Strict FSM state transitions. An assessment cannot jump from `Draft` to `Live` without undergoing review and explicit VRM approval (or qualifying for documented Tier 3 auto-approval `WR.T3.3`).
- **A05: Security Misconfiguration:** Strict schema validation with Pydantic v2.
- **A09: Security Logging & Monitoring:** Complete append-only audit trail in `audit_logs`.
