"""Persona domain entity for ERPNext Test Automation Meta-Framework.

Represents test personas that define user types with specific roles and permissions
within the ERPNext system for test automation purposes.
"""

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from ..base_entity import BaseEntity
from .erpnext_roles import ERPNextRole, validate_erpnext_roles
from .exceptions import PersonaValidationError


class Persona(BaseEntity):
    """Domain entity representing a test persona.

    A persona defines a specific user type with associated ERPNext roles
    and permissions that can be used in test scenarios.
    """

    def __init__(
        self,
        name: str,
        description: str,
        erpnext_roles: list[str],
        permissions: Optional[str] = None,
        is_active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        version: int = 1,
    ):
        """Initialize persona entity.

        Args:
            name: Unique name for the persona
            description: Description of the persona's purpose
            erpnext_roles: List of ERPNext role names
            permissions: Comma-separated permission strings
            is_active: Whether the persona is active
            id: Unique identifier (auto-generated if None)
            created_at: Creation timestamp
            updated_at: Last update timestamp
            version: Entity version for optimistic locking

        Raises:
            PersonaValidationError: If validation fails
        """
        super().__init__(id, created_at, updated_at, version)

        self._name: str = ""
        self._description: str = ""
        self._erpnext_roles: list[str] = []
        self._permissions: str = ""
        self._is_active: bool = True

        # Validate and set all fields
        self.set_name(name)
        self.set_description(description)
        self.set_erpnext_roles(erpnext_roles)
        self.set_permissions(permissions or "")
        self.set_is_active(is_active)

    @property
    def name(self) -> str:
        """Get persona name."""
        return self._name

    @property
    def description(self) -> str:
        """Get persona description."""
        return self._description

    @property
    def erpnext_roles(self) -> list[str]:
        """Get ERPNext roles as list."""
        return self._erpnext_roles.copy()

    @property
    def erpnext_roles_str(self) -> str:
        """Get ERPNext roles as comma-separated string."""
        return ",".join(self._erpnext_roles)

    @property
    def permissions(self) -> str:
        """Get permissions string."""
        return self._permissions

    @property
    def permissions_list(self) -> list[str]:
        """Get permissions as list."""
        if not self._permissions:
            return []
        return [p.strip() for p in self._permissions.split(",") if p.strip()]

    @property
    def is_active(self) -> bool:
        """Get active status."""
        return self._is_active

    def set_name(self, name: str) -> None:
        """Set persona name with validation.

        Args:
            name: Persona name

        Raises:
            PersonaValidationError: If name is invalid
        """
        if not name or not name.strip():
            raise PersonaValidationError("Persona name is required")

        name = name.strip()

        if len(name) < 2:
            raise PersonaValidationError(
                "Persona name must be at least 2 characters long"
            )

        if len(name) > 255:
            raise PersonaValidationError("Persona name must not exceed 255 characters")

        # Check for invalid characters (allow letters, numbers, spaces, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", name):
            raise PersonaValidationError(
                "Persona name can only contain letters, numbers, spaces, hyphens, and underscores"
            )

        self._name = name
        self._mark_as_modified()

    def set_description(self, description: str) -> None:
        """Set persona description with validation.

        Args:
            description: Persona description

        Raises:
            PersonaValidationError: If description is invalid
        """
        if not description or not description.strip():
            raise PersonaValidationError("Persona description is required")

        description = description.strip()

        if len(description) < 10:
            raise PersonaValidationError(
                "Persona description must be at least 10 characters long"
            )

        if len(description) > 2000:
            raise PersonaValidationError(
                "Persona description must not exceed 2000 characters"
            )

        self._description = description
        self._mark_as_modified()

    def set_erpnext_roles(self, roles: list[str]) -> None:
        """Set ERPNext roles with validation.

        Args:
            roles: List of ERPNext role names

        Raises:
            PersonaValidationError: If roles are invalid
        """
        if not roles:
            raise PersonaValidationError("At least one ERPNext role is required")

        # Validate each role
        validate_erpnext_roles(roles)

        # Remove duplicates while preserving order
        unique_roles = []
        seen = set()
        for role in roles:
            role = role.strip()
            if role and role not in seen:
                unique_roles.append(role)
                seen.add(role)

        if not unique_roles:
            raise PersonaValidationError("At least one valid ERPNext role is required")

        self._erpnext_roles = unique_roles
        self._mark_as_modified()

    def set_permissions(self, permissions: str) -> None:
        """Set permissions string with validation.

        Args:
            permissions: Comma-separated permission strings

        Raises:
            PersonaValidationError: If permissions format is invalid
        """
        if not permissions:
            self._permissions = ""
            self._mark_as_modified()
            return

        permissions = permissions.strip()

        if len(permissions) > 1000:
            raise PersonaValidationError(
                "Permissions string must not exceed 1000 characters"
            )

        # Validate permission format: action:resource or action:*
        permission_list = [p.strip() for p in permissions.split(",") if p.strip()]

        for permission in permission_list:
            if not self._is_valid_permission_format(permission):
                raise PersonaValidationError(
                    f"Invalid permission format: '{permission}'. "
                    "Use format 'action:resource' (e.g., 'read:sales', 'write:*')"
                )

        self._permissions = permissions
        self._mark_as_modified()

    def set_is_active(self, is_active: bool) -> None:
        """Set active status.

        Args:
            is_active: Whether persona is active
        """
        self._is_active = bool(is_active)
        self._mark_as_modified()

    def add_erpnext_role(self, role: str) -> None:
        """Add an ERPNext role to the persona.

        Args:
            role: ERPNext role name to add

        Raises:
            PersonaValidationError: If role is invalid
        """
        role = role.strip()
        if not role:
            raise PersonaValidationError("Role name cannot be empty")

        # Validate the role
        validate_erpnext_roles([role])

        if role not in self._erpnext_roles:
            self._erpnext_roles.append(role)
            self._mark_as_modified()

    def remove_erpnext_role(self, role: str) -> bool:
        """Remove an ERPNext role from the persona.

        Args:
            role: ERPNext role name to remove

        Returns:
            True if role was removed, False if not found

        Raises:
            PersonaValidationError: If removing role would leave persona with no roles
        """
        if len(self._erpnext_roles) <= 1:
            raise PersonaValidationError(
                "Cannot remove role - persona must have at least one role"
            )

        if role in self._erpnext_roles:
            self._erpnext_roles.remove(role)
            self._mark_as_modified()
            return True

        return False

    def add_permission(self, permission: str) -> None:
        """Add a permission to the persona.

        Args:
            permission: Permission string to add (format: action:resource)

        Raises:
            PersonaValidationError: If permission format is invalid
        """
        permission = permission.strip()
        if not permission:
            raise PersonaValidationError("Permission cannot be empty")

        if not self._is_valid_permission_format(permission):
            raise PersonaValidationError(
                f"Invalid permission format: '{permission}'. "
                "Use format 'action:resource' (e.g., 'read:sales', 'write:*')"
            )

        current_permissions = self.permissions_list
        if permission not in current_permissions:
            current_permissions.append(permission)
            self._permissions = ",".join(current_permissions)
            self._mark_as_modified()

    def remove_permission(self, permission: str) -> bool:
        """Remove a permission from the persona.

        Args:
            permission: Permission string to remove

        Returns:
            True if permission was removed, False if not found
        """
        current_permissions = self.permissions_list
        if permission in current_permissions:
            current_permissions.remove(permission)
            self._permissions = ",".join(current_permissions)
            self._mark_as_modified()
            return True

        return False

    def has_permission(self, action: str, resource: str) -> bool:
        """Check if persona has specific permission.

        Args:
            action: Action to check (read, write, create, delete, admin)
            resource: Resource to check (or * for all)

        Returns:
            True if persona has the permission
        """
        permissions = self.permissions_list

        # Check for exact match
        exact_permission = f"{action}:{resource}"
        if exact_permission in permissions:
            return True

        # Check for wildcard action
        wildcard_action = f"{action}:*"
        if wildcard_action in permissions:
            return True

        # Check for admin permissions (admin:* or admin:system)
        if "admin:*" in permissions or "admin:system" in permissions:
            return True

        return False

    def has_erpnext_role(self, role: str) -> bool:
        """Check if persona has specific ERPNext role.

        Args:
            role: ERPNext role name to check

        Returns:
            True if persona has the role
        """
        return role in self._erpnext_roles

    def deactivate(self) -> None:
        """Deactivate the persona."""
        self.set_is_active(False)

    def activate(self) -> None:
        """Activate the persona."""
        self.set_is_active(True)

    def get_effective_permissions(self) -> set[str]:
        """Get all effective permissions including role-based permissions.

        Returns:
            Set of all effective permissions
        """
        permissions = set(self.permissions_list)

        # Add role-based permissions
        for role in self._erpnext_roles:
            role_permissions = ERPNextRole.get_role_permissions(role)
            permissions.update(role_permissions)

        return permissions

    def validate(self) -> None:
        """Validate the entire persona entity.

        Raises:
            PersonaValidationError: If validation fails
        """
        # Re-validate all fields
        temp_name = self._name
        temp_description = self._description
        temp_roles = self._erpnext_roles.copy()
        temp_permissions = self._permissions

        # Reset and re-validate to ensure consistency
        self._name = ""
        self._description = ""
        self._erpnext_roles = []
        self._permissions = ""

        try:
            self.set_name(temp_name)
            self.set_description(temp_description)
            self.set_erpnext_roles(temp_roles)
            self.set_permissions(temp_permissions)
        except PersonaValidationError:
            # Restore original values if validation fails
            self._name = temp_name
            self._description = temp_description
            self._erpnext_roles = temp_roles
            self._permissions = temp_permissions
            raise

    def to_dict(self) -> dict:
        """Convert persona to dictionary representation.

        Returns:
            Dictionary representation of the persona
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "erpnext_roles": self.erpnext_roles_str,
            "permissions": self.permissions,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Persona":
        """Create persona from dictionary representation.

        Args:
            data: Dictionary containing persona data

        Returns:
            Persona instance
        """
        # Parse roles from string
        roles_str = data.get("erpnext_roles", "")
        roles = (
            [r.strip() for r in roles_str.split(",") if r.strip()] if roles_str else []
        )

        # Parse timestamps
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            )

        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(
                data["updated_at"].replace("Z", "+00:00")
            )

        # Parse UUID
        id = UUID(data["id"]) if data.get("id") else None

        return cls(
            name=data["name"],
            description=data["description"],
            erpnext_roles=roles,
            permissions=data.get("permissions", ""),
            is_active=data.get("is_active", True),
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            version=data.get("version", 1),
        )

    def _is_valid_permission_format(self, permission: str) -> bool:
        """Validate permission string format.

        Args:
            permission: Permission string to validate

        Returns:
            True if format is valid
        """
        if not permission or ":" not in permission:
            return False

        parts = permission.split(":")
        if len(parts) != 2:
            return False

        action, resource = parts
        action = action.strip()
        resource = resource.strip()

        if not action or not resource:
            return False

        # Valid actions
        valid_actions = {"read", "write", "create", "delete", "admin"}
        if action not in valid_actions:
            return False

        # Valid resource format (alphanumeric, underscore, or *)
        if resource != "*" and not re.match(r"^[a-zA-Z0-9_]+$", resource):
            return False

        return True

    def __str__(self) -> str:
        """String representation of persona."""
        return f"Persona(name='{self.name}', roles={len(self.erpnext_roles)}, active={self.is_active})"

    def __repr__(self) -> str:
        """Detailed string representation of persona."""
        return (
            f"Persona(id={self.id}, name='{self.name}', "
            f"roles={self.erpnext_roles}, permissions='{self.permissions}', "
            f"active={self.is_active}, version={self.version})"
        )
