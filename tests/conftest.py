"""
Shared pytest fixtures.

Tests run with:
  - DEMO_MODE=true (so no Gmail/Anthropic credentials are needed - the mock
    analyzer and mock execution providers are used)
  - An isolated in-memory SQLite database per test, via dependency override
    of `get_db`. This means tests never touch the developer's app.db file
    and each test starts from a clean schema.
"""

import os

# Must be set before app modules are imported, since Settings() is
# instantiated at import time in app/config.py.
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    """A TestClient wired to a fresh in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def synced_client(client):
    """A client that has already synced the 8 demo emails."""
    response = client.post("/emails/sync")
    assert response.status_code == 200
    return client
