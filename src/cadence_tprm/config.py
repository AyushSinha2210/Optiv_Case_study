"""Application configuration and environment management."""

import os
import secrets
from pathlib import Path
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class TPRMSettings(BaseModel):
    APP_NAME: str = "Cadence Third-Party Risk Management"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    DATABASE_PATH: Path = BASE_DIR / "cadence_tprm.db"
    DATABASE_URL: str = Field(default="")
    JWT_SECRET: str = Field(default="")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    DAILY_RUN_HOUR: int = 1
    TORII_API_KEY: str = Field(default="")
    TORII_ENDPOINT: str = Field(default="https://api.torii.com/v1")
    IRONCLAD_WEBHOOK_SECRET: str = Field(default="")
    CORS_ORIGINS: str = Field(default="http://localhost:5173,http://127.0.0.1:5173")
    DEMO_LOGIN_PASSWORD: str = Field(default="")

    def model_post_init(self, __context):
        environment = self.ENVIRONMENT.lower().strip()
        production_like = environment in {"production", "staging", "prod"}
        missing = []
        if not self.JWT_SECRET:
            missing.append("JWT_SECRET")
        if not self.IRONCLAD_WEBHOOK_SECRET:
            missing.append("IRONCLAD_WEBHOOK_SECRET")
        if production_like and missing:
            raise ValueError("Missing required production secrets: " + ", ".join(missing))
        if not self.JWT_SECRET:
            self.JWT_SECRET = secrets.token_urlsafe(32)
        if not self.DATABASE_URL:
            if production_like:
                raise ValueError("DATABASE_URL is required outside development")
            db_file_str = str(self.DATABASE_PATH).replace("\\", "/")
            self.DATABASE_URL = f"sqlite:///{db_file_str}"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = TPRMSettings(
    ENVIRONMENT=os.getenv("TPRM_ENV", "development"),
    DATABASE_URL=os.getenv("DATABASE_URL", ""),
    JWT_SECRET=os.getenv("JWT_SECRET", ""),
    TORII_API_KEY=os.getenv("TORII_API_KEY", ""),
    TORII_ENDPOINT=os.getenv("TORII_ENDPOINT", "https://api.torii.com/v1"),
    IRONCLAD_WEBHOOK_SECRET=os.getenv("IRONCLAD_WEBHOOK_SECRET", ""),
    CORS_ORIGINS=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"),
    DEMO_LOGIN_PASSWORD=os.getenv("TPRM_DEMO_PASSWORD", ""),
)
