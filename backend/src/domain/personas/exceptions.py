"""Persona domain exceptions.

Custom exceptions for persona-related business rule violations
and validation errors in the ERPNext Test Automation Meta-Framework.
"""

from typing import Any, Optional


class PersonaDomainError(Exception):
    """Base exception for persona domain errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        """Initialize persona domain error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PersonaValidationError(PersonaDomainError):
    """Exception raised when persona validation fails."""

    def __init__(
        self,
        field: str,
        message: str,
        value: Optional[Any] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """Initialize persona validation error.

        Args:
            field: Field that failed validation
            message: Validation error message
            value: Value that caused validation failure
            details: Additional error details
        """
        super().__init__(message, details)
        self.field = field
        self.value = value

    def __str__(self) -> str:
        """String representation of the error."""
        return self.message


class PersonaNotFoundError(PersonaDomainError):
    """Exception raised when persona is not found."""

    def __init__(self, identifier: str, identifier_type: str = "id"):
        """Initialize persona not found error.

        Args:
            identifier: Persona identifier that was not found
            identifier_type: Type of identifier (id, name, etc.)
        """
        message = f"Persona not found with {identifier_type}: {identifier}"
        super().__init__(message)
        self.identifier = identifier
        self.identifier_type = identifier_type


class PersonaAlreadyExistsError(PersonaDomainError):
    """Exception raised when trying to create persona that already exists."""

    def __init__(self, field: str, value: str):
        """Initialize persona already exists error.

        Args:
            field: Field that has duplicate value
            value: Duplicate value
        """
        message = f"Persona with {field} '{value}' already exists"
        super().__init__(message)
        self.field = field
        self.value = value


class PersonaStateError(PersonaDomainError):
    """Exception raised when persona is in invalid state for operation."""

    def __init__(self, message: str, current_state: Optional[str] = None):
        """Initialize persona state error.

        Args:
            message: State error message
            current_state: Current state that prevents operation
        """
        super().__init__(message)
        self.current_state = current_state


class PersonaBusinessRuleError(PersonaDomainError):
    """Exception raised when persona business rule is violated."""

    def __init__(self, rule: str, message: str):
        """Initialize persona business rule error.

        Args:
            rule: Business rule that was violated
            message: Error message describing the violation
        """
        super().__init__(message)
        self.rule = rule


class PersonaPermissionError(PersonaDomainError):
    """Exception raised for persona permission-related errors."""

    def __init__(self, message: str, permission: Optional[str] = None):
        """Initialize persona permission error.

        Args:
            message: Permission error message
            permission: Permission that caused the error
        """
        super().__init__(message)
        self.permission = permission


class PersonaRoleError(PersonaDomainError):
    """Exception raised for persona role-related errors."""

    def __init__(self, message: str, role: Optional[str] = None):
        """Initialize persona role error.

        Args:
            message: Role error message
            role: Role that caused the error
        """
        super().__init__(message)
        self.role = role


class PersonaConcurrencyError(PersonaDomainError):
    """Exception raised when persona concurrent modification is detected."""

    def __init__(self, persona_id: str, expected_version: int, actual_version: int):
        """Initialize persona concurrency error.

        Args:
            persona_id: ID of the persona being modified
            expected_version: Expected version number
            actual_version: Actual version number in storage
        """
        message = (
            f"Persona {persona_id} was modified by another process. "
            f"Expected version {expected_version}, found version {actual_version}"
        )
        super().__init__(message)
        self.persona_id = persona_id
        self.expected_version = expected_version
        self.actual_version = actual_version


class PersonaMultipleValidationError(PersonaDomainError):
    """Exception raised when multiple validation errors occur."""

    def __init__(self, errors: list[PersonaValidationError]):
        """Initialize multiple validation errors.

        Args:
            errors: List of validation errors
        """
        field_names = [error.field for error in errors]
        combined_message = "Multiple validation errors: " + "; ".join(field_names)
        super().__init__(combined_message)
        self.errors = errors
        self.error_count = len(errors)

    def get_field_errors(self) -> dict[str, list[str]]:
        """Get errors grouped by field.

        Returns:
            Dictionary mapping field names to error messages
        """
        field_errors = {}
        for error in self.errors:
            field = error.field or "general"
            if field not in field_errors:
                field_errors[field] = []
            field_errors[field].append(error.message)
        return field_errors

    def has_field_error(self, field: str) -> bool:
        """Check if specific field has validation errors.

        Args:
            field: Field name to check

        Returns:
            True if field has errors
        """
        return any(error.field == field for error in self.errors)


def create_validation_error(
    message: str, field: Optional[str] = None, value: Optional[Any] = None
) -> PersonaValidationError:
    """Create a validation error with consistent formatting.

    Args:
        message: Error message
        field: Field that failed validation
        value: Value that caused failure

    Returns:
        PersonaValidationError instance
    """
    return PersonaValidationError(message, field, value)


def create_business_rule_error(rule: str, message: str) -> PersonaBusinessRuleError:
    """Create a business rule error with consistent formatting.

    Args:
        rule: Business rule identifier
        message: Error message

    Returns:
        PersonaBusinessRuleError instance
    """
    return PersonaBusinessRuleError(rule, message)


def aggregate_validation_errors(
    errors: list[PersonaValidationError],
) -> PersonaMultipleValidationError:
    """Aggregate multiple validation errors into single exception.

    Args:
        errors: List of validation errors

    Returns:
        PersonaMultipleValidationError containing all errors
    """
    return PersonaMultipleValidationError(errors)
