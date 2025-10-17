"""Persona application service.

Orchestrates persona use cases and coordinates between
domain layer and infrastructure in the ERPNext Test Automation Meta-Framework.
"""

import logging
from uuid import UUID

from src.domain.personas.persona import Persona
from src.domain.personas.exceptions import (
    PersonaAlreadyExistsError,
    PersonaMultipleValidationError,
    PersonaNotFoundError,
    PersonaValidationError,
)
from src.domain.personas.persona_service import PersonaService as PersonaDomainService
from src.domain.personas.persona_repository import PersonaRepository
from src.infrastructure.database.repositories.unit_of_work import UnitOfWork
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

logger = logging.getLogger(__name__)


class PersonaService:
    """Application service for persona use cases."""

    def __init__(self, persona_repository: PersonaRepository, unit_of_work: UnitOfWork):
        """Initialize persona service.

        Args:
            persona_repository: Repository for persona persistence
            unit_of_work: Unit of work for transaction management
        """
        self.persona_repository = persona_repository
        self.unit_of_work = unit_of_work
        self.domain_service = PersonaDomainService()

    async def create_persona(self, request: PersonaCreateRequest) -> PersonaResponse:
        """Create a new persona.

        Args:
            request: Persona creation request

        Returns:
            Created persona response

        Raises:
            PersonaAlreadyExistsError: If persona with same name exists
            PersonaValidationError: If persona data is invalid
        """
        logger.info(f"Creating persona: {request.name}")

        # Check if persona name already exists
        existing_persona = await self.persona_repository.find_by_name(request.name)
        if existing_persona:
            raise PersonaAlreadyExistsError("name", request.name)

        # Parse roles from string
        roles = [
            role.strip() for role in request.erpnext_roles.split(",") if role.strip()
        ]

        # Create persona domain entity
        persona = Persona(
            name=request.name,
            description=request.description,
            erpnext_roles=roles,
            permissions=request.permissions or "",
            is_active=request.is_active,
        )

        # Validate persona using domain service
        self.domain_service.validate_persona_creation(persona)

        # Save persona using unit of work
        async with self.unit_of_work:
            saved_persona = await self.persona_repository.save(persona)
            await self.unit_of_work.commit()

        logger.info(f"Created persona with ID: {saved_persona.id}")
        return self._to_response(saved_persona)

    async def get_persona(self, persona_id: UUID) -> PersonaResponse:
        """Get persona by ID.

        Args:
            persona_id: Unique persona identifier

        Returns:
            Persona response

        Raises:
            PersonaNotFoundError: If persona not found
        """
        persona = await self.persona_repository.find_by_id(persona_id)
        if not persona:
            raise PersonaNotFoundError(str(persona_id))

        return self._to_response(persona)

    async def get_persona_by_name(self, name: str) -> PersonaResponse:
        """Get persona by name.

        Args:
            name: Persona name

        Returns:
            Persona response

        Raises:
            PersonaNotFoundError: If persona not found
        """
        persona = await self.persona_repository.find_by_name(name)
        if not persona:
            raise PersonaNotFoundError(name, "name")

        return self._to_response(persona)

    async def update_persona(
        self, persona_id: UUID, request: PersonaUpdateRequest
    ) -> PersonaResponse:
        """Update an existing persona.

        Args:
            persona_id: Unique persona identifier
            request: Persona update request

        Returns:
            Updated persona response

        Raises:
            PersonaNotFoundError: If persona not found
            PersonaAlreadyExistsError: If name conflicts with existing persona
            PersonaValidationError: If update data is invalid
        """
        logger.info(f"Updating persona: {persona_id}")

        # Get current persona
        current_persona = await self.persona_repository.find_by_id(persona_id)
        if not current_persona:
            raise PersonaNotFoundError(str(persona_id))

        # Check name uniqueness if name is being updated
        if request.name and request.name != current_persona.name:
            existing_persona = await self.persona_repository.find_by_name(request.name)
            if existing_persona and existing_persona.id != persona_id:
                raise PersonaAlreadyExistsError("name", request.name)

        # Apply updates to current persona
        updated_persona = self._apply_updates(current_persona, request)

        # Validate update using domain service
        self.domain_service.validate_persona_update(current_persona, updated_persona)

        # Save updated persona using unit of work
        async with self.unit_of_work:
            saved_persona = await self.persona_repository.save(updated_persona)
            await self.unit_of_work.commit()

        logger.info(f"Updated persona: {persona_id}")
        return self._to_response(saved_persona)

    async def delete_persona(self, persona_id: UUID) -> None:
        """Delete a persona.

        Args:
            persona_id: Unique persona identifier

        Raises:
            PersonaNotFoundError: If persona not found
        """
        logger.info(f"Deleting persona: {persona_id}")

        # Get current persona
        persona = await self.persona_repository.find_by_id(persona_id)
        if not persona:
            raise PersonaNotFoundError(str(persona_id))

        # Check if persona can be deleted (business rules)
        # TODO: Check usage count from activities/journeys
        usage_count = 0  # await self._get_persona_usage_count(persona_id)
        self.domain_service.validate_persona_deletion(persona, usage_count)

        # Delete persona using unit of work
        async with self.unit_of_work:
            await self.persona_repository.delete(persona_id)
            await self.unit_of_work.commit()

        logger.info(f"Deleted persona: {persona_id}")

    async def list_personas(self, request: PersonaSearchRequest) -> PersonaListResponse:
        """List personas with filtering and pagination.

        Args:
            request: Search and pagination parameters

        Returns:
            Paginated list of personas
        """
        # Build filters
        filters = {}
        if request.query:
            filters["search"] = request.query
        if request.erpnext_roles:
            filters["erpnext_roles"] = request.erpnext_roles
        if request.is_active is not None:
            filters["is_active"] = request.is_active
        if request.has_permissions:
            filters["has_permissions"] = request.has_permissions
        if request.created_after:
            filters["created_after"] = request.created_after

        # Get personas with pagination
        personas, total = await self.persona_repository.find_with_pagination(
            filters=filters,
            page=request.page,
            page_size=request.page_size,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
        )

        # Convert to response format
        persona_responses = [self._to_response(persona) for persona in personas]

        return PersonaListResponse(
            items=persona_responses,
            total=total,
            page=request.page,
            page_size=request.page_size,
            has_next=(request.page * request.page_size) < total,
            has_previous=request.page > 1,
        )

    async def get_persona_summary(self, persona_id: UUID) -> PersonaSummaryResponse:
        """Get persona summary information.

        Args:
            persona_id: Unique persona identifier

        Returns:
            Persona summary

        Raises:
            PersonaNotFoundError: If persona not found
        """
        persona = await self.persona_repository.find_by_id(persona_id)
        if not persona:
            raise PersonaNotFoundError(str(persona_id))

        return PersonaSummaryResponse(
            id=persona.id,
            name=persona.name,
            description=persona.description,
            erpnext_roles_count=len(persona.erpnext_roles),
            permissions_count=len(persona.permissions_list),
            is_active=persona.is_active,
            created_at=persona.created_at,
        )

    async def validate_persona_data(
        self, request: PersonaCreateRequest
    ) -> PersonaValidationResponse:
        """Validate persona data without creating it.

        Args:
            request: Persona data to validate

        Returns:
            Validation response with errors and warnings
        """
        errors = []
        warnings = []
        suggestions = []

        try:
            # Parse roles
            roles = [
                role.strip()
                for role in request.erpnext_roles.split(",")
                if role.strip()
            ]

            # Create persona for validation
            persona = Persona(
                name=request.name,
                description=request.description,
                erpnext_roles=roles,
                permissions=request.permissions or "",
                is_active=request.is_active,
            )

            # Validate using domain service
            self.domain_service.validate_persona_creation(persona)

        except PersonaValidationError as e:
            errors.append(e.message)
        except PersonaMultipleValidationError as e:
            errors.extend([error.message for error in e.errors])
        except Exception as e:
            errors.append(str(e))

        # Get role combination warnings
        try:
            roles = [
                role.strip()
                for role in request.erpnext_roles.split(",")
                if role.strip()
            ]
            from src.domain.personas.erpnext_roles import validate_role_combination

            role_warnings = validate_role_combination(roles)
            warnings.extend(role_warnings)
        except Exception:
            pass

        # Generate suggestions
        if len(request.description) < 50:
            suggestions.append("Consider adding more detail to the persona description")

        if len(roles) == 1:
            suggestions.append(
                "Consider if this persona needs additional roles for complete functionality"
            )

        return PersonaValidationResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    async def get_persona_suggestions(
        self, request: PersonaSuggestionRequest
    ) -> PersonaSuggestionResponse:
        """Generate persona suggestions based on module and user level.

        Args:
            request: Suggestion request parameters

        Returns:
            List of suggested persona configurations
        """
        suggestions_data = self.domain_service.generate_persona_suggestions(
            module=request.module,
            user_level=request.user_level,
            description_keywords=request.description_keywords,
        )

        # Convert to PersonaCreateRequest objects
        suggestions = []
        for suggestion_data in suggestions_data:
            suggestion = PersonaCreateRequest(
                name=suggestion_data["name"],
                description=suggestion_data["description"],
                erpnext_roles=suggestion_data["erpnext_roles"],
                permissions=suggestion_data["permissions"],
            )
            suggestions.append(suggestion)

        return PersonaSuggestionResponse(
            suggestions=suggestions,
            module=request.module,
            user_level=request.user_level,
        )

    async def get_persona_statistics(self) -> PersonaStatsResponse:
        """Get statistics about personas in the system.

        Returns:
            Persona statistics
        """
        stats = await self.persona_repository.get_statistics()

        return PersonaStatsResponse(
            total_personas=stats["total"],
            active_personas=stats["active"],
            inactive_personas=stats["inactive"],
            roles_distribution=stats["roles_distribution"],
            permissions_distribution=stats["permissions_distribution"],
            creation_trend=stats["creation_trend"],
            complexity_metrics=stats["complexity_metrics"],
        )

    async def activate_persona(self, persona_id: UUID) -> PersonaResponse:
        """Activate a persona.

        Args:
            persona_id: Unique persona identifier

        Returns:
            Updated persona response

        Raises:
            PersonaNotFoundError: If persona not found
        """
        persona = await self.persona_repository.find_by_id(persona_id)
        if not persona:
            raise PersonaNotFoundError(str(persona_id))

        persona.activate()

        async with self.unit_of_work:
            saved_persona = await self.persona_repository.save(persona)
            await self.unit_of_work.commit()

        logger.info(f"Activated persona: {persona_id}")
        return self._to_response(saved_persona)

    async def deactivate_persona(self, persona_id: UUID) -> PersonaResponse:
        """Deactivate a persona.

        Args:
            persona_id: Unique persona identifier

        Returns:
            Updated persona response

        Raises:
            PersonaNotFoundError: If persona not found
        """
        persona = await self.persona_repository.find_by_id(persona_id)
        if not persona:
            raise PersonaNotFoundError(str(persona_id))

        persona.deactivate()

        async with self.unit_of_work:
            saved_persona = await self.persona_repository.save(persona)
            await self.unit_of_work.commit()

        logger.info(f"Deactivated persona: {persona_id}")
        return self._to_response(saved_persona)

    async def find_similar_personas(
        self, persona_id: UUID, similarity_threshold: float = 0.7
    ) -> list[PersonaSummaryResponse]:
        """Find personas similar to the given persona.

        Args:
            persona_id: Reference persona identifier
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of similar personas with summary information

        Raises:
            PersonaNotFoundError: If reference persona not found
        """
        persona = await self.persona_repository.find_by_id(persona_id)
        if not persona:
            raise PersonaNotFoundError(str(persona_id))

        # Get all personas for comparison
        all_personas = await self.persona_repository.find_all()

        # Find similar personas using domain service
        similar_results = self.domain_service.find_similar_personas(
            persona, all_personas, similarity_threshold
        )

        # Convert to summary responses
        similar_personas = []
        for result in similar_results:
            similar_persona = result["persona"]
            summary = PersonaSummaryResponse(
                id=similar_persona.id,
                name=similar_persona.name,
                description=similar_persona.description,
                erpnext_roles_count=len(similar_persona.erpnext_roles),
                permissions_count=len(similar_persona.permissions_list),
                is_active=similar_persona.is_active,
                created_at=similar_persona.created_at,
            )
            similar_personas.append(summary)

        return similar_personas

    def _to_response(self, persona: Persona) -> PersonaResponse:
        """Convert persona domain entity to response DTO.

        Args:
            persona: Persona domain entity

        Returns:
            Persona response DTO
        """
        effective_permissions = persona.get_effective_permissions()

        return PersonaResponse(
            id=persona.id,
            name=persona.name,
            description=persona.description,
            erpnext_roles=persona.erpnext_roles_str,
            permissions=persona.permissions,
            is_active=persona.is_active,
            created_at=persona.created_at,
            updated_at=persona.updated_at,
            version=persona.version,
            erpnext_roles_list=persona.erpnext_roles,
            permissions_list=persona.permissions_list,
            effective_permissions_count=len(effective_permissions),
        )

    def _apply_updates(
        self, persona: Persona, request: PersonaUpdateRequest
    ) -> Persona:
        """Apply update request to persona entity.

        Args:
            persona: Current persona entity
            request: Update request

        Returns:
            Updated persona entity
        """
        # Create a copy of the persona to avoid modifying the original
        updated_persona = Persona(
            name=persona.name,
            description=persona.description,
            erpnext_roles=persona.erpnext_roles,
            permissions=persona.permissions,
            is_active=persona.is_active,
            id=persona.id,
            created_at=persona.created_at,
            updated_at=persona.updated_at,
            version=persona.version,
        )

        # Apply updates
        if request.name is not None:
            updated_persona.set_name(request.name)

        if request.description is not None:
            updated_persona.set_description(request.description)

        if request.erpnext_roles is not None:
            roles = [
                role.strip()
                for role in request.erpnext_roles.split(",")
                if role.strip()
            ]
            updated_persona.set_erpnext_roles(roles)

        if request.permissions is not None:
            updated_persona.set_permissions(request.permissions)

        if request.is_active is not None:
            updated_persona.set_is_active(request.is_active)

        return updated_persona

    async def _get_persona_usage_count(self, persona_id: UUID) -> int:
        """Get count of places where persona is used.

        Args:
            persona_id: Persona identifier

        Returns:
            Usage count
        """
        # TODO: Implement when activities and journeys are available
        # This will need to check:
        # - Activities that reference this persona
        # - Journeys that use this persona
        # - Test executions that involve this persona
        return 0
