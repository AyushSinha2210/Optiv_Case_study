"""Application configuration and environment management."""

import os
from pathlib import Path
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class TPRMSettings(BaseModel):
    APP_NAME: str = "Cadence Third-Party Risk Management"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    
    # SQLite Database default
    DATABASE_PATH: Path = BASE_DIR / "cadence_tprm.db"
    DATABASE_URL: str = Field(default="")
    
    JWT_SECRET: str = Field(default="cadence-tprm-enterprise-secret-key-2026-optiv")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60 * 24  # 24 hours
    
    # SLA & Scheduler Configuration
    DAILY_RUN_HOUR: int = 1  # 01:00 UTC
    
    # Integrations
    TORII_API_KEY: str = Field(default="simulated-torii-key")
    TORII_ENDPOINT: str = Field(default="https://api.torii.com/v1")
    IRONCLAD_WEBHOOK_SECRET: str = Field(default="ironclad-whsec-cadence-2026")
    
    def model_post_init(self, __context):
        if not self.DATABASE_URL:
            # Normalized SQLite connection URL
            db_file_str = str(self.DATABASE_PATH).replace("\\", "/")
            self.DATABASE_URL = f"sqlite:///{db_file_str}"

settings = TPRMSettings(
    ENVIRONMENT=os.getenv("TPRM_ENV", "development"),
    DATABASE_URL=os.getenv("DATABASE_URL", ""),
    JWT_SECRET=os.getenv("JWT_SECRET", "cadence-tprm-enterprise-secret-key-2026-optiv")
)
