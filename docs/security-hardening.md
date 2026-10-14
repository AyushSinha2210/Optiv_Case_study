# Security hardening status

This branch applies the following controls:

- Partial document extraction stops the authoritative pipeline before redaction and release.
- TPRM requests require a signed bearer token; the X-User-Email adapter is development/test-only.
- Login requires a configured password and no longer creates arbitrary fallback users.
- Ironclad webhooks require a fresh HMAC-SHA256 signature using
  X-Ironclad-Timestamp and X-Ironclad-Signature.
- Default production secrets are removed. Staging/production require
  JWT_SECRET, IRONCLAD_WEBHOOK_SECRET, and DATABASE_URL.
- CORS uses an explicit CORS_ORIGINS allowlist.
- Raw extracted text and entity values are not returned to the browser.
- Audit details are recursively sanitized and webhook bodies are never persisted.
- RapidOCR is optional; if it is selected but unavailable, the OCR factory falls
  back to Tesseract. The external Tesseract binary is still required for OCR.

Required production configuration must be supplied by the deployment environment,
not committed to Git:

TPRM_ENV=production
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET=<secret-manager-value>
IRONCLAD_WEBHOOK_SECRET=<secret-manager-value>
CORS_ORIGINS=https://trusted-frontend.example

Live OneTrust/Torii/SMTP credentials and deployment-specific PostgreSQL
migrations still require the actual integration environments; this code cannot
invent those external credentials.
