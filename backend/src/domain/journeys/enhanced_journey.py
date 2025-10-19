"""
Enhanced Journey Domain Entity with Action Library Integration

This module extends the existing Journey entity to integrate with the comprehensive
Action Library system, providing advanced step sequencing, action validation,
and execution planning capabilities.
"""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from ..actions.action_library import Action, ActionType
from ..actions.action_types import ActionClassificationService
from ..actions.parameter_structures import ParameterSetValidator
from .journey import Journey as BaseJourney
from .journey_step import JourneyStep
from .journey_validation_error import JourneyValidationError


class JourneyExecutionStatus(Enum):
    """Journey execution status states."""

    DRAFT = "draft"  # Journey is being created/edited
    READY = "ready"  # Journey is ready for execution
    RUNNING = "running"  # Journey is currently executing
    COMPLETED = "completed"  # Journey execution completed successfully
    FAILED = "failed"  # Journey execution failed
    CANCELLED = "cancelled"  # Journey execution was cancelled
    SUSPENDED = "suspended"  # Journey execution is paused


class JourneyComplexityLevel(Enum):
    """Journey complexity levels with execution characteristics."""

    SIMPLE = "simple"  # 1-5 steps, basic actions
    MEDIUM = "medium"  # 6-15 steps, moderate complexity
    COMPLEX = "complex"  # 16-30 steps, advanced logic
    ADVANCED = "advanced"  # 30+ steps, expert level


@dataclass
class JourneyExecutionPlan:
    """Execution plan for a journey with timing and resource estimates."""

    total_steps: int
    estimated_duration: timedelta
    complexity_score: int
    resource_requirements: list[str]
    parallel_executable_steps: list[tuple[int, int]]  # (start_step, end_step) ranges
    critical_path_steps: list[int]
    rollback_points: list[int]

    @property
    def can_execute_parallel(self) -> bool:
        """Check if journey has parallelizable sections."""
        return len(self.parallel_executable_steps) > 0

    @property
    def has_critical_path(self) -> bool:
        """Check if journey has identified critical path."""
        return len(self.critical_path_steps) > 0


@dataclass
class ActionStepEnhanced:
    """Enhanced step with full action integration and validation."""

    step_number: int
    action: Action
    parameters: dict[str, Any]
    expected_outputs: dict[str, Any]
    step_description: Optional[str] = None
    timeout_override: Optional[int] = None
    retry_override: Optional[int] = None
    depends_on_steps: Optional[list[int]] = None
    can_run_parallel: bool = False
    is_critical: bool = False
    rollback_action: Optional[Action] = None

    def validate_parameters(self) -> list[str]:
        """Validate step parameters against action requirements."""
        if not self.action.parameters:
            return []

        validator = ParameterSetValidator([param for param in self.action.parameters])

        errors = validator.validate_parameter_set(self.parameters)
        return [error for error_list in errors.values() for error in error_list]

    def get_effective_timeout(self) -> int:
        """Get effective timeout (override or action default)."""
        return self.timeout_override or self.action.execution_timeout or 60

    def get_effective_retry_count(self) -> int:
        """Get effective retry count (override or action default)."""
        return (
            self.retry_override
            if self.retry_override is not None
            else self.action.retry_count or 0
        )


class EnhancedJourney(BaseJourney):
    """Enhanced Journey with Action Library integration."""

    _enhanced_steps: list[ActionStepEnhanced] = []
    _action_cache: dict[UUID, Action] = {}
    _execution_status: JourneyExecutionStatus = JourneyExecutionStatus.DRAFT
    _execution_plan: Optional[JourneyExecutionPlan] = None
    _validation_cache: dict[str, list[str]] = {}

    def __init__(self, *args, **kwargs):
        # Call parent first in Pydantic V2
        super().__init__(*args, **kwargs)

    @property
    def enhanced_steps(self) -> list[ActionStepEnhanced]:
        """Get enhanced action steps."""
        return self._enhanced_steps.copy()

    @property
    def execution_status(self) -> JourneyExecutionStatus:
        """Get current execution status."""
        return self._execution_status

    @execution_status.setter
    def execution_status(self, status: JourneyExecutionStatus) -> None:
        """Set execution status."""
        self._execution_status = status

    @property
    def is_active(self) -> bool:
        """Get active status."""
        return self._is_active

    @is_active.setter
    def is_active(self, active: bool) -> None:
        """Set active status."""
        self._is_active = active

    @property
    def execution_plan(self) -> Optional[JourneyExecutionPlan]:
        """Get execution plan."""
        return self._execution_plan

    @property
    def is_complete_scenario(self) -> bool:
        """Check if journey represents a complete BDD scenario."""
        return (
            self.has_given_steps and
            self.has_when_steps and
            self.has_then_steps
        )

    @property
    def has_given_steps(self) -> bool:
        """Check if journey has Given steps."""
        return any(step.action.action_type == ActionType.GIVEN for step in self._enhanced_steps)

    @property
    def has_when_steps(self) -> bool:
        """Check if journey has When steps."""
        return any(step.action.action_type == ActionType.WHEN for step in self._enhanced_steps)

    @property
    def has_then_steps(self) -> bool:
        """Check if journey has Then steps."""
        return any(step.action.action_type == ActionType.THEN for step in self._enhanced_steps)

    def add_action_step(
        self,
        action: Action,
        parameters: dict[str, Any],
        expected_outputs: Optional[dict[str, Any]] = None,
        step_description: Optional[str] = None,
        position: Optional[int] = None,
        **step_kwargs,
    ) -> None:
        """
        Add an action step to the journey.

        Args:
            action: Action to add
            parameters: Step parameters
            expected_outputs: Expected outputs
            step_description: Override step description
            position: Position to insert (None = append)
            **step_kwargs: Additional step configuration
        """
        # Validate action parameters
        if action.parameters:
            validator = ParameterSetValidator(action.parameters)
            param_errors = validator.validate_parameter_set(parameters)
            if param_errors:
                error_msg = "; ".join(
                    [
                        f"{param}: {', '.join(errors)}"
                        for param, errors in param_errors.items()
                    ]
                )
                raise JourneyValidationError(
                    f"Parameter validation failed: {error_msg}"
                )

        # Create enhanced step
        step_number = len(self._enhanced_steps) + 1 if position is None else position
        enhanced_step = ActionStepEnhanced(
            step_number=step_number,
            action=action,
            parameters=parameters,
            expected_outputs=expected_outputs or {},
            step_description=step_description,
            **step_kwargs,
        )

        # Add to enhanced steps
        if position is None:
            self._enhanced_steps.append(enhanced_step)
        else:
            self._enhanced_steps.insert(position - 1, enhanced_step)
            self._renumber_enhanced_steps()

        # Create corresponding journey step for base class
        journey_step = JourneyStep(
            step_number=enhanced_step.step_number,
            action_id=action.id,
            action_type=action.action_type.value,
            action_name=action.name,
            description=step_description or action.description,
            parameters=parameters,
            expected_outputs=expected_outputs or {},
            metadata={"enhanced": True},
        )

        # Cache the action
        self._action_cache[action.id] = action

        # Invalidate validation cache
        self._validation_cache.clear()

        # Update execution status
        if self._execution_status == JourneyExecutionStatus.READY:
            self._execution_status = JourneyExecutionStatus.DRAFT

    def remove_enhanced_step(self, step_number: int) -> ActionStepEnhanced:
        """Remove an enhanced step."""
        if step_number < 1 or step_number > len(self._enhanced_steps):
            raise JourneyValidationError(f"Invalid step number: {step_number}")

        # Remove from enhanced steps
        removed_step = self._enhanced_steps.pop(step_number - 1)
        self._renumber_enhanced_steps()

        # Clear caches
        self._validation_cache.clear()

        return removed_step

    def update_step_parameters(
        self, step_number: int, parameters: dict[str, Any]
    ) -> None:
        """Update parameters for a specific step."""
        if step_number < 1 or step_number > len(self._enhanced_steps):
            raise JourneyValidationError(f"Invalid step number: {step_number}")

        step = self._enhanced_steps[step_number - 1]

        # Validate new parameters
        if step.action.parameters:
            validator = ParameterSetValidator(step.action.parameters)
            param_errors = validator.validate_parameter_set(parameters)
            if param_errors:
                error_msg = "; ".join(
                    [
                        f"{param}: {', '.join(errors)}"
                        for param, errors in param_errors.items()
                    ]
                )
                raise JourneyValidationError(
                    f"Parameter validation failed: {error_msg}"
                )

        # Update parameters
        step.parameters.update(parameters)

        # Update base class step
        base_steps = list(self.steps)
        if step_number <= len(base_steps):
            base_step = base_steps[step_number - 1]
            base_step.parameters.update(parameters)

        # Clear validation cache
        self._validation_cache.clear()

    def validate_enhanced_journey(self) -> list[str]:
        """Comprehensive validation of enhanced journey."""
        cache_key = f"enhanced_validation_{len(self._enhanced_steps)}_{hash(str(self._enhanced_steps))}"
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]

        errors = []

        # Base validation
        base_errors = self.get_validation_errors()
        errors.extend(base_errors)

        # Enhanced step validation
        for step in self._enhanced_steps:
            step_errors = step.validate_parameters()
            if step_errors:
                errors.extend(
                    [f"Step {step.step_number}: {error}" for error in step_errors]
                )

        # Action sequence validation
        if self._enhanced_steps:
            actions = [step.action for step in self._enhanced_steps]
            sequence_errors = ActionClassificationService.validate_action_sequence(
                actions
            )
            errors.extend([f"Sequence: {error}" for error in sequence_errors])

        # Dependency validation
        dependency_errors = self._validate_step_dependencies()
        errors.extend(dependency_errors)

        # Resource conflict validation
        resource_errors = self._validate_resource_conflicts()
        errors.extend(resource_errors)

        # Cache results
        self._validation_cache[cache_key] = errors

        return errors

    def _validate_step_dependencies(self) -> list[str]:
        """Validate step dependencies are correctly ordered."""
        errors = []

        for step in self._enhanced_steps:
            if step.depends_on_steps:
                for dep_step in step.depends_on_steps:
                    if dep_step >= step.step_number:
                        errors.append(
                            f"Step {step.step_number} cannot depend on step {dep_step} "
                            "(dependencies must be on earlier steps)"
                        )

        return errors

    def _validate_resource_conflicts(self) -> list[str]:
        """Validate no resource conflicts in parallel steps."""
        errors = []

        # Group steps that can run in parallel
        parallel_groups = self._identify_parallel_groups()

        for group in parallel_groups:
            # Check for ERPNext module conflicts
            modules_in_group = set()
            for step_num in group:
                step = self._enhanced_steps[step_num - 1]
                if step.action.erpnext_module:
                    if step.action.erpnext_module in modules_in_group:
                        errors.append(
                            f"Resource conflict: Multiple steps in parallel group "
                            f"access same ERPNext module '{step.action.erpnext_module}'"
                        )
                    modules_in_group.add(step.action.erpnext_module)

        return errors

    def _identify_parallel_groups(self) -> list[list[int]]:
        """Identify groups of steps that can run in parallel."""
        groups = []
        current_group = []

        for step in self._enhanced_steps:
            if step.can_run_parallel and not step.depends_on_steps:
                current_group.append(step.step_number)
            else:
                if current_group:
                    groups.append(current_group)
                    current_group = []

        if current_group:
            groups.append(current_group)

        return groups

    def generate_execution_plan(self) -> JourneyExecutionPlan:
        """Generate optimized execution plan for the journey."""
        if not self._enhanced_steps:
            return JourneyExecutionPlan(
                total_steps=0,
                estimated_duration=timedelta(seconds=0),
                complexity_score=0,
                resource_requirements=[],
                parallel_executable_steps=[],
                critical_path_steps=[],
                rollback_points=[],
            )

        # Calculate total duration
        total_duration = sum(
            step.get_effective_timeout()
            + (step.get_effective_retry_count() * step.get_effective_timeout())
            for step in self._enhanced_steps
        )

        # Calculate complexity score
        complexity_score = sum(
            ActionClassificationService.get_action_complexity_score(step.action)[
                "total_score"
            ]
            for step in self._enhanced_steps
        )

        # Identify parallel sections
        parallel_groups = self._identify_parallel_groups()
        parallel_ranges = []
        for group in parallel_groups:
            if len(group) > 1:
                parallel_ranges.append((min(group), max(group)))

        # Identify critical path (steps that cannot be parallelized)
        critical_steps = [
            step.step_number
            for step in self._enhanced_steps
            if step.is_critical or not step.can_run_parallel
        ]

        # Identify rollback points
        rollback_points = [
            step.step_number
            for step in self._enhanced_steps
            if step.rollback_action is not None
        ]

        # Collect resource requirements
        resources = set()
        for step in self._enhanced_steps:
            if step.action.erpnext_module:
                resources.add(f"erpnext_module:{step.action.erpnext_module}")
            if step.action.implementation_type:
                resources.add(f"implementation:{step.action.implementation_type.value}")

        plan = JourneyExecutionPlan(
            total_steps=len(self._enhanced_steps),
            estimated_duration=timedelta(seconds=total_duration),
            complexity_score=complexity_score,
            resource_requirements=list(resources),
            parallel_executable_steps=parallel_ranges,
            critical_path_steps=critical_steps,
            rollback_points=rollback_points,
        )

        self._execution_plan = plan
        return plan

    def prepare_for_execution(self) -> bool:
        """Prepare journey for execution and validate readiness."""
        # Validate journey
        errors = self.validate_enhanced_journey()
        if errors:
            return False

        # Generate execution plan
        self.generate_execution_plan()

        # Update status
        self._execution_status = JourneyExecutionStatus.READY

        return True

    def get_step_by_action_type(
        self, action_type: ActionType
    ) -> list[ActionStepEnhanced]:
        """Get all steps of specified action type."""
        return [
            step
            for step in self._enhanced_steps
            if step.action.action_type == action_type
        ]

    def get_actions_summary(self) -> dict[str, Any]:
        """Get summary of actions used in this journey."""
        if not self._enhanced_steps:
            return {}

        action_types = {}
        modules = set()
        implementations = set()

        for step in self._enhanced_steps:
            action = step.action

            # Count by action type
            type_name = action.action_type.value
            action_types[type_name] = action_types.get(type_name, 0) + 1

            # Collect modules and implementations
            if action.erpnext_module:
                modules.add(action.erpnext_module)
            if action.implementation_type:
                implementations.add(action.implementation_type.value)

        return {
            "total_steps": len(self._enhanced_steps),
            "action_types": action_types,
            "erpnext_modules": list(modules),
            "implementation_types": list(implementations),
            "has_complete_bdd_flow": (
                ActionType.GIVEN.value in action_types
                and ActionType.WHEN.value in action_types
                and ActionType.THEN.value in action_types
            ),
        }

    def _renumber_enhanced_steps(self) -> None:
        """Renumber enhanced steps to maintain sequence."""
        for i, step in enumerate(self._enhanced_steps, 1):
            step.step_number = i

    @classmethod
    def create_enhanced(
        cls,
        name: str,
        description: str,
        persona_id: UUID,
        activity_id: UUID,
        actions_and_params: Optional[list[tuple[Action, dict[str, Any]]]] = None,
        **kwargs,
    ) -> "EnhancedJourney":
        """
        Create enhanced journey with initial actions.

        Args:
            name: Journey name
            description: Journey description
            persona_id: Persona ID
            activity_id: Activity ID
            actions_and_params: List of (action, parameters) tuples
            **kwargs: Additional journey parameters

        Returns:
            New enhanced journey instance
        """
        journey = cls.create(
            name=name,
            description=description,
            persona_id=persona_id,
            activity_id=activity_id,
            **kwargs,
        )

        # Add initial actions if provided
        if actions_and_params:
            for action, params in actions_and_params:
                journey.add_action_step(action, params)

        return journey
