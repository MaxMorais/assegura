"""Persona repository interface.

Defines the contract for persona persistence operations
in the ERPNext Test Automation Meta-Framework domain layer.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from .persona import Persona


class PersonaRepository(ABC):
    """Abstract repository interface for persona persistence.

    Defines the contract that infrastructure repositories must implement
    for persona storage and retrieval operations.
    """

    @abstractmethod
    async def save(self, persona: Persona) -> Persona:
        """Save a persona entity.

        Args:
            persona: Persona entity to save

        Returns:
            Saved persona entity with updated metadata

        Raises:
            PersonaAlreadyExistsError: If persona with same name already exists
            PersonaConcurrencyError: If persona was modified by another process
        """
        pass

    @abstractmethod
    async def find_by_id(self, persona_id: UUID) -> Optional[Persona]:
        """Find persona by unique identifier.

        Args:
            persona_id: Unique persona identifier

        Returns:
            Persona entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Persona]:
        """Find persona by name.

        Args:
            name: Persona name (case-sensitive)

        Returns:
            Persona entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_all(self) -> list[Persona]:
        """Find all personas in the system.

        Returns:
            List of all persona entities
        """
        pass

    @abstractmethod
    async def find_active(self) -> list[Persona]:
        """Find all active personas.

        Returns:
            List of active persona entities
        """
        pass

    @abstractmethod
    async def find_by_role(self, erpnext_role: str) -> list[Persona]:
        """Find personas that have specific ERPNext role.

        Args:
            erpnext_role: ERPNext role name to search for

        Returns:
            List of personas with the specified role
        """
        pass

    @abstractmethod
    async def find_with_permission(self, permission: str) -> list[Persona]:
        """Find personas that have specific permission.

        Args:
            permission: Permission string to search for (format: action:resource)

        Returns:
            List of personas with the specified permission
        """
        pass

    @abstractmethod
    async def search(self, query: str) -> list[Persona]:
        """Search personas by name or description.

        Args:
            query: Search query string

        Returns:
            List of personas matching the search criteria
        """
        pass

    @abstractmethod
    async def find_with_pagination(
        self,
        filters: Optional[dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Persona], int]:
        """Find personas with filtering, pagination, and sorting.

        Args:
            filters: Dictionary of filters to apply
            page: Page number (1-based)
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)

        Returns:
            Tuple of (personas list, total count)
        """
        pass

    @abstractmethod
    async def count_total(self) -> int:
        """Get total count of personas.

        Returns:
            Total number of personas
        """
        pass

    @abstractmethod
    async def count_active(self) -> int:
        """Get count of active personas.

        Returns:
            Number of active personas
        """
        pass

    @abstractmethod
    async def count_by_role(self, erpnext_role: str) -> int:
        """Get count of personas with specific role.

        Args:
            erpnext_role: ERPNext role name

        Returns:
            Number of personas with the role
        """
        pass

    @abstractmethod
    async def delete(self, persona_id: UUID) -> bool:
        """Delete a persona.

        Args:
            persona_id: Unique persona identifier

        Returns:
            True if persona was deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists_by_name(
        self, name: str, exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if persona with name exists.

        Args:
            name: Persona name to check
            exclude_id: Persona ID to exclude from check (for updates)

        Returns:
            True if persona with name exists (excluding specified ID)
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> dict[str, Any]:
        """Get persona statistics for analytics.

        Returns:
            Dictionary containing various persona statistics
        """
        pass

    @abstractmethod
    async def find_created_after(self, date: datetime) -> list[Persona]:
        """Find personas created after specific date.

        Args:
            date: Cutoff date

        Returns:
            List of personas created after the date
        """
        pass

    @abstractmethod
    async def find_updated_after(self, date: datetime) -> list[Persona]:
        """Find personas updated after specific date.

        Args:
            date: Cutoff date

        Returns:
            List of personas updated after the date
        """
        pass

    @abstractmethod
    async def find_by_multiple_roles(
        self, erpnext_roles: list[str], match_all: bool = False
    ) -> list[Persona]:
        """Find personas that have multiple ERPNext roles.

        Args:
            erpnext_roles: List of ERPNext role names
            match_all: If True, persona must have ALL roles; if False, ANY role

        Returns:
            List of personas matching the role criteria
        """
        pass

    @abstractmethod
    async def find_complex_personas(
        self, min_roles: int = 3, min_permissions: int = 5
    ) -> list[Persona]:
        """Find personas with high complexity (many roles/permissions).

        Args:
            min_roles: Minimum number of roles
            min_permissions: Minimum number of permissions

        Returns:
            List of complex personas
        """
        pass

    @abstractmethod
    async def get_role_distribution(self) -> dict[str, int]:
        """Get distribution of ERPNext roles across personas.

        Returns:
            Dictionary mapping role names to usage counts
        """
        pass

    @abstractmethod
    async def get_permission_distribution(self) -> dict[str, int]:
        """Get distribution of permissions across personas.

        Returns:
            Dictionary mapping permission strings to usage counts
        """
        pass

    @abstractmethod
    async def get_creation_trend(self, days: int = 30) -> list[dict[str, Any]]:
        """Get persona creation trend over specified period.

        Args:
            days: Number of days to analyze

        Returns:
            List of daily creation counts
        """
        pass

    @abstractmethod
    async def find_similar_by_roles(
        self, persona: Persona, similarity_threshold: float = 0.5
    ) -> list[Persona]:
        """Find personas with similar role combinations.

        Args:
            persona: Reference persona
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of personas with similar roles
        """
        pass

    @abstractmethod
    async def bulk_update_status(self, persona_ids: list[UUID], is_active: bool) -> int:
        """Bulk update active status for multiple personas.

        Args:
            persona_ids: List of persona IDs to update
            is_active: New active status

        Returns:
            Number of personas updated
        """
        pass

    @abstractmethod
    async def cleanup_inactive(self, days_inactive: int = 90) -> int:
        """Clean up personas that have been inactive for specified period.

        Args:
            days_inactive: Number of days of inactivity before cleanup

        Returns:
            Number of personas cleaned up
        """
        pass
