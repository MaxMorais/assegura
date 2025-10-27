"""
Journey Domain Entity

This module implements the Journey domain entity for the ERPNext test automation framework.
A Journey represents a complete test scenario that combines a persona (user type) with
an activity (business process) and defines the steps needed to execute the test.

Domain Rules:
- Journey must have a unique name per persona/activity combination
- Journey must reference valid Persona and Activity entities
- Journey can have multiple steps in a specific order
- Journey steps must follow Given/When/Then pattern for BDD
- Journey must be associated with at least one activity
- Journey name and description are required and must be meaningful
- Journey can be active/inactive for execution control
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from src.domain.base_entity import BaseEntity
from src.domain.journeys.journey_step import JourneyStep
from src.domain.journeys.journey_validation_error import JourneyValidationError

if TYPE_CHECKING:
    pass


class Journey(BaseEntity):
    """
    Journey domain entity representing a complete test automation scenario.

    A Journey combines a Persona (who performs the test) with an Activity
    (what business process is being tested) and defines the specific steps
    needed to execute the test scenario.

    Attributes:
        name: Unique name of the journey within persona/activity scope
        description: Detailed description of what the journey tests
        persona_id: Reference to the persona who executes this journey
        activity_id: Reference to the activity being tested
        steps: Ordered list of test steps to execute
        is_active: Whether this journey is available for execution
        metadata: Additional journey configuration and settings
        estimated_duration_minutes: Expected execution time in minutes
        complexity_level: Journey complexity (simple, medium, complex)
        prerequisites: List of conditions needed before execution
        expected_outcomes: List of expected results after execution
    """

    def __init__(
        self,
        id: Optional[UUID] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        persona_id: Optional[UUID] = None,
        activity_id: Optional[UUID] = None,
        steps: Optional[list[JourneyStep]] = None,
        is_active: bool = True,
        metadata: Optional[dict[str, Any]] = None,
        estimated_duration_minutes: Optional[int] = None,
        complexity_level: str = "medium",
        prerequisites: Optional[list[str]] = None,
        expected_outcomes: Optional[list[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        """
        Initialize a new Journey instance.

        Args:
            id: Unique identifier for the journey
            name: Journey name (required for persistence)
            description: Journey description (required for persistence)
            persona_id: ID of the persona executing this journey
            activity_id: ID of the activity being tested
            steps: List of journey steps to execute
            is_active: Whether journey is active for execution
            metadata: Additional journey configuration
            estimated_duration_minutes: Expected execution time
            complexity_level: Journey complexity level
            prerequisites: Prerequisites for journey execution
            expected_outcomes: Expected results after execution
            created_at: Journey creation timestamp
            updated_at: Journey last update timestamp
        """
        super().__init__()

        # Set BaseEntity fields
        self.id = id or uuid4()
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.version = 1

        self._name = name
        self._description = description
        self._persona_id = persona_id
        self._activity_id = activity_id
        self._steps: list[JourneyStep] = steps or []
        self._is_active = is_active
        self._metadata = metadata or {}
        self._estimated_duration_minutes = estimated_duration_minutes
        self._complexity_level = complexity_level
        self._prerequisites: list[str] = prerequisites or []
        self._expected_outcomes: list[str] = expected_outcomes or []

        # Validate after initialization
        if name is not None and description is not None:
            self._validate()

    @property
    def name(self) -> Optional[str]:
        """Get journey name."""
        return self._name

    @property
    def description(self) -> Optional[str]:
        """Get journey description."""
        return self._description

    @property
    def persona_id(self) -> Optional[UUID]:
        """Get persona ID."""
        return self._persona_id

    @property
    def activity_id(self) -> Optional[UUID]:
        """Get activity ID."""
        return self._activity_id

    @property
    def steps(self) -> list[JourneyStep]:
        """Get journey steps."""
        return self._steps.copy()

    @property
    def is_active(self) -> bool:
        """Get active status."""
        return self._is_active

    @property
    def metadata(self) -> dict[str, Any]:
        """Get journey metadata."""
        return self._metadata.copy()

    @property
    def estimated_duration_minutes(self) -> Optional[int]:
        """Get estimated duration in minutes."""
        return self._estimated_duration_minutes

    @property
    def complexity_level(self) -> str:
        """Get complexity level."""
        return self._complexity_level

    @property
    def prerequisites(self) -> list[str]:
        """Get prerequisites list."""
        return self._prerequisites.copy()

    @property
    def expected_outcomes(self) -> list[str]:
        """Get expected outcomes list."""
        return self._expected_outcomes.copy()

    @property
    def step_count(self) -> int:
        """Get total number of steps."""
        return len(self._steps)

    @property
    def has_given_steps(self) -> bool:
        """Check if journey has Given steps."""
        return any(step.action_type == "given" for step in self._steps)

    @property
    def has_when_steps(self) -> bool:
        """Check if journey has When steps."""
        return any(step.action_type == "when" for step in self._steps)

    @property
    def has_then_steps(self) -> bool:
        """Check if journey has Then steps."""
        return any(step.action_type == "then" for step in self._steps)

    @property
    def is_complete_scenario(self) -> bool:
        """Check if journey represents a complete BDD scenario."""
        return self.has_given_steps and self.has_when_steps and self.has_then_steps

    def update_details(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        estimated_duration_minutes: Optional[int] = None,
        complexity_level: Optional[str] = None,
    ) -> None:
        """
        Update journey basic details.

        Args:
            name: New journey name
            description: New journey description
            is_active: New active status
            estimated_duration_minutes: New estimated duration
            complexity_level: New complexity level

        Raises:
            JourneyValidationError: If validation fails
        """
        if name is not None:
            self._name = name
        if description is not None:
            self._description = description
        if is_active is not None:
            self._is_active = is_active
        if estimated_duration_minutes is not None:
            self._estimated_duration_minutes = estimated_duration_minutes
        if complexity_level is not None:
            self._complexity_level = complexity_level

        self._validate()
        self._updated_at = datetime.now(timezone.utc)

    def update_associations(
        self,
        persona_id: Optional[UUID] = None,
        activity_id: Optional[UUID] = None,
    ) -> None:
        """
        Update journey persona and activity associations.

        Args:
            persona_id: New persona ID
            activity_id: New activity ID

        Raises:
            JourneyValidationError: If validation fails
        """
        if persona_id is not None:
            self._persona_id = persona_id
        if activity_id is not None:
            self._activity_id = activity_id

        self._validate()
        self._updated_at = datetime.now(timezone.utc)

    def add_step(
        self,
        step: JourneyStep,
        position: Optional[int] = None,
    ) -> None:
        """
        Add a step to the journey.

        Args:
            step: Journey step to add
            position: Position to insert step (None = append)

        Raises:
            JourneyValidationError: If step validation fails
        """
        if position is None:
            # Append to end with next step number
            step._step_number = len(self._steps) + 1
            self._steps.append(step)
        else:
            if position < 1 or position > len(self._steps) + 1:
                raise JourneyValidationError(
                    f"Invalid position {position}. Must be between 1 and {len(self._steps) + 1}"
                )

            # Insert at position and renumber steps
            step._step_number = position
            self._steps.insert(position - 1, step)
            self._renumber_steps()

        self._validate_step_sequence()
        self._updated_at = datetime.now(timezone.utc)

    def remove_step(self, step_number: int) -> JourneyStep:
        """
        Remove a step from the journey.

        Args:
            step_number: Number of step to remove

        Returns:
            The removed journey step

        Raises:
            JourneyValidationError: If step number is invalid
        """
        if step_number < 1 or step_number > len(self._steps):
            raise JourneyValidationError(
                f"Invalid step number {step_number}. Must be between 1 and {len(self._steps)}"
            )

        removed_step = self._steps.pop(step_number - 1)
        self._renumber_steps()
        self._updated_at = datetime.now(timezone.utc)

        return removed_step

    def move_step(self, from_position: int, to_position: int) -> None:
        """
        Move a step to a different position.

        Args:
            from_position: Current step position
            to_position: New step position

        Raises:
            JourneyValidationError: If positions are invalid
        """
        if from_position < 1 or from_position > len(self._steps):
            raise JourneyValidationError(f"Invalid from position {from_position}")
        if to_position < 1 or to_position > len(self._steps):
            raise JourneyValidationError(f"Invalid to position {to_position}")

        if from_position != to_position:
            step = self._steps.pop(from_position - 1)
            self._steps.insert(to_position - 1, step)
            self._renumber_steps()
            self._validate_step_sequence()
            self._updated_at = datetime.now(timezone.utc)

    def clear_steps(self) -> None:
        """Remove all steps from the journey."""
        self._steps.clear()
        self._updated_at = datetime.now(timezone.utc)

    def update_prerequisites(self, prerequisites: list[str]) -> None:
        """
        Update journey prerequisites.

        Args:
            prerequisites: New list of prerequisites
        """
        self._prerequisites = prerequisites or []
        self._updated_at = datetime.now(timezone.utc)

    def add_prerequisite(self, prerequisite: str) -> None:
        """
        Add a prerequisite to the journey.

        Args:
            prerequisite: Prerequisite to add
        """
        if prerequisite and prerequisite not in self._prerequisites:
            self._prerequisites.append(prerequisite)
            self._updated_at = datetime.now(timezone.utc)

    def remove_prerequisite(self, prerequisite: str) -> None:
        """
        Remove a prerequisite from the journey.

        Args:
            prerequisite: Prerequisite to remove
        """
        if prerequisite in self._prerequisites:
            self._prerequisites.remove(prerequisite)
            self._updated_at = datetime.now(timezone.utc)

    def update_expected_outcomes(self, outcomes: list[str]) -> None:
        """
        Update journey expected outcomes.

        Args:
            outcomes: New list of expected outcomes
        """
        self._expected_outcomes = outcomes or []
        self._updated_at = datetime.now(timezone.utc)

    def add_expected_outcome(self, outcome: str) -> None:
        """
        Add an expected outcome to the journey.

        Args:
            outcome: Expected outcome to add
        """
        if outcome and outcome not in self._expected_outcomes:
            self._expected_outcomes.append(outcome)
            self._updated_at = datetime.now(timezone.utc)

    def remove_expected_outcome(self, outcome: str) -> None:
        """
        Remove an expected outcome from the journey.

        Args:
            outcome: Expected outcome to remove
        """
        if outcome in self._expected_outcomes:
            self._expected_outcomes.remove(outcome)
            self._updated_at = datetime.now(timezone.utc)

    def update_metadata(self, metadata: dict[str, Any]) -> None:
        """
        Update journey metadata.

        Args:
            metadata: New metadata dictionary
        """
        self._metadata = metadata or {}
        self._updated_at = datetime.now(timezone.utc)

    def set_metadata_value(self, key: str, value: Any) -> None:
        """
        Set a specific metadata value.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value
        self._updated_at = datetime.now(timezone.utc)

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self._metadata.get(key, default)

    def get_steps_by_type(self, action_type: str) -> list[JourneyStep]:
        """
        Get all steps of a specific type.

        Args:
            action_type: Type of steps to get (given/when/then)

        Returns:
            List of steps of the specified type
        """
        return [step for step in self._steps if step.action_type == action_type]

    def get_step_by_number(self, step_number: int) -> Optional[JourneyStep]:
        """
        Get a step by its number.

        Args:
            step_number: Step number to find

        Returns:
            Journey step or None if not found
        """
        for step in self._steps:
            if step.step_number == step_number:
                return step
        return None

    def validate_step_sequence(self) -> list[str]:
        """
        Validate the journey step sequence.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not self._steps:
            return errors

        # Check for proper BDD sequence: Given -> When -> Then
        given_steps = self.get_steps_by_type("given")
        when_steps = self.get_steps_by_type("when")
        then_steps = self.get_steps_by_type("then")

        if given_steps and when_steps:
            # Ensure Given steps come before When steps
            last_given = max(step.step_number for step in given_steps)
            first_when = min(step.step_number for step in when_steps)
            if last_given > first_when:
                errors.append("Given steps must come before When steps")

        if when_steps and then_steps:
            # Ensure When steps come before Then steps
            last_when = max(step.step_number for step in when_steps)
            first_then = min(step.step_number for step in then_steps)
            if last_when > first_then:
                errors.append("When steps must come before Then steps")

        # Check for step number continuity
        expected_numbers = list(range(1, len(self._steps) + 1))
        actual_numbers = sorted([step.step_number for step in self._steps])
        if actual_numbers != expected_numbers:
            errors.append("Step numbers must be continuous starting from 1")

        # Check for duplicate step numbers
        step_numbers = [step.step_number for step in self._steps]
        if len(step_numbers) != len(set(step_numbers)):
            errors.append("Duplicate step numbers found")

        return errors

    def is_valid(self) -> bool:
        """
        Check if the journey is valid.

        Returns:
            True if journey is valid, False otherwise
        """
        try:
            self._validate()
            return True
        except JourneyValidationError:
            return False

    def get_validation_errors(self) -> list[str]:
        """
        Get all validation errors for this journey.

        Returns:
            List of validation error messages
        """
        errors = []

        try:
            self._validate()
        except JourneyValidationError as e:
            errors.append(str(e))

        # Add step sequence validation errors
        sequence_errors = self.validate_step_sequence()
        errors.extend(sequence_errors)

        return errors

    def _validate(self) -> None:
        """
        Validate journey domain rules.

        Raises:
            JourneyValidationError: If validation fails
        """
        # Validate name
        if not self._name:
            raise JourneyValidationError("Journey name is required")

        if len(self._name.strip()) < 3:
            raise JourneyValidationError("Journey name must be at least 3 characters")

        if len(self._name) > 200:
            raise JourneyValidationError("Journey name must not exceed 200 characters")

        # Validate description
        if not self._description:
            raise JourneyValidationError("Journey description is required")

        if len(self._description.strip()) < 10:
            raise JourneyValidationError(
                "Journey description must be at least 10 characters"
            )

        if len(self._description) > 1000:
            raise JourneyValidationError(
                "Journey description must not exceed 1000 characters"
            )

        # Validate complexity level
        valid_complexity_levels = ["simple", "medium", "complex", "advanced"]
        if self._complexity_level not in valid_complexity_levels:
            raise JourneyValidationError(
                f"Invalid complexity level. Must be one of: {valid_complexity_levels}"
            )

        # Validate duration
        if self._estimated_duration_minutes is not None:
            if self._estimated_duration_minutes < 1:
                raise JourneyValidationError(
                    "Estimated duration must be at least 1 minute"
                )
            if self._estimated_duration_minutes > 1440:  # 24 hours
                raise JourneyValidationError(
                    "Estimated duration must not exceed 1440 minutes (24 hours)"
                )

    def _validate_step_sequence(self) -> None:
        """
        Validate step sequence and raise error if invalid.

        Raises:
            JourneyValidationError: If step sequence is invalid
        """
        errors = self.validate_step_sequence()
        if errors:
            raise JourneyValidationError(
                f"Step sequence validation failed: {'; '.join(errors)}"
            )

    def _renumber_steps(self) -> None:
        """Renumber all steps to ensure continuous numbering."""
        for i, step in enumerate(self._steps, 1):
            step._step_number = i

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        persona_id: UUID,
        activity_id: UUID,
        estimated_duration_minutes: Optional[int] = None,
        complexity_level: str = "medium",
        prerequisites: Optional[list[str]] = None,
        expected_outcomes: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Journey:
        """
        Create a new journey with required fields.

        Args:
            name: Journey name
            description: Journey description
            persona_id: Associated persona ID
            activity_id: Associated activity ID
            estimated_duration_minutes: Expected execution time
            complexity_level: Journey complexity
            prerequisites: Prerequisites for execution
            expected_outcomes: Expected results
            metadata: Additional configuration

        Returns:
            New Journey instance

        Raises:
            JourneyValidationError: If validation fails
        """
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            persona_id=persona_id,
            activity_id=activity_id,
            estimated_duration_minutes=estimated_duration_minutes,
            complexity_level=complexity_level,
            prerequisites=prerequisites,
            expected_outcomes=expected_outcomes,
            metadata=metadata,
            created_at=datetime.now(timezone.utc),
        )

    def __str__(self) -> str:
        """String representation of the journey."""
        return f"Journey(id={self.id}, name='{self.name}', steps={len(self._steps)})"

    def __repr__(self) -> str:
        """Detailed string representation of the journey."""
        return (
            f"Journey(id={self.id}, name='{self.name}', "
            f"persona_id={self.persona_id}, activity_id={self.activity_id}, "
            f"steps={len(self._steps)}, is_active={self.is_active})"
        )
