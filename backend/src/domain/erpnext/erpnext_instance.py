"""ERPNext Instance domain entity for ERPNext Test Automation Meta-Framework.

Represents ERPNext system connections with authentication and validation
capabilities for test execution environments.
"""

import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
from uuid import UUID

from pydantic import Field, field_validator

from src.domain.base_entity import BaseEntity


class ERPNextInstance(BaseEntity):
    """Domain entity representing an ERPNext instance connection.

    An ERPNext instance defines the connection parameters and authentication
    credentials needed to interact with a specific ERPNext installation
    for test execution and validation.
    """

    # Core instance fields
    name: str = Field(..., description="Unique identifier for the ERPNext instance")
    base_url: str = Field(..., description="Base URL of the ERPNext instance")
    api_key: str = Field(..., description="Encrypted API key for authentication")
    api_secret: str = Field(..., description="Encrypted API secret for authentication")
    consultant_id: UUID = Field(..., description="ID of the consultant owning this instance")
    is_active: bool = Field(default=True, description="Whether the instance connection is active")
    last_connected: Optional[datetime] = Field(default=None, description="Timestamp of last successful connection")

    @field_validator('name')
    def validate_name(cls, v):
        """Validate instance name."""
        if not v or not v.strip():
            raise ValueError("Instance name is required")

        v = v.strip()

        if len(v) < 2:
            raise ValueError("Instance name must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Instance name must not exceed 255 characters")

        # Check for invalid characters (allow letters, numbers, spaces, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", v):
            raise ValueError(
                "Instance name can only contain letters, numbers, spaces, hyphens, and underscores"
            )

        return v

    @field_validator('base_url')
    def validate_base_url(cls, v):
        """Validate ERPNext instance base URL."""
        if not v or not v.strip():
            raise ValueError("Base URL is required")

        v = v.strip()

        # Parse URL to validate format
        try:
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception:
            raise ValueError("Invalid URL format")

        # Must be HTTP or HTTPS
        if parsed.scheme not in ['http', 'https']:
            raise ValueError("URL must use HTTP or HTTPS protocol")

        # Remove trailing slash if present
        if v.endswith('/'):
            v = v.rstrip('/')

        return v

    @field_validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key format."""
        if not v or not v.strip():
            raise ValueError("API key is required")

        v = v.strip()

        # API keys should be non-empty strings (exact format depends on ERPNext)
        if len(v) < 10:
            raise ValueError("API key appears to be too short")

        if len(v) > 500:
            raise ValueError("API key appears to be too long")

        return v

    @field_validator('api_secret')
    def validate_api_secret(cls, v):
        """Validate API secret format."""
        if not v or not v.strip():
            raise ValueError("API secret is required")

        v = v.strip()

        # API secrets should be non-empty strings
        if len(v) < 10:
            raise ValueError("API secret appears to be too short")

        if len(v) > 500:
            raise ValueError("API secret appears to be too long")

        return v

    def mark_connected(self) -> None:
        """Mark the instance as successfully connected."""
        self.last_connected = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the instance connection."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate the instance connection."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def get_connection_info(self) -> dict:
        """Get connection information for API calls (without sensitive data)."""
        return {
            'id': str(self.id),
            'name': self.name,
            'base_url': self.base_url,
            'is_active': self.is_active,
            'last_connected': self.last_connected.isoformat() if self.last_connected else None,
        }

    def is_connection_recent(self, minutes: int = 30) -> bool:
        """Check if the instance was connected within the specified minutes."""
        if not self.last_connected:
            return False

        time_diff = datetime.utcnow() - self.last_connected
        return time_diff.total_seconds() < (minutes * 60)

    def __str__(self) -> str:
        """String representation of the ERPNext instance."""
        return f"ERPNextInstance(name='{self.name}', url='{self.base_url}', active={self.is_active})"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"ERPNextInstance("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"base_url='{self.base_url}', "
            f"consultant_id={self.consultant_id}, "
            f"is_active={self.is_active}, "
            f"last_connected={self.last_connected}"
            f")"
        )