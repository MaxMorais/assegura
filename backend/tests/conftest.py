"""Test configuration and fixtures."""

import os
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
import os
import pytest

# Set testing environment variable before any imports
os.environ["TESTING"] = "true"

from src.infrastructure.database import get_sync_db
from src.infrastructure.database.models.base import Base
# Force model imports to use testing types
from src.infrastructure.database.models import activity_model, persona_model

# Set testing environment
os.environ["TESTING"] = "true"


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Set up test database schema."""
    # Drop all tables first to ensure clean schema
    for session in get_sync_db():
        Base.metadata.drop_all(bind=session.get_bind())
        Base.metadata.create_all(bind=session.get_bind())
        break  # Only need to do this once


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