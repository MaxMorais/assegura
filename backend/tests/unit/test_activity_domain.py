"""Unit tests for activity domain entities and services.

This module provides comprehensive unit tests for the Activity domain,
including entity validation, business rules, and domain services.
"""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any, List

from src.domain.activities.activity import Activity
from src.domain.activities.activity_service import ActivityService
from src.domain.activities.exceptions import (
    ActivityValidationError,
    ActivityMultipleValidationError,
    ActivityIncompatibleError
)


class TestActivityEntity:
    """Unit tests for Activity domain entity."""
    
    @pytest.fixture
    def valid_activity_data(self) -> Dict[str, Any]:
        """Valid activity data for testing."""
        return {
            "name": "Test Activity",
            "description": "A test activity for unit testing",
            "erpnext_module": "Accounts",
            "action_type": "create",
            "target_doctype": "Sales Invoice",
            "required_fields": ["customer", "items"],
            "validation_rules": {"customer": {"required": True}},
            "success_criteria": ["Document created", "Status is Draft"],
            "complexity_score": 3,
            "estimated_duration": 120,
            "prerequisites": ["Customer exists"],
            "postconditions": ["Invoice saved"],
            "test_data_requirements": {"customer": "test_customer"},
            "tags": ["test", "automation"],
            "is_active": True,
            "version": "1.0.0"
        }
    
    def test_create_valid_activity(self, valid_activity_data: Dict[str, Any]):
        """Test creating a valid activity."""
        activity = Activity(**valid_activity_data)
        
        assert activity.name == valid_activity_data["name"]
        assert activity.description == valid_activity_data["description"]
        assert activity.erpnext_module == valid_activity_data["erpnext_module"]
        assert activity.action_type == valid_activity_data["action_type"]
        assert activity.target_doctype == valid_activity_data["target_doctype"]
        assert activity.complexity_score == valid_activity_data["complexity_score"]
        assert activity.estimated_duration == valid_activity_data["estimated_duration"]
        assert activity.is_active == valid_activity_data["is_active"]
        assert activity.version == valid_activity_data["version"]
        assert isinstance(activity.id, uuid.UUID)
        assert isinstance(activity.created_at, datetime)
        assert isinstance(activity.updated_at, datetime)
    
    def test_activity_name_validation(self, valid_activity_data: Dict[str, Any]):
        """Test activity name validation."""
        
        # Test empty name
        with pytest.raises(ActivityValidationError) as exc_info:
            Activity(**{**valid_activity_data, "name": ""})
        assert "name" in str(exc_info.value)
        assert "required" in str(exc_info.value).lower()
        
        # Test whitespace-only name
        with pytest.raises(ActivityValidationError) as exc_info:
            Activity(**{**valid_activity_data, "name": "   "})
        assert "name" in str(exc_info.value)
        
        # Test name too long
        with pytest.raises(ActivityValidationError) as exc_info:
            Activity(**{**valid_activity_data, "name": "x" * 256})
        assert "name" in str(exc_info.value)
        assert "255" in str(exc_info.value)
    
    def test_activity_description_validation(self, valid_activity_data: Dict[str, Any]):
        """Test activity description validation."""
        
        # Test empty description
        with pytest.raises(ActivityValidationError) as exc_info:
            Activity(**{**valid_activity_data, "description": ""})
        assert "description" in str(exc_info.value)
        
        # Test description too long
        with pytest.raises(ActivityValidationError) as exc_info:
            Activity(**{**valid_activity_data, "description": "x" * 2001})
        assert "description" in str(exc_info.value)
        assert "2000" in str(exc_info.value)
    
    def test_erpnext_module_validation(self, valid_activity_data: Dict[str, Any]):
        """Test ERPNext module validation."""
        
        # Test invalid module
        with pytest.raises(ActivityValidationError) as exc_info:
            Activity(**{**valid_activity_data, "erpnext_module": "InvalidModule"})
        assert "erpnext_module" in str(exc_info.value)
        assert "valid ERPNext module" in str(exc_info.value)
        
        # Test valid modules
        valid_modules = [
            "Accounts", "Stock", "Buying", "Selling", "CRM", "Projects",
            "Manufacturing", "HR", "Payroll", "Assets", "Support", "Website",
            "Desk", "Core", "Custom", "Integrations"
        ]
        
        for module in valid_modules:
            activity = Activity(**{**valid_activity_data, "erpnext_module": module})
            assert activity.erpnext_module == module
    
    def test_action_type_validation(self, valid_activity_data: Dict[str, Any]):
        """Test action type validation."""
        
        # Test invalid action type
        with pytest.raises(ActivityValidationError) as exc_info:
            Activity(**{**valid_activity_data, "action_type": "invalid_action"})
        assert "action_type" in str(exc_info.value)
        
        # Test valid action types
        valid_actions = [
            "create", "read", "update", "delete", "list", "search", "filter",
            "export", "import", "approve", "reject", "submit", "cancel",
            "duplicate", "print", "email", "share", "assign", "comment",
            "attachment", "workflow", "permission", "custom"
        ]
        
        for action in valid_actions:
            activity = Activity(**{**valid_activity_data, "action_type": action})
            assert activity.action_type == action
    
    def test_complexity_score_validation(self, valid_activity_data: Dict[str, Any]):
        """Test complexity score validation."""
        
        # Test invalid complexity scores
        invalid_scores = [-1, 0, 6, 10]
        for score in invalid_scores:
            with pytest.raises(ActivityValidationError) as exc_info:
                Activity(**{**valid_activity_data, "complexity_score": score})
            assert "complexity_score" in str(exc_info.value)
            assert "1 and 5" in str(exc_info.value)
        
        # Test valid complexity scores
        for score in range(1, 6):
            activity = Activity(**{**valid_activity_data, "complexity_score": score})
            assert activity.complexity_score == score
    
    def test_estimated_duration_validation(self, valid_activity_data: Dict[str, Any]):
        """Test estimated duration validation."""
        
        # Test invalid durations
        invalid_durations = [-1, 0]
        for duration in invalid_durations:
            with pytest.raises(ActivityValidationError) as exc_info:
                Activity(**{**valid_activity_data, "estimated_duration": duration})
            assert "estimated_duration" in str(exc_info.value)
            assert "positive" in str(exc_info.value)
        
        # Test valid durations
        valid_durations = [1, 30, 60, 120, 300, 3600]
        for duration in valid_durations:
            activity = Activity(**{**valid_activity_data, "estimated_duration": duration})
            assert activity.estimated_duration == duration
    
    def test_target_doctype_validation(self, valid_activity_data: Dict[str, Any]):
        """Test target DocType validation."""
        
        # Test empty DocType
        with pytest.raises(ActivityValidationError) as exc_info:
            Activity(**{**valid_activity_data, "target_doctype": ""})
        assert "target_doctype" in str(exc_info.value)
        
        # Test DocType too long
        with pytest.raises(ActivityValidationError) as exc_info:
            Activity(**{**valid_activity_data, "target_doctype": "x" * 101})
        assert "target_doctype" in str(exc_info.value)
        assert "100" in str(exc_info.value)
    
    def test_version_validation(self, valid_activity_data: Dict[str, Any]):
        """Test version validation."""
        
        # Test invalid version formats
        invalid_versions = ["", "1", "1.0", "1.0.0.0", "v1.0.0", "invalid"]
        for version in invalid_versions:
            with pytest.raises(ActivityValidationError) as exc_info:
                Activity(**{**valid_activity_data, "version": version})
            assert "version" in str(exc_info.value)
        
        # Test valid version formats
        valid_versions = ["1.0.0", "2.1.3", "10.15.22", "0.1.0"]
        for version in valid_versions:
            activity = Activity(**{**valid_activity_data, "version": version})
            assert activity.version == version
    
    def test_validation_rules_property(self, valid_activity_data: Dict[str, Any]):
        """Test validation rules property handling."""
        
        # Test with valid JSON
        validation_rules = {
            "customer": {"required": True, "type": "string"},
            "amount": {"required": True, "type": "number", "min": 0}
        }
        activity = Activity(**{**valid_activity_data, "validation_rules": validation_rules})
        assert activity.validation_rules == validation_rules
        assert activity.validation_rules_json == '{"customer": {"required": true, "type": "string"}, "amount": {"required": true, "type": "number", "min": 0}}'
    
    def test_test_data_requirements_property(self, valid_activity_data: Dict[str, Any]):
        """Test test data requirements property handling."""
        
        # Test with valid JSON
        test_data = {
            "customer": "test_customer_001",
            "items": [{"item_code": "ITEM001", "qty": 1}]
        }
        activity = Activity(**{**valid_activity_data, "test_data_requirements": test_data})
        assert activity.test_data_requirements == test_data
        assert activity.test_data_requirements_json == '{"customer": "test_customer_001", "items": [{"item_code": "ITEM001", "qty": 1}]}'
    
    def test_list_properties(self, valid_activity_data: Dict[str, Any]):
        """Test list property string conversions."""
        
        activity = Activity(**valid_activity_data)
        
        # Test required_fields
        assert activity.required_fields == ["customer", "items"]
        assert activity.required_fields_str == "customer, items"
        
        # Test success_criteria
        assert activity.success_criteria == ["Document created", "Status is Draft"]
        assert activity.success_criteria_str == "Document created, Status is Draft"
        
        # Test prerequisites
        assert activity.prerequisites == ["Customer exists"]
        assert activity.prerequisites_str == "Customer exists"
        
        # Test postconditions
        assert activity.postconditions == ["Invoice saved"]
        assert activity.postconditions_str == "Invoice saved"
        
        # Test tags
        assert activity.tags == ["test", "automation"]
        assert activity.tags_str == "test, automation"
    
    def test_activity_similarity_calculation(self, valid_activity_data: Dict[str, Any]):
        """Test activity similarity calculation."""
        
        activity1 = Activity(**valid_activity_data)
        
        # Create similar activity
        similar_data = {**valid_activity_data, "name": "Similar Test Activity"}
        activity2 = Activity(**similar_data)
        
        similarity = activity1.calculate_similarity(activity2)
        assert 0.8 <= similarity <= 1.0  # Should be very similar
        
        # Create different activity
        different_data = {
            **valid_activity_data,
            "name": "Different Activity",
            "erpnext_module": "Stock",
            "action_type": "delete",
            "target_doctype": "Stock Entry",
            "complexity_score": 5,
            "tags": ["different", "test"]
        }
        activity3 = Activity(**different_data)
        
        similarity = activity1.calculate_similarity(activity3)
        assert 0.0 <= similarity <= 0.5  # Should be quite different
    
    def test_activity_update_functionality(self, valid_activity_data: Dict[str, Any]):
        """Test activity update functionality."""
        
        activity = Activity(**valid_activity_data)
        original_updated_at = activity.updated_at
        
        # Update activity
        activity.name = "Updated Activity Name"
        activity.description = "Updated description"
        activity.complexity_score = 4
        activity.is_active = False
        
        activity.update()
        
        assert activity.name == "Updated Activity Name"
        assert activity.description == "Updated description"
        assert activity.complexity_score == 4
        assert activity.is_active is False
        assert activity.updated_at > original_updated_at
    
    def test_multiple_validation_errors(self, valid_activity_data: Dict[str, Any]):
        """Test handling of multiple validation errors."""
        
        invalid_data = {
            **valid_activity_data,
            "name": "",  # Invalid: empty
            "description": "",  # Invalid: empty
            "complexity_score": 10,  # Invalid: out of range
            "estimated_duration": -5,  # Invalid: negative
            "erpnext_module": "InvalidModule",  # Invalid: not in allowed list
            "action_type": "invalid_action",  # Invalid: not in allowed list
            "version": "invalid_version"  # Invalid: wrong format
        }
        
        with pytest.raises(ActivityMultipleValidationError) as exc_info:
            Activity(**invalid_data)
        
        error = exc_info.value
        assert len(error.errors) >= 5  # Should have multiple validation errors
        
        # Check that specific errors are present
        error_messages = [str(err) for err in error.errors]
        assert any("name" in msg for msg in error_messages)
        assert any("description" in msg for msg in error_messages)
        assert any("complexity_score" in msg for msg in error_messages)
        assert any("estimated_duration" in msg for msg in error_messages)


class TestActivityService:
    """Unit tests for Activity domain service."""
    
    @pytest.fixture
    def valid_activity_data(self) -> Dict[str, Any]:
        """Valid activity data for testing."""
        return {
            "name": "Service Test Activity",
            "description": "A test activity for service testing",
            "erpnext_module": "Accounts",
            "action_type": "create",
            "target_doctype": "Sales Invoice",
            "required_fields": ["customer", "items"],
            "validation_rules": {"customer": {"required": True}},
            "success_criteria": ["Document created"],
            "complexity_score": 3,
            "estimated_duration": 120,
            "prerequisites": ["Customer exists"],
            "postconditions": ["Invoice saved"],
            "test_data_requirements": {"customer": "test_customer"},
            "tags": ["test"],
            "is_active": True,
            "version": "1.0.0"
        }
    
    @pytest.fixture
    def activity_service(self) -> ActivityService:
        """Activity service fixture."""
        return ActivityService()
    
    def test_validate_activity_configuration(
        self, 
        activity_service: ActivityService,
        valid_activity_data: Dict[str, Any]
    ):
        """Test activity configuration validation."""
        
        activity = Activity(**valid_activity_data)
        
        # Test valid configuration
        result = activity_service.validate_activity_configuration(activity)
        assert result["is_valid"] is True
        assert len(result.get("errors", [])) == 0
        
        # Test configuration with issues
        problematic_data = {
            **valid_activity_data,
            "required_fields": [],  # No required fields
            "success_criteria": [],  # No success criteria
            "validation_rules": {},  # No validation rules
            "test_data_requirements": {}  # No test data requirements
        }
        problematic_activity = Activity(**problematic_data)
        
        result = activity_service.validate_activity_configuration(problematic_activity)
        assert len(result.get("warnings", [])) > 0
    
    def test_calculate_compatibility(
        self, 
        activity_service: ActivityService,
        valid_activity_data: Dict[str, Any]
    ):
        """Test activity compatibility calculation."""
        
        # Create first activity
        activity1 = Activity(**valid_activity_data)
        
        # Create compatible activity (same module, different action)
        compatible_data = {
            **valid_activity_data,
            "name": "Read Sales Invoice",
            "action_type": "read",
            "prerequisites": ["Invoice exists"],
            "postconditions": ["Data retrieved"]
        }
        activity2 = Activity(**compatible_data)
        
        compatibility = activity_service.calculate_compatibility(activity1, activity2)
        assert compatibility["compatible"] is True
        assert compatibility["compatibility_score"] > 0.5
        
        # Create incompatible activity (conflicting postconditions/prerequisites)
        incompatible_data = {
            **valid_activity_data,
            "name": "Delete Customer",
            "erpnext_module": "CRM",
            "action_type": "delete",
            "target_doctype": "Customer",
            "prerequisites": ["Customer exists"],
            "postconditions": ["Customer deleted"]
        }
        activity3 = Activity(**incompatible_data)
        
        compatibility = activity_service.calculate_compatibility(activity1, activity3)
        assert compatibility["compatible"] is False
        assert compatibility["compatibility_score"] < 0.5
    
    def test_suggest_similar_activities(
        self, 
        activity_service: ActivityService,
        valid_activity_data: Dict[str, Any]
    ):
        """Test similar activities suggestion."""
        
        base_activity = Activity(**valid_activity_data)
        
        # Create pool of activities
        activities = []
        
        # Very similar activity
        similar_data = {**valid_activity_data, "name": "Create Purchase Invoice"}
        activities.append(Activity(**similar_data))
        
        # Somewhat similar activity
        somewhat_similar_data = {
            **valid_activity_data,
            "name": "Create Customer",
            "erpnext_module": "CRM",
            "target_doctype": "Customer"
        }
        activities.append(Activity(**somewhat_similar_data))
        
        # Different activity
        different_data = {
            **valid_activity_data,
            "name": "Delete Stock Entry",
            "erpnext_module": "Stock",
            "action_type": "delete",
            "target_doctype": "Stock Entry",
            "complexity_score": 5
        }
        activities.append(Activity(**different_data))
        
        suggestions = activity_service.suggest_similar_activities(
            base_activity, 
            activities, 
            min_similarity=0.3
        )
        
        assert len(suggestions) >= 1  # Should find at least the very similar one
        assert all(s["similarity_score"] >= 0.3 for s in suggestions)
        assert suggestions[0]["similarity_score"] > suggestions[-1]["similarity_score"]  # Should be sorted
    
    def test_analyze_activity_relationships(
        self, 
        activity_service: ActivityService,
        valid_activity_data: Dict[str, Any]
    ):
        """Test activity relationship analysis."""
        
        # Create sequence of related activities
        create_customer_data = {
            **valid_activity_data,
            "name": "Create Customer",
            "erpnext_module": "CRM",
            "action_type": "create",
            "target_doctype": "Customer",
            "postconditions": ["Customer created", "Customer ID generated"]
        }
        create_customer = Activity(**create_customer_data)
        
        create_invoice_data = {
            **valid_activity_data,
            "name": "Create Sales Invoice",
            "prerequisites": ["Customer exists"],
            "postconditions": ["Invoice created", "Customer linked"]
        }
        create_invoice = Activity(**create_invoice_data)
        
        activities = [create_customer, create_invoice]
        
        relationships = activity_service.analyze_activity_relationships(activities)
        
        assert len(relationships) > 0
        assert any(
            rel["from_activity_name"] == "Create Customer" and 
            rel["to_activity_name"] == "Create Sales Invoice"
            for rel in relationships
        )
    
    def test_generate_execution_context(
        self, 
        activity_service: ActivityService,
        valid_activity_data: Dict[str, Any]
    ):
        """Test execution context generation."""
        
        activity = Activity(**valid_activity_data)
        
        context = activity_service.generate_execution_context(activity)
        
        assert "activity_id" in context
        assert "required_fields" in context
        assert "validation_rules" in context
        assert "success_criteria" in context
        assert "test_data" in context
        assert "metadata" in context
        
        assert context["activity_id"] == str(activity.id)
        assert context["required_fields"] == activity.required_fields
        assert context["validation_rules"] == activity.validation_rules
        assert context["success_criteria"] == activity.success_criteria
    
    def test_check_prerequisite_satisfaction(
        self, 
        activity_service: ActivityService,
        valid_activity_data: Dict[str, Any]
    ):
        """Test prerequisite satisfaction checking."""
        
        activity = Activity(**valid_activity_data)
        
        # Test with satisfied prerequisites
        satisfied_state = {
            "customer_exists": True,
            "items_available": True,
            "permissions_granted": True
        }
        
        result = activity_service.check_prerequisite_satisfaction(activity, satisfied_state)
        assert result["satisfied"] is True
        assert len(result.get("missing_prerequisites", [])) == 0
        
        # Test with unsatisfied prerequisites
        unsatisfied_state = {
            "customer_exists": False,
            "items_available": True
        }
        
        result = activity_service.check_prerequisite_satisfaction(activity, unsatisfied_state)
        assert result["satisfied"] is False
        assert len(result.get("missing_prerequisites", [])) > 0
    
    def test_estimate_execution_time(
        self, 
        activity_service: ActivityService,
        valid_activity_data: Dict[str, Any]
    ):
        """Test execution time estimation."""
        
        activity = Activity(**valid_activity_data)
        
        # Test base estimation
        estimation = activity_service.estimate_execution_time(activity)
        assert estimation["base_duration"] == activity.estimated_duration
        assert "adjusted_duration" in estimation
        assert "factors" in estimation
        
        # Test with complexity adjustment
        high_complexity_data = {**valid_activity_data, "complexity_score": 5}
        high_complexity_activity = Activity(**high_complexity_data)
        
        high_complexity_estimation = activity_service.estimate_execution_time(high_complexity_activity)
        assert high_complexity_estimation["adjusted_duration"] > estimation["adjusted_duration"]