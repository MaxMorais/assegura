"""
Journey Service - Application Layer

This module implements the JourneyService for managing journey use cases
and business logic in the ERPNext test automation framework. It coordinates
between the domain layer and infrastructure layer, handling journey CRUD
operations, validation, and business workflows.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID

from src.application.dto.base_schemas import PaginatedResponse
from src.application.dto.journey_schemas import (
    ActionsSummarySchema,
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
from src.domain.journeys.enhanced_journey import (
    ActionStepEnhanced,
    EnhancedJourney,
    JourneyExecutionStatus,
)
from src.domain.journeys.journey_action_service import (
    JourneyActionService,
)
from src.domain.journeys.journey_validation_error import JourneyValidationError
from src.domain.journeys.journey_validator import JourneyValidator


class JourneyRepositoryInterface(ABC):
    """Abstract interface for journey data persistence."""

    @abstractmethod
    async def create(self, journey: EnhancedJourney) -> EnhancedJourney:
        """Create a new journey."""
        pass

    @abstractmethod
    async def get_by_id(self, journey_id: UUID) -> Optional[EnhancedJourney]:
        """Get journey by ID."""
        pass

    @abstractmethod
    async def get_by_persona_and_activity(
        self, persona_id: UUID, activity_id: UUID
    ) -> list[EnhancedJourney]:
        """Get journeys by persona and activity."""
        pass

    @abstractmethod
    async def list_journeys(
        self,
        filters: Optional[JourneyFilterSchema] = None,
        sort: Optional[JourneySortSchema] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[EnhancedJourney], int]:
        """List journeys with filtering, sorting and pagination."""
        pass

    @abstractmethod
    async def update(self, journey: EnhancedJourney) -> EnhancedJourney:
        """Update existing journey."""
        pass

    @abstractmethod
    async def delete(self, journey_id: UUID) -> bool:
        """Delete journey."""
        pass

    @abstractmethod
    async def get_journey_stats(self) -> dict[str, Any]:
        """Get journey statistics."""
        pass

    @abstractmethod
    async def bulk_update_status(
        self, journey_ids: list[UUID], status: JourneyExecutionStatus
    ) -> dict[UUID, bool]:
        """Bulk update journey execution status."""
        pass


class PersonaServiceInterface(ABC):
    """Interface for persona service operations."""

    @abstractmethod
    async def exists(self, persona_id: UUID) -> bool:
        """Check if persona exists."""
        pass

    @abstractmethod
    async def get_persona_info(self, persona_id: UUID) -> Optional[dict[str, Any]]:
        """Get persona information."""
        pass


class ActivityServiceInterface(ABC):
    """Interface for activity service operations."""

    @abstractmethod
    async def exists(self, activity_id: UUID) -> bool:
        """Check if activity exists."""
        pass

    @abstractmethod
    async def get_activity_info(self, activity_id: UUID) -> Optional[dict[str, Any]]:
        """Get activity information."""
        pass


class JourneyServiceError(Exception):
    """Base exception for journey service errors."""

    pass


class JourneyNotFoundError(JourneyServiceError):
    """Journey not found error."""

    pass


class JourneyValidationServiceError(JourneyServiceError):
    """Journey validation error."""

    pass


class JourneyService:
    """Service for managing journey operations and business logic."""

    def __init__(
        self,
        journey_repository: JourneyRepositoryInterface,
        journey_action_service: JourneyActionService,
        persona_service: PersonaServiceInterface,
        activity_service: ActivityServiceInterface,
    ):
        self.journey_repository = journey_repository
        self.journey_action_service = journey_action_service
        self.persona_service = persona_service
        self.activity_service = activity_service
        self.validator = JourneyValidator()
        self._journey_templates: dict[str, JourneyTemplateSchema] = {}

    async def create_journey(
        self, journey_data: JourneyCreateSchema
    ) -> JourneyResponseSchema:
        """
        Create a new journey with validation.

        Args:
            journey_data: Journey creation data

        Returns:
            Created journey response

        Raises:
            JourneyValidationServiceError: If validation fails
            JourneyServiceError: If creation fails
        """
        try:
            # Validate persona and activity exist
            if not await self.persona_service.exists(journey_data.persona_id):
                raise JourneyValidationServiceError(
                    f"Persona {journey_data.persona_id} does not exist"
                )

            if not await self.activity_service.exists(journey_data.activity_id):
                raise JourneyValidationServiceError(
                    f"Activity {journey_data.activity_id} does not exist"
                )

            # Create enhanced journey
            journey = EnhancedJourney.create_enhanced(
                name=journey_data.name,
                description=journey_data.description,
                persona_id=journey_data.persona_id,
                activity_id=journey_data.activity_id,
                estimated_duration_minutes=journey_data.estimated_duration_minutes,
                complexity_level=journey_data.complexity_level.value,
                prerequisites=journey_data.prerequisites,
                expected_outcomes=journey_data.expected_outcomes,
                metadata=journey_data.metadata,
            )

            # Add initial steps if provided
            if journey_data.steps:
                for step_data in journey_data.steps:
                    await self._add_step_to_journey(journey, step_data)

            # Validate journey
            validation_errors = await self._validate_journey_comprehensive(journey)
            if validation_errors:
                raise JourneyValidationServiceError(
                    f"Journey validation failed: {validation_errors}"
                )

            # Save to repository
            saved_journey = await self.journey_repository.create(journey)

            return await self._convert_to_response_schema(saved_journey)

        except JourneyValidationError as e:
            raise JourneyValidationServiceError(str(e))
        except Exception as e:
            raise JourneyServiceError(f"Failed to create journey: {str(e)}")

    async def get_journey(
        self, journey_id: UUID, include_details: bool = True
    ) -> JourneyResponseSchema:
        """
        Get journey by ID with optional detailed information.

        Args:
            journey_id: Journey ID
            include_details: Whether to include execution plan and validation

        Returns:
            Journey response

        Raises:
            JourneyNotFoundError: If journey not found
        """
        journey = await self.journey_repository.get_by_id(journey_id)
        if not journey:
            raise JourneyNotFoundError(f"Journey {journey_id} not found")

        return await self._convert_to_response_schema(journey, include_details)

    async def list_journeys(
        self,
        filters: Optional[JourneyFilterSchema] = None,
        sort: Optional[JourneySortSchema] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> PaginatedResponse[JourneyListItemSchema]:
        """
        List journeys with filtering, sorting and pagination.

        Args:
            filters: Filter criteria
            sort: Sort criteria
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            Paginated journey list
        """
        try:
            journeys, total_count = await self.journey_repository.list_journeys(
                filters, sort, offset, limit
            )

            items = [
                await self._convert_to_list_item_schema(journey) for journey in journeys
            ]

            return PaginatedResponse(
                items=items,
                total_count=total_count,
                offset=offset,
                limit=limit,
                has_next=offset + limit < total_count,
            )

        except Exception as e:
            raise JourneyServiceError(f"Failed to list journeys: {str(e)}")

    async def update_journey(
        self, journey_id: UUID, update_data: JourneyUpdateSchema
    ) -> JourneyResponseSchema:
        """
        Update journey details.

        Args:
            journey_id: Journey ID
            update_data: Update data

        Returns:
            Updated journey response

        Raises:
            JourneyNotFoundError: If journey not found
            JourneyValidationServiceError: If validation fails
        """
        try:
            journey = await self.journey_repository.get_by_id(journey_id)
            if not journey:
                raise JourneyNotFoundError(f"Journey {journey_id} not found")

            # Apply updates
            if update_data.name is not None:
                journey.update_details(name=update_data.name)
            if update_data.description is not None:
                journey.update_details(description=update_data.description)
            if update_data.is_active is not None:
                journey.update_details(is_active=update_data.is_active)
            if update_data.estimated_duration_minutes is not None:
                journey.update_details(
                    estimated_duration_minutes=update_data.estimated_duration_minutes
                )
            if update_data.complexity_level is not None:
                journey.update_details(
                    complexity_level=update_data.complexity_level.value
                )

            if update_data.prerequisites is not None:
                journey.update_prerequisites(update_data.prerequisites)
            if update_data.expected_outcomes is not None:
                journey.update_expected_outcomes(update_data.expected_outcomes)
            if update_data.metadata is not None:
                journey.update_metadata(update_data.metadata)

            # Validate updated journey
            validation_errors = await self._validate_journey_comprehensive(journey)
            if validation_errors:
                raise JourneyValidationServiceError(
                    f"Journey validation failed: {validation_errors}"
                )

            # Save updates
            updated_journey = await self.journey_repository.update(journey)

            return await self._convert_to_response_schema(updated_journey)

        except JourneyValidationError as e:
            raise JourneyValidationServiceError(str(e))
        except JourneyNotFoundError:
            raise
        except Exception as e:
            raise JourneyServiceError(f"Failed to update journey: {str(e)}")

    async def update_journey_associations(
        self, journey_id: UUID, association_data: JourneyAssociationUpdateSchema
    ) -> JourneyResponseSchema:
        """Update journey persona and activity associations."""
        try:
            journey = await self.journey_repository.get_by_id(journey_id)
            if not journey:
                raise JourneyNotFoundError(f"Journey {journey_id} not found")

            # Validate new associations exist
            if association_data.persona_id:
                if not await self.persona_service.exists(association_data.persona_id):
                    raise JourneyValidationServiceError(
                        f"Persona {association_data.persona_id} does not exist"
                    )

            if association_data.activity_id:
                if not await self.activity_service.exists(association_data.activity_id):
                    raise JourneyValidationServiceError(
                        f"Activity {association_data.activity_id} does not exist"
                    )

            # Update associations
            journey.update_associations(
                persona_id=association_data.persona_id,
                activity_id=association_data.activity_id,
            )

            # Save updates
            updated_journey = await self.journey_repository.update(journey)

            return await self._convert_to_response_schema(updated_journey)

        except JourneyValidationError as e:
            raise JourneyValidationServiceError(str(e))
        except JourneyNotFoundError:
            raise
        except Exception as e:
            raise JourneyServiceError(
                f"Failed to update journey associations: {str(e)}"
            )

    async def delete_journey(self, journey_id: UUID) -> bool:
        """
        Delete journey.

        Args:
            journey_id: Journey ID

        Returns:
            True if deleted successfully

        Raises:
            JourneyNotFoundError: If journey not found
        """
        try:
            # Verify journey exists
            journey = await self.journey_repository.get_by_id(journey_id)
            if not journey:
                raise JourneyNotFoundError(f"Journey {journey_id} not found")

            # Check if journey can be deleted (not running)
            if journey.execution_status in [
                JourneyExecutionStatus.RUNNING,
                JourneyExecutionStatus.SUSPENDED,
            ]:
                raise JourneyServiceError("Cannot delete running or suspended journey")

            return await self.journey_repository.delete(journey_id)

        except JourneyNotFoundError:
            raise
        except Exception as e:
            raise JourneyServiceError(f"Failed to delete journey: {str(e)}")

    async def add_journey_step(
        self, journey_id: UUID, step_data: JourneyStepCreateSchema
    ) -> ActionStepSchema:
        """Add a step to journey."""
        try:
            journey = await self.journey_repository.get_by_id(journey_id)
            if not journey:
                raise JourneyNotFoundError(f"Journey {journey_id} not found")

            # Add step using journey action service
            added_step = await self.journey_action_service.add_action_to_journey(
                journey=journey,
                action_id=step_data.action_id,
                parameters=step_data.parameters,
                position=step_data.step_number,
                step_customization={
                    "step_description": step_data.step_description,
                    "timeout_override": step_data.timeout_override,
                    "retry_override": step_data.retry_override,
                    "depends_on_steps": step_data.depends_on_steps,
                    "can_run_parallel": step_data.can_run_parallel,
                    "is_critical": step_data.is_critical,
                },
            )

            # Save updated journey
            await self.journey_repository.update(journey)

            return await self._convert_step_to_schema(added_step)

        except JourneyValidationError as e:
            raise JourneyValidationServiceError(str(e))
        except JourneyNotFoundError:
            raise
        except Exception as e:
            raise JourneyServiceError(f"Failed to add journey step: {str(e)}")

    async def update_journey_step(
        self, journey_id: UUID, step_number: int, step_data: JourneyStepUpdateSchema
    ) -> ActionStepSchema:
        """Update a journey step."""
        try:
            journey = await self.journey_repository.get_by_id(journey_id)
            if not journey:
                raise JourneyNotFoundError(f"Journey {journey_id} not found")

            # Update step parameters if provided
            if step_data.parameters is not None:
                journey.update_step_parameters(step_number, step_data.parameters)

            # Update other step properties
            if step_number <= len(journey.enhanced_steps):
                step = journey.enhanced_steps[step_number - 1]

                if step_data.step_description is not None:
                    step.step_description = step_data.step_description
                if step_data.expected_outputs is not None:
                    step.expected_outputs = step_data.expected_outputs
                if step_data.timeout_override is not None:
                    step.timeout_override = step_data.timeout_override
                if step_data.retry_override is not None:
                    step.retry_override = step_data.retry_override
                if step_data.can_run_parallel is not None:
                    step.can_run_parallel = step_data.can_run_parallel
                if step_data.is_critical is not None:
                    step.is_critical = step_data.is_critical

            # Save updated journey
            await self.journey_repository.update(journey)

            return await self._convert_step_to_schema(
                journey.enhanced_steps[step_number - 1]
            )

        except JourneyValidationError as e:
            raise JourneyValidationServiceError(str(e))
        except JourneyNotFoundError:
            raise
        except Exception as e:
            raise JourneyServiceError(f"Failed to update journey step: {str(e)}")

    async def remove_journey_step(self, journey_id: UUID, step_number: int) -> bool:
        """Remove a step from journey."""
        try:
            journey = await self.journey_repository.get_by_id(journey_id)
            if not journey:
                raise JourneyNotFoundError(f"Journey {journey_id} not found")

            # Remove step
            journey.remove_enhanced_step(step_number)

            # Save updated journey
            await self.journey_repository.update(journey)

            return True

        except JourneyValidationError as e:
            raise JourneyValidationServiceError(str(e))
        except JourneyNotFoundError:
            raise
        except Exception as e:
            raise JourneyServiceError(f"Failed to remove journey step: {str(e)}")

    async def validate_journey(self, journey_id: UUID) -> JourneyValidationSchema:
        """Get comprehensive journey validation results."""
        try:
            journey = await self.journey_repository.get_by_id(journey_id)
            if not journey:
                raise JourneyNotFoundError(f"Journey {journey_id} not found")

            # Run validation
            validation_results = (
                await self.journey_action_service.validate_journey_with_actions(journey)
            )
            summary = self.validator.get_validation_summary(journey)

            return JourneyValidationSchema(**summary)

        except JourneyNotFoundError:
            raise
        except Exception as e:
            raise JourneyServiceError(f"Failed to validate journey: {str(e)}")

    async def generate_execution_plan(
        self, journey_id: UUID
    ) -> JourneyExecutionPlanSchema:
        """Generate execution plan for journey."""
        try:
            journey = await self.journey_repository.get_by_id(journey_id)
            if not journey:
                raise JourneyNotFoundError(f"Journey {journey_id} not found")

            # Generate execution plan
            plan_data = await self.journey_action_service.get_journey_execution_plan(
                journey
            )

            return JourneyExecutionPlanSchema(**plan_data["plan"])

        except JourneyNotFoundError:
            raise
        except Exception as e:
            raise JourneyServiceError(f"Failed to generate execution plan: {str(e)}")

    async def prepare_journey_for_execution(self, journey_id: UUID) -> bool:
        """Prepare journey for execution and validate readiness."""
        try:
            journey = await self.journey_repository.get_by_id(journey_id)
            if not journey:
                raise JourneyNotFoundError(f"Journey {journey_id} not found")

            # Prepare journey for execution
            is_ready = journey.prepare_for_execution()

            if is_ready:
                # Save updated journey with execution plan
                await self.journey_repository.update(journey)

            return is_ready

        except JourneyNotFoundError:
            raise
        except Exception as e:
            raise JourneyServiceError(
                f"Failed to prepare journey for execution: {str(e)}"
            )

    async def bulk_operation(
        self, operation_data: JourneyBulkOperationSchema
    ) -> JourneyBulkResultSchema:
        """Execute bulk operations on journeys."""
        successful_ids = []
        failed_ids = []
        errors = {}

        try:
            for journey_id in operation_data.journey_ids:
                try:
                    if operation_data.operation == "activate":
                        await self.update_journey(
                            journey_id, JourneyUpdateSchema(is_active=True)
                        )
                        successful_ids.append(journey_id)
                    elif operation_data.operation == "deactivate":
                        await self.update_journey(
                            journey_id, JourneyUpdateSchema(is_active=False)
                        )
                        successful_ids.append(journey_id)
                    elif operation_data.operation == "delete":
                        await self.delete_journey(journey_id)
                        successful_ids.append(journey_id)
                    elif operation_data.operation == "execute":
                        # Prepare for execution (actual execution would be handled by execution service)
                        await self.prepare_journey_for_execution(journey_id)
                        successful_ids.append(journey_id)
                    else:
                        failed_ids.append(journey_id)
                        errors[
                            str(journey_id)
                        ] = f"Unsupported operation: {operation_data.operation}"

                except Exception as e:
                    failed_ids.append(journey_id)
                    errors[str(journey_id)] = str(e)

            return JourneyBulkResultSchema(
                successful_ids=successful_ids,
                failed_ids=failed_ids,
                errors=errors,
                total_processed=len(operation_data.journey_ids),
            )

        except Exception as e:
            raise JourneyServiceError(f"Bulk operation failed: {str(e)}")

    async def get_journey_statistics(self) -> JourneyStatsSchema:
        """Get journey statistics."""
        try:
            stats_data = await self.journey_repository.get_journey_stats()
            return JourneyStatsSchema(**stats_data)

        except Exception as e:
            raise JourneyServiceError(f"Failed to get journey statistics: {str(e)}")

    async def create_journey_template(
        self, template_data: JourneyTemplateSchema
    ) -> str:
        """Create a reusable journey template."""
        try:
            self._journey_templates[template_data.template_name] = template_data
            return template_data.template_name

        except Exception as e:
            raise JourneyServiceError(f"Failed to create journey template: {str(e)}")

    async def create_journey_from_template(
        self, template_data: JourneyFromTemplateSchema
    ) -> JourneyResponseSchema:
        """Create journey from template."""
        try:
            if template_data.template_name not in self._journey_templates:
                raise JourneyServiceError(
                    f"Template '{template_data.template_name}' not found"
                )

            template = self._journey_templates[template_data.template_name]

            # Apply parameter values to template
            journey_data = template.journey_template.copy()

            # Apply parameter substitutions
            for param_key, param_value in template_data.parameter_values.items():
                if param_key in template.parameter_placeholders:
                    # Substitute in journey data (simplified - real implementation would be more sophisticated)
                    pass

            # Apply any overrides
            if template_data.journey_overrides:
                overrides_dict = template_data.journey_overrides.dict(exclude_none=True)
                journey_dict = journey_data.dict()
                journey_dict.update(overrides_dict)
                journey_data = JourneyCreateSchema(**journey_dict)

            return await self.create_journey(journey_data)

        except Exception as e:
            raise JourneyServiceError(
                f"Failed to create journey from template: {str(e)}"
            )

    # Private helper methods

    async def _add_step_to_journey(
        self, journey: EnhancedJourney, step_data: JourneyStepCreateSchema
    ) -> None:
        """Add step to journey using journey action service."""
        if self.journey_action_service is None:
            raise JourneyServiceError("Journey action service not available for step management")
        
        await self.journey_action_service.add_action_to_journey(
            journey=journey,
            action_id=step_data.action_id,
            parameters=step_data.parameters,
            position=step_data.step_number,
            step_customization={
                "step_description": step_data.step_description,
                "timeout_override": step_data.timeout_override,
                "retry_override": step_data.retry_override,
                "depends_on_steps": step_data.depends_on_steps,
                "can_run_parallel": step_data.can_run_parallel,
                "is_critical": step_data.is_critical,
            },
        )

    async def _validate_journey_comprehensive(
        self, journey: EnhancedJourney
    ) -> list[str]:
        """Run comprehensive journey validation."""
        if self.journey_action_service is None:
            # Skip validation if journey action service is not available
            return []
        
        validation_results = (
            await self.journey_action_service.validate_journey_with_actions(journey)
        )
        return [result.message for result in validation_results if result.is_blocking]

    async def _convert_to_response_schema(
        self, journey: EnhancedJourney, include_details: bool = True
    ) -> JourneyResponseSchema:
        """Convert journey to response schema."""

        # Convert steps
        steps = [
            await self._convert_step_to_schema(step) for step in journey.enhanced_steps
        ]

        # Prepare response data
        response_data = {
            "id": journey.id,
            "name": journey.name,
            "description": journey.description,
            "persona_id": journey.persona_id,
            "activity_id": journey.activity_id,
            "execution_status": journey.execution_status.value,
            "is_active": journey.is_active,
            "estimated_duration_minutes": journey.estimated_duration_minutes,
            "complexity_level": journey.complexity_level,
            "prerequisites": journey.prerequisites,
            "expected_outcomes": journey.expected_outcomes,
            "metadata": journey.metadata,
            "steps": steps,
            "step_count": journey.step_count,
            "has_given_steps": journey.has_given_steps,
            "has_when_steps": journey.has_when_steps,
            "has_then_steps": journey.has_then_steps,
            "is_complete_scenario": journey.is_complete_scenario,
            "created_at": journey.created_at,
            "updated_at": journey.updated_at,
            "version": journey.version,
        }

        if include_details:
            # Add execution plan
            if journey.execution_plan:
                plan_data = {
                    "total_steps": journey.execution_plan.total_steps,
                    "estimated_duration_seconds": journey.execution_plan.estimated_duration.total_seconds(),
                    "complexity_score": journey.execution_plan.complexity_score,
                    "can_parallelize": journey.execution_plan.can_execute_parallel,
                    "parallel_sections": journey.execution_plan.parallel_executable_steps,
                    "critical_path": journey.execution_plan.critical_path_steps,
                    "rollback_points": journey.execution_plan.rollback_points,
                    "resource_requirements": journey.execution_plan.resource_requirements,
                }
                response_data["execution_plan"] = JourneyExecutionPlanSchema(
                    **plan_data
                )

            # Add actions summary
            actions_summary = journey.get_actions_summary()
            if actions_summary:
                response_data["actions_summary"] = ActionsSummarySchema(
                    **actions_summary
                )

            # Add validation errors if any
            validation_errors = journey.get_validation_errors()
            if validation_errors:
                response_data["validation_errors"] = validation_errors

        return JourneyResponseSchema(**response_data)

    async def _convert_to_list_item_schema(
        self, journey: EnhancedJourney
    ) -> JourneyListItemSchema:
        """Convert journey to list item schema."""
        return JourneyListItemSchema(
            id=journey.id,
            name=journey.name,
            description=journey.description,
            persona_id=journey.persona_id,
            activity_id=journey.activity_id,
            execution_status=journey.execution_status.value,
            complexity_level=journey.complexity_level,
            step_count=journey.step_count,
            estimated_duration_minutes=journey.estimated_duration_minutes,
            is_active=journey.is_active,
            is_complete_scenario=journey.is_complete_scenario,
            created_at=journey.created_at,
            updated_at=journey.updated_at,
        )

    async def _convert_step_to_schema(
        self, step: ActionStepEnhanced
    ) -> ActionStepSchema:
        """Convert enhanced step to action step schema."""
        return ActionStepSchema(
            step_number=step.step_number,
            action_id=step.action.action_id,
            action_name=step.action.name,
            action_type=step.action.action_type.value,
            step_description=step.step_description or step.action.description,
            parameters=step.parameters,
            expected_outputs=step.expected_outputs,
            timeout_override=step.timeout_override,
            retry_override=step.retry_override,
            depends_on_steps=step.depends_on_steps,
            can_run_parallel=step.can_run_parallel,
            is_critical=step.is_critical,
        )
