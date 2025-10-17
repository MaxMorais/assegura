"""
Advanced Action Parameter and Output Structures

This module provides sophisticated parameter validation, output structures,
and type checking for action definitions in the ERPNext test automation framework.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union


class ParameterType(Enum):
    """Enhanced parameter types with validation rules."""

    # Basic types
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"

    # Complex types
    OBJECT = "object"
    ARRAY = "array"
    JSON = "json"

    # ERPNext specific types
    DOCTYPE = "doctype"
    DOCUMENT_NAME = "document_name"
    FIELD_NAME = "field_name"
    USER_EMAIL = "user_email"
    COMPANY_NAME = "company_name"
    CURRENCY_CODE = "currency_code"

    # UI specific types
    SELECTOR = "selector"
    XPATH = "xpath"
    CSS_SELECTOR = "css_selector"

    # File types
    FILE_PATH = "file_path"
    IMAGE_PATH = "image_path"
    PDF_PATH = "pdf_path"

    # Network types
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"

    # Validation types
    REGEX_PATTERN = "regex_pattern"
    ENUM_VALUE = "enum_value"


class ValidationRule(ABC):
    """Abstract base class for parameter validation rules."""

    @abstractmethod
    def validate(
        self, value: Any, context: Optional[dict[str, Any]] = None
    ) -> list[str]:
        """
        Validate a value against this rule.

        Args:
            value: Value to validate
            context: Optional validation context

        Returns:
            List of validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def description(self) -> str:
        """Get human-readable description of this rule."""
        pass


class LengthRule(ValidationRule):
    """Validate string/array length constraints."""

    def __init__(
        self, min_length: Optional[int] = None, max_length: Optional[int] = None
    ):
        self.min_length = min_length
        self.max_length = max_length

    def validate(
        self, value: Any, context: Optional[dict[str, Any]] = None
    ) -> list[str]:
        errors = []

        if value is None:
            return errors

        if hasattr(value, "__len__"):
            length = len(value)
            if self.min_length is not None and length < self.min_length:
                errors.append(
                    f"Value length {length} is less than minimum {self.min_length}"
                )
            if self.max_length is not None and length > self.max_length:
                errors.append(
                    f"Value length {length} exceeds maximum {self.max_length}"
                )
        else:
            errors.append("Value does not support length validation")

        return errors

    def description(self) -> str:
        parts = []
        if self.min_length is not None:
            parts.append(f"min length {self.min_length}")
        if self.max_length is not None:
            parts.append(f"max length {self.max_length}")
        return f"Length constraints: {', '.join(parts)}"


class RegexRule(ValidationRule):
    """Validate value against regular expression pattern."""

    def __init__(self, pattern: str, flags: int = 0):
        self.pattern = pattern
        self.regex = re.compile(pattern, flags)

    def validate(
        self, value: Any, context: Optional[dict[str, Any]] = None
    ) -> list[str]:
        errors = []

        if value is None:
            return errors

        str_value = str(value)
        if not self.regex.match(str_value):
            errors.append(
                f"Value '{str_value}' does not match pattern '{self.pattern}'"
            )

        return errors

    def description(self) -> str:
        return f"Must match regex pattern: {self.pattern}"


class RangeRule(ValidationRule):
    """Validate numeric range constraints."""

    def __init__(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
    ):
        self.min_value = min_value
        self.max_value = max_value

    def validate(
        self, value: Any, context: Optional[dict[str, Any]] = None
    ) -> list[str]:
        errors = []

        if value is None:
            return errors

        try:
            num_value = float(value)
            if self.min_value is not None and num_value < self.min_value:
                errors.append(
                    f"Value {num_value} is less than minimum {self.min_value}"
                )
            if self.max_value is not None and num_value > self.max_value:
                errors.append(f"Value {num_value} exceeds maximum {self.max_value}")
        except (ValueError, TypeError):
            errors.append(f"Value '{value}' is not numeric for range validation")

        return errors

    def description(self) -> str:
        parts = []
        if self.min_value is not None:
            parts.append(f"min {self.min_value}")
        if self.max_value is not None:
            parts.append(f"max {self.max_value}")
        return f"Range constraints: {', '.join(parts)}"


class EnumRule(ValidationRule):
    """Validate value is in allowed enumeration."""

    def __init__(self, allowed_values: list[Any]):
        self.allowed_values = allowed_values

    def validate(
        self, value: Any, context: Optional[dict[str, Any]] = None
    ) -> list[str]:
        errors = []

        if value is None:
            return errors

        if value not in self.allowed_values:
            errors.append(
                f"Value '{value}' not in allowed values: {self.allowed_values}"
            )

        return errors

    def description(self) -> str:
        return f"Must be one of: {self.allowed_values}"


class ERPNextDocTypeRule(ValidationRule):
    """Validate ERPNext document type exists."""

    def __init__(self, valid_doctypes: Optional[list[str]] = None):
        self.valid_doctypes = valid_doctypes or [
            "User",
            "Company",
            "Customer",
            "Supplier",
            "Item",
            "Sales Invoice",
            "Purchase Invoice",
            "Sales Order",
            "Purchase Order",
            "Quotation",
            "Delivery Note",
            "Purchase Receipt",
            "Payment Entry",
            "Journal Entry",
            "Lead",
            "Opportunity",
            "Project",
            "Task",
            "Timesheet",
            "Employee",
            "Salary Slip",
            "Leave Application",
            "Attendance",
            "Asset",
            "Stock Entry",
        ]

    def validate(
        self, value: Any, context: Optional[dict[str, Any]] = None
    ) -> list[str]:
        errors = []

        if value is None:
            return errors

        str_value = str(value)
        if str_value not in self.valid_doctypes:
            errors.append(
                f"DocType '{str_value}' not recognized. Valid types: {', '.join(self.valid_doctypes[:10])}..."
            )

        return errors

    def description(self) -> str:
        return f"Must be valid ERPNext DocType (e.g., {', '.join(self.valid_doctypes[:5])})"


@dataclass
class ActionParameterAdvanced:
    """Advanced action parameter with comprehensive validation."""

    name: str
    param_type: ParameterType
    required: bool = True
    description: str = ""
    default_value: Any = None
    validation_rules: list[ValidationRule] = field(default_factory=list)

    # Advanced features
    depends_on: Optional[str] = None  # Parameter this depends on
    conditional_required: Optional[dict[str, Any]] = None  # Conditions for requirement
    transformation: Optional[str] = None  # Data transformation rule
    examples: list[Any] = field(default_factory=list)

    # ERPNext specific
    erpnext_field: Optional[str] = None  # Corresponding ERPNext field
    doctype_context: Optional[str] = None  # Related DocType

    # UI hints
    ui_component: str = "input"  # UI component type
    ui_placeholder: str = ""
    ui_help_text: str = ""

    def __post_init__(self):
        """Initialize parameter with type-specific validation rules."""
        if not self.validation_rules:
            self.validation_rules = self._get_default_validation_rules()

    def _get_default_validation_rules(self) -> list[ValidationRule]:
        """Get default validation rules for parameter type."""
        rules = []

        if self.param_type == ParameterType.STRING:
            rules.append(LengthRule(max_length=1000))
        elif self.param_type == ParameterType.EMAIL:
            rules.append(RegexRule(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"))
        elif self.param_type == ParameterType.URL:
            rules.append(RegexRule(r"^https?://[^\s/$.?#].[^\s]*$"))
        elif self.param_type == ParameterType.PHONE:
            rules.append(RegexRule(r"^\+?[1-9]\d{1,14}$"))
        elif self.param_type == ParameterType.DOCTYPE:
            rules.append(ERPNextDocTypeRule())
        elif self.param_type == ParameterType.INTEGER:
            rules.append(RangeRule(min_value=-2147483648, max_value=2147483647))
        elif self.param_type == ParameterType.FLOAT:
            rules.append(RangeRule(min_value=-1e308, max_value=1e308))

        return rules

    def validate_value(
        self, value: Any, context: Optional[dict[str, Any]] = None
    ) -> list[str]:
        """
        Validate parameter value against all rules.

        Args:
            value: Value to validate
            context: Validation context (other parameters, etc.)

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check if required
        if self.required and (value is None or value == ""):
            # Check conditional requirements
            if self.conditional_required and context:
                required = self._evaluate_conditional_required(context)
                if required:
                    errors.append(f"Parameter '{self.name}' is required")
            else:
                errors.append(f"Parameter '{self.name}' is required")
            return errors

        # Skip validation if value is None/empty and not required
        if value is None or value == "":
            return errors

        # Type validation
        type_error = self._validate_type(value)
        if type_error:
            errors.append(type_error)
            return errors  # Don't continue if type is wrong

        # Apply all validation rules
        for rule in self.validation_rules:
            rule_errors = rule.validate(value, context)
            errors.extend(rule_errors)

        # Dependency validation
        if self.depends_on and context:
            dep_error = self._validate_dependency(value, context)
            if dep_error:
                errors.append(dep_error)

        return errors

    def _validate_type(self, value: Any) -> Optional[str]:
        """Validate value matches expected type."""

        if self.param_type == ParameterType.STRING:
            if not isinstance(value, str):
                return f"Expected string, got {type(value).__name__}"
        elif self.param_type == ParameterType.INTEGER:
            if not isinstance(value, int):
                try:
                    int(value)
                except (ValueError, TypeError):
                    return f"Expected integer, got {type(value).__name__}"
        elif self.param_type == ParameterType.FLOAT:
            if not isinstance(value, (int, float)):
                try:
                    float(value)
                except (ValueError, TypeError):
                    return f"Expected number, got {type(value).__name__}"
        elif self.param_type == ParameterType.BOOLEAN:
            if not isinstance(value, bool):
                if str(value).lower() not in ["true", "false", "1", "0", "yes", "no"]:
                    return f"Expected boolean, got {type(value).__name__}"
        elif self.param_type == ParameterType.ARRAY:
            if not isinstance(value, (list, tuple)):
                return f"Expected array, got {type(value).__name__}"
        elif self.param_type == ParameterType.OBJECT:
            if not isinstance(value, dict):
                return f"Expected object, got {type(value).__name__}"
        elif self.param_type == ParameterType.JSON:
            if isinstance(value, str):
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    return "Invalid JSON string"
            elif not isinstance(value, (dict, list)):
                return f"Expected JSON (object/array), got {type(value).__name__}"

        return None

    def _evaluate_conditional_required(self, context: dict[str, Any]) -> bool:
        """Evaluate conditional requirement rules."""
        if not self.conditional_required:
            return False

        for condition_param, expected_value in self.conditional_required.items():
            if condition_param in context:
                if context[condition_param] == expected_value:
                    return True

        return False

    def _validate_dependency(
        self, value: Any, context: dict[str, Any]
    ) -> Optional[str]:
        """Validate parameter dependency."""
        if self.depends_on not in context:
            return f"Parameter '{self.name}' depends on '{self.depends_on}' which is not provided"

        return None

    def transform_value(self, value: Any) -> Any:
        """Apply transformation to parameter value."""
        if not self.transformation or value is None:
            return value

        # Common transformations
        if self.transformation == "upper":
            return str(value).upper()
        elif self.transformation == "lower":
            return str(value).lower()
        elif self.transformation == "trim":
            return str(value).strip()
        elif self.transformation == "int":
            return int(value)
        elif self.transformation == "float":
            return float(value)
        elif self.transformation == "json_parse":
            if isinstance(value, str):
                return json.loads(value)
            return value

        return value

    def get_ui_schema(self) -> dict[str, Any]:
        """Get UI schema for parameter rendering."""
        schema = {
            "type": self.param_type.value,
            "title": self.name.replace("_", " ").title(),
            "description": self.description or self.ui_help_text,
            "required": self.required,
            "component": self.ui_component,
        }

        if self.ui_placeholder:
            schema["placeholder"] = self.ui_placeholder

        if self.default_value is not None:
            schema["default"] = self.default_value

        if self.examples:
            schema["examples"] = self.examples

        # Add validation constraints to schema
        for rule in self.validation_rules:
            if isinstance(rule, LengthRule):
                if rule.min_length is not None:
                    schema["minLength"] = rule.min_length
                if rule.max_length is not None:
                    schema["maxLength"] = rule.max_length
            elif isinstance(rule, RangeRule):
                if rule.min_value is not None:
                    schema["minimum"] = rule.min_value
                if rule.max_value is not None:
                    schema["maximum"] = rule.max_value
            elif isinstance(rule, EnumRule):
                schema["enum"] = rule.allowed_values
            elif isinstance(rule, RegexRule):
                schema["pattern"] = rule.pattern

        return schema


@dataclass
class ActionOutputAdvanced:
    """Advanced action output with type validation and transformation."""

    name: str
    output_type: ParameterType
    description: str = ""
    required: bool = True

    # Advanced features
    transformation: Optional[str] = None
    validation_rules: list[ValidationRule] = field(default_factory=list)
    examples: list[Any] = field(default_factory=list)

    # Output-specific
    capture_method: str = "return"  # return, extract, parse
    extraction_rule: Optional[str] = None  # XPath, JSON path, regex
    aggregation: Optional[str] = None  # sum, count, avg, etc.

    # ERPNext specific
    erpnext_field: Optional[str] = None
    doctype_context: Optional[str] = None

    def validate_output(
        self, value: Any, context: Optional[dict[str, Any]] = None
    ) -> list[str]:
        """Validate output value."""
        errors = []

        if self.required and (value is None or value == ""):
            errors.append(f"Output '{self.name}' is required but not provided")
            return errors

        if value is None or value == "":
            return errors

        # Type validation
        type_error = self._validate_output_type(value)
        if type_error:
            errors.append(type_error)

        # Apply validation rules
        for rule in self.validation_rules:
            rule_errors = rule.validate(value, context)
            errors.extend(rule_errors)

        return errors

    def _validate_output_type(self, value: Any) -> Optional[str]:
        """Validate output type."""
        # Similar to parameter type validation
        if self.output_type == ParameterType.STRING:
            if not isinstance(value, str):
                return f"Expected string output, got {type(value).__name__}"
        elif self.output_type == ParameterType.INTEGER:
            if not isinstance(value, int):
                try:
                    int(value)
                except (ValueError, TypeError):
                    return f"Expected integer output, got {type(value).__name__}"
        elif self.output_type == ParameterType.BOOLEAN:
            if not isinstance(value, bool):
                if str(value).lower() not in ["true", "false", "1", "0"]:
                    return f"Expected boolean output, got {type(value).__name__}"

        return None

    def transform_output(self, value: Any) -> Any:
        """Transform output value."""
        if not self.transformation or value is None:
            return value

        if self.transformation == "json_extract":
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
        elif self.transformation == "string_extract":
            return str(value)
        elif self.transformation == "count":
            if hasattr(value, "__len__"):
                return len(value)
            return 1 if value else 0

        return value

    def extract_value(self, raw_output: Any) -> Any:
        """Extract value from raw output using extraction rules."""
        if not self.extraction_rule:
            return raw_output

        if self.capture_method == "extract":
            # JSON path extraction
            if self.extraction_rule.startswith("$."):
                # Simple JSON path (could use jsonpath library for complex paths)
                path_parts = self.extraction_rule[2:].split(".")
                current = raw_output
                for part in path_parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        return None
                return current

            # Regex extraction
            elif self.extraction_rule.startswith("regex:"):
                pattern = self.extraction_rule[6:]
                if isinstance(raw_output, str):
                    match = re.search(pattern, raw_output)
                    return (
                        match.group(1)
                        if match and match.groups()
                        else match.group(0)
                        if match
                        else None
                    )

        return raw_output


class ParameterSetValidator:
    """Validate complete parameter sets with cross-parameter rules."""

    def __init__(self, parameters: list[ActionParameterAdvanced]):
        self.parameters = {p.name: p for p in parameters}

    def validate_parameter_set(self, values: dict[str, Any]) -> dict[str, list[str]]:
        """
        Validate complete parameter set.

        Args:
            values: Parameter values to validate

        Returns:
            Dictionary mapping parameter names to validation errors
        """
        errors = {}

        # Transform values first
        transformed_values = {}
        for param_name, param in self.parameters.items():
            if param_name in values:
                if hasattr(param, 'transform_value'):
                    transformed_values[param_name] = param.transform_value(
                        values[param_name]
                    )
                else:
                    transformed_values[param_name] = values[param_name]
            else:
                transformed_values[param_name] = param.default_value

        # Validate each parameter
        for param_name, param in self.parameters.items():
            value = transformed_values.get(param_name)
            param_errors = param.validate_value(value)
            if param_errors:
                errors[param_name] = param_errors

        # Cross-parameter validation
        cross_errors = self._validate_cross_parameters(transformed_values)
        for param_name, cross_error_list in cross_errors.items():
            if param_name in errors:
                errors[param_name].extend(cross_error_list)
            else:
                errors[param_name] = cross_error_list

        return errors

    def _validate_cross_parameters(
        self, values: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Validate relationships between parameters."""
        errors = {}

        # Example cross-parameter validations
        # Date range validation
        if "start_date" in values and "end_date" in values:
            start = values["start_date"]
            end = values["end_date"]
            if start and end and start > end:
                errors.setdefault("end_date", []).append(
                    "End date must be after start date"
                )

        # Conditional requirements (beyond single parameter level)
        if "operation_type" in values and values["operation_type"] == "bulk":
            if not values.get("batch_size"):
                errors.setdefault("batch_size", []).append(
                    "Batch size required for bulk operations"
                )

        return errors

    def get_parameter_schema(self) -> dict[str, Any]:
        """Get JSON schema for all parameters."""
        schema = {"type": "object", "properties": {}, "required": []}

        for param_name, param in self.parameters.items():
            schema["properties"][param_name] = param.get_ui_schema()
            if param.required:
                schema["required"].append(param_name)

        return schema


class OutputSetValidator:
    """Validate complete output sets."""

    def __init__(self, outputs: list[ActionOutputAdvanced]):
        self.outputs = {o.name: o for o in outputs}

    def validate_output_set(self, values: dict[str, Any]) -> dict[str, list[str]]:
        """Validate complete output set."""
        errors = {}

        for output_name, output in self.outputs.items():
            value = values.get(output_name)
            output_errors = output.validate_output(value, values)
            if output_errors:
                errors[output_name] = output_errors

        return errors

    def process_outputs(self, raw_outputs: dict[str, Any]) -> dict[str, Any]:
        """Process and transform raw outputs."""
        processed = {}

        for output_name, output in self.outputs.items():
            raw_value = raw_outputs.get(output_name)
            if raw_value is not None:
                extracted = output.extract_value(raw_value)
                transformed = output.transform_output(extracted)
                processed[output_name] = transformed

        return processed


# Factory functions for common parameter types
def create_doctype_parameter(
    name: str = "doctype", required: bool = True, **kwargs
) -> ActionParameterAdvanced:
    """Create ERPNext DocType parameter."""
    return ActionParameterAdvanced(
        name=name,
        param_type=ParameterType.DOCTYPE,
        required=required,
        description="ERPNext document type",
        ui_component="select",
        ui_placeholder="Select document type",
        **kwargs,
    )


def create_document_name_parameter(
    name: str = "document_name", depends_on: str = "doctype", **kwargs
) -> ActionParameterAdvanced:
    """Create document name parameter."""
    return ActionParameterAdvanced(
        name=name,
        param_type=ParameterType.DOCUMENT_NAME,
        required=True,
        description="Document name/ID",
        depends_on=depends_on,
        ui_placeholder="Enter document name",
        **kwargs,
    )


def create_field_data_parameter(
    name: str = "field_data", **kwargs
) -> ActionParameterAdvanced:
    """Create field data object parameter."""
    return ActionParameterAdvanced(
        name=name,
        param_type=ParameterType.OBJECT,
        required=True,
        description="Field values as key-value pairs",
        ui_component="json_editor",
        examples=[{"field1": "value1", "field2": "value2"}],
        **kwargs,
    )


def create_selector_parameter(
    name: str = "selector", **kwargs
) -> ActionParameterAdvanced:
    """Create UI selector parameter."""
    return ActionParameterAdvanced(
        name=name,
        param_type=ParameterType.SELECTOR,
        required=True,
        description="CSS selector or XPath for UI element",
        ui_placeholder="e.g., #element-id or //button[@text='Save']",
        validation_rules=[LengthRule(min_length=1, max_length=500)],
        **kwargs,
    )


def create_boolean_output(
    name: str, description: str = "", **kwargs
) -> ActionOutputAdvanced:
    """Create boolean output (success/failure)."""
    return ActionOutputAdvanced(
        name=name,
        output_type=ParameterType.BOOLEAN,
        description=description,
        examples=[True, False],
        **kwargs,
    )


def create_document_name_output(
    name: str = "document_name", **kwargs
) -> ActionOutputAdvanced:
    """Create document name output."""
    return ActionOutputAdvanced(
        name=name,
        output_type=ParameterType.STRING,
        description="Name/ID of the document",
        extraction_rule="$.name",
        **kwargs,
    )
