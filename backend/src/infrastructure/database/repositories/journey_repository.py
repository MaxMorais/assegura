"""
Journey Repository - Infrastructure Layer

This module implements the JourneyRepository using SQLAlchemy ORM for managing
journey data persistence in the ERPNext test automation framework. It provides
comprehensive CRUD operations, complex queries, filtering, sorting, and
relationship management with the database.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, or_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from src.application.dto.journey_schemas import JourneyFilterSchema, JourneySortSchema
from src.application.services.journey_service import JourneyRepositoryInterface
from src.domain.actions.action_library import Action, ActionType, ImplementationType
from src.domain.journeys.enhanced_journey import (
    ActionStepEnhanced,
    EnhancedJourney,
    JourneyExecutionPlan,
    JourneyExecutionStatus,
)
from src.infrastructure.database.models.action_library_models import ActionLibraryModel
from src.infrastructure.database.models.journey_models import (
    JourneyExecutionPlanModel,
    JourneyModel,
    JourneyStepModel,
)
from src.infrastructure.database.repositories.base import BaseRepository


class JourneyRepositoryError(Exception):
    """Base exception for journey repository operations."""

    pass


class JourneyRepository(BaseRepository, JourneyRepositoryInterface):
    """SQLAlchemy implementation of journey repository."""

    def __init__(self, db_session: Session):
        super().__init__(db_session, JourneyModel)

    def _entity_to_model(self, entity: EnhancedJourney) -> JourneyModel:
        """Convert EnhancedJourney entity to JourneyModel."""
        return self._convert_domain_to_model(entity)

    def _model_to_entity(self, model: JourneyModel) -> EnhancedJourney:
        """Convert JourneyModel to EnhancedJourney entity."""
        # For synchronous conversion, we'll create a basic journey without async loading
        # This is a simplified version for the base repository methods
        from src.domain.journeys.enhanced_journey import EnhancedJourney, JourneyExecutionStatus
        
        # Create basic journey without loading related data
        journey = EnhancedJourney(
            id=model.id,
            name=model.name,
            description=model.description,
            persona_id=model.persona_id,
            activity_id=model.activity_id,
            execution_status=JourneyExecutionStatus(model.execution_status or "draft"),
            is_active=model.is_active,
            estimated_duration_minutes=model.estimated_duration_minutes,
            complexity_level=model.complexity_level,
            prerequisites=model.prerequisites or [],
            expected_outcomes=model.expected_outcomes or [],
            metadata=model.journey_metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
        
        return journey

    async def create(self, journey: EnhancedJourney) -> EnhancedJourney:
        """
        Create a new journey in the database.

        Args:
            journey: Enhanced journey domain object

        Returns:
            Created journey with database ID

        Raises:
            JourneyRepositoryError: If creation fails
        """
        try:
            # Convert domain object to database model
            journey_model = self._convert_domain_to_model(journey)

            # Add to session and flush to get ID
            self.session.add(journey_model)
            self.session.flush()

            print(f"DEBUG: Journey model created with ID: {journey_model.id}")

            # Create journey steps
            if journey.enhanced_steps:
                for step in journey.enhanced_steps:
                    step_model = self._convert_step_to_model(step, journey_model.id)
                    self.session.add(step_model)

            # Create execution plan if present
            if journey.execution_plan:
                plan_model = self._convert_execution_plan_to_model(
                    journey.execution_plan, journey_model.id
                )
                self.session.add(plan_model)

            # Commit transaction
            self.session.commit()
            print(f"DEBUG: Journey committed to database with ID: {journey_model.id}")

            # Debug: Verify journey is actually in database after commit
            verify_query = self.session.query(JourneyModel).filter(JourneyModel.id == journey_model.id)
            verify_result = verify_query.first()
            print(f"DEBUG: Verification query result after commit: {verify_result}")

            # Refresh and return converted domain object
            self.session.refresh(journey_model)
            return await self._convert_model_to_domain(journey_model)

        except IntegrityError as e:
            self.session.rollback()
            raise JourneyRepositoryError(
                f"Journey creation failed due to constraint violation: {str(e)}"
            )
        except SQLAlchemyError as e:
            self.session.rollback()
            raise JourneyRepositoryError(
                f"Database error during journey creation: {str(e)}"
            )
        except Exception as e:
            self.session.rollback()
            raise JourneyRepositoryError(
                f"Unexpected error during journey creation: {str(e)}"
            )

    async def get_by_id(self, journey_id: UUID) -> Optional[EnhancedJourney]:
        """
        Get journey by ID with all related data.

        Args:
            journey_id: Journey UUID

        Returns:
            Enhanced journey or None if not found
        """
        try:
            journey_model = (
                self.session.query(JourneyModel)
                .options(
                    selectinload(JourneyModel.steps).selectinload(
                        JourneyStepModel.action
                    ),
                    selectinload(JourneyModel.execution_plan),
                    joinedload(JourneyModel.persona),
                    joinedload(JourneyModel.activity),
                )
                .filter(JourneyModel.id == str(journey_id))
                .first()
            )

            if not journey_model:
                return None

            return await self._convert_model_to_domain(journey_model)

        except SQLAlchemyError as e:
            raise JourneyRepositoryError(
                f"Database error retrieving journey {journey_id}: {str(e)}"
            )
        except Exception as e:
            raise JourneyRepositoryError(
                f"Unexpected error retrieving journey {journey_id}: {str(e)}"
            )

    async def get_by_persona_and_activity(
        self, persona_id: UUID, activity_id: UUID
    ) -> list[EnhancedJourney]:
        """
        Get journeys by persona and activity.

        Args:
            persona_id: Persona UUID
            activity_id: Activity UUID

        Returns:
            List of enhanced journeys
        """
        try:
            journey_models = (
                self.session.query(JourneyModel)
                .options(
                    selectinload(JourneyModel.steps).selectinload(
                        JourneyStepModel.action
                    ),
                    selectinload(JourneyModel.execution_plan),
                )
                .filter(
                    and_(
                        JourneyModel.persona_id == str(persona_id),
                        JourneyModel.activity_id == str(activity_id),
                    )
                )
                .all()
            )

            journeys = []
            for model in journey_models:
                journey = await self._convert_model_to_domain(model)
                journeys.append(journey)

            return journeys

        except SQLAlchemyError as e:
            raise JourneyRepositoryError(
                f"Database error retrieving journeys: {str(e)}"
            )
        except Exception as e:
            raise JourneyRepositoryError(
                f"Unexpected error retrieving journeys: {str(e)}"
            )

    async def list_journeys(
        self,
        filters: Optional[JourneyFilterSchema] = None,
        sort: Optional[JourneySortSchema] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[EnhancedJourney], int]:
        """
        List journeys with filtering, sorting and pagination.

        Args:
            filters: Filter criteria
            sort: Sort criteria
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (journeys list, total count)
        """
        try:
            # Base query with optimized loading
            query = self.session.query(JourneyModel).options(
                selectinload(JourneyModel.steps).selectinload(JourneyStepModel.action),
                selectinload(JourneyModel.execution_plan),
                joinedload(JourneyModel.persona),
                joinedload(JourneyModel.activity),
            )

            # Apply filters
            if filters:
                query = self._apply_filters(query, filters)

            # Get total count before pagination
            total_count = query.count()

            # Apply sorting
            if sort:
                query = self._apply_sorting(query, sort)
            else:
                # Default sorting by updated_at desc
                query = query.order_by(desc(JourneyModel.updated_at))

            # Apply pagination
            query = query.offset(offset).limit(limit)

            # Execute query
            journey_models = query.all()

            # Convert to domain objects
            journeys = []
            for model in journey_models:
                journey = await self._convert_model_to_domain(model)
                journeys.append(journey)

            return journeys, total_count

        except SQLAlchemyError as e:
            raise JourneyRepositoryError(f"Database error listing journeys: {str(e)}")
        except Exception as e:
            raise JourneyRepositoryError(f"Unexpected error listing journeys: {str(e)}")

    async def update(self, journey: EnhancedJourney) -> EnhancedJourney:
        """
        Update existing journey.

        Args:
            journey: Enhanced journey with updates

        Returns:
            Updated journey

        Raises:
            JourneyRepositoryError: If update fails
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Updating journey {journey.id} with {len(journey.enhanced_steps)} steps")
            
            # Get existing journey model
            journey_model = (
                self.session.query(JourneyModel)
                .options(
                    selectinload(JourneyModel.steps).selectinload(
                        JourneyStepModel.action
                    ),
                    selectinload(JourneyModel.execution_plan),
                )
                .filter(JourneyModel.id == str(journey.id))
                .first()
            )

            if not journey_model:
                raise JourneyRepositoryError(
                    f"Journey {journey.id} not found for update"
                )

            logger.debug(f"Found journey model with {len(journey_model.steps)} existing steps")

            # Update journey fields
            self._update_model_from_domain(journey_model, journey)

            # Handle steps updates
            await self._update_journey_steps(journey_model, journey.enhanced_steps)

            # Handle execution plan updates
            if journey.execution_plan:
                await self._update_execution_plan(journey_model, journey.execution_plan)

            # Commit changes
            logger.debug(f"Committing journey {journey.id} updates")
            self.session.commit()
            logger.info(f"Successfully committed journey {journey.id} with {len(journey.enhanced_steps)} steps")
            
            # Return the journey (relationships were loaded when we queried at the beginning of update)
            return journey

        except JourneyRepositoryError:
            self.session.rollback()
            logger.error(f"Journey repository error updating journey {journey.id}", exc_info=True)
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error updating journey {journey.id}: {str(e)}", exc_info=True)
            raise JourneyRepositoryError(f"Database error updating journey: {str(e)}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Unexpected error updating journey {journey.id}: {str(e)}", exc_info=True)
            raise JourneyRepositoryError(f"Unexpected error updating journey: {str(e)}")

    async def delete(self, journey_id: UUID) -> bool:
        """
        Delete journey and all related data.

        Args:
            journey_id: Journey UUID

        Returns:
            True if deleted successfully

        Raises:
            JourneyRepositoryError: If deletion fails
        """
        try:
            # Get journey with related data
            journey_model = (
                self.session.query(JourneyModel)
                .options(
                    selectinload(JourneyModel.steps),
                    selectinload(JourneyModel.execution_plan),
                )
                .filter(JourneyModel.id == str(journey_id))
                .first()
            )

            if not journey_model:
                return False

            # Delete related data (steps and execution plan will be deleted by cascade)
            self.session.delete(journey_model)
            self.session.commit()

            return True

        except SQLAlchemyError as e:
            self.session.rollback()
            raise JourneyRepositoryError(f"Database error deleting journey: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise JourneyRepositoryError(f"Unexpected error deleting journey: {str(e)}")

    async def get_journey_stats(self) -> dict[str, Any]:
        """
        Get comprehensive journey statistics.

        Returns:
            Dictionary with journey statistics
        """
        try:
            # Basic counts
            total_journeys = self.session.query(func.count(JourneyModel.id)).scalar()
            active_journeys = (
                self.session.query(func.count(JourneyModel.id))
                .filter(JourneyModel.is_active == True)
                .scalar()
            )

            # Status distribution
            status_stats = (
                self.session.query(
                    JourneyModel.execution_status,
                    func.count(JourneyModel.id).label("count"),
                )
                .group_by(JourneyModel.execution_status)
                .all()
            )

            # Complexity distribution
            complexity_stats = (
                self.session.query(
                    JourneyModel.complexity_level,
                    func.count(JourneyModel.id).label("count"),
                    func.avg(JourneyModel.estimated_duration_minutes).label(
                        "avg_duration"
                    ),
                )
                .group_by(JourneyModel.complexity_level)
                .all()
            )

            # Step count statistics
            step_stats = (
                self.session.query(
                    func.count(JourneyStepModel.id).label("total_steps"),
                    func.avg(func.count(JourneyStepModel.id))
                    .over()
                    .label("avg_steps_per_journey"),
                )
                .join(JourneyModel)
                .group_by(JourneyModel.id)
                .subquery()
            )

            total_steps = (
                self.session.query(func.sum(step_stats.c.total_steps)).scalar() or 0
            )
            avg_steps = (
                self.session.query(func.avg(step_stats.c.total_steps)).scalar() or 0
            )

            # Recent activity - database-agnostic datetime calculation
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            recent_journeys = (
                self.session.query(func.count(JourneyModel.id))
                .filter(JourneyModel.created_at >= seven_days_ago)
                .scalar()
            )

            return {
                "total_journeys": total_journeys,
                "active_journeys": active_journeys,
                "inactive_journeys": total_journeys - active_journeys,
                "recent_journeys_7_days": recent_journeys,
                "status_distribution": {
                    status: count for status, count in status_stats
                },
                "complexity_distribution": {
                    complexity: {
                        "count": count,
                        "avg_duration_minutes": float(avg_duration or 0),
                    }
                    for complexity, count, avg_duration in complexity_stats
                },
                "step_statistics": {
                    "total_steps": total_steps,
                    "average_steps_per_journey": float(avg_steps),
                },
                "activity_metrics": {
                    "completion_rate": 0.0,  # Would calculate from execution history
                    "average_execution_time": 0.0,  # Would calculate from execution history
                    "success_rate": 0.0,  # Would calculate from execution history
                },
            }

        except SQLAlchemyError as e:
            raise JourneyRepositoryError(
                f"Database error getting journey stats: {str(e)}"
            )
        except Exception as e:
            raise JourneyRepositoryError(
                f"Unexpected error getting journey stats: {str(e)}"
            )

    async def bulk_update_status(
        self, journey_ids: list[UUID], status: JourneyExecutionStatus
    ) -> dict[UUID, bool]:
        """
        Bulk update journey execution status.

        Args:
            journey_ids: List of journey UUIDs
            status: New execution status

        Returns:
            Dictionary mapping journey ID to success status
        """
        results = {}

        try:
            for journey_id in journey_ids:
                try:
                    updated_count = (
                        self.session.query(JourneyModel)
                        .filter(JourneyModel.id == str(journey_id))
                        .update(
                            {
                                "execution_status": status.value,
                                "updated_at": datetime.now(timezone.utc),
                            }
                        )
                    )
                    results[journey_id] = updated_count > 0

                except Exception:
                    results[journey_id] = False

            self.session.commit()
            return results

        except SQLAlchemyError as e:
            self.session.rollback()
            raise JourneyRepositoryError(
                f"Database error in bulk status update: {str(e)}"
            )
        except Exception as e:
            self.session.rollback()
            raise JourneyRepositoryError(
                f"Unexpected error in bulk status update: {str(e)}"
            )

    # Private helper methods

    def _apply_filters(self, query, filters: JourneyFilterSchema):
        """Apply filters to the query."""

        if filters.persona_ids:
            query = query.filter(JourneyModel.persona_id.in_(filters.persona_ids))

        if filters.activity_ids:
            query = query.filter(JourneyModel.activity_id.in_(filters.activity_ids))

        if filters.execution_statuses:
            status_values = [
                status.value if hasattr(status, "value") else status
                for status in filters.execution_statuses
            ]
            query = query.filter(JourneyModel.execution_status.in_(status_values))

        if filters.complexity_levels:
            complexity_values = [
                level.value if hasattr(level, "value") else level
                for level in filters.complexity_levels
            ]
            query = query.filter(JourneyModel.complexity_level.in_(complexity_values))

        if filters.is_active is not None:
            query = query.filter(JourneyModel.is_active == filters.is_active)

        if filters.has_steps is not None:
            if filters.has_steps:
                query = query.join(JourneyStepModel)
            else:
                query = query.outerjoin(JourneyStepModel).filter(
                    JourneyStepModel.id.is_(None)
                )

        if filters.min_duration_minutes is not None:
            query = query.filter(
                JourneyModel.estimated_duration_minutes >= filters.min_duration_minutes
            )

        if filters.max_duration_minutes is not None:
            query = query.filter(
                JourneyModel.estimated_duration_minutes <= filters.max_duration_minutes
            )

        if filters.created_after:
            query = query.filter(JourneyModel.created_at >= filters.created_after)

        if filters.created_before:
            query = query.filter(JourneyModel.created_at <= filters.created_before)

        if filters.updated_after:
            query = query.filter(JourneyModel.updated_at >= filters.updated_after)

        if filters.updated_before:
            query = query.filter(JourneyModel.updated_at <= filters.updated_before)

        if filters.search_text:
            search_pattern = f"%{filters.search_text}%"
            query = query.filter(
                or_(
                    JourneyModel.name.ilike(search_pattern),
                    JourneyModel.description.ilike(search_pattern),
                )
            )

        if filters.tags:
            # Assuming tags are stored as JSON array
            for tag in filters.tags:
                query = query.filter(JourneyModel.metadata.op("?")("tags"))

        return query

    def _apply_sorting(self, query, sort: JourneySortSchema):
        """Apply sorting to the query."""

        # Map sort fields to model attributes
        sort_field_map = {
            "name": JourneyModel.name,
            "created_at": JourneyModel.created_at,
            "updated_at": JourneyModel.updated_at,
            "execution_status": JourneyModel.execution_status,
            "complexity_level": JourneyModel.complexity_level,
            "estimated_duration_minutes": JourneyModel.estimated_duration_minutes,
        }

        if sort.field in sort_field_map:
            field = sort_field_map[sort.field]
            if sort.direction == "desc":
                query = query.order_by(desc(field))
            else:
                query = query.order_by(asc(field))

        return query

    def _convert_domain_to_model(self, journey: EnhancedJourney) -> JourneyModel:
        """Convert domain object to database model."""

        return JourneyModel(
            id=str(journey.id),
            name=journey.name,
            description=journey.description,
            persona_id=str(journey.persona_id),
            activity_id=str(journey.activity_id),
            execution_status=journey.execution_status.value,
            is_active=journey.is_active,
            estimated_duration_minutes=journey.estimated_duration_minutes,
            complexity_level=journey.complexity_level,
            prerequisites=journey.prerequisites,
            expected_outcomes=journey.expected_outcomes,
            journey_metadata=journey.metadata or {},
            created_at=journey.created_at,
            updated_at=journey.updated_at,
        )

    def _convert_step_to_model(
        self, step: ActionStepEnhanced, journey_id: UUID
    ) -> JourneyStepModel:
        """Convert domain step to database model."""

        return JourneyStepModel(
            journey_id=str(journey_id),
            step_number=step.step_number,
            action_id=str(step.action.id),
            step_description=step.step_description,
            parameters=step.parameters or {},
            expected_outputs=step.expected_outputs or {},  # FIXED: Use dict not list
            timeout_override=step.timeout_override,
            retry_override=step.retry_override,
            depends_on_steps=step.depends_on_steps or [],
            can_run_parallel=step.can_run_parallel,
            is_critical=step.is_critical,
        )

    def _convert_execution_plan_to_model(
        self, plan: JourneyExecutionPlan, journey_id: UUID
    ) -> JourneyExecutionPlanModel:
        """Convert execution plan to database model."""

        return JourneyExecutionPlanModel(
            journey_id=str(journey_id),
            total_steps=plan.total_steps,
            estimated_duration_seconds=int(plan.estimated_duration.total_seconds()),
            complexity_score=plan.complexity_score,
            can_execute_parallel=plan.can_execute_parallel,
            parallel_executable_steps=plan.parallel_executable_steps,
            critical_path_steps=plan.critical_path_steps,
            rollback_points=plan.rollback_points,
            resource_requirements=plan.resource_requirements or {},
        )

    def _update_model_from_domain(
        self, model: JourneyModel, journey: EnhancedJourney
    ) -> None:
        """Update model fields from domain object."""

        model.name = journey.name
        model.description = journey.description
        model.persona_id = str(journey.persona_id)
        model.activity_id = str(journey.activity_id)
        model.execution_status = journey.execution_status.value
        model.is_active = journey.is_active
        model.estimated_duration_minutes = journey.estimated_duration_minutes
        model.complexity_level = journey.complexity_level
        model.prerequisites = journey.prerequisites
        model.expected_outcomes = journey.expected_outcomes
        model.journey_metadata = journey.metadata or {}
        model.updated_at = journey.updated_at or datetime.now(timezone.utc)

    async def _update_journey_steps(
        self, journey_model: JourneyModel, steps: list[ActionStepEnhanced]
    ) -> None:
        """Update journey steps, handling additions, updates, and deletions."""
        
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"Updating journey {journey_model.id} steps: {len(steps)} steps requested")
        
        # Get existing step models
        existing_steps = {step.step_number: step for step in journey_model.steps}
        logger.debug(f"Found {len(existing_steps)} existing steps: {list(existing_steps.keys())}")
        
        # Track which steps we've seen
        seen_step_numbers = set()
        
        # Update or create steps
        for step in steps:
            seen_step_numbers.add(step.step_number)
            
            if step.step_number in existing_steps:
                # Update existing step
                existing_step = existing_steps[step.step_number]
                logger.debug(f"Updating existing step {step.step_number}, action_id: {step.action.id}")
                existing_step.action_id = str(step.action.id)
                existing_step.step_description = step.step_description
                existing_step.parameters = step.parameters or {}
                existing_step.expected_outputs = step.expected_outputs or {}  # FIXED: Use dict not list
                existing_step.timeout_override = step.timeout_override
                existing_step.retry_override = step.retry_override
                existing_step.depends_on_steps = step.depends_on_steps or []
                existing_step.can_run_parallel = step.can_run_parallel
                existing_step.is_critical = step.is_critical
            else:
                # Create new step
                logger.debug(f"Creating new step {step.step_number}, action_id: {step.action.id}")
                step_model = self._convert_step_to_model(step, journey_model.id)
                self.session.add(step_model)
        
        # Delete steps that are no longer in the journey
        for step_number, step_model in existing_steps.items():
            if step_number not in seen_step_numbers:
                logger.debug(f"Deleting step {step_number}")
                self.session.delete(step_model)
        
        self.session.flush()
        logger.debug(f"Flushed journey steps updates")

    async def _update_execution_plan(
        self, journey_model: JourneyModel, plan: JourneyExecutionPlan
    ) -> None:
        """Update execution plan."""

        # Delete existing plan
        self.session.query(JourneyExecutionPlanModel).filter(
            JourneyExecutionPlanModel.journey_id == journey_model.id
        ).delete()

        # Add new plan
        plan_model = self._convert_execution_plan_to_model(plan, journey_model.id)
        self.session.add(plan_model)

    async def _convert_model_to_domain(self, model: JourneyModel) -> EnhancedJourney:
        """Convert database model to domain object."""

        # Create base journey
        journey = EnhancedJourney.create_enhanced(
            name=model.name,
            description=model.description,
            persona_id=model.persona_id,
            activity_id=model.activity_id,
            estimated_duration_minutes=model.estimated_duration_minutes,
            complexity_level=model.complexity_level,
            prerequisites=model.prerequisites,
            expected_outcomes=model.expected_outcomes,
            metadata=model.journey_metadata,
        )

        # Set additional properties
        journey.id = model.id
        journey.execution_status = JourneyExecutionStatus(model.execution_status)
        journey.is_active = model.is_active
        journey.created_at = model.created_at
        journey.updated_at = model.updated_at

        # Convert steps if present
        if hasattr(model, "steps") and model.steps:
            enhanced_steps = []
            for step_model in sorted(model.steps, key=lambda s: s.step_number):
                enhanced_step = await self._convert_step_model_to_domain(step_model)
                enhanced_steps.append(enhanced_step)
            journey._enhanced_steps = enhanced_steps  # Use private attribute

        # Convert execution plan if present
        if hasattr(model, "execution_plan") and model.execution_plan:
            execution_plan = await self._convert_execution_plan_model_to_domain(
                model.execution_plan
            )
            journey._execution_plan = execution_plan  # Use private attribute

        return journey

    async def _convert_step_model_to_domain(
        self, step_model: JourneyStepModel
    ) -> ActionStepEnhanced:
        """Convert step model to domain object."""

        # Get action - if not loaded via relationship, fetch it manually
        action_model = step_model.action
        if action_model is None:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Action relationship not loaded for step {step_model.id}, fetching manually. Action ID: {step_model.action_id}")
            
            # Manually load the action
            from src.infrastructure.database.models.action_library_models import ActionLibraryModel
            action_model = self.session.query(ActionLibraryModel).filter(
                ActionLibraryModel.id == step_model.action_id
            ).first()
            
            if action_model is None:
                logger.error(f"Action {step_model.action_id} not found in database for step {step_model.id}")
                logger.error(f"Step details: journey_id={step_model.journey_id}, step_number={step_model.step_number}")
                
                # Debug: List all actions in database
                all_actions = self.session.query(ActionLibraryModel).all()
                logger.error(f"Available actions in DB: {[(a.id, a.name) for a in all_actions]}")
                
                raise ValueError(f"Action {step_model.action_id} not found for step {step_model.id}")
        
        action = await self._convert_action_model_to_domain(action_model)

        return ActionStepEnhanced(
            step_number=step_model.step_number,
            action=action,
            parameters=step_model.parameters or {},
            step_description=step_model.step_description,
            expected_outputs=step_model.expected_outputs or {},  # FIXED: Use dict not list
            timeout_override=step_model.timeout_override,
            retry_override=step_model.retry_override,
            depends_on_steps=step_model.depends_on_steps or [],
            can_run_parallel=step_model.can_run_parallel,
            is_critical=step_model.is_critical,
        )

    async def _convert_execution_plan_model_to_domain(
        self, plan_model: JourneyExecutionPlanModel
    ) -> JourneyExecutionPlan:
        """Convert execution plan model to domain object."""

        from datetime import timedelta

        return JourneyExecutionPlan(
            total_steps=plan_model.total_steps,
            estimated_duration=timedelta(seconds=plan_model.estimated_duration_seconds),
            complexity_score=plan_model.complexity_score,
            can_execute_parallel=plan_model.can_execute_parallel,
            parallel_executable_steps=plan_model.parallel_executable_steps,
            critical_path_steps=plan_model.critical_path_steps,
            rollback_points=plan_model.rollback_points,
            resource_requirements=plan_model.resource_requirements or {},
        )

    async def _convert_action_model_to_domain(
        self, action_model: ActionLibraryModel
    ) -> Action:
        """Convert action model to domain object."""

        # Use constructor directly to preserve the database ID
        # DO NOT use Action.create() as it generates a new UUID!
        return Action(
            id=UUID(action_model.id),  # CRITICAL: Use existing ID from database
            name=action_model.name,
            description=action_model.description,
            action_type=ActionType(action_model.bdd_step_type),  # Use bdd_step_type for action type
            erpnext_module=action_model.erpnext_doctype or "Unknown",
            implementation_type=ImplementationType(action_model.action_type),  # Use action_type for implementation type
            parameters=[],  # Would need to be converted from model
            expected_outputs={},  # FIXED: Use dict not list to match domain model
            robot_keywords=action_model.implementation.get("robot_keywords", []) if action_model.implementation else [],
            validation_rules=action_model.action_metadata.get("validation_rules", {}) if action_model.action_metadata else {},
            tags=action_model.tags or [],
            prerequisites=action_model.prerequisites or [],
            postconditions=action_model.postconditions or [],
            execution_timeout=action_model.default_timeout_seconds or 30,
            retry_count=action_model.default_retry_count or 0,
            metadata=action_model.action_metadata or {},
            created_at=action_model.created_at,
            updated_at=action_model.updated_at,
        )

