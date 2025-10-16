"""Activity domain exceptions.

This module defines all exceptions related to Activity domain logic
and business rule validation.
"""

from typing import List, Optional


class ActivityDomainError(Exception):
    """Base exception for all activity domain errors."""
    pass


class ActivityValidationError(ActivityDomainError):
    """Exception raised when activity validation fails."""
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error for field '{field}': {message}")


class ActivityMultipleValidationError(ActivityDomainError):
    """Exception raised when multiple activity validation errors occur."""
    
    def __init__(self, errors: List[ActivityValidationError]):
        self.errors = errors
        messages = [str(error) for error in errors]
        super().__init__(f"Multiple validation errors: {'; '.join(messages)}")


class ActivityNotFoundError(ActivityDomainError):
    """Exception raised when an activity is not found."""
    
    def __init__(self, activity_id: str):
        self.activity_id = activity_id
        super().__init__(f"Activity with ID '{activity_id}' not found")


class ActivityAlreadyExistsError(ActivityDomainError):
    """Exception raised when trying to create an activity that already exists."""
    
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Activity with {field} '{value}' already exists")


class ActivityInvalidModuleError(ActivityValidationError):
    """Exception raised when an invalid ERPNext module is specified."""
    
    def __init__(self, module: str):
        self.module = module
        super().__init__("erpnext_module", f"Invalid ERPNext module: {module}")


class ActivityInvalidActionTypeError(ActivityValidationError):
    """Exception raised when an invalid action type is specified."""
    
    def __init__(self, action_type: str, valid_types: List[str]):
        self.action_type = action_type
        self.valid_types = valid_types
        super().__init__(
            "action_type", 
            f"Invalid action type: {action_type}. Valid types: {', '.join(valid_types)}"
        )


class ActivityInactiveError(ActivityDomainError):
    """Exception raised when trying to use an inactive activity."""
    
    def __init__(self, activity_id: str):
        self.activity_id = activity_id
        super().__init__(f"Activity '{activity_id}' is inactive and cannot be used")


class ActivityLinkError(ActivityDomainError):
    """Base exception for activity linking errors."""
    pass


class ActivityPersonaLinkNotFoundError(ActivityLinkError):
    """Exception raised when an activity-persona link is not found."""
    
    def __init__(self, activity_id: str, persona_id: str):
        self.activity_id = activity_id
        self.persona_id = persona_id
        super().__init__(f"Link between activity '{activity_id}' and persona '{persona_id}' not found")


class ActivityPersonaLinkAlreadyExistsError(ActivityLinkError):
    """Exception raised when trying to create a duplicate activity-persona link."""
    
    def __init__(self, activity_id: str, persona_id: str):
        self.activity_id = activity_id
        self.persona_id = persona_id
        super().__init__(f"Activity '{activity_id}' is already linked to persona '{persona_id}'")


class ActivityExecutionError(ActivityDomainError):
    """Exception raised during activity execution."""
    
    def __init__(self, activity_id: str, message: str, context: Optional[dict] = None):
        self.activity_id = activity_id
        self.context = context or {}
        super().__init__(f"Execution error for activity '{activity_id}': {message}")


class ActivityDataValidationError(ActivityDomainError):
    """Exception raised when activity execution data validation fails."""
    
    def __init__(self, activity_id: str, validation_errors: List[str]):
        self.activity_id = activity_id
        self.validation_errors = validation_errors
        error_list = '; '.join(validation_errors)
        super().__init__(f"Data validation failed for activity '{activity_id}': {error_list}")


class ActivityCompatibilityError(ActivityDomainError):
    """Exception raised when activities are not compatible."""
    
    def __init__(self, activity_id: str, target_id: str, reason: str):
        self.activity_id = activity_id
        self.target_id = target_id
        self.reason = reason
        super().__init__(f"Activity '{activity_id}' is not compatible with '{target_id}': {reason}")


class ActivityPrerequisiteError(ActivityDomainError):
    """Exception raised when activity prerequisites are not met."""
    
    def __init__(self, activity_id: str, missing_prerequisites: List[str]):
        self.activity_id = activity_id
        self.missing_prerequisites = missing_prerequisites
        prereq_list = ', '.join(missing_prerequisites)
        super().__init__(f"Prerequisites not met for activity '{activity_id}': {prereq_list}")


class ActivityPostconditionError(ActivityDomainError):
    """Exception raised when activity postconditions are not satisfied."""
    
    def __init__(self, activity_id: str, failed_postconditions: List[str]):
        self.activity_id = activity_id
        self.failed_postconditions = failed_postconditions
        postcond_list = ', '.join(failed_postconditions)
        super().__init__(f"Postconditions not satisfied for activity '{activity_id}': {postcond_list}")