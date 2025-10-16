"""Persona DTO schemas for API requests and responses.

Provides Pydantic models for persona data transfer objects
in the ERPNext Test Automation Meta-Framework.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator
from pydantic import ConfigDict

from .base_schemas import EntityDTO


class PersonaCreateRequest(BaseModel):
    """Schema for creating a new persona."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Unique name for the persona",
        examples=["Sales Manager", "Purchase User", "System Admin"]
    )
    
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Detailed description of the persona's purpose and responsibilities",
        examples=["Sales manager responsible for quotations, orders, and customer relationships"]
    )
    
    erpnext_roles: str = Field(
        ...,
        description="Comma-separated list of ERPNext roles",
        examples=["Sales Manager,Sales User,Employee"]
    )
    
    permissions: Optional[str] = Field(
        default="",
        max_length=1000,
        description="Comma-separated list of permissions (format: action:resource)",
        examples=["read:sales,write:sales,create:quotation"]
    )
    
    is_active: bool = Field(
        default=True,
        description="Whether the persona is active and available for use"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Validate persona name."""
        if not v or not v.strip():
            raise ValueError("Persona name is required")
        
        # Check for invalid characters
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError("Persona name can only contain letters, numbers, spaces, hyphens, and underscores")
        
        return v.strip()
    
    @validator('erpnext_roles')
    def validate_erpnext_roles(cls, v):
        """Validate ERPNext roles format."""
        if not v or not v.strip():
            raise ValueError("At least one ERPNext role is required")
        
        roles = [role.strip() for role in v.split(',') if role.strip()]
        if not roles:
            raise ValueError("At least one valid ERPNext role is required")
        
        return v.strip()
    
    @validator('permissions')
    def validate_permissions(cls, v):
        """Validate permissions format."""
        if not v:
            return ""
        
        v = v.strip()
        if not v:
            return ""
        
        permissions = [p.strip() for p in v.split(',') if p.strip()]
        
        for permission in permissions:
            if ':' not in permission:
                raise ValueError(f"Invalid permission format: '{permission}'. Use format 'action:resource'")
            
            parts = permission.split(':')
            if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
                raise ValueError(f"Invalid permission format: '{permission}'. Use format 'action:resource'")
            
            action = parts[0].strip()
            if action not in ['read', 'write', 'create', 'delete', 'admin']:
                raise ValueError(f"Invalid permission action: '{action}'. Valid actions: read, write, create, delete, admin")
        
        return v


class PersonaUpdateRequest(BaseModel):
    """Schema for updating an existing persona."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        description="Updated name for the persona"
    )
    
    description: Optional[str] = Field(
        None,
        min_length=10,
        max_length=2000,
        description="Updated description of the persona's purpose"
    )
    
    erpnext_roles: Optional[str] = Field(
        None,
        description="Updated comma-separated list of ERPNext roles"
    )
    
    permissions: Optional[str] = Field(
        None,
        max_length=1000,
        description="Updated comma-separated list of permissions"
    )
    
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status"
    )
    
    # Use same validators as create request
    _validate_name = validator('name', allow_reuse=True)(PersonaCreateRequest.validate_name)
    _validate_erpnext_roles = validator('erpnext_roles', allow_reuse=True)(PersonaCreateRequest.validate_erpnext_roles)
    _validate_permissions = validator('permissions', allow_reuse=True)(PersonaCreateRequest.validate_permissions)


class PersonaResponse(EntityDTO):
    """Schema for persona API responses."""
    
    name: str = Field(..., description="Persona name")
    description: str = Field(..., description="Persona description")
    erpnext_roles: str = Field(..., description="Comma-separated ERPNext roles")
    permissions: str = Field(..., description="Comma-separated permissions")
    is_active: bool = Field(..., description="Whether persona is active")
    
    # Computed fields
    erpnext_roles_list: List[str] = Field(
        ...,
        description="ERPNext roles as list",
        alias="erpnext_roles_list"
    )
    permissions_list: List[str] = Field(
        ..., 
        description="Permissions as list",
        alias="permissions_list"
    )
    effective_permissions_count: int = Field(
        ...,
        description="Total number of effective permissions including role-based",
        alias="effective_permissions_count"
    )
    
    @validator('erpnext_roles_list', pre=True, always=True)
    def compute_roles_list(cls, v, values):
        """Compute roles list from roles string."""
        roles_str = values.get('erpnext_roles', '')
        if not roles_str:
            return []
        return [role.strip() for role in roles_str.split(',') if role.strip()]
    
    @validator('permissions_list', pre=True, always=True)
    def compute_permissions_list(cls, v, values):
        """Compute permissions list from permissions string."""
        perms_str = values.get('permissions', '')
        if not perms_str:
            return []
        return [perm.strip() for perm in perms_str.split(',') if perm.strip()]
    
    @validator('effective_permissions_count', pre=True, always=True)
    def compute_effective_permissions_count(cls, v, values):
        """Compute effective permissions count."""
        # This would normally be computed by the domain entity
        # For now, just return the count of explicit permissions
        permissions_list = values.get('permissions_list', [])
        return len(permissions_list)


class PersonaListResponse(BaseModel):
    """Schema for persona list API responses."""
    
    items: List[PersonaResponse] = Field(..., description="List of personas")
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
        ...,
        max_length=200,
        description="Truncated persona description"
    )
    erpnext_roles_count: int = Field(
        ...,
        ge=0,
        description="Number of ERPNext roles"
    )
    permissions_count: int = Field(
        ...,
        ge=0,
        description="Number of explicit permissions"
    )
    is_active: bool = Field(..., description="Whether persona is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    @validator('description')
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
        default="",
        description="Comma-separated permissions"
    )


class PersonaValidationResponse(BaseModel):
    """Schema for persona validation responses."""
    
    is_valid: bool = Field(..., description="Whether persona data is valid")
    errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of validation warnings"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="List of improvement suggestions"
    )


class PersonaSuggestionRequest(BaseModel):
    """Schema for persona suggestion requests."""
    
    module: str = Field(
        ...,
        description="ERPNext module name",
        examples=["sales", "purchase", "stock", "accounts", "hr"]
    )
    user_level: str = Field(
        ...,
        description="User level",
        examples=["user", "manager", "admin"]
    )
    description_keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords to include in generated description",
        examples=[["experienced", "senior"], ["new", "trainee"]]
    )
    
    @validator('module')
    def validate_module(cls, v):
        """Validate ERPNext module name."""
        valid_modules = {
            'sales', 'purchase', 'stock', 'accounts', 'hr', 'projects',
            'manufacturing', 'quality', 'website', 'maintenance',
            'agriculture', 'healthcare', 'education', 'nonprofit'
        }
        
        if v.lower() not in valid_modules:
            raise ValueError(f"Invalid module: {v}. Valid modules: {', '.join(valid_modules)}")
        
        return v.lower()
    
    @validator('user_level')
    def validate_user_level(cls, v):
        """Validate user level."""
        valid_levels = {'user', 'manager', 'admin'}
        
        if v.lower() not in valid_levels:
            raise ValueError(f"Invalid user level: {v}. Valid levels: {', '.join(valid_levels)}")
        
        return v.lower()


class PersonaSuggestionResponse(BaseModel):
    """Schema for persona suggestion responses."""
    
    suggestions: List[PersonaCreateRequest] = Field(
        ...,
        description="List of suggested persona configurations"
    )
    module: str = Field(..., description="Module the suggestions are for")
    user_level: str = Field(..., description="User level the suggestions are for")


class PersonaSearchRequest(BaseModel):
    """Schema for persona search requests."""
    
    query: Optional[str] = Field(
        None,
        max_length=255,
        description="Search query for persona name or description"
    )
    erpnext_roles: Optional[List[str]] = Field(
        None,
        description="Filter by ERPNext roles"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Filter by active status"
    )
    has_permissions: Optional[List[str]] = Field(
        None,
        description="Filter by required permissions"
    )
    created_after: Optional[datetime] = Field(
        None,
        description="Filter by creation date"
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number"
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page"
    )
    sort_by: Optional[str] = Field(
        default="created_at",
        description="Sort field",
        examples=["name", "created_at", "updated_at"]
    )
    sort_order: Optional[str] = Field(
        default="desc",
        description="Sort order",
        examples=["asc", "desc"]
    )
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort field."""
        valid_fields = {'name', 'created_at', 'updated_at', 'is_active'}
        
        if v and v not in valid_fields:
            raise ValueError(f"Invalid sort field: {v}. Valid fields: {', '.join(valid_fields)}")
        
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort order."""
        valid_orders = {'asc', 'desc'}
        
        if v and v.lower() not in valid_orders:
            raise ValueError(f"Invalid sort order: {v}. Valid orders: {', '.join(valid_orders)}")
        
        return v.lower() if v else v


class PersonaStatsResponse(BaseModel):
    """Schema for persona statistics."""
    
    total_personas: int = Field(..., ge=0, description="Total number of personas")
    active_personas: int = Field(..., ge=0, description="Number of active personas")
    inactive_personas: int = Field(..., ge=0, description="Number of inactive personas")
    roles_distribution: dict = Field(
        ...,
        description="Distribution of ERPNext roles across personas"
    )
    permissions_distribution: dict = Field(
        ...,
        description="Distribution of permissions across personas"
    )
    creation_trend: List[dict] = Field(
        ...,
        description="Persona creation trend over time"
    )
    complexity_metrics: dict = Field(
        ...,
        description="Complexity metrics for personas"
    )