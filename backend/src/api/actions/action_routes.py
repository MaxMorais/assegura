"""
Action Library REST API Endpoints

This module provides comprehensive REST API endpoints for action library management
in the ERPNext test automation framework. Handles CRUD operations, validation,
complexity scoring, usage analytics, and action classification.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from ...application.dto.action_schemas import (
    ActionBulkOperationSchema,
    ActionBulkResultSchema,
    ActionComplexityScoreSchema,
    ActionCreateSchema,
    ActionFilterSchema,
    ActionFromTemplateSchema,
    ActionListItemSchema,
    ActionPatternSchema,
    ActionResponseSchema,
    ActionSortSchema,
    ActionSuggestionSchema,
    ActionTemplateSchema,
    ActionUpdateSchema,
    ActionUsageStatsSchema,
    ActionValidationResultSchema,
)
from ...application.dto.base_schemas import PaginatedResponse
from ...application.services.action_service import ActionLibraryService
from ...domain.actions.action_library import ActionType, ImplementationType
from ...infrastructure.database import get_sync_db
from ...infrastructure.database.repositories.action_repository import (
    SQLAlchemyActionRepository,
)

# Create router for action library endpoints
router = APIRouter(prefix="/actions", tags=["actions"])


def get_service(db: Session = Depends(get_sync_db)):
    """Dependency to get action library service."""
    action_repo = SQLAlchemyActionRepository(db)
    return ActionLibraryService(action_repo)


@router.post(
    "/",
    response_model=ActionResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create new action",
    description="Create a new action with parameters and outputs",
)
async def create_action(
    action_data: ActionCreateSchema,
    service: ActionLibraryService = Depends(get_service),
) -> ActionResponseSchema:
    """Create a new action."""
    try:
        return await service.create_action(action_data)
    except Exception as e:
        if "validation" in str(e).lower() or "already exists" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create action: {str(e)}",
        )


@router.get(
    "/{action_id}",
    response_model=ActionResponseSchema,
    summary="Get action by ID",
    description="Retrieve action details including parameters and outputs",
)
async def get_action(
    action_id: uuid.UUID = Path(..., description="Action ID"),
    service: ActionLibraryService = Depends(get_service),
) -> ActionResponseSchema:
    """Get action by ID."""
    try:
        return await service.get_action(action_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action with ID {action_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve action: {str(e)}",
        )


@router.get(
    "/",
    response_model=PaginatedResponse[ActionListItemSchema],
    summary="List actions",
    description="List actions with filtering, sorting, and pagination",
)
async def list_actions(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of actions"),
    offset: int = Query(0, ge=0, description="Number of actions to skip"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    implementation_type: Optional[str] = Query(
        None, description="Filter by implementation type"
    ),
    erpnext_module: Optional[str] = Query(None, description="Filter by ERPNext module"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    name_contains: Optional[str] = Query(
        None, description="Filter by name containing text"
    ),
    description_contains: Optional[str] = Query(
        None, description="Filter by description containing text"
    ),
    tags: Optional[list[str]] = Query(None, description="Filter by tags"),
    sort_by: Optional[str] = Query("updated_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    service: ActionLibraryService = Depends(get_service),
) -> PaginatedResponse[ActionListItemSchema]:
    """List actions with filtering and pagination."""

    # Build filters
    filters = ActionFilterSchema(
        action_type=ActionType(action_type) if action_type else None,
        implementation_type=ImplementationType(implementation_type)
        if implementation_type
        else None,
        erpnext_module=erpnext_module,
        is_active=is_active,
        name_contains=name_contains,
        description_contains=description_contains,
        tags=tags,
    )

    # Build sorting
    sort = ActionSortSchema(sort_by=sort_by, sort_order=sort_order)

    try:
        return await service.list_actions(
            filters=filters, sort=sort, limit=limit, offset=offset
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list actions: {str(e)}",
        )


@router.put(
    "/{action_id}",
    response_model=ActionResponseSchema,
    summary="Update action",
    description="Update action details and properties",
)
async def update_action(
    action_id: uuid.UUID = Path(..., description="Action ID"),
    update_data: ActionUpdateSchema = None,
    service: ActionLibraryService = Depends(get_service),
) -> ActionResponseSchema:
    """Update action."""
    try:
        return await service.update_action(action_id, update_data)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action with ID {action_id} not found",
            )
        elif "validation" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update action: {str(e)}",
        )


@router.delete(
    "/{action_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete action",
    description="Delete action from library",
)
async def delete_action(
    action_id: uuid.UUID = Path(..., description="Action ID"),
    service: ActionLibraryService = Depends(get_service),
):
    """Delete action."""
    try:
        success = await service.delete_action(action_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action with ID {action_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete action: {str(e)}",
        )


# Action Validation and Analysis


@router.post(
    "/{action_id}/validate",
    response_model=ActionValidationResultSchema,
    summary="Validate action",
    description="Perform comprehensive action validation",
)
async def validate_action(
    action_id: uuid.UUID = Path(..., description="Action ID"),
    service: ActionLibraryService = Depends(get_service),
) -> ActionValidationResultSchema:
    """Validate action."""
    try:
        return await service.validate_action(action_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action with ID {action_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate action: {str(e)}",
        )


@router.get(
    "/{action_id}/complexity-score",
    response_model=ActionComplexityScoreSchema,
    summary="Get complexity score",
    description="Calculate action complexity score and breakdown",
)
async def get_action_complexity_score(
    action_id: uuid.UUID = Path(..., description="Action ID"),
    service: ActionLibraryService = Depends(get_service),
) -> ActionComplexityScoreSchema:
    """Get action complexity score."""
    try:
        return await service.get_action_complexity_score(action_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action with ID {action_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get complexity score: {str(e)}",
        )


@router.get(
    "/{action_id}/usage-stats",
    response_model=ActionUsageStatsSchema,
    summary="Get usage statistics",
    description="Retrieve action usage and performance statistics",
)
async def get_action_usage_stats(
    action_id: uuid.UUID = Path(..., description="Action ID"),
    service: ActionLibraryService = Depends(get_service),
) -> ActionUsageStatsSchema:
    """Get action usage statistics."""
    try:
        return await service.get_action_usage_stats(action_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action with ID {action_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage statistics: {str(e)}",
        )


# Module-based Operations


@router.get(
    "/by-module/{erpnext_module}",
    response_model=list[ActionResponseSchema],
    summary="Get actions by module",
    description="Retrieve all actions for specific ERPNext module",
)
async def get_actions_by_module(
    erpnext_module: str = Path(..., description="ERPNext module name"),
    service: ActionLibraryService = Depends(get_service),
) -> list[ActionResponseSchema]:
    """Get actions for specific ERPNext module."""
    try:
        return await service.get_actions_by_module(erpnext_module)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve actions for module: {str(e)}",
        )


# Action Discovery and Suggestions


@router.post(
    "/suggestions",
    response_model=list[ActionSuggestionSchema],
    summary="Get action suggestions",
    description="Get action suggestions based on criteria and patterns",
)
async def get_action_suggestions(
    criteria: ActionPatternSchema,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
    service: ActionLibraryService = Depends(get_service),
) -> list[ActionSuggestionSchema]:
    """Get action suggestions based on criteria."""
    try:
        suggestions = await service.suggest_similar_actions(criteria)
        return suggestions[:limit] if suggestions else []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get action suggestions: {str(e)}",
        )


# Bulk Operations


@router.post(
    "/bulk",
    response_model=ActionBulkResultSchema,
    summary="Bulk action operations",
    description="Perform bulk operations on multiple actions",
)
async def bulk_action_operation(
    operation_data: ActionBulkOperationSchema,
    service: ActionLibraryService = Depends(get_service),
) -> ActionBulkResultSchema:
    """Perform bulk operations on actions."""
    try:
        return await service.bulk_operation(operation_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk operation: {str(e)}",
        )


# Template Management


@router.post(
    "/templates",
    summary="Create action template",
    description="Create reusable action template",
)
async def create_action_template(
    template_data: ActionTemplateSchema,
    service: ActionLibraryService = Depends(get_service),
):
    """Create action template."""
    try:
        template_name = await service.create_action_template(template_data)
        return {
            "template_name": template_name,
            "message": "Template created successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}",
        )


@router.post(
    "/from-template",
    response_model=ActionResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create action from template",
    description="Create new action from existing template",
)
async def create_action_from_template(
    template_request: ActionFromTemplateSchema,
    service: ActionLibraryService = Depends(get_service),
) -> ActionResponseSchema:
    """Create action from template."""
    try:
        return await service.create_action_from_template(template_request)
    except Exception as e:
        if "template" in str(e).lower() and "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "validation" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create action from template: {str(e)}",
        )


# Action Type and Classification Utilities


@router.get(
    "/types",
    summary="Get action types",
    description="Retrieve available action types and their descriptions",
)
async def get_action_types():
    """Get available action types."""
    return {
        "action_types": [
            {
                "value": action_type.value,
                "name": action_type.name,
                "description": f"{action_type.value.replace('_', ' ').title()} action type",
            }
            for action_type in ActionType
        ]
    }


@router.get(
    "/implementation-types",
    summary="Get implementation types",
    description="Retrieve available implementation types and their descriptions",
)
async def get_implementation_types():
    """Get available implementation types."""
    return {
        "implementation_types": [
            {
                "value": impl_type.value,
                "name": impl_type.name,
                "description": f"{impl_type.value.replace('_', ' ').title()} implementation",
            }
            for impl_type in ImplementationType
        ]
    }


# Health and Status


@router.get(
    "/health",
    summary="Action library health check",
    description="Check action library system health and statistics",
)
async def action_library_health(service: ActionLibraryService = Depends(get_service)):
    """Get action library health status."""
    try:
        # Get basic statistics from repository
        stats = await service.action_repository.get_usage_statistics()

        return {
            "status": "healthy",
            "statistics": stats,
            "message": "Action library is functioning normally",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}",
        )
