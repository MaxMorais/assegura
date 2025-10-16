"""Multi-tenant authentication models and domain entities.

Implements consultant authentication with tenant isolation following
DDD patterns and constitutional requirements.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from ...domain.base import AggregateRoot, Entity, ValueObject


class ConsultantRole(str, Enum):
    """Consultant roles within the system."""

    ADMIN = "admin"  # Full system access
    CONSULTANT = "consultant"  # Standard consultant access
    VIEWER = "viewer"  # Read-only access


class TenantStatus(str, Enum):
    """Tenant status enumeration."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    INACTIVE = "inactive"


class Permission(ValueObject):
    """Permission value object for role-based access control."""

    def __init__(self, resource: str, action: str, scope: Optional[str] = None) -> None:
        """Initialize permission.

        Args:
            resource: Resource type (e.g., 'personas', 'activities')
            action: Action type (e.g., 'read', 'write', 'delete')
            scope: Optional scope for fine-grained permissions
        """
        if not resource or not resource.strip():
            raise ValueError("Resource cannot be empty")
        if not action or not action.strip():
            raise ValueError("Action cannot be empty")

        self.resource = resource.lower().strip()
        self.action = action.lower().strip()
        self.scope = scope.lower().strip() if scope else None

    def __str__(self) -> str:
        """String representation of permission."""
        if self.scope:
            return f"{self.resource}:{self.action}:{self.scope}"
        return f"{self.resource}:{self.action}"

    def matches(self, resource: str, action: str, scope: Optional[str] = None) -> bool:
        """Check if this permission matches the given parameters.

        Args:
            resource: Resource to check
            action: Action to check
            scope: Optional scope to check

        Returns:
            True if permission matches
        """
        return (
            self.resource == resource.lower()
            and self.action == action.lower()
            and (self.scope is None or self.scope == (scope.lower() if scope else None))
        )


class Tenant(AggregateRoot):
    """Tenant aggregate root for multi-tenant architecture."""

    def __init__(
        self,
        name: str,
        subdomain: str,
        status: TenantStatus = TenantStatus.PENDING,
        settings: Optional[dict] = None,
    ) -> None:
        """Initialize tenant.

        Args:
            name: Tenant display name
            subdomain: Unique subdomain identifier
            status: Tenant status
            settings: Optional tenant-specific settings
        """
        super().__init__()

        if not name or not name.strip():
            raise ValueError("Tenant name cannot be empty")
        if not subdomain or not subdomain.strip():
            raise ValueError("Tenant subdomain cannot be empty")

        self.name = name.strip()
        self.subdomain = subdomain.lower().strip()
        self.status = status
        self.settings = settings or {}

        # Validate subdomain format (basic validation)
        if not self.subdomain.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Subdomain must be alphanumeric with hyphens or underscores"
            )

    def activate(self) -> None:
        """Activate the tenant."""
        if self.status == TenantStatus.INACTIVE:
            raise ValueError("Cannot activate inactive tenant")
        self.status = TenantStatus.ACTIVE
        self._updated_at = datetime.utcnow()

    def suspend(self) -> None:
        """Suspend the tenant."""
        if self.status == TenantStatus.INACTIVE:
            raise ValueError("Cannot suspend inactive tenant")
        self.status = TenantStatus.SUSPENDED
        self._updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the tenant."""
        self.status = TenantStatus.INACTIVE
        self._updated_at = datetime.utcnow()

    def update_settings(self, new_settings: dict) -> None:
        """Update tenant settings.

        Args:
            new_settings: New settings to merge
        """
        self.settings.update(new_settings)
        self._updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self.status == TenantStatus.ACTIVE


class Consultant(Entity):
    """Consultant entity for authentication and authorization."""

    def __init__(
        self,
        tenant_id: UUID,
        email: str,
        first_name: str,
        last_name: str,
        role: ConsultantRole = ConsultantRole.CONSULTANT,
        permissions: Optional[list[Permission]] = None,
        is_active: bool = True,
    ) -> None:
        """Initialize consultant.

        Args:
            tenant_id: ID of the tenant this consultant belongs to
            email: Consultant email (unique within tenant)
            first_name: First name
            last_name: Last name
            role: Consultant role
            permissions: Additional permissions beyond role defaults
            is_active: Whether consultant is active
        """
        super().__init__()

        if not tenant_id:
            raise ValueError("Tenant ID is required")
        if not email or not email.strip():
            raise ValueError("Email cannot be empty")
        if "@" not in email:
            raise ValueError("Invalid email format")
        if not first_name or not first_name.strip():
            raise ValueError("First name cannot be empty")
        if not last_name or not last_name.strip():
            raise ValueError("Last name cannot be empty")

        self.tenant_id = tenant_id
        self.email = email.lower().strip()
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        self.role = role
        self.permissions = permissions or []
        self.is_active = is_active
        self.last_login: Optional[datetime] = None
        self.password_hash: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get consultant's full name."""
        return f"{self.first_name} {self.last_name}"

    def activate(self) -> None:
        """Activate the consultant."""
        self.is_active = True
        self._updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the consultant."""
        self.is_active = False
        self._updated_at = datetime.utcnow()

    def update_role(self, new_role: ConsultantRole) -> None:
        """Update consultant role.

        Args:
            new_role: New role to assign
        """
        self.role = new_role
        self._updated_at = datetime.utcnow()

    def add_permission(self, permission: Permission) -> None:
        """Add additional permission.

        Args:
            permission: Permission to add
        """
        if permission not in self.permissions:
            self.permissions.append(permission)
            self._updated_at = datetime.utcnow()

    def remove_permission(self, permission: Permission) -> None:
        """Remove permission.

        Args:
            permission: Permission to remove
        """
        if permission in self.permissions:
            self.permissions.remove(permission)
            self._updated_at = datetime.utcnow()

    def has_permission(
        self, resource: str, action: str, scope: Optional[str] = None
    ) -> bool:
        """Check if consultant has specific permission.

        Args:
            resource: Resource to check
            action: Action to check
            scope: Optional scope to check

        Returns:
            True if consultant has permission
        """
        if not self.is_active:
            return False

        # Check role-based permissions
        role_permissions = self._get_role_permissions()
        for perm in role_permissions:
            if perm.matches(resource, action, scope):
                return True

        # Check additional permissions
        for perm in self.permissions:
            if perm.matches(resource, action, scope):
                return True

        return False

    def record_login(self) -> None:
        """Record successful login."""
        self.last_login = datetime.utcnow()
        self._updated_at = datetime.utcnow()

    def _get_role_permissions(self) -> list[Permission]:
        """Get permissions based on role.

        Returns:
            List of permissions for the consultant's role
        """
        if self.role == ConsultantRole.ADMIN:
            return [
                Permission("*", "*"),  # Full access to everything
            ]
        elif self.role == ConsultantRole.CONSULTANT:
            return [
                Permission("personas", "read"),
                Permission("personas", "write"),
                Permission("activities", "read"),
                Permission("activities", "write"),
                Permission("journeys", "read"),
                Permission("journeys", "write"),
                Permission("tests", "read"),
                Permission("tests", "write"),
                Permission("tests", "execute"),
            ]
        elif self.role == ConsultantRole.VIEWER:
            return [
                Permission("personas", "read"),
                Permission("activities", "read"),
                Permission("journeys", "read"),
                Permission("tests", "read"),
            ]

        return []
