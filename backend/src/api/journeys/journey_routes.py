"""
Journey REST API Endpoints

This module provides comprehensive REST API endpoints for journey management
in the ERPNext test automation framework. Handles CRUD operations, validation,
execution planning, and journey lifecycle management.
"""

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from ...application.dto.base_schemas import PaginatedResponse
from ...application.dto.journey_schemas import (
    ActionStepSchema,
    JourneyAssociationUpdateSchema,
    JourneyBulkOperationSchema,
    JourneyBulkResultSchema,
    JourneyCreateSchema,
    JourneyExecutionPlanSchema,
    JourneyFilterSchema,
    JourneyFromTemplateSchema,
    JourneyListItemSchema,
    JourneyResponseSchema,
    JourneySortSchema,
    JourneyStatsSchema,
    JourneyStepCreateSchema,
    JourneyStepUpdateSchema,
    JourneyTemplateSchema,
    JourneyUpdateSchema,
    JourneyValidationSchema,
)
from ...application.services.action_service import ActionLibraryService
from ...application.services.journey_service import JourneyService
from ...domain.journeys.journey_action_service import JourneyActionService
from ...infrastructure.database import get_sync_db
from ...infrastructure.database.repositories.action_repository import (
    SQLAlchemyActionRepository,
)
from ...infrastructure.database.repositories.activity_repository import (
    SQLAlchemyActivityRepository,
)
from ...infrastructure.database.repositories.journey_repository import JourneyRepository
from ...infrastructure.database.repositories.persona_repository import (
    SQLAlchemyPersonaRepository,
)

# Create router for journey endpoints
router = APIRouter(prefix="/journeys", tags=["journeys"])


def get_services(db: Session = Depends(get_sync_db)):
    """Dependency to get required services."""
    journey_repo = JourneyRepository(db)
    action_repo = SQLAlchemyActionRepository(db)
    persona_repo = SQLAlchemyPersonaRepository(db)
    activity_repo = SQLAlchemyActivityRepository(db)

    # Mock persona and activity services (would be proper implementations)
    class MockPersonaService:
        async def exists(self, persona_id: uuid.UUID) -> bool:
            persona = await persona_repo.find_by_id(persona_id)
            return persona is not None

        async def get_persona_info(
            self, persona_id: uuid.UUID
        ) -> Optional[dict[str, Any]]:
            persona = await persona_repo.find_by_id(persona_id)
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
    activity_service = MockActivityService()
    action_service = ActionLibraryService(action_repo)

    journey_action_service = JourneyActionService(action_repo)

    journey_service = JourneyService(
        journey_repo,
        journey_action_service,
        persona_service,
        activity_service,  # journey_action_service would be implemented
    )

    return journey_service, action_service


@router.post(
    "/",
    response_model=JourneyResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create new journey",
    description="Create a new journey with validation and initial steps",
)
async def create_journey(
    journey_data: JourneyCreateSchema, services=Depends(get_services)
) -> JourneyResponseSchema:
    """Create a new journey."""
    journey_service, _ = services

    try:
        return await journey_service.create_journey(journey_data)
    except Exception as e:
        if "validation" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create journey: {str(e)}",
        )


@router.get(
    "/{journey_id}",
    response_model=JourneyResponseSchema,
    summary="Get journey by ID",
    description="Retrieve journey details including steps and execution plan",
)
async def get_journey(
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    include_details: bool = Query(
        True, description="Include detailed step information"
    ),
    services=Depends(get_services),
) -> JourneyResponseSchema:
    """Get journey by ID."""
    journey_service, _ = services

    try:
        return await journey_service.get_journey(journey_id, include_details)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journey with ID {journey_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve journey: {str(e)}",
        )


@router.get(
    "/",
    response_model=PaginatedResponse[JourneyListItemSchema],
    summary="List journeys",
    description="List journeys with filtering, sorting, and pagination",
)
async def list_journeys(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of journeys"),
    offset: int = Query(0, ge=0, description="Number of journeys to skip"),
    persona_id: Optional[uuid.UUID] = Query(None, description="Filter by persona ID"),
    activity_id: Optional[uuid.UUID] = Query(None, description="Filter by activity ID"),
    execution_status: Optional[str] = Query(
        None, description="Filter by execution status"
    ),
    complexity_level: Optional[str] = Query(
        None, description="Filter by complexity level"
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    name_contains: Optional[str] = Query(
        None, description="Filter by name containing text"
    ),
    sort_by: Optional[str] = Query("updated_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    services=Depends(get_services),
) -> PaginatedResponse[JourneyListItemSchema]:
    """List journeys with filtering and pagination."""
    journey_service, _ = services

    # Build filters
    filters = JourneyFilterSchema(
        persona_id=persona_id,
        activity_id=activity_id,
        execution_status=execution_status,
        complexity_level=complexity_level,
        is_active=is_active,
        name_contains=name_contains,
    )

    # Build sorting
    sort = JourneySortSchema(sort_by=sort_by, sort_order=sort_order)

    try:
        return await journey_service.list_journeys(
            filters=filters, sort=sort, limit=limit, offset=offset
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list journeys: {str(e)}",
        )


@router.put(
    "/{journey_id}",
    response_model=JourneyResponseSchema,
    summary="Update journey",
    description="Update journey details and properties",
)
async def update_journey(
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    update_data: JourneyUpdateSchema = None,
    services=Depends(get_services),
) -> JourneyResponseSchema:
    """Update journey."""
    journey_service, _ = services

    try:
        return await journey_service.update_journey(journey_id, update_data)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journey with ID {journey_id} not found",
            )
        elif "validation" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update journey: {str(e)}",
        )


@router.patch(
    "/{journey_id}/associations",
    response_model=JourneyResponseSchema,
    summary="Update journey associations",
    description="Update persona and activity associations",
)
async def update_journey_associations(
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    association_data: JourneyAssociationUpdateSchema = None,
    services=Depends(get_services),
) -> JourneyResponseSchema:
    """Update journey associations."""
    journey_service, _ = services

    try:
        return await journey_service.update_journey_associations(
            journey_id, association_data
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journey with ID {journey_id} not found",
            )
        elif "validation" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update journey associations: {str(e)}",
        )


@router.delete(
    "/{journey_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete journey",
    description="Delete journey and all associated steps",
)
async def delete_journey(
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    services=Depends(get_services),
):
    """Delete journey."""
    journey_service, _ = services

    try:
        success = await journey_service.delete_journey(journey_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journey with ID {journey_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete journey: {str(e)}",
        )


# Journey Steps Management


@router.post(
    "/{journey_id}/steps",
    response_model=ActionStepSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add journey step",
    description="Add a new step to journey",
)
async def add_journey_step(
    step_data: JourneyStepCreateSchema,
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    services=Depends(get_services),
) -> ActionStepSchema:
    """Add step to journey."""
    journey_service, _ = services

    try:
        return await journey_service.add_journey_step(journey_id, step_data)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "validation" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add journey step: {str(e)}",
        )


@router.put(
    "/{journey_id}/steps/{step_number}",
    response_model=ActionStepSchema,
    summary="Update journey step",
    description="Update existing journey step",
)
async def update_journey_step(
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    step_number: int = Path(..., description="Step number to update"),
    step_data: JourneyStepUpdateSchema = None,
    services=Depends(get_services),
) -> ActionStepSchema:
    """Update journey step."""
    journey_service, _ = services

    try:
        return await journey_service.update_journey_step(
            journey_id, step_number, step_data
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "validation" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update journey step: {str(e)}",
        )


@router.delete(
    "/{journey_id}/steps/{step_number}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove journey step",
    description="Remove step from journey",
)
async def remove_journey_step(
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    step_number: int = Path(..., description="Step number to remove"),
    services=Depends(get_services),
):
    """Remove journey step."""
    journey_service, _ = services

    try:
        success = await journey_service.remove_journey_step(journey_id, step_number)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Step {step_number} not found in journey {journey_id}",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove journey step: {str(e)}",
        )


# Journey Validation and Execution Planning


@router.post(
    "/{journey_id}/validate",
    response_model=JourneyValidationSchema,
    summary="Validate journey",
    description="Perform comprehensive journey validation",
)
async def validate_journey(
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    services=Depends(get_services),
) -> JourneyValidationSchema:
    """Validate journey."""
    journey_service, _ = services

    try:
        return await journey_service.validate_journey(journey_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journey with ID {journey_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate journey: {str(e)}",
        )


@router.post(
    "/{journey_id}/execution-plan",
    response_model=JourneyExecutionPlanSchema,
    summary="Generate execution plan",
    description="Generate optimized execution plan for journey",
)
async def generate_execution_plan(
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    services=Depends(get_services),
) -> JourneyExecutionPlanSchema:
    """Generate execution plan."""
    journey_service, _ = services

    try:
        return await journey_service.generate_execution_plan(journey_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journey with ID {journey_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate execution plan: {str(e)}",
        )


@router.post(
    "/{journey_id}/prepare-execution",
    summary="Prepare for execution",
    description="Prepare journey for execution",
)
async def prepare_journey_for_execution(
    journey_id: uuid.UUID = Path(..., description="Journey ID"),
    services=Depends(get_services),
):
    """Prepare journey for execution."""
    journey_service, _ = services

    try:
        success = await journey_service.prepare_journey_for_execution(journey_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Journey preparation failed",
            )
        return {"message": "Journey prepared for execution successfully"}
    except HTTPException:
        raise
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Journey with ID {journey_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to prepare journey: {str(e)}",
        )


# Bulk Operations


@router.post(
    "/bulk",
    response_model=JourneyBulkResultSchema,
    summary="Bulk journey operations",
    description="Perform bulk operations on multiple journeys",
)
async def bulk_journey_operation(
    operation_data: JourneyBulkOperationSchema, services=Depends(get_services)
) -> JourneyBulkResultSchema:
    """Perform bulk operations on journeys."""
    journey_service, _ = services

    try:
        return await journey_service.bulk_operation(operation_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk operation: {str(e)}",
        )


# Statistics and Analytics


@router.get(
    "/statistics",
    response_model=JourneyStatsSchema,
    summary="Get journey statistics",
    description="Retrieve journey usage and performance statistics",
)
async def get_journey_statistics(services=Depends(get_services)) -> JourneyStatsSchema:
    """Get journey statistics."""
    journey_service, _ = services

    try:
        return await journey_service.get_journey_statistics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}",
        )


# Template Management


@router.post(
    "/templates",
    summary="Create journey template",
    description="Create reusable journey template",
)
async def create_journey_template(
    template_data: JourneyTemplateSchema, services=Depends(get_services)
):
    """Create journey template."""
    journey_service, _ = services

    try:
        template_name = await journey_service.create_journey_template(template_data)
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
    response_model=JourneyResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create journey from template",
    description="Create new journey from existing template",
)
async def create_journey_from_template(
    template_request: JourneyFromTemplateSchema, services=Depends(get_services)
) -> JourneyResponseSchema:
    """Create journey from template."""
    journey_service, _ = services

    try:
        return await journey_service.create_journey_from_template(template_request)
    except Exception as e:
        if "template" in str(e).lower() and "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "validation" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create journey from template: {str(e)}",
        )
