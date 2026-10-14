import os

# Test-only credentials must be explicit and are never production defaults.
os.environ.setdefault("TPRM_ENV", "development")
os.environ.setdefault("TPRM_DEMO_PASSWORD", "test-password")
os.environ.setdefault("DEMO_LOGIN_PASSWORD", "test-password")
os.environ.setdefault("IRONCLAD_WEBHOOK_SECRET", "test-ironclad-secret")
