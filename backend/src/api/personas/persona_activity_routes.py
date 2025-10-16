"""Nested persona-activities endpoints.

This module provides REST API endpoints for managing relationships
between personas and activities, nested under the personas API.
"""

import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ...infrastructure.database.config import get_db
from ...infrastructure.database.repositories.persona_repository import SQLAlchemyPersonaRepository
from ...infrastructure.database.repositories.activity_repository import (
    SQLAlchemyActivityRepository,
    SQLAlchemyActivityPersonaLinkRepository
)
from ...application.services.activity_service import ActivityApplicationService
from ...application.dto.activity_schemas import (
    ActivityResponse,
    ActivityListResponse,
    ActivityPersonaLinkCreateRequest,
    ActivityPersonaLinkResponse,
    ActivityPersonaLinkUpdateRequest,
    ActivityBulkOperationRequest
)
from ...domain.personas.exceptions import PersonaNotFoundError
from ...domain.activities.exceptions import (
    ActivityNotFoundError,
    ActivityPersonaLinkNotFoundError,
    ActivityPersonaLinkAlreadyExistsError
)

# Create router for nested persona-activities endpoints
router = APIRouter()


def get_services(db: Session = Depends(get_db)):
    """Dependency to get required services."""
    persona_repo = SQLAlchemyPersonaRepository(db)
    activity_repo = SQLAlchemyActivityRepository(db)
    link_repo = SQLAlchemyActivityPersonaLinkRepository(db)
    activity_service = ActivityApplicationService(activity_repo, link_repo)
    return persona_repo, activity_service


@router.get(
    "/personas/{persona_id}/activities",
    response_model=ActivityListResponse,
    summary="List persona activities",
    description="Get all activities associated with a specific persona"
)
async def list_persona_activities(
    persona_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    priority: Optional[str] = Query(None, regex="^(low|medium|high)$"),
    is_active: Optional[bool] = Query(None),
    services=Depends(get_services)
) -> ActivityListResponse:
    """List all activities for a specific persona."""
    persona_repo, activity_service = services
    
    try:
        # Verify persona exists
        persona = await persona_repo.get_by_id(persona_id)
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona with ID {persona_id} not found"
            )
        
        # Get activities for persona
        filters = {}
        if priority is not None:
            filters["priority"] = priority
        if is_active is not None:
            filters["is_active"] = is_active
        
        activities, total = await activity_service.list_persona_activities(
            persona_id=persona_id,
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        return ActivityListResponse(
            activities=[ActivityResponse.from_entity(a) for a in activities],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except PersonaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona with ID {persona_id} not found"
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.post(
    "/personas/{persona_id}/activities/{activity_id}",
    response_model=ActivityPersonaLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link persona to activity",
    description="Create a relationship between a persona and an activity"
)
async def link_persona_to_activity(
    persona_id: uuid.UUID,
    activity_id: uuid.UUID,
    link_data: ActivityPersonaLinkCreateRequest,
    services=Depends(get_services)
) -> ActivityPersonaLinkResponse:
    """Create a link between persona and activity."""
    persona_repo, activity_service = services
    
    try:
        # Verify both persona and activity exist
        persona = await persona_repo.get_by_id(persona_id)
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona with ID {persona_id} not found"
            )
        
        link = await activity_service.create_persona_activity_link(
            persona_id=persona_id,
            activity_id=activity_id,
            priority=link_data.priority,
            notes=link_data.notes
        )
        
        return ActivityPersonaLinkResponse.from_model(link)
        
    except PersonaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona with ID {persona_id} not found"
        )
    except ActivityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with ID {activity_id} not found"
        )
    except ActivityPersonaLinkAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Link between persona {persona_id} and activity {activity_id} already exists"
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/personas/{persona_id}/activities/{activity_id}",
    response_model=ActivityPersonaLinkResponse,
    summary="Get persona-activity link",
    description="Get details of the relationship between a persona and activity"
)
async def get_persona_activity_link(
    persona_id: uuid.UUID,
    activity_id: uuid.UUID,
    services=Depends(get_services)
) -> ActivityPersonaLinkResponse:
    """Get persona-activity link details."""
    persona_repo, activity_service = services
    
    try:
        link = await activity_service.get_persona_activity_link(persona_id, activity_id)
        return ActivityPersonaLinkResponse.from_model(link)
        
    except ActivityPersonaLinkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link between persona {persona_id} and activity {activity_id} not found"
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.put(
    "/personas/{persona_id}/activities/{activity_id}",
    response_model=ActivityPersonaLinkResponse,
    summary="Update persona-activity link",
    description="Update the relationship between a persona and activity"
)
async def update_persona_activity_link(
    persona_id: uuid.UUID,
    activity_id: uuid.UUID,
    link_data: ActivityPersonaLinkUpdateRequest,
    services=Depends(get_services)
) -> ActivityPersonaLinkResponse:
    """Update persona-activity link."""
    persona_repo, activity_service = services
    
    try:
        link = await activity_service.update_persona_activity_link(
            persona_id=persona_id,
            activity_id=activity_id,
            **link_data.dict(exclude_unset=True)
        )
        
        return ActivityPersonaLinkResponse.from_model(link)
        
    except ActivityPersonaLinkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link between persona {persona_id} and activity {activity_id} not found"
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.delete(
    "/personas/{persona_id}/activities/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove persona-activity link",
    description="Remove the relationship between a persona and activity"
)
async def remove_persona_activity_link(
    persona_id: uuid.UUID,
    activity_id: uuid.UUID,
    services=Depends(get_services)
):
    """Remove persona-activity link."""
    persona_repo, activity_service = services
    
    try:
        await activity_service.delete_persona_activity_link(persona_id, activity_id)
        
    except ActivityPersonaLinkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link between persona {persona_id} and activity {activity_id} not found"
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.post(
    "/personas/{persona_id}/activities/bulk",
    response_model=Dict[str, Any],
    summary="Bulk link persona to activities",
    description="Create relationships between a persona and multiple activities"
)
async def bulk_link_persona_to_activities(
    persona_id: uuid.UUID,
    bulk_data: ActivityBulkOperationRequest,
    services=Depends(get_services)
) -> Dict[str, Any]:
    """Bulk create persona-activity links."""
    persona_repo, activity_service = services
    
    try:
        # Verify persona exists
        persona = await persona_repo.get_by_id(persona_id)
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona with ID {persona_id} not found"
            )
        
        results = await activity_service.bulk_create_persona_activity_links(
            persona_id=persona_id,
            activity_ids=bulk_data.activity_ids,
            priority=bulk_data.priority,
            notes=bulk_data.notes or ""
        )
        
        return {
            "created_count": len(results),
            "created_links": [ActivityPersonaLinkResponse.from_model(link) for link in results],
            "persona_id": str(persona_id)
        }
        
    except PersonaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona with ID {persona_id} not found"
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.delete(
    "/personas/{persona_id}/activities/bulk",
    response_model=Dict[str, Any],
    summary="Bulk remove persona-activity links",
    description="Remove relationships between a persona and multiple activities"
)
async def bulk_remove_persona_activity_links(
    persona_id: uuid.UUID,
    bulk_data: ActivityBulkOperationRequest,
    services=Depends(get_services)
) -> Dict[str, Any]:
    """Bulk remove persona-activity links."""
    persona_repo, activity_service = services
    
    try:
        deleted_count = await activity_service.bulk_delete_persona_activity_links(
            persona_id=persona_id,
            activity_ids=bulk_data.activity_ids
        )
        
        return {
            "deleted_count": deleted_count,
            "persona_id": str(persona_id),
            "activity_ids": [str(aid) for aid in bulk_data.activity_ids]
        }
        
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/personas/{persona_id}/activities/statistics",
    response_model=Dict[str, Any],
    summary="Get persona activity statistics",
    description="Get statistical information about activities associated with a persona"
)
async def get_persona_activity_statistics(
    persona_id: uuid.UUID,
    services=Depends(get_services)
) -> Dict[str, Any]:
    """Get persona activity statistics."""
    persona_repo, activity_service = services
    
    try:
        # Verify persona exists
        persona = await persona_repo.get_by_id(persona_id)
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona with ID {persona_id} not found"
            )
        
        stats = await activity_service.get_persona_activity_statistics(persona_id)
        
        return {
            "persona_id": str(persona_id),
            "statistics": stats
        }
        
    except PersonaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona with ID {persona_id} not found"
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/personas/{persona_id}/activities/recommendations",
    response_model=List[ActivityResponse],
    summary="Get activity recommendations",
    description="Get recommended activities for a persona based on their profile"
)
async def get_activity_recommendations(
    persona_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=50),
    services=Depends(get_services)
) -> List[ActivityResponse]:
    """Get activity recommendations for persona."""
    persona_repo, activity_service = services
    
    try:
        # Verify persona exists
        persona = await persona_repo.get_by_id(persona_id)
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona with ID {persona_id} not found"
            )
        
        recommendations = await activity_service.get_activity_recommendations(
            persona_id=persona_id,
            limit=limit
        )
        
        return [ActivityResponse.from_entity(activity) for activity in recommendations]
        
    except PersonaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona with ID {persona_id} not found"
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )