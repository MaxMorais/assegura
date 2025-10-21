"""Test configuration and fixtures."""

import os
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

# Set testing environment variable before any imports
os.environ["TESTING"] = "true"

from src.api.main import app
from src.infrastructure.database import get_sync_db
from src.infrastructure.database.models.base import Base
# Force model imports to use testing types
from src.infrastructure.database.models import activity_model, persona_model, journey_models, action_library_models


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Set up test database schema once per test session."""
    # Drop all tables first to ensure clean schema
    for session in get_sync_db():
        Base.metadata.drop_all(bind=session.get_bind())
        Base.metadata.create_all(bind=session.get_bind())
        break  # Only need to do this once


@pytest.fixture(scope="function", autouse=True)
def cleanup_database():
    """Clean up database after each test to ensure isolation."""
    yield
    # Clean up test data after each test
    for session in get_sync_db():
        # Delete all data from tables in reverse dependency order
        session.execute(text("DELETE FROM activity_persona_links"))
        session.execute(text("DELETE FROM activities"))
        session.execute(text("DELETE FROM personas"))
        session.commit()
        break


@pytest.fixture
def db_session():
    """Provide a test database session."""
    for session in get_sync_db():
        yield session


@pytest.fixture
async def async_client():
    """Provide an async test client."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def client():
    """Provide a synchronous test client."""
    with TestClient(app) as client:
        yield client