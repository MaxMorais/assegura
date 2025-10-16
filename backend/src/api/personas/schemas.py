"""API schemas and documentation for persona endpoints.

Provides OpenAPI documentation, examples, and response models
for comprehensive API documentation generation.
"""

from typing import Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field

from ...application.dto.persona_schemas import (
    PersonaCreateRequest,
    PersonaUpdateRequest, 
    PersonaResponse,
    PersonaListResponse,
    PersonaSummaryResponse
)


class PersonaAPIExamples:
    """Example data for API documentation."""
    
    # Example persona creation request
    CREATE_PERSONA_REQUEST = {
        "name": "Sales Manager",
        "description": "A sales manager responsible for managing sales orders, quotations, and customer relationships",
        "erpnext_roles": "Sales Manager, Customer, Item Manager",
        "permissions": "read_sales_order,write_sales_order,read_quotation,write_quotation",
        "is_active": True
    }
    
    # Example persona response
    PERSONA_RESPONSE = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Sales Manager", 
        "description": "A sales manager responsible for managing sales orders, quotations, and customer relationships",
        "erpnext_roles": "Sales Manager, Customer, Item Manager",
        "permissions": "read_sales_order,write_sales_order,read_quotation,write_quotation",
        "is_active": True,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "version": 1,
        "erpnext_roles_list": ["Sales Manager", "Customer", "Item Manager"],
        "permissions_list": ["read_sales_order", "write_sales_order", "read_quotation", "write_quotation"],
        "effective_permissions_count": 15
    }
    
    # Example persona list response
    PERSONA_LIST_RESPONSE = {
        "personas": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Sales Manager",
                "description": "A sales manager responsible for managing sales orders",
                "erpnext_roles": "Sales Manager, Customer",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": "987fcdeb-51d2-43a8-b456-426614174001", 
                "name": "Purchase Manager",
                "description": "A purchase manager handling procurement and vendor management",
                "erpnext_roles": "Purchase Manager, Supplier",
                "is_active": True,
                "created_at": "2024-01-15T11:00:00Z",
                "updated_at": "2024-01-15T11:00:00Z"
            }
        ],
        "total": 2,
        "limit": 50,
        "offset": 0,
        "has_more": False
    }
    
    # Example persona summary
    PERSONA_SUMMARY = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Sales Manager",
        "description": "A sales manager responsible for managing sales orders",
        "erpnext_roles_count": 3,
        "permissions_count": 4,
        "is_active": True,
        "activities_count": 5,
        "last_used": "2024-01-14T15:30:00Z"
    }
    
    # Example validation response
    VALIDATION_RESPONSE = {
        "is_valid": True,
        "errors": [],
        "warnings": [
            {
                "field": "erpnext_roles",
                "message": "Role 'Custom Role' is not a standard ERPNext role",
                "code": "non_standard_role"
            }
        ],
        "suggestions": [
            {
                "field": "permissions",
                "message": "Consider adding 'read_customer' permission for Sales Manager role",
                "suggested_value": "read_customer"
            }
        ]
    }
    
    # Example suggestion request and response
    SUGGESTION_REQUEST = {
        "context": "I need a persona for managing inventory and stock movements",
        "erpnext_modules": ["Stock", "Item"],
        "business_process": "inventory_management"
    }
    
    SUGGESTION_RESPONSE = {
        "suggestions": [
            {
                "name": "Stock Manager",
                "description": "Manages inventory levels, stock movements, and warehouse operations",
                "erpnext_roles": ["Stock Manager", "Stock User", "Item Manager"],
                "permissions": ["read_stock_entry", "write_stock_entry", "read_item", "write_item"],
                "confidence": 0.95,
                "reasoning": "Based on inventory management context and Stock/Item modules"
            },
            {
                "name": "Warehouse Supervisor", 
                "description": "Supervises warehouse operations and stock reconciliation",
                "erpnext_roles": ["Stock User", "Warehouse User"],
                "permissions": ["read_stock_reconciliation", "write_stock_reconciliation"],
                "confidence": 0.87,
                "reasoning": "Alternative for warehouse-focused inventory management"
            }
        ],
        "total_suggestions": 2
    }
    
    # Example statistics response
    STATISTICS_RESPONSE = {
        "total_personas": 15,
        "active_personas": 12,
        "inactive_personas": 3,
        "total_activities": 47,
        "personas_by_module": {
            "Sales": 5,
            "Purchase": 3,
            "Stock": 4,
            "Accounts": 2,
            "HR": 1
        },
        "most_used_roles": [
            {"role": "Sales Manager", "count": 4},
            {"role": "Purchase Manager", "count": 3},
            {"role": "Stock Manager", "count": 3}
        ],
        "recent_activity": {
            "personas_created_last_week": 2,
            "personas_updated_last_week": 5,
            "most_recently_used": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Sales Manager",
                "last_used": "2024-01-14T15:30:00Z"
            }
        }
    }


class PersonaAPIDocumentation:
    """OpenAPI documentation components for persona endpoints."""
    
    # Tags for grouping endpoints
    TAGS_METADATA = [
        {
            "name": "personas",
            "description": "Operations for managing test personas. Personas represent different user types with specific ERPNext roles and permissions.",
            "externalDocs": {
                "description": "Persona Domain Documentation",
                "url": "/docs/personas"
            }
        }
    ]
    
    # Common responses
    COMMON_RESPONSES = {
        400: {
            "description": "Bad Request - Validation errors or business rule violations",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"},
                            "errors": {"type": "array", "items": {"type": "object"}}
                        }
                    },
                    "example": {
                        "detail": "Persona with name 'Sales Manager' already exists"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object", 
                        "properties": {
                            "detail": {"type": "string"}
                        }
                    },
                    "example": {
                        "detail": "Could not validate credentials"
                    }
                }
            }
        },
        403: {
            "description": "Forbidden - Insufficient permissions",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"}
                        }
                    },
                    "example": {
                        "detail": "Not enough permissions to access this resource"
                    }
                }
            }
        },
        404: {
            "description": "Not Found - Persona does not exist or is not accessible",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"}
                        }
                    },
                    "example": {
                        "detail": "Persona 123e4567-e89b-12d3-a456-426614174000 not found"
                    }
                }
            }
        },
        409: {
            "description": "Conflict - Resource conflict (e.g., cannot delete persona with associated activities)",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"}
                        }
                    },
                    "example": {
                        "detail": "Cannot delete persona with associated activities"
                    }
                }
            }
        },
        422: {
            "description": "Unprocessable Entity - Validation errors",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "object"},
                            "errors": {"type": "array"}
                        }
                    },
                    "example": {
                        "detail": {
                            "errors": [
                                {
                                    "field": "erpnext_roles",
                                    "message": "Invalid ERPNext role: 'InvalidRole'",
                                    "code": "invalid_role"
                                }
                            ]
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - Unexpected server error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {"type": "string"}
                        }
                    },
                    "example": {
                        "detail": "An unexpected error occurred"
                    }
                }
            }
        }
    }
    
    # Endpoint-specific documentation
    ENDPOINT_DOCS = {
        "create_persona": {
            "summary": "Create new persona",
            "description": """
            Create a new test persona with ERPNext roles and permissions.
            
            Personas represent different user types that will be used in test scenarios.
            Each persona must have a unique name within the consultant's workspace and
            at least one valid ERPNext role.
            
            **Key Features:**
            - Automatic validation of ERPNext roles and permissions
            - Duplicate name detection
            - Rich permission modeling with inheritance from roles
            - Comprehensive audit trail
            
            **Business Rules:**
            - Persona name must be unique per consultant
            - At least one ERPNext role is required
            - Permissions are validated against ERPNext schema
            - Inactive personas can be created but not used in tests
            """,
            "response_description": "The created persona with generated ID, timestamps, and computed fields"
        },
        
        "list_personas": {
            "summary": "List personas with filtering and pagination", 
            "description": """
            Retrieve a paginated list of personas for the authenticated consultant
            with comprehensive filtering options.
            
            **Filtering Options:**
            - **search**: Full-text search in names and descriptions
            - **is_active**: Filter by active/inactive status
            - **erpnext_role**: Filter by specific ERPNext role
            
            **Sorting:**
            - Default: Recently updated first
            - Supports sorting by name, creation date, update date
            
            **Pagination:**
            - Limit: 1-100 results per page (default: 50)
            - Offset-based pagination with total count
            - `has_more` indicator for efficient UI pagination
            """,
            "response_description": "Paginated list of personas with metadata and filtering results"
        },
        
        "get_persona": {
            "summary": "Get detailed persona information",
            "description": """
            Retrieve complete information for a specific persona including
            computed fields and relationship data.
            
            **Included Data:**
            - Basic persona information (name, description, roles)
            - Effective permissions (computed from roles and explicit permissions)
            - Usage statistics (activities count, last used)
            - Audit information (creation/update timestamps, version)
            
            **Security:**
            - Only personas owned by the authenticated consultant are accessible
            - Cross-tenant isolation enforced
            """,
            "response_description": "Complete persona information with computed fields"
        },
        
        "update_persona": {
            "summary": "Update existing persona",
            "description": """
            Update an existing persona with partial or complete data changes.
            
            **Update Behavior:**
            - Partial updates supported (only provide fields to change)
            - Name uniqueness validated against other personas
            - Role and permission changes validated
            - Version-based optimistic locking prevents conflicts
            
            **Audit Trail:**
            - All changes tracked with timestamps
            - Version number incremented on each update
            - Previous values logged for compliance
            """,
            "response_description": "Updated persona with new timestamps and version number"
        },
        
        "delete_persona": {
            "summary": "Delete persona and associated data",
            "description": """
            Permanently delete a persona and all associated data.
            
            **Deletion Rules:**
            - Cannot delete personas with associated activities (returns 409)
            - Soft delete option available for audit compliance
            - All associated test data is also removed
            
            **Safety Measures:**
            - Confirmation required for personas with historical usage
            - Backup recommendations for production environments
            - Cascade deletion warnings
            """,
            "response_description": "No content returned on successful deletion"
        }
    }


class PersonaAPISchemas:
    """Additional schema definitions for API documentation."""
    
    class ErrorDetail(BaseModel):
        """Standard error response structure."""
        detail: str = Field(..., description="Human-readable error message")
        code: str = Field(None, description="Machine-readable error code")
        field: str = Field(None, description="Field name for validation errors")
        
    class ValidationError(BaseModel):
        """Validation error response."""
        detail: str = Field(..., description="Error message")
        errors: List['PersonaAPISchemas.ErrorDetail'] = Field(default=[], description="Detailed validation errors")
        
    class HealthResponse(BaseModel):
        """Health check response."""
        status: str = Field(..., description="Service health status")
        service: str = Field(..., description="Service name")
        version: str = Field(..., description="API version")
        timestamp: str = Field(..., description="Response timestamp")


# Export documentation components
__all__ = [
    "PersonaAPIExamples",
    "PersonaAPIDocumentation", 
    "PersonaAPISchemas"
]