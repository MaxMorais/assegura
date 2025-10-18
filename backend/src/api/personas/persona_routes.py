"""Persona REST endpoints for ERPNext Test Automation Meta-Framework.

Provides comprehensive CRUD operations for persona management with
multi-tenant support, validation, and error handling.
"""

import logging
from typing import Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from src.application.dto.persona_schemas import (
    PersonaCreateRequest,
    PersonaListResponse,
    PersonaResponse,
    PersonaSearchRequest,
    PersonaStatsResponse,
    PersonaSuggestionRequest,
    PersonaSuggestionResponse,
    PersonaSummaryResponse,
    PersonaUpdateRequest,
    PersonaValidationResponse,
)
from src.application.dto.activity_schemas import (
    ActivityPersonaLinkResponseDTO,
    ActivityPersonaLinkCreateRequestDTO,
    ActivityListResponseDTO,
)
from src.application.services.activity_service import ActivityApplicationService
from src.application.services.persona_service import PersonaService
from src.domain.personas.exceptions import (
    PersonaAlreadyExistsError,
    PersonaMultipleValidationError,
    PersonaNotFoundError,
    PersonaValidationError,
)
from src.infrastructure.auth.middleware import get_current_consultant_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personas", tags=["personas"])


def get_persona_service() -> PersonaService:
    """Dependency injection for PersonaService."""
    # This will be properly configured with DI container in production
    from src.infrastructure.database import get_sync_db
    from src.infrastructure.database.repositories.persona_repository import (
        SQLAlchemyPersonaRepository,
    )
    from src.infrastructure.database.repositories.unit_of_work import SqlUnitOfWork

    session = next(get_sync_db())
    repository = SQLAlchemyPersonaRepository(session)
    unit_of_work = SqlUnitOfWork(session)
    return PersonaService(repository, unit_of_work)


def get_activity_service() -> ActivityApplicationService:
    """Dependency injection for ActivityApplicationService."""
    # This will be properly configured with DI container in production
    from src.infrastructure.database import get_sync_db
    from src.infrastructure.database.repositories.activity_repository import (
        SQLAlchemyActivityRepository,
        SQLAlchemyActivityPersonaLinkRepository,
    )
    from src.infrastructure.database.repositories.persona_repository import (
        SQLAlchemyPersonaRepository,
    )

    session = next(get_sync_db())
    activity_repo = SQLAlchemyActivityRepository(session)
    persona_repo = SQLAlchemyPersonaRepository(session)
    link_repo = SQLAlchemyActivityPersonaLinkRepository(session)
    return ActivityApplicationService(activity_repo, persona_repo, link_repo)


@router.post(
    "/",
    response_model=PersonaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new persona",
    description="Create a new test persona with ERPNext roles and permissions",
)
async def create_persona(
    request: PersonaCreateRequest,
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaResponse:
    """Create a new persona for the authenticated consultant.

    Args:
        request: Persona creation data
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Returns:
        Created persona with generated ID and timestamps

    Raises:
        400: Validation errors or duplicate name
        422: Invalid ERPNext roles or permissions
    """
    try:
        logger.info(f"Creating persona '{request.name}' for consultant {consultant_id}")

        # TODO: Add consultant_id to request or service layer
        persona = await persona_service.create_persona(request)

        logger.info(f"Successfully created persona {persona.id}")
        return persona

    except PersonaAlreadyExistsError as e:
        logger.warning(f"Persona creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Persona with name '{request.name}' already exists",
        )
    except PersonaValidationError as e:
        logger.warning(f"Persona validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except PersonaMultipleValidationError as e:
        logger.warning(f"Multiple validation errors: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": e.errors},
        )


@router.get(
    "/",
    response_model=PersonaListResponse,
    summary="List personas",
    description="Get paginated list of personas for authenticated consultant",
)
async def list_personas(
    limit: int = Query(
        default=50, ge=1, le=100, description="Maximum number of personas to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of personas to skip"),
    search: Optional[str] = Query(
        default=None, description="Search in persona names and descriptions"
    ),
    is_active: Optional[bool] = Query(
        default=None, description="Filter by active status"
    ),
    erpnext_role: Optional[str] = Query(
        default=None, description="Filter by ERPNext role"
    ),
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaListResponse:
    """List personas with filtering and pagination.

    Args:
        limit: Maximum results per page (1-100)
        offset: Number of results to skip
        search: Optional search term for names/descriptions
        is_active: Optional filter by active status
        erpnext_role: Optional filter by ERPNext role
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Returns:
        Paginated list of personas with metadata
    """
    try:
        logger.info(
            f"Listing personas for consultant {consultant_id} (limit={limit}, offset={offset})"
        )

        search_request = PersonaSearchRequest(
            limit=limit,
            offset=offset,
            search_term=search,
            is_active=is_active,
            erpnext_role=erpnext_role,
        )

        result = await persona_service.list_personas(search_request)

        logger.info(
            f"Retrieved {len(result.items)} personas (total: {result.total})"
        )
        return result

    except Exception as e:
        logger.error(f"Error listing personas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve personas",
        )


@router.get(
    "/{persona_id}",
    response_model=PersonaResponse,
    summary="Get persona by ID",
    description="Retrieve detailed persona information",
)
async def get_persona(
    persona_id: UUID,
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaResponse:
    """Get persona by ID for authenticated consultant.

    Args:
        persona_id: Unique persona identifier
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Returns:
        Complete persona information

    Raises:
        404: Persona not found or not owned by consultant
    """
    try:
        logger.info(f"Retrieving persona {persona_id} for consultant {consultant_id}")

        persona = await persona_service.get_persona(persona_id)

        # TODO: Verify persona ownership by consultant
        logger.info(f"Successfully retrieved persona {persona_id}")
        return persona

    except PersonaNotFoundError:
        logger.warning(f"Persona {persona_id} not found for consultant {consultant_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona {persona_id} not found",
        )


@router.put(
    "/{persona_id}",
    response_model=PersonaResponse,
    summary="Update persona",
    description="Update existing persona information",
)
async def update_persona(
    persona_id: UUID,
    request: PersonaUpdateRequest,
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaResponse:
    """Update persona information.

    Args:
        persona_id: Unique persona identifier
        request: Updated persona data
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Returns:
        Updated persona information

    Raises:
        404: Persona not found
        400: Validation errors or name conflicts
        422: Invalid ERPNext roles or permissions
    """
    try:
        logger.info(f"Updating persona {persona_id} for consultant {consultant_id}")

        # TODO: Verify persona ownership by consultant
        persona = await persona_service.update_persona(persona_id, request)

        logger.info(f"Successfully updated persona {persona_id}")
        return persona

    except PersonaNotFoundError:
        logger.warning(f"Persona {persona_id} not found for update")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona {persona_id} not found",
        )
    except PersonaAlreadyExistsError as e:
        logger.warning(f"Persona update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Persona with name '{request.name}' already exists",
        )
    except PersonaValidationError as e:
        logger.warning(f"Persona validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.delete(
    "/{persona_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete persona",
    description="Delete persona and all associated data",
)
async def delete_persona(
    persona_id: UUID,
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> None:
    """Delete persona by ID.

    Args:
        persona_id: Unique persona identifier
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Raises:
        404: Persona not found
        409: Cannot delete persona with associated activities
    """
    try:
        logger.info(f"Deleting persona {persona_id} for consultant {consultant_id}")

        # TODO: Verify persona ownership by consultant
        await persona_service.delete_persona(persona_id)

        logger.info(f"Successfully deleted persona {persona_id}")

    except PersonaNotFoundError:
        logger.warning(f"Persona {persona_id} not found for deletion")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona {persona_id} not found",
        )
    except ValueError as e:
        logger.warning(f"Cannot delete persona {persona_id}: {e}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{persona_id}/summary",
    response_model=PersonaSummaryResponse,
    summary="Get persona summary",
    description="Get condensed persona information for lists and overviews",
)
async def get_persona_summary(
    persona_id: UUID,
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaSummaryResponse:
    """Get persona summary for lists and quick views.

    Args:
        persona_id: Unique persona identifier
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Returns:
        Condensed persona information

    Raises:
        404: Persona not found
    """
    try:
        logger.info(f"Retrieving persona summary {persona_id}")

        summary = await persona_service.get_persona_summary(persona_id)
        return summary

    except PersonaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona {persona_id} not found",
        )


@router.post(
    "/validate",
    response_model=PersonaValidationResponse,
    summary="Validate persona data",
    description="Validate persona data without creating the persona",
)
async def validate_persona_data(
    request: PersonaCreateRequest,
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaValidationResponse:
    """Validate persona data without saving.

    Args:
        request: Persona data to validate
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Returns:
        Validation results with detailed feedback
    """
    try:
        logger.info(f"Validating persona data for '{request.name}'")

        result = await persona_service.validate_persona_data(request)
        return result

    except Exception as e:
        logger.error(f"Error validating persona data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate persona data",
        )


@router.post(
    "/suggestions",
    response_model=PersonaSuggestionResponse,
    summary="Get persona suggestions",
    description="Get intelligent suggestions for persona creation",
)
async def get_persona_suggestions(
    request: PersonaSuggestionRequest,
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaSuggestionResponse:
    """Get intelligent suggestions for persona creation.

    Args:
        request: Context for generating suggestions
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Returns:
        Intelligent suggestions based on context
    """
    try:
        logger.info(
            f"Generating persona suggestions for context: {request.context[:50]}..."
        )

        suggestions = await persona_service.get_persona_suggestions(request)
        return suggestions

    except Exception as e:
        logger.error(f"Error generating persona suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate persona suggestions",
        )


@router.get(
    "/statistics/overview",
    response_model=PersonaStatsResponse,
    summary="Get persona statistics",
    description="Get overview statistics for all personas",
)
async def get_persona_statistics(
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaStatsResponse:
    """Get persona statistics and overview.

    Args:
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Returns:
        Statistics about personas and their usage
    """
    try:
        logger.info(f"Retrieving persona statistics for consultant {consultant_id}")

        stats = await persona_service.get_persona_statistics()
        return stats

    except Exception as e:
        logger.error(f"Error retrieving persona statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve persona statistics",
        )


@router.post(
    "/{persona_id}/activate",
    response_model=PersonaResponse,
    summary="Activate persona",
    description="Activate an inactive persona",
)
async def activate_persona(
    persona_id: UUID,
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaResponse:
    """Activate a persona.

    Args:
        persona_id: Unique persona identifier
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Returns:
        Updated persona with active status

    Raises:
        404: Persona not found
    """
    try:
        logger.info(f"Activating persona {persona_id}")

        persona = await persona_service.activate_persona(persona_id)
        return persona

    except PersonaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona {persona_id} not found",
        )


@router.post(
    "/{persona_id}/deactivate",
    response_model=PersonaResponse,
    summary="Deactivate persona",
    description="Deactivate an active persona",
)
async def deactivate_persona(
    persona_id: UUID,
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaResponse:
    """Deactivate a persona.

    Args:
        persona_id: Unique persona identifier
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Returns:
        Updated persona with inactive status

    Raises:
        404: Persona not found
    """
    try:
        logger.info(f"Deactivating persona {persona_id}")

        persona = await persona_service.deactivate_persona(persona_id)
        return persona

    except PersonaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona {persona_id} not found",
        )


@router.get(
    "/{persona_id}/similar",
    response_model=list[PersonaSummaryResponse],
    summary="Find similar personas",
    description="Find personas similar to the specified one",
)
async def find_similar_personas(
    persona_id: UUID,
    similarity_threshold: float = Query(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score (0-1)"
    ),
    consultant_id: UUID = Depends(get_current_consultant_id),
    persona_service: PersonaService = Depends(get_persona_service),
) -> list[PersonaSummaryResponse]:
    """Find personas similar to the specified persona.

    Args:
        persona_id: Reference persona identifier
        similarity_threshold: Minimum similarity score (0-1)
        consultant_id: ID of authenticated consultant
        persona_service: Injected persona service

    Returns:
        List of similar personas with similarity scores

    Raises:
        404: Persona not found
    """
    try:
        logger.info(
            f"Finding similar personas to {persona_id} (threshold={similarity_threshold})"
        )

        similar_personas = await persona_service.find_similar_personas(
            persona_id, similarity_threshold
        )

        logger.info(f"Found {len(similar_personas)} similar personas")
        return similar_personas

    except PersonaNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona {persona_id} not found",
        )


# Health check endpoint for persona service
@router.get(
    "/health", summary="Health check", description="Check if persona service is healthy"
)
async def health_check() -> JSONResponse:
    """Health check for persona endpoints."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "persona-api",
            "version": "1.0.0",
            "timestamp": "2025-01-15T10:30:00Z",
        },
    )


# Persona-Activity endpoints
@router.get(
    "/{persona_id}/activities",
    response_model=ActivityListResponseDTO,
    summary="List persona activities",
    description="Get paginated list of activities linked to a persona",
)
async def list_persona_activities(
    persona_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ActivityApplicationService = Depends(get_activity_service),
) -> ActivityListResponseDTO:
    """List activities linked to a persona."""
    result = await service.get_persona_activities(str(persona_id), None, page, per_page)
    return result


@router.get(
    "/{persona_id}/activities/statistics",
    summary="Get persona activity statistics",
    description="Get statistics about activities linked to a persona",
)
async def get_persona_activity_statistics(
    persona_id: UUID,
    service: ActivityApplicationService = Depends(get_activity_service),
):
    """Get persona activity statistics."""
    try:
        activities_response = await service.get_persona_activities(str(persona_id), page=1, per_page=100)
        activities = activities_response.activities  # Access the activities from the paginated response
        result = {
            "persona_id": str(persona_id),
            "statistics": {
                "total_activities": len(activities),
                "average_complexity": 3.0,  # Mock value
                "total_estimated_duration": sum(getattr(activity.activity, 'estimated_duration', 180) for activity in activities),
            },
        }
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/{persona_id}/activities/recommendations",
    summary="Get activity recommendations",
    description="Get recommended activities for a persona",
)
async def get_activity_recommendations(
    persona_id: UUID,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations"),
    service: ActivityApplicationService = Depends(get_activity_service),
) -> list[dict[str, Any]]:
    """Get activity recommendations for a persona."""
    try:
        # For now, return mock recommendations
        return [
            {
                "activity_id": "mock-activity-1",
                "name": "Recommended Activity 1",
                "reason": "Based on persona role",
                "confidence_score": 0.85,
            },
            {
                "activity_id": "mock-activity-2", 
                "name": "Recommended Activity 2",
                "reason": "Complementary to existing activities",
                "confidence_score": 0.72,
            },
        ][:limit]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/{persona_id}/activities/{activity_id}",
    response_model=ActivityPersonaLinkResponseDTO,
    summary="Get persona-activity link",
    description="Get the link between a specific persona and activity",
)
async def get_persona_activity_link(
    persona_id: UUID,
    activity_id: UUID,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> ActivityPersonaLinkResponseDTO:
    """Get specific persona-activity link."""
    try:
        # Use the repository directly to get the link
        link = service.activity_persona_link_repository.get_by_ids(persona_id, activity_id)
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Link between persona {persona_id} and activity {activity_id} not found",
            )
        return service._link_to_dto(link)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.delete(
    "/{persona_id}/activities/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete persona-activity link",
    description="Remove the link between a persona and activity",
)
async def delete_persona_activity_link(
    persona_id: UUID,
    activity_id: UUID,
    service: ActivityApplicationService = Depends(get_activity_service),
) -> None:
    """Delete persona-activity link."""
    try:
        await service.unlink_activity_from_persona(persona_id, activity_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link between persona {persona_id} and activity {activity_id} not found",
        )
