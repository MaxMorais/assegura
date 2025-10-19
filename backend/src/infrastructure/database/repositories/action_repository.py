"""
Action Library Repository - Infrastructure Layer

This module implements the ActionLibraryRepository using SQLAlchemy ORM for managing
action library data persistence in the ERPNext test automation framework. It provides
comprehensive CRUD operations, complex queries, filtering, sorting, and
relationship management with the database.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, asc, desc, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from src.application.dto.action_schemas import ActionFilterSchema, ActionSortSchema
from src.application.services.action_service import ActionRepositoryInterface
from src.domain.actions.action_library import (
    Action,
    ActionOutput,
    ActionParameter,
    ActionType,
    ImplementationType,
)
from src.infrastructure.database.models.action_library_models import (
    ActionLibraryModel,
    ActionOutputModel,
    ActionParameterModel,
)
from src.infrastructure.database.repositories.base import BaseRepository


class ActionRepositoryError(Exception):
    """Base exception for action repository operations."""

    pass


class SQLAlchemyActionRepository(BaseRepository, ActionRepositoryInterface):
    """SQLAlchemy implementation of action library repository."""

    def __init__(self, db_session: Session):
        super().__init__(db_session, ActionLibraryModel)

    def _entity_to_model(self, entity: Action) -> ActionLibraryModel:
        """Convert Action entity to ActionLibraryModel."""
        return self._convert_domain_to_model(entity)

    def _model_to_entity(self, model: ActionLibraryModel) -> Action:
        """Convert ActionLibraryModel to Action entity."""
        # Note: This is a synchronous version for BaseRepository compatibility
        # The async version _convert_model_to_domain should be used in async contexts
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._convert_model_to_domain(model))
        finally:
            loop.close()

    async def create(self, action: Action) -> Action:
        """
        Create a new action in the database.

        Args:
            action: Action library domain object

        Returns:
            Created action with assigned ID

        Raises:
            ActionRepositoryError: If creation fails
        """
        try:
            # Convert domain object to model
            action_model = self._convert_domain_to_model(action)

            # Add to database
            self.session.add(action_model)
            self.session.commit()
            self.session.refresh(action_model)

            # Convert back to domain object
            return await self._convert_model_to_domain(action_model)

        except IntegrityError as e:
            self.session.rollback()
            raise ActionRepositoryError(
                f"Action creation failed due to constraint violation: {e}"
            )
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ActionRepositoryError(f"Database error during action creation: {e}")

    async def get_by_id(self, action_id: UUID) -> Optional[Action]:
        """
        Get action by ID.

        Args:
            action_id: Action ID

        Returns:
            Action if found, None otherwise
        """
        try:
            query = (
                self.session.query(ActionLibraryModel)
                .options(
                    selectinload(ActionLibraryModel.parameters),
                    selectinload(ActionLibraryModel.outputs),
                )
                .filter(ActionLibraryModel.id == action_id)
            )

            action_model = query.first()
            if not action_model:
                return None

            return await self._convert_model_to_domain(action_model)

        except SQLAlchemyError as e:
            raise ActionRepositoryError(f"Database error during action retrieval: {e}")

    async def get_by_name_and_type(
        self, name: str, action_type: ActionType
    ) -> Optional[Action]:
        """
        Get action by name and type.

        Args:
            name: Action name
            action_type: Action type

        Returns:
            Action if found, None otherwise
        """
        try:
            query = (
                self.session.query(ActionLibraryModel)
                .options(
                    selectinload(ActionLibraryModel.parameters),
                    selectinload(ActionLibraryModel.outputs),
                )
                .filter(
                    and_(
                        ActionLibraryModel.name == name,
                        ActionLibraryModel.action_type == action_type.value,
                    )
                )
            )

            action_model = query.first()
            if not action_model:
                return None

            return await self._convert_model_to_domain(action_model)

        except SQLAlchemyError as e:
            raise ActionRepositoryError(f"Database error during action retrieval: {e}")

    async def list_actions(
        self,
        filters: Optional[ActionFilterSchema] = None,
        sort: Optional[ActionSortSchema] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Action], int]:
        """
        List actions with filtering and pagination.

        Args:
            filters: Optional filters to apply
            sort: Optional sorting criteria
            limit: Maximum number of actions to return
            offset: Number of actions to skip

        Returns:
            Tuple of (actions list, total count)
        """
        try:
            # Base query with eager loading
            query = self.session.query(ActionLibraryModel).options(
                selectinload(ActionLibraryModel.parameters),
                selectinload(ActionLibraryModel.outputs),
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
                query = query.order_by(desc(ActionLibraryModel.updated_at))

            # Apply pagination
            query = query.offset(offset).limit(limit)

            # Execute query
            action_models = query.all()

            # Convert to domain objects
            actions = []
            for model in action_models:
                action = await self._convert_model_to_domain(model)
                actions.append(action)

            return actions, total_count

        except SQLAlchemyError as e:
            raise ActionRepositoryError(f"Database error during action listing: {e}")

    async def update(self, action: Action) -> Action:
        """
        Update existing action.

        Args:
            action: Updated action domain object

        Returns:
            Updated action

        Raises:
            ActionRepositoryError: If update fails
        """
        try:
            # Get existing model
            action_model = (
                self.session.query(ActionLibraryModel)
                .filter(ActionLibraryModel.id == action.id)
                .first()
            )

            if not action_model:
                raise ActionRepositoryError(
                    f"Action with ID {action.id} not found"
                )

            # Update model from domain object
            self._update_model_from_domain(action_model, action)

            # Update parameters and outputs
            await self._update_action_parameters(action_model, action)
            await self._update_action_outputs(action_model, action)

            # Commit changes
            self.session.commit()
            self.session.refresh(action_model)

            return await self._convert_model_to_domain(action_model)

        except IntegrityError as e:
            self.session.rollback()
            raise ActionRepositoryError(
                f"Action update failed due to constraint violation: {e}"
            )
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ActionRepositoryError(f"Database error during action update: {e}")

    async def delete(self, action_id: UUID) -> bool:
        """
        Delete action.

        Args:
            action_id: Action ID to delete

        Returns:
            True if deleted successfully

        Raises:
            ActionRepositoryError: If deletion fails
        """
        try:
            # Get existing action
            action_model = (
                self.session.query(ActionLibraryModel)
                .filter(ActionLibraryModel.id == action_id)
                .first()
            )

            if not action_model:
                return False

            # Delete related parameters and outputs (cascade should handle this)
            self.session.delete(action_model)
            self.session.commit()

            return True

        except SQLAlchemyError as e:
            self.session.rollback()
            raise ActionRepositoryError(f"Database error during action deletion: {e}")

    async def get_actions_by_module(self, erpnext_module: str) -> list[Action]:
        """
        Get actions for specific ERPNext module.

        Args:
            erpnext_module: ERPNext module name

        Returns:
            List of actions for the module
        """
        try:
            query = (
                self.session.query(ActionLibraryModel)
                .options(
                    selectinload(ActionLibraryModel.parameters),
                    selectinload(ActionLibraryModel.outputs),
                )
                .filter(ActionLibraryModel.erpnext_module == erpnext_module)
                .filter(ActionLibraryModel.is_active == True)
                .order_by(ActionLibraryModel.name)
            )

            action_models = query.all()

            actions = []
            for model in action_models:
                action = await self._convert_model_to_domain(model)
                actions.append(action)

            return actions

        except SQLAlchemyError as e:
            raise ActionRepositoryError(
                f"Database error during module actions retrieval: {e}"
            )

    async def get_usage_statistics(self) -> dict[str, Any]:
        """
        Get action usage statistics.

        Returns:
            Dictionary with action usage statistics
        """
        try:
            # This would typically involve joins with execution/journey tables
            # For now, return basic statistics
            total_actions = self.session.query(ActionLibraryModel).count()
            active_actions = (
                self.session.query(ActionLibraryModel)
                .filter(ActionLibraryModel.is_active == True)
                .count()
            )

            by_type = (
                self.session.query(
                    ActionLibraryModel.action_type,
                    func.count(ActionLibraryModel.id).label("count"),
                )
                .group_by(ActionLibraryModel.action_type)
                .all()
            )

            by_module = (
                self.session.query(
                    ActionLibraryModel.erpnext_module,
                    func.count(ActionLibraryModel.id).label("count"),
                )
                .group_by(ActionLibraryModel.erpnext_module)
                .all()
            )

            return {
                "total_actions": total_actions,
                "active_actions": active_actions,
                "inactive_actions": total_actions - active_actions,
                "by_type": {item.action_type: item.count for item in by_type},
                "by_module": {
                    item.erpnext_module or "unassigned": item.count
                    for item in by_module
                },
            }

        except SQLAlchemyError as e:
            raise ActionRepositoryError(
                f"Database error during statistics retrieval: {e}"
            )

    async def bulk_update_status(self, action_ids: list[UUID], is_active: bool) -> int:
        """
        Bulk update action status.

        Args:
            action_ids: List of action IDs
            is_active: New active status

        Returns:
            Number of actions updated
        """
        try:
            updated_count = (
                self.db.query(ActionLibraryModel)
                .filter(ActionLibraryModel.id.in_(action_ids))
                .update(
                    {"is_active": is_active, "updated_at": datetime.utcnow()},
                    synchronize_session=False,
                )
            )

            self.db.commit()
            return updated_count

        except SQLAlchemyError as e:
            self.db.rollback()
            raise ActionRepositoryError(
                f"Database error during bulk status update: {e}"
            )

    # Private helper methods

    def _apply_filters(self, query, filters: ActionFilterSchema):
        """Apply filters to query."""

        if filters.action_type:
            query = query.filter(
                ActionLibraryModel.action_type == filters.action_type.value
            )

        if filters.implementation_type:
            query = query.filter(
                ActionLibraryModel.implementation_type
                == filters.implementation_type.value
            )

        if filters.erpnext_module:
            query = query.filter(
                ActionLibraryModel.erpnext_module == filters.erpnext_module
            )

        if filters.is_active is not None:
            query = query.filter(ActionLibraryModel.is_active == filters.is_active)

        if filters.name_contains:
            query = query.filter(
                ActionLibraryModel.name.ilike(f"%{filters.name_contains}%")
            )

        if filters.description_contains:
            query = query.filter(
                ActionLibraryModel.description.ilike(
                    f"%{filters.description_contains}%"
                )
            )

        if filters.tags:
            for tag in filters.tags:
                query = query.filter(ActionLibraryModel.tags.contains([tag]))

        if filters.created_after:
            query = query.filter(ActionLibraryModel.created_at >= filters.created_after)

        if filters.created_before:
            query = query.filter(
                ActionLibraryModel.created_at <= filters.created_before
            )

        if filters.updated_after:
            query = query.filter(ActionLibraryModel.updated_at >= filters.updated_after)

        if filters.updated_before:
            query = query.filter(
                ActionLibraryModel.updated_at <= filters.updated_before
            )

        return query

    def _apply_sorting(self, query, sort: ActionSortSchema):
        """Apply sorting to query."""

        sort_column = getattr(
            ActionLibraryModel, sort.sort_by, ActionLibraryModel.updated_at
        )

        if sort.sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        return query

    def _convert_domain_to_model(self, action: Action) -> ActionLibraryModel:
        """Convert domain object to database model."""

        return ActionLibraryModel(
            id=str(action.id),  # Convert UUID to string for database
            name=action.name,
            description=action.description,
            action_type=action.implementation_type.value,  # UI_INTERACTION, etc.
            bdd_step_type=action.action_type.value,  # given, when, then
            category="utility",  # Default category, could be derived from other fields
            implementation={"robot_keywords": action.robot_keywords},  # Store robot keywords in implementation JSON
            erpnext_doctype=action.erpnext_module,
            default_timeout_seconds=action.execution_timeout,
            default_retry_count=action.retry_count,
            tags=action.tags,
            action_metadata=action.metadata,
            is_active=action.is_active,
            created_at=action.created_at,
            updated_at=action.updated_at,
            # Parameters and outputs will be handled separately
        )

    def _convert_parameter_to_model(
        self, parameter: ActionParameter, action_id: UUID
    ) -> ActionParameterModel:
        """Convert parameter domain object to model."""

        return ActionParameterModel(
            id=parameter.parameter_id,
            action_id=action_id,
            name=parameter.name,
            parameter_type=parameter.parameter_type,
            description=parameter.description,
            is_required=parameter.is_required,
            default_value=parameter.default_value,
            validation_rules=parameter.validation_rules,
            example_values=parameter.example_values,
        )

    def _convert_output_to_model(
        self, output: ActionOutput, action_id: UUID
    ) -> ActionOutputModel:
        """Convert output domain object to model."""

        return ActionOutputModel(
            id=output.output_id,
            action_id=action_id,
            name=output.name,
            output_type=output.output_type,
            description=output.description,
            data_path=output.data_path,
            validation_schema=output.validation_schema,
        )

    def _update_model_from_domain(
        self, model: ActionLibraryModel, action: Action
    ) -> None:
        """Update model properties from domain object."""

        model.name = action.name
        model.description = action.description
        model.action_type = action.implementation_type.value
        model.bdd_step_type = action.action_type.value
        model.implementation = {"robot_keywords": action.robot_keywords}
        model.erpnext_doctype = action.erpnext_module
        model.default_timeout_seconds = action.execution_timeout
        model.default_retry_count = action.retry_count
        model.tags = action.tags
        model.action_metadata = action.metadata
        model.is_active = action.is_active
        model.updated_at = action.updated_at

    async def _update_action_parameters(
        self, action_model: ActionLibraryModel, action: Action
    ) -> None:
        """Update action parameters."""

        # Remove existing parameters
        self.db.query(ActionParameterModel).filter(
            ActionParameterModel.action_id == action_model.id
        ).delete()

        # Add new parameters
        for parameter in action.parameters:
            param_model = self._convert_parameter_to_model(parameter, action_model.id)
            self.db.add(param_model)

    async def _update_action_outputs(
        self, action_model: ActionLibraryModel, action: Action
    ) -> None:
        """Update action outputs."""

        # Remove existing outputs
        self.db.query(ActionOutputModel).filter(
            ActionOutputModel.action_id == action_model.id
        ).delete()

        # Add new outputs
        for output in action.outputs:
            output_model = self._convert_output_to_model(output, action_model.id)
            self.db.add(output_model)

    async def _convert_model_to_domain(
        self, model: ActionLibraryModel
    ) -> Action:
        """Convert database model to domain object."""

        # Convert parameters
        parameters = []
        for param_model in model.parameters:
            parameter = ActionParameter(
                parameter_id=param_model.id,
                name=param_model.name,
                parameter_type=param_model.parameter_type,
                description=param_model.description,
                is_required=param_model.is_required,
                default_value=param_model.default_value,
                validation_rules=param_model.validation_rules or {},
                example_values=param_model.example_values or [],
            )
            parameters.append(parameter)

        # Convert outputs
        outputs = []
        for output_model in model.outputs:
            output = ActionOutput(
                output_id=output_model.id,
                name=output_model.name,
                output_type=output_model.output_type,
                description=output_model.description,
                data_path=output_model.data_path,
                validation_schema=output_model.validation_schema or {},
            )
            outputs.append(output)

        # Create domain object
        action = Action(
            id=UUID(model.id),
            name=model.name,
            description=model.description,
            action_type=ActionType(model.bdd_step_type),
            erpnext_module=model.erpnext_doctype,
            implementation_type=ImplementationType(model.action_type),
            parameters=parameters,
            expected_outputs=outputs,
            robot_keywords=model.implementation.get("robot_keywords", []) if model.implementation else [],
            execution_timeout=model.default_timeout_seconds,
            retry_count=model.default_retry_count,
            metadata=model.action_metadata,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

        return action
