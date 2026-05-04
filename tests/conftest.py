"""Shared pytest fixtures: in-memory SQLite + FastAPI TestClient.

Each test function gets a fresh database, so tests are order-independent.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.main import app


@pytest.fixture
def client():
    # Brand-new in-memory SQLite per test, with StaticPool so the same
    # connection is reused across the request lifecycle.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def _override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    # Construct TestClient WITHOUT a `with` block so FastAPI startup events
    # (which would call the real init_db on the production sqlite file) are
    # skipped. We've already created tables on the in-memory engine above.
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
