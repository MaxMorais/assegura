"""Database fixtures for testing."""

import pytest
from sqlalchemy.orm import Session

from src.infrastructure.database import get_sync_db


@pytest.fixture
def test_db_session():
    """Provide a test database session."""
    for session in get_sync_db():
        yield session