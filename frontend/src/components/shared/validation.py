"""Form validation utilities for Streamlit components.

Provides validation functions and error handling for form inputs
in the ERPNext Test Automation Meta-Framework frontend.
"""

import re
from datetime import date, datetime
from typing import Any, Optional, Union


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def validate_required(value: Any, field_name: str) -> Any:
    """Validate that a required field has a value.

    Args:
        value: Field value to validate
        field_name: Name of the field for error messages

    Returns:
        The value if valid

    Raises:
        ValidationError: If field is empty or None
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(f"{field_name} is required")
    return value


def validate_email(email: str, field_name: str = "Email") -> str:
    """Validate email format.

    Args:
        email: Email to validate
        field_name: Name of the field for error messages

    Returns:
        The email if valid

    Raises:
        ValidationError: If email format is invalid
    """
    if not email:
        return email

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError(f"{field_name} must be a valid email address")

    return email


def validate_url(url: str, field_name: str = "URL") -> str:
    """Validate URL format.

    Args:
        url: URL to validate
        field_name: Name of the field for error messages

    Returns:
        The URL if valid

    Raises:
        ValidationError: If URL format is invalid
    """
    if not url:
        return url

    url_pattern = r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$"
    if not re.match(url_pattern, url):
        raise ValidationError(f"{field_name} must be a valid URL")

    return url


def validate_length(
    value: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: str = "Field",
) -> str:
    """Validate string length.

    Args:
        value: String to validate
        min_length: Minimum required length
        max_length: Maximum allowed length
        field_name: Name of the field for error messages

    Returns:
        The value if valid

    Raises:
        ValidationError: If length is invalid
    """
    if not isinstance(value, str):
        return value

    length = len(value)

    if min_length is not None and length < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")

    if max_length is not None and length > max_length:
        raise ValidationError(
            f"{field_name} must be no more than {max_length} characters"
        )

    return value


def validate_number_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    field_name: str = "Number",
) -> Union[int, float]:
    """Validate number is within range.

    Args:
        value: Number to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        field_name: Name of the field for error messages

    Returns:
        The value if valid

    Raises:
        ValidationError: If number is out of range
    """
    if not isinstance(value, (int, float)):
        return value

    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} must be no more than {max_value}")

    return value


def validate_date_range(
    value: Union[date, datetime],
    min_date: Optional[Union[date, datetime]] = None,
    max_date: Optional[Union[date, datetime]] = None,
    field_name: str = "Date",
) -> Union[date, datetime]:
    """Validate date is within range.

    Args:
        value: Date to validate
        min_date: Minimum allowed date
        max_date: Maximum allowed date
        field_name: Name of the field for error messages

    Returns:
        The value if valid

    Raises:
        ValidationError: If date is out of range
    """
    if not isinstance(value, (date, datetime)):
        return value

    # Convert datetime to date for comparison if needed
    check_date = value.date() if isinstance(value, datetime) else value
    min_check = min_date.date() if isinstance(min_date, datetime) else min_date
    max_check = max_date.date() if isinstance(max_date, datetime) else max_date

    if min_check is not None and check_date < min_check:
        raise ValidationError(f"{field_name} must be on or after {min_check}")

    if max_check is not None and check_date > max_check:
        raise ValidationError(f"{field_name} must be on or before {max_check}")

    return value


def validate_choice(value: Any, choices: list[Any], field_name: str = "Field") -> Any:
    """Validate value is in allowed choices.

    Args:
        value: Value to validate
        choices: List of allowed choices
        field_name: Name of the field for error messages

    Returns:
        The value if valid

    Raises:
        ValidationError: If value is not in choices
    """
    if value not in choices:
        raise ValidationError(
            f"{field_name} must be one of: {', '.join(map(str, choices))}"
        )

    return value


def validate_pattern(
    value: str,
    pattern: str,
    field_name: str = "Field",
    error_message: Optional[str] = None,
) -> str:
    """Validate string matches regex pattern.

    Args:
        value: String to validate
        pattern: Regex pattern to match
        field_name: Name of the field for error messages
        error_message: Custom error message

    Returns:
        The value if valid

    Raises:
        ValidationError: If pattern doesn't match
    """
    if not isinstance(value, str):
        return value

    if not re.match(pattern, value):
        message = error_message or f"{field_name} format is invalid"
        raise ValidationError(message)

    return value


class FormValidator:
    """Form validation helper class."""

    def __init__(self):
        """Initialize form validator."""
        self.errors: dict[str, str] = {}

    def add_rule(self, field_name: str, value: Any, validator_func, *args, **kwargs):
        """Add a validation rule for a field.

        Args:
            field_name: Name of the field
            value: Value to validate
            validator_func: Validation function to apply
            *args: Arguments for validator function
            **kwargs: Keyword arguments for validator function
        """
        try:
            return validator_func(value, field_name, *args, **kwargs)
        except ValidationError as e:
            self.errors[field_name] = str(e)
            return value

    def is_valid(self) -> bool:
        """Check if form is valid (no errors).

        Returns:
            True if no validation errors
        """
        return len(self.errors) == 0

    def get_errors(self) -> dict[str, str]:
        """Get all validation errors.

        Returns:
            Dictionary of field names to error messages
        """
        return self.errors.copy()

    def clear_errors(self):
        """Clear all validation errors."""
        self.errors.clear()


def validate_form_data(
    data: dict[str, Any], validation_rules: dict[str, list[dict[str, Any]]]
) -> dict[str, str]:
    """Validate form data against validation rules.

    Args:
        data: Form data to validate
        validation_rules: Dictionary of field names to validation rule lists

    Returns:
        Dictionary of validation errors (empty if no errors)

    Example:
        rules = {
            'email': [
                {'validator': validate_required},
                {'validator': validate_email}
            ],
            'age': [
                {'validator': validate_required},
                {'validator': validate_number_range, 'min_value': 18, 'max_value': 100}
            ]
        }
        errors = validate_form_data(form_data, rules)
    """
    validator = FormValidator()

    for field_name, rules in validation_rules.items():
        field_value = data.get(field_name)

        for rule in rules:
            validator_func = rule["validator"]
            rule_args = {k: v for k, v in rule.items() if k != "validator"}

            validated_value = validator.add_rule(
                field_name, field_value, validator_func, **rule_args
            )

            # Update the value for subsequent validators
            field_value = validated_value

    return validator.get_errors()


def display_validation_errors(errors: dict[str, list[str]]) -> None:
    """Display validation errors in Streamlit UI.

    Args:
        errors: Dictionary of field names to list of error messages
    """
    try:
        import streamlit as st
    except ImportError:
        return

    if not errors:
        return

    for field_name, field_errors in errors.items():
        for error in field_errors:
            st.error(f"**{field_name}**: {error}")


def validate_required_field(value: Any, field_name: str) -> bool:
    """Validate that a field is not empty.

    Args:
        value: Field value to validate
        field_name: Name of the field (for error messages)

    Returns:
        True if valid, False otherwise
    """
    try:
        validate_required(value, field_name)
        return True
    except ValidationError:
        return False


def validate_text_length(
    text: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: str = "Text"
) -> bool:
    """Validate text length constraints.

    Args:
        text: Text to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        field_name: Name of the field (for error messages)

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(text, str):
        return False

    if min_length is not None and len(text) < min_length:
        return False

    if max_length is not None and len(text) > max_length:
        return False

    return True
