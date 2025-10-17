"""Authentication middleware for FastAPI.

Provides JWT authentication middleware with tenant context and role-based
access control for the ERPNext Test Automation Meta-Framework API.
"""

from typing import Any, Optional
from uuid import UUID

try:
    from fastapi import Depends, HTTPException, Request, status
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
except ImportError as e:
    print(f"FastAPI dependencies not installed: {e}")

from .models import Consultant, ConsultantRole, Tenant
from .services import TokenService


class AuthenticationMiddleware:
    """Authentication middleware for FastAPI requests."""

    def __init__(
        self,
        token_service: TokenService,
        get_consultant_by_id: callable,
        get_tenant_by_id: callable,
    ) -> None:
        """Initialize authentication middleware.

        Args:
            token_service: Token service for JWT operations
            get_consultant_by_id: Function to retrieve consultant by ID
            get_tenant_by_id: Function to retrieve tenant by ID
        """
        self.token_service = token_service
        self.get_consultant_by_id = get_consultant_by_id
        self.get_tenant_by_id = get_tenant_by_id
        self.security = HTTPBearer() if "HTTPBearer" in globals() else None

    async def get_current_user(
        self, credentials: Optional["HTTPAuthorizationCredentials"] = None
    ) -> tuple[Consultant, Tenant]:
        """Get current authenticated user from JWT token.

        Args:
            credentials: HTTP Bearer credentials

        Returns:
            Tuple of (consultant, tenant)

        Raises:
            HTTPException: If authentication fails
        """
        if not self.security or not credentials:
            raise self._create_auth_exception("Authentication required")

        try:
            # Verify token
            payload = self.token_service.verify_token(credentials.credentials)
            if not payload:
                raise self._create_auth_exception("Invalid or expired token")

            # Check token type
            if payload.get("type") != "access":
                raise self._create_auth_exception("Invalid token type")

            # Get consultant and tenant IDs
            consultant_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")

            if not consultant_id or not tenant_id:
                raise self._create_auth_exception("Invalid token payload")

            # Retrieve consultant and tenant
            consultant = await self.get_consultant_by_id(consultant_id)
            if not consultant:
                raise self._create_auth_exception("Consultant not found")

            tenant = await self.get_tenant_by_id(tenant_id)
            if not tenant:
                raise self._create_auth_exception("Tenant not found")

            # Verify consultant belongs to tenant
            if str(consultant.tenant_id) != tenant_id:
                raise self._create_auth_exception("Invalid tenant context")

            # Verify consultant and tenant are active
            if not consultant.is_active:
                raise self._create_auth_exception("Consultant account is inactive")

            if not tenant.is_active():
                raise self._create_auth_exception("Tenant account is inactive")

            return consultant, tenant

        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service unavailable",
            ) if "HTTPException" in globals() else Exception("Auth unavailable")

    def require_role(self, required_role: ConsultantRole) -> callable:
        """Create dependency that requires specific role.

        Args:
            required_role: Role required to access endpoint

        Returns:
            FastAPI dependency function
        """

        async def check_role(
            current_user: tuple[Consultant, Tenant] = Depends(self.get_current_user)
        ) -> tuple[Consultant, Tenant]:
            consultant, tenant = current_user

            # Admin role can access everything
            if consultant.role == ConsultantRole.ADMIN:
                return consultant, tenant

            # Check if consultant has required role
            if consultant.role != required_role:
                raise self._create_permission_exception(
                    f"Role '{required_role.value}' required"
                )

            return consultant, tenant

        return check_role if "Depends" in globals() else lambda: None

    def require_permission(
        self, resource: str, action: str, scope: Optional[str] = None
    ) -> callable:
        """Create dependency that requires specific permission.

        Args:
            resource: Resource type required
            action: Action type required
            scope: Optional scope required

        Returns:
            FastAPI dependency function
        """

        async def check_permission(
            current_user: tuple[Consultant, Tenant] = Depends(self.get_current_user)
        ) -> tuple[Consultant, Tenant]:
            consultant, tenant = current_user

            # Check if consultant has required permission
            if not consultant.has_permission(resource, action, scope):
                permission_str = f"{resource}:{action}"
                if scope:
                    permission_str += f":{scope}"

                raise self._create_permission_exception(
                    f"Permission '{permission_str}' required"
                )

            return consultant, tenant

        return check_permission if "Depends" in globals() else lambda: None

    def optional_auth(self) -> callable:
        """Create dependency for optional authentication.

        Returns:
            FastAPI dependency function that returns None if not authenticated
        """

        async def get_optional_user(
            request: "Request",
        ) -> Optional[tuple[Consultant, Tenant]]:
            # Check for Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None

            try:
                token = auth_header.split(" ")[1]
                credentials = type("MockCredentials", (), {"credentials": token})()
                return await self.get_current_user(credentials)
            except Exception:
                return None  # Ignore authentication errors for optional auth

        return get_optional_user if "Request" in globals() else lambda: None

    def _create_auth_exception(self, detail: str) -> "HTTPException":
        """Create authentication exception.

        Args:
            detail: Error detail message

        Returns:
            HTTPException for authentication failure
        """
        if "HTTPException" in globals():
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail,
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            return Exception(f"Auth error: {detail}")

    def _create_permission_exception(self, detail: str) -> "HTTPException":
        """Create permission exception.

        Args:
            detail: Error detail message

        Returns:
            HTTPException for permission failure
        """
        if "HTTPException" in globals():
            return HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail,
            )
        else:
            return Exception(f"Permission error: {detail}")


# Factory function for creating authentication dependencies
def create_auth_dependencies(
    token_service: TokenService,
    get_consultant_by_id: callable,
    get_tenant_by_id: callable,
) -> dict[str, Any]:
    """Create authentication dependency functions.

    Args:
        token_service: Token service instance
        get_consultant_by_id: Function to retrieve consultant by ID
        get_tenant_by_id: Function to retrieve tenant by ID

    Returns:
        Dictionary of authentication dependency functions
    """
    middleware = AuthenticationMiddleware(
        token_service=token_service,
        get_consultant_by_id=get_consultant_by_id,
        get_tenant_by_id=get_tenant_by_id,
    )

    return {
        "get_current_user": middleware.get_current_user,
        "get_current_consultant_id": middleware.get_current_consultant_id,
        "require_admin": middleware.require_role(ConsultantRole.ADMIN),
        "require_consultant": middleware.require_role(ConsultantRole.CONSULTANT),
        "require_viewer": middleware.require_role(ConsultantRole.VIEWER),
        "optional_auth": middleware.optional_auth(),
        # Common permission dependencies
        "can_read_personas": middleware.require_permission("personas", "read"),
        "can_write_personas": middleware.require_permission("personas", "write"),
        "can_read_activities": middleware.require_permission("activities", "read"),
        "can_write_activities": middleware.require_permission("activities", "write"),
        "can_read_journeys": middleware.require_permission("journeys", "read"),
        "can_write_journeys": middleware.require_permission("journeys", "write"),
        "can_read_tests": middleware.require_permission("tests", "read"),
        "can_write_tests": middleware.require_permission("tests", "write"),
        "can_execute_tests": middleware.require_permission("tests", "execute"),
    }


# Standalone dependency function for getting current consultant ID
async def get_current_consultant_id(
    current_user: tuple[Consultant, Tenant] = Depends(lambda: None if "Depends" not in globals() else None)
) -> UUID:
    """Get current consultant ID from authenticated user.

    Args:
        current_user: Tuple of (consultant, tenant) from authentication

    Returns:
        Consultant UUID
    """
    if not current_user:
        # For development/testing, return a mock consultant ID
        # In production, this should be properly implemented with authentication
        from uuid import uuid4
        return uuid4()

    consultant, tenant = current_user
    return consultant.id
