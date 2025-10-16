"""Persona domain module.

Contains the persona aggregate root and related domain objects
for the ERPNext Test Automation Meta-Framework.
"""

from .erpnext_roles import (
    ERPNextRole,
    get_role_recommendations,
    validate_erpnext_roles,
    validate_role_combination,
)
from .exceptions import (
    PersonaAlreadyExistsError,
    PersonaBusinessRuleError,
    PersonaConcurrencyError,
    PersonaDomainError,
    PersonaMultipleValidationError,
    PersonaNotFoundError,
    PersonaPermissionError,
    PersonaRoleError,
    PersonaStateError,
    PersonaValidationError,
)
from .persona import Persona
from .persona_service import PersonaService

__all__ = [
    # Main entities
    "Persona",
    "PersonaService",
    # Value objects
    "ERPNextRole",
    # Validation functions
    "validate_erpnext_roles",
    "get_role_recommendations",
    "validate_role_combination",
    # Exceptions
    "PersonaDomainError",
    "PersonaValidationError",
    "PersonaNotFoundError",
    "PersonaAlreadyExistsError",
    "PersonaStateError",
    "PersonaBusinessRuleError",
    "PersonaPermissionError",
    "PersonaRoleError",
    "PersonaConcurrencyError",
    "PersonaMultipleValidationError",
]
