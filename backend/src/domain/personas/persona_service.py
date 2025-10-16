"""Persona business rules and domain service.

Implements business logic and rules for persona management
in the ERPNext Test Automation Meta-Framework.
"""

from typing import Optional

from .erpnext_roles import ERPNextRole, validate_role_combination
from .exceptions import (
    PersonaBusinessRuleError,
    PersonaMultipleValidationError,
    PersonaValidationError,
)
from .persona import Persona


class PersonaService:
    """Domain service for persona business logic and rules."""

    @staticmethod
    def validate_persona_creation(persona: Persona) -> None:
        """Validate persona can be created according to business rules.

        Args:
            persona: Persona to validate

        Raises:
            PersonaBusinessRuleError: If business rules are violated
            PersonaMultipleValidationError: If multiple validation errors occur
        """
        errors = []

        # Basic persona structure is validated during construction in Pydantic v2

        # Business rule: Persona name must be meaningful
        if len(persona.name.strip()) < 3:
            errors.append(
                PersonaValidationError(
                    "name",
                    "Persona name must be at least 3 characters for clarity",
                    value=persona.name,
                )
            )

        # Business rule: Description must provide context
        if len(persona.description.strip()) < 20:
            errors.append(
                PersonaValidationError(
                    "description",
                    "Persona description must be at least 20 characters to provide meaningful context",
                    value=persona.description,
                )
            )

        # Business rule: Role combination should make sense
        role_warnings = validate_role_combination(persona.erpnext_roles)
        for warning in role_warnings:
            if "redundant" in warning.lower() or "conflicting" in warning.lower():
                errors.append(
                    PersonaValidationError(
                        "erpnext_roles",
                        f"Role combination issue: {warning}",
                        value=persona.erpnext_roles_str,
                    )
                )

        # Business rule: External personas (Customer/Supplier) have restrictions
        PersonaService._validate_external_persona_rules(persona, errors)

        # Business rule: Admin personas have restrictions
        PersonaService._validate_admin_persona_rules(persona, errors)

        if errors:
            raise PersonaMultipleValidationError(errors)

    @staticmethod
    def validate_persona_update(
        current_persona: Persona,
        updated_persona: Persona,
        allow_role_reduction: bool = False,
    ) -> None:
        """Validate persona can be updated according to business rules.

        Args:
            current_persona: Current persona state
            updated_persona: Updated persona state
            allow_role_reduction: Whether to allow reducing roles

        Raises:
            PersonaBusinessRuleError: If business rules are violated
        """
        errors = []

        # Validate the updated persona
        try:
            PersonaService.validate_persona_creation(updated_persona)
        except PersonaMultipleValidationError as e:
            errors.extend(e.errors)

        # Business rule: Cannot reduce roles without explicit permission
        if not allow_role_reduction:
            current_roles = set(current_persona.erpnext_roles)
            updated_roles = set(updated_persona.erpnext_roles)

            if not current_roles.issubset(updated_roles.union(current_roles)):
                removed_roles = current_roles - updated_roles
                if removed_roles:
                    errors.append(
                        PersonaBusinessRuleError(
                            "role_reduction_not_allowed",
                            f"Cannot remove roles {removed_roles} without explicit permission",
                        )
                    )

        # Business rule: Cannot change from external to internal persona type
        current_is_external = PersonaService._is_external_persona(current_persona)
        updated_is_external = PersonaService._is_external_persona(updated_persona)

        if current_is_external and not updated_is_external:
            errors.append(
                PersonaBusinessRuleError(
                    "external_to_internal_not_allowed",
                    "Cannot change external persona (Customer/Supplier) to internal persona",
                )
            )

        if errors:
            if len(errors) == 1 and isinstance(errors[0], PersonaBusinessRuleError):
                raise errors[0]
            else:
                validation_errors = [
                    e for e in errors if isinstance(e, PersonaValidationError)
                ]
                if validation_errors:
                    raise PersonaMultipleValidationError(validation_errors)
                else:
                    raise errors[0]

    @staticmethod
    def validate_persona_deletion(persona: Persona, usage_count: int = 0) -> None:
        """Validate persona can be deleted according to business rules.

        Args:
            persona: Persona to delete
            usage_count: Number of places where persona is used

        Raises:
            PersonaBusinessRuleError: If deletion is not allowed
        """
        # Business rule: Cannot delete persona that is in use
        if usage_count > 0:
            raise PersonaBusinessRuleError(
                "persona_in_use",
                f"Cannot delete persona '{persona.name}' - it is used in {usage_count} places",
            )

        # Business rule: Admin personas require special confirmation
        if PersonaService._is_admin_persona(persona):
            raise PersonaBusinessRuleError(
                "admin_persona_deletion",
                f"Admin persona '{persona.name}' requires special confirmation for deletion",
            )

    @staticmethod
    def generate_persona_suggestions(
        module: str, user_level: str, description_keywords: Optional[list[str]] = None
    ) -> list[dict[str, str]]:
        """Generate persona suggestions based on module and user level.

        Args:
            module: ERPNext module (sales, purchase, stock, etc.)
            user_level: User level (user, manager, admin)
            description_keywords: Keywords to include in description

        Returns:
            List of persona suggestion dictionaries
        """
        from .erpnext_roles import get_role_recommendations

        suggestions = []

        # Get recommended roles for the module
        recommended_roles = get_role_recommendations(module, user_level)

        if not recommended_roles:
            return suggestions

        # Generate base persona name
        module_name = module.title()
        level_name = user_level.title()

        base_name = f"{module_name} {level_name}"
        if user_level.lower() == "admin":
            base_name = f"{module_name} Administrator"

        # Generate description
        keywords = description_keywords or []
        keyword_text = f" with {', '.join(keywords)}" if keywords else ""

        description = (
            f"{level_name} responsible for {module} operations in ERPNext{keyword_text}. "
            f"Has appropriate permissions for {module} module workflows."
        )

        # Create suggestion
        suggestion = {
            "name": base_name,
            "description": description,
            "erpnext_roles": ",".join(recommended_roles),
            "permissions": PersonaService._generate_default_permissions(
                module, user_level
            ),
            "module": module,
            "user_level": user_level,
        }

        suggestions.append(suggestion)

        # Add variation with Employee role if not external
        if (
            user_level.lower() != "admin"
            and ERPNextRole.EMPLOYEE.value not in recommended_roles
        ):
            employee_roles = recommended_roles + [ERPNextRole.EMPLOYEE.value]
            employee_suggestion = suggestion.copy()
            employee_suggestion["name"] = f"{base_name} (Employee)"
            employee_suggestion["description"] = (
                description + " Also has employee access for HR functions."
            )
            employee_suggestion["erpnext_roles"] = ",".join(employee_roles)
            suggestions.append(employee_suggestion)

        return suggestions

    @staticmethod
    def calculate_persona_complexity(persona: Persona) -> dict[str, int]:
        """Calculate complexity metrics for a persona.

        Args:
            persona: Persona to analyze

        Returns:
            Dictionary with complexity metrics
        """
        metrics = {
            "role_count": len(persona.erpnext_roles),
            "permission_count": len(persona.permissions_list),
            "description_length": len(persona.description),
            "name_length": len(persona.name),
        }

        # Calculate effective permissions including role-based
        effective_permissions = persona.get_effective_permissions()
        metrics["effective_permission_count"] = len(effective_permissions)

        # Calculate complexity score
        complexity_score = (
            metrics["role_count"] * 2
            + metrics["permission_count"] * 1
            + (metrics["description_length"] // 100)
            + (1 if PersonaService._is_admin_persona(persona) else 0) * 5
        )
        metrics["complexity_score"] = complexity_score

        return metrics

    @staticmethod
    def find_similar_personas(
        persona: Persona,
        candidate_personas: list[Persona],
        similarity_threshold: float = 0.7,
    ) -> list[dict[str, any]]:
        """Find personas similar to the given persona.

        Args:
            persona: Reference persona
            candidate_personas: List of personas to compare against
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of similar personas with similarity scores
        """
        similar = []

        persona_roles = set(persona.erpnext_roles)
        persona_permissions = set(persona.permissions_list)

        for candidate in candidate_personas:
            if candidate.id == persona.id:
                continue

            candidate_roles = set(candidate.erpnext_roles)
            candidate_permissions = set(candidate.permissions_list)

            # Calculate role similarity
            role_intersection = len(persona_roles.intersection(candidate_roles))
            role_union = len(persona_roles.union(candidate_roles))
            role_similarity = role_intersection / role_union if role_union > 0 else 0

            # Calculate permission similarity
            perm_intersection = len(
                persona_permissions.intersection(candidate_permissions)
            )
            perm_union = len(persona_permissions.union(candidate_permissions))
            perm_similarity = perm_intersection / perm_union if perm_union > 0 else 0

            # Calculate overall similarity
            overall_similarity = role_similarity * 0.7 + perm_similarity * 0.3

            if overall_similarity >= similarity_threshold:
                similar.append(
                    {
                        "persona": candidate,
                        "similarity_score": overall_similarity,
                        "role_similarity": role_similarity,
                        "permission_similarity": perm_similarity,
                        "shared_roles": list(
                            persona_roles.intersection(candidate_roles)
                        ),
                        "shared_permissions": list(
                            persona_permissions.intersection(candidate_permissions)
                        ),
                    }
                )

        # Sort by similarity score descending
        similar.sort(key=lambda x: x["similarity_score"], reverse=True)

        return similar

    @staticmethod
    def _validate_external_persona_rules(persona: Persona, errors: list) -> None:
        """Validate business rules for external personas."""
        external_roles = {ERPNextRole.CUSTOMER.value, ERPNextRole.SUPPLIER.value}
        persona_roles = set(persona.erpnext_roles)

        has_external = bool(persona_roles.intersection(external_roles))
        has_internal = bool(persona_roles - external_roles)

        if has_external and has_internal:
            errors.append(
                PersonaValidationError(
                    "erpnext_roles",
                    "External roles (Customer/Supplier) should not be combined with internal roles",
                    value=persona.erpnext_roles_str,
                )
            )

        if has_external:
            # External personas should have limited permissions
            restricted_actions = {"admin", "delete", "create"}
            for permission in persona.permissions_list:
                if ":" in permission:
                    action = permission.split(":")[0]
                    if action in restricted_actions:
                        errors.append(
                            PersonaValidationError(
                                "permissions",
                                f"External personas should not have '{action}' permissions",
                                value=permission,
                            )
                        )

    @staticmethod
    def _validate_admin_persona_rules(persona: Persona, errors: list) -> None:
        """Validate business rules for admin personas."""
        admin_roles = {
            ERPNextRole.ADMINISTRATOR.value,
            ERPNextRole.SYSTEM_MANAGER.value,
        }
        persona_roles = set(persona.erpnext_roles)

        if persona_roles.intersection(admin_roles):
            # Admin personas should have comprehensive descriptions
            if len(persona.description) < 50:
                errors.append(
                    PersonaValidationError(
                        "description",
                        "Admin personas require detailed descriptions (minimum 50 characters)",
                        value=persona.description,
                    )
                )

            # Admin personas should be explicitly marked
            if "admin" not in persona.name.lower():
                errors.append(
                    PersonaValidationError(
                        "name",
                        "Admin personas should include 'Admin' or 'Administrator' in the name",
                        value=persona.name,
                    )
                )

    @staticmethod
    def _is_external_persona(persona: Persona) -> bool:
        """Check if persona is external (Customer/Supplier)."""
        external_roles = {ERPNextRole.CUSTOMER.value, ERPNextRole.SUPPLIER.value}
        return bool(set(persona.erpnext_roles).intersection(external_roles))

    @staticmethod
    def _is_admin_persona(persona: Persona) -> bool:
        """Check if persona has admin roles."""
        admin_roles = {
            ERPNextRole.ADMINISTRATOR.value,
            ERPNextRole.SYSTEM_MANAGER.value,
        }
        return bool(set(persona.erpnext_roles).intersection(admin_roles))

    @staticmethod
    def _generate_default_permissions(module: str, user_level: str) -> str:
        """Generate default permissions for module and user level."""
        permissions = []

        # Base read permission
        permissions.append(f"read:{module}")

        # Additional permissions based on user level
        if user_level.lower() in ["user", "manager", "admin"]:
            permissions.append(f"write:{module}")

        if user_level.lower() in ["manager", "admin"]:
            permissions.extend(
                [f"create:{module}_documents", f"delete:{module}_documents"]
            )

        if user_level.lower() == "admin":
            permissions.append(f"admin:{module}")

        return ",".join(permissions)
