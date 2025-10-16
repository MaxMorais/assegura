"""JWT token management and authentication services.

Handles JWT token creation, validation, and refresh for consultant authentication
with tenant-aware security.
"""

import secrets
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import Optional

try:
    import jwt
    from passlib.context import CryptContext
except ImportError as e:
    print(f"JWT/crypto dependencies not installed: {e}")
    print("Run 'pip install python-jose[cryptography] passlib[bcrypt]'")

from .models import Consultant
from .models import Tenant


class TokenService:
    """Service for JWT token management."""
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ) -> None:
        """Initialize token service.
        
        Args:
            secret_key: Secret key for JWT signing (generates if None)
            algorithm: JWT algorithm to use
            access_token_expire_minutes: Access token expiration in minutes
            refresh_token_expire_days: Refresh token expiration in days
        """
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(
        self,
        consultant: Consultant,
        tenant: Tenant,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token for consultant.
        
        Args:
            consultant: Consultant to create token for
            tenant: Tenant context
            expires_delta: Optional custom expiration
            
        Returns:
            JWT access token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": str(consultant.id),  # Subject (consultant ID)
            "email": consultant.email,
            "tenant_id": str(tenant.id),
            "tenant_subdomain": tenant.subdomain,
            "role": consultant.role.value,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        try:
            return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        except NameError:
            raise ImportError("JWT library not available")
    
    def create_refresh_token(
        self,
        consultant: Consultant,
        tenant: Tenant,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token for consultant.
        
        Args:
            consultant: Consultant to create token for
            tenant: Tenant context
            expires_delta: Optional custom expiration
            
        Returns:
            JWT refresh token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": str(consultant.id),
            "tenant_id": str(tenant.id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        try:
            return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        except NameError:
            raise ImportError("JWT library not available")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token expired
        except jwt.InvalidTokenError:
            return None  # Invalid token
        except NameError:
            raise ImportError("JWT library not available")
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired.
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is expired
        """
        try:
            jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return False
        except jwt.ExpiredSignatureError:
            return True
        except jwt.InvalidTokenError:
            return True  # Treat invalid tokens as expired
        except NameError:
            raise ImportError("JWT library not available")


class PasswordService:
    """Service for password hashing and verification."""
    
    def __init__(self) -> None:
        """Initialize password service."""
        try:
            self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        except NameError:
            print("Passlib not available - password service disabled")
            self.pwd_context = None
    
    def hash_password(self, password: str) -> str:
        """Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        if not self.pwd_context:
            raise ImportError("Passlib not available")
        
        if not password:
            raise ValueError("Password cannot be empty")
        
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            True if password matches
        """
        if not self.pwd_context:
            raise ImportError("Passlib not available")
        
        if not plain_password or not hashed_password:
            return False
        
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def needs_update(self, hashed_password: str) -> bool:
        """Check if password hash needs update.
        
        Args:
            hashed_password: Hashed password to check
            
        Returns:
            True if hash needs update
        """
        if not self.pwd_context:
            return False
        
        return self.pwd_context.needs_update(hashed_password)


class AuthenticationService:
    """Service for consultant authentication operations."""
    
    def __init__(
        self,
        token_service: TokenService,
        password_service: PasswordService
    ) -> None:
        """Initialize authentication service.
        
        Args:
            token_service: Token management service
            password_service: Password hashing service
        """
        self.token_service = token_service
        self.password_service = password_service
    
    def authenticate_consultant(
        self,
        email: str,
        password: str,
        tenant: Tenant,
        consultant: Consultant
    ) -> Optional[Dict[str, str]]:
        """Authenticate consultant and return tokens.
        
        Args:
            email: Consultant email
            password: Plain text password
            tenant: Tenant context
            consultant: Consultant entity
            
        Returns:
            Dictionary with access and refresh tokens if successful
        """
        # Verify consultant belongs to tenant
        if consultant.tenant_id != tenant.id:
            return None
        
        # Verify consultant is active
        if not consultant.is_active:
            return None
        
        # Verify tenant is active
        if not tenant.is_active():
            return None
        
        # Verify password
        if not consultant.password_hash:
            return None
        
        if not self.password_service.verify_password(password, consultant.password_hash):
            return None
        
        # Create tokens
        access_token = self.token_service.create_access_token(consultant, tenant)
        refresh_token = self.token_service.create_refresh_token(consultant, tenant)
        
        # Record login
        consultant.record_login()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def refresh_access_token(
        self,
        refresh_token: str,
        consultant: Consultant,
        tenant: Tenant
    ) -> Optional[str]:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            consultant: Consultant entity
            tenant: Tenant context
            
        Returns:
            New access token if successful
        """
        # Verify refresh token
        payload = self.token_service.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        # Verify token belongs to consultant and tenant
        if (
            payload.get("sub") != str(consultant.id) or
            payload.get("tenant_id") != str(tenant.id)
        ):
            return None
        
        # Verify consultant and tenant are still active
        if not consultant.is_active or not tenant.is_active():
            return None
        
        # Create new access token
        return self.token_service.create_access_token(consultant, tenant)
    
    def change_password(
        self,
        consultant: Consultant,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change consultant password.
        
        Args:
            consultant: Consultant entity
            current_password: Current plain text password
            new_password: New plain text password
            
        Returns:
            True if password was changed successfully
        """
        # Verify current password
        if not consultant.password_hash:
            return False
        
        if not self.password_service.verify_password(current_password, consultant.password_hash):
            return False
        
        # Hash new password
        new_hash = self.password_service.hash_password(new_password)
        consultant.password_hash = new_hash
        consultant._updated_at = datetime.utcnow()
        
        return True
    
    def set_password(self, consultant: Consultant, password: str) -> None:
        """Set consultant password (for admin use).
        
        Args:
            consultant: Consultant entity
            password: Plain text password
        """
        consultant.password_hash = self.password_service.hash_password(password)
        consultant._updated_at = datetime.utcnow()