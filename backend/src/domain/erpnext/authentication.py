"""ERPNext API authentication models for ERPNext Test Automation Meta-Framework.

Provides authentication models and utilities for connecting to ERPNext instances
with proper credential management and security.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ERPNextCredentials(BaseModel):
    """Model for ERPNext API credentials."""

    api_key: str = Field(..., description="ERPNext API key")
    api_secret: str = Field(..., description="ERPNext API secret")

    @field_validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key format."""
        if not v or not v.strip():
            raise ValueError("API key is required")

        v = v.strip()

        # API keys should be non-empty strings
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


class ERPNextAuthToken(BaseModel):
    """Model for ERPNext authentication token with expiration."""

    access_token: str = Field(..., description="Access token for API calls")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    expires_at: Optional[datetime] = Field(default=None, description="Token expiration timestamp")

    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    def time_until_expiry(self) -> Optional[timedelta]:
        """Get time until token expires."""
        if not self.expires_at:
            return None
        return self.expires_at - datetime.utcnow()

    def should_refresh(self, buffer_minutes: int = 5) -> bool:
        """Check if token should be refreshed (with buffer time)."""
        if not self.expires_at:
            return False
        buffer_time = timedelta(minutes=buffer_minutes)
        return datetime.utcnow() >= (self.expires_at - buffer_time)


class ERPNextConnectionInfo(BaseModel):
    """Model for ERPNext connection information."""

    instance_id: UUID = Field(..., description="ERPNext instance ID")
    base_url: str = Field(..., description="ERPNext instance base URL")
    credentials: ERPNextCredentials = Field(..., description="API credentials")
    timeout: int = Field(default=30, description="Connection timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")

    @field_validator('base_url')
    def validate_base_url(cls, v):
        """Validate base URL format."""
        if not v or not v.strip():
            raise ValueError("Base URL is required")

        v = v.strip()

        if not v.startswith(('http://', 'https://')):
            raise ValueError("Base URL must start with http:// or https://")

        if v.endswith('/'):
            v = v.rstrip('/')

        return v

    @field_validator('timeout')
    def validate_timeout(cls, v):
        """Validate timeout value."""
        if v < 1:
            raise ValueError("Timeout must be at least 1 second")
        if v > 300:
            raise ValueError("Timeout cannot exceed 300 seconds")
        return v

    @field_validator('retry_attempts')
    def validate_retry_attempts(cls, v):
        """Validate retry attempts."""
        if v < 0:
            raise ValueError("Retry attempts cannot be negative")
        if v > 10:
            raise ValueError("Retry attempts cannot exceed 10")
        return v

    @field_validator('retry_delay')
    def validate_retry_delay(cls, v):
        """Validate retry delay."""
        if v < 0.1:
            raise ValueError("Retry delay must be at least 0.1 seconds")
        if v > 60.0:
            raise ValueError("Retry delay cannot exceed 60 seconds")
        return v


class ERPNextAuthRequest(BaseModel):
    """Model for ERPNext authentication request."""

    usr: str = Field(..., description="API key as username")
    pwd: str = Field(..., description="API secret as password")

    @classmethod
    def from_credentials(cls, credentials: ERPNextCredentials) -> 'ERPNextAuthRequest':
        """Create auth request from credentials."""
        return cls(
            usr=credentials.api_key,
            pwd=credentials.api_secret
        )


class ERPNextAuthResponse(BaseModel):
    """Model for ERPNext authentication response."""

    message: str = Field(..., description="Authentication result message")
    full_name: Optional[str] = Field(default=None, description="User full name")
    user: Optional[str] = Field(default=None, description="Authenticated user")
    api_key: Optional[str] = Field(default=None, description="API key (if generated)")
    api_secret: Optional[str] = Field(default=None, description="API secret (if generated)")

    def is_successful(self) -> bool:
        """Check if authentication was successful."""
        return "success" in self.message.lower() or self.user is not None


class ConnectionTestResult(BaseModel):
    """Model for ERPNext connection test results."""

    instance_id: UUID = Field(..., description="Tested instance ID")
    is_connected: bool = Field(..., description="Connection success status")
    response_time: Optional[float] = Field(default=None, description="Response time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if connection failed")
    erpnext_version: Optional[str] = Field(default=None, description="ERPNext version if connected")
    tested_at: datetime = Field(default_factory=datetime.utcnow, description="Test timestamp")

    def __str__(self) -> str:
        """String representation of connection test result."""
        status = "SUCCESS" if self.is_connected else "FAILED"
        return f"ConnectionTestResult(instance={self.instance_id}, status={status}, response_time={self.response_time})"


class AuthenticatedSession(BaseModel):
    """Model for authenticated ERPNext session."""

    instance_id: UUID = Field(..., description="ERPNext instance ID")
    session_token: Optional[str] = Field(default=None, description="Session token")
    auth_token: Optional[ERPNextAuthToken] = Field(default=None, description="Authentication token")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    last_used: datetime = Field(default_factory=datetime.utcnow, description="Last usage time")

    def is_valid(self) -> bool:
        """Check if the session is still valid."""
        if self.auth_token and self.auth_token.is_expired():
            return False
        return True

    def update_last_used(self) -> None:
        """Update the last used timestamp."""
        self.last_used = datetime.utcnow()

    def get_auth_header(self) -> dict:
        """Get authorization header for API requests."""
        if self.auth_token:
            return {"Authorization": f"{self.auth_token.token_type} {self.auth_token.access_token}"}
        elif self.session_token:
            return {"Cookie": f"sid={self.session_token}"}
        else:
            return {}