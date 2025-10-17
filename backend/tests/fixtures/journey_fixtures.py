"""Journey test fixtures with sample data."""

from datetime import datetime


def sample_persona_data():
    """Sample persona data for testing."""
    return {
        "name": "Test Persona",
        "description": "A test persona for journey testing",
        "role": "Test User",
        "department": "Testing",
        "experience_level": "intermediate",
        "goals": ["Complete test journeys", "Validate functionality"],
        "pain_points": ["Complex workflows", "Missing features"],
        "tags": ["test", "automation"]
    }


def sample_activity_data():
    """Sample activity data for testing."""
    return {
        "name": "Test Activity",
        "description": "A test activity for journey testing",
        "action_type": "create",
        "complexity": 2,
        "estimated_duration": 30,
        "required_fields": ["name", "description"],
        "success_criteria": ["Activity created successfully"],
        "tags": ["test", "sample"]
    }


def sample_journey_data():
    """Sample journey data for testing."""
    return {
        "name": "Test Journey",
        "description": "A test journey for validation",
        "persona_id": "test-persona-id",  # Will be replaced with actual ID
        "steps": [
            {
                "name": "Step 1",
                "description": "First step in test journey",
                "activity_id": "test-activity-id",  # Will be replaced with actual ID
                "order": 1,
                "required": True
            }
        ],
        "tags": ["test", "sample"]
    }


def sample_journey_step_data():
    """Sample journey step data for testing."""
    return {
        "name": "Test Step",
        "description": "A test journey step",
        "activity_id": "test-activity-id",
        "order": 1,
        "required": True,
        "conditions": [],
        "expected_outcomes": ["Step completed successfully"]
    }