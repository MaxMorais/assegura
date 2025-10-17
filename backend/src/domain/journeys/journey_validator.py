"""
Journey Validation Rules and Business Logic

This module implements comprehensive validation rules and business logic
for journey step sequences, ensuring journeys follow proper BDD patterns,
ERPNext business rules, and test automation best practices.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from ..actions.action_library import ActionType, ImplementationType
from ..actions.action_types import ActionClassificationService
from .enhanced_journey import EnhancedJourney


class ValidationSeverity(Enum):
    """Validation rule severity levels."""

    ERROR = "error"  # Blocks execution
    WARNING = "warning"  # Allowed but not recommended
    INFO = "info"  # Informational only


@dataclass
class ValidationResult:
    """Result of a validation rule check."""

    rule_name: str
    severity: ValidationSeverity
    message: str
    affected_steps: list[int] = None
    suggested_fix: Optional[str] = None

    @property
    def is_blocking(self) -> bool:
        """Check if this validation result blocks execution."""
        return self.severity == ValidationSeverity.ERROR


class JourneyValidationRule(ABC):
    """Abstract base class for journey validation rules."""

    def __init__(
        self, name: str, severity: ValidationSeverity = ValidationSeverity.ERROR
    ):
        self.name = name
        self.severity = severity

    @abstractmethod
    def validate(self, journey: EnhancedJourney) -> list[ValidationResult]:
        """
        Validate journey against this rule.

        Args:
            journey: Journey to validate

        Returns:
            List of validation results
        """
        pass

    def _create_result(
        self,
        message: str,
        affected_steps: Optional[list[int]] = None,
        suggested_fix: Optional[str] = None,
    ) -> ValidationResult:
        """Create validation result with rule info."""
        return ValidationResult(
            rule_name=self.name,
            severity=self.severity,
            message=message,
            affected_steps=affected_steps or [],
            suggested_fix=suggested_fix,
        )


class BDDSequenceRule(JourneyValidationRule):
    """Validate proper Given/When/Then BDD sequence."""

    def __init__(self):
        super().__init__("BDD Sequence Rule", ValidationSeverity.ERROR)

    def validate(self, journey: EnhancedJourney) -> list[ValidationResult]:
        results = []

        if not journey.enhanced_steps:
            return results

        # Check for complete BDD flow
        given_steps = journey.get_step_by_action_type(ActionType.GIVEN)
        when_steps = journey.get_step_by_action_type(ActionType.WHEN)
        then_steps = journey.get_step_by_action_type(ActionType.THEN)

        if not when_steps:
            results.append(
                self._create_result(
                    "Journey must have at least one When step (main action)",
                    suggested_fix="Add a When step that performs the main business action",
                )
            )

        if not then_steps:
            results.append(
                self._create_result(
                    "Journey should have Then steps to verify results",
                    suggested_fix="Add Then steps to verify the expected outcomes",
                )
            )

        # Validate sequence order
        if given_steps and when_steps:
            last_given = max(step.step_number for step in given_steps)
            first_when = min(step.step_number for step in when_steps)

            if last_given > first_when:
                given_nums = [
                    step.step_number
                    for step in given_steps
                    if step.step_number > first_when
                ]
                results.append(
                    self._create_result(
                        "Given steps (setup) should come before When steps (actions)",
                        affected_steps=given_nums,
                        suggested_fix="Move Given steps to the beginning of the journey",
                    )
                )

        if when_steps and then_steps:
            last_when = max(step.step_number for step in when_steps)
            first_then = min(step.step_number for step in then_steps)

            if last_when > first_then:
                when_nums = [
                    step.step_number
                    for step in when_steps
                    if step.step_number > first_then
                ]
                results.append(
                    self._create_result(
                        "When steps (actions) should come before Then steps (verifications)",
                        affected_steps=when_nums,
                        suggested_fix="Move When steps before Then steps",
                    )
                )

        return results


class ERPNextBusinessRule(JourneyValidationRule):
    """Validate ERPNext business logic compliance."""

    def __init__(self):
        super().__init__("ERPNext Business Rule", ValidationSeverity.ERROR)

    def validate(self, journey: EnhancedJourney) -> list[ValidationResult]:
        results = []

        # Check for proper ERPNext document workflow
        document_operations = self._analyze_document_operations(journey)

        for doctype, operations in document_operations.items():
            # Cannot delete before create
            if "delete" in operations and "create" not in operations:
                results.append(
                    self._create_result(
                        f"Cannot delete {doctype} without creating it first",
                        suggested_fix=f"Add a step to create {doctype} before deleting",
                    )
                )

            # Cannot submit before save
            if (
                "submit" in operations
                and "save" not in operations
                and "create" not in operations
            ):
                results.append(
                    self._create_result(
                        f"Cannot submit {doctype} without saving/creating it first",
                        suggested_fix=f"Add a step to save {doctype} before submitting",
                    )
                )

            # Cannot cancel without submit
            if "cancel" in operations and "submit" not in operations:
                results.append(
                    self._create_result(
                        f"Cannot cancel {doctype} without submitting it first",
                        suggested_fix=f"Add a step to submit {doctype} before cancelling",
                    )
                )

        # Check for proper authentication
        has_login = any(
            "login" in step.action.name.lower()
            or "authentication" in step.action.description.lower()
            for step in journey.enhanced_steps
        )

        if not has_login and len(journey.enhanced_steps) > 1:
            results.append(
                ValidationResult(
                    rule_name=self.name,
                    severity=ValidationSeverity.WARNING,
                    message="Journey should start with user authentication",
                    suggested_fix="Add a login step at the beginning",
                )
            )

        return results

    def _analyze_document_operations(
        self, journey: EnhancedJourney
    ) -> dict[str, set[str]]:
        """Analyze document operations by doctype."""
        operations = {}

        for step in journey.enhanced_steps:
            # Extract doctype from parameters
            doctype = step.parameters.get("doctype")
            if not doctype:
                continue

            if doctype not in operations:
                operations[doctype] = set()

            # Determine operation type from action name/description
            action_text = (step.action.name + " " + step.action.description).lower()

            if any(word in action_text for word in ["create", "new", "add"]):
                operations[doctype].add("create")
            if any(word in action_text for word in ["save", "update", "modify"]):
                operations[doctype].add("save")
            if any(word in action_text for word in ["submit", "approve"]):
                operations[doctype].add("submit")
            if any(word in action_text for word in ["cancel", "reject"]):
                operations[doctype].add("cancel")
            if any(word in action_text for word in ["delete", "remove"]):
                operations[doctype].add("delete")

        return operations


class StepComplexityRule(JourneyValidationRule):
    """Validate step complexity and journey maintainability."""

    def __init__(self):
        super().__init__("Step Complexity Rule", ValidationSeverity.WARNING)

    def validate(self, journey: EnhancedJourney) -> list[ValidationResult]:
        results = []

        # Check total step count
        total_steps = len(journey.enhanced_steps)
        if total_steps > 50:
            results.append(
                self._create_result(
                    f"Journey has {total_steps} steps, consider breaking into smaller journeys",
                    suggested_fix="Split complex journey into multiple focused journeys",
                )
            )
        elif total_steps > 30:
            results.append(
                ValidationResult(
                    rule_name=self.name,
                    severity=ValidationSeverity.INFO,
                    message=f"Journey has {total_steps} steps, monitor complexity",
                    suggested_fix="Consider adding intermediate validation points",
                )
            )

        # Check individual step complexity
        complex_steps = []
        for step in journey.enhanced_steps:
            complexity = ActionClassificationService.get_action_complexity_score(
                step.action
            )
            if complexity["complexity_level"] == "complex":
                complex_steps.append(step.step_number)

        if complex_steps:
            results.append(
                ValidationResult(
                    rule_name=self.name,
                    severity=ValidationSeverity.INFO,
                    message=f"Steps {complex_steps} have high complexity",
                    affected_steps=complex_steps,
                    suggested_fix="Consider breaking complex steps into simpler ones",
                )
            )

        # Check parameter complexity
        for step in journey.enhanced_steps:
            if len(step.parameters) > 10:
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        severity=ValidationSeverity.WARNING,
                        message=f"Step {step.step_number} has many parameters ({len(step.parameters)})",
                        affected_steps=[step.step_number],
                        suggested_fix="Consider using parameter objects or splitting the step",
                    )
                )

        return results


class DataDependencyRule(JourneyValidationRule):
    """Validate data dependencies between steps."""

    def __init__(self):
        super().__init__("Data Dependency Rule", ValidationSeverity.ERROR)

    def validate(self, journey: EnhancedJourney) -> list[ValidationResult]:
        results = []

        # Track data flow between steps
        produced_data = {}  # {variable_name: producing_step_number}
        consumed_data = {}  # {variable_name: [consuming_step_numbers]}

        for step in journey.enhanced_steps:
            step_num = step.step_number

            # Analyze outputs (data produced)
            for output_name in step.expected_outputs.keys():
                produced_data[output_name] = step_num

            # Analyze parameters that reference other step outputs
            for param_name, param_value in step.parameters.items():
                if isinstance(param_value, str) and param_value.startswith("${"):
                    # Parameter references output from another step
                    referenced_var = param_value[2:-1]  # Remove ${ }
                    if referenced_var not in consumed_data:
                        consumed_data[referenced_var] = []
                    consumed_data[referenced_var].append(step_num)

        # Validate dependencies
        for var_name, consuming_steps in consumed_data.items():
            if var_name not in produced_data:
                results.append(
                    self._create_result(
                        f"Variable '{var_name}' is used but never produced",
                        affected_steps=consuming_steps,
                        suggested_fix=f"Add a step that produces '{var_name}' before using it",
                    )
                )
            else:
                producing_step = produced_data[var_name]
                for consuming_step in consuming_steps:
                    if consuming_step <= producing_step:
                        results.append(
                            self._create_result(
                                f"Step {consuming_step} uses '{var_name}' before it's produced in step {producing_step}",
                                affected_steps=[consuming_step, producing_step],
                                suggested_fix="Reorder steps or use different variable names",
                            )
                        )

        # Check for invalid step dependencies (referencing non-existent steps)
        all_step_numbers = {step.step_number for step in journey.enhanced_steps}
        for step in journey.enhanced_steps:
            if step.depends_on_steps:
                for dep in step.depends_on_steps:
                    if dep not in all_step_numbers:
                        results.append(
                            self._create_result(
                                f"Step {step.step_number} depends on non-existent step {dep}",
                                affected_steps=[step.step_number],
                                suggested_fix=f"Remove dependency on step {dep} or add the missing step",
                            )
                        )

        # Check for circular dependencies in depends_on_steps
        dependency_graph = {}
        for step in journey.enhanced_steps:
            dependency_graph[step.step_number] = step.depends_on_steps or []

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: int) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for dependency in dependency_graph.get(node, []):
                if dependency not in visited:
                    if has_cycle(dependency):
                        return True
                elif dependency in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False

        for step_num in dependency_graph:
            if step_num not in visited:
                if has_cycle(step_num):
                    results.append(
                        self._create_result(
                            "Circular dependency detected in step dependencies",
                            affected_steps=list(dependency_graph.keys()),
                            suggested_fix="Remove or reorder circular dependencies between steps",
                        )
                    )
                    break  # Only report once

        return results


class ResourceConflictRule(JourneyValidationRule):
    """Validate resource conflicts in parallel execution."""

    def __init__(self):
        super().__init__("Resource Conflict Rule", ValidationSeverity.WARNING)

    def validate(self, journey: EnhancedJourney) -> list[ValidationResult]:
        results = []

        # Find parallel step groups
        parallel_steps = [
            step for step in journey.enhanced_steps if step.can_run_parallel
        ]

        if len(parallel_steps) < 2:
            return results  # No parallel execution possible

        # Group by ERPNext module access
        module_groups = {}
        for step in parallel_steps:
            module = step.action.erpnext_module
            if module:
                if module not in module_groups:
                    module_groups[module] = []
                module_groups[module].append(step.step_number)

        # Check for conflicts
        for module, step_numbers in module_groups.items():
            if len(step_numbers) > 1:
                results.append(
                    self._create_result(
                        f"Parallel steps {step_numbers} access same ERPNext module '{module}'",
                        affected_steps=step_numbers,
                        suggested_fix="Make steps sequential or ensure module access is thread-safe",
                    )
                )

        # Check for UI interaction conflicts
        ui_steps = [
            step
            for step in parallel_steps
            if step.action.implementation_type == ImplementationType.UI_INTERACTION
        ]

        if len(ui_steps) > 1:
            step_numbers = [step.step_number for step in ui_steps]
            results.append(
                self._create_result(
                    f"Multiple UI interaction steps {step_numbers} cannot run in parallel",
                    affected_steps=step_numbers,
                    suggested_fix="Make UI interaction steps sequential",
                )
            )

        return results


class ActionPatternRule(JourneyValidationRule):
    """Validate action pattern consistency and best practices."""

    def __init__(self):
        super().__init__("Action Pattern Rule", ValidationSeverity.WARNING)

    def validate(self, journey: EnhancedJourney) -> list[ValidationResult]:
        results = []

        # Check for consistent naming patterns
        given_steps = journey.get_step_by_action_type(ActionType.GIVEN)
        when_steps = journey.get_step_by_action_type(ActionType.WHEN)
        then_steps = journey.get_step_by_action_type(ActionType.THEN)

        # Validate Given step patterns
        for step in given_steps:
            action_name = step.action.name.lower()
            if not any(
                keyword in action_name
                for keyword in ["given", "setup", "prepare", "login", "navigate"]
            ):
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        severity=ValidationSeverity.INFO,
                        message=f"Given step {step.step_number} name should indicate setup/precondition",
                        affected_steps=[step.step_number],
                        suggested_fix="Use naming like 'Given user is logged in' or 'Setup test data'",
                    )
                )

        # Validate When step patterns
        for step in when_steps:
            action_name = step.action.name.lower()
            if not any(
                keyword in action_name
                for keyword in ["when", "create", "update", "submit", "process"]
            ):
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        severity=ValidationSeverity.INFO,
                        message=f"When step {step.step_number} name should indicate main action",
                        affected_steps=[step.step_number],
                        suggested_fix="Use naming like 'When user creates invoice' or 'Process payment'",
                    )
                )

        # Validate Then step patterns
        for step in then_steps:
            action_name = step.action.name.lower()
            if not any(
                keyword in action_name
                for keyword in ["then", "verify", "check", "should", "assert"]
            ):
                results.append(
                    ValidationResult(
                        rule_name=self.name,
                        severity=ValidationSeverity.INFO,
                        message=f"Then step {step.step_number} name should indicate verification",
                        affected_steps=[step.step_number],
                        suggested_fix="Use naming like 'Then invoice should be created' or 'Verify payment status'",
                    )
                )

        return results


class PerformanceRule(JourneyValidationRule):
    """Validate journey performance characteristics."""

    def __init__(self):
        super().__init__("Performance Rule", ValidationSeverity.WARNING)

    def validate(self, journey: EnhancedJourney) -> list[ValidationResult]:
        results = []

        # Check total estimated duration
        plan = journey.execution_plan or journey.generate_execution_plan()

        if plan.estimated_duration.total_seconds() > 1800:  # 30 minutes
            results.append(
                self._create_result(
                    f"Journey estimated duration is {plan.estimated_duration.total_seconds()/60:.1f} minutes",
                    suggested_fix="Consider breaking into smaller journeys or optimizing steps",
                )
            )
        elif plan.estimated_duration.total_seconds() > 600:  # 10 minutes
            results.append(
                ValidationResult(
                    rule_name=self.name,
                    severity=ValidationSeverity.INFO,
                    message=f"Journey duration is {plan.estimated_duration.total_seconds()/60:.1f} minutes",
                    suggested_fix="Monitor execution time and consider optimization",
                )
            )

        # Check for steps with very long timeouts
        long_timeout_steps = []
        for step in journey.enhanced_steps:
            timeout = step.get_effective_timeout()
            if timeout > 300:  # 5 minutes
                long_timeout_steps.append(step.step_number)

        if long_timeout_steps:
            results.append(
                ValidationResult(
                    rule_name=self.name,
                    severity=ValidationSeverity.INFO,
                    message=f"Steps {long_timeout_steps} have long timeouts (>5 minutes)",
                    affected_steps=long_timeout_steps,
                    suggested_fix="Review if long timeouts are necessary",
                )
            )

        # Check retry patterns
        high_retry_steps = []
        for step in journey.enhanced_steps:
            retries = step.get_effective_retry_count()
            if retries > 5:
                high_retry_steps.append(step.step_number)

        if high_retry_steps:
            results.append(
                ValidationResult(
                    rule_name=self.name,
                    severity=ValidationSeverity.INFO,
                    message=f"Steps {high_retry_steps} have high retry counts",
                    affected_steps=high_retry_steps,
                    suggested_fix="Review if high retry counts indicate underlying issues",
                )
            )

        return results


class JourneyValidator:
    """Main validator that applies all validation rules."""

    def __init__(self):
        self.rules = [
            BDDSequenceRule(),
            ERPNextBusinessRule(),
            StepComplexityRule(),
            DataDependencyRule(),
            ResourceConflictRule(),
            ActionPatternRule(),
            PerformanceRule(),
        ]

    def validate_journey(
        self,
        journey: EnhancedJourney,
        include_warnings: bool = True,
        include_info: bool = False,
    ) -> list[ValidationResult]:
        """
        Validate journey against all rules.

        Args:
            journey: Journey to validate
            include_warnings: Include warning-level results
            include_info: Include info-level results

        Returns:
            List of validation results
        """
        all_results = []

        for rule in self.rules:
            try:
                rule_results = rule.validate(journey)
                all_results.extend(rule_results)
            except Exception as e:
                # Log validation rule error but don't fail
                error_result = ValidationResult(
                    rule_name=rule.name,
                    severity=ValidationSeverity.ERROR,
                    message=f"Validation rule failed: {str(e)}",
                )
                all_results.append(error_result)

        # Filter by severity
        filtered_results = []
        for result in all_results:
            if result.severity == ValidationSeverity.ERROR:
                filtered_results.append(result)
            elif result.severity == ValidationSeverity.WARNING and include_warnings:
                filtered_results.append(result)
            elif result.severity == ValidationSeverity.INFO and include_info:
                filtered_results.append(result)

        return filtered_results

    def can_execute(self, journey: EnhancedJourney) -> bool:
        """Check if journey can be executed (no blocking errors)."""
        results = self.validate_journey(
            journey, include_warnings=False, include_info=False
        )
        return not any(result.is_blocking for result in results)

    def get_validation_summary(self, journey: EnhancedJourney) -> dict[str, Any]:
        """Get validation summary with counts and recommendations."""
        results = self.validate_journey(
            journey, include_warnings=True, include_info=True
        )

        error_count = sum(1 for r in results if r.severity == ValidationSeverity.ERROR)
        warning_count = sum(
            1 for r in results if r.severity == ValidationSeverity.WARNING
        )
        info_count = sum(1 for r in results if r.severity == ValidationSeverity.INFO)

        return {
            "can_execute": error_count == 0,
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "total_issues": len(results),
            "results": [
                {
                    "rule": r.rule_name,
                    "severity": r.severity.value,
                    "message": r.message,
                    "affected_steps": r.affected_steps,
                    "suggested_fix": r.suggested_fix,
                }
                for r in results
            ],
        }
