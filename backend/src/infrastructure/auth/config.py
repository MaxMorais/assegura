"""Authentication configuration and factory.

Provides configuration management and factory functions for authentication
services with environment-based setup.
"""

import os
from typing import Optional

from .middleware import create_auth_dependencies
from .services import AuthenticationService
from .services import PasswordService
from .services import TokenService


class AuthConfig:
    """Configuration class for authentication services."""
    
    def __init__(self) -> None:
        """Initialize authentication configuration from environment."""
        # JWT Configuration
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.refresh_token_expire_days = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )
        
        # Security Configuration
        self.password_min_length = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
        self.require_password_complexity = os.getenv(
            "REQUIRE_PASSWORD_COMPLEXITY", "true"
        ).lower() == "true"
        
        # Session Configuration
        self.max_sessions_per_user = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))
        self.remember_me_expire_days = int(
            os.getenv("REMEMBER_ME_EXPIRE_DAYS", "30")
        )
    
    def validate(self) -> None:
        """Validate configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        
        if self.access_token_expire_minutes <= 0:
            raise ValueError("Access token expiration must be positive")
        
        if self.refresh_token_expire_days <= 0:
            raise ValueError("Refresh token expiration must be positive")
        
        if self.password_min_length < 8:
            raise ValueError("Password minimum length should be at least 8")


class AuthServiceFactory:
    """Factory for creating authentication services."""
    
    def __init__(self, config: Optional[AuthConfig] = None) -> None:
        """Initialize factory with configuration.
        
        Args:
            config: Authentication configuration (creates default if None)
        """
        self.config = config or AuthConfig()
        self._token_service: Optional[TokenService] = None
        self._password_service: Optional[PasswordService] = None
        self._auth_service: Optional[AuthenticationService] = None
    
    def create_token_service(self) -> TokenService:
        """Create or get token service instance.
        
        Returns:
            TokenService instance
        """
        if not self._token_service:
            self._token_service = TokenService(
                secret_key=self.config.jwt_secret_key,
                algorithm=self.config.jwt_algorithm,
                access_token_expire_minutes=self.config.access_token_expire_minutes,
                refresh_token_expire_days=self.config.refresh_token_expire_days
            )
        
        return self._token_service
    
    def create_password_service(self) -> PasswordService:
        """Create or get password service instance.
        
        Returns:
            PasswordService instance
        """
        if not self._password_service:
            self._password_service = PasswordService()
        
        return self._password_service
    
    def create_auth_service(self) -> AuthenticationService:
        """Create or get authentication service instance.
        
        Returns:
            AuthenticationService instance
        """
        if not self._auth_service:
            self._auth_service = AuthenticationService(
                token_service=self.create_token_service(),
                password_service=self.create_password_service()
            )
        
        return self._auth_service
    
    def create_auth_dependencies(
        self,
        get_consultant_by_id: callable,
        get_tenant_by_id: callable
    ) -> dict:
        """Create authentication dependencies for FastAPI.
        
        Args:
            get_consultant_by_id: Function to retrieve consultant by ID
            get_tenant_by_id: Function to retrieve tenant by ID
            
        Returns:
            Dictionary of authentication dependencies
        """
        return create_auth_dependencies(
            token_service=self.create_token_service(),
            get_consultant_by_id=get_consultant_by_id,
            get_tenant_by_id=get_tenant_by_id
        )


# Global factory instance (will be configured at startup)
auth_factory: Optional[AuthServiceFactory] = None


def initialize_auth(config: Optional[AuthConfig] = None) -> AuthServiceFactory:
    """Initialize global authentication factory.
    
    Args:
        config: Authentication configuration
        
    Returns:
        Configured AuthServiceFactory instance
    """
    global auth_factory
    
    if config:
        config.validate()
    
    auth_factory = AuthServiceFactory(config)
    return auth_factory


def get_auth_factory() -> AuthServiceFactory:
    """Get global authentication factory.
    
    Returns:
        AuthServiceFactory instance
        
    Raises:
        RuntimeError: If factory not initialized
    """
    if not auth_factory:
        raise RuntimeError(
            "Authentication factory not initialized. Call initialize_auth() first."
        )
    
    return auth_factory