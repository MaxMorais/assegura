"""
ActionLibrary Service - Application Layer

This module implements the ActionLibraryService for managing action library use cases
and business logic in the ERPNext test automation framework. It coordinates
between the domain layer and infrastructure layer, handling action CRUD operations,
parameter validation, and action classification workflows.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import UUID

from src.application.dto.action_schemas import (
    ActionBulkOperationSchema,
    ActionBulkResultSchema,
    ActionComplexityScoreSchema,
    ActionCreateSchema,
    ActionFilterSchema,
    ActionFromTemplateSchema,
    ActionListItemSchema,
    ActionOutputSchema,
    ActionParameterSchema,
    ActionPatternSchema,
    ActionResponseSchema,
    ActionSortSchema,
    ActionSuggestionSchema,
    ActionTemplateSchema,
    ActionUpdateSchema,
    ActionUsageStatsSchema,
    ActionValidationResultSchema,
)
from src.application.dto.base_schemas import PaginatedResponse
from src.domain.actions.action_library import (
    Action,
    ActionOutput,
    ActionParameter,
    ActionType,
    ImplementationType,
)


class ActionRepositoryInterface(ABC):
    """Abstract interface for action data persistence."""

    @abstractmethod
    async def create(self, action: Action) -> Action:
        """Create a new action."""
        pass

    @abstractmethod
    async def get_by_id(self, action_id: UUID) -> Optional[Action]:
        """Get action by ID."""
        pass

    @abstractmethod
    async def get_by_name_and_type(
        self, name: str, action_type: ActionType
    ) -> Optional[Action]:
        """Get action by name and type."""
        pass

    @abstractmethod
    async def list_actions(
        self,
        filters: Optional[ActionFilterSchema] = None,
        sort: Optional[ActionSortSchema] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Action], int]:
        """List actions with filtering and pagination."""
        pass

    @abstractmethod
    async def update(self, action: Action) -> Action:
        """Update existing action."""
        pass

    @abstractmethod
    async def delete(self, action_id: UUID) -> bool:
        """Delete action."""
        pass

    @abstractmethod
    async def get_actions_by_module(self, erpnext_module: str) -> list[Action]:
        """Get actions for specific ERPNext module."""
        pass

    @abstractmethod
    async def get_usage_statistics(self) -> dict[str, Any]:
        """Get action usage statistics."""
        pass

    @abstractmethod
    async def bulk_update_status(self, action_ids: list[UUID], is_active: bool) -> int:
        """Bulk update action status."""
        pass


class ActionLibraryServiceError(Exception):
    """Base exception for ActionLibraryService errors."""

    pass


class ActionNotFoundError(ActionLibraryServiceError):
    """Raised when action is not found."""

    pass


class ActionValidationServiceError(ActionLibraryServiceError):
    """Raised when action validation fails."""

    pass


class ActionLibraryService:
    """Service for managing action library operations and business logic."""

    def __init__(self, action_repository: ActionRepositoryInterface):
        self.action_repository = action_repository
        # Remove parameter_validator as ActionParameter has its own validate_value method
        self._action_templates: dict[str, ActionTemplateSchema] = {}

    async def create_action(
        self, action_data: ActionCreateSchema
    ) -> ActionResponseSchema:
        """
        Create a new action with validation.

        Args:
            action_data: Action creation data

        Returns:
            Created action response

        Raises:
            ActionValidationServiceError: If validation fails
            ActionLibraryServiceError: If creation fails
        """
        try:
            # Validate action uniqueness
            existing_action = await self.action_repository.get_by_name_and_type(
                action_data.name, ActionType(action_data.action_type.value)
            )
            if existing_action:
                raise ActionValidationServiceError(
                    f"Action '{action_data.name}' of type '{action_data.action_type}' already exists"
                )

            # Create action library entity
            action = Action.create(
                name=action_data.name,
                description=action_data.description,
                action_type=ActionType(action_data.action_type.value),
                implementation_type=ImplementationType(
                    action_data.implementation_type.value
                ),
                erpnext_module=action_data.erpnext_module,
                robot_keywords=action_data.robot_keywords,
                execution_timeout=action_data.execution_timeout,
                retry_count=action_data.retry_count,
                tags=action_data.tags,
            )

            # Add parameters if provided
            if action_data.parameters:
                for param_data in action_data.parameters:
                    await self._add_parameter_to_action(action, param_data)

            # Add outputs if provided
            if action_data.expected_outputs:
                for output_data in action_data.expected_outputs:
                    await self._add_output_to_action(action, output_data)

            # Validate action comprehensive
            validation_errors = await self._validate_action_comprehensive(action)
            if validation_errors:
                raise ActionValidationServiceError(
                    f"Action validation failed: {validation_errors}"
                )

            # Save to repository
            saved_action = await self.action_repository.create(action)

            return await self._convert_to_response_schema(saved_action)

        except Exception as e:
            if isinstance(e, ActionLibraryServiceError):
                raise
            raise ActionLibraryServiceError(f"Failed to create action: {str(e)}")

    async def get_action(self, action_id: UUID) -> ActionResponseSchema:
        """
        Get action by ID.

        Args:
            action_id: Action ID

        Returns:
            Action response

        Raises:
            ActionNotFoundError: If action not found
        """
        action = await self.action_repository.get_by_id(action_id)
        if not action:
            raise ActionNotFoundError(f"Action with ID {action_id} not found")

        return await self._convert_to_response_schema(action)

    async def list_actions(
        self,
        filters: Optional[ActionFilterSchema] = None,
        sort: Optional[ActionSortSchema] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse[ActionListItemSchema]:
        """
        List actions with filtering and pagination.

        Args:
            filters: Optional filters to apply
            sort: Optional sorting criteria
            limit: Maximum number of actions to return
            offset: Number of actions to skip

        Returns:
            Paginated action list
        """
        actions, total = await self.action_repository.list_actions(
            filters=filters, sort=sort, limit=limit, offset=offset
        )

        items = [await self._convert_to_list_item_schema(action) for action in actions]

        return PaginatedResponse[ActionListItemSchema](
            items=items, total=total, limit=limit, offset=offset
        )

    async def update_action(
        self, action_id: UUID, update_data: ActionUpdateSchema
    ) -> ActionResponseSchema:
        """
        Update existing action.

        Args:
            action_id: Action ID to update
            update_data: Updated action data

        Returns:
            Updated action response

        Raises:
            ActionNotFoundError: If action not found
            ActionValidationServiceError: If validation fails
        """
        action = await self.action_repository.get_by_id(action_id)
        if not action:
            raise ActionNotFoundError(f"Action with ID {action_id} not found")

        # Update action properties
        if update_data.name is not None:
            action.update_name(update_data.name)

        if update_data.description is not None:
            action.update_description(update_data.description)

        if update_data.robot_keywords is not None:
            action.update_robot_keywords(update_data.robot_keywords)

        if update_data.execution_timeout is not None:
            action.update_details(execution_timeout=update_data.execution_timeout)

        if update_data.retry_count is not None:
            action.update_details(retry_count=update_data.retry_count)

        if update_data.tags is not None:
            action.update_tags(update_data.tags)

        if update_data.metadata is not None:
            action.update_metadata(update_data.metadata)

        if update_data.is_active is not None:
            if update_data.is_active:
                action.activate()
            else:
                action.deactivate()

        # Validate updated action
        validation_errors = await self._validate_action_comprehensive(action)
        if validation_errors:
            raise ActionValidationServiceError(
                f"Action validation failed: {validation_errors}"
            )

        # Save changes
        updated_action = await self.action_repository.update(action)

        return await self._convert_to_response_schema(updated_action)

    async def delete_action(self, action_id: UUID) -> bool:
        """
        Delete action.

        Args:
            action_id: Action ID to delete

        Returns:
            True if deleted successfully

        Raises:
            ActionNotFoundError: If action not found
        """
        action = await self.action_repository.get_by_id(action_id)
        if not action:
            raise ActionNotFoundError(f"Action with ID {action_id} not found")

        return await self.action_repository.delete(action_id)

    async def get_actions_by_module(
        self, erpnext_module: str
    ) -> list[ActionResponseSchema]:
        """Get actions for specific ERPNext module."""
        actions = await self.action_repository.get_actions_by_module(erpnext_module)
        return [await self._convert_to_response_schema(action) for action in actions]

    async def validate_action(self, action_id: UUID) -> ActionValidationResultSchema:
        """
        Validate action comprehensively.

        Args:
            action_id: Action ID to validate

        Returns:
            Validation result

        Raises:
            ActionNotFoundError: If action not found
        """
        action = await self.action_repository.get_by_id(action_id)
        if not action:
            raise ActionNotFoundError(f"Action with ID {action_id} not found")

        errors = await self._validate_action_comprehensive(action)
        warnings = await self._get_action_warnings(action)
        suggestions = await self._get_action_suggestions(action)

        return ActionValidationResultSchema(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    async def get_action_complexity_score(
        self, action_id: UUID
    ) -> ActionComplexityScoreSchema:
        """Get complexity score for action."""
        action = await self.action_repository.get_by_id(action_id)
        if not action:
            raise ActionNotFoundError(f"Action with ID {action_id} not found")

        complexity_score = action.calculate_complexity_score()
        complexity_details = action.get_complexity_breakdown()

        return ActionComplexityScoreSchema(
            action_id=action_id,
            complexity_score=complexity_score,
            complexity_level=action.get_complexity_level(),
            complexity_breakdown=complexity_details,
        )

    async def get_action_usage_stats(self, action_id: UUID) -> ActionUsageStatsSchema:
        """Get usage statistics for action."""
        action = await self.action_repository.get_by_id(action_id)
        if not action:
            raise ActionNotFoundError(f"Action with ID {action_id} not found")

        # Get usage stats from repository
        stats = await self.action_repository.get_usage_statistics()
        action_stats = stats.get(str(action_id), {})

        return ActionUsageStatsSchema(
            action_id=action_id,
            usage_count=action_stats.get("usage_count", 0),
            success_rate=action_stats.get("success_rate", 0.0),
            average_execution_time=action_stats.get("average_execution_time", 0.0),
            last_used_at=action_stats.get("last_used_at"),
        )

    async def suggest_similar_actions(
        self, action_criteria: ActionPatternSchema
    ) -> list[ActionSuggestionSchema]:
        """Suggest similar actions based on criteria."""
        # Implementation for finding similar actions based on pattern matching
        # This would analyze existing actions and suggest similar ones
        pass

    async def bulk_operation(
        self, operation_data: ActionBulkOperationSchema
    ) -> ActionBulkResultSchema:
        """
        Perform bulk operations on actions.

        Args:
            operation_data: Bulk operation specification

        Returns:
            Bulk operation results
        """
        success_count = 0
        failed_operations = []

        for action_id in operation_data.action_ids:
            try:
                if operation_data.operation == "activate":
                    action = await self.action_repository.get_by_id(action_id)
                    if action:
                        action.activate()
                        await self.action_repository.update(action)
                        success_count += 1
                elif operation_data.operation == "deactivate":
                    action = await self.action_repository.get_by_id(action_id)
                    if action:
                        action.deactivate()
                        await self.action_repository.update(action)
                        success_count += 1
                elif operation_data.operation == "delete":
                    if await self.action_repository.delete(action_id):
                        success_count += 1
            except Exception as e:
                failed_operations.append({"action_id": str(action_id), "error": str(e)})

        return ActionBulkResultSchema(
            operation=operation_data.operation,
            total_actions=len(operation_data.action_ids),
            success_count=success_count,
            failed_count=len(failed_operations),
            failed_operations=failed_operations,
        )

    async def create_action_template(self, template_data: ActionTemplateSchema) -> str:
        """Create action template for reuse."""
        template_name = template_data.template_name
        self._action_templates[template_name] = template_data
        return template_name

    async def create_action_from_template(
        self, template_request: ActionFromTemplateSchema
    ) -> ActionResponseSchema:
        """Create action from template with parameter substitution."""
        template = self._action_templates.get(template_request.template_name)
        if not template:
            raise ActionLibraryServiceError(
                f"Template '{template_request.template_name}' not found"
            )

        # Create action data from template with parameter substitution
        action_data = template.action_template

        # Apply parameter values
        for param_name, param_value in template_request.parameter_values.items():
            # Replace placeholders in action data
            pass

        # Apply any overrides
        if template_request.action_overrides:
            # Apply overrides to action data
            pass

        return await self.create_action(action_data)

    # Private helper methods

    async def _add_parameter_to_action(
        self, action: Action, param_data: ActionParameterSchema
    ) -> None:
        """Add parameter to action."""
        parameter = ActionParameter.create_parameter(
            name=param_data.name,
            parameter_type=param_data.parameter_type.value,
            description=param_data.description,
            is_required=param_data.is_required,
            default_value=param_data.default_value,
            validation_rules=param_data.validation_rules,
            example_values=param_data.example_values,
        )
        action.add_parameter(parameter)

    async def _add_output_to_action(
        self, action: Action, output_data: ActionOutputSchema
    ) -> None:
        """Add output to action."""
        output = ActionOutput.create_output(
            name=output_data.name,
            output_type=output_data.output_type.value,
            description=output_data.description,
            data_path=output_data.data_path,
            validation_schema=output_data.validation_schema,
        )
        action.add_output(output)

    async def _validate_action_comprehensive(self, action: Action) -> list[str]:
        """Perform comprehensive action validation."""
        errors = []

        # Validate action completeness
        if not action.name or len(action.name.strip()) < 3:
            errors.append("Action name must be at least 3 characters")

        if not action.description or len(action.description.strip()) < 10:
            errors.append("Action description must be at least 10 characters")

        if not action.robot_keywords:
            errors.append("Robot Framework keywords are required")

        # Validate parameters
        for parameter in action.parameters:
            param_errors = parameter.validate_value(parameter.default_value if parameter.default_value is not None else None)
            if param_errors:
                errors.extend([f"Parameter '{parameter.name}': {error}" for error in param_errors])

        # Validate outputs
        for output in action.expected_outputs:
            if not output.name or not output.description:
                errors.append(f"Output '{output.name}' must have name and description")

        return errors

    async def _get_action_warnings(self, action: Action) -> list[str]:
        """Get action warnings."""
        warnings = []

        if action.expected_execution_time and action.expected_execution_time > 300:
            warnings.append("Action execution time is longer than 5 minutes")

        if len(action.parameters) > 10:
            warnings.append("Action has many parameters, consider simplifying")

        return warnings

    async def _get_action_suggestions(self, action: Action) -> list[str]:
        """Get action improvement suggestions."""
        suggestions = []

        if not action.tags:
            suggestions.append("Consider adding tags to improve action discoverability")

        if not action.metadata:
            suggestions.append("Consider adding metadata for better action context")

        return suggestions

    async def _convert_to_response_schema(
        self, action: Action
    ) -> ActionResponseSchema:
        """Convert action entity to response schema."""
        return ActionResponseSchema(
            id=action.id,
            name=action.name,
            description=action.description,
            action_type=action.action_type.value,
            implementation_type=action.implementation_type.value,
            erpnext_module=action.erpnext_module,
            parameters=[
                self._convert_parameter_to_schema(p) for p in action.parameters
            ],
            expected_outputs=[self._convert_output_to_schema(o) for o in action.expected_outputs],
            parameter_count=len(action.parameters),
            output_count=len(action.expected_outputs),
            robot_keywords=action.robot_keywords,
            execution_timeout=action.execution_timeout,
            retry_count=action.retry_count,
            tags=action.tags,
            is_active=action.is_active,
            created_at=action.created_at,
            updated_at=action.updated_at,
            version=f"{action.version}.0.0",
        )

    async def _convert_to_list_item_schema(
        self, action: Action
    ) -> ActionListItemSchema:
        """Convert action entity to list item schema."""
        return ActionListItemSchema(
            id=action.id,
            name=action.name,
            description=action.description,
            action_type=action.action_type.value,
            implementation_type=action.implementation_type.value,
            erpnext_module=action.erpnext_module,
            parameter_count=len(action.parameters),
            output_count=len(action.expected_outputs),
            expected_execution_time=action.expected_execution_time,
            tags=action.tags,
            is_active=action.is_active,
            created_at=action.created_at,
        )

    def _convert_parameter_to_schema(
        self, parameter: ActionParameter
    ) -> ActionParameterSchema:
        """Convert parameter entity to schema."""
        return ActionParameterSchema(
            name=parameter.name,
            param_type=parameter.parameter_type,
            required=parameter.is_required,
            description=parameter.description,
            default_value=parameter.default_value,
            validation_rules=parameter.validation_rules,
            examples=parameter.example_values,
        )

    def _convert_output_to_schema(self, output: ActionOutput) -> ActionOutputSchema:
        """Convert output entity to schema."""
        return ActionOutputSchema(
            name=output.name,
            output_type=output.output_type,
            description=output.description,
            required=True,  # Default to required
        )
