"""Activity repository interface definition.

This module defines the repository interface for activity persistence operations,
following the repository pattern to abstract data access concerns from the domain.
"""

import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Union

from .activity import Activity

if TYPE_CHECKING:
    from .activity_service import ActivityPersonaLink


class ActivityRepository(ABC):
    """Abstract repository interface for Activity entities."""

    @abstractmethod
    async def create(self, activity: Activity) -> Activity:
        """Create a new activity in the repository.

        Args:
            activity: The Activity entity to create

        Returns:
            The created Activity entity with updated metadata

        Raises:
            ActivityAlreadyExistsError: If activity with same name exists
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, activity_id: Union[str, uuid.UUID]) -> Optional[Activity]:
        """Get an activity by its ID.

        Args:
            activity_id: The unique identifier of the activity

        Returns:
            The Activity entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Activity]:
        """Get an activity by its name.

        Args:
            name: The name of the activity

        Returns:
            The Activity entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(self) -> list[Activity]:
        """Get all activities.

        Returns:
            List of all Activity entities
        """
        pass

    @abstractmethod
    async def update(self, activity: Activity) -> Activity:
        """Update an existing activity.

        Args:
            activity: The Activity entity with updates

        Returns:
            The updated Activity entity

        Raises:
            ActivityNotFoundError: If activity doesn't exist
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def delete(self, activity_id: Union[str, uuid.UUID]) -> None:
        """Delete an activity by ID.

        Args:
            activity_id: The unique identifier of the activity to delete

        Raises:
            ActivityNotFoundError: If activity doesn't exist
            RepositoryError: If deletion fails
        """
        pass

    @abstractmethod
    async def list_with_filters(
        self, filters: dict[str, Any], page: int = 1, per_page: int = 20
    ) -> tuple[list[Activity], int]:
        """List activities with filtering and pagination.

        Args:
            filters: Dictionary of filter criteria:
                - erpnext_module: Filter by ERPNext module
                - action_type: Filter by action type
                - target_doctype: Filter by target DocType
                - complexity_score: Filter by complexity score
                - is_active: Filter by active status
                - tags_any: Filter by any of the provided tags
                - min_duration: Minimum estimated duration
                - max_duration: Maximum estimated duration
                - search: Search in name and description
                - created_after: Filter by creation date (after)
                - created_before: Filter by creation date (before)
            page: Page number (1-based)
            per_page: Items per page

        Returns:
            Tuple of (activities list, total count)
        """
        pass

    @abstractmethod
    async def get_by_module(self, erpnext_module: str) -> list[Activity]:
        """Get all activities for a specific ERPNext module.

        Args:
            erpnext_module: The ERPNext module name

        Returns:
            List of Activity entities for the module
        """
        pass

    @abstractmethod
    async def get_by_action_type(self, action_type: str) -> list[Activity]:
        """Get all activities for a specific action type.

        Args:
            action_type: The action type

        Returns:
            List of Activity entities with the action type
        """
        pass

    @abstractmethod
    async def get_by_doctype(self, target_doctype: str) -> list[Activity]:
        """Get all activities targeting a specific DocType.

        Args:
            target_doctype: The target DocType name

        Returns:
            List of Activity entities targeting the DocType
        """
        pass

    @abstractmethod
    async def get_active_activities(self) -> list[Activity]:
        """Get all active activities.

        Returns:
            List of active Activity entities
        """
        pass

    @abstractmethod
    async def get_inactive_activities(self) -> list[Activity]:
        """Get all inactive activities.

        Returns:
            List of inactive Activity entities
        """
        pass

    @abstractmethod
    async def search_activities(
        self, query: str, page: int = 1, per_page: int = 20
    ) -> tuple[list[Activity], int]:
        """Search activities by name and description.

        Args:
            query: Search query string
            page: Page number (1-based)
            per_page: Items per page

        Returns:
            Tuple of (matching activities, total count)
        """
        pass

    @abstractmethod
    async def get_by_complexity_range(
        self, min_complexity: int, max_complexity: int
    ) -> list[Activity]:
        """Get activities within a complexity score range.

        Args:
            min_complexity: Minimum complexity score (1-5)
            max_complexity: Maximum complexity score (1-5)

        Returns:
            List of Activity entities within the complexity range
        """
        pass

    @abstractmethod
    async def get_by_duration_range(
        self, min_duration: int, max_duration: int
    ) -> list[Activity]:
        """Get activities within an estimated duration range.

        Args:
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds

        Returns:
            List of Activity entities within the duration range
        """
        pass

    @abstractmethod
    async def get_by_tags(
        self, tags: list[str], match_any: bool = True
    ) -> list[Activity]:
        """Get activities by tags.

        Args:
            tags: List of tags to match
            match_any: If True, match any tag; if False, match all tags

        Returns:
            List of Activity entities matching the tag criteria
        """
        pass

    @abstractmethod
    async def count_total(self) -> int:
        """Get total count of all activities.

        Returns:
            Total number of activities
        """
        pass

    @abstractmethod
    async def count_active(self) -> int:
        """Get count of active activities.

        Returns:
            Number of active activities
        """
        pass

    @abstractmethod
    async def count_inactive(self) -> int:
        """Get count of inactive activities.

        Returns:
            Number of inactive activities
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> dict[str, Any]:
        """Get activity statistics.

        Returns:
            Dictionary containing activity statistics:
                - total: Total number of activities
                - active: Number of active activities
                - inactive: Number of inactive activities
                - by_module: Count by ERPNext module
                - by_action_type: Count by action type
                - by_complexity: Count by complexity score
                - avg_duration: Average estimated duration
                - total_duration: Total estimated duration
        """
        pass

    @abstractmethod
    async def bulk_update_status(
        self, activity_ids: list[Union[str, uuid.UUID]], is_active: bool
    ) -> int:
        """Bulk update activity status.

        Args:
            activity_ids: List of activity IDs to update
            is_active: New active status

        Returns:
            Number of activities updated
        """
        pass

    @abstractmethod
    async def bulk_delete(self, activity_ids: list[Union[str, uuid.UUID]]) -> int:
        """Bulk delete activities.

        Args:
            activity_ids: List of activity IDs to delete

        Returns:
            Number of activities deleted
        """
        pass

    @abstractmethod
    async def get_activities_by_ids(
        self, activity_ids: list[Union[str, uuid.UUID]]
    ) -> list[Activity]:
        """Get multiple activities by their IDs.

        Args:
            activity_ids: List of activity IDs

        Returns:
            List of found Activity entities (may be fewer than requested)
        """
        pass

    @abstractmethod
    async def exists_by_name(
        self, name: str, exclude_id: Optional[Union[str, uuid.UUID]] = None
    ) -> bool:
        """Check if an activity with the given name exists.

        Args:
            name: Activity name to check
            exclude_id: Optional activity ID to exclude from check

        Returns:
            True if activity exists, False otherwise
        """
        pass

    @abstractmethod
    async def get_recent_activities(
        self, limit: int = 10, days: int = 30
    ) -> list[Activity]:
        """Get recently created or updated activities.

        Args:
            limit: Maximum number of activities to return
            days: Number of days to look back

        Returns:
            List of recent Activity entities, sorted by update time (desc)
        """
        pass

    @abstractmethod
    async def get_activities_needing_review(self) -> list[Activity]:
        """Get activities that might need review.

        This could include activities with:
        - Very high or very low complexity scores
        - Unusual duration estimates
        - Missing validation rules
        - No success criteria defined

        Returns:
            List of Activity entities that might need review
        """
        pass


class ActivityPersonaLinkRepository(ABC):
    """Abstract repository interface for Activity-Persona link entities."""

    @abstractmethod
    def create(
        self,
        persona_id: uuid.UUID,
        activity_id: uuid.UUID,
        priority: str = "medium",
        notes: str = "",
        is_primary: bool = False,
        execution_order: int = 0,
    ) -> "ActivityPersonaLink":
        """Create a new activity-persona link.

        Args:
            persona_id: The persona ID
            activity_id: The activity ID
            priority: Link priority (low, medium, high, critical)
            notes: Notes about the relationship
            is_primary: Whether this is a primary activity for the persona
            execution_order: Order in workflow/journey

        Returns:
            The created link entity

        Raises:
            ActivityPersonaLinkAlreadyExistsError: If link already exists
        """
        pass

    @abstractmethod
    def get_by_ids(
        self, persona_id: uuid.UUID, activity_id: uuid.UUID
    ) -> Optional["ActivityPersonaLink"]:
        """Get a link by persona and activity IDs.

        Args:
            persona_id: The persona ID
            activity_id: The activity ID

        Returns:
            The link entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_persona_id(
        self,
        persona_id: uuid.UUID,
        priority_filter: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list["ActivityPersonaLink"]:
        """Get all links for a persona.

        Args:
            persona_id: The persona ID
            priority_filter: Optional priority filter
            page: Page number
            per_page: Items per page

        Returns:
            List of link entities for the persona
        """
        pass

    @abstractmethod
    async def get_by_activity_id(
        self, activity_id: uuid.UUID, page: int = 1, per_page: int = 20
    ) -> list["ActivityPersonaLink"]:
        """Get all links for an activity.

        Args:
            activity_id: The activity ID
            page: Page number
            per_page: Items per page

        Returns:
            List of link entities for the activity
        """
        pass

    @abstractmethod
    async def update(self, link: "ActivityPersonaLink") -> "ActivityPersonaLink":
        """Update an activity-persona link.

        Args:
            link: The link entity with updates

        Returns:
            The updated link entity
        """
        pass

    @abstractmethod
    async def delete_by_ids(
        self, persona_id: uuid.UUID, activity_id: uuid.UUID
    ) -> None:
        """Delete a link by persona and activity IDs.

        Args:
            persona_id: The persona ID
            activity_id: The activity ID
        """
        pass

    @abstractmethod
    async def delete_by_persona_id(self, persona_id: uuid.UUID) -> int:
        """Delete all links for a persona.

        Args:
            persona_id: The persona ID

        Returns:
            Number of links deleted
        """
        pass

    @abstractmethod
    async def delete_by_activity_id(self, activity_id: uuid.UUID) -> int:
        """Delete all links for an activity.

        Args:
            activity_id: The activity ID

        Returns:
            Number of links deleted
        """
        pass

    @abstractmethod
    async def count_by_persona_id(
        self, persona_id: uuid.UUID, priority_filter: Optional[str] = None
    ) -> int:
        """Count links for a persona.

        Args:
            persona_id: The persona ID
            priority_filter: Optional priority filter

        Returns:
            Number of links for the persona
        """
        pass

    @abstractmethod
    async def count_by_activity_id(self, activity_id: uuid.UUID) -> int:
        """Count links for an activity.

        Args:
            activity_id: The activity ID

        Returns:
            Number of links for the activity
        """
        pass

    @abstractmethod
    async def get_link_statistics(self) -> dict[str, Any]:
        """Get activity-persona link statistics.

        Returns:
            Dictionary containing link statistics:
                - total_links: Total number of links
                - unique_personas: Number of unique personas with links
                - unique_activities: Number of unique activities with links
                - by_priority: Count by priority level
                - avg_activities_per_persona: Average activities per persona
                - avg_personas_per_activity: Average personas per activity
        """
        pass

    @abstractmethod
    async def bulk_create_links(
        self,
        persona_id: uuid.UUID,
        activity_ids: list[uuid.UUID],
        priority: str = "medium",
        notes: str = "",
    ) -> list["ActivityPersonaLink"]:
        """Bulk create activity-persona links.

        Args:
            persona_id: The persona ID
            activity_ids: List of activity IDs to link
            priority: Priority for all links
            notes: Notes for all links

        Returns:
            List of created link entities
        """
        pass

    @abstractmethod
    async def bulk_delete_links(
        self, persona_id: uuid.UUID, activity_ids: list[uuid.UUID]
    ) -> int:
        """Bulk delete activity-persona links.

        Args:
            persona_id: The persona ID
            activity_ids: List of activity IDs to unlink

        Returns:
            Number of links deleted
        """
        pass
