"""
Journey DTO Schemas for API Requests and Responses

This module defines comprehensive Pydantic schemas for Journey-related
API operations, ensuring proper data validation, serialization, and
documentation for the ERPNext test automation framework.
"""

from typing import List, Optional, Dict, Any, Union, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator

from src.application.dto.base_schemas import BaseResponseSchema, PaginatedResponse
from src.domain.journeys.enhanced_journey import JourneyExecutionStatus, JourneyComplexityLevel
from src.domain.actions.action_library import ActionType, ImplementationType


class JourneyStatusEnum(str, Enum):
    """Journey status for API responses."""
    
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class ComplexityLevelEnum(str, Enum):
    """Journey complexity levels."""
    
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex" 
    ADVANCED = "advanced"


class ActionTypeEnum(str, Enum):
    """Action types for journey steps."""
    
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


# Base Journey Schemas
class JourneyBaseSchema(BaseModel):
    """Base schema for journey data."""
    
    name: str = Field(..., min_length=3, max_length=200, description="Journey name")
    description: str = Field(..., min_length=10, max_length=1000, description="Journey description")
    is_active: bool = Field(default=True, description="Whether journey is active")
    estimated_duration_minutes: Optional[int] = Field(
        None, ge=1, le=1440, description="Expected execution time in minutes"
    )
    complexity_level: ComplexityLevelEnum = Field(
        default=ComplexityLevelEnum.MEDIUM, description="Journey complexity level"
    )
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites for execution")
    expected_outcomes: List[str] = Field(default_factory=list, description="Expected results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate journey name."""
        if not v.strip():
            raise ValueError('Journey name cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        """Validate journey description."""
        if not v.strip():
            raise ValueError('Journey description cannot be empty')
        return v.strip()
    
    @validator('prerequisites')
    def validate_prerequisites(cls, v):
        """Validate prerequisites list."""
        return [item.strip() for item in v if item.strip()]
    
    @validator('expected_outcomes')
    def validate_expected_outcomes(cls, v):
        """Validate expected outcomes list."""
        return [item.strip() for item in v if item.strip()]


class ActionStepSchema(BaseModel):
    """Schema for individual journey steps."""
    
    step_number: int = Field(..., ge=1, description="Step number in sequence")
    action_id: UUID = Field(..., description="Referenced action ID")
    action_name: str = Field(..., description="Action display name")
    action_type: ActionTypeEnum = Field(..., description="Action BDD type")
    step_description: Optional[str] = Field(None, description="Custom step description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Step parameters")
    expected_outputs: Dict[str, Any] = Field(default_factory=dict, description="Expected outputs")
    
    # Step execution configuration
    timeout_override: Optional[int] = Field(
        None, ge=1, le=3600, description="Override timeout in seconds"
    )
    retry_override: Optional[int] = Field(
        None, ge=0, le=10, description="Override retry count"
    )
    depends_on_steps: Optional[List[int]] = Field(
        None, description="Steps this step depends on"
    )
    can_run_parallel: bool = Field(
        default=False, description="Whether step can run in parallel"
    )
    is_critical: bool = Field(
        default=False, description="Whether step is critical for journey success"
    )
    
    @validator('depends_on_steps')
    def validate_dependencies(cls, v, values):
        """Validate step dependencies."""
        if v is not None:
            step_number = values.get('step_number')
            if step_number is not None:
                # Dependencies must be on earlier steps
                invalid_deps = [dep for dep in v if dep >= step_number]
                if invalid_deps:
                    raise ValueError(f'Dependencies must be on earlier steps: {invalid_deps}')
        return v


class JourneyStepCreateSchema(ActionStepSchema):
    """Schema for creating new journey steps."""
    
    # Remove step_number as it's assigned automatically
    step_number: Optional[int] = Field(None, description="Optional position for step")


class JourneyStepUpdateSchema(BaseModel):
    """Schema for updating existing journey steps."""
    
    step_description: Optional[str] = Field(None, description="Updated step description")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Updated parameters")
    expected_outputs: Optional[Dict[str, Any]] = Field(None, description="Updated expected outputs")
    timeout_override: Optional[int] = Field(None, ge=1, le=3600, description="Updated timeout")
    retry_override: Optional[int] = Field(None, ge=0, le=10, description="Updated retry count")
    can_run_parallel: Optional[bool] = Field(None, description="Updated parallel flag")
    is_critical: Optional[bool] = Field(None, description="Updated critical flag")


# Journey Request Schemas
class JourneyCreateSchema(JourneyBaseSchema):
    """Schema for creating new journeys."""
    
    persona_id: UUID = Field(..., description="Associated persona ID")
    activity_id: UUID = Field(..., description="Associated activity ID")
    steps: Optional[List[JourneyStepCreateSchema]] = Field(
        default_factory=list, description="Initial journey steps"
    )


class JourneyUpdateSchema(BaseModel):
    """Schema for updating existing journeys."""
    
    name: Optional[str] = Field(None, min_length=3, max_length=200, description="Updated name")
    description: Optional[str] = Field(None, min_length=10, max_length=1000, description="Updated description")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    estimated_duration_minutes: Optional[int] = Field(
        None, ge=1, le=1440, description="Updated estimated duration"
    )
    complexity_level: Optional[ComplexityLevelEnum] = Field(None, description="Updated complexity")
    prerequisites: Optional[List[str]] = Field(None, description="Updated prerequisites")
    expected_outcomes: Optional[List[str]] = Field(None, description="Updated expected outcomes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate journey name."""
        if v is not None and not v.strip():
            raise ValueError('Journey name cannot be empty')
        return v.strip() if v else v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate journey description."""
        if v is not None and not v.strip():
            raise ValueError('Journey description cannot be empty')
        return v.strip() if v else v


class JourneyAssociationUpdateSchema(BaseModel):
    """Schema for updating journey associations."""
    
    persona_id: Optional[UUID] = Field(None, description="New persona ID")
    activity_id: Optional[UUID] = Field(None, description="New activity ID")


# Journey Response Schemas
class JourneyExecutionPlanSchema(BaseModel):
    """Schema for journey execution plan."""
    
    total_steps: int = Field(..., description="Total number of steps")
    estimated_duration_seconds: float = Field(..., description="Estimated duration in seconds")
    complexity_score: int = Field(..., description="Overall complexity score")
    can_parallelize: bool = Field(..., description="Whether journey can use parallel execution")
    parallel_sections: List[Tuple[int, int]] = Field(
        default_factory=list, description="Parallelizable step ranges"
    )
    critical_path: List[int] = Field(default_factory=list, description="Critical path step numbers")
    rollback_points: List[int] = Field(default_factory=list, description="Rollback point step numbers")
    resource_requirements: List[str] = Field(
        default_factory=list, description="Required resources"
    )


class ActionsSummarySchema(BaseModel):
    """Schema for journey actions summary."""
    
    total_steps: int = Field(..., description="Total number of steps")
    action_types: Dict[str, int] = Field(..., description="Count by action type")
    erpnext_modules: List[str] = Field(..., description="ERPNext modules involved")
    implementation_types: List[str] = Field(..., description="Implementation types used")
    has_complete_bdd_flow: bool = Field(..., description="Whether journey has Given/When/Then")


class JourneyResponseSchema(JourneyBaseSchema, BaseResponseSchema):
    """Schema for journey API responses."""
    
    persona_id: UUID = Field(..., description="Associated persona ID")
    activity_id: UUID = Field(..., description="Associated activity ID")
    execution_status: JourneyStatusEnum = Field(..., description="Current execution status")
    steps: List[ActionStepSchema] = Field(..., description="Journey steps")
    
    # Computed properties
    step_count: int = Field(..., description="Total number of steps")
    has_given_steps: bool = Field(..., description="Whether journey has Given steps")
    has_when_steps: bool = Field(..., description="Whether journey has When steps") 
    has_then_steps: bool = Field(..., description="Whether journey has Then steps")
    is_complete_scenario: bool = Field(..., description="Whether journey is complete BDD scenario")
    
    # Optional detailed information
    execution_plan: Optional[JourneyExecutionPlanSchema] = Field(
        None, description="Execution plan details"
    )
    actions_summary: Optional[ActionsSummarySchema] = Field(
        None, description="Actions summary"
    )
    validation_errors: Optional[List[str]] = Field(
        None, description="Current validation errors"
    )


class JourneyListItemSchema(BaseModel):
    """Schema for journey list items."""
    
    id: UUID = Field(..., description="Journey ID")
    name: str = Field(..., description="Journey name")
    description: str = Field(..., description="Journey description")
    persona_id: UUID = Field(..., description="Associated persona ID")
    activity_id: UUID = Field(..., description="Associated activity ID")
    execution_status: JourneyStatusEnum = Field(..., description="Execution status")
    complexity_level: ComplexityLevelEnum = Field(..., description="Complexity level")
    step_count: int = Field(..., description="Number of steps")
    estimated_duration_minutes: Optional[int] = Field(None, description="Estimated duration")
    is_active: bool = Field(..., description="Whether journey is active")
    is_complete_scenario: bool = Field(..., description="Whether journey is complete")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# Journey Validation Schemas
class ValidationResultSchema(BaseModel):
    """Schema for validation results."""
    
    rule_name: str = Field(..., description="Validation rule name")
    severity: str = Field(..., description="Validation severity (error/warning/info)")
    message: str = Field(..., description="Validation message")
    affected_steps: List[int] = Field(default_factory=list, description="Affected step numbers")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix")
    is_blocking: bool = Field(..., description="Whether this blocks execution")


class JourneyValidationSchema(BaseModel):
    """Schema for journey validation results."""
    
    can_execute: bool = Field(..., description="Whether journey can be executed")
    error_count: int = Field(..., description="Number of errors")
    warning_count: int = Field(..., description="Number of warnings")
    info_count: int = Field(..., description="Number of info messages")
    total_issues: int = Field(..., description="Total issues found")
    results: List[ValidationResultSchema] = Field(..., description="Detailed results")


# Journey Execution Schemas
class StepExecutionResultSchema(BaseModel):
    """Schema for step execution results."""
    
    step_number: int = Field(..., description="Step number")
    action_id: UUID = Field(..., description="Action ID")
    status: str = Field(..., description="Execution status")
    start_time: Optional[datetime] = Field(None, description="Execution start time")
    end_time: Optional[datetime] = Field(None, description="Execution end time")
    duration_seconds: Optional[float] = Field(None, description="Execution duration")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Step outputs")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retries performed")


class JourneyExecutionResultSchema(BaseModel):
    """Schema for complete journey execution results."""
    
    journey_id: UUID = Field(..., description="Journey ID")
    execution_id: UUID = Field(..., description="Execution instance ID")
    status: JourneyStatusEnum = Field(..., description="Overall execution status")
    start_time: datetime = Field(..., description="Execution start time")
    end_time: Optional[datetime] = Field(None, description="Execution end time")
    duration_seconds: Optional[float] = Field(None, description="Total duration")
    steps_executed: List[StepExecutionResultSchema] = Field(..., description="Step results")
    success_count: int = Field(..., description="Number of successful steps")
    failure_count: int = Field(..., description="Number of failed steps")
    skipped_count: int = Field(..., description="Number of skipped steps")


# Journey Search and Filtering
class JourneyFilterSchema(BaseModel):
    """Schema for journey filtering parameters."""
    
    persona_id: Optional[UUID] = Field(None, description="Filter by persona")
    activity_id: Optional[UUID] = Field(None, description="Filter by activity") 
    execution_status: Optional[JourneyStatusEnum] = Field(None, description="Filter by status")
    complexity_level: Optional[ComplexityLevelEnum] = Field(None, description="Filter by complexity")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    has_complete_bdd: Optional[bool] = Field(None, description="Filter by BDD completeness")
    min_steps: Optional[int] = Field(None, ge=0, description="Minimum number of steps")
    max_steps: Optional[int] = Field(None, ge=0, description="Maximum number of steps")
    erpnext_modules: Optional[List[str]] = Field(None, description="Filter by ERPNext modules")
    tags: Optional[List[str]] = Field(None, description="Filter by tags in metadata")
    text_search: Optional[str] = Field(None, description="Text search in name/description")


class JourneySortSchema(BaseModel):
    """Schema for journey sorting parameters."""
    
    sort_by: str = Field(
        default="created_at", 
        description="Field to sort by",
        regex="^(name|created_at|updated_at|step_count|complexity_level|estimated_duration_minutes)$"
    )
    sort_order: str = Field(
        default="desc",
        description="Sort order",
        regex="^(asc|desc)$"
    )


# Journey Statistics Schemas
class JourneyStatsSchema(BaseModel):
    """Schema for journey statistics."""
    
    total_journeys: int = Field(..., description="Total number of journeys")
    active_journeys: int = Field(..., description="Number of active journeys")
    draft_journeys: int = Field(..., description="Number of draft journeys")
    ready_journeys: int = Field(..., description="Number of ready journeys")
    avg_steps_per_journey: float = Field(..., description="Average steps per journey")
    complexity_distribution: Dict[str, int] = Field(..., description="Distribution by complexity")
    most_used_modules: List[Tuple[str, int]] = Field(..., description="Most used ERPNext modules")
    recent_executions: int = Field(..., description="Recent execution count")


# Paginated Response Schemas
class JourneyListResponse(PaginatedResponse):
    """Paginated journey list response."""
    
    items: List[JourneyListItemSchema] = Field(..., description="Journey items")


class JourneyStepListResponse(BaseModel):
    """Journey steps list response."""
    
    journey_id: UUID = Field(..., description="Journey ID")
    steps: List[ActionStepSchema] = Field(..., description="Journey steps")
    total_steps: int = Field(..., description="Total number of steps")


# Bulk Operations Schemas
class JourneyBulkOperationSchema(BaseModel):
    """Schema for bulk journey operations."""
    
    journey_ids: List[UUID] = Field(..., min_items=1, max_items=100, description="Journey IDs")
    operation: str = Field(..., regex="^(activate|deactivate|delete|execute)$", description="Operation")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")


class JourneyBulkResultSchema(BaseModel):
    """Schema for bulk operation results."""
    
    successful_ids: List[UUID] = Field(..., description="Successfully processed IDs")
    failed_ids: List[UUID] = Field(..., description="Failed to process IDs")
    errors: Dict[str, str] = Field(..., description="Errors by journey ID")
    total_processed: int = Field(..., description="Total journeys processed")


# Journey Templates Schemas
class JourneyTemplateSchema(BaseModel):
    """Schema for journey templates."""
    
    template_name: str = Field(..., description="Template name")
    template_description: str = Field(..., description="Template description")
    journey_template: JourneyCreateSchema = Field(..., description="Journey template data")
    parameter_placeholders: Dict[str, Any] = Field(
        default_factory=dict, description="Parameter placeholders"
    )
    tags: List[str] = Field(default_factory=list, description="Template tags")


class JourneyFromTemplateSchema(BaseModel):
    """Schema for creating journey from template."""
    
    template_name: str = Field(..., description="Template to use")
    parameter_values: Dict[str, Any] = Field(..., description="Parameter values")
    journey_overrides: Optional[JourneyUpdateSchema] = Field(
        None, description="Journey-specific overrides"
    )