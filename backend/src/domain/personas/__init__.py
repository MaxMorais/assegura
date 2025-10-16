"""Persona domain module.

Contains the persona aggregate root and related domain objects
for the ERPNext Test Automation Meta-Framework.
"""

from .persona import Persona
from .erpnext_roles import ERPNextRole, validate_erpnext_roles, get_role_recommendations, validate_role_combination
from .exceptions import (
    PersonaDomainError,
    PersonaValidationError,
    PersonaNotFoundError,
    PersonaAlreadyExistsError,
    PersonaStateError,
    PersonaBusinessRuleError,
    PersonaPermissionError,
    PersonaRoleError,
    PersonaConcurrencyError,
    PersonaMultipleValidationError
)

__all__ = [
    # Main entities
    'Persona',
    
    # Value objects
    'ERPNextRole',
    
    # Validation functions
    'validate_erpnext_roles',
    'get_role_recommendations', 
    'validate_role_combination',
    
    # Exceptions
    'PersonaDomainError',
    'PersonaValidationError',
    'PersonaNotFoundError',
    'PersonaAlreadyExistsError',
    'PersonaStateError',
    'PersonaBusinessRuleError',
    'PersonaPermissionError',
    'PersonaRoleError',
    'PersonaConcurrencyError',
    'PersonaMultipleValidationError'
]