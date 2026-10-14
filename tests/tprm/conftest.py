"""Pytest configuration and fixtures for isolated TPRM test runs."""

import os

os.environ.setdefault("TPRM_ENV", "development")
os.environ.setdefault("TPRM_DEMO_PASSWORD", "test-password")
os.environ.setdefault("IRONCLAD_WEBHOOK_SECRET", "test-ironclad-secret")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.cadence_tprm.database import Base, get_db
from src.cadence_tprm.seed.seed_data import seed_database
from src.cadence_tprm.main import app

# Create in-memory SQLite database with StaticPool for test suite isolation
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Sets up schema and seeds authoritative data once for test session."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    seed_database(db)
    db.close()
    
    # Override FastAPI database dependency to use in-memory database
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    """Provides a transactional database session for unit tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
