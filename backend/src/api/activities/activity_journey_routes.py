"""
Activity-Journey REST API Endpoints

This module provides nested REST API endpoints for managing relationships
between activities and journeys in the ERPNext test automation framework.
Enables CRUD operations for journeys within the context of specific activities.
"""

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from ...application.dto.base_schemas import PaginatedResponse
from ...application.dto.journey_schemas import (
    JourneyCreateSchema,
    JourneyFilterSchema,
    JourneyListItemSchema,
    JourneyResponseSchema,
    JourneySortSchema,
    JourneyStatsSchema,
    JourneyUpdateSchema,
    JourneyValidationSchema,
)
from ...application.services.activity_service import ActivityApplicationService
from ...application.services.journey_service import JourneyService
from ...infrastructure.database.config import get_db
from ...infrastructure.database.repositories.action_repository import (
    SQLAlchemyActionRepository,
)
from ...infrastructure.database.repositories.activity_repository import (
    SQLAlchemyActivityPersonaLinkRepository,
    SQLAlchemyActivityRepository,
)
from ...infrastructure.database.repositories.journey_repository import JourneyRepository
from ...infrastructure.database.repositories.persona_repository import (
    SQLAlchemyPersonaRepository,
)

# Create router for nested activity-journey endpoints
router = APIRouter()


def get_services(db: Session = Depends(get_db)):
    """Dependency to get required services."""
    # Initialize repositories
    activity_repo = SQLAlchemyActivityRepository(db)
    activity_link_repo = SQLAlchemyActivityPersonaLinkRepository(db)
    journey_repo = JourneyRepository(db)
    action_repo = SQLAlchemyActionRepository(db)
    persona_repo = SQLAlchemyPersonaRepository(db)

    # Initialize services
    activity_service = ActivityApplicationService(activity_repo, activity_link_repo)

    # Mock implementations for persona and activity services
    class MockPersonaService:
        async def exists(self, persona_id: uuid.UUID) -> bool:
            persona = await persona_repo.get_by_id(persona_id)
            return persona is not None

        async def get_persona_info(
            self, persona_id: uuid.UUID
        ) -> Optional[dict[str, Any]]:
            persona = await persona_repo.get_by_id(persona_id)
            return {"id": str(persona.id), "name": persona.name} if persona else None

    class MockActivityService:
        async def exists(self, activity_id: uuid.UUID) -> bool:
            activity = await activity_repo.get_by_id(activity_id)
            return activity is not None

        async def get_activity_info(
            self, activity_id: uuid.UUID
        ) -> Optional[dict[str, Any]]:
            activity = await activity_repo.get_by_id(activity_id)
            return {"id": str(activity.id), "name": activity.name} if activity else None

    persona_service = MockPersonaService()
    mock_activity_service = MockActivityService()

    journey_service = JourneyService(
        journey_repo,
        None,  # journey_action_service would be implemented
        persona_service,
        mock_activity_service,
    )

    return activity_service, journey_service


@router.get(
    "/activities/{activity_id}/journeys",
    response_model=PaginatedResponse[JourneyListItemSchema],
    summary="List activity journeys",
    description="Get all journeys associated with a specific activity",
)
async def list_activity_journeys(
    activity_id: uuid.UUID = Path(..., description="Activity ID"),
    skip: int = Query(0, ge=0, description="Number of journeys to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of journeys"),
    persona_id: Optional[uuid.UUID] = Query(None, description="Filter by persona"),
    execution_status: Optional[str] = Query(
        None, description="Filter by execution status"
    ),
    complexity_level: Optional[str] = Query(
        None, description="Filter by complexity level"
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    services=Depends(get_services),
) -> PaginatedResponse[JourneyListItemSchema]:
    """List all journeys for a specific activity."""
    activity_service, journey_service = services

    try:
        # Verify activity exists
        activity = await activity_service.get_activity(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found",
            )

        # Build filters
        filters = JourneyFilterSchema(
            activity_id=activity_id,
            persona_id=persona_id,
            execution_status=execution_status,
            complexity_level=complexity_level,
            is_active=is_active,
        )

        # Get journeys for activity
        journeys, total = await journey_service.list_journeys(
            filters=filters, skip=skip, limit=limit
        )

        return PaginatedResponse[JourneyListItemSchema](
            items=[JourneyListItemSchema.from_entity(j) for j in journeys],
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity journeys: {str(e)}",
        )


@router.post(
    "/activities/{activity_id}/journeys",
    response_model=JourneyResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create journey for activity",
    description="Create a new journey associated with a specific activity",
)
async def create_activity_journey(
    activity_id: uuid.UUID = Path(..., description="Activity ID"),
    journey_data: JourneyCreateSchema = ...,
    services=Depends(get_services),
) -> JourneyResponseSchema:
    """Create a new journey for a specific activity."""
    activity_service, journey_service = services

    try:
        # Verify activity exists
        activity = await activity_service.get_activity(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found",
            )

        # Ensure journey is linked to correct activity
        journey_data.activity_id = activity_id

        # Create journey
        journey = await journey_service.create_journey(journey_data)

        return journey

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found",
            )
        if "validation" in str(e).lower() or "already exists" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create journey: {str(e)}",
        )


@router.get(
    "/activities/{activity_id}/journeys/{journey_id}",
    response_model=JourneyResponseSchema,
    summary="Get activity journey",
    description="Get details of a specific journey within an activity",
)
async def get_activity_journey(
    activity_id: uuid.UUID = Path(..., description="Activity ID"),
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    services=Depends(get_services),
) -> JourneyResponseSchema:
    """Get a specific journey for an activity."""
    activity_service, journey_service = services

    try:
        # Verify activity exists
        activity = await activity_service.get_activity(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found",
            )

        # Get journey and verify it belongs to the activity
        journey = await journey_service.get_journey(journey_id)
        if not journey or journey.activity_id != activity_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journey with ID {journey_id} not found for activity {activity_id}",
            )

        return journey

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve journey: {str(e)}",
        )


@router.put(
    "/activities/{activity_id}/journeys/{journey_id}",
    response_model=JourneyResponseSchema,
    summary="Update activity journey",
    description="Update a specific journey within an activity",
)
async def update_activity_journey(
    activity_id: uuid.UUID = Path(..., description="Activity ID"),
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    journey_data: JourneyUpdateSchema = ...,
    services=Depends(get_services),
) -> JourneyResponseSchema:
    """Update a specific journey for an activity."""
    activity_service, journey_service = services

    try:
        # Verify activity exists
        activity = await activity_service.get_activity(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found",
            )

        # Get journey and verify it belongs to the activity
        existing_journey = await journey_service.get_journey(journey_id)
        if not existing_journey or existing_journey.activity_id != activity_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journey with ID {journey_id} not found for activity {activity_id}",
            )

        # Update journey
        updated_journey = await journey_service.update_journey(journey_id, journey_data)

        return updated_journey

    except HTTPException:
        raise
    except Exception as e:
        if "validation" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update journey: {str(e)}",
        )


@router.delete(
    "/activities/{activity_id}/journeys/{journey_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete activity journey",
    description="Delete a specific journey within an activity",
)
async def delete_activity_journey(
    activity_id: uuid.UUID = Path(..., description="Activity ID"),
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    services=Depends(get_services),
):
    """Delete a specific journey for an activity."""
    activity_service, journey_service = services

    try:
        # Verify activity exists
        activity = await activity_service.get_activity(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found",
            )

        # Get journey and verify it belongs to the activity
        existing_journey = await journey_service.get_journey(journey_id)
        if not existing_journey or existing_journey.activity_id != activity_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journey with ID {journey_id} not found for activity {activity_id}",
            )

        # Delete journey
        await journey_service.delete_journey(journey_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete journey: {str(e)}",
        )


@router.get(
    "/activities/{activity_id}/journeys/statistics",
    response_model=JourneyStatsSchema,
    summary="Get activity journey statistics",
    description="Get statistical information about journeys for a specific activity",
)
async def get_activity_journey_statistics(
    activity_id: uuid.UUID = Path(..., description="Activity ID"),
    services=Depends(get_services),
) -> JourneyStatsSchema:
    """Get journey statistics for a specific activity."""
    activity_service, journey_service = services

    try:
        # Verify activity exists
        activity = await activity_service.get_activity(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found",
            )

        # Get journey statistics for the activity
        stats = await journey_service.get_journey_statistics(activity_id=activity_id)

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve journey statistics: {str(e)}",
        )


@router.post(
    "/activities/{activity_id}/journeys/{journey_id}/validate",
    response_model=JourneyValidationSchema,
    summary="Validate activity journey",
    description="Validate a specific journey within an activity",
)
async def validate_activity_journey(
    activity_id: uuid.UUID = Path(..., description="Activity ID"),
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    services=Depends(get_services),
) -> JourneyValidationSchema:
    """Validate a specific journey for an activity."""
    activity_service, journey_service = services

    try:
        # Verify activity exists
        activity = await activity_service.get_activity(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with ID {activity_id} not found",
            )

        # Get journey and verify it belongs to the activity
        journey = await journey_service.get_journey(journey_id)
        if not journey or journey.activity_id != activity_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journey with ID {journey_id} not found for activity {activity_id}",
            )

        # Validate journey
        validation_result = await journey_service.validate_journey(journey_id)

        return validation_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate journey: {str(e)}",
        )