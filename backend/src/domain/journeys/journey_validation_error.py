"""
Journey Validation Error

Custom exception for journey domain validation errors.
"""


class JourneyValidationError(ValueError):
    """
    Exception raised when journey validation fails.
    
    This exception is raised when a journey entity violates domain rules
    or business invariants during creation or updates.
    """
    
    def __init__(self, message: str) -> None:
        """
        Initialize journey validation error.
        
        Args:
            message: Error description
        """
        super().__init__(message)
        self.message = message
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"Journey validation failed: {self.message}"