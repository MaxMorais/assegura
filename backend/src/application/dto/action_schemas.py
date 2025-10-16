"""
Action Library DTO Schemas for API Requests and Responses

This module defines comprehensive Pydantic schemas for Action Library
operations, ensuring proper data validation, serialization, and
documentation for action management in the ERPNext test automation framework.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from src.application.dto.base_schemas import BaseResponseSchema, PaginatedResponse


class ActionTypeEnum(str, Enum):
    """Action types for BDD classification."""

    GIVEN = "given"
    WHEN = "when"
    THEN = "then"


class ImplementationTypeEnum(str, Enum):
    """Implementation types for actions."""

    UI_INTERACTION = "ui_interaction"
    API_CALL = "api_call"
    ROBOT_FRAMEWORK = "robot_framework"
    VERIFICATION = "verification"
    DATA_SETUP = "data_setup"
    CLEANUP = "cleanup"


class ParameterTypeEnum(str, Enum):
    """Parameter types for action parameters."""

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


# Action Parameter Schemas
class ValidationRuleSchema(BaseModel):
    """Schema for parameter validation rules."""

    rule_type: str = Field(..., description="Type of validation rule")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Rule parameters"
    )
    description: str = Field(..., description="Human-readable rule description")


class ActionParameterSchema(BaseModel):
    """Schema for action parameters."""

    name: str = Field(..., description="Parameter name")
    param_type: ParameterTypeEnum = Field(..., description="Parameter data type")
    required: bool = Field(default=True, description="Whether parameter is required")
    description: str = Field(default="", description="Parameter description")
    default_value: Optional[Any] = Field(None, description="Default value")
    validation_rules: list[ValidationRuleSchema] = Field(
        default_factory=list, description="Validation rules"
    )

    # Advanced features
    depends_on: Optional[str] = Field(None, description="Parameter this depends on")
    conditional_required: Optional[dict[str, Any]] = Field(
        None, description="Conditions for requirement"
    )
    transformation: Optional[str] = Field(None, description="Data transformation rule")
    examples: list[Any] = Field(default_factory=list, description="Example values")

    # ERPNext specific
    erpnext_field: Optional[str] = Field(
        None, description="Corresponding ERPNext field"
    )
    doctype_context: Optional[str] = Field(None, description="Related DocType")

    # UI hints
    ui_component: str = Field(default="input", description="UI component type")
    ui_placeholder: str = Field(default="", description="UI placeholder text")
    ui_help_text: str = Field(default="", description="UI help text")

    @validator("name")
    def validate_parameter_name(cls, v):
        """Validate parameter name."""
        if not v.strip():
            raise ValueError("Parameter name cannot be empty")
        if not v.replace("_", "").isalnum():
            raise ValueError("Parameter name must be alphanumeric with underscores")
        return v.strip()


class ActionParameterCreateSchema(ActionParameterSchema):
    """Schema for creating new action parameters."""

    pass


class ActionParameterUpdateSchema(BaseModel):
    """Schema for updating action parameters."""

    param_type: Optional[ParameterTypeEnum] = Field(
        None, description="Updated parameter type"
    )
    required: Optional[bool] = Field(None, description="Updated required flag")
    description: Optional[str] = Field(None, description="Updated description")
    default_value: Optional[Any] = Field(None, description="Updated default value")
    validation_rules: Optional[list[ValidationRuleSchema]] = Field(
        None, description="Updated validation rules"
    )
    examples: Optional[list[Any]] = Field(None, description="Updated examples")
    ui_component: Optional[str] = Field(None, description="Updated UI component")
    ui_placeholder: Optional[str] = Field(None, description="Updated placeholder")
    ui_help_text: Optional[str] = Field(None, description="Updated help text")


class ActionOutputSchema(BaseModel):
    """Schema for action outputs."""

    name: str = Field(..., description="Output name")
    output_type: ParameterTypeEnum = Field(..., description="Output data type")
    description: str = Field(default="", description="Output description")
    required: bool = Field(default=True, description="Whether output is required")

    # Advanced features
    transformation: Optional[str] = Field(None, description="Output transformation")
    validation_rules: list[ValidationRuleSchema] = Field(
        default_factory=list, description="Output validation rules"
    )
    examples: list[Any] = Field(default_factory=list, description="Example outputs")

    # Output-specific
    capture_method: str = Field(default="return", description="How output is captured")
    extraction_rule: Optional[str] = Field(
        None, description="Extraction rule (XPath, JSON path, regex)"
    )
    aggregation: Optional[str] = Field(
        None, description="Aggregation method (sum, count, avg)"
    )

    # ERPNext specific
    erpnext_field: Optional[str] = Field(None, description="ERPNext field mapping")
    doctype_context: Optional[str] = Field(None, description="Related DocType")

    @validator("name")
    def validate_output_name(cls, v):
        """Validate output name."""
        if not v.strip():
            raise ValueError("Output name cannot be empty")
        if not v.replace("_", "").isalnum():
            raise ValueError("Output name must be alphanumeric with underscores")
        return v.strip()


class ActionOutputCreateSchema(ActionOutputSchema):
    """Schema for creating new action outputs."""

    pass


class ActionOutputUpdateSchema(BaseModel):
    """Schema for updating action outputs."""

    output_type: Optional[ParameterTypeEnum] = Field(
        None, description="Updated output type"
    )
    description: Optional[str] = Field(None, description="Updated description")
    required: Optional[bool] = Field(None, description="Updated required flag")
    transformation: Optional[str] = Field(None, description="Updated transformation")
    capture_method: Optional[str] = Field(None, description="Updated capture method")
    extraction_rule: Optional[str] = Field(None, description="Updated extraction rule")


# Base Action Schemas
class ActionBaseSchema(BaseModel):
    """Base schema for action data."""

    name: str = Field(..., min_length=3, max_length=200, description="Action name")
    description: str = Field(
        ..., min_length=10, max_length=1000, description="Action description"
    )
    action_type: ActionTypeEnum = Field(..., description="BDD action type")
    implementation_type: ImplementationTypeEnum = Field(
        ..., description="Implementation type"
    )
    erpnext_module: Optional[str] = Field(None, description="ERPNext module")

    # Execution configuration
    execution_timeout: Optional[int] = Field(
        60, ge=1, le=3600, description="Execution timeout in seconds"
    )
    retry_count: Optional[int] = Field(
        0, ge=0, le=10, description="Number of retries on failure"
    )

    # Organization
    tags: list[str] = Field(default_factory=list, description="Action tags")
    category: Optional[str] = Field(None, description="Action category")
    version: str = Field(default="1.0.0", description="Action version")

    # Robot Framework integration
    robot_keywords: list[str] = Field(
        default_factory=list, description="Robot Framework keywords"
    )
    robot_library: Optional[str] = Field(None, description="Robot library name")

    # Documentation
    documentation_url: Optional[str] = Field(None, description="Documentation URL")
    examples: list[str] = Field(default_factory=list, description="Usage examples")

    # Status
    is_active: bool = Field(default=True, description="Whether action is active")
    is_deprecated: bool = Field(
        default=False, description="Whether action is deprecated"
    )

    @validator("name")
    def validate_action_name(cls, v):
        """Validate action name."""
        if not v.strip():
            raise ValueError("Action name cannot be empty")
        return v.strip()

    @validator("description")
    def validate_description(cls, v):
        """Validate action description."""
        if not v.strip():
            raise ValueError("Action description cannot be empty")
        return v.strip()

    @validator("tags")
    def validate_tags(cls, v):
        """Validate and clean tags."""
        return [tag.strip().lower() for tag in v if tag.strip()]

    @validator("version")
    def validate_version(cls, v):
        """Validate version format."""
        import re

        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("Version must be in format X.Y.Z")
        return v


class ActionCreateSchema(ActionBaseSchema):
    """Schema for creating new actions."""

    parameters: list[ActionParameterCreateSchema] = Field(
        default_factory=list, description="Action parameters"
    )
    expected_outputs: list[ActionOutputCreateSchema] = Field(
        default_factory=list, description="Expected outputs"
    )


class ActionUpdateSchema(BaseModel):
    """Schema for updating existing actions."""

    name: Optional[str] = Field(
        None, min_length=3, max_length=200, description="Updated name"
    )
    description: Optional[str] = Field(
        None, min_length=10, max_length=1000, description="Updated description"
    )
    action_type: Optional[ActionTypeEnum] = Field(
        None, description="Updated action type"
    )
    implementation_type: Optional[ImplementationTypeEnum] = Field(
        None, description="Updated implementation type"
    )
    erpnext_module: Optional[str] = Field(None, description="Updated ERPNext module")
    execution_timeout: Optional[int] = Field(
        None, ge=1, le=3600, description="Updated timeout"
    )
    retry_count: Optional[int] = Field(
        None, ge=0, le=10, description="Updated retry count"
    )
    tags: Optional[list[str]] = Field(None, description="Updated tags")
    category: Optional[str] = Field(None, description="Updated category")
    robot_keywords: Optional[list[str]] = Field(
        None, description="Updated Robot keywords"
    )
    robot_library: Optional[str] = Field(None, description="Updated Robot library")
    documentation_url: Optional[str] = Field(
        None, description="Updated documentation URL"
    )
    examples: Optional[list[str]] = Field(None, description="Updated examples")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    is_deprecated: Optional[bool] = Field(
        None, description="Updated deprecation status"
    )

    @validator("name")
    def validate_name(cls, v):
        """Validate action name."""
        if v is not None and not v.strip():
            raise ValueError("Action name cannot be empty")
        return v.strip() if v else v

    @validator("description")
    def validate_description(cls, v):
        """Validate action description."""
        if v is not None and not v.strip():
            raise ValueError("Action description cannot be empty")
        return v.strip() if v else v


# Action Response Schemas
class ActionComplexityScoreSchema(BaseModel):
    """Schema for action complexity scoring."""

    base_score: int = Field(..., description="Base complexity score")
    implementation_score: int = Field(..., description="Implementation complexity")
    parameter_score: int = Field(..., description="Parameter complexity")
    output_score: int = Field(..., description="Output complexity")
    keyword_score: int = Field(..., description="Robot keyword complexity")
    total_score: int = Field(..., description="Total complexity score")
    complexity_level: str = Field(
        ..., description="Complexity level (simple/medium/complex)"
    )


class ActionUsageStatsSchema(BaseModel):
    """Schema for action usage statistics."""

    usage_count: int = Field(..., description="Total usage count")
    journey_references: list[UUID] = Field(..., description="Referencing journey IDs")
    success_rate: float = Field(..., description="Success rate (0.0-1.0)")
    average_duration_seconds: Optional[float] = Field(
        None, description="Average execution duration"
    )
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    common_parameters: dict[str, Any] = Field(
        ..., description="Most common parameter values"
    )


class ActionResponseSchema(ActionBaseSchema, BaseResponseSchema):
    """Schema for action API responses."""

    parameters: list[ActionParameterSchema] = Field(
        ..., description="Action parameters"
    )
    expected_outputs: list[ActionOutputSchema] = Field(
        ..., description="Expected outputs"
    )

    # Computed properties
    parameter_count: int = Field(..., description="Number of parameters")
    output_count: int = Field(..., description="Number of outputs")
    complexity_score: Optional[ActionComplexityScoreSchema] = Field(
        None, description="Complexity analysis"
    )
    usage_stats: Optional[ActionUsageStatsSchema] = Field(
        None, description="Usage statistics"
    )


class ActionListItemSchema(BaseModel):
    """Schema for action list items."""

    id: UUID = Field(..., description="Action ID")
    name: str = Field(..., description="Action name")
    description: str = Field(..., description="Action description")
    action_type: ActionTypeEnum = Field(..., description="BDD action type")
    implementation_type: ImplementationTypeEnum = Field(
        ..., description="Implementation type"
    )
    erpnext_module: Optional[str] = Field(None, description="ERPNext module")
    category: Optional[str] = Field(None, description="Action category")
    tags: list[str] = Field(..., description="Action tags")
    parameter_count: int = Field(..., description="Number of parameters")
    output_count: int = Field(..., description="Number of outputs")
    usage_count: int = Field(default=0, description="Usage count")
    is_active: bool = Field(..., description="Whether action is active")
    is_deprecated: bool = Field(..., description="Whether action is deprecated")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# Action Search and Filtering
class ActionFilterSchema(BaseModel):
    """Schema for action filtering parameters."""

    action_type: Optional[ActionTypeEnum] = Field(
        None, description="Filter by action type"
    )
    implementation_type: Optional[ImplementationTypeEnum] = Field(
        None, description="Filter by implementation type"
    )
    erpnext_module: Optional[str] = Field(None, description="Filter by ERPNext module")
    category: Optional[str] = Field(None, description="Filter by category")
    tags: Optional[list[str]] = Field(None, description="Filter by tags")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_deprecated: Optional[bool] = Field(
        None, description="Filter by deprecation status"
    )
    has_robot_integration: Optional[bool] = Field(
        None, description="Filter by Robot Framework integration"
    )
    min_parameters: Optional[int] = Field(
        None, ge=0, description="Minimum parameter count"
    )
    max_parameters: Optional[int] = Field(
        None, ge=0, description="Maximum parameter count"
    )
    complexity_level: Optional[str] = Field(
        None, description="Filter by complexity level"
    )
    text_search: Optional[str] = Field(
        None, description="Text search in name/description/tags"
    )


class ActionSortSchema(BaseModel):
    """Schema for action sorting parameters."""

    sort_by: str = Field(
        default="created_at",
        description="Field to sort by",
        regex="^(name|created_at|updated_at|usage_count|parameter_count|action_type)$",
    )
    sort_order: str = Field(
        default="desc", description="Sort order", regex="^(asc|desc)$"
    )


# Action Pattern Schemas
class ActionPatternSchema(BaseModel):
    """Schema for action patterns."""

    pattern_name: str = Field(..., description="Pattern name")
    pattern_type: ActionTypeEnum = Field(..., description="BDD pattern type")
    description: str = Field(..., description="Pattern description")
    recommended_parameters: list[ActionParameterSchema] = Field(
        ..., description="Recommended parameters"
    )
    recommended_outputs: list[ActionOutputSchema] = Field(
        ..., description="Recommended outputs"
    )
    usage_examples: list[str] = Field(..., description="Usage examples")


# Action Validation Schemas
class ActionValidationResultSchema(BaseModel):
    """Schema for action validation results."""

    is_valid: bool = Field(..., description="Whether action is valid")
    errors: list[str] = Field(..., description="Validation errors")
    warnings: list[str] = Field(..., description="Validation warnings")
    suggestions: list[str] = Field(..., description="Improvement suggestions")


class ActionSuggestionSchema(BaseModel):
    """Schema for action suggestions."""

    action: ActionListItemSchema = Field(..., description="Suggested action")
    confidence_score: float = Field(..., description="Confidence score (0.0-1.0)")
    reason: str = Field(..., description="Reason for suggestion")
    context_match: dict[str, Any] = Field(..., description="Context matching details")


# Bulk Operations Schemas
class ActionBulkOperationSchema(BaseModel):
    """Schema for bulk action operations."""

    action_ids: list[UUID] = Field(
        ..., min_items=1, max_items=100, description="Action IDs"
    )
    operation: str = Field(
        ...,
        regex="^(activate|deactivate|deprecate|delete|tag)$",
        description="Operation",
    )
    parameters: Optional[dict[str, Any]] = Field(
        None, description="Operation parameters"
    )


class ActionBulkResultSchema(BaseModel):
    """Schema for bulk operation results."""

    successful_ids: list[UUID] = Field(..., description="Successfully processed IDs")
    failed_ids: list[UUID] = Field(..., description="Failed to process IDs")
    errors: dict[str, str] = Field(..., description="Errors by action ID")
    total_processed: int = Field(..., description="Total actions processed")


# Action Library Statistics
class ActionLibraryStatsSchema(BaseModel):
    """Schema for action library statistics."""

    total_actions: int = Field(..., description="Total number of actions")
    active_actions: int = Field(..., description="Number of active actions")
    deprecated_actions: int = Field(..., description="Number of deprecated actions")
    action_type_distribution: dict[str, int] = Field(
        ..., description="Distribution by action type"
    )
    implementation_type_distribution: dict[str, int] = Field(
        ..., description="Distribution by implementation type"
    )
    module_distribution: dict[str, int] = Field(
        ..., description="Distribution by ERPNext module"
    )
    avg_parameters_per_action: float = Field(
        ..., description="Average parameters per action"
    )
    most_used_actions: list[ActionListItemSchema] = Field(
        ..., description="Most used actions"
    )
    recently_created: list[ActionListItemSchema] = Field(
        ..., description="Recently created actions"
    )


# Paginated Response Schemas
class ActionListResponse(PaginatedResponse):
    """Paginated action list response."""

    items: list[ActionListItemSchema] = Field(..., description="Action items")


class ActionParameterListResponse(BaseModel):
    """Action parameters list response."""

    action_id: UUID = Field(..., description="Action ID")
    parameters: list[ActionParameterSchema] = Field(
        ..., description="Action parameters"
    )
    total_parameters: int = Field(..., description="Total number of parameters")


class ActionOutputListResponse(BaseModel):
    """Action outputs list response."""

    action_id: UUID = Field(..., description="Action ID")
    outputs: list[ActionOutputSchema] = Field(..., description="Action outputs")
    total_outputs: int = Field(..., description="Total number of outputs")


# Action Template Schemas
class ActionTemplateSchema(BaseModel):
    """Schema for action templates."""

    template_name: str = Field(..., description="Template name")
    template_description: str = Field(..., description="Template description")
    action_template: ActionCreateSchema = Field(..., description="Action template data")
    parameter_placeholders: dict[str, Any] = Field(
        default_factory=dict, description="Parameter placeholders"
    )
    tags: list[str] = Field(default_factory=list, description="Template tags")
    erpnext_module: Optional[str] = Field(None, description="Target ERPNext module")


class ActionFromTemplateSchema(BaseModel):
    """Schema for creating action from template."""

    template_name: str = Field(..., description="Template to use")
    parameter_values: dict[str, Any] = Field(..., description="Parameter values")
    action_overrides: Optional[ActionUpdateSchema] = Field(
        None, description="Action-specific overrides"
    )
