"""Journey test fixtures with sample data."""

from datetime import datetime


def sample_persona_data():
    """Sample persona data for testing."""
    return {
        "name": "Test Persona",
        "description": "A test persona for journey testing with sufficient length to meet validation requirements",
        "erpnext_roles": "Sales Manager,Sales User",
        "permissions": "read:sales_order,write:sales_order",
        "is_active": True
    }


def sample_activity_data():
    """Sample activity data for testing."""
    return {
        "name": "Test Activity",
        "description": "A test activity for journey testing",
        "erpnext_module": "Sales",
        "action_type": "create",
        "target_doctype": "Sales Order",
        "required_fields": ["name", "description"],
        "success_criteria": ["Activity created successfully"],
        "complexity_score": 2,
        "estimated_duration": 126,
        "tags": ["test", "sample"]
    }


def sample_journey_data(persona_id=None, activity_id=None, action_id=None, name=None, complexity_level=None):
    """Sample journey data for testing."""
    journey_data = {
        "name": name or "Test Journey",
        "description": "A test journey for validation",
        "persona_id": persona_id or "test-persona-id",  # Will be replaced with actual ID
        "activity_id": activity_id or "test-activity-id",  # Will be replaced with actual ID
    }
    
    # Only include steps if action_id is provided
    if action_id:
        journey_data["steps"] = [
            {
                "step_number": 1,
                "action_id": action_id,
                "action_name": "Test Action",
                "action_type": "when",
                "step_description": "First step in test journey",
                "parameters": {},
                "expected_outputs": {},
                "can_run_parallel": False,
                "is_critical": True
            }
        ]
    
    return journey_data


def sample_action_data():
    """Sample action data for testing."""
    return {
        "name": "Test Action",
        "description": "A test action for journey testing with sufficient length to meet validation requirements",
        "action_type": "when",
        "implementation_type": "robot_framework",
        "erpnext_module": "Sales",
        "execution_timeout": 60,
        "retry_count": 0,
        "tags": ["test", "sample"],
        "robot_keywords": ["Test Keyword", "Another Keyword"],
        "parameters": [],
        "expected_outputs": []
    }


def sample_journey_step_data(action_id=None):
    """Sample journey step data for testing."""
    return {
        "action_id": action_id or "test-action-id",
        "action_name": "Test Action",
        "action_type": "when",
        "step_description": "A test journey step",
        "parameters": {},
        "expected_outputs": {},
        "can_run_parallel": False,
        "is_critical": True
    }