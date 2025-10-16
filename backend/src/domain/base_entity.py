"""Base domain entity class following Domain-Driven Design principles.

This module provides the foundational base class for all domain entities
in the ERPNext Test Automation Meta-Framework, implementing common patterns
and ensuring constitutional compliance with DDD architecture.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    """Base domain entity with common fields and behavior.

    All domain entities MUST inherit from this class to ensure
    consistent structure, validation, and behavior across the
    application following DDD principles.

    Attributes:
        id: Unique identifier (UUID) for the entity
        created_at: Timestamp when entity was created
        updated_at: Timestamp when entity was last modified
        version: Optimistic concurrency control version
    """

    # Primary identifier
    id: UUID = Field(default_factory=uuid4, description="Unique entity identifier")

    # Audit fields
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    # Concurrency control
    version: int = Field(
        default=1, description="Entity version for optimistic concurrency"
    )

    class Config:
        """Pydantic model configuration."""

        # Use enum values (not names) for better API compatibility
        use_enum_values = True
        # Validate assignment to ensure data integrity
        validate_assignment = True
        # Allow field population by name or alias
        allow_population_by_field_name = True
        # JSON schema extra options
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2025-10-15T10:30:00Z",
                "updated_at": "2025-10-15T10:30:00Z",
                "version": 1,
            }
        }

    def update_timestamp(self) -> None:
        """Update the modification timestamp.

        Should be called whenever the entity is modified.
        This ensures proper audit trail maintenance.
        """
        self.updated_at = datetime.utcnow()

    def increment_version(self) -> None:
        """Increment entity version for optimistic concurrency control.

        Should be called before persisting entity changes
        to detect concurrent modifications.
        """
        self.version += 1
        self.update_timestamp()

    def is_newer_than(self, other_version: int) -> bool:
        """Check if this entity version is newer than given version.

        Args:
            other_version: Version to compare against

        Returns:
            True if this entity is newer, False otherwise
        """
        return self.version > other_version

    def to_dict(self, exclude_none: bool = True) -> dict[str, Any]:
        """Convert entity to dictionary representation.

        Args:
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary representation of the entity
        """
        return self.dict(exclude_none=exclude_none, by_alias=True)

    def copy_with_new_id(self) -> "BaseEntity":
        """Create a copy of this entity with a new ID.

        Useful for creating new entities based on existing ones
        while maintaining data integrity.

        Returns:
            New entity instance with different ID and reset timestamps
        """
        entity_data = self.dict(exclude={"id", "created_at", "updated_at", "version"})
        return self.__class__(**entity_data)

    def __eq__(self, other: Any) -> bool:
        """Entity equality based on ID.

        Two entities are considered equal if they have the same ID,
        following DDD identity patterns.

        Args:
            other: Object to compare with

        Returns:
            True if entities have same ID, False otherwise
        """
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Entity hash based on ID for use in sets and dictionaries."""
        return hash(self.id)

    def __str__(self) -> str:
        """String representation showing entity type and ID."""
        return f"{self.__class__.__name__}(id={self.id})"

    def __repr__(self) -> str:
        """Developer-friendly representation with key fields."""
        return (
            f"{self.__class__.__name__}("
            f"id={self.id}, "
            f"version={self.version}, "
            f"updated_at={self.updated_at})"
        )


class AggregateRoot(BaseEntity):
    """Base class for aggregate roots in DDD.

    Aggregate roots are the only entities that can be directly
    loaded and persisted by repositories. They maintain consistency
    boundaries and coordinate access to their child entities.
    """

    # Domain events (to be implemented when event sourcing is added)
    _domain_events: list = []

    def add_domain_event(self, event: Any) -> None:
        """Add a domain event to be published.

        Args:
            event: Domain event to add
        """
        self._domain_events.append(event)

    def clear_domain_events(self) -> list:
        """Clear and return all domain events.

        Returns:
            List of domain events to publish
        """
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def has_domain_events(self) -> bool:
        """Check if aggregate has pending domain events.

        Returns:
            True if there are pending events, False otherwise
        """
        return bool(self._domain_events)


class ValueObject(BaseModel):
    """Base class for value objects in DDD.

    Value objects are immutable and defined by their attributes
    rather than identity. They should be used for modeling
    concepts that are primarily characterized by their values.
    """

    class Config:
        """Pydantic configuration for value objects."""

        # Value objects are immutable
        allow_mutation = False
        # Use frozen=True for hashability
        frozen = True
        # Validate assignment
        validate_assignment = True

    def __eq__(self, other: Any) -> bool:
        """Value object equality based on all attributes."""
        if not isinstance(other, self.__class__):
            return False
        return self.dict() == other.dict()

    def __hash__(self) -> int:
        """Hash based on all attribute values."""
        return hash(tuple(sorted(self.dict().items())))


class DomainService:
    """Base class for domain services.

    Domain services encapsulate domain logic that doesn't
    naturally belong to any entity or value object.
    They operate on domain objects but don't maintain state.
    """

    pass


class Repository:
    """Base repository interface following DDD patterns.

    Repositories provide collection-like interface for
    aggregate roots, abstracting the underlying persistence
    mechanism from the domain layer.
    """

    async def save(self, entity: AggregateRoot) -> AggregateRoot:
        """Save an aggregate root.

        Args:
            entity: Aggregate root to save

        Returns:
            Saved entity with updated version
        """
        raise NotImplementedError

    async def find_by_id(self, entity_id: UUID) -> Optional[AggregateRoot]:
        """Find aggregate root by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Found entity or None
        """
        raise NotImplementedError

    async def delete(self, entity: AggregateRoot) -> None:
        """Delete an aggregate root.

        Args:
            entity: Aggregate root to delete
        """
        raise NotImplementedError
