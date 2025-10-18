"""Activity application service for use cases.

This module implements the application layer service for activities,
coordinating between the domain layer and infrastructure layer to
fulfill activity-related use cases.
"""

import uuid
from typing import Any, Optional, Union

from ...domain.activities.activity import Activity
from ...domain.activities.activity_service import (
    ActivityService as ActivityDomainService,
)
from ...domain.activities.exceptions import (
    ActivityAlreadyExistsError,
    ActivityNotFoundError,
    ActivityPersonaLinkAlreadyExistsError,
    ActivityPersonaLinkNotFoundError,
    ActivityValidationError,
)
from ...domain.personas.exceptions import (
    PersonaNotFoundError,
)
from ..dto.activity_schemas import (
    ActivityBulkLinkRequestDTO,
    ActivityBulkLinkResponseDTO,
    ActivityBulkOperationRequestDTO,
    ActivityBulkOperationResponseDTO,
    ActivityCompatibilityResponseDTO,
    ActivityCreateRequestDTO,
    ActivityFilterDTO,
    ActivityListResponseDTO,
    ActivityPersonaLinkCreateRequestDTO,
    ActivityPersonaLinkResponseDTO,
    ActivityPersonaLinkUpdateRequestDTO,
    ActivityResponseDTO,
    ActivityStatisticsResponseDTO,
    ActivitySuggestionResponseDTO,
    ActivityUpdateRequestDTO,
    PersonaActivityResponseDTO,
)


class ActivityApplicationService:
    """Application service for activity use cases."""

    def __init__(
        self, activity_repository, persona_repository, activity_persona_link_repository
    ):
        """Initialize with repository dependencies."""
        self.activity_repository = activity_repository
        self.persona_repository = persona_repository
        self.activity_persona_link_repository = activity_persona_link_repository
        self.domain_service = ActivityDomainService()

    # Activity CRUD Operations

    async def create_activity(
        self, request: ActivityCreateRequestDTO
    ) -> ActivityResponseDTO:
        """Create a new activity."""
        # Check if activity with same name already exists
        existing = await self.activity_repository.get_by_name(request.name)
        if existing:
            raise ActivityAlreadyExistsError("name", request.name)

        # Create domain entity
        activity = Activity(
            name=request.name,
            description=request.description,
            erpnext_module=request.erpnext_module,
            action_type=request.action_type.value,
            target_doctype=request.target_doctype,
            required_fields=request.required_fields,
            validation_rules=request.validation_rules,
            success_criteria=request.success_criteria,
            complexity_score=request.complexity_score,
            estimated_duration=request.estimated_duration,
            prerequisites=request.prerequisites,
            postconditions=request.postconditions,
            test_data_requirements=request.test_data_requirements,
            tags=request.tags,
            is_active=request.is_active,
        )

        # Validate with domain service
        self.domain_service.validate_activity_creation(activity)

        # Save to repository
        saved_activity = await self.activity_repository.create(activity)

        return self._activity_to_dto(saved_activity)

    async def get_activity_by_id(self, activity_id: Union[str, uuid.UUID]) -> ActivityResponseDTO:
        """Get activity by ID."""
        activity = await self.activity_repository.get_by_id(activity_id)
        if not activity:
            raise ActivityNotFoundError(activity_id)

        return self._activity_to_dto(activity)

    async def update_activity(
        self, activity_id: Union[str, uuid.UUID], request: ActivityUpdateRequestDTO
    ) -> ActivityResponseDTO:
        """Update an existing activity."""
        # Get existing activity
        activity = await self.activity_repository.get_by_id(activity_id)
        if not activity:
            raise ActivityNotFoundError(str(activity_id))

        # Apply updates
        if request.name is not None:
            # Check if new name conflicts with another activity
            existing = await self.activity_repository.get_by_name(request.name)
            if existing and existing.id != activity.id:
                raise ActivityAlreadyExistsError("name", request.name)
            activity.update_name(request.name)

        if request.description is not None:
            activity.update_description(request.description)

        if request.complexity_score is not None:
            activity.update_complexity_score(request.complexity_score)

        if request.estimated_duration is not None:
            activity.update_estimated_duration(request.estimated_duration)

        if request.prerequisites is not None:
            activity.prerequisites = request.prerequisites
            activity._update_metadata()

        if request.postconditions is not None:
            activity.postconditions = request.postconditions
            activity._update_metadata()

        if request.test_data_requirements is not None:
            activity.test_data_requirements = request.test_data_requirements
            activity._update_metadata()

        if request.tags is not None:
            activity.tags = request.tags
            activity._update_metadata()

        if request.is_active is not None:
            if request.is_active:
                activity.activate()
            else:
                activity.deactivate()

        # Validate with domain service
        original_activity = await self.activity_repository.get_by_id(activity_id)
        self.domain_service.validate_activity_update(original_activity, activity)

        # Save updates
        updated_activity = await self.activity_repository.update(activity)

        return self._activity_to_dto(updated_activity)

    async def delete_activity(self, activity_id: Union[str, uuid.UUID]) -> None:
        """Delete an activity."""
        activity = await self.activity_repository.get_by_id(activity_id)
        if not activity:
            raise ActivityNotFoundError(str(activity_id))

        # Remove all persona links first
        await self.activity_persona_link_repository.delete_by_activity_id(activity_id)

        # Delete the activity
        await self.activity_repository.delete(activity_id)

    async def list_activities(
        self,
        filters: Optional[ActivityFilterDTO] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> ActivityListResponseDTO:
        """List activities with filtering and pagination."""
        # Build filter criteria
        filter_criteria = {}
        if filters:
            if filters.erpnext_module:
                filter_criteria["erpnext_module"] = filters.erpnext_module
            if filters.action_type:
                filter_criteria["action_type"] = filters.action_type.value
            if filters.target_doctype:
                filter_criteria["target_doctype"] = filters.target_doctype
            if filters.complexity_score:
                filter_criteria["complexity_score"] = filters.complexity_score
            if filters.is_active is not None:
                filter_criteria["is_active"] = filters.is_active
            if filters.tags:
                filter_criteria["tags_any"] = filters.tags
            if filters.min_duration:
                filter_criteria["min_duration"] = filters.min_duration
            if filters.max_duration:
                filter_criteria["max_duration"] = filters.max_duration
            if filters.search:
                filter_criteria["search"] = filters.search

        # Get paginated results
        activities, total = await self.activity_repository.list_with_filters(
            filter_criteria, page, per_page
        )

        # Convert to DTOs
        activity_dtos = [self._activity_to_dto(activity) for activity in activities]

        return ActivityListResponseDTO(
            activities=activity_dtos,
            total=total,
            page=page,
            per_page=per_page,
            has_next=page * per_page < total,
            has_prev=page > 1,
        )

    async def get_activity_statistics(self) -> ActivityStatisticsResponseDTO:
        """Get comprehensive activity statistics."""
        activities = await self.activity_repository.get_all()
        stats = self.domain_service.calculate_activity_statistics(activities)

        return ActivityStatisticsResponseDTO(**stats)

    async def activate_activity(self, activity_id: Union[str, uuid.UUID]) -> ActivityResponseDTO:
        """Activate an activity."""
        # Convert activity_id to UUID if it's a string
        if isinstance(activity_id, str):
            activity_id = uuid.UUID(activity_id)
        
        activity = await self.activity_repository.get_by_id(activity_id)
        if not activity:
            raise ActivityNotFoundError(str(activity_id))

        activity.activate()
        updated_activity = await self.activity_repository.update(activity)

        return self._activity_to_dto(updated_activity)

    async def deactivate_activity(self, activity_id: Union[str, uuid.UUID]) -> ActivityResponseDTO:
        """Deactivate an activity."""
        # Convert activity_id to UUID if it's a string
        if isinstance(activity_id, str):
            activity_id = uuid.UUID(activity_id)
        
        activity = await self.activity_repository.get_by_id(activity_id)
        if not activity:
            raise ActivityNotFoundError(str(activity_id))

        activity.deactivate()
        updated_activity = await self.activity_repository.update(activity)

        return self._activity_to_dto(updated_activity)

    # Activity-Persona Link Operations

    async def link_activity_to_persona(
        self,
        persona_id: str,
        activity_id: str,
        request: ActivityPersonaLinkCreateRequestDTO,
    ) -> ActivityPersonaLinkResponseDTO:
        """Link an activity to a persona."""
        # Verify persona and activity exist
        persona_id_uuid = persona_id if isinstance(persona_id, uuid.UUID) else uuid.UUID(persona_id)
        persona = self.persona_repository.find_by_id(persona_id_uuid)
        if not persona:
            raise ActivityNotFoundError(
                persona_id
            )  # Using generic error for simplicity

        activity_id_uuid = activity_id if isinstance(activity_id, uuid.UUID) else uuid.UUID(activity_id)
        activity = await self.activity_repository.get_by_id(activity_id_uuid)
        if not activity:
            raise ActivityNotFoundError(activity_id)

        # Check if link already exists
        existing_link = self.activity_persona_link_repository.get_by_ids(
            persona_id_uuid, activity_id_uuid
        )
        if existing_link:
            raise ActivityPersonaLinkAlreadyExistsError(activity_id, persona_id)

        # Create link
        link = self.activity_persona_link_repository.create(
            persona_id=persona_id_uuid,
            activity_id=activity_id_uuid,
            priority=request.priority.value,
            notes=request.notes,
            is_primary=request.is_primary,
            execution_order=request.execution_order,
        )

        return self._link_to_dto(link)

    async def update_activity_persona_link(
        self,
        persona_id: str,
        activity_id: str,
        request: ActivityPersonaLinkUpdateRequestDTO,
    ) -> ActivityPersonaLinkResponseDTO:
        """Update an activity-persona link."""
        link = await self.activity_persona_link_repository.get_by_ids(
            uuid.UUID(persona_id), uuid.UUID(activity_id)
        )
        if not link:
            raise ActivityPersonaLinkNotFoundError(activity_id, persona_id)

        # Apply updates
        if request.priority is not None:
            link.priority = request.priority.value
        if request.notes is not None:
            link.notes = request.notes
        if request.is_primary is not None:
            link.is_primary = request.is_primary
        if request.execution_order is not None:
            link.execution_order = request.execution_order

        updated_link = await self.activity_persona_link_repository.update(link)

        return self._link_to_dto(updated_link)

    async def unlink_activity_from_persona(
        self, persona_id: str, activity_id: str
    ) -> None:
        """Unlink an activity from a persona."""
        persona_id_uuid = persona_id if isinstance(persona_id, uuid.UUID) else uuid.UUID(persona_id)
        activity_id_uuid = activity_id if isinstance(activity_id, uuid.UUID) else uuid.UUID(activity_id)
        
        link = self.activity_persona_link_repository.get_by_ids(
            persona_id_uuid, activity_id_uuid
        )
        if not link:
            raise ActivityPersonaLinkNotFoundError(activity_id, persona_id)

        await self.activity_persona_link_repository.delete_by_ids(
            persona_id_uuid, activity_id_uuid
        )

    async def get_persona_activities(
        self,
        persona_id: str,
        priority_filter: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> ActivityListResponseDTO:
        """Get activities linked to a persona."""
        # Verify persona exists
        print(f"DEBUG: Looking for persona with id: {persona_id}")
        persona = await self.persona_repository.find_by_id(uuid.UUID(persona_id))
        print(f"DEBUG: Found persona: {persona}")
        if not persona:
            raise PersonaNotFoundError(persona_id)

        # Get linked activities
        links = await self.activity_persona_link_repository.get_by_persona_id(
            uuid.UUID(persona_id), priority_filter, page, per_page
        )

        # Get activities and convert to DTOs
        persona_activities = []
        for link in links:
            activity = await self.activity_repository.get_by_id(link.activity_id)
            if activity:
                persona_activities.append(
                    PersonaActivityResponseDTO(
                        activity=self._activity_to_dto(activity),
                        link=self._link_to_dto(link),
                    )
                )

        # Get total count
        total = await self.activity_persona_link_repository.count_by_persona_id(
            uuid.UUID(persona_id), priority_filter
        )

        return ActivityListResponseDTO(
            activities=[item.activity for item in persona_activities],
            total=total,
            page=page,
            per_page=per_page,
            has_next=page * per_page < total,
            has_prev=page > 1,
        )

    async def get_activity_personas(
        self, activity_id: str, page: int = 1, per_page: int = 20
    ) -> ActivityListResponseDTO:
        """Get personas linked to an activity."""
        # Verify activity exists
        activity = await self.activity_repository.get_by_id(uuid.UUID(activity_id))
        if not activity:
            raise ActivityNotFoundError(activity_id)

        # Get linked personas
        links = await self.activity_persona_link_repository.get_by_activity_id(
            uuid.UUID(activity_id), page, per_page
        )

        # Get personas and convert to DTOs
        activity_personas = []
        for link in links:
            persona = await self.persona_repository.find_by_id(link.persona_id)
            if persona:
                activity_personas.append(
                    {
                        "persona": persona.to_dict(),  # Assuming persona has to_dict method
                        "link": self._link_to_dto(link),
                    }
                )

        # Get total count
        total = await self.activity_persona_link_repository.count_by_activity_id(
            uuid.UUID(activity_id)
        )

        return ActivityListResponseDTO(
            items=activity_personas,
            total=total,
            page=page,
            per_page=per_page,
            has_next=page * per_page < total,
            has_prev=page > 1,
        )

    # Compatibility and Suggestions

    async def check_activity_compatibility(
        self, activity1_id: str, activity2_id: str
    ) -> ActivityCompatibilityResponseDTO:
        """Check compatibility between two activities."""
        activity1 = await self.activity_repository.get_by_id(uuid.UUID(activity1_id))
        if not activity1:
            raise ActivityNotFoundError(activity1_id)

        activity2 = await self.activity_repository.get_by_id(uuid.UUID(activity2_id))
        if not activity2:
            raise ActivityNotFoundError(activity2_id)

        compatibility = self.domain_service.calculate_activity_compatibility(
            activity1, activity2
        )

        return ActivityCompatibilityResponseDTO(
            is_compatible=compatibility.is_compatible,
            compatibility_score=compatibility.compatibility_score,
            reasons=compatibility.reasons,
            suggestions=compatibility.suggestions,
            confidence=compatibility.confidence,
        )

    async def get_similar_activities(
        self, activity_id: Union[str, uuid.UUID], limit: int = 10, min_similarity: float = 0.6
    ) -> list[dict[str, Any]]:
        """Find activities similar to the given activity."""
        # Convert to UUID if it's a string
        if isinstance(activity_id, str):
            activity_id = uuid.UUID(activity_id)
        
        target_activity = await self.activity_repository.get_by_id(activity_id)
        if not target_activity:
            raise ActivityNotFoundError(activity_id)

        all_activities = await self.activity_repository.get_all()
        similar_activities = self.domain_service.find_similar_activities(
            target_activity, all_activities, min_similarity
        )

        # Limit results
        similar_activities = similar_activities[:limit]

        # Convert to DTOs
        result = []
        for item in similar_activities:
            result.append(
                {
                    "activity": self._activity_to_dto(item["activity"]),
                    "similarity": item["similarity"],
                    "similarity_factors": item["similarity_factors"],
                }
            )

        return result

    async def suggest_activities(
        self,
        context: str,
        erpnext_modules: list[str],
        persona_roles: Optional[list[str]] = None,
    ) -> list[ActivitySuggestionResponseDTO]:
        """Suggest activities based on context and requirements."""
        suggestions = self.domain_service.generate_activity_suggestions(
            context, erpnext_modules, persona_roles
        )

        # Convert to DTOs
        return [
            ActivitySuggestionResponseDTO(**suggestion) for suggestion in suggestions
        ]

    # Bulk Operations

    async def bulk_activity_operation(
        self, request: ActivityBulkOperationRequestDTO
    ) -> ActivityBulkOperationResponseDTO:
        """Perform bulk operations on activities."""
        updated_ids = []
        failed_ids = []
        errors = []

        for activity_id in request.activity_ids:
            try:
                if request.action == "activate":
                    await self.activate_activity(activity_id)
                elif request.action == "deactivate":
                    await self.deactivate_activity(activity_id)
                elif request.action == "delete":
                    await self.delete_activity(activity_id)

                updated_ids.append(activity_id)

            except Exception as e:
                failed_ids.append(activity_id)
                errors.append(f"Activity {activity_id}: {str(e)}")

        return ActivityBulkOperationResponseDTO(
            updated_count=len(updated_ids),
            updated_ids=updated_ids,
            failed_count=len(failed_ids),
            failed_ids=failed_ids,
            errors=errors,
        )

    async def bulk_link_activities(
        self, persona_id: str, request: ActivityBulkLinkRequestDTO
    ) -> ActivityBulkLinkResponseDTO:
        """Bulk link activities to a persona."""
        linked_activities = []
        failed_activities = []
        errors = []

        for activity_id in request.activity_ids:
            try:
                link_request = ActivityPersonaLinkCreateRequestDTO(
                    priority=request.priority, notes=request.notes
                )
                await self.link_activity_to_persona(
                    persona_id, activity_id, link_request
                )
                linked_activities.append(activity_id)

            except Exception as e:
                failed_activities.append(activity_id)
                errors.append(f"Activity {activity_id}: {str(e)}")

        return ActivityBulkLinkResponseDTO(
            linked_count=len(linked_activities),
            linked_activities=linked_activities,
            failed_count=len(failed_activities),
            failed_activities=failed_activities,
            errors=errors,
        )

    async def validate_activity(self, activity_id: Union[str, uuid.UUID]) -> dict[str, Any]:
        """Validate activity configuration and return validation results."""
        try:
            activity = await self.activity_repository.get_by_id(activity_id)
            if not activity:
                raise ActivityNotFoundError(f"Activity with ID {activity_id} not found")
            
            return self.domain_service.validate_activity_configuration(activity)
        except ActivityNotFoundError:
            raise
        except Exception as e:
            raise ActivityValidationError("validation", f"Validation failed: {str(e)}")

    # Private helper methods

    def _activity_to_dto(self, activity: Activity) -> ActivityResponseDTO:
        """Convert Activity entity to DTO."""
        # Convert semantic version string (x.y.z) to integer (x)
        version_int = int(activity.version.split('.')[0]) if activity.version else 1
        
        return ActivityResponseDTO(
            id=str(activity.id),
            name=activity.name,
            description=activity.description,
            erpnext_module=activity.erpnext_module,
            action_type=activity.action_type,
            target_doctype=activity.target_doctype,
            required_fields=activity.required_fields,
            validation_rules=activity.validation_rules,
            success_criteria=activity.success_criteria,
            complexity_score=activity.complexity_score,
            estimated_duration=activity.estimated_duration,
            prerequisites=activity.prerequisites,
            postconditions=activity.postconditions,
            test_data_requirements=activity.test_data_requirements,
            tags=activity.tags,
            is_active=activity.is_active,
            version=version_int,
            created_at=activity.created_at,
            updated_at=activity.updated_at,
        )

    def _link_to_dto(self, link) -> ActivityPersonaLinkResponseDTO:
        """Convert link entity to DTO."""
        return ActivityPersonaLinkResponseDTO(
            persona_id=str(link.persona_id),
            activity_id=str(link.activity_id),
            priority=link.priority,
            notes=link.notes,
            is_primary=link.is_primary,
            execution_order=link.execution_order,
            created_at=link.created_at,
            updated_at=link.updated_at,
        )
