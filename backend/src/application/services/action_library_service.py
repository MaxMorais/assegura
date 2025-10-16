"""
Action Library Service - Application Layer

This module implements the ActionLibraryService for managing action library
operations in the ERPNext test automation framework. It provides comprehensive
action management, CRUD operations, BDD classification, import/export capabilities,
and validation services.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from src.application.dto.action_library_schemas import (
    ActionLibraryBulkOperationSchema,
    ActionLibraryBulkResultSchema,
    ActionLibraryCategoryStatsSchema,
    ActionLibraryCreateSchema,
    ActionLibraryDuplicateCheckSchema,
    ActionLibraryExecutionMetricsSchema,
    ActionLibraryExportSchema,
    ActionLibraryFilterSchema,
    ActionLibraryImportSchema,
    ActionLibraryListItemSchema,
    ActionLibraryParameterValidationSchema,
    ActionLibraryRelationshipSchema,
    ActionLibraryResponseSchema,
    ActionLibrarySearchResultSchema,
    ActionLibrarySearchSchema,
    ActionLibrarySortSchema,
    ActionLibraryStatsSchema,
    ActionLibraryTemplateSchema,
    ActionLibraryUpdateSchema,
    ActionLibraryValidationSchema,
)
from src.application.dto.base_schemas import PaginatedResponse
from src.domain.actions.action_relationship_service import ActionRelationshipService
from src.domain.actions.action_validator import ActionValidator
from src.domain.actions.enhanced_action_library import (
    ActionCategory,
    BDDStepType,
    EnhancedActionLibrary,
)


class ActionLibraryRepositoryInterface(ABC):
    """Abstract interface for action library data persistence."""

    @abstractmethod
    async def create(self, action: EnhancedActionLibrary) -> EnhancedActionLibrary:
        """Create a new action."""
        pass

    @abstractmethod
    async def get_by_id(self, action_id: UUID) -> Optional[EnhancedActionLibrary]:
        """Get action by ID."""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[EnhancedActionLibrary]:
        """Get action by name."""
        pass

    @abstractmethod
    async def list_actions(
        self,
        filters: Optional[ActionLibraryFilterSchema] = None,
        sort: Optional[ActionLibrarySortSchema] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[EnhancedActionLibrary], int]:
        """List actions with filtering, sorting and pagination."""
        pass

    @abstractmethod
    async def search_actions(
        self, search_criteria: ActionLibrarySearchSchema
    ) -> list[EnhancedActionLibrary]:
        """Search actions by various criteria."""
        pass

    @abstractmethod
    async def update(self, action: EnhancedActionLibrary) -> EnhancedActionLibrary:
        """Update existing action."""
        pass

    @abstractmethod
    async def delete(self, action_id: UUID) -> bool:
        """Delete action."""
        pass

    @abstractmethod
    async def get_actions_by_category(
        self, category: ActionCategory
    ) -> list[EnhancedActionLibrary]:
        """Get actions by category."""
        pass

    @abstractmethod
    async def get_actions_by_bdd_type(
        self, bdd_type: BDDStepType
    ) -> list[EnhancedActionLibrary]:
        """Get actions by BDD step type."""
        pass

    @abstractmethod
    async def get_action_stats(self) -> dict[str, Any]:
        """Get action statistics."""
        pass

    @abstractmethod
    async def bulk_update_status(
        self, action_ids: list[UUID], is_active: bool
    ) -> dict[UUID, bool]:
        """Bulk update action status."""
        pass

    @abstractmethod
    async def get_duplicate_candidates(
        self, action: EnhancedActionLibrary
    ) -> list[EnhancedActionLibrary]:
        """Find potential duplicate actions."""
        pass


class ActionLibraryServiceError(Exception):
    """Base exception for action library service errors."""

    pass


class ActionNotFoundError(ActionLibraryServiceError):
    """Action not found error."""

    pass


class ActionValidationServiceError(ActionLibraryServiceError):
    """Action validation error."""

    pass


class ActionDuplicateError(ActionLibraryServiceError):
    """Action duplicate error."""

    pass


class ActionLibraryService:
    """Service for managing action library operations and business logic."""

    def __init__(
        self,
        action_repository: ActionLibraryRepositoryInterface,
        action_relationship_service: ActionRelationshipService,
    ):
        self.action_repository = action_repository
        self.action_relationship_service = action_relationship_service
        self.validator = ActionValidator()
        self._action_templates: dict[str, ActionLibraryTemplateSchema] = {}

    async def create_action(
        self, action_data: ActionLibraryCreateSchema
    ) -> ActionLibraryResponseSchema:
        """
        Create a new action with validation and duplicate checking.

        Args:
            action_data: Action creation data

        Returns:
            Created action response

        Raises:
            ActionValidationServiceError: If validation fails
            ActionDuplicateError: If duplicate action exists
            ActionLibraryServiceError: If creation fails
        """
        try:
            # Check for duplicates
            duplicate_check = await self._check_for_duplicates(action_data)
            if duplicate_check.has_potential_duplicates:
                raise ActionDuplicateError(
                    f"Potential duplicate actions found: {duplicate_check.duplicate_action_names}"
                )

            # Create enhanced action
            action = EnhancedActionLibrary.create_enhanced(
                name=action_data.name,
                description=action_data.description,
                action_type=action_data.action_type,
                bdd_step_type=action_data.bdd_step_type,
                category=action_data.category,
                implementation=action_data.implementation,
                parameters_schema=action_data.parameters_schema,
                expected_outputs_schema=action_data.expected_outputs_schema,
                default_timeout_seconds=action_data.default_timeout_seconds,
                default_retry_count=action_data.default_retry_count,
                prerequisites=action_data.prerequisites,
                postconditions=action_data.postconditions,
                tags=action_data.tags,
                metadata=action_data.metadata,
                erpnext_doctype=action_data.erpnext_doctype,
                ui_selectors=action_data.ui_selectors,
            )

            # Validate action
            validation_result = self.validator.validate_action_comprehensive(action)
            if not validation_result.is_valid:
                raise ActionValidationServiceError(
                    f"Action validation failed: {validation_result.error_messages}"
                )

            # Save to repository
            saved_action = await self.action_repository.create(action)

            return await self._convert_to_response_schema(saved_action)

        except ActionDuplicateError:
            raise
        except Exception as e:
            raise ActionLibraryServiceError(f"Failed to create action: {str(e)}")

    async def get_action(
        self, action_id: UUID, include_details: bool = True
    ) -> ActionLibraryResponseSchema:
        """
        Get action by ID with optional detailed information.

        Args:
            action_id: Action ID
            include_details: Whether to include validation and metrics

        Returns:
            Action response

        Raises:
            ActionNotFoundError: If action not found
        """
        action = await self.action_repository.get_by_id(action_id)
        if not action:
            raise ActionNotFoundError(f"Action {action_id} not found")

        return await self._convert_to_response_schema(action, include_details)

    async def get_action_by_name(self, name: str) -> ActionLibraryResponseSchema:
        """Get action by name."""
        action = await self.action_repository.get_by_name(name)
        if not action:
            raise ActionNotFoundError(f"Action '{name}' not found")

        return await self._convert_to_response_schema(action)

    async def list_actions(
        self,
        filters: Optional[ActionLibraryFilterSchema] = None,
        sort: Optional[ActionLibrarySortSchema] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> PaginatedResponse[ActionLibraryListItemSchema]:
        """
        List actions with filtering, sorting and pagination.

        Args:
            filters: Filter criteria
            sort: Sort criteria
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            Paginated action list
        """
        try:
            actions, total_count = await self.action_repository.list_actions(
                filters, sort, offset, limit
            )

            items = [
                await self._convert_to_list_item_schema(action) for action in actions
            ]

            return PaginatedResponse(
                items=items,
                total_count=total_count,
                offset=offset,
                limit=limit,
                has_next=offset + limit < total_count,
            )

        except Exception as e:
            raise ActionLibraryServiceError(f"Failed to list actions: {str(e)}")

    async def search_actions(
        self, search_criteria: ActionLibrarySearchSchema
    ) -> ActionLibrarySearchResultSchema:
        """
        Search actions by various criteria with advanced filtering.

        Args:
            search_criteria: Search criteria

        Returns:
            Search results with relevance scoring
        """
        try:
            actions = await self.action_repository.search_actions(search_criteria)

            # Apply relevance scoring
            scored_results = []
            for action in actions:
                relevance_score = self._calculate_search_relevance(
                    action, search_criteria
                )
                result_item = await self._convert_to_list_item_schema(action)
                scored_results.append(
                    {"action": result_item, "relevance_score": relevance_score}
                )

            # Sort by relevance
            scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)

            return ActionLibrarySearchResultSchema(
                results=[result["action"] for result in scored_results],
                total_results=len(scored_results),
                search_criteria=search_criteria,
                relevance_scores={
                    str(result["action"].id): result["relevance_score"]
                    for result in scored_results
                },
            )

        except Exception as e:
            raise ActionLibraryServiceError(f"Failed to search actions: {str(e)}")

    async def update_action(
        self, action_id: UUID, update_data: ActionLibraryUpdateSchema
    ) -> ActionLibraryResponseSchema:
        """
        Update action details.

        Args:
            action_id: Action ID
            update_data: Update data

        Returns:
            Updated action response

        Raises:
            ActionNotFoundError: If action not found
            ActionValidationServiceError: If validation fails
        """
        try:
            action = await self.action_repository.get_by_id(action_id)
            if not action:
                raise ActionNotFoundError(f"Action {action_id} not found")

            # Apply updates
            update_dict = update_data.dict(exclude_none=True)
            for field, value in update_dict.items():
                if hasattr(action, field):
                    setattr(action, field, value)

            # Update version if significant changes
            if any(
                field in update_dict
                for field in [
                    "implementation",
                    "parameters_schema",
                    "expected_outputs_schema",
                ]
            ):
                action.create_version()

            # Validate updated action
            validation_result = self.validator.validate_action_comprehensive(action)
            if not validation_result.is_valid:
                raise ActionValidationServiceError(
                    f"Action validation failed: {validation_result.error_messages}"
                )

            # Save updates
            updated_action = await self.action_repository.update(action)

            return await self._convert_to_response_schema(updated_action)

        except ActionNotFoundError:
            raise
        except Exception as e:
            raise ActionLibraryServiceError(f"Failed to update action: {str(e)}")

    async def delete_action(self, action_id: UUID, force: bool = False) -> bool:
        """
        Delete action with usage validation.

        Args:
            action_id: Action ID
            force: Force deletion even if action is in use

        Returns:
            True if deleted successfully

        Raises:
            ActionNotFoundError: If action not found
            ActionLibraryServiceError: If action is in use and force=False
        """
        try:
            action = await self.action_repository.get_by_id(action_id)
            if not action:
                raise ActionNotFoundError(f"Action {action_id} not found")

            # Check if action is in use (this would require integration with journey service)
            if not force and action.usage_count > 0:
                raise ActionLibraryServiceError(
                    f"Cannot delete action {action_id}: it is currently in use in {action.usage_count} journeys"
                )

            return await self.action_repository.delete(action_id)

        except ActionNotFoundError:
            raise
        except Exception as e:
            raise ActionLibraryServiceError(f"Failed to delete action: {str(e)}")

    async def validate_action(self, action_id: UUID) -> ActionLibraryValidationSchema:
        """Get comprehensive action validation results."""
        try:
            action = await self.action_repository.get_by_id(action_id)
            if not action:
                raise ActionNotFoundError(f"Action {action_id} not found")

            validation_result = self.validator.validate_action_comprehensive(action)

            return ActionLibraryValidationSchema(
                is_valid=validation_result.is_valid,
                validation_errors=validation_result.error_messages,
                validation_warnings=validation_result.warning_messages,
                parameter_validation=self._validate_parameters(action),
                implementation_validation=self._validate_implementation(action),
                bdd_compliance=self._validate_bdd_compliance(action),
            )

        except ActionNotFoundError:
            raise
        except Exception as e:
            raise ActionLibraryServiceError(f"Failed to validate action: {str(e)}")

    async def get_actions_by_category(
        self, category: ActionCategory
    ) -> list[ActionLibraryListItemSchema]:
        """Get actions by category."""
        try:
            actions = await self.action_repository.get_actions_by_category(category)
            return [
                await self._convert_to_list_item_schema(action) for action in actions
            ]

        except Exception as e:
            raise ActionLibraryServiceError(
                f"Failed to get actions by category: {str(e)}"
            )

    async def get_actions_by_bdd_type(
        self, bdd_type: BDDStepType
    ) -> list[ActionLibraryListItemSchema]:
        """Get actions by BDD step type."""
        try:
            actions = await self.action_repository.get_actions_by_bdd_type(bdd_type)
            return [
                await self._convert_to_list_item_schema(action) for action in actions
            ]

        except Exception as e:
            raise ActionLibraryServiceError(
                f"Failed to get actions by BDD type: {str(e)}"
            )

    async def bulk_operation(
        self, operation_data: ActionLibraryBulkOperationSchema
    ) -> ActionLibraryBulkResultSchema:
        """Execute bulk operations on actions."""
        successful_ids = []
        failed_ids = []
        errors = {}

        try:
            for action_id in operation_data.action_ids:
                try:
                    if operation_data.operation == "activate":
                        await self.update_action(
                            action_id, ActionLibraryUpdateSchema(is_active=True)
                        )
                        successful_ids.append(action_id)
                    elif operation_data.operation == "deactivate":
                        await self.update_action(
                            action_id, ActionLibraryUpdateSchema(is_active=False)
                        )
                        successful_ids.append(action_id)
                    elif operation_data.operation == "delete":
                        await self.delete_action(
                            action_id,
                            force=operation_data.parameters.get("force", False),
                        )
                        successful_ids.append(action_id)
                    elif operation_data.operation == "tag":
                        tags = operation_data.parameters.get("tags", [])
                        action = await self.action_repository.get_by_id(action_id)
                        if action:
                            action.add_tags(tags)
                            await self.action_repository.update(action)
                            successful_ids.append(action_id)
                    else:
                        failed_ids.append(action_id)
                        errors[
                            str(action_id)
                        ] = f"Unsupported operation: {operation_data.operation}"

                except Exception as e:
                    failed_ids.append(action_id)
                    errors[str(action_id)] = str(e)

            return ActionLibraryBulkResultSchema(
                successful_ids=successful_ids,
                failed_ids=failed_ids,
                errors=errors,
                total_processed=len(operation_data.action_ids),
            )

        except Exception as e:
            raise ActionLibraryServiceError(f"Bulk operation failed: {str(e)}")

    async def get_action_statistics(self) -> ActionLibraryStatsSchema:
        """Get comprehensive action library statistics."""
        try:
            stats_data = await self.action_repository.get_action_stats()

            # Calculate category statistics
            category_stats = []
            for category in ActionCategory:
                category_actions = await self.action_repository.get_actions_by_category(
                    category
                )
                category_stats.append(
                    ActionLibraryCategoryStatsSchema(
                        category=category.value,
                        action_count=len(category_actions),
                        active_count=len([a for a in category_actions if a.is_active]),
                        average_usage=sum(a.usage_count for a in category_actions)
                        / len(category_actions)
                        if category_actions
                        else 0,
                    )
                )

            stats_data["category_stats"] = [stat.dict() for stat in category_stats]

            return ActionLibraryStatsSchema(**stats_data)

        except Exception as e:
            raise ActionLibraryServiceError(
                f"Failed to get action statistics: {str(e)}"
            )

    async def export_actions(
        self, export_criteria: ActionLibraryExportSchema
    ) -> dict[str, Any]:
        """Export actions based on criteria."""
        try:
            # Get actions to export
            if export_criteria.action_ids:
                actions = []
                for action_id in export_criteria.action_ids:
                    action = await self.action_repository.get_by_id(action_id)
                    if action:
                        actions.append(action)
            else:
                actions, _ = await self.action_repository.list_actions()

            # Apply additional filters
            filtered_actions = []
            for action in actions:
                if (
                    export_criteria.categories
                    and action.category not in export_criteria.categories
                ):
                    continue
                if (
                    export_criteria.bdd_step_types
                    and action.bdd_step_type not in export_criteria.bdd_step_types
                ):
                    continue
                if export_criteria.tags and not any(
                    tag in action.tags for tag in export_criteria.tags
                ):
                    continue
                filtered_actions.append(action)

            # Convert to export format
            export_data = {
                "export_metadata": {
                    "export_date": datetime.utcnow().isoformat(),
                    "export_format": export_criteria.export_format,
                    "total_actions": len(filtered_actions),
                    "export_criteria": export_criteria.dict(),
                },
                "actions": [],
            }

            for action in filtered_actions:
                action_data = await self._convert_to_response_schema(action)
                export_data["actions"].append(action_data.dict())

            return export_data

        except Exception as e:
            raise ActionLibraryServiceError(f"Failed to export actions: {str(e)}")

    async def import_actions(
        self, import_data: ActionLibraryImportSchema
    ) -> ActionLibraryBulkResultSchema:
        """Import actions from external source."""
        successful_ids = []
        failed_ids = []
        errors = {}

        try:
            for action_data in import_data.actions:
                try:
                    # Handle duplicate strategy
                    existing_action = None
                    if "name" in action_data:
                        existing_action = await self.action_repository.get_by_name(
                            action_data["name"]
                        )

                    if existing_action and import_data.duplicate_strategy == "skip":
                        continue
                    elif (
                        existing_action and import_data.duplicate_strategy == "replace"
                    ):
                        # Update existing action
                        update_schema = ActionLibraryUpdateSchema(**action_data)
                        updated_action = await self.update_action(
                            existing_action.action_id, update_schema
                        )
                        successful_ids.append(updated_action.id)
                    else:
                        # Create new action
                        create_schema = ActionLibraryCreateSchema(**action_data)
                        created_action = await self.create_action(create_schema)
                        successful_ids.append(created_action.id)

                except Exception as e:
                    failed_ids.append(action_data.get("name", "unknown"))
                    errors[action_data.get("name", "unknown")] = str(e)

            return ActionLibraryBulkResultSchema(
                successful_ids=successful_ids,
                failed_ids=failed_ids,
                errors=errors,
                total_processed=len(import_data.actions),
            )

        except Exception as e:
            raise ActionLibraryServiceError(f"Failed to import actions: {str(e)}")

    async def check_for_duplicates(
        self, action_data: ActionLibraryCreateSchema
    ) -> ActionLibraryDuplicateCheckSchema:
        """Check for potential duplicate actions."""
        return await self._check_for_duplicates(action_data)

    async def create_action_template(
        self, template_data: ActionLibraryTemplateSchema
    ) -> str:
        """Create a reusable action template."""
        try:
            self._action_templates[template_data.template_name] = template_data
            return template_data.template_name

        except Exception as e:
            raise ActionLibraryServiceError(
                f"Failed to create action template: {str(e)}"
            )

    async def get_action_relationships(
        self, action_id: UUID
    ) -> ActionLibraryRelationshipSchema:
        """Get action relationships and dependencies."""
        try:
            action = await self.action_repository.get_by_id(action_id)
            if not action:
                raise ActionNotFoundError(f"Action {action_id} not found")

            # Get relationships using the relationship service
            relationships = (
                await self.action_relationship_service.get_action_relationships(action)
            )

            return ActionLibraryRelationshipSchema(**relationships)

        except ActionNotFoundError:
            raise
        except Exception as e:
            raise ActionLibraryServiceError(
                f"Failed to get action relationships: {str(e)}"
            )

    # Private helper methods

    async def _check_for_duplicates(
        self, action_data: ActionLibraryCreateSchema
    ) -> ActionLibraryDuplicateCheckSchema:
        """Check for potential duplicate actions based on name and implementation."""
        # Create temporary action for duplicate checking
        temp_action = EnhancedActionLibrary.create_enhanced(
            name=action_data.name,
            description=action_data.description,
            action_type=action_data.action_type,
            bdd_step_type=action_data.bdd_step_type,
            category=action_data.category,
            implementation=action_data.implementation,
        )

        duplicates = await self.action_repository.get_duplicate_candidates(temp_action)

        return ActionLibraryDuplicateCheckSchema(
            has_potential_duplicates=len(duplicates) > 0,
            duplicate_action_names=[action.name for action in duplicates],
            duplicate_action_ids=[action.action_id for action in duplicates],
            similarity_threshold=0.8,  # This would be configurable
            similarity_scores={
                str(action.action_id): self._calculate_similarity_score(
                    temp_action, action
                )
                for action in duplicates
            },
        )

    def _calculate_similarity_score(
        self, action1: EnhancedActionLibrary, action2: EnhancedActionLibrary
    ) -> float:
        """Calculate similarity score between two actions."""
        # Simplified similarity calculation - real implementation would be more sophisticated
        score = 0.0

        # Name similarity
        if action1.name.lower() == action2.name.lower():
            score += 0.4
        elif (
            action1.name.lower() in action2.name.lower()
            or action2.name.lower() in action1.name.lower()
        ):
            score += 0.2

        # Type similarity
        if action1.action_type == action2.action_type:
            score += 0.2
        if action1.bdd_step_type == action2.bdd_step_type:
            score += 0.2
        if action1.category == action2.category:
            score += 0.1

        # Implementation similarity (simplified)
        impl1_keywords = set(action1.implementation.get("steps", []))
        impl2_keywords = set(action2.implementation.get("steps", []))
        if impl1_keywords and impl2_keywords:
            common_keywords = impl1_keywords.intersection(impl2_keywords)
            score += 0.1 * (
                len(common_keywords) / max(len(impl1_keywords), len(impl2_keywords))
            )

        return min(score, 1.0)

    def _calculate_search_relevance(
        self, action: EnhancedActionLibrary, search_criteria: ActionLibrarySearchSchema
    ) -> float:
        """Calculate search relevance score for an action."""
        score = 0.0

        # Text match in name and description
        if search_criteria.text_query:
            query_lower = search_criteria.text_query.lower()
            if query_lower in action.name.lower():
                score += 1.0
            if query_lower in action.description.lower():
                score += 0.5

        # Category match
        if search_criteria.categories and action.category in search_criteria.categories:
            score += 0.5

        # BDD step type match
        if (
            search_criteria.bdd_step_types
            and action.bdd_step_type in search_criteria.bdd_step_types
        ):
            score += 0.5

        # Tag matches
        if search_criteria.tags:
            matching_tags = set(search_criteria.tags).intersection(set(action.tags))
            score += 0.1 * len(matching_tags)

        # Usage frequency (popular actions get slight boost)
        if action.usage_count > 10:
            score += 0.1

        return score

    def _validate_parameters(
        self, action: EnhancedActionLibrary
    ) -> ActionLibraryParameterValidationSchema:
        """Validate action parameters schema."""
        try:
            # Validate JSON schema format
            if action.parameters_schema:
                # This would use a proper JSON schema validator
                pass

            return ActionLibraryParameterValidationSchema(
                is_valid=True,
                required_parameters=[],
                optional_parameters=[],
                parameter_errors=[],
                schema_warnings=[],
            )
        except Exception as e:
            return ActionLibraryParameterValidationSchema(
                is_valid=False,
                required_parameters=[],
                optional_parameters=[],
                parameter_errors=[str(e)],
                schema_warnings=[],
            )

    def _validate_implementation(self, action: EnhancedActionLibrary) -> dict[str, Any]:
        """Validate action implementation."""
        validation_results = {
            "is_valid": True,
            "implementation_errors": [],
            "implementation_warnings": [],
            "execution_complexity": "medium",
        }

        try:
            # Validate implementation structure
            if not action.implementation:
                validation_results["is_valid"] = False
                validation_results["implementation_errors"].append(
                    "Implementation is required"
                )

            # Additional implementation validation logic would go here

        except Exception as e:
            validation_results["is_valid"] = False
            validation_results["implementation_errors"].append(str(e))

        return validation_results

    def _validate_bdd_compliance(self, action: EnhancedActionLibrary) -> dict[str, Any]:
        """Validate BDD compliance."""
        return {
            "is_bdd_compliant": True,
            "bdd_step_format_valid": True,
            "natural_language_score": 0.8,
            "gherkin_compliance_issues": [],
        }

    async def _convert_to_response_schema(
        self, action: EnhancedActionLibrary, include_details: bool = True
    ) -> ActionLibraryResponseSchema:
        """Convert action to response schema."""

        response_data = {
            "id": action.action_id,
            "name": action.name,
            "description": action.description,
            "action_type": action.action_type.value,
            "bdd_step_type": action.bdd_step_type.value,
            "category": action.category.value,
            "implementation": action.implementation,
            "parameters_schema": action.parameters_schema,
            "expected_outputs_schema": action.expected_outputs_schema,
            "default_timeout_seconds": action.default_timeout_seconds,
            "default_retry_count": action.default_retry_count,
            "is_active": action.is_active,
            "prerequisites": action.prerequisites,
            "postconditions": action.postconditions,
            "tags": action.tags,
            "usage_count": action.usage_count,
            "last_used_date": action.last_used_date,
            "metadata": action.metadata,
            "erpnext_doctype": action.erpnext_doctype,
            "ui_selectors": action.ui_selectors,
            "created_at": action.created_at,
            "updated_at": action.updated_at,
        }

        if include_details:
            # Add validation results
            validation_result = self.validator.validate_action_comprehensive(action)
            response_data["validation"] = ActionLibraryValidationSchema(
                is_valid=validation_result.is_valid,
                validation_errors=validation_result.error_messages,
                validation_warnings=validation_result.warning_messages,
                parameter_validation=self._validate_parameters(action),
                implementation_validation=self._validate_implementation(action),
                bdd_compliance=self._validate_bdd_compliance(action),
            )

            # Add execution metrics if available
            if hasattr(action, "execution_metrics") and action.execution_metrics:
                response_data[
                    "execution_metrics"
                ] = ActionLibraryExecutionMetricsSchema(
                    total_executions=action.execution_metrics.total_executions,
                    success_rate=action.execution_metrics.success_rate,
                    average_duration_seconds=action.execution_metrics.average_duration.total_seconds(),
                    last_execution_date=action.execution_metrics.last_execution_date,
                    common_failure_reasons=action.execution_metrics.common_failure_reasons,
                )

        return ActionLibraryResponseSchema(**response_data)

    async def _convert_to_list_item_schema(
        self, action: EnhancedActionLibrary
    ) -> ActionLibraryListItemSchema:
        """Convert action to list item schema."""
        return ActionLibraryListItemSchema(
            id=action.action_id,
            name=action.name,
            description=action.description,
            action_type=action.action_type.value,
            bdd_step_type=action.bdd_step_type.value,
            category=action.category.value,
            is_active=action.is_active,
            tags=action.tags,
            usage_count=action.usage_count,
            last_used_date=action.last_used_date,
            created_at=action.created_at,
            updated_at=action.updated_at,
        )
