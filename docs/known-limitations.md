# Known Limitations & Environmental Assumptions: Cadence TPRM Application

**Authority:** `Cadence_TPRM_Training.docx`  

---

## 1. External Integrations
- **Torii SaaS Management Integration:**
  - *Document Citation:* Section 4.2.3: *"For future iterations, Cadence may consider expanding automation by developing an integration with Torii to streamline the offboarding workflow through API-triggered deprovisioning and asset revocation."*
  - *Current Status:* Implemented via a resilient adapter pattern (`ToriiDeprovisioningAdapter`). In local and testing environments without active Torii API keys, the adapter operates in an explicit simulated mode, creating audit records and queuing simulated deprovisioning requests. Production deployment requires configuring `TORII_API_KEY` and `TORII_ENDPOINT`.
- **Live Ironclad Webhook Signatures:**
  - *Current Status:* Full webhook payload parsing and schema mapping (Table 9) are implemented and tested. In environments where no live Ironclad webhook secret is configured, an authorization bearer token or mock development signature is supported.

## 2. In-App vs. External Email Dispatch
- In development/local mode, notifications are persisted directly to the `notifications` table and rendered in the in-app notification center.
- SMTP / SendGrid email delivery can be activated by providing standard environment variables (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`).

## 3. Pre-existing Repository Scope
- The repository previously contained an evaluation fixture sandbox for PII Guard. All PII Guard endpoints and tests have been preserved under their own namespace to guarantee zero regressions for existing work.
