"""
Journey-Action Relationships and Step Management

This module implements the relationship management between journeys and actions,
providing services for step management, action lifecycle, and journey execution
coordination within the ERPNext test automation framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from ..actions.action_library import Action, ActionType
from ..actions.action_types import ActionClassificationService
from ..actions.parameter_structures import ParameterSetValidator
from .enhanced_journey import ActionStepEnhanced, EnhancedJourney
from .journey_validation_error import JourneyValidationError
from .journey_validator import JourneyValidator, ValidationResult


class StepExecutionStatus(Enum):
    """Step execution status states."""

    PENDING = "pending"  # Step not yet executed
    RUNNING = "running"  # Step currently executing
    COMPLETED = "completed"  # Step completed successfully
    FAILED = "failed"  # Step execution failed
    SKIPPED = "skipped"  # Step was skipped
    RETRYING = "retrying"  # Step is being retried
    CANCELLED = "cancelled"  # Step execution was cancelled


class ActionLinkType(Enum):
    """Types of relationships between actions and journey steps."""

    DIRECT = "direct"  # Direct action execution
    TEMPLATE = "template"  # Action used as template (parameters customized)
    DERIVED = "derived"  # Action derived from another action
    COMPOSED = "composed"  # Multiple actions composed into one step


@dataclass
class StepExecutionResult:
    """Result of executing a journey step."""

    step_number: int
    action_id: UUID
    status: StepExecutionStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    outputs: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    execution_context: dict[str, Any] = field(default_factory=dict)

    @property
    def is_successful(self) -> bool:
        """Check if step execution was successful."""
        return self.status == StepExecutionStatus.COMPLETED

    @property
    def execution_duration(self) -> Optional[timedelta]:
        """Get execution duration as timedelta."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


@dataclass
class ActionUsageInfo:
    """Information about how an action is used in journeys."""

    action_id: UUID
    action_name: str
    usage_count: int = 0
    journey_references: list[UUID] = field(default_factory=list)
    parameter_variations: list[dict[str, Any]] = field(default_factory=list)
    common_patterns: list[str] = field(default_factory=list)
    success_rate: float = 0.0
    average_duration: Optional[timedelta] = None

    def add_usage(self, journey_id: UUID, parameters: dict[str, Any]) -> None:
        """Add usage information for this action."""
        self.usage_count += 1
        if journey_id not in self.journey_references:
            self.journey_references.append(journey_id)
        if parameters not in self.parameter_variations:
            self.parameter_variations.append(parameters)


class ActionRepository(ABC):
    """Abstract repository for action persistence and retrieval."""

    @abstractmethod
    async def get_action_by_id(self, action_id: UUID) -> Optional[Action]:
        """Get action by ID."""
        pass

    @abstractmethod
    async def search_actions(
        self,
        action_type: Optional[ActionType] = None,
        erpnext_module: Optional[str] = None,
        tags: Optional[list[str]] = None,
        text_search: Optional[str] = None,
    ) -> list[Action]:
        """Search actions by criteria."""
        pass

    @abstractmethod
    async def save_action(self, action: Action) -> Action:
        """Save action to repository."""
        pass

    @abstractmethod
    async def get_action_usage_stats(self, action_id: UUID) -> ActionUsageInfo:
        """Get usage statistics for an action."""
        pass


class JourneyActionService:
    """Service for managing journey-action relationships."""

    def __init__(self, action_repository: ActionRepository):
        self.action_repository = action_repository
        self.validator = JourneyValidator()
        self._step_templates: dict[str, ActionStepEnhanced] = {}
        self._execution_history: dict[UUID, list[StepExecutionResult]] = {}

    async def add_action_to_journey(
        self,
        journey: EnhancedJourney,
        action_id: UUID,
        parameters: dict[str, Any],
        position: Optional[int] = None,
        step_customization: Optional[dict[str, Any]] = None,
    ) -> ActionStepEnhanced:
        """
        Add an action as a step to a journey.

        Args:
            journey: Target journey
            action_id: ID of action to add
            parameters: Step parameters
            position: Position to insert step (None = append)
            step_customization: Additional step configuration

        Returns:
            The created step

        Raises:
            JourneyValidationError: If action cannot be added
        """
        # Retrieve action
        action = await self.action_repository.get_by_id(action_id)
        if not action:
            raise JourneyValidationError(f"Action {action_id} not found")

        # Validate parameters
        if action.parameters:
            validator = ParameterSetValidator(action.parameters)
            param_errors = validator.validate_parameter_set(parameters)
            if param_errors:
                error_details = "; ".join(
                    [
                        f"{param}: {', '.join(errors)}"
                        for param, errors in param_errors.items()
                    ]
                )
                raise JourneyValidationError(f"Invalid parameters: {error_details}")

        # Apply step customization
        step_kwargs = step_customization or {}

        # Add to journey
        journey.add_action_step(
            action=action, parameters=parameters, position=position, **step_kwargs
        )

        # Get the added step
        step_index = position - 1 if position else len(journey.enhanced_steps) - 1
        added_step = journey.enhanced_steps[step_index]

        # Update action usage
        await self._update_action_usage(action_id, journey.id, parameters)

        return added_step

    async def replace_action_in_step(
        self,
        journey: EnhancedJourney,
        step_number: int,
        new_action_id: UUID,
        parameters: Optional[dict[str, Any]] = None,
    ) -> ActionStepEnhanced:
        """Replace the action in an existing step."""
        if step_number < 1 or step_number > len(journey.enhanced_steps):
            raise JourneyValidationError(f"Invalid step number: {step_number}")

        # Get new action
        new_action = await self.action_repository.get_action_by_id(new_action_id)
        if not new_action:
            raise JourneyValidationError(f"Action {new_action_id} not found")

        # Get current step
        current_step = journey.enhanced_steps[step_number - 1]

        # Use provided parameters or try to adapt existing ones
        new_parameters = parameters
        if new_parameters is None:
            new_parameters = await self._adapt_parameters(
                current_step.parameters, current_step.action, new_action
            )

        # Validate new parameters
        if new_action.parameters:
            validator = ParameterSetValidator(new_action.parameters)
            param_errors = validator.validate_parameter_set(new_parameters)
            if param_errors:
                error_details = "; ".join(
                    [
                        f"{param}: {', '.join(errors)}"
                        for param, errors in param_errors.items()
                    ]
                )
                raise JourneyValidationError(
                    f"Invalid parameters for new action: {error_details}"
                )

        # Remove old step and add new one
        journey.remove_enhanced_step(step_number)
        journey.add_action_step(
            action=new_action,
            parameters=new_parameters,
            position=step_number,
            step_description=current_step.step_description,
            timeout_override=current_step.timeout_override,
            retry_override=current_step.retry_override,
            depends_on_steps=current_step.depends_on_steps,
            can_run_parallel=current_step.can_run_parallel,
            is_critical=current_step.is_critical,
        )

        return journey.enhanced_steps[step_number - 1]

    async def suggest_actions_for_journey(
        self, journey: EnhancedJourney, context: Optional[dict[str, Any]] = None
    ) -> list[tuple[Action, float]]:
        """
        Suggest actions that would fit well in the journey.

        Args:
            journey: Journey to analyze
            context: Additional context for suggestions

        Returns:
            List of (action, confidence_score) tuples
        """
        suggestions = []

        # Analyze current journey state
        journey_summary = journey.get_actions_summary()
        current_action_types = journey_summary.get("action_types", {})
        current_modules = journey_summary.get("erpnext_modules", [])

        # Determine what's missing for complete BDD flow
        missing_types = []
        if not current_action_types.get("given"):
            missing_types.append(ActionType.GIVEN)
        if not current_action_types.get("when"):
            missing_types.append(ActionType.WHEN)
        if not current_action_types.get("then"):
            missing_types.append(ActionType.THEN)

        # Search for actions to complete BDD flow
        for action_type in missing_types:
            actions = await self.action_repository.search_actions(
                action_type=action_type
            )
            for action in actions:
                confidence = await self._calculate_action_fit_score(
                    action, journey, context
                )
                if confidence > 0.3:  # Only suggest reasonably fitting actions
                    suggestions.append((action, confidence))

        # Search for actions in same ERPNext modules
        for module in current_modules:
            actions = await self.action_repository.search_actions(erpnext_module=module)
            for action in actions:
                # Skip if already used
                if any(
                    step.action.action_id == action.action_id
                    for step in journey.enhanced_steps
                ):
                    continue

                confidence = await self._calculate_action_fit_score(
                    action, journey, context
                )
                if confidence > 0.4:  # Higher threshold for module-based suggestions
                    suggestions.append((action, confidence))

        # Sort by confidence and remove duplicates
        unique_suggestions = {}
        for action, confidence in suggestions:
            if action.action_id not in unique_suggestions:
                unique_suggestions[action.action_id] = (action, confidence)
            else:
                # Keep higher confidence
                existing_confidence = unique_suggestions[action.action_id][1]
                if confidence > existing_confidence:
                    unique_suggestions[action.action_id] = (action, confidence)

        # Return sorted suggestions
        return sorted(unique_suggestions.values(), key=lambda x: x[1], reverse=True)

    async def create_step_template(
        self,
        template_name: str,
        action: Action,
        default_parameters: dict[str, Any],
        description: Optional[str] = None,
    ) -> str:
        """Create a reusable step template."""
        template_step = ActionStepEnhanced(
            step_number=0,  # Templates don't have step numbers
            action=action,
            parameters=default_parameters,
            expected_outputs={},
            step_description=description or f"Template: {action.name}",
        )

        self._step_templates[template_name] = template_step
        return template_name

    async def apply_step_template(
        self,
        journey: EnhancedJourney,
        template_name: str,
        parameter_overrides: Optional[dict[str, Any]] = None,
        position: Optional[int] = None,
    ) -> ActionStepEnhanced:
        """Apply a step template to a journey."""
        if template_name not in self._step_templates:
            raise JourneyValidationError(f"Step template '{template_name}' not found")

        template = self._step_templates[template_name]

        # Merge parameters
        parameters = template.parameters.copy()
        if parameter_overrides:
            parameters.update(parameter_overrides)

        # Add step to journey
        return await self.add_action_to_journey(
            journey=journey,
            action_id=template.action.action_id,
            parameters=parameters,
            position=position,
            step_customization={
                "step_description": template.step_description,
                "timeout_override": template.timeout_override,
                "retry_override": template.retry_override,
            },
        )

    async def optimize_journey_steps(self, journey: EnhancedJourney) -> list[str]:
        """
        Optimize journey steps for better performance and maintainability.

        Returns:
            List of optimization suggestions applied
        """
        optimizations = []

        # Identify redundant steps
        redundant_pairs = await self._find_redundant_steps(journey)
        for step1, step2 in redundant_pairs:
            # Remove the later redundant step
            journey.remove_enhanced_step(step2.step_number)
            optimizations.append(f"Removed redundant step {step2.step_number}")

        # Optimize step ordering for better flow
        reordering_suggestions = await self._suggest_step_reordering(journey)
        for from_pos, to_pos, reason in reordering_suggestions:
            journey.move_step(from_pos, to_pos)
            optimizations.append(
                f"Moved step {from_pos} to position {to_pos}: {reason}"
            )

        # Merge compatible steps
        merge_suggestions = await self._find_mergeable_steps(journey)
        for step_numbers, merged_action in merge_suggestions:
            # This would require creating composite actions
            optimizations.append(f"Suggested merging steps {step_numbers}")

        return optimizations

    async def validate_journey_with_actions(
        self, journey: EnhancedJourney
    ) -> list[ValidationResult]:
        """Validate journey including action-specific rules."""
        # Basic validation
        results = self.validator.validate_journey(journey)

        # Action-specific validation
        for step in journey.enhanced_steps:
            action = step.action

            # Check action availability/deprecation
            if hasattr(action, "is_deprecated") and action.is_deprecated:
                results.append(
                    ValidationResult(
                        rule_name="Action Availability",
                        severity=self.validator.rules[
                            0
                        ].severity,  # Use first rule's default severity
                        message=f"Step {step.step_number} uses deprecated action '{action.name}'",
                        affected_steps=[step.step_number],
                        suggested_fix="Replace with updated action version",
                    )
                )

            # Check parameter compatibility
            param_validation = step.validate_parameters()
            if param_validation:
                results.append(
                    ValidationResult(
                        rule_name="Parameter Validation",
                        severity=self.validator.rules[0].severity,
                        message=f"Step {step.step_number} has parameter issues: {'; '.join(param_validation)}",
                        affected_steps=[step.step_number],
                        suggested_fix="Update parameters to match action requirements",
                    )
                )

        return results

    async def get_journey_execution_plan(
        self, journey: EnhancedJourney
    ) -> dict[str, Any]:
        """Get detailed execution plan for journey."""
        plan = journey.generate_execution_plan()

        # Enhance with action-specific information
        action_details = []
        for step in journey.enhanced_steps:
            usage_info = await self.action_repository.get_action_usage_stats(
                step.action.action_id
            )

            action_details.append(
                {
                    "step_number": step.step_number,
                    "action_id": str(step.action.action_id),
                    "action_name": step.action.name,
                    "estimated_duration": step.get_effective_timeout(),
                    "retry_count": step.get_effective_retry_count(),
                    "success_rate": usage_info.success_rate,
                    "usage_count": usage_info.usage_count,
                    "complexity_score": ActionClassificationService.get_action_complexity_score(
                        step.action
                    ),
                    "can_parallelize": step.can_run_parallel,
                    "is_critical": step.is_critical,
                }
            )

        return {
            "plan": {
                "total_steps": plan.total_steps,
                "estimated_duration_seconds": plan.estimated_duration.total_seconds(),
                "complexity_score": plan.complexity_score,
                "can_parallelize": plan.can_execute_parallel,
                "parallel_sections": plan.parallel_executable_steps,
                "critical_path": plan.critical_path_steps,
                "rollback_points": plan.rollback_points,
            },
            "steps": action_details,
            "resource_requirements": plan.resource_requirements,
        }

    async def _adapt_parameters(
        self, old_parameters: dict[str, Any], old_action: Action, new_action: Action
    ) -> dict[str, Any]:
        """Adapt parameters when replacing an action."""
        adapted = {}

        if not new_action.parameters:
            return adapted

        # Map parameters by name first (exact matches)
        old_param_names = set(old_parameters.keys())
        new_param_names = {param.name for param in new_action.parameters}

        # Direct mapping
        for param_name in old_param_names.intersection(new_param_names):
            adapted[param_name] = old_parameters[param_name]

        # Try semantic mapping for remaining parameters
        remaining_old = old_param_names - new_param_names
        remaining_new = new_param_names - old_param_names

        semantic_mappings = {
            "document_name": ["name", "doc_name", "id"],
            "doctype": ["document_type", "type"],
            "data": ["field_data", "fields", "values"],
            "selector": ["element", "locator", "xpath"],
        }

        for old_name in remaining_old:
            old_value = old_parameters[old_name]

            # Check semantic mappings
            for new_name in remaining_new:
                if self._are_parameters_compatible(
                    old_name, new_name, semantic_mappings
                ):
                    adapted[new_name] = old_value
                    remaining_new.remove(new_name)
                    break

        return adapted

    def _are_parameters_compatible(
        self, old_name: str, new_name: str, mappings: dict[str, list[str]]
    ) -> bool:
        """Check if two parameter names are semantically compatible."""
        # Direct similarity
        if old_name.lower() in new_name.lower() or new_name.lower() in old_name.lower():
            return True

        # Semantic mapping
        for canonical, variants in mappings.items():
            if old_name in variants and new_name in variants:
                return True
            if old_name == canonical and new_name in variants:
                return True
            if new_name == canonical and old_name in variants:
                return True

        return False

    async def _calculate_action_fit_score(
        self,
        action: Action,
        journey: EnhancedJourney,
        context: Optional[dict[str, Any]],
    ) -> float:
        """Calculate how well an action fits in the journey."""
        score = 0.0

        # ERPNext module compatibility
        journey_modules = journey.get_actions_summary().get("erpnext_modules", [])
        if action.erpnext_module in journey_modules:
            score += 0.3

        # Action type balance
        journey_types = journey.get_actions_summary().get("action_types", {})
        action_type = action.action_type.value

        # Encourage completing BDD flow
        if action_type == "given" and not journey_types.get("given"):
            score += 0.4
        elif action_type == "when" and not journey_types.get("when"):
            score += 0.4
        elif action_type == "then" and not journey_types.get("then"):
            score += 0.4

        # Usage statistics
        usage_info = await self.action_repository.get_action_usage_stats(
            action.action_id
        )
        if usage_info.success_rate > 0.8:
            score += 0.2

        # Context matching
        if context:
            context_modules = context.get("preferred_modules", [])
            if action.erpnext_module in context_modules:
                score += 0.2

        return min(score, 1.0)  # Cap at 1.0

    async def _find_redundant_steps(
        self, journey: EnhancedJourney
    ) -> list[tuple[ActionStepEnhanced, ActionStepEnhanced]]:
        """Find redundant steps in the journey."""
        redundant_pairs = []

        steps = journey.enhanced_steps
        for i in range(len(steps)):
            for j in range(i + 1, len(steps)):
                step1, step2 = steps[i], steps[j]

                # Same action with similar parameters
                if step1.action.action_id == step2.action.action_id:
                    param_similarity = self._calculate_parameter_similarity(
                        step1.parameters, step2.parameters
                    )
                    if param_similarity > 0.8:
                        redundant_pairs.append((step1, step2))

        return redundant_pairs

    def _calculate_parameter_similarity(
        self, params1: dict[str, Any], params2: dict[str, Any]
    ) -> float:
        """Calculate similarity between parameter sets."""
        if not params1 and not params2:
            return 1.0

        if not params1 or not params2:
            return 0.0

        all_keys = set(params1.keys()) | set(params2.keys())
        matching_keys = 0

        for key in all_keys:
            if key in params1 and key in params2 and params1[key] == params2[key]:
                matching_keys += 1

        return matching_keys / len(all_keys)

    async def _suggest_step_reordering(
        self, journey: EnhancedJourney
    ) -> list[tuple[int, int, str]]:
        """Suggest better ordering for journey steps."""
        suggestions = []

        steps = journey.enhanced_steps

        # Check BDD ordering
        for i, step in enumerate(steps):
            action_type = step.action.action_type

            # Given steps should be early
            if action_type == ActionType.GIVEN and i > len(steps) // 3:
                # Find better position (earlier in sequence)
                for j in range(i):
                    if steps[j].action.action_type != ActionType.GIVEN:
                        suggestions.append((i + 1, j + 1, "Move Given step earlier"))
                        break

            # Then steps should be later
            if action_type == ActionType.THEN and i < len(steps) // 2:
                # Find better position (later in sequence)
                for j in range(i + 1, len(steps)):
                    if steps[j].action.action_type != ActionType.THEN:
                        suggestions.append((i + 1, j + 1, "Move Then step later"))
                        break

        return suggestions

    async def _find_mergeable_steps(
        self, journey: EnhancedJourney
    ) -> list[tuple[list[int], Action]]:
        """Find steps that could be merged into composite actions."""
        # This is a placeholder for more complex step merging logic
        # Would require creating composite actions from multiple simple ones
        return []

    async def _update_action_usage(
        self, action_id: UUID, journey_id: UUID, parameters: dict[str, Any]
    ) -> None:
        """Update action usage statistics."""
        # This would typically update the action repository with usage information
        pass

    def record_step_execution(self, execution_result: StepExecutionResult) -> None:
        """Record the result of step execution."""
        journey_id = execution_result.execution_context.get("journey_id")
        if journey_id:
            if journey_id not in self._execution_history:
                self._execution_history[journey_id] = []
            self._execution_history[journey_id].append(execution_result)

    def get_execution_history(self, journey_id: UUID) -> list[StepExecutionResult]:
        """Get execution history for a journey."""
        return self._execution_history.get(journey_id, [])

    def get_step_templates(self) -> dict[str, ActionStepEnhanced]:
        """Get all available step templates."""
        return self._step_templates.copy()
