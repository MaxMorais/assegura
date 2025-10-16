"""
Journey Service

This module implements business rules and invariants for journey management.
It provides advanced validation, dependency checking, and business logic
that goes beyond basic entity validation.
"""

from __future__ import annotations
from typing import List, Dict, Set, Optional, Tuple, Any
from uuid import UUID

from src.domain.journeys.journey import Journey
from src.domain.journeys.journey_step import JourneyStep
from src.domain.journeys.journey_validation_error import JourneyValidationError


class JourneyService:
    """
    Service for journey business rules and validation.
    
    This service implements complex validation rules that require analysis
    of the entire journey structure, step relationships, and business invariants.
    """
    
    def validate_journey_completeness(self, journey: Journey) -> List[str]:
        """
        Validate that journey represents a complete test scenario.
        
        Args:
            journey: Journey to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not journey.steps:
            errors.append("Journey must have at least one step")
            return errors
        
        # Check for complete BDD pattern
        has_given = journey.has_given_steps
        has_when = journey.has_when_steps
        has_then = journey.has_then_steps
        
        if not has_given:
            errors.append("Journey should have at least one Given step (precondition)")
        
        if not has_when:
            errors.append("Journey must have at least one When step (action)")
        
        if not has_then:
            errors.append("Journey should have at least one Then step (verification)")
        
        return errors
    
    def validate_step_sequence_logic(self, journey: Journey) -> List[str]:
        """
        Validate the logical flow of journey steps.
        
        Args:
            journey: Journey to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not journey.steps:
            return errors
        
        steps = sorted(journey.steps, key=lambda s: s.step_number)
        
        # Analyze step type transitions
        previous_type = None
        type_transition_valid = True
        
        for step in steps:
            current_type = step.action_type
            
            if previous_type is not None:
                # Validate allowed transitions
                if previous_type == "then" and current_type in ("given", "when"):
                    errors.append(
                        f"Invalid transition: {previous_type} -> {current_type} at step {step.step_number}. "
                        "Then steps should typically be at the end of a sequence."
                    )
                    type_transition_valid = False
                
                # Check for logical groupings
                if previous_type == "given" and current_type == "then":
                    errors.append(
                        f"Missing When step between Given and Then at step {step.step_number}. "
                        "Consider adding an action step."
                    )
            
            previous_type = current_type
        
        # Validate step type distribution
        given_steps = [s for s in steps if s.action_type == "given"]
        when_steps = [s for s in steps if s.action_type == "when"]
        then_steps = [s for s in steps if s.action_type == "then"]
        
        # Check for reasonable distribution
        if len(when_steps) == 0:
            errors.append("Journey must have at least one When step (action)")
        
        if len(given_steps) > len(when_steps) * 3:
            errors.append(
                f"Too many Given steps ({len(given_steps)}) relative to When steps ({len(when_steps)}). "
                "Consider consolidating preconditions."
            )
        
        if len(then_steps) > len(when_steps) * 2:
            errors.append(
                f"Too many Then steps ({len(then_steps)}) relative to When steps ({len(when_steps)}). "
                "Consider consolidating verifications."
            )
        
        return errors
    
    def validate_parameter_consistency(self, journey: Journey) -> List[str]:
        """
        Validate parameter consistency across journey steps.
        
        Args:
            journey: Journey to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not journey.steps:
            return errors
        
        # Track parameter flow through steps
        available_outputs: Dict[str, Set[int]] = {}  # parameter_name -> set of step_numbers providing it
        required_inputs: Dict[str, Set[int]] = {}   # parameter_name -> set of step_numbers requiring it
        
        # Build parameter dependency graph
        for step in journey.steps:
            # Track what this step produces
            for output_name in step.expected_outputs.keys():
                if output_name not in available_outputs:
                    available_outputs[output_name] = set()
                available_outputs[output_name].add(step.step_number)
            
            # Track what this step requires
            for param_name in step.parameters.keys():
                if param_name not in required_inputs:
                    required_inputs[param_name] = set()
                required_inputs[param_name].add(step.step_number)
        
        # Check for unresolved dependencies
        for param_name, requiring_steps in required_inputs.items():
            providing_steps = available_outputs.get(param_name, set())
            
            for requiring_step in requiring_steps:
                # Check if any earlier step provides this parameter
                available_before = {s for s in providing_steps if s < requiring_step}
                
                if not available_before:
                    # Check if this is a journey-level parameter (should be in prerequisites)
                    if param_name not in [p.lower().replace(' ', '_') for p in journey.prerequisites]:
                        errors.append(
                            f"Step {requiring_step} requires parameter '{param_name}' "
                            "but no earlier step provides it. Consider adding to journey prerequisites."
                        )
        
        return errors
    
    def detect_circular_dependencies(self, journey: Journey) -> List[str]:
        """
        Detect circular dependencies in step parameter flow.
        
        Args:
            journey: Journey to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not journey.steps:
            return errors
        
        # Build dependency graph: step -> set of steps it depends on
        dependencies: Dict[int, Set[int]] = {}
        
        for step in journey.steps:
            step_deps = set()
            
            # Find steps that provide required parameters
            for param_name in step.parameters.keys():
                for other_step in journey.steps:
                    if (other_step.step_number != step.step_number and
                        param_name in other_step.expected_outputs):
                        step_deps.add(other_step.step_number)
            
            dependencies[step.step_number] = step_deps
        
        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: int) -> bool:
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependencies.get(node, set()):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Check each step for cycles
        for step_number in dependencies.keys():
            if step_number not in visited:
                if has_cycle(step_number):
                    errors.append(
                        f"Circular dependency detected involving step {step_number}. "
                        "Steps cannot depend on each other in a cycle."
                    )
                    break  # Report first cycle found
        
        return errors
    
    def validate_journey_complexity(self, journey: Journey) -> List[str]:
        """
        Validate journey complexity and suggest improvements.
        
        Args:
            journey: Journey to validate
            
        Returns:
            List of validation warnings and suggestions
        """
        warnings = []
        
        step_count = journey.step_count
        
        # Check complexity vs declared level
        if journey.complexity_level == "simple" and step_count > 5:
            warnings.append(
                f"Journey marked as 'simple' but has {step_count} steps. "
                "Consider breaking into smaller journeys or changing complexity level."
            )
        
        if journey.complexity_level == "medium" and step_count > 15:
            warnings.append(
                f"Journey marked as 'medium' but has {step_count} steps. "
                "Consider breaking into smaller journeys or marking as 'complex'."
            )
        
        if journey.complexity_level == "simple" and step_count > 25:
            warnings.append(
                f"Journey has {step_count} steps which is very complex. "
                "Consider breaking into multiple smaller journeys."
            )
        
        # Check estimated duration consistency
        if journey.estimated_duration_minutes:
            # Rough heuristic: 1-2 minutes per step
            expected_min = step_count
            expected_max = step_count * 2
            
            if journey.estimated_duration_minutes < expected_min:
                warnings.append(
                    f"Estimated duration ({journey.estimated_duration_minutes}min) "
                    f"seems too short for {step_count} steps. Consider {expected_min}-{expected_max}min."
                )
            
            if journey.estimated_duration_minutes > expected_max * 3:
                warnings.append(
                    f"Estimated duration ({journey.estimated_duration_minutes}min) "
                    f"seems too long for {step_count} steps. Consider breaking into smaller journeys."
                )
        
        return warnings
    
    def validate_business_rules(self, journey: Journey) -> List[str]:
        """
        Validate business-specific rules for journeys.
        
        Args:
            journey: Journey to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Rule: Journey name should be descriptive and unique-ish
        if journey.name and len(journey.name.split()) < 3:
            errors.append(
                "Journey name should be descriptive (at least 3 words recommended)"
            )
        
        # Rule: Description should explain the business value
        if journey.description:
            business_words = ["test", "verify", "ensure", "validate", "check", "confirm"]
            if not any(word in journey.description.lower() for word in business_words):
                errors.append(
                    "Journey description should explain what is being tested or verified"
                )
        
        # Rule: Prerequisites should be actionable
        for prereq in journey.prerequisites:
            if len(prereq.strip()) < 5:
                errors.append(f"Prerequisite '{prereq}' is too vague. Be more specific.")
        
        # Rule: Expected outcomes should be measurable  
        for outcome in journey.expected_outcomes:
            if len(outcome.strip()) < 10:
                errors.append(f"Expected outcome '{outcome}' should be more detailed and measurable.")
        
        # Rule: Active journeys should be complete
        if journey.is_active:
            completeness_errors = self.validate_journey_completeness(journey)
            if completeness_errors:
                errors.append("Active journey must be complete (have Given/When/Then steps)")
        
        return errors
    
    def get_journey_health_score(self, journey: Journey) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate overall journey health score and detailed metrics.
        
        Args:
            journey: Journey to analyze
            
        Returns:
            Tuple of (score 0-100, detailed metrics)
        """
        metrics = {
            "completeness_score": 0.0,
            "sequence_score": 0.0,
            "parameter_score": 0.0,
            "complexity_score": 0.0,
            "business_rules_score": 0.0,
            "total_errors": 0,
            "total_warnings": 0,
        }
        
        # Completeness (25% weight)
        completeness_errors = self.validate_journey_completeness(journey)
        metrics["completeness_score"] = max(0, 100 - len(completeness_errors) * 25)
        
        # Sequence logic (25% weight)  
        sequence_errors = self.validate_step_sequence_logic(journey)
        metrics["sequence_score"] = max(0, 100 - len(sequence_errors) * 20)
        
        # Parameter consistency (20% weight)
        parameter_errors = self.validate_parameter_consistency(journey)
        circular_errors = self.detect_circular_dependencies(journey)
        total_param_errors = len(parameter_errors) + len(circular_errors)
        metrics["parameter_score"] = max(0, 100 - total_param_errors * 15)
        
        # Complexity appropriateness (15% weight)
        complexity_warnings = self.validate_journey_complexity(journey)
        metrics["complexity_score"] = max(0, 100 - len(complexity_warnings) * 10)
        
        # Business rules (15% weight)
        business_errors = self.validate_business_rules(journey)
        metrics["business_rules_score"] = max(0, 100 - len(business_errors) * 20)
        
        # Calculate weighted total
        weights = {
            "completeness_score": 0.25,
            "sequence_score": 0.25,
            "parameter_score": 0.20,
            "complexity_score": 0.15,
            "business_rules_score": 0.15,
        }
        
        total_score = sum(
            metrics[key] * weights[key]
            for key in weights.keys()
        )
        
        # Count total issues
        all_errors = (
            completeness_errors +
            sequence_errors +
            parameter_errors +
            circular_errors +
            business_errors
        )
        all_warnings = complexity_warnings
        
        metrics["total_errors"] = len(all_errors)
        metrics["total_warnings"] = len(all_warnings)
        
        return round(total_score, 1), metrics
    
    def suggest_improvements(self, journey: Journey) -> List[str]:
        """
        Suggest improvements for journey quality.
        
        Args:
            journey: Journey to analyze
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Analyze current issues
        completeness_errors = self.validate_journey_completeness(journey)
        sequence_errors = self.validate_step_sequence_logic(journey)
        parameter_errors = self.validate_parameter_consistency(journey)
        complexity_warnings = self.validate_journey_complexity(journey)
        
        # Suggest fixes based on issues found
        if completeness_errors:
            suggestions.append("Add missing Given/When/Then steps to create a complete BDD scenario")
        
        if sequence_errors:
            suggestions.append("Review step sequence to ensure logical Given->When->Then flow")
        
        if parameter_errors:
            suggestions.append("Review parameter dependencies between steps and add missing prerequisites")
        
        if len(complexity_warnings) > 2:
            suggestions.append("Consider breaking this journey into smaller, focused scenarios")
        
        # Positive suggestions
        if journey.step_count > 0:
            if not journey.prerequisites:
                suggestions.append("Add prerequisites to clarify initial conditions needed")
            
            if not journey.expected_outcomes:
                suggestions.append("Define expected outcomes to clarify what success looks like")
            
            if not journey.estimated_duration_minutes:
                suggestions.append("Add estimated duration to help with test planning")
        
        return suggestions