"""Persona DTO schemas for API requests and responses.

Provides Pydantic models for persona data transfer objects
in the ERPNext Test Automation Meta-Framework.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, computed_field

from .base_schemas import EntityDTO


class PersonaCreateRequest(BaseModel):
    """Schema for creating a new persona."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, use_enum_values=True
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Unique name for the persona",
        examples=["Sales Manager", "Purchase User", "System Admin"],
    )

    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Detailed description of the persona's purpose and responsibilities",
        examples=[
            "Sales manager responsible for quotations, orders, and customer relationships"
        ],
    )

    erpnext_roles: str = Field(
        ...,
        description="Comma-separated list of ERPNext roles",
        examples=["Sales Manager,Sales User,Employee"],
    )

    permissions: Optional[str] = Field(
        default="",
        max_length=1000,
        description="Comma-separated list of permissions (format: action:resource)",
        examples=["read:sales,write:sales,create:quotation"],
    )

    is_active: bool = Field(
        default=True, description="Whether the persona is active and available for use"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate persona name."""
        if not v or not v.strip():
            raise ValueError("Persona name is required")

        # Check for invalid characters
        import re

        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", v):
            raise ValueError(
                "Persona name can only contain letters, numbers, spaces, hyphens, and underscores"
            )

        return v.strip()

    @field_validator("erpnext_roles")
    @classmethod
    def validate_erpnext_roles(cls, v):
        """Validate ERPNext roles format."""
        if not v or not v.strip():
            raise ValueError("At least one ERPNext role is required")

        roles = [role.strip() for role in v.split(",") if role.strip()]
        if not roles:
            raise ValueError("At least one valid ERPNext role is required")

        return v.strip()

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v):
        """Validate permissions format."""
        if not v:
            return ""

        v = v.strip()
        if not v:
            return ""

        permissions = [p.strip() for p in v.split(",") if p.strip()]

        for permission in permissions:
            if ":" not in permission:
                raise ValueError(
                    f"Invalid permission format: '{permission}'. Use format 'action:resource'"
                )

            parts = permission.split(":")
            if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
                raise ValueError(
                    f"Invalid permission format: '{permission}'. Use format 'action:resource'"
                )

            action = parts[0].strip()
            if action not in ["read", "write", "create", "delete", "admin"]:
                raise ValueError(
                    f"Invalid permission action: '{action}'. Valid actions: read, write, create, delete, admin"
                )

        return v


class PersonaUpdateRequest(BaseModel):
    """Schema for updating an existing persona."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, use_enum_values=True
    )

    name: Optional[str] = Field(
        None, min_length=2, max_length=255, description="Updated name for the persona"
    )

    description: Optional[str] = Field(
        None,
        min_length=10,
        max_length=2000,
        description="Updated description of the persona's purpose",
    )

    erpnext_roles: Optional[str] = Field(
        None, description="Updated comma-separated list of ERPNext roles"
    )

    permissions: Optional[str] = Field(
        None, max_length=1000, description="Updated comma-separated list of permissions"
    )

    is_active: Optional[bool] = Field(None, description="Updated active status")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate persona name."""
        if v is None:
            return v
        return PersonaCreateRequest.validate_name(v)

    @field_validator("erpnext_roles")
    @classmethod
    def validate_erpnext_roles(cls, v):
        """Validate ERPNext roles format."""
        if v is None:
            return v
        return PersonaCreateRequest.validate_erpnext_roles(v)

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v):
        """Validate permissions format."""
        if v is None:
            return v
        return PersonaCreateRequest.validate_permissions(v)


class PersonaResponse(EntityDTO):
    """Schema for persona API responses."""

    name: str = Field(..., description="Persona name")
    description: str = Field(..., description="Persona description")
    erpnext_roles: str = Field(..., description="Comma-separated ERPNext roles")
    permissions: str = Field(..., description="Comma-separated permissions")
    is_active: bool = Field(..., description="Whether persona is active")

    # Computed fields
    erpnext_roles_list: list[str] = Field(
        ..., description="ERPNext roles as list"
    )
    permissions_list: list[str] = Field(
        ..., description="Permissions as list"
    )
    effective_permissions_count: int = Field(
        ...,
        description="Total number of effective permissions including role-based",
    )


class PersonaListResponse(BaseModel):
    """Schema for persona list API responses."""

    items: list[PersonaResponse] = Field(..., description="List of personas")
    total: int = Field(..., ge=0, description="Total number of personas")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class PersonaSummaryResponse(BaseModel):
    """Schema for persona summary information."""

    id: UUID = Field(..., description="Persona unique identifier")
    name: str = Field(..., description="Persona name")
    description: str = Field(
        ..., max_length=200, description="Truncated persona description"
    )
    erpnext_roles_count: int = Field(..., ge=0, description="Number of ERPNext roles")
    permissions_count: int = Field(
        ..., ge=0, description="Number of explicit permissions"
    )
    is_active: bool = Field(..., description="Whether persona is active")
    created_at: datetime = Field(..., description="Creation timestamp")

    @field_validator("description")
    @classmethod
    def truncate_description(cls, v):
        """Truncate description for summary."""
        if len(v) > 200:
            return v[:197] + "..."
        return v


class PersonaValidationRequest(BaseModel):
    """Schema for persona validation requests."""

    name: str = Field(..., description="Persona name to validate")
    erpnext_roles: str = Field(..., description="Comma-separated ERPNext roles")
    permissions: Optional[str] = Field(
        default="", description="Comma-separated permissions"
    )


class PersonaValidationResponse(BaseModel):
    """Schema for persona validation responses."""

    is_valid: bool = Field(..., description="Whether persona data is valid")
    errors: list[str] = Field(
        default_factory=list, description="List of validation errors"
    )
    warnings: list[str] = Field(
        default_factory=list, description="List of validation warnings"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="List of improvement suggestions"
    )


class PersonaSuggestionRequest(BaseModel):
    """Schema for persona suggestion requests."""

    module: str = Field(
        ...,
        description="ERPNext module name",
        examples=["sales", "purchase", "stock", "accounts", "hr"],
    )
    user_level: str = Field(
        ..., description="User level", examples=["user", "manager", "admin"]
    )
    description_keywords: Optional[list[str]] = Field(
        default=None,
        description="Keywords to include in generated description",
        examples=[["experienced", "senior"], ["new", "trainee"]],
    )

    @field_validator("module")
    @classmethod
    def validate_module(cls, v):
        """Validate ERPNext module name."""
        valid_modules = {
            "sales",
            "purchase",
            "stock",
            "accounts",
            "hr",
            "projects",
            "manufacturing",
            "quality",
            "website",
            "maintenance",
            "agriculture",
            "healthcare",
            "education",
            "nonprofit",
        }

        if v.lower() not in valid_modules:
            raise ValueError(
                f"Invalid module: {v}. Valid modules: {', '.join(valid_modules)}"
            )

        return v.lower()

    @field_validator("user_level")
    @classmethod
    def validate_user_level(cls, v):
        """Validate user level."""
        valid_levels = {"user", "manager", "admin"}

        if v.lower() not in valid_levels:
            raise ValueError(
                f"Invalid user level: {v}. Valid levels: {', '.join(valid_levels)}"
            )

        return v.lower()


class PersonaSuggestionResponse(BaseModel):
    """Schema for persona suggestion responses."""

    suggestions: list[PersonaCreateRequest] = Field(
        ..., description="List of suggested persona configurations"
    )
    module: str = Field(..., description="Module the suggestions are for")
    user_level: str = Field(..., description="User level the suggestions are for")


class PersonaSearchRequest(BaseModel):
    """Schema for persona search requests."""

    query: Optional[str] = Field(
        None, max_length=255, description="Search query for persona name or description"
    )
    erpnext_roles: Optional[list[str]] = Field(
        None, description="Filter by ERPNext roles"
    )
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    has_permissions: Optional[list[str]] = Field(
        None, description="Filter by required permissions"
    )
    created_after: Optional[datetime] = Field(
        None, description="Filter by creation date"
    )
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page"
    )
    sort_by: Optional[str] = Field(
        default="created_at",
        description="Sort field",
        examples=["name", "created_at", "updated_at"],
    )
    sort_order: Optional[str] = Field(
        default="desc", description="Sort order", examples=["asc", "desc"]
    )

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v):
        """Validate sort field."""
        valid_fields = {"name", "created_at", "updated_at", "is_active"}

        if v and v not in valid_fields:
            raise ValueError(
                f"Invalid sort field: {v}. Valid fields: {', '.join(valid_fields)}"
            )

        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v):
        """Validate sort order."""
        valid_orders = {"asc", "desc"}

        if v and v.lower() not in valid_orders:
            raise ValueError(
                f"Invalid sort order: {v}. Valid orders: {', '.join(valid_orders)}"
            )

        return v.lower() if v else v


class PersonaStatsResponse(BaseModel):
    """Schema for persona statistics."""

    total_personas: int = Field(..., ge=0, description="Total number of personas")
    active_personas: int = Field(..., ge=0, description="Number of active personas")
    inactive_personas: int = Field(..., ge=0, description="Number of inactive personas")
    roles_distribution: dict = Field(
        ..., description="Distribution of ERPNext roles across personas"
    )
    permissions_distribution: dict = Field(
        ..., description="Distribution of permissions across personas"
    )
    creation_trend: list[dict] = Field(
        ..., description="Persona creation trend over time"
    )
    complexity_metrics: dict = Field(..., description="Complexity metrics for personas")
