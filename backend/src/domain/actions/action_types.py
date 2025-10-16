"""
Given/When/Then Action Classifications

This module provides specialized action types for BDD (Behavior-Driven Development)
test automation, implementing the Given/When/Then pattern with specific validation
rules and execution patterns for each type.
"""

from typing import List, Dict, Any, Optional, Set
from abc import ABC, abstractmethod
from enum import Enum

from .action_library import Action, ActionType, ImplementationType, ActionParameter, ActionOutput


class GivenActionPattern(Enum):
    """Common patterns for Given (precondition) actions."""
    
    USER_LOGIN = "user_login"                    # User authentication
    DATA_SETUP = "data_setup"                   # Test data preparation
    SYSTEM_STATE = "system_state"               # System configuration
    NAVIGATION = "navigation"                   # UI navigation
    PERMISSION_SETUP = "permission_setup"       # User permissions
    COMPANY_SETUP = "company_setup"            # Company/tenant setup
    MODULE_CONFIG = "module_config"            # ERPNext module configuration
    WORKFLOW_STATE = "workflow_state"          # Document workflow state


class WhenActionPattern(Enum):
    """Common patterns for When (action/operation) actions."""
    
    CREATE_DOCUMENT = "create_document"         # Create new document
    UPDATE_DOCUMENT = "update_document"         # Update existing document
    DELETE_DOCUMENT = "delete_document"         # Delete document
    SUBMIT_DOCUMENT = "submit_document"         # Submit document
    CANCEL_DOCUMENT = "cancel_document"         # Cancel document
    APPROVE_DOCUMENT = "approve_document"       # Approve document
    BULK_OPERATION = "bulk_operation"          # Bulk operations
    WORKFLOW_ACTION = "workflow_action"        # Workflow transition
    API_CALL = "api_call"                      # Direct API operation
    FORM_SUBMISSION = "form_submission"        # UI form submission
    SEARCH_FILTER = "search_filter"            # Search/filter operations
    REPORT_GENERATION = "report_generation"    # Generate reports


class ThenActionPattern(Enum):
    """Common patterns for Then (verification) actions."""
    
    DOCUMENT_EXISTS = "document_exists"         # Verify document exists
    DOCUMENT_STATE = "document_state"          # Verify document state
    FIELD_VALUE = "field_value"                # Verify field values
    LIST_CONTAINS = "list_contains"            # Verify list contents
    ERROR_MESSAGE = "error_message"            # Verify error messages
    SUCCESS_MESSAGE = "success_message"        # Verify success messages
    WORKFLOW_STATE = "workflow_state"          # Verify workflow state
    PERMISSION_CHECK = "permission_check"      # Verify permissions
    CALCULATION = "calculation"                # Verify calculations
    NOTIFICATION = "notification"              # Verify notifications
    EMAIL_SENT = "email_sent"                 # Verify email delivery
    REPORT_CONTENT = "report_content"         # Verify report content


class ActionClassificationService:
    """Service for action classification and validation."""
    
    @staticmethod
    def get_valid_patterns_for_type(action_type: ActionType) -> List[str]:
        """
        Get valid patterns for action type.
        
        Args:
            action_type: The BDD action type
            
        Returns:
            List of valid pattern names
        """
        if action_type == ActionType.GIVEN:
            return [pattern.value for pattern in GivenActionPattern]
        elif action_type == ActionType.WHEN:
            return [pattern.value for pattern in WhenActionPattern]
        elif action_type == ActionType.THEN:
            return [pattern.value for pattern in ThenActionPattern]
        else:
            return []
    
    @staticmethod
    def validate_action_classification(action: Action) -> List[str]:
        """
        Validate action classification rules.
        
        Args:
            action: Action to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not action.action_type:
            errors.append("Action type is required")
            return errors
        
        # Type-specific validation
        if action.action_type == ActionType.GIVEN:
            errors.extend(ActionClassificationService._validate_given_action(action))
        elif action.action_type == ActionType.WHEN:
            errors.extend(ActionClassificationService._validate_when_action(action))
        elif action.action_type == ActionType.THEN:
            errors.extend(ActionClassificationService._validate_then_action(action))
        
        return errors
    
    @staticmethod
    def _validate_given_action(action: Action) -> List[str]:
        """Validate Given action specific rules."""
        errors = []
        
        # Given actions should typically be setup/precondition actions
        if action.implementation_type == ImplementationType.VERIFICATION:
            errors.append("Given actions should not be verification actions - use Then instead")
        
        # Given actions should not have complex outputs (they set up state)
        if len(action.expected_outputs) > 3:
            errors.append("Given actions should have minimal outputs (max 3) - they set up state")
        
        # Check for appropriate naming patterns
        given_keywords = ["given", "setup", "prepare", "login", "navigate", "create", "configure"]
        if not any(keyword in action.name.lower() for keyword in given_keywords):
            errors.append("Given action name should indicate setup/precondition (e.g., 'Given user is logged in')")
        
        return errors
    
    @staticmethod
    def _validate_when_action(action: Action) -> List[str]:
        """Validate When action specific rules."""
        errors = []
        
        # When actions should not be pure setup or verification
        if action.implementation_type == ImplementationType.DATA_SETUP:
            errors.append("When actions should not be data setup - use Given instead")
        
        if action.implementation_type == ImplementationType.VERIFICATION:
            errors.append("When actions should not be verification - use Then instead")
        
        # When actions should have meaningful outputs
        if len(action.expected_outputs) == 0 and action.implementation_type != ImplementationType.CLEANUP:
            errors.append("When actions should typically produce outputs to verify")
        
        # Check for appropriate naming patterns
        when_keywords = ["when", "create", "update", "delete", "submit", "cancel", "approve", "process"]
        if not any(keyword in action.name.lower() for keyword in when_keywords):
            errors.append("When action name should indicate the main action (e.g., 'When user creates invoice')")
        
        return errors
    
    @staticmethod
    def _validate_then_action(action: Action) -> List[str]:
        """Validate Then action specific rules."""
        errors = []
        
        # Then actions should be verification/assertion actions
        if action.implementation_type not in [ImplementationType.VERIFICATION, ImplementationType.API_CALL]:
            errors.append("Then actions should typically be verification actions")
        
        # Then actions should have minimal parameters (they verify existing state)
        if len(action.parameters) > 5:
            errors.append("Then actions should have minimal parameters (max 5) - they verify state")
        
        # Then actions should not have many outputs (they verify, not create)
        if len(action.expected_outputs) > 2:
            errors.append("Then actions should have minimal outputs (max 2) - they verify results")
        
        # Check for appropriate naming patterns
        then_keywords = ["then", "should", "verify", "check", "assert", "confirm", "validate", "exists"]
        if not any(keyword in action.name.lower() for keyword in then_keywords):
            errors.append("Then action name should indicate verification (e.g., 'Then invoice should be created')")
        
        return errors
    
    @staticmethod
    def suggest_action_type(action: Action) -> ActionType:
        """
        Suggest appropriate action type based on action characteristics.
        
        Args:
            action: Action to analyze
            
        Returns:
            Suggested action type
        """
        name_lower = action.name.lower() if action.name else ""
        desc_lower = action.description.lower() if action.description else ""
        
        # Analyze name and description for keywords
        given_indicators = ["given", "setup", "prepare", "login", "navigate", "configure", "initialize"]
        when_indicators = ["when", "create", "update", "delete", "submit", "process", "execute", "perform"]
        then_indicators = ["then", "should", "verify", "check", "assert", "validate", "confirm", "exists"]
        
        given_score = sum(1 for word in given_indicators if word in name_lower or word in desc_lower)
        when_score = sum(1 for word in when_indicators if word in name_lower or word in desc_lower)
        then_score = sum(1 for word in then_indicators if word in name_lower or word in desc_lower)
        
        # Consider implementation type
        if action.implementation_type == ImplementationType.VERIFICATION:
            then_score += 2
        elif action.implementation_type == ImplementationType.DATA_SETUP:
            given_score += 2
        elif action.implementation_type in [ImplementationType.UI_INTERACTION, ImplementationType.API_CALL]:
            when_score += 1
        
        # Determine best match
        if given_score > when_score and given_score > then_score:
            return ActionType.GIVEN
        elif then_score > when_score and then_score > given_score:
            return ActionType.THEN
        else:
            return ActionType.WHEN
    
    @staticmethod
    def get_recommended_parameters_for_pattern(pattern: str, action_type: ActionType) -> List[ActionParameter]:
        """
        Get recommended parameters for common action patterns.
        
        Args:
            pattern: Action pattern
            action_type: BDD action type
            
        Returns:
            List of recommended parameters
        """
        parameters = []
        
        if action_type == ActionType.GIVEN:
            if pattern == GivenActionPattern.USER_LOGIN.value:
                parameters = [
                    ActionParameter("username", "string", required=True, description="Username for login"),
                    ActionParameter("password", "string", required=True, description="Password for login"),
                    ActionParameter("company", "string", required=False, description="Company to login to")
                ]
            elif pattern == GivenActionPattern.DATA_SETUP.value:
                parameters = [
                    ActionParameter("doctype", "string", required=True, description="Document type to create"),
                    ActionParameter("data", "object", required=True, description="Document data"),
                    ActionParameter("save", "boolean", required=False, description="Save after creation", default_value=True)
                ]
            elif pattern == GivenActionPattern.NAVIGATION.value:
                parameters = [
                    ActionParameter("module", "string", required=True, description="ERPNext module name"),
                    ActionParameter("doctype", "string", required=False, description="Document type to navigate to"),
                    ActionParameter("view", "string", required=False, description="View type (list/form/report)")
                ]
        
        elif action_type == ActionType.WHEN:
            if pattern == WhenActionPattern.CREATE_DOCUMENT.value:
                parameters = [
                    ActionParameter("doctype", "string", required=True, description="Document type"),
                    ActionParameter("data", "object", required=True, description="Document data"),
                    ActionParameter("save", "boolean", required=False, description="Save document", default_value=True),
                    ActionParameter("submit", "boolean", required=False, description="Submit document", default_value=False)
                ]
            elif pattern == WhenActionPattern.UPDATE_DOCUMENT.value:
                parameters = [
                    ActionParameter("doctype", "string", required=True, description="Document type"),
                    ActionParameter("name", "string", required=True, description="Document name/ID"),
                    ActionParameter("data", "object", required=True, description="Updated data"),
                    ActionParameter("save", "boolean", required=False, description="Save changes", default_value=True)
                ]
        
        elif action_type == ActionType.THEN:
            if pattern == ThenActionPattern.DOCUMENT_EXISTS.value:
                parameters = [
                    ActionParameter("doctype", "string", required=True, description="Document type"),
                    ActionParameter("name", "string", required=True, description="Document name/ID")
                ]
            elif pattern == ThenActionPattern.FIELD_VALUE.value:
                parameters = [
                    ActionParameter("doctype", "string", required=True, description="Document type"),
                    ActionParameter("name", "string", required=True, description="Document name/ID"),
                    ActionParameter("field", "string", required=True, description="Field name"),
                    ActionParameter("expected_value", "string", required=True, description="Expected field value")
                ]
        
        return parameters
    
    @staticmethod
    def get_recommended_outputs_for_pattern(pattern: str, action_type: ActionType) -> List[ActionOutput]:
        """
        Get recommended outputs for common action patterns.
        
        Args:
            pattern: Action pattern
            action_type: BDD action type
            
        Returns:
            List of recommended outputs
        """
        outputs = []
        
        if action_type == ActionType.GIVEN:
            if pattern == GivenActionPattern.USER_LOGIN.value:
                outputs = [
                    ActionOutput("logged_in", "boolean", "Whether login was successful"),
                    ActionOutput("session_id", "string", "Session identifier")
                ]
            elif pattern == GivenActionPattern.DATA_SETUP.value:
                outputs = [
                    ActionOutput("document_name", "string", "Name/ID of created document"),
                    ActionOutput("success", "boolean", "Whether setup was successful")
                ]
        
        elif action_type == ActionType.WHEN:
            if pattern == WhenActionPattern.CREATE_DOCUMENT.value:
                outputs = [
                    ActionOutput("document_name", "string", "Name/ID of created document"),
                    ActionOutput("status", "string", "Document status after creation"),
                    ActionOutput("success", "boolean", "Whether creation was successful")
                ]
            elif pattern == WhenActionPattern.UPDATE_DOCUMENT.value:
                outputs = [
                    ActionOutput("updated", "boolean", "Whether update was successful"),
                    ActionOutput("modified", "string", "Last modified timestamp")
                ]
        
        elif action_type == ActionType.THEN:
            if pattern == ThenActionPattern.DOCUMENT_EXISTS.value:
                outputs = [
                    ActionOutput("exists", "boolean", "Whether document exists"),
                    ActionOutput("verification_result", "string", "Verification outcome")
                ]
            elif pattern == ThenActionPattern.FIELD_VALUE.value:
                outputs = [
                    ActionOutput("matches", "boolean", "Whether field value matches expected"),
                    ActionOutput("actual_value", "string", "Actual field value found")
                ]
        
        return outputs
    
    @staticmethod
    def validate_action_sequence(actions: List[Action]) -> List[str]:
        """
        Validate sequence of actions follows BDD patterns.
        
        Args:
            actions: List of actions in sequence
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not actions:
            return errors
        
        # Track action types in sequence
        action_types = [action.action_type for action in actions]
        
        # Check for proper BDD flow
        has_given = ActionType.GIVEN in action_types
        has_when = ActionType.WHEN in action_types
        has_then = ActionType.THEN in action_types
        
        if not has_when:
            errors.append("Action sequence should have at least one When action")
        
        # Check order - Given should come before When, When before Then
        given_indices = [i for i, t in enumerate(action_types) if t == ActionType.GIVEN]
        when_indices = [i for i, t in enumerate(action_types) if t == ActionType.WHEN]
        then_indices = [i for i, t in enumerate(action_types) if t == ActionType.THEN]
        
        # Validate ordering
        if given_indices and when_indices:
            if max(given_indices) > min(when_indices):
                errors.append("Given actions should generally come before When actions")
        
        if when_indices and then_indices:
            if max(when_indices) > min(then_indices):
                errors.append("When actions should generally come before Then actions")
        
        # Check for anti-patterns
        consecutive_same_type = 1
        for i in range(1, len(action_types)):
            if action_types[i] == action_types[i-1]:
                consecutive_same_type += 1
                if consecutive_same_type > 3:
                    errors.append(f"Too many consecutive {action_types[i].value} actions - consider grouping or refactoring")
            else:
                consecutive_same_type = 1
        
        return errors
    
    @staticmethod
    def get_action_complexity_score(action: Action) -> Dict[str, Any]:
        """
        Calculate complexity score for action based on classification.
        
        Args:
            action: Action to analyze
            
        Returns:
            Dictionary with complexity metrics
        """
        base_score = 1
        
        # Implementation type complexity
        impl_scores = {
            ImplementationType.UI_INTERACTION: 3,
            ImplementationType.API_CALL: 2,
            ImplementationType.ROBOT_FRAMEWORK: 4,
            ImplementationType.VERIFICATION: 2,
            ImplementationType.DATA_SETUP: 1,
            ImplementationType.CLEANUP: 1
        }
        
        impl_score = impl_scores.get(action.implementation_type, 2)
        
        # Parameter complexity
        param_score = min(len(action.parameters), 5)  # Cap at 5
        
        # Output complexity  
        output_score = min(len(action.expected_outputs), 3)  # Cap at 3
        
        # Robot keyword complexity
        keyword_score = min(len(action.robot_keywords) // 2, 3)  # 2 keywords = 1 point, cap at 3
        
        # Total complexity
        total_score = base_score + impl_score + param_score + output_score + keyword_score
        
        return {
            "base_score": base_score,
            "implementation_score": impl_score,
            "parameter_score": param_score,
            "output_score": output_score,
            "keyword_score": keyword_score,
            "total_score": total_score,
            "complexity_level": "simple" if total_score <= 5 else "medium" if total_score <= 10 else "complex"
        }


class ActionTypeFactory:
    """Factory for creating actions of specific types with proper defaults."""
    
    @staticmethod
    def create_given_action(
        name: str,
        description: str,
        erpnext_module: str,
        pattern: Optional[GivenActionPattern] = None,
        **kwargs
    ) -> Action:
        """Create a Given action with appropriate defaults."""
        
        # Set appropriate defaults for Given actions
        defaults = {
            "action_type": ActionType.GIVEN,
            "implementation_type": ImplementationType.DATA_SETUP,
            "execution_timeout": 30,
            "retry_count": 1
        }
        
        # Add pattern-specific parameters and outputs
        if pattern:
            defaults["parameters"] = ActionClassificationService.get_recommended_parameters_for_pattern(
                pattern.value, ActionType.GIVEN
            )
            defaults["expected_outputs"] = ActionClassificationService.get_recommended_outputs_for_pattern(
                pattern.value, ActionType.GIVEN
            )
            defaults["tags"] = [pattern.value, "given", "setup"]
        
        # Override with provided kwargs
        defaults.update(kwargs)
        
        return Action.create(
            name=name,
            description=description,
            erpnext_module=erpnext_module,
            **defaults
        )
    
    @staticmethod
    def create_when_action(
        name: str,
        description: str,
        erpnext_module: str,
        pattern: Optional[WhenActionPattern] = None,
        **kwargs
    ) -> Action:
        """Create a When action with appropriate defaults."""
        
        defaults = {
            "action_type": ActionType.WHEN,
            "implementation_type": ImplementationType.UI_INTERACTION,
            "execution_timeout": 60,
            "retry_count": 2
        }
        
        if pattern:
            defaults["parameters"] = ActionClassificationService.get_recommended_parameters_for_pattern(
                pattern.value, ActionType.WHEN
            )
            defaults["expected_outputs"] = ActionClassificationService.get_recommended_outputs_for_pattern(
                pattern.value, ActionType.WHEN
            )
            defaults["tags"] = [pattern.value, "when", "action"]
        
        defaults.update(kwargs)
        
        return Action.create(
            name=name,
            description=description,
            erpnext_module=erpnext_module,
            **defaults
        )
    
    @staticmethod
    def create_then_action(
        name: str,
        description: str,
        erpnext_module: str,
        pattern: Optional[ThenActionPattern] = None,
        **kwargs
    ) -> Action:
        """Create a Then action with appropriate defaults."""
        
        defaults = {
            "action_type": ActionType.THEN,
            "implementation_type": ImplementationType.VERIFICATION,
            "execution_timeout": 30,
            "retry_count": 0  # Verifications typically shouldn't retry
        }
        
        if pattern:
            defaults["parameters"] = ActionClassificationService.get_recommended_parameters_for_pattern(
                pattern.value, ActionType.THEN
            )
            defaults["expected_outputs"] = ActionClassificationService.get_recommended_outputs_for_pattern(
                pattern.value, ActionType.THEN
            )
            defaults["tags"] = [pattern.value, "then", "verification"]
        
        defaults.update(kwargs)
        
        return Action.create(
            name=name,
            description=description,
            erpnext_module=erpnext_module,
            **defaults
        )