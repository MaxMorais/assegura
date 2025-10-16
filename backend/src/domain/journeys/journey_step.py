"""
Journey Step Value Object

This module defines the JourneyStep value object that represents a single step
within a test journey. Each step references an action from the action library
and defines the parameters and expected outcomes for that step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID


@dataclass(frozen=True)
class JourneyStep:
    """
    Value object representing a single step in a journey.

    A journey step combines an action from the action library with specific
    parameters and expected outcomes for the step execution context.

    Attributes:
        step_number: Sequential number of this step in the journey (1-based)
        action_id: Reference to an action in the action library
        action_type: Type of action (given/when/then)
        action_name: Display name of the action
        description: Human-readable description of what this step does
        parameters: Input parameters for this step's action
        expected_outputs: Expected results from executing this step
        metadata: Additional step configuration
    """

    step_number: int
    action_id: UUID
    action_type: str  # "given" | "when" | "then"
    action_name: str
    description: str
    parameters: dict[str, Any]
    expected_outputs: dict[str, Any]
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate step after initialization."""
        if self.step_number < 1:
            raise ValueError("Step number must be positive")

        if self.action_type not in ("given", "when", "then"):
            raise ValueError("Action type must be 'given', 'when', or 'then'")

        if not self.action_name.strip():
            raise ValueError("Action name is required")

        if not self.description.strip():
            raise ValueError("Step description is required")

    @property
    def is_given_step(self) -> bool:
        """Check if this is a Given step."""
        return self.action_type == "given"

    @property
    def is_when_step(self) -> bool:
        """Check if this is a When step."""
        return self.action_type == "when"

    @property
    def is_then_step(self) -> bool:
        """Check if this is a Then step."""
        return self.action_type == "then"

    @property
    def has_parameters(self) -> bool:
        """Check if step has input parameters."""
        return bool(self.parameters)

    @property
    def has_expected_outputs(self) -> bool:
        """Check if step has expected outputs defined."""
        return bool(self.expected_outputs)

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        Get a specific parameter value.

        Args:
            key: Parameter key
            default: Default value if key not found

        Returns:
            Parameter value or default
        """
        return self.parameters.get(key, default)

    def get_expected_output(self, key: str, default: Any = None) -> Any:
        """
        Get a specific expected output value.

        Args:
            key: Output key
            default: Default value if key not found

        Returns:
            Expected output value or default
        """
        return self.expected_outputs.get(key, default)

    @classmethod
    def create(
        cls,
        step_number: int,
        action_id: UUID,
        action_type: str,
        action_name: str,
        description: str,
        parameters: Optional[dict[str, Any]] = None,
        expected_outputs: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> JourneyStep:
        """
        Create a new journey step.

        Args:
            step_number: Sequential step number
            action_id: Reference to action in action library
            action_type: Type of action (given/when/then)
            action_name: Display name of the action
            description: Step description
            parameters: Input parameters for the step
            expected_outputs: Expected results from the step
            metadata: Additional step configuration

        Returns:
            New JourneyStep instance
        """
        return cls(
            step_number=step_number,
            action_id=action_id,
            action_type=action_type,
            action_name=action_name,
            description=description,
            parameters=parameters or {},
            expected_outputs=expected_outputs or {},
            metadata=metadata or {},
        )
