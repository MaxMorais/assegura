"""
Action Library Domain Entity

This module implements the Action Library domain entity for the ERPNext test automation framework.
An Action represents a reusable test step that can be executed as part of a journey, with
specific parameters, expected outputs, and implementation details.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from src.domain.base_entity import BaseEntity


class ActionType(Enum):
    """Enumeration of BDD action types."""

    GIVEN = "given"  # Precondition/setup actions
    WHEN = "when"  # Main actions/operations
    THEN = "then"  # Verification/assertion actions


class ImplementationType(Enum):
    """Enumeration of action implementation types."""

    UI_INTERACTION = "ui_interaction"  # Browser-based UI actions
    API_CALL = "api_call"  # Direct ERPNext API calls
    ROBOT_FRAMEWORK = "robot_framework"  # Custom Robot Framework keywords
    VERIFICATION = "verification"  # Result checking/validation
    DATA_SETUP = "data_setup"  # Test data preparation
    CLEANUP = "cleanup"  # Test cleanup operations


class ActionValidationError(ValueError):
    """Exception raised when action validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ActionParameter:
    """Represents an action input parameter."""

    def __init__(
        self,
        name: str,
        parameter_type: str,
        required: bool = True,
        description: Optional[str] = None,
        default_value: Any = None,
        validation_rules: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize action parameter.

        Args:
            name: Parameter name
            parameter_type: Parameter data type (string, number, boolean, date, etc.)
            required: Whether parameter is required
            description: Parameter description
            default_value: Default value if not provided
            validation_rules: Additional validation rules
        """
        self.name = name
        self.parameter_type = parameter_type
        self.required = required
        self.description = description or ""
        self.default_value = default_value
        self.validation_rules = validation_rules or {}

    def validate_value(self, value: Any) -> list[str]:
        """
        Validate parameter value against rules.

        Args:
            value: Value to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required
        if self.required and (value is None or value == ""):
            errors.append(f"Parameter '{self.name}' is required")
            return errors

        # Skip further validation if value is None/empty and not required
        if value is None or value == "":
            return errors

        # Type validation
        if self.parameter_type == "string" and not isinstance(value, str):
            errors.append(f"Parameter '{self.name}' must be a string")
        elif self.parameter_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"Parameter '{self.name}' must be a number")
        elif self.parameter_type == "boolean" and not isinstance(value, bool):
            errors.append(f"Parameter '{self.name}' must be a boolean")

        # Additional validation rules
        if isinstance(value, str):
            if "min_length" in self.validation_rules:
                min_len = self.validation_rules["min_length"]
                if len(value) < min_len:
                    errors.append(
                        f"Parameter '{self.name}' must be at least {min_len} characters"
                    )

            if "max_length" in self.validation_rules:
                max_len = self.validation_rules["max_length"]
                if len(value) > max_len:
                    errors.append(
                        f"Parameter '{self.name}' must not exceed {max_len} characters"
                    )

            if "pattern" in self.validation_rules:
                import re

                pattern = self.validation_rules["pattern"]
                if not re.match(pattern, value):
                    errors.append(
                        f"Parameter '{self.name}' does not match required pattern"
                    )

        return errors


class ActionOutput:
    """Represents an action output/result."""

    def __init__(
        self,
        name: str,
        output_type: str,
        description: Optional[str] = None,
        expected_format: Optional[str] = None,
    ) -> None:
        """
        Initialize action output.

        Args:
            name: Output name
            output_type: Output data type
            description: Output description
            expected_format: Expected format/pattern
        """
        self.name = name
        self.output_type = output_type
        self.description = description or ""
        self.expected_format = expected_format


class Action(BaseEntity):
    """
    Action domain entity representing a reusable test step.

    An Action encapsulates a specific operation that can be performed
    as part of a test journey, with defined inputs, outputs, and
    implementation details.

    Attributes:
        name: Unique name of the action
        description: Detailed description of what the action does
        action_type: BDD type (given/when/then)
        erpnext_module: ERPNext module this action relates to
        implementation_type: How this action is implemented
        parameters: Input parameters required by the action
        expected_outputs: Outputs produced by the action
        robot_keywords: Robot Framework keywords for implementation
        validation_rules: Rules for validating action execution
        is_active: Whether this action is available for use
        metadata: Additional action configuration
        tags: Tags for categorization and search
        prerequisites: Conditions needed before action execution
        postconditions: Expected state after action execution
        execution_timeout: Maximum execution time in seconds
        retry_count: Number of retries on failure
    """

    def __init__(
        self,
        id: Optional[UUID] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        action_type: Optional[ActionType] = None,
        erpnext_module: Optional[str] = None,
        implementation_type: Optional[ImplementationType] = None,
        parameters: Optional[list[ActionParameter]] = None,
        expected_outputs: Optional[list[ActionOutput]] = None,
        robot_keywords: Optional[list[str]] = None,
        validation_rules: Optional[dict[str, Any]] = None,
        is_active: bool = True,
        metadata: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        prerequisites: Optional[list[str]] = None,
        postconditions: Optional[list[str]] = None,
        execution_timeout: int = 30,
        retry_count: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        """
        Initialize a new Action instance.

        Args:
            id: Unique identifier for the action
            name: Action name (required for persistence)
            description: Action description (required for persistence)
            action_type: BDD action type (given/when/then)
            erpnext_module: Related ERPNext module
            implementation_type: How action is implemented
            parameters: Input parameters
            expected_outputs: Output definitions
            robot_keywords: Robot Framework implementation
            validation_rules: Validation configuration
            is_active: Whether action is active
            metadata: Additional configuration
            tags: Categorization tags
            prerequisites: Prerequisites for execution
            postconditions: Expected post-execution state
            execution_timeout: Timeout in seconds
            retry_count: Number of retries on failure
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        super().__init__(id, created_at, updated_at)

        self._name = name
        self._description = description
        self._action_type = action_type
        self._erpnext_module = erpnext_module
        self._implementation_type = implementation_type
        self._parameters: list[ActionParameter] = parameters or []
        self._expected_outputs: list[ActionOutput] = expected_outputs or []
        self._robot_keywords: list[str] = robot_keywords or []
        self._validation_rules = validation_rules or {}
        self._is_active = is_active
        self._metadata = metadata or {}
        self._tags: list[str] = tags or []
        self._prerequisites: list[str] = prerequisites or []
        self._postconditions: list[str] = postconditions or []
        self._execution_timeout = execution_timeout
        self._retry_count = retry_count

        # Validate after initialization
        if name is not None and description is not None:
            self._validate()

    @property
    def name(self) -> Optional[str]:
        """Get action name."""
        return self._name

    @property
    def description(self) -> Optional[str]:
        """Get action description."""
        return self._description

    @property
    def action_type(self) -> Optional[ActionType]:
        """Get action type."""
        return self._action_type

    @property
    def erpnext_module(self) -> Optional[str]:
        """Get ERPNext module."""
        return self._erpnext_module

    @property
    def implementation_type(self) -> Optional[ImplementationType]:
        """Get implementation type."""
        return self._implementation_type

    @property
    def parameters(self) -> list[ActionParameter]:
        """Get action parameters."""
        return self._parameters.copy()

    @property
    def expected_outputs(self) -> list[ActionOutput]:
        """Get expected outputs."""
        return self._expected_outputs.copy()

    @property
    def robot_keywords(self) -> list[str]:
        """Get Robot Framework keywords."""
        return self._robot_keywords.copy()

    @property
    def validation_rules(self) -> dict[str, Any]:
        """Get validation rules."""
        return self._validation_rules.copy()

    @property
    def is_active(self) -> bool:
        """Get active status."""
        return self._is_active

    @property
    def metadata(self) -> dict[str, Any]:
        """Get metadata."""
        return self._metadata.copy()

    @property
    def tags(self) -> list[str]:
        """Get tags."""
        return self._tags.copy()

    @property
    def prerequisites(self) -> list[str]:
        """Get prerequisites."""
        return self._prerequisites.copy()

    @property
    def postconditions(self) -> list[str]:
        """Get postconditions."""
        return self._postconditions.copy()

    @property
    def execution_timeout(self) -> int:
        """Get execution timeout."""
        return self._execution_timeout

    @property
    def retry_count(self) -> int:
        """Get retry count."""
        return self._retry_count

    @property
    def parameter_count(self) -> int:
        """Get number of parameters."""
        return len(self._parameters)

    @property
    def output_count(self) -> int:
        """Get number of outputs."""
        return len(self._expected_outputs)

    @property
    def is_given_action(self) -> bool:
        """Check if this is a Given action."""
        return self._action_type == ActionType.GIVEN

    @property
    def is_when_action(self) -> bool:
        """Check if this is a When action."""
        return self._action_type == ActionType.WHEN

    @property
    def is_then_action(self) -> bool:
        """Check if this is a Then action."""
        return self._action_type == ActionType.THEN

    @property
    def requires_ui_interaction(self) -> bool:
        """Check if action requires UI interaction."""
        return self._implementation_type == ImplementationType.UI_INTERACTION

    @property
    def uses_api_calls(self) -> bool:
        """Check if action uses API calls."""
        return self._implementation_type == ImplementationType.API_CALL

    @property
    def is_verification_action(self) -> bool:
        """Check if this is a verification action."""
        return self._implementation_type == ImplementationType.VERIFICATION

    def update_details(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        execution_timeout: Optional[int] = None,
        retry_count: Optional[int] = None,
    ) -> None:
        """
        Update action basic details.

        Args:
            name: New action name
            description: New description
            is_active: New active status
            execution_timeout: New timeout
            retry_count: New retry count

        Raises:
            ActionValidationError: If validation fails
        """
        if name is not None:
            self._name = name
        if description is not None:
            self._description = description
        if is_active is not None:
            self._is_active = is_active
        if execution_timeout is not None:
            self._execution_timeout = execution_timeout
        if retry_count is not None:
            self._retry_count = retry_count

        self._validate()
        self._updated_at = datetime.utcnow()

    def update_classification(
        self,
        action_type: Optional[ActionType] = None,
        erpnext_module: Optional[str] = None,
        implementation_type: Optional[ImplementationType] = None,
    ) -> None:
        """
        Update action classification.

        Args:
            action_type: New action type
            erpnext_module: New ERPNext module
            implementation_type: New implementation type

        Raises:
            ActionValidationError: If validation fails
        """
        if action_type is not None:
            self._action_type = action_type
        if erpnext_module is not None:
            self._erpnext_module = erpnext_module
        if implementation_type is not None:
            self._implementation_type = implementation_type

        self._validate()
        self._updated_at = datetime.utcnow()

    def add_parameter(self, parameter: ActionParameter) -> None:
        """
        Add a parameter to the action.

        Args:
            parameter: Parameter to add

        Raises:
            ActionValidationError: If parameter name already exists
        """
        # Check for duplicate parameter names
        existing_names = [p.name for p in self._parameters]
        if parameter.name in existing_names:
            raise ActionValidationError(f"Parameter '{parameter.name}' already exists")

        self._parameters.append(parameter)
        self._updated_at = datetime.utcnow()

    def remove_parameter(self, parameter_name: str) -> bool:
        """
        Remove a parameter from the action.

        Args:
            parameter_name: Name of parameter to remove

        Returns:
            True if parameter was removed, False if not found
        """
        for i, param in enumerate(self._parameters):
            if param.name == parameter_name:
                self._parameters.pop(i)
                self._updated_at = datetime.utcnow()
                return True
        return False

    def get_parameter(self, parameter_name: str) -> Optional[ActionParameter]:
        """
        Get parameter by name.

        Args:
            parameter_name: Name of parameter to find

        Returns:
            Parameter if found, None otherwise
        """
        for param in self._parameters:
            if param.name == parameter_name:
                return param
        return None

    def add_expected_output(self, output: ActionOutput) -> None:
        """
        Add an expected output to the action.

        Args:
            output: Output to add

        Raises:
            ActionValidationError: If output name already exists
        """
        # Check for duplicate output names
        existing_names = [o.name for o in self._expected_outputs]
        if output.name in existing_names:
            raise ActionValidationError(f"Output '{output.name}' already exists")

        self._expected_outputs.append(output)
        self._updated_at = datetime.utcnow()

    def remove_expected_output(self, output_name: str) -> bool:
        """
        Remove an expected output from the action.

        Args:
            output_name: Name of output to remove

        Returns:
            True if output was removed, False if not found
        """
        for i, output in enumerate(self._expected_outputs):
            if output.name == output_name:
                self._expected_outputs.pop(i)
                self._updated_at = datetime.utcnow()
                return True
        return False

    def update_robot_keywords(self, keywords: list[str]) -> None:
        """
        Update Robot Framework keywords.

        Args:
            keywords: New list of keywords
        """
        self._robot_keywords = keywords or []
        self._updated_at = datetime.utcnow()

    def add_robot_keyword(self, keyword: str) -> None:
        """
        Add a Robot Framework keyword.

        Args:
            keyword: Keyword to add
        """
        if keyword and keyword not in self._robot_keywords:
            self._robot_keywords.append(keyword)
            self._updated_at = datetime.utcnow()

    def update_tags(self, tags: list[str]) -> None:
        """
        Update action tags.

        Args:
            tags: New list of tags
        """
        self._tags = [tag.lower().strip() for tag in tags or [] if tag.strip()]
        self._updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the action.

        Args:
            tag: Tag to add
        """
        clean_tag = tag.lower().strip()
        if clean_tag and clean_tag not in self._tags:
            self._tags.append(clean_tag)
            self._updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> bool:
        """
        Remove a tag from the action.

        Args:
            tag: Tag to remove

        Returns:
            True if tag was removed, False if not found
        """
        clean_tag = tag.lower().strip()
        if clean_tag in self._tags:
            self._tags.remove(clean_tag)
            self._updated_at = datetime.utcnow()
            return True
        return False

    def has_tag(self, tag: str) -> bool:
        """
        Check if action has a specific tag.

        Args:
            tag: Tag to check

        Returns:
            True if tag exists, False otherwise
        """
        return tag.lower().strip() in self._tags

    def validate_parameter_values(self, parameter_values: dict[str, Any]) -> list[str]:
        """
        Validate parameter values against parameter definitions.

        Args:
            parameter_values: Values to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check all required parameters are provided
        for param in self._parameters:
            if param.required and param.name not in parameter_values:
                errors.append(f"Required parameter '{param.name}' is missing")
            elif param.name in parameter_values:
                param_errors = param.validate_value(parameter_values[param.name])
                errors.extend(param_errors)

        # Check for unknown parameters
        param_names = {p.name for p in self._parameters}
        for param_name in parameter_values.keys():
            if param_name not in param_names:
                errors.append(f"Unknown parameter '{param_name}'")

        return errors

    def is_valid(self) -> bool:
        """
        Check if the action is valid.

        Returns:
            True if action is valid, False otherwise
        """
        try:
            self._validate()
            return True
        except ActionValidationError:
            return False

    def get_validation_errors(self) -> list[str]:
        """
        Get all validation errors for this action.

        Returns:
            List of validation error messages
        """
        errors = []

        try:
            self._validate()
        except ActionValidationError as e:
            errors.append(str(e))

        return errors

    def _validate(self) -> None:
        """
        Validate action domain rules.

        Raises:
            ActionValidationError: If validation fails
        """
        # Validate name
        if not self._name:
            raise ActionValidationError("Action name is required")

        if len(self._name.strip()) < 3:
            raise ActionValidationError("Action name must be at least 3 characters")

        if len(self._name) > 200:
            raise ActionValidationError("Action name must not exceed 200 characters")

        # Validate description
        if not self._description:
            raise ActionValidationError("Action description is required")

        if len(self._description.strip()) < 10:
            raise ActionValidationError(
                "Action description must be at least 10 characters"
            )

        if len(self._description) > 1000:
            raise ActionValidationError(
                "Action description must not exceed 1000 characters"
            )

        # Validate execution timeout
        if self._execution_timeout < 1:
            raise ActionValidationError("Execution timeout must be at least 1 second")

        if self._execution_timeout > 3600:  # 1 hour
            raise ActionValidationError(
                "Execution timeout must not exceed 3600 seconds (1 hour)"
            )

        # Validate retry count
        if self._retry_count < 0:
            raise ActionValidationError("Retry count cannot be negative")

        if self._retry_count > 10:
            raise ActionValidationError("Retry count must not exceed 10")

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        action_type: ActionType,
        erpnext_module: str,
        implementation_type: ImplementationType,
        parameters: Optional[list[ActionParameter]] = None,
        expected_outputs: Optional[list[ActionOutput]] = None,
        robot_keywords: Optional[list[str]] = None,
        validation_rules: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        prerequisites: Optional[list[str]] = None,
        postconditions: Optional[list[str]] = None,
        execution_timeout: int = 30,
        retry_count: int = 0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Action:
        """
        Create a new action with required fields.

        Args:
            name: Action name
            description: Action description
            action_type: BDD action type
            erpnext_module: ERPNext module
            implementation_type: Implementation type
            parameters: Input parameters
            expected_outputs: Output definitions
            robot_keywords: Robot Framework keywords
            validation_rules: Validation configuration
            tags: Categorization tags
            prerequisites: Prerequisites for execution
            postconditions: Expected post-execution state
            execution_timeout: Timeout in seconds
            retry_count: Number of retries
            metadata: Additional configuration

        Returns:
            New Action instance

        Raises:
            ActionValidationError: If validation fails
        """
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            action_type=action_type,
            erpnext_module=erpnext_module,
            implementation_type=implementation_type,
            parameters=parameters,
            expected_outputs=expected_outputs,
            robot_keywords=robot_keywords,
            validation_rules=validation_rules,
            tags=tags,
            prerequisites=prerequisites,
            postconditions=postconditions,
            execution_timeout=execution_timeout,
            retry_count=retry_count,
            metadata=metadata,
            created_at=datetime.utcnow(),
        )

    def __str__(self) -> str:
        """String representation of the action."""
        return f"Action(id={self.id}, name='{self.name}', type={self.action_type})"

    def __repr__(self) -> str:
        """Detailed string representation of the action."""
        return (
            f"Action(id={self.id}, name='{self.name}', "
            f"type={self.action_type}, module='{self.erpnext_module}', "
            f"params={len(self._parameters)}, active={self.is_active})"
        )
