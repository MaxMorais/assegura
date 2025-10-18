"""FastAPI endpoints for activity management.

This module provides REST API endpoints for managing ERPNext business activities
including CRUD operations, filtering, and activity-persona relationships.
"""

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.application.dto.activity_schemas import (
    ActivityBulkOperationRequestDTO,
    ActivityCreateRequestDTO,
    ActivityFilterDTO,
    ActivityListResponseDTO,
    ActivityPersonaLinkCreateRequestDTO,
    ActivityPersonaLinkResponseDTO,
    ActivityResponseDTO,
    ActivityUpdateRequestDTO,
)
from src.application.services.activity_service import ActivityApplicationService
from src.domain.activities.exceptions import (
    ActivityAlreadyExistsError,
    ActivityNotFoundError,
    ActivityPersonaLinkAlreadyExistsError,
    ActivityPersonaLinkNotFoundError,
    ActivityValidationError,
)
from src.infrastructure.database import get_sync_db
from src.infrastructure.database.repositories.activity_repository import (
    SQLAlchemyActivityPersonaLinkRepository,
    SQLAlchemyActivityRepository,
)
from src.infrastructure.database.repositories.persona_repository import (
    SQLAlchemyPersonaRepository,
)

# Create router
router = APIRouter(prefix="/activities", tags=["activities"])


def get_activity_service(db: Session = Depends(get_sync_db)) -> ActivityApplicationService:
    """Dependency to get activity application service."""
    activity_repo = SQLAlchemyActivityRepository(db)
    persona_repo = SQLAlchemyPersonaRepository(db)
    link_repo = SQLAlchemyActivityPersonaLinkRepository(db)
    return ActivityApplicationService(activity_repo, persona_repo, link_repo)


@router.post(
    "/",
    response_model=ActivityResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create new activity",
    description="Create a new business activity with validation.",
)
async def create_activity(
    request: ActivityCreateRequestDTO,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> ActivityResponseDTO:
    """Create a new activity."""
    try:
        activity = await service.create_activity(request)
        return activity
    except ActivityAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Activity already exists: {str(e)}",
        )
    except ActivityValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/{activity_id}",
    response_model=ActivityResponseDTO,
    summary="Get activity by ID",
    description="Retrieve a specific activity by its unique identifier.",
)
async def get_activity(
    activity_id: uuid.UUID,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> ActivityResponseDTO:
    """Get an activity by ID."""
    try:
        activity = await service.get_activity_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found",
            )
        return activity
    except ActivityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with ID {activity_id} not found",
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/",
    response_model=ActivityListResponseDTO,
    summary="List activities with filtering",
    description="Retrieve activities with optional filtering, search, and pagination",
)
async def list_activities(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    erpnext_module: Optional[str] = Query(None, description="Filter by ERPNext module"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    target_doctype: Optional[str] = Query(None, description="Filter by target DocType"),
    complexity_score: Optional[int] = Query(
        None, ge=1, le=5, description="Filter by complexity score"
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    min_duration: Optional[int] = Query(
        None, ge=0, description="Minimum estimated duration"
    ),
    max_duration: Optional[int] = Query(
        None, ge=0, description="Maximum estimated duration"
    ),
    service: ActivityApplicationService = Depends(get_activity_service),
) -> ActivityListResponseDTO:
    """List activities with filtering and pagination."""
    try:
        # Build filter request
        filters = ActivityFilterDTO(
            erpnext_module=erpnext_module,
            action_type=action_type,
            target_doctype=target_doctype,
            complexity_score=complexity_score,
            is_active=is_active,
            search=search,
            tags_any=[tag.strip() for tag in tags.split(",")] if tags else None,
            min_duration=min_duration,
            max_duration=max_duration,
        )

        result = await service.list_activities(filters, page, per_page)
        return result
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.put(
    "/{activity_id}",
    response_model=ActivityResponseDTO,
    summary="Update activity",
    description="Update an existing activity with new data and validation",
)
async def update_activity(
    activity_id: uuid.UUID,
    request: ActivityUpdateRequestDTO,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> ActivityResponseDTO:
    """Update an activity."""
    try:
        activity = await service.update_activity(activity_id, request)
        return activity
    except ActivityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with ID {activity_id} not found",
        )
    except ActivityValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.delete(
    "/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete activity",
    description="Delete an activity and all its relationships",
)
async def delete_activity(
    activity_id: uuid.UUID,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> None:
    """Delete an activity."""
    try:
        await service.delete_activity(activity_id)
    except ActivityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with ID {activity_id} not found",
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post(
    "/search",
    response_model=ActivityListResponseDTO,
    summary="Search activities",
    description="Advanced search for activities with multiple criteria",
)
async def search_activities(
    request: ActivityFilterDTO,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> ActivityListResponseDTO:
    """Search activities with advanced criteria."""
    try:
        result = await service.search_activities(request)
        return result
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/modules/{module_name}",
    response_model=list[ActivityResponseDTO],
    summary="Get activities by module",
    description="Retrieve all activities for a specific ERPNext module",
)
async def get_activities_by_module(
    module_name: str,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> list[ActivityResponseDTO]:
    """Get activities by ERPNext module."""
    try:
        activities = await service.get_activities_by_module(module_name)
        return activities
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/doctypes/{doctype_name}",
    response_model=list[ActivityResponseDTO],
    summary="Get activities by DocType",
    description="Retrieve all activities targeting a specific DocType",
)
async def get_activities_by_doctype(
    doctype_name: str,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> list[ActivityResponseDTO]:
    """Get activities by target DocType."""
    try:
        activities = await service.get_activities_by_doctype(doctype_name)
        return activities
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/statistics",
    response_model=dict[str, Any],
    summary="Get activity statistics",
    description="Retrieve comprehensive statistics about activities",
)
async def get_activity_statistics(
    service: ActivityApplicationService = Depends(get_activity_service),
) -> dict[str, Any]:
    """Get activity statistics."""
    try:
        stats = await service.get_activity_statistics()
        return stats
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post(
    "/bulk/update-status",
    response_model=dict[str, int],
    summary="Bulk update activity status",
    description="Update the active/inactive status of multiple activities",
)
async def bulk_update_activity_status(
    request: ActivityBulkOperationRequestDTO,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> dict[str, int]:
    """Bulk update activity status."""
    try:
        result = await service.bulk_activity_operation(request)
        return {"updated_count": result.updated_count}
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.delete(
    "/bulk",
    response_model=dict[str, int],
    summary="Bulk delete activities",
    description="Delete multiple activities at once",
)
async def bulk_delete_activities(
    activity_ids: list[uuid.UUID],
    service: ActivityApplicationService = Depends(get_activity_service),
) -> dict[str, int]:
    """Bulk delete activities."""
    try:
        count = await service.bulk_delete_activities(activity_ids)
        return {"deleted_count": count}
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


# Activity-Persona Link endpoints
@router.post(
    "/{activity_id}/personas",
    response_model=ActivityPersonaLinkResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Link activity to persona",
    description="Create a relationship between an activity and a persona",
)
async def link_activity_to_persona(
    activity_id: uuid.UUID,
    request: ActivityPersonaLinkCreateRequestDTO,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> ActivityPersonaLinkResponseDTO:
    """Link an activity to a persona."""
    try:
        # Set activity_id from URL parameter
        request.activity_id = activity_id
        link = await service.create_activity_persona_link(request)
        return link
    except ActivityPersonaLinkAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Activity {activity_id} is already linked to persona {request.persona_id}",
        )
    except ActivityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with ID {activity_id} not found",
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/{activity_id}/personas",
    response_model=list[ActivityPersonaLinkResponseDTO],
    summary="Get activity personas",
    description="Retrieve all personas linked to an activity",
)
async def get_activity_personas(
    activity_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service: ActivityApplicationService = Depends(get_activity_service),
) -> list[ActivityPersonaLinkResponseDTO]:
    """Get personas linked to an activity."""
    try:
        links = await service.get_activity_personas(activity_id, page, per_page)
        return links
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.delete(
    "/{activity_id}/personas/{persona_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink activity from persona",
    description="Remove the relationship between an activity and a persona",
)
async def unlink_activity_from_persona(
    activity_id: uuid.UUID,
    persona_id: uuid.UUID,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> None:
    """Unlink an activity from a persona."""
    try:
        await service.delete_activity_persona_link(persona_id, activity_id)
    except ActivityPersonaLinkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link between activity {activity_id} and persona {persona_id} not found",
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/{activity_id}/compatibility/{other_activity_id}",
    response_model=dict[str, Any],
    summary="Check activity compatibility",
    description="Check compatibility between two activities for sequence execution",
)
async def check_activity_compatibility(
    activity_id: uuid.UUID,
    other_activity_id: uuid.UUID,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> dict[str, Any]:
    """Check compatibility between two activities."""
    try:
        compatibility = await service.check_activity_compatibility(
            activity_id, other_activity_id
        )
        return compatibility
    except ActivityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/{activity_id}/similar",
    response_model=list[dict[str, Any]],
    summary="Find similar activities",
    description="Find activities similar to the given activity based on various criteria",
)
async def find_similar_activities(
    activity_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.7, ge=0.0, le=1.0),
    service: ActivityApplicationService = Depends(get_activity_service),
) -> list[dict[str, Any]]:
    """Find similar activities."""
    try:
        similar = await service.find_similar_activities(
            activity_id, limit, min_similarity
        )
        return similar
    except ActivityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with ID {activity_id} not found",
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/{activity_id}/validation",
    response_model=dict[str, Any],
    summary="Validate activity",
    description="Perform comprehensive validation of activity configuration",
)
async def validate_activity(
    activity_id: uuid.UUID,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> dict[str, Any]:
    """Validate activity configuration."""
    try:
        validation_result = await service.validate_activity(activity_id)
        return validation_result
    except ActivityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with ID {activity_id} not found",
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
