"""Test Data Set domain entity for test data generation and lifecycle management.

This module implements the Test Data Set domain entity which manages:
- Generated test data for ERPNext entities (customers, items, etc.)
- Association with journeys and test execution
- Data lifecycle (generation → usage → cleanup)
- Generation parameters and validation
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ..base_entity import BaseEntity


class CleanupStatus(str, Enum):
    """Status of test data cleanup process."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class TestDataSet(BaseEntity):
    """Test Data Set domain entity.

    Represents a collection of generated test data for ERPNext entities
    required by test execution. Manages the complete data lifecycle from
    generation through cleanup.

    Attributes:
        id: Unique identifier for the test data set
        name: Human-readable data set identifier
        erpnext_entities: Generated entity data (customers, items, etc.)
        journey_id: Associated journey that requires this data
        generation_parameters: Parameters used for data generation
        cleanup_status: Current cleanup state (Pending, Completed, Failed)
        consultant_id: Owning consultant
        created_at: Timestamp when data set was created
        cleaned_up_at: Timestamp when data was cleaned up (nullable)
    """

    def __init__(
        self,
        name: str,
        erpnext_entities: Dict[str, Any],
        journey_id: UUID,
        consultant_id: UUID,
        generation_parameters: Optional[Dict[str, Any]] = None,
        cleanup_status: CleanupStatus = CleanupStatus.PENDING,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        cleaned_up_at: Optional[datetime] = None,
    ):
        """Initialize TestDataSet domain entity.

        Args:
            name: Data set identifier (must be unique per journey)
            erpnext_entities: Generated entity data as JSON structure
            journey_id: Associated journey UUID
            consultant_id: Owning consultant UUID
            generation_parameters: Parameters used for generation (optional)
            cleanup_status: Current cleanup state (default: PENDING)
            id: Entity UUID (generated if not provided)
            created_at: Creation timestamp (generated if not provided)
            cleaned_up_at: Cleanup timestamp (nullable)

        Raises:
            ValueError: If validation rules are violated
        """
        super().__init__(id=id, created_at=created_at)
        self._name = ""
        self._erpnext_entities = {}
        self._journey_id = journey_id
        self._consultant_id = consultant_id
        self._generation_parameters = generation_parameters or {}
        self._cleanup_status = cleanup_status
        self._cleaned_up_at = cleaned_up_at

        # Validate and set attributes
        self.name = name
        self.erpnext_entities = erpnext_entities

    @property
    def name(self) -> str:
        """Get data set name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set data set name with validation.

        Args:
            value: Data set name

        Raises:
            ValueError: If name is empty or invalid
        """
        if not value or not value.strip():
            raise ValueError("Test data set name cannot be empty")
        if len(value) > 255:
            raise ValueError("Test data set name cannot exceed 255 characters")
        self._name = value.strip()

    @property
    def erpnext_entities(self) -> Dict[str, Any]:
        """Get generated ERPNext entity data."""
        return self._erpnext_entities

    @erpnext_entities.setter
    def erpnext_entities(self, value: Dict[str, Any]) -> None:
        """Set ERPNext entity data with validation.

        Args:
            value: Dictionary of entity data

        Raises:
            ValueError: If entities data is invalid
        """
        if not isinstance(value, dict):
            raise ValueError("ERPNext entities must be a dictionary")
        if not value:
            raise ValueError("ERPNext entities cannot be empty")
        
        # Validate that entity data has required structure
        for entity_type, entity_data in value.items():
            if not isinstance(entity_type, str):
                raise ValueError(f"Entity type must be string, got {type(entity_type)}")
            if not isinstance(entity_data, (list, dict)):
                raise ValueError(
                    f"Entity data for {entity_type} must be list or dict, "
                    f"got {type(entity_data)}"
                )
        
        self._erpnext_entities = value

    @property
    def journey_id(self) -> UUID:
        """Get associated journey ID."""
        return self._journey_id

    @property
    def consultant_id(self) -> UUID:
        """Get owning consultant ID."""
        return self._consultant_id

    @property
    def generation_parameters(self) -> Dict[str, Any]:
        """Get generation parameters."""
        return self._generation_parameters

    @property
    def cleanup_status(self) -> CleanupStatus:
        """Get current cleanup status."""
        return self._cleanup_status

    @property
    def cleaned_up_at(self) -> Optional[datetime]:
        """Get cleanup timestamp."""
        return self._cleaned_up_at

    def mark_as_cleaned(self) -> None:
        """Mark test data as cleaned up.

        Updates cleanup status to COMPLETED and sets cleaned_up_at timestamp.
        """
        self._cleanup_status = CleanupStatus.COMPLETED
        self._cleaned_up_at = datetime.utcnow()

    def mark_cleanup_failed(self) -> None:
        """Mark cleanup as failed.

        Updates cleanup status to FAILED but does not set cleaned_up_at.
        """
        self._cleanup_status = CleanupStatus.FAILED

    def retry_cleanup(self) -> None:
        """Reset cleanup status to allow retry.

        Sets status back to PENDING and clears cleaned_up_at timestamp.
        """
        self._cleanup_status = CleanupStatus.PENDING
        self._cleaned_up_at = None

    def get_entity_count(self) -> int:
        """Get total count of generated entities.

        Returns:
            Total number of entities across all types
        """
        count = 0
        for entity_data in self._erpnext_entities.values():
            if isinstance(entity_data, list):
                count += len(entity_data)
            elif isinstance(entity_data, dict):
                count += 1
        return count

    def get_entity_types(self) -> List[str]:
        """Get list of entity types in this data set.

        Returns:
            List of entity type names (e.g., ['Customer', 'Item', 'Sales Order'])
        """
        return list(self._erpnext_entities.keys())

    def has_entity_type(self, entity_type: str) -> bool:
        """Check if data set contains specific entity type.

        Args:
            entity_type: Entity type to check (e.g., 'Customer')

        Returns:
            True if entity type exists in data set
        """
        return entity_type in self._erpnext_entities

    def get_entities_by_type(self, entity_type: str) -> Optional[Any]:
        """Get entities of a specific type.

        Args:
            entity_type: Entity type to retrieve

        Returns:
            Entity data (list or dict) or None if not found
        """
        return self._erpnext_entities.get(entity_type)

    def is_cleanup_required(self) -> bool:
        """Check if cleanup is required.

        Returns:
            True if cleanup status is PENDING
        """
        return self._cleanup_status == CleanupStatus.PENDING

    def is_cleaned_up(self) -> bool:
        """Check if data has been cleaned up.

        Returns:
            True if cleanup status is COMPLETED
        """
        return self._cleanup_status == CleanupStatus.COMPLETED

    def validate_entities(self) -> List[str]:
        """Validate entity data structure.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self._erpnext_entities:
            errors.append("ERPNext entities cannot be empty")
            return errors

        for entity_type, entity_data in self._erpnext_entities.items():
            if not entity_type.strip():
                errors.append("Entity type cannot be empty string")
            
            if isinstance(entity_data, list):
                if not entity_data:
                    errors.append(f"Entity list for {entity_type} cannot be empty")
                for i, item in enumerate(entity_data):
                    if not isinstance(item, dict):
                        errors.append(
                            f"Entity item {i} in {entity_type} must be dictionary"
                        )
            elif isinstance(entity_data, dict):
                if not entity_data:
                    errors.append(f"Entity dict for {entity_type} cannot be empty")
            else:
                errors.append(
                    f"Entity data for {entity_type} must be list or dict, "
                    f"got {type(entity_data).__name__}"
                )

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation.

        Returns:
            Dictionary with all entity attributes
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "erpnext_entities": self.erpnext_entities,
            "journey_id": str(self.journey_id),
            "consultant_id": str(self.consultant_id),
            "generation_parameters": self.generation_parameters,
            "cleanup_status": self.cleanup_status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "cleaned_up_at": (
                self.cleaned_up_at.isoformat() if self.cleaned_up_at else None
            ),
            "entity_count": self.get_entity_count(),
            "entity_types": self.get_entity_types(),
        }

    def __repr__(self) -> str:
        """Get string representation of test data set."""
        return (
            f"TestDataSet(id={self.id}, name='{self.name}', "
            f"entity_count={self.get_entity_count()}, "
            f"cleanup_status={self.cleanup_status.value})"
        )
