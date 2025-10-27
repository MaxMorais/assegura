"""Activity DTO schemas for API requests and responses.

This module defines all data transfer objects (DTOs) used for activity-related
API endpoints, including request/response schemas with validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ActivityActionTypeDTO(str, Enum):
    """Activity action types for API."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    REPORT = "report"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    CANCEL = "cancel"
    SUBMIT = "submit"
    DUPLICATE = "duplicate"
    PRINT = "print"
    EMAIL = "email"


class ActivityComplexityDTO(int, Enum):
    """Activity complexity levels for API."""

    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


class ActivityPriorityDTO(str, Enum):
    """Activity priority levels for persona relationships."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Request DTOs


class ActivityCreateRequestDTO(BaseModel):
    """Request DTO for creating an activity."""

    name: str = Field(..., min_length=3, max_length=100, description="Activity name")
    description: str = Field("", max_length=500, description="Activity description")
    erpnext_module: str = Field(..., min_length=2, description="ERPNext module name")
    action_type: ActivityActionTypeDTO = Field(
        ..., description="Type of action to perform"
    )
    target_doctype: str = Field(..., min_length=2, description="Target ERPNext DocType")
    required_fields: list[str] = Field(
        default_factory=list, description="Required fields for execution"
    )
    validation_rules: dict[str, Any] = Field(
        default_factory=dict, description="Validation rules for fields"
    )
    success_criteria: list[str] = Field(
        default_factory=list, description="Success criteria for completion"
    )
    complexity_score: int = Field(1, ge=1, le=5, description="Complexity score (1-5)")
    estimated_duration: int = Field(
        60, ge=1, description="Estimated duration in seconds"
    )
    prerequisites: list[str] = Field(
        default_factory=list, description="Activity prerequisites"
    )
    postconditions: list[str] = Field(
        default_factory=list, description="Activity postconditions"
    )
    test_data_requirements: dict[str, Any] = Field(
        default_factory=dict, description="Test data requirements"
    )
    tags: list[str] = Field(default_factory=list, description="Activity tags")
    is_active: bool = Field(True, description="Whether activity is active")

    @classmethod
    @field_validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()

    @classmethod
    @field_validator("required_fields")
    def validate_required_fields(cls, v):
        if v and len(v) > 20:
            raise ValueError("Cannot have more than 20 required fields")
        return [field.strip() for field in v if field.strip()]

    @classmethod
    @field_validator("success_criteria")
    def validate_success_criteria(cls, v):
        if v and len(v) > 10:
            raise ValueError("Cannot have more than 10 success criteria")
        return [criteria.strip() for criteria in v if criteria.strip()]

    @classmethod
    @field_validator("tags")
    def validate_tags(cls, v):
        if v and len(v) > 10:
            raise ValueError("Cannot have more than 10 tags")
        return [tag.strip().lower() for tag in v if tag.strip()]

    class Config:
        schema_extra = {
            "example": {
                "name": "Create Sales Order",
                "description": "Create a new sales order in ERPNext",
                "erpnext_module": "Sales",
                "action_type": "create",
                "target_doctype": "Sales Order",
                "required_fields": ["customer", "items"],
                "validation_rules": {
                    "customer": {"required": True},
                    "items": {"array_min": 1},
                },
                "success_criteria": ["order_created", "customer_notified"],
                "complexity_score": 4,
                "estimated_duration": 300,
                "prerequisites": ["setup_customer"],
                "postconditions": ["order_exists"],
                "test_data_requirements": {
                    "customer": "valid_customer_id",
                    "items": "item_list",
                },
                "tags": ["sales", "order", "create"],
                "is_active": True,
            }
        }


class ActivityUpdateRequestDTO(BaseModel):
    """Request DTO for updating an activity."""

    name: Optional[str] = Field(
        None, min_length=3, max_length=100, description="Activity name"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Activity description"
    )
    complexity_score: Optional[int] = Field(
        None, ge=1, le=5, description="Complexity score (1-5)"
    )
    estimated_duration: Optional[int] = Field(
        None, ge=1, description="Estimated duration in seconds"
    )
    prerequisites: Optional[list[str]] = Field(
        None, description="Activity prerequisites"
    )
    postconditions: Optional[list[str]] = Field(
        None, description="Activity postconditions"
    )
    test_data_requirements: Optional[dict[str, Any]] = Field(
        None, description="Test data requirements"
    )
    tags: Optional[list[str]] = Field(None, description="Activity tags")
    is_active: Optional[bool] = Field(None, description="Whether activity is active")

    @classmethod
    @field_validator("name")
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip() if v else v

    @classmethod
    @field_validator("tags")
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError("Cannot have more than 10 tags")
            return [tag.strip().lower() for tag in v if tag.strip()]
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Sales Order Creation",
                "description": "Updated description for creating sales orders",
                "complexity_score": 5,
                "estimated_duration": 420,
                "tags": ["sales", "order", "updated"],
            }
        }


class ActivityFilterDTO(BaseModel):
    """DTO for filtering activities."""

    erpnext_module: Optional[str] = Field(None, description="Filter by ERPNext module")
    action_type: Optional[ActivityActionTypeDTO] = Field(
        None, description="Filter by action type"
    )
    target_doctype: Optional[str] = Field(None, description="Filter by target DocType")
    complexity_score: Optional[int] = Field(
        None, ge=1, le=5, description="Filter by complexity score"
    )
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    tags: Optional[list[str]] = Field(None, description="Filter by tags (OR logic)")
    min_duration: Optional[int] = Field(
        None, ge=0, description="Minimum duration in seconds"
    )
    max_duration: Optional[int] = Field(
        None, ge=0, description="Maximum duration in seconds"
    )
    search: Optional[str] = Field(
        None, max_length=100, description="Search in name and description"
    )

    @classmethod
    @field_validator("max_duration")
    def validate_duration_range(cls, v, values):
        if v is not None and values.get("min_duration") is not None:
            if v < values["min_duration"]:
                raise ValueError(
                    "max_duration must be greater than or equal to min_duration"
                )
        return v


# Response DTOs


class ActivityResponseDTO(BaseModel):
    """Response DTO for activity data."""

    id: str = Field(..., description="Activity unique identifier")
    name: str = Field(..., description="Activity name")
    description: str = Field(..., description="Activity description")
    erpnext_module: str = Field(..., description="ERPNext module name")
    action_type: str = Field(..., description="Type of action to perform")
    target_doctype: str = Field(..., description="Target ERPNext DocType")
    required_fields: list[str] = Field(..., description="Required fields for execution")
    validation_rules: dict[str, Any] = Field(
        ..., description="Validation rules for fields"
    )
    success_criteria: list[str] = Field(
        ..., description="Success criteria for completion"
    )
    complexity_score: int = Field(..., description="Complexity score (1-5)")
    estimated_duration: int = Field(..., description="Estimated duration in seconds")
    prerequisites: list[str] = Field(..., description="Activity prerequisites")
    postconditions: list[str] = Field(..., description="Activity postconditions")
    test_data_requirements: dict[str, Any] = Field(
        ..., description="Test data requirements"
    )
    tags: list[str] = Field(..., description="Activity tags")
    is_active: bool = Field(..., description="Whether activity is active")
    version: int = Field(..., description="Activity version")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Create Sales Order",
                "description": "Create a new sales order in ERPNext",
                "erpnext_module": "Sales",
                "action_type": "create",
                "target_doctype": "Sales Order",
                "required_fields": ["customer", "items"],
                "validation_rules": {
                    "customer": {"required": True},
                    "items": {"array_min": 1},
                },
                "success_criteria": ["order_created", "customer_notified"],
                "complexity_score": 4,
                "estimated_duration": 300,
                "prerequisites": ["setup_customer"],
                "postconditions": ["order_exists"],
                "test_data_requirements": {
                    "customer": "valid_customer_id",
                    "items": "item_list",
                },
                "tags": ["sales", "order", "create"],
                "is_active": True,
                "version": 1,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }


class ActivityListResponseDTO(BaseModel):
    """Response DTO for paginated activity lists."""

    activities: list[ActivityResponseDTO] = Field(..., description="List of activities")
    total: int = Field(..., ge=0, description="Total number of activities")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")

    class Config:
        schema_extra = {
            "example": {
                "activities": [],  # Would contain ActivityResponseDTO objects
                "total": 25,
                "page": 1,
                "per_page": 10,
                "has_next": True,
                "has_prev": False,
            }
        }


class ActivityStatisticsResponseDTO(BaseModel):
    """Response DTO for activity statistics."""

    total: int = Field(..., ge=0, description="Total number of activities")
    active: int = Field(..., ge=0, description="Number of active activities")
    inactive: int = Field(..., ge=0, description="Number of inactive activities")
    by_module: dict[str, int] = Field(
        ..., description="Activities count by ERPNext module"
    )
    by_action_type: dict[str, int] = Field(
        ..., description="Activities count by action type"
    )
    complexity_distribution: dict[int, int] = Field(
        ..., description="Activities count by complexity score"
    )
    avg_duration: float = Field(..., ge=0, description="Average estimated duration")
    total_duration: int = Field(..., ge=0, description="Total estimated duration")
    avg_complexity: float = Field(
        ..., ge=0, le=5, description="Average complexity score"
    )
    most_common_module: str = Field(..., description="Most frequently used module")
    most_common_action: str = Field(..., description="Most frequently used action type")

    class Config:
        schema_extra = {
            "example": {
                "total": 50,
                "active": 45,
                "inactive": 5,
                "by_module": {
                    "Sales": 15,
                    "CRM": 10,
                    "Stock": 8,
                    "Accounts": 12,
                    "HR": 5,
                },
                "by_action_type": {"create": 20, "read": 15, "update": 10, "delete": 5},
                "complexity_distribution": {1: 5, 2: 10, 3: 20, 4: 12, 5: 3},
                "avg_duration": 185.5,
                "total_duration": 9275,
                "avg_complexity": 2.8,
                "most_common_module": "Sales",
                "most_common_action": "create",
            }
        }


# Activity-Persona Link DTOs


class ActivityPersonaLinkCreateRequestDTO(BaseModel):
    """Request DTO for creating activity-persona links."""

    priority: ActivityPriorityDTO = Field(
        ActivityPriorityDTO.MEDIUM, description="Link priority"
    )
    notes: str = Field("", max_length=500, description="Notes about the relationship")
    is_primary: bool = Field(
        False, description="Whether this is a primary activity for the persona"
    )
    execution_order: int = Field(0, ge=0, description="Execution order in workflow")

    class Config:
        schema_extra = {
            "example": {
                "priority": "high",
                "notes": "Critical activity for sales operations",
                "is_primary": True,
                "execution_order": 1,
            }
        }


class ActivityPersonaLinkUpdateRequestDTO(BaseModel):
    """Request DTO for updating activity-persona links."""

    priority: Optional[ActivityPriorityDTO] = Field(None, description="Link priority")
    notes: Optional[str] = Field(
        None, max_length=500, description="Notes about the relationship"
    )
    is_primary: Optional[bool] = Field(
        None, description="Whether this is a primary activity for the persona"
    )
    execution_order: Optional[int] = Field(
        None, ge=0, description="Execution order in workflow"
    )

    class Config:
        schema_extra = {
            "example": {
                "priority": "medium",
                "notes": "Updated notes for the relationship",
                "execution_order": 2,
            }
        }


class ActivityPersonaLinkResponseDTO(BaseModel):
    """Response DTO for activity-persona links."""

    persona_id: str = Field(..., description="Persona ID")
    activity_id: str = Field(..., description="Activity ID")
    priority: str = Field(..., description="Link priority")
    notes: str = Field(..., description="Notes about the relationship")
    is_primary: bool = Field(
        ..., description="Whether this is a primary activity for the persona"
    )
    execution_order: int = Field(..., description="Execution order in workflow")
    created_at: datetime = Field(..., description="Link creation timestamp")
    updated_at: datetime = Field(..., description="Link last update timestamp")

    class Config:
        schema_extra = {
            "example": {
                "persona_id": "123e4567-e89b-12d3-a456-426614174001",
                "activity_id": "123e4567-e89b-12d3-a456-426614174002",
                "priority": "high",
                "notes": "Critical activity for sales operations",
                "is_primary": True,
                "execution_order": 1,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }


class PersonaActivityResponseDTO(BaseModel):
    """Response DTO for persona activities with link metadata."""

    activity: ActivityResponseDTO = Field(..., description="Activity data")
    link: ActivityPersonaLinkResponseDTO = Field(..., description="Link metadata")

    class Config:
        schema_extra = {
            "example": {
                "activity": {},  # ActivityResponseDTO example
                "link": {},  # ActivityPersonaLinkResponseDTO example
            }
        }


class ActivityPersonaResponseDTO(BaseModel):
    """Response DTO for activity personas with link metadata (reverse relationship)."""

    persona: dict[str, Any] = Field(
        ..., description="Persona data"
    )  # PersonaResponseDTO would be imported
    link: ActivityPersonaLinkResponseDTO = Field(..., description="Link metadata")


# Compatibility and Suggestion DTOs


class ActivityCompatibilityResponseDTO(BaseModel):
    """Response DTO for activity compatibility check."""

    is_compatible: bool = Field(..., description="Whether activities are compatible")
    compatibility_score: float = Field(
        ..., ge=0, le=1, description="Compatibility score (0-1)"
    )
    reasons: list[str] = Field(
        ..., description="Reasons for compatibility/incompatibility"
    )
    suggestions: list[str] = Field(..., description="Suggestions for improvement")
    confidence: float = Field(
        ..., ge=0, le=1, description="Confidence in the assessment"
    )

    class Config:
        schema_extra = {
            "example": {
                "is_compatible": True,
                "compatibility_score": 0.85,
                "reasons": [
                    "Both activities operate in the same ERPNext module",
                    "Activities have compatible action types",
                ],
                "suggestions": [
                    "These activities work very well together in workflows"
                ],
                "confidence": 0.9,
            }
        }


class ActivitySuggestionResponseDTO(BaseModel):
    """Response DTO for activity suggestions."""

    name: str = Field(..., description="Suggested activity name")
    description: str = Field(..., description="Suggested activity description")
    erpnext_module: str = Field(..., description="Suggested ERPNext module")
    action_type: str = Field(..., description="Suggested action type")
    target_doctype: str = Field(..., description="Suggested target DocType")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in suggestion")
    required_fields: list[str] = Field(..., description="Suggested required fields")
    complexity_score: int = Field(
        ..., ge=1, le=5, description="Suggested complexity score"
    )
    estimated_duration: int = Field(
        ..., ge=1, description="Suggested duration in seconds"
    )

    class Config:
        schema_extra = {
            "example": {
                "name": "Create Customer",
                "description": "Create a new customer record in ERPNext CRM module",
                "erpnext_module": "CRM",
                "action_type": "create",
                "target_doctype": "Customer",
                "confidence": 0.9,
                "required_fields": ["customer_name", "customer_type"],
                "complexity_score": 2,
                "estimated_duration": 120,
            }
        }


# Bulk Operation DTOs


class ActivityBulkOperationRequestDTO(BaseModel):
    """Request DTO for bulk operations on activities."""

    activity_ids: list[str] = Field(
        ..., min_length=1, max_length=50, description="List of activity IDs"
    )
    action: str = Field(..., description="Bulk action to perform")

    @classmethod
    @field_validator("action")
    def validate_action(cls, v):
        valid_actions = ["activate", "deactivate", "delete", "export"]
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {", ".join(valid_actions)}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "activity_ids": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "123e4567-e89b-12d3-a456-426614174002",
                ],
                "action": "activate",
            }
        }


class ActivityBulkOperationResponseDTO(BaseModel):
    """Response DTO for bulk operations results."""

    updated_count: int = Field(..., ge=0, description="Number of activities updated")
    updated_ids: list[str] = Field(..., description="List of updated activity IDs")
    failed_count: int = Field(..., ge=0, description="Number of failed operations")
    failed_ids: list[str] = Field(..., description="List of failed activity IDs")
    errors: list[str] = Field(..., description="List of error messages")

    class Config:
        schema_extra = {
            "example": {
                "updated_count": 2,
                "updated_ids": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "123e4567-e89b-12d3-a456-426614174002",
                ],
                "failed_count": 0,
                "failed_ids": [],
                "errors": [],
            }
        }


class ActivityBulkLinkRequestDTO(BaseModel):
    """Request DTO for bulk linking activities to personas."""

    activity_ids: list[str] = Field(
        ..., min_length=1, max_length=20, description="List of activity IDs to link"
    )
    priority: ActivityPriorityDTO = Field(
        ActivityPriorityDTO.MEDIUM, description="Link priority for all activities"
    )
    notes: str = Field("", max_length=500, description="Notes for all links")

    class Config:
        schema_extra = {
            "example": {
                "activity_ids": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "123e4567-e89b-12d3-a456-426614174002",
                ],
                "priority": "medium",
                "notes": "Bulk linked activities for testing",
            }
        }


class ActivityBulkLinkResponseDTO(BaseModel):
    """Response DTO for bulk linking results."""

    linked_count: int = Field(..., ge=0, description="Number of activities linked")
    linked_activities: list[str] = Field(..., description="List of linked activity IDs")
    failed_count: int = Field(..., ge=0, description="Number of failed links")
    failed_activities: list[str] = Field(..., description="List of failed activity IDs")
    errors: list[str] = Field(..., description="List of error messages")

    class Config:
        schema_extra = {
            "example": {
                "linked_count": 2,
                "linked_activities": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "123e4567-e89b-12d3-a456-426614174002",
                ],
                "failed_count": 0,
                "failed_activities": [],
                "errors": [],
            }
        }
