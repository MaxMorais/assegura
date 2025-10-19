"""Activity domain service for business rules and relationships.

This module implements the core business logic for activities,
including validation, relationships with personas, compatibility checking,
and activity lifecycle management.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .activity import Activity, ActivityPriority
from .erpnext_modules import ERPNextDocTypeHelper, ERPNextModuleValidator
from .exceptions import (
    ActivityMultipleValidationError,
    ActivityValidationError,
)


class ActivityRelationshipType(Enum):
    """Types of relationships between activities."""

    PREREQUISITE = "prerequisite"
    POSTCONDITION = "postcondition"
    ALTERNATIVE = "alternative"
    SIMILAR = "similar"
    CONFLICTING = "conflicting"
    COMPLEMENTARY = "complementary"


@dataclass
class ActivityRelationship:
    """Represents a relationship between two activities."""

    source_activity_id: uuid.UUID
    target_activity_id: uuid.UUID
    relationship_type: ActivityRelationshipType
    strength: float  # 0.0 to 1.0
    description: str
    created_at: datetime
    is_bidirectional: bool = False


@dataclass
class ActivityPersonaLink:
    """Represents a link between an activity and a persona."""

    activity_id: uuid.UUID
    persona_id: uuid.UUID
    priority: ActivityPriority
    notes: str
    created_at: datetime
    updated_at: datetime
    is_primary: bool = False  # Primary activity for the persona
    execution_order: int = 0  # Order in journey/workflow


@dataclass
class ActivityExecutionContext:
    """Context for activity execution validation."""

    persona_id: uuid.UUID
    execution_data: dict[str, Any]
    prerequisites_met: list[str]
    available_test_data: dict[str, Any]
    erpnext_context: dict[str, Any]
    execution_environment: str = "test"


@dataclass
class ActivityCompatibilityResult:
    """Result of activity compatibility check."""

    is_compatible: bool
    compatibility_score: float  # 0.0 to 1.0
    reasons: list[str]
    suggestions: list[str]
    confidence: float  # 0.0 to 1.0


class ActivityService:
    """Domain service for activity business logic and relationships."""

    def __init__(self):
        self.module_validator = ERPNextModuleValidator()
        self.doctype_helper = ERPNextDocTypeHelper()

    def validate_activity_creation(self, activity: Activity) -> None:
        """Validate activity for creation with business rules."""
        errors = []

        # Basic validation is handled by the Activity entity
        # Additional business rule validation here

        # Check module and doctype compatibility
        compatibility = self.module_validator.validate_activity_module_compatibility(
            activity.erpnext_module, activity.target_doctype, activity.action_type
        )

        if not compatibility["is_valid"]:
            for error in compatibility["errors"]:
                errors.append(ActivityValidationError("module_compatibility", error))

        # Validate complexity score matches action type complexity
        expected_complexity = self._get_expected_complexity_for_action(
            activity.action_type, activity.target_doctype
        )

        if abs(activity.complexity_score - expected_complexity) > 2:
            errors.append(
                ActivityValidationError(
                    "complexity_score",
                    f"Complexity score {activity.complexity_score} seems inappropriate for "
                    f"{activity.action_type} on {activity.target_doctype}. Expected around {expected_complexity}",
                )
            )

        # Validate estimated duration reasonableness
        expected_duration = self._get_expected_duration_for_activity(activity)
        if (
            activity.estimated_duration < expected_duration * 0.1
            or activity.estimated_duration > expected_duration * 10
        ):
            errors.append(
                ActivityValidationError(
                    "estimated_duration",
                    f"Estimated duration {activity.estimated_duration}s seems unrealistic for this activity type",
                )
            )

        if errors:
            if len(errors) == 1:
                raise errors[0]
            else:
                raise ActivityMultipleValidationError(errors)

    def validate_activity_update(self, original: Activity, updated: Activity) -> None:
        """Validate activity update with business rules."""
        # Ensure ID doesn't change
        if original.id != updated.id:
            raise ActivityValidationError("id", "Activity ID cannot be changed")

        # Validate the updated activity
        self.validate_activity_creation(updated)

        # Additional update-specific validations
        # Check if critical fields changed (might affect existing relationships)
        critical_fields = ["erpnext_module", "action_type", "target_doctype"]
        for field in critical_fields:
            if getattr(original, field) != getattr(updated, field):
                # Could add warning or validation logic here
                pass

    def calculate_activity_compatibility(
        self, activity1: Activity, activity2: Activity
    ) -> ActivityCompatibilityResult:
        """Calculate compatibility between two activities."""
        reasons = []
        suggestions = []
        compatibility_factors = []

        # Module compatibility (high weight)
        if activity1.erpnext_module == activity2.erpnext_module:
            compatibility_factors.append((1.0, 0.3, "Same ERPNext module"))
            reasons.append("Both activities operate in the same ERPNext module")
        else:
            compatibility_factors.append((0.2, 0.3, "Different ERPNext modules"))
            reasons.append("Activities operate in different ERPNext modules")
            suggestions.append(
                "Consider grouping activities by module for better workflow coherence"
            )

        # DocType compatibility
        if activity1.target_doctype == activity2.target_doctype:
            compatibility_factors.append((1.0, 0.25, "Same target DocType"))
            reasons.append("Both activities target the same DocType")
        else:
            # Check if doctypes are related
            related_score = self._calculate_doctype_relationship(
                activity1.target_doctype, activity2.target_doctype
            )
            compatibility_factors.append((related_score, 0.25, "Related DocTypes"))
            if related_score > 0.5:
                reasons.append("Activities target related DocTypes")
            else:
                reasons.append("Activities target unrelated DocTypes")

        # Action type compatibility
        action_compatibility = self._calculate_action_type_compatibility(
            activity1.action_type, activity2.action_type
        )
        compatibility_factors.append(
            (action_compatibility, 0.2, "Action type compatibility")
        )

        if action_compatibility > 0.7:
            reasons.append("Activities have compatible action types")
        else:
            reasons.append("Activities have different action patterns")
            suggestions.append(
                "Consider sequencing activities to create logical workflow"
            )

        # Complexity compatibility
        complexity_diff = abs(activity1.complexity_score - activity2.complexity_score)
        complexity_compatibility = max(0, 1 - (complexity_diff / 4))
        compatibility_factors.append(
            (complexity_compatibility, 0.1, "Similar complexity")
        )

        # Duration compatibility
        duration_ratio = min(
            activity1.estimated_duration, activity2.estimated_duration
        ) / max(activity1.estimated_duration, activity2.estimated_duration)
        compatibility_factors.append((duration_ratio, 0.1, "Similar duration"))

        # Prerequisites/postconditions overlap
        prereq_overlap = self._calculate_prerequisite_overlap(activity1, activity2)
        compatibility_factors.append((prereq_overlap, 0.05, "Prerequisites overlap"))

        # Calculate weighted score
        total_score = sum(score * weight for score, weight, _ in compatibility_factors)
        confidence = min(
            1.0,
            len([f for f in compatibility_factors if f[0] > 0.5])
            / len(compatibility_factors),
        )

        # Add specific suggestions based on compatibility
        if total_score > 0.8:
            suggestions.append("These activities work very well together in workflows")
        elif total_score > 0.6:
            suggestions.append(
                "These activities can be effectively combined with proper sequencing"
            )
        elif total_score < 0.3:
            suggestions.append(
                "Consider reviewing if these activities belong in the same test scenario"
            )

        return ActivityCompatibilityResult(
            is_compatible=total_score > 0.5,
            compatibility_score=total_score,
            reasons=reasons,
            suggestions=suggestions,
            confidence=confidence,
        )

    def find_similar_activities(
        self,
        target_activity: Activity,
        all_activities: list[Activity],
        similarity_threshold: float = 0.6,
    ) -> list[dict[str, Any]]:
        """Find activities similar to the target activity."""
        similar_activities = []

        for activity in all_activities:
            if activity.id == target_activity.id:
                continue

            similarity_score = target_activity.calculate_similarity(activity)

            if similarity_score >= similarity_threshold:
                similar_activities.append(
                    {
                        "activity": activity,
                        "similarity": similarity_score,
                        "similarity_factors": self._analyze_similarity_factors(
                            target_activity, activity
                        ),
                    }
                )

        # Sort by similarity (highest first)
        similar_activities.sort(key=lambda x: x["similarity"], reverse=True)

        return similar_activities

    def suggest_activity_relationships(
        self, activity: Activity, candidate_activities: list[Activity]
    ) -> list[ActivityRelationship]:
        """Suggest relationships between activities."""
        suggested_relationships = []

        for candidate in candidate_activities:
            if candidate.id == activity.id:
                continue

            # Check for prerequisite relationships
            if self._could_be_prerequisite(activity, candidate):
                relationship = ActivityRelationship(
                    source_activity_id=activity.id,
                    target_activity_id=candidate.id,
                    relationship_type=ActivityRelationshipType.PREREQUISITE,
                    strength=self._calculate_prerequisite_strength(activity, candidate),
                    description=f"{activity.name} should be completed before {candidate.name}",
                    created_at=datetime.utcnow(),
                    is_bidirectional=False,
                )
                suggested_relationships.append(relationship)

            # Check for alternative relationships
            if self._could_be_alternative(activity, candidate):
                relationship = ActivityRelationship(
                    source_activity_id=activity.id,
                    target_activity_id=candidate.id,
                    relationship_type=ActivityRelationshipType.ALTERNATIVE,
                    strength=activity.calculate_similarity(candidate),
                    description=f"{activity.name} and {candidate.name} achieve similar goals",
                    created_at=datetime.utcnow(),
                    is_bidirectional=True,
                )
                suggested_relationships.append(relationship)

            # Check for complementary relationships
            compatibility = self.calculate_activity_compatibility(activity, candidate)
            if compatibility.is_compatible and compatibility.compatibility_score > 0.7:
                relationship = ActivityRelationship(
                    source_activity_id=activity.id,
                    target_activity_id=candidate.id,
                    relationship_type=ActivityRelationshipType.COMPLEMENTARY,
                    strength=compatibility.compatibility_score,
                    description=f"{activity.name} works well with {candidate.name}",
                    created_at=datetime.utcnow(),
                    is_bidirectional=True,
                )
                suggested_relationships.append(relationship)

        return suggested_relationships

    def validate_activity_execution_context(
        self, activity: Activity, context: ActivityExecutionContext
    ) -> list[str]:
        """Validate if an activity can be executed in the given context."""
        validation_errors = []

        # Validate execution data against activity's validation rules
        data_errors = activity.validate_execution_data(context.execution_data)
        validation_errors.extend(data_errors)

        # Check prerequisites
        missing_prerequisites = []
        for prereq in activity.prerequisites:
            if prereq not in context.prerequisites_met:
                missing_prerequisites.append(prereq)

        if missing_prerequisites:
            validation_errors.append(
                f"Missing prerequisites: {', '.join(missing_prerequisites)}"
            )

        # Validate required test data availability
        for field in activity.required_fields:
            if (
                field not in context.available_test_data
                and field not in context.execution_data
            ):
                validation_errors.append(
                    f"Required test data for field '{field}' is not available"
                )

        # Check ERPNext context compatibility
        if context.erpnext_context:
            module_compatible = context.erpnext_context.get("active_modules", [])
            if activity.erpnext_module not in module_compatible:
                validation_errors.append(
                    f"ERPNext module '{activity.erpnext_module}' is not active in context"
                )

        return validation_errors

    def generate_activity_suggestions(
        self,
        context: str,
        erpnext_modules: list[str],
        target_persona_roles: list[str] = None,
    ) -> list[dict[str, Any]]:
        """Generate activity suggestions based on context and requirements."""
        suggestions = []

        # Get module suggestions based on context
        for module in erpnext_modules:
            module_suggestions = self.module_validator.suggest_modules_for_activity(
                context, ""
            )

            for suggestion in module_suggestions:
                if suggestion["module"] == module:
                    # Generate specific activity suggestions for this module
                    doctypes = suggestion["doctypes"]

                    for doctype in doctypes[:3]:  # Top 3 doctypes per module
                        for action in ["create", "read", "update"]:
                            activity_suggestion = {
                                "name": f"{action.title()} {doctype}",
                                "description": f"{action.title()} a new {doctype} record in ERPNext {module} module",
                                "erpnext_module": module,
                                "action_type": action,
                                "target_doctype": doctype,
                                "confidence": suggestion["confidence"]
                                * 0.8,  # Slightly reduce confidence
                                "required_fields": self.doctype_helper.get_required_fields(
                                    doctype
                                ),
                                "complexity_score": self._get_expected_complexity_for_action(
                                    action, doctype
                                ),
                                "estimated_duration": self._get_expected_duration_for_action(
                                    action, doctype
                                ),
                            }
                            suggestions.append(activity_suggestion)

        # Filter and rank suggestions
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)

        return suggestions[:10]  # Top 10 suggestions

    def optimize_activity_sequence(self, activities: list[Activity]) -> list[Activity]:
        """Optimize the sequence of activities for execution efficiency."""
        if not activities:
            return []

        # Create a dependency graph
        dependencies = self._build_dependency_graph(activities)

        # Topological sort with optimization for efficiency
        optimized_sequence = []
        remaining_activities = activities.copy()
        processed_ids = set()

        while remaining_activities:
            # Find activities with no unmet dependencies
            ready_activities = []
            for activity in remaining_activities:
                deps = dependencies.get(activity.id, set())
                if deps.issubset(processed_ids):
                    ready_activities.append(activity)

            if not ready_activities:
                # Break circular dependencies or add remaining activities
                ready_activities = [remaining_activities[0]]

            # Sort ready activities by priority (complexity, then duration)
            ready_activities.sort(
                key=lambda a: (a.complexity_score, a.estimated_duration)
            )

            # Add the best candidate
            next_activity = ready_activities[0]
            optimized_sequence.append(next_activity)
            processed_ids.add(next_activity.id)
            remaining_activities.remove(next_activity)

        return optimized_sequence

    def calculate_activity_statistics(
        self, activities: list[Activity]
    ) -> dict[str, Any]:
        """Calculate comprehensive statistics for a list of activities."""
        if not activities:
            return {
                "total": 0,
                "active": 0,
                "inactive": 0,
                "by_module": {},
                "by_action_type": {},
                "complexity_distribution": {},
                "avg_duration": 0,
                "total_duration": 0,
                "avg_complexity": 0,
                "most_common_module": "",
                "most_common_action": "",
            }

        stats = {
            "total": len(activities),
            "active": sum(1 for a in activities if a.is_active),
            "inactive": sum(1 for a in activities if not a.is_active),
            "by_module": {},
            "by_action_type": {},
            "complexity_distribution": {},
            "avg_duration": 0,
            "total_duration": sum(a.estimated_duration for a in activities),
            "avg_complexity": 0,
            "most_common_module": "",
            "most_common_action": "",
        }

        # Calculate distributions
        for activity in activities:
            # Module distribution
            module = activity.erpnext_module
            stats["by_module"][module] = stats["by_module"].get(module, 0) + 1

            # Action type distribution
            action = activity.action_type
            stats["by_action_type"][action] = stats["by_action_type"].get(action, 0) + 1

            # Complexity distribution
            complexity = activity.complexity_score
            stats["complexity_distribution"][complexity] = (
                stats["complexity_distribution"].get(complexity, 0) + 1
            )

        # Calculate averages
        stats["avg_duration"] = stats["total_duration"] / len(activities)
        stats["avg_complexity"] = sum(a.complexity_score for a in activities) / len(
            activities
        )

        # Find most common values
        if stats["by_module"]:
            stats["most_common_module"] = max(
                stats["by_module"], key=stats["by_module"].get
            )
        if stats["by_action_type"]:
            stats["most_common_action"] = max(
                stats["by_action_type"], key=stats["by_action_type"].get
            )

        return stats

    # Private helper methods

    def _get_expected_complexity_for_action(
        self, action_type: str, doctype: str
    ) -> int:
        """Get expected complexity score for action type and doctype."""
        base_complexity = {
            "read": 1,
            "search": 1,
            "create": 3,
            "update": 2,
            "delete": 2,
            "report": 2,
            "export": 1,
            "import": 4,
            "approve": 3,
            "cancel": 2,
            "submit": 3,
            "print": 1,
            "email": 2,
        }

        # Adjust based on doctype complexity
        complex_doctypes = [
            "Sales Order",
            "Purchase Order",
            "Work Order",
            "Journal Entry",
        ]
        simple_doctypes = ["Customer", "Supplier", "Item", "Contact"]

        complexity = base_complexity.get(action_type, 2)

        if doctype in complex_doctypes:
            complexity += 1
        elif doctype in simple_doctypes:
            complexity = max(1, complexity - 1)

        return min(5, complexity)

    def _get_expected_duration_for_activity(self, activity: Activity) -> int:
        """Get expected duration for an activity."""
        base_duration = self._get_expected_duration_for_action(
            activity.action_type, activity.target_doctype
        )

        # Adjust based on complexity
        complexity_multiplier = {1: 0.5, 2: 0.7, 3: 1.0, 4: 1.5, 5: 2.0}

        return int(
            base_duration * complexity_multiplier.get(activity.complexity_score, 1.0)
        )

    def _get_expected_duration_for_action(self, action_type: str, doctype: str) -> int:
        """Get expected duration for action type and doctype."""
        base_durations = {
            "read": 30,
            "search": 45,
            "create": 180,
            "update": 120,
            "delete": 60,
            "report": 90,
            "export": 60,
            "import": 300,
            "approve": 90,
            "cancel": 60,
            "submit": 90,
            "print": 30,
            "email": 60,
        }

        return base_durations.get(action_type, 120)

    def _calculate_doctype_relationship(self, doctype1: str, doctype2: str) -> float:
        """Calculate relationship score between two doctypes."""
        # Define doctype relationships (simplified)
        relationships = {
            ("Sales Order", "Sales Invoice"): 0.9,
            ("Sales Order", "Delivery Note"): 0.8,
            ("Purchase Order", "Purchase Invoice"): 0.9,
            ("Purchase Order", "Purchase Receipt"): 0.8,
            ("Customer", "Sales Order"): 0.7,
            ("Supplier", "Purchase Order"): 0.7,
            ("Item", "Stock Entry"): 0.6,
        }

        # Check both directions
        score = relationships.get((doctype1, doctype2), 0)
        if score == 0:
            score = relationships.get((doctype2, doctype1), 0)

        return score

    def _calculate_action_type_compatibility(self, action1: str, action2: str) -> float:
        """Calculate compatibility between action types."""
        if action1 == action2:
            return 1.0

        # Define action compatibility groups
        read_actions = {"read", "search", "report", "export", "print"}
        write_actions = {"create", "update", "delete", "import"}
        workflow_actions = {"approve", "cancel", "submit", "email"}

        # Actions in the same group are more compatible
        if (
            (action1 in read_actions and action2 in read_actions)
            or (action1 in write_actions and action2 in write_actions)
            or (action1 in workflow_actions and action2 in workflow_actions)
        ):
            return 0.7

        # Some specific compatible combinations
        compatible_pairs = [
            ("create", "read"),
            ("update", "read"),
            ("create", "submit"),
            ("create", "approve"),
        ]

        for pair in compatible_pairs:
            if (action1, action2) == pair or (action2, action1) == pair:
                return 0.8

        return 0.3

    def _calculate_prerequisite_overlap(
        self, activity1: Activity, activity2: Activity
    ) -> float:
        """Calculate overlap in prerequisites between activities."""
        if not activity1.prerequisites or not activity2.prerequisites:
            return 0.0

        set1 = set(activity1.prerequisites)
        set2 = set(activity2.prerequisites)

        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / len(union) if union else 0.0

    def _analyze_similarity_factors(
        self, activity1: Activity, activity2: Activity
    ) -> dict[str, float]:
        """Analyze what makes two activities similar."""
        factors = {}

        factors["module_match"] = (
            1.0 if activity1.erpnext_module == activity2.erpnext_module else 0.0
        )
        factors["action_match"] = (
            1.0 if activity1.action_type == activity2.action_type else 0.0
        )
        factors["doctype_match"] = (
            1.0 if activity1.target_doctype == activity2.target_doctype else 0.0
        )

        complexity_diff = abs(activity1.complexity_score - activity2.complexity_score)
        factors["complexity_similarity"] = max(0, 1 - (complexity_diff / 4))

        duration_ratio = min(
            activity1.estimated_duration, activity2.estimated_duration
        ) / max(activity1.estimated_duration, activity2.estimated_duration)
        factors["duration_similarity"] = duration_ratio

        return factors

    def _could_be_prerequisite(self, activity1: Activity, activity2: Activity) -> bool:
        """Check if activity1 could be a prerequisite for activity2."""
        # Simple heuristics for prerequisite relationships

        # Create typically comes before update/delete
        if activity1.action_type == "create" and activity2.action_type in [
            "update",
            "delete",
            "cancel",
        ]:
            return activity1.target_doctype == activity2.target_doctype

        # Read/search might be prerequisite for create/update
        if activity1.action_type in ["read", "search"] and activity2.action_type in [
            "create",
            "update",
        ]:
            # Check if they're related doctypes
            return (
                self._calculate_doctype_relationship(
                    activity1.target_doctype, activity2.target_doctype
                )
                > 0.5
            )

        return False

    def _could_be_alternative(self, activity1: Activity, activity2: Activity) -> bool:
        """Check if activities could be alternatives."""
        # Activities with same action type and module but different doctypes
        if (
            activity1.action_type == activity2.action_type
            and activity1.erpnext_module == activity2.erpnext_module
            and activity1.target_doctype != activity2.target_doctype
        ):
            return True

        # High similarity score indicates potential alternatives
        return activity1.calculate_similarity(activity2) > 0.8

    def _calculate_prerequisite_strength(
        self, prerequisite: Activity, dependent: Activity
    ) -> float:
        """Calculate the strength of a prerequisite relationship."""
        strength = 0.5  # Base strength

        # Same doctype increases strength
        if prerequisite.target_doctype == dependent.target_doctype:
            strength += 0.3

        # Logical action sequence increases strength
        if prerequisite.action_type == "create" and dependent.action_type in [
            "update",
            "delete",
            "submit",
            "cancel",
        ]:
            strength += 0.2

        return min(1.0, strength)

    def _build_dependency_graph(
        self, activities: list[Activity]
    ) -> dict[uuid.UUID, set[uuid.UUID]]:
        """Build a dependency graph based on activity prerequisites."""
        dependencies = {}
        activity_by_name = {a.name: a for a in activities}

        for activity in activities:
            deps = set()
            for prereq_name in activity.prerequisites:
                if prereq_name in activity_by_name:
                    deps.add(activity_by_name[prereq_name].id)
            dependencies[activity.id] = deps

        return dependencies

    # Test-compatible method aliases and new methods

    def validate_activity_configuration(self, activity: Activity) -> dict[str, Any]:
        """Validate activity configuration and return result dictionary."""
        errors = []
        warnings = []

        # Check required fields
        if not activity.required_fields:
            warnings.append("No required fields defined")

        # Check success criteria
        if not activity.success_criteria:
            warnings.append("No success criteria defined")

        # Check validation rules
        if not activity.validation_rules:
            warnings.append("No validation rules defined")

        # Check test data requirements
        if not activity.test_data_requirements:
            warnings.append("No test data requirements defined")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def calculate_compatibility(self, activity1: Activity, activity2: Activity) -> dict[str, Any]:
        """Calculate compatibility between two activities - test compatible version."""
        result = self.calculate_activity_compatibility(activity1, activity2)
        
        return {
            "compatible": result.compatibility_score > 0.5,
            "compatibility_score": result.compatibility_score,
            "reasons": result.reasons,
            "suggestions": result.suggestions
        }

    def suggest_similar_activities(self, activity: Activity, candidates: list[Activity], min_similarity: float = 0.3) -> list[dict[str, Any]]:
        """Suggest similar activities from a pool of candidates."""
        suggestions = []
        
        for candidate in candidates:
            similarity = self.calculate_activity_compatibility(activity, candidate)
            if similarity.compatibility_score >= min_similarity:
                suggestions.append({
                    "activity": candidate,
                    "similarity_score": similarity.compatibility_score,
                    "reasons": similarity.reasons
                })
        
        # Sort by compatibility score (descending)
        suggestions.sort(key=lambda s: s["similarity_score"], reverse=True)
        return suggestions

    def analyze_activity_relationships(self, activities: list[Activity]) -> list[dict[str, Any]]:
        """Analyze relationships between activities."""
        relationships = []
        
        for i, activity1 in enumerate(activities):
            for j, activity2 in enumerate(activities[i+1:], i+1):
                # Check if activity1 postconditions match activity2 prerequisites
                prereq_matches = []
                for prereq in activity2.prerequisites:
                    for postcond in activity1.postconditions:
                        # More flexible matching - check for common words
                        prereq_words = set(prereq.lower().split())
                        postcond_words = set(postcond.lower().split())
                        
                        # Find common meaningful words (skip common words)
                        common_words = prereq_words & postcond_words
                        common_words -= {'the', 'a', 'an', 'is', 'are', 'and', 'or', 'of', 'to', 'in', 'on', 'at', 'for'}
                        
                        if common_words or prereq.lower() in postcond.lower() or postcond.lower() in prereq.lower():
                            prereq_matches.append((prereq, postcond))
                
                if prereq_matches:
                    relationships.append({
                        "from_activity_name": activity1.name,
                        "to_activity_name": activity2.name,
                        "relationship_type": "prerequisite",
                        "matches": prereq_matches
                    })
        
        return relationships

    def generate_execution_context(self, activity: Activity) -> dict[str, Any]:
        """Generate execution context for an activity."""
        return {
            "activity_id": str(activity.id),
            "required_fields": activity.required_fields,
            "validation_rules": activity.validation_rules,
            "success_criteria": activity.success_criteria,
            "test_data": activity.test_data_requirements,
            "metadata": {
                "module": activity.erpnext_module,
                "doctype": activity.target_doctype,
                "action": activity.action_type,
                "prerequisites": activity.prerequisites,
                "expected_duration": activity.estimated_duration,
                "complexity_level": activity.complexity_score
            }
        }

    def check_prerequisite_satisfaction(self, activity: Activity, state: dict[str, Any]) -> dict[str, Any]:
        """Check if prerequisites are satisfied given current state."""
        satisfied_prereqs = []
        missing_prereqs = []
        
        for prereq in activity.prerequisites:
            # Simple matching logic - check if prerequisite key exists and is True
            prereq_key = prereq.lower().replace(" ", "_")
            if state.get(prereq_key, False):
                satisfied_prereqs.append(prereq)
            else:
                missing_prereqs.append(prereq)
        
        all_satisfied = len(missing_prereqs) == 0
        
        return {
            "satisfied": all_satisfied,
            "satisfied_prerequisites": satisfied_prereqs,
            "missing_prerequisites": missing_prereqs,
            "satisfaction_ratio": len(satisfied_prereqs) / len(activity.prerequisites) if activity.prerequisites else 1.0
        }

    def estimate_execution_time(self, activity: Activity) -> dict[str, Any]:
        """Estimate execution time for an activity."""
        base_time = activity.estimated_duration
        
        # Adjust based on complexity
        complexity_multiplier = 1 + (activity.complexity_score - 3) * 0.2  # Scale around complexity 3
        
        # Adjust based on number of required fields
        field_overhead = len(activity.required_fields) * 5  # 5 seconds per field
        
        # Adjust based on validation rules complexity
        validation_overhead = len(activity.validation_rules) * 10  # 10 seconds per rule
        
        estimated_time = base_time * complexity_multiplier + field_overhead + validation_overhead
        
        return {
            "base_duration": base_time,
            "adjusted_duration": int(estimated_time),
            "factors": {
                "complexity_multiplier": complexity_multiplier,
                "field_overhead": field_overhead,
                "validation_overhead": validation_overhead
            },
            "confidence_level": 0.8  # 80% confidence in estimation
        }
