"""Base Pydantic schemas for API validation and serialization.

This module provides foundational DTO (Data Transfer Object) classes
for API request/response validation, following the application layer
patterns in Domain-Driven Design architecture.
"""

from datetime import datetime
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import validator


# Generic type for paginated responses
T = TypeVar('T')


class BaseDTO(BaseModel):
    """Base Data Transfer Object for all API schemas.
    
    Provides common configuration and validation patterns
    for consistent API behavior across all endpoints.
    """
    
    model_config = ConfigDict(
        # Use enum values instead of names for better API compatibility
        use_enum_values=True,
        # Validate assignments to ensure data integrity
        validate_assignment=True,
        # Allow population by field name or alias
        populate_by_name=True,
        # Forbid extra fields to prevent injection
        extra='forbid',
        # Enable JSON schema generation
        json_schema_extra={
            "example": {
                "message": "Base DTO schema example"
            }
        }
    )


class EntityDTO(BaseDTO):
    """Base DTO for entity representations.
    
    Includes common entity fields that are typically
    exposed in API responses.
    """
    
    id: UUID = Field(description="Unique entity identifier")
    created_at: datetime = Field(description="Entity creation timestamp")
    updated_at: datetime = Field(description="Last modification timestamp")
    version: int = Field(description="Entity version for optimistic concurrency", ge=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2025-10-15T10:30:00Z",
                "updated_at": "2025-10-15T10:30:00Z",
                "version": 1
            }
        }
    )


class CreateDTO(BaseDTO):
    """Base DTO for entity creation requests.
    
    Excludes system-generated fields like ID and timestamps
    that should not be provided in creation requests.
    """
    
    pass


class UpdateDTO(BaseDTO):
    """Base DTO for entity update requests.
    
    Includes version field for optimistic concurrency control
    but excludes ID and timestamps.
    """
    
    version: int = Field(description="Current entity version for concurrency control", ge=1)
    
    @validator('version')
    def validate_version(cls, v: int) -> int:
        """Ensure version is positive for concurrency control."""
        if v < 1:
            raise ValueError("Version must be a positive integer")
        return v


class PaginationParams(BaseDTO):
    """Standard pagination parameters for list endpoints."""
    
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    
    @validator('limit')
    def validate_limit(cls, v: int) -> int:
        """Ensure reasonable pagination limits."""
        if v > 100:
            raise ValueError("Limit cannot exceed 100 items")
        return v


class PaginatedResponse(BaseDTO, Generic[T]):
    """Standard paginated response wrapper."""
    
    items: List[T] = Field(description="List of items for current page")
    total: int = Field(ge=0, description="Total number of items across all pages")
    limit: int = Field(ge=1, description="Maximum items per page")
    offset: int = Field(ge=0, description="Number of items skipped")
    has_next: bool = Field(description="Whether there are more pages available")
    has_prev: bool = Field(description="Whether there are previous pages available")
    
    @validator('has_next', pre=True, always=True)
    def calculate_has_next(cls, v: Any, values: Dict[str, Any]) -> bool:
        """Calculate if there are more pages."""
        if 'total' in values and 'offset' in values and 'limit' in values:
            return (values['offset'] + values['limit']) < values['total']
        return False
        
    @validator('has_prev', pre=True, always=True)  
    def calculate_has_prev(cls, v: Any, values: Dict[str, Any]) -> bool:
        """Calculate if there are previous pages."""
        if 'offset' in values:
            return values['offset'] > 0
        return False
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 42,
                "limit": 20,
                "offset": 0,
                "has_next": True,
                "has_prev": False
            }
        }
    )


class SortParams(BaseDTO):
    """Standard sorting parameters for list endpoints."""
    
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: str = Field(default="asc", regex="^(asc|desc)$", description="Sort order")
    
    @validator('sort_order')
    def validate_sort_order(cls, v: str) -> str:
        """Ensure sort order is valid."""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()


class FilterParams(BaseDTO):
    """Base class for filtering parameters."""
    
    search: Optional[str] = Field(default=None, max_length=100, description="Search term")
    
    @validator('search')
    def validate_search(cls, v: Optional[str]) -> Optional[str]:
        """Clean up search term."""
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Search term must be at least 2 characters")
        return v


class ErrorResponse(BaseDTO):
    """Standard error response format."""
    
    error: str = Field(description="Error type or code")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "The provided data is invalid",
                "details": {
                    "field": "email",
                    "issue": "Invalid email format"
                },
                "timestamp": "2025-10-15T10:30:00Z"
            }
        }
    )


class ValidationErrorDetail(BaseDTO):
    """Detailed validation error information."""
    
    field: str = Field(description="Field name that failed validation")
    message: str = Field(description="Validation error message")
    value: Optional[Any] = Field(default=None, description="Invalid value that was provided")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field details."""
    
    error: str = Field(default="ValidationError", description="Error type")
    validation_errors: List[ValidationErrorDetail] = Field(
        description="List of field validation errors"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Request validation failed",
                "validation_errors": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "value": "not-an-email"
                    }
                ],
                "timestamp": "2025-10-15T10:30:00Z"
            }
        }
    )


class SuccessResponse(BaseDTO):
    """Standard success response format."""
    
    message: str = Field(description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Optional response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully",
                "data": {"id": "123e4567-e89b-12d3-a456-426614174000"},
                "timestamp": "2025-10-15T10:30:00Z"
            }
        }
    )


class HealthResponse(BaseDTO):
    """Health check response format."""
    
    status: str = Field(description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(description="Application version")
    database: str = Field(description="Database connectivity status")
    redis: str = Field(description="Redis connectivity status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-15T10:30:00Z",
                "version": "1.0.0",
                "database": "connected",
                "redis": "connected"
            }
        }
    )


# Commonly used field validators
class CommonValidators:
    """Collection of reusable field validators."""
    
    @staticmethod
    @validator('name', pre=True, always=True)
    def validate_name(cls, v: str) -> str:
        """Standard name validation."""
        if not v or not v.strip():
            raise ValueError("Name is required and cannot be empty")
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters long")
        if len(v) > 100:
            raise ValueError("Name cannot exceed 100 characters")
        return v
        
    @staticmethod
    @validator('description', pre=True, always=True)
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Standard description validation."""
        if v is not None:
            v = v.strip()
            if len(v) > 1000:
                raise ValueError("Description cannot exceed 1000 characters")
        return v if v else None