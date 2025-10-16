"""Database configuration for PostgreSQL connection.

This module provides configuration classes for database connectivity
following the research.md decisions for PostgreSQL with JSONb support
and multi-tenant data isolation.
"""

import os
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """PostgreSQL database configuration settings.

    Supports multi-tenant architecture with proper connection pooling
    per research.md recommendations.
    """

    # Database Connection
    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    name: str = Field(default="erpnext_test_automation", description="Database name")
    user: str = Field(description="Database username")
    password: str = Field(description="Database password")

    # Connection Pool Settings
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max pool overflow")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")

    # Multi-tenant Settings
    default_schema: str = Field(default="public", description="Default schema")
    enable_multi_tenant: bool = Field(
        default=True, description="Enable multi-tenant support"
    )

    # SSL Configuration
    ssl_mode: str = Field(
        default="prefer", description="SSL mode (disable/allow/prefer/require)"
    )
    ssl_cert: Optional[str] = Field(default=None, description="SSL certificate path")
    ssl_key: Optional[str] = Field(default=None, description="SSL key path")
    ssl_ca: Optional[str] = Field(
        default=None, description="SSL CA certificate path"
    )

    # Performance Settings
    echo_sql: bool = Field(default=False, description="Echo SQL queries for debugging")
    query_timeout: int = Field(default=30, description="Query timeout in seconds")

    class Config:
        """Pydantic configuration."""

        env_prefix = "DB_"
        case_sensitive = False

    @validator("port")
    def validate_port(cls, v: int) -> int:
        """Validate database port range."""
        if not 1 <= v <= 65535:
            raise ValueError("Database port must be between 1 and 65535")
        return v

    @validator("pool_size")
    def validate_pool_size(cls, v: int) -> int:
        """Validate connection pool size."""
        if v < 1:
            raise ValueError("Pool size must be at least 1")
        return v

    @validator("ssl_mode")
    def validate_ssl_mode(cls, v: str) -> str:
        """Validate SSL mode."""
        valid_modes = {
            "disable",
            "allow",
            "prefer",
            "require",
            "verify-ca",
            "verify-full",
        }
        if v not in valid_modes:
            raise ValueError(f"SSL mode must be one of {valid_modes}")
        return v

    def get_database_url(self, include_password: bool = True) -> str:
        """Generate PostgreSQL connection URL.

        Args:
            include_password: Whether to include password in URL

        Returns:
            PostgreSQL connection URL
        """
        password_part = f":{self.password}" if include_password else ""
        ssl_part = (
            f"?sslmode={self.ssl_mode}" if self.ssl_mode != "disable" else ""
        )

        return (
            f"postgresql://{self.user}{password_part}@"
            f"{self.host}:{self.port}/{self.name}{ssl_part}"
        )

    def get_async_database_url(self, include_password: bool = True) -> str:
        """Generate async PostgreSQL connection URL.

        Args:
            include_password: Whether to include password in URL

        Returns:
            Async PostgreSQL connection URL
        """
        url = self.get_database_url(include_password)
        return url.replace("postgresql://", "postgresql+asyncpg://")


class TestDatabaseConfig(DatabaseConfig):
    """Test database configuration.

    Inherits from main config but uses test-specific defaults.
    """

    name: str = Field(
        default="erpnext_test_automation_test", description="Test database name"
    )
    echo_sql: bool = Field(default=True, description="Echo SQL for test debugging")
    pool_size: int = Field(default=5, description="Smaller pool for tests")

    class Config:
        """Pydantic configuration for tests."""

        env_prefix = "TEST_DB_"


def get_database_config() -> DatabaseConfig:
    """Get database configuration instance.

    Returns appropriate config based on environment.

    Returns:
        Database configuration instance
    """
    if os.getenv("TESTING", "false").lower() == "true":
        return TestDatabaseConfig()
    return DatabaseConfig()


# Global configuration instance
database_config = get_database_config()
