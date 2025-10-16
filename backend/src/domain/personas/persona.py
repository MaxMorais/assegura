"""Persona domain entity for ERPNext Test Automation Meta-Framework.

Represents test personas that define user types with specific roles and permissions
within the ERPNext system for test automation purposes.
"""

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from ..base_entity import BaseEntity
from .erpnext_roles import ERPNextRole, validate_erpnext_roles
from .exceptions import PersonaValidationError


class Persona(BaseEntity):
    """Domain entity representing a test persona.

    A persona defines a specific user type with associated ERPNext roles
    and permissions that can be used in test scenarios.
    """

    # Core persona fields
    name: str = Field(..., description="Unique name for the persona")
    description: str = Field(..., description="Description of the persona's purpose")
    erpnext_roles: list[str] = Field(..., description="List of ERPNext role names")
    permissions: Optional[str] = Field(default=None, description="Comma-separated permission strings")
    is_active: bool = Field(default=True, description="Whether the persona is active")

    @field_validator('name')
    def validate_name(cls, v):
        """Validate persona name."""
        if not v or not v.strip():
            raise PersonaValidationError("name", "Persona name is required")

        v = v.strip()

        if len(v) < 2:
            raise PersonaValidationError("name", "Persona name must be at least 2 characters long")

        if len(v) > 255:
            raise PersonaValidationError("name", "Persona name must not exceed 255 characters")

        # Check for invalid characters (allow letters, numbers, spaces, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", v):
            raise PersonaValidationError(
                "name", 
                "Persona name can only contain letters, numbers, spaces, hyphens, and underscores"
            )

        return v

    @field_validator('description')
    def validate_description(cls, v):
        """Validate persona description."""
        if not v or not v.strip():
            raise PersonaValidationError("description", "Persona description is required")

        v = v.strip()

        if len(v) < 10:
            raise PersonaValidationError("description", "Persona description must be at least 10 characters long")

        if len(v) > 2000:
            raise PersonaValidationError("description", "Persona description must not exceed 2000 characters")

        return v

    @field_validator('erpnext_roles')
    def validate_erpnext_roles(cls, v):
        """Validate ERPNext roles."""
        if not v:
            raise PersonaValidationError("erpnext_roles", "At least one ERPNext role is required")

        # Validate each role
        validate_erpnext_roles(v)

        # Remove duplicates while preserving order
        unique_roles = []
        seen = set()
        for role in v:
            role = role.strip()
            if role and role not in seen:
                unique_roles.append(role)
                seen.add(role)

        if not unique_roles:
            raise PersonaValidationError("erpnext_roles", "At least one valid ERPNext role is required")

        return unique_roles

    @property
    def erpnext_roles_str(self) -> str:
        """Get ERPNext roles as comma-separated string."""
        return ",".join(self.erpnext_roles)

    @property
    def permissions_list(self) -> list[str]:
        """Get permissions as list."""
        if not self.permissions:
            return []
        return [p.strip() for p in self.permissions.split(",") if p.strip()]

    def add_erpnext_role(self, role: str) -> None:
        """Add an ERPNext role to the persona.

        Args:
            role: ERPNext role name to add

        Raises:
            PersonaValidationError: If role is invalid
        """
        role = role.strip()
        if not role:
            raise PersonaValidationError("erpnext_roles", "Role name cannot be empty")

        # Validate the role
        validate_erpnext_roles([role])

        if role not in self.erpnext_roles:
            self.erpnext_roles.append(role)
            self.increment_version()

    def remove_erpnext_role(self, role: str) -> bool:
        """Remove an ERPNext role from the persona.

        Args:
            role: ERPNext role name to remove

        Returns:
            True if role was removed, False if not found

        Raises:
            PersonaValidationError: If removing role would leave persona with no roles
        """
        if len(self.erpnext_roles) <= 1:
            raise PersonaValidationError(
                "erpnext_roles",
                "Cannot remove role - persona must have at least one role"
            )

        if role in self.erpnext_roles:
            self.erpnext_roles.remove(role)
            self.increment_version()
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
            raise PersonaValidationError("permissions", "Permission cannot be empty")

        if not self._is_valid_permission_format(permission):
            raise PersonaValidationError(
                "permissions",
                f"Invalid permission format: '{permission}'. "
                "Use format 'action:resource' (e.g., 'read:sales', 'write:*')"
            )

        current_permissions = self.permissions_list
        if permission not in current_permissions:
            current_permissions.append(permission)
            self.permissions = ",".join(current_permissions)
            self.increment_version()

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
            self.permissions = ",".join(current_permissions)
            self.increment_version()
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
        return role in self.erpnext_roles

    def deactivate(self) -> None:
        """Deactivate the persona."""
        self.is_active = False
        self.increment_version()

    def activate(self) -> None:
        """Activate the persona."""
        self.is_active = True
        self.increment_version()

    def get_effective_permissions(self) -> set[str]:
        """Get all effective permissions including role-based permissions.

        Returns:
            Set of all effective permissions
        """
        permissions = set(self.permissions_list)

        # Add role-based permissions
        for role in self.erpnext_roles:
            role_permissions = ERPNextRole.get_role_permissions(role)
            permissions.update(role_permissions)

        return permissions

    def update_name(self, name: str) -> None:
        """Update persona name."""
        self.name = name  # Will trigger validation
        self.increment_version()

    def update_description(self, description: str) -> None:
        """Update persona description."""
        self.description = description  # Will trigger validation
        self.increment_version()

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
            "permissions": self.permissions or "",
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
        return f"Persona(id={self.id}, name='{self.name}', roles={len(self.erpnext_roles)}, active={self.is_active})"

    def __repr__(self) -> str:
        """Detailed string representation of persona."""
        return (
            f"Persona(id={self.id}, name='{self.name}', "
            f"roles={self.erpnext_roles}, permissions='{self.permissions}', "
            f"active={self.is_active}, version={self.version})"
        )
