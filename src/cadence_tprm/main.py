"""Cadence TPRM FastAPI Application Entrypoint.

Registers models, ensures database tables exist, executes idempotent seed,
and mounts all /api/tprm/v1 routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.cadence_tprm.config import settings
from src.cadence_tprm.database import engine, Base, SessionLocal
from src.cadence_tprm.seed.seed_data import seed_database
from src.cadence_tprm.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and seed database
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    # Shutdown

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Third-Party Risk Management platform for Cadence Financial Group.",
    lifespan=lifespan
)

# Enable CORS for local Vite development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all TPRM API routes
app.include_router(api_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/api/health")
def api_health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }
