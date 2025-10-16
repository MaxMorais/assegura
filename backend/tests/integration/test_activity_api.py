"""Integration tests for Activity API endpoints.

This module tests the complete activity API functionality including
CRUD operations, validation, error handling, and relationship management.
"""

import pytest
import uuid
from typing import Dict, Any, List
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.infrastructure.database.config import get_db
from src.infrastructure.database.models.activity_model import ActivityModel, ActivityPersonaLinkModel
from src.infrastructure.database.models.persona_model import PersonaModel


class TestActivityAPI:
    """Test suite for Activity API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session, client: TestClient):
        """Set up test environment."""
        self.db = db_session
        self.client = client
        self.base_url = "/api/v1/activities"
        
        # Create test persona for relationship tests
        self.test_persona = PersonaModel(
            id=uuid.uuid4(),
            name="Test Persona",
            description="Test persona for integration tests",
            erpnext_roles=["System Manager"],
            permissions=["read", "write"],
            experience_level="intermediate",
            business_context="Test context",
            is_active=True
        )
        self.db.add(self.test_persona)
        self.db.commit()
    
    def test_create_activity_success(self):
        """Test successful activity creation."""
        activity_data = {
            "name": "Test Activity Creation",
            "description": "Test activity for integration testing",
            "erpnext_module": "Accounts",
            "action_type": "create",
            "target_doctype": "Sales Invoice",
            "required_fields": ["customer", "items"],
            "validation_rules": {"customer": {"required": True}},
            "success_criteria": ["Invoice created", "Status is Draft"],
            "complexity_score": 5,
            "estimated_duration": 300,
            "prerequisites": ["Customer must exist"],
            "postconditions": ["Invoice exists in system"],
            "is_active": True
        }
        
        response = self.client.post(self.base_url, json=activity_data)
        
        assert response.status_code == 201
        
        response_data = response.json()
        assert response_data["name"] == activity_data["name"]
        assert response_data["description"] == activity_data["description"]
        assert response_data["erpnext_module"] == activity_data["erpnext_module"]
        assert response_data["action_type"] == activity_data["action_type"]
        assert response_data["target_doctype"] == activity_data["target_doctype"]
        assert response_data["complexity_score"] == activity_data["complexity_score"]
        assert response_data["estimated_duration"] == activity_data["estimated_duration"]
        assert response_data["is_active"] == activity_data["is_active"]
        assert "id" in response_data
        assert "created_at" in response_data
        assert "updated_at" in response_data
    
    def test_create_activity_duplicate_name(self):
        """Test activity creation with duplicate name fails."""
        # Create first activity
        activity_data = {
            "name": "Duplicate Activity Name",
            "description": "First activity",
            "erpnext_module": "Accounts",
            "action_type": "create",
            "target_doctype": "Sales Invoice",
            "complexity_score": 3,
            "estimated_duration": 180
        }
        
        response1 = self.client.post(self.base_url, json=activity_data)
        assert response1.status_code == 201
        
        # Try to create second activity with same name
        activity_data["description"] = "Second activity with same name"
        response2 = self.client.post(self.base_url, json=activity_data)
        
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()
    
    def test_create_activity_validation_errors(self):
        """Test activity creation with validation errors."""
        # Missing required fields
        invalid_data = {
            "name": "Test",  # Too short
            "description": "",  # Empty
            "erpnext_module": "Accounts",
            "complexity_score": -1,  # Invalid
            "estimated_duration": 0  # Invalid
        }
        
        response = self.client.post(self.base_url, json=invalid_data)
        assert response.status_code == 422
        
        # Missing completely required fields
        minimal_data = {"name": "Test Activity"}
        response = self.client.post(self.base_url, json=minimal_data)
        assert response.status_code == 422
    
    def test_list_activities(self):
        """Test listing activities with pagination."""
        # Create test activities
        for i in range(5):
            activity_data = {
                "name": f"Test Activity {i}",
                "description": f"Test activity {i} for listing",
                "erpnext_module": "Accounts" if i % 2 == 0 else "Stock",
                "action_type": "create",
                "target_doctype": "Test DocType",
                "complexity_score": i + 1,
                "estimated_duration": 300
            }
            response = self.client.post(self.base_url, json=activity_data)
            assert response.status_code == 201
        
        # Test default listing
        response = self.client.get(self.base_url)
        assert response.status_code == 200
        
        data = response.json()
        assert "activities" in data
        assert "total" in data
        assert data["total"] >= 5
        assert len(data["activities"]) >= 5
    
    def test_list_activities_with_filters(self):
        """Test listing activities with various filters."""
        # Create activities with different attributes
        activities = [
            {"name": "Accounts Activity", "erpnext_module": "Accounts", "action_type": "create"},
            {"name": "Stock Activity", "erpnext_module": "Stock", "action_type": "update"},
            {"name": "Inactive Activity", "erpnext_module": "CRM", "is_active": False}
        ]
        
        for activity_data in activities:
            full_data = {
                "description": "Test activity",
                "target_doctype": "Test DocType",
                "complexity_score": 3,
                "estimated_duration": 300,
                **activity_data
            }
            response = self.client.post(self.base_url, json=full_data)
            assert response.status_code == 201
        
        # Test module filter
        response = self.client.get(f"{self.base_url}?erpnext_module=Accounts")
        assert response.status_code == 200
        data = response.json()
        for activity in data["activities"]:
            assert activity["erpnext_module"] == "Accounts"
        
        # Test action type filter
        response = self.client.get(f"{self.base_url}?action_type=create")
        assert response.status_code == 200
        data = response.json()
        for activity in data["activities"]:
            assert activity["action_type"] == "create"
        
        # Test active status filter
        response = self.client.get(f"{self.base_url}?is_active=false")
        assert response.status_code == 200
        data = response.json()
        for activity in data["activities"]:
            assert activity["is_active"] is False
    
    def test_get_activity_by_id(self):
        """Test retrieving activity by ID."""
        # Create activity
        activity_data = {
            "name": "Get By ID Test Activity",
            "description": "Activity for get by ID testing",
            "erpnext_module": "Accounts",
            "action_type": "read",
            "target_doctype": "Sales Invoice",
            "complexity_score": 4,
            "estimated_duration": 240
        }
        
        create_response = self.client.post(self.base_url, json=activity_data)
        assert create_response.status_code == 201
        
        created_activity = create_response.json()
        activity_id = created_activity["id"]
        
        # Get activity by ID
        response = self.client.get(f"{self.base_url}/{activity_id}")
        assert response.status_code == 200
        
        retrieved_activity = response.json()
        assert retrieved_activity["id"] == activity_id
        assert retrieved_activity["name"] == activity_data["name"]
        assert retrieved_activity["description"] == activity_data["description"]
    
    def test_get_activity_not_found(self):
        """Test retrieving non-existent activity."""
        non_existent_id = str(uuid.uuid4())
        response = self.client.get(f"{self.base_url}/{non_existent_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_activity(self):
        """Test updating activity."""
        # Create activity
        activity_data = {
            "name": "Update Test Activity",
            "description": "Original description",
            "erpnext_module": "Accounts",
            "action_type": "create",
            "target_doctype": "Sales Invoice",
            "complexity_score": 3,
            "estimated_duration": 300
        }
        
        create_response = self.client.post(self.base_url, json=activity_data)
        assert create_response.status_code == 201
        
        created_activity = create_response.json()
        activity_id = created_activity["id"]
        
        # Update activity
        update_data = {
            "description": "Updated description",
            "complexity_score": 5,
            "estimated_duration": 450,
            "is_active": False
        }
        
        response = self.client.put(f"{self.base_url}/{activity_id}", json=update_data)
        assert response.status_code == 200
        
        updated_activity = response.json()
        assert updated_activity["description"] == update_data["description"]
        assert updated_activity["complexity_score"] == update_data["complexity_score"]
        assert updated_activity["estimated_duration"] == update_data["estimated_duration"]
        assert updated_activity["is_active"] == update_data["is_active"]
        
        # Original fields should remain unchanged
        assert updated_activity["name"] == activity_data["name"]
        assert updated_activity["erpnext_module"] == activity_data["erpnext_module"]
    
    def test_update_activity_not_found(self):
        """Test updating non-existent activity."""
        non_existent_id = str(uuid.uuid4())
        update_data = {"description": "Updated description"}
        
        response = self.client.put(f"{self.base_url}/{non_existent_id}", json=update_data)
        assert response.status_code == 404
    
    def test_delete_activity(self):
        """Test deleting activity."""
        # Create activity
        activity_data = {
            "name": "Delete Test Activity",
            "description": "Activity to be deleted",
            "erpnext_module": "Stock",
            "action_type": "delete",
            "target_doctype": "Item",
            "complexity_score": 2,
            "estimated_duration": 120
        }
        
        create_response = self.client.post(self.base_url, json=activity_data)
        assert create_response.status_code == 201
        
        created_activity = create_response.json()
        activity_id = created_activity["id"]
        
        # Delete activity
        response = self.client.delete(f"{self.base_url}/{activity_id}")
        assert response.status_code == 204
        
        # Verify activity is deleted
        get_response = self.client.get(f"{self.base_url}/{activity_id}")
        assert get_response.status_code == 404
    
    def test_delete_activity_not_found(self):
        """Test deleting non-existent activity."""
        non_existent_id = str(uuid.uuid4())
        response = self.client.delete(f"{self.base_url}/{non_existent_id}")
        assert response.status_code == 404
    
    def test_search_activities(self):
        """Test activity search functionality."""
        # Create activities with searchable content
        activities = [
            {"name": "Customer Management Activity", "description": "Manage customer data"},
            {"name": "Invoice Processing", "description": "Process customer invoices"},
            {"name": "Stock Management", "description": "Manage inventory items"}
        ]
        
        for activity_data in activities:
            full_data = {
                "erpnext_module": "Accounts",
                "action_type": "create",
                "target_doctype": "Test DocType",
                "complexity_score": 3,
                "estimated_duration": 300,
                **activity_data
            }
            response = self.client.post(self.base_url, json=full_data)
            assert response.status_code == 201
        
        # Search for activities containing "customer"
        search_data = {"query": "customer", "page": 1, "per_page": 10}
        response = self.client.post(f"{self.base_url}/search", json=search_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert "total" in data
        
        # Should find activities with "customer" in name or description
        found_activities = data["activities"]
        assert len(found_activities) >= 2
        
        for activity in found_activities:
            text_to_search = f"{activity['name']} {activity['description']}".lower()
            assert "customer" in text_to_search
    
    def test_activity_statistics(self):
        """Test activity statistics endpoint."""
        response = self.client.get(f"{self.base_url}/statistics")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total" in stats
        assert "by_module" in stats
        assert "by_action_type" in stats
        assert "avg_complexity" in stats
        assert "avg_duration" in stats
        assert isinstance(stats["total"], int)
        assert isinstance(stats["by_module"], dict)
        assert isinstance(stats["by_action_type"], dict)
    
    def test_activity_validation(self):
        """Test activity validation endpoint."""
        # Create activity
        activity_data = {
            "name": "Validation Test Activity",
            "description": "Activity for validation testing",
            "erpnext_module": "Accounts",
            "action_type": "create",
            "target_doctype": "Sales Invoice",
            "complexity_score": 3,
            "estimated_duration": 300
        }
        
        create_response = self.client.post(self.base_url, json=activity_data)
        assert create_response.status_code == 201
        
        activity_id = create_response.json()["id"]
        
        # Test validation
        response = self.client.get(f"{self.base_url}/{activity_id}/validation")
        assert response.status_code == 200
        
        validation_result = response.json()
        assert "is_valid" in validation_result
        assert "validation_errors" in validation_result
        assert isinstance(validation_result["is_valid"], bool)
        assert isinstance(validation_result["validation_errors"], list)
    
    def test_find_similar_activities(self):
        """Test finding similar activities."""
        # Create reference activity
        reference_activity = {
            "name": "Reference Sales Activity",
            "description": "Create and manage sales invoices",
            "erpnext_module": "Accounts",
            "action_type": "create",
            "target_doctype": "Sales Invoice",
            "complexity_score": 4,
            "estimated_duration": 300
        }
        
        create_response = self.client.post(self.base_url, json=reference_activity)
        assert create_response.status_code == 201
        reference_id = create_response.json()["id"]
        
        # Create similar activities
        similar_activities = [
            {
                "name": "Purchase Invoice Activity",
                "description": "Create and manage purchase invoices",
                "erpnext_module": "Accounts",
                "action_type": "create",
                "target_doctype": "Purchase Invoice",
                "complexity_score": 4,
                "estimated_duration": 320
            },
            {
                "name": "Different Module Activity",
                "description": "Completely different activity",
                "erpnext_module": "Stock",
                "action_type": "update",
                "target_doctype": "Item",
                "complexity_score": 1,
                "estimated_duration": 60
            }
        ]
        
        for activity_data in similar_activities:
            response = self.client.post(self.base_url, json=activity_data)
            assert response.status_code == 201
        
        # Find similar activities
        response = self.client.get(
            f"{self.base_url}/{reference_id}/similar?limit=5&min_similarity=0.5"
        )
        assert response.status_code == 200
        
        similar_list = response.json()
        assert isinstance(similar_list, list)
    
    def test_bulk_operations(self):
        """Test bulk operations on activities."""
        # Create multiple activities
        activity_ids = []
        for i in range(3):
            activity_data = {
                "name": f"Bulk Test Activity {i}",
                "description": f"Activity {i} for bulk testing",
                "erpnext_module": "Accounts",
                "action_type": "create",
                "target_doctype": "Test DocType",
                "complexity_score": 3,
                "estimated_duration": 300
            }
            
            response = self.client.post(self.base_url, json=activity_data)
            assert response.status_code == 201
            activity_ids.append(response.json()["id"])
        
        # Test bulk deactivate
        bulk_data = {
            "operation": "deactivate",
            "activity_ids": activity_ids
        }
        
        response = self.client.post(f"{self.base_url}/bulk", json=bulk_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "processed" in result
        assert result["processed"] == len(activity_ids)
        
        # Verify activities are deactivated
        for activity_id in activity_ids:
            response = self.client.get(f"{self.base_url}/{activity_id}")
            assert response.status_code == 200
            assert response.json()["is_active"] is False


class TestPersonaActivityAPI:
    """Test suite for Persona-Activity relationship API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session, client: TestClient):
        """Set up test environment."""
        self.db = db_session
        self.client = client
        
        # Create test persona
        self.test_persona = PersonaModel(
            id=uuid.uuid4(),
            name="Test Persona",
            description="Test persona for relationship tests",
            erpnext_roles=["System Manager"],
            permissions=["read", "write"],
            experience_level="intermediate",
            business_context="Test context",
            is_active=True
        )
        self.db.add(self.test_persona)
        
        # Create test activity
        self.test_activity = ActivityModel(
            id=uuid.uuid4(),
            name="Test Activity",
            description="Test activity for relationship tests",
            erpnext_module="Accounts",
            action_type="create",
            target_doctype="Sales Invoice",
            complexity_score=3,
            estimated_duration=300,
            is_active=True
        )
        self.db.add(self.test_activity)
        self.db.commit()
    
    def test_link_persona_to_activity(self):
        """Test linking persona to activity."""
        link_data = {
            "priority": "high",
            "notes": "Important activity for this persona"
        }
        
        url = f"/api/v1/personas/{self.test_persona.id}/activities/{self.test_activity.id}"
        response = self.client.post(url, json=link_data)
        
        assert response.status_code == 201
        
        link_response = response.json()
        assert link_response["persona_id"] == str(self.test_persona.id)
        assert link_response["activity_id"] == str(self.test_activity.id)
        assert link_response["priority"] == "high"
        assert link_response["notes"] == "Important activity for this persona"
    
    def test_list_persona_activities(self):
        """Test listing activities for a persona."""
        # Create link first
        link = ActivityPersonaLinkModel(
            persona_id=self.test_persona.id,
            activity_id=self.test_activity.id,
            priority="medium",
            notes="Test link"
        )
        self.db.add(link)
        self.db.commit()
        
        url = f"/api/v1/personas/{self.test_persona.id}/activities"
        response = self.client.get(url)
        
        assert response.status_code == 200
        
        data = response.json()
        assert "activities" in data
        assert "total" in data
        assert data["total"] >= 1
        
        # Check if our test activity is in the list
        activity_ids = [activity["id"] for activity in data["activities"]]
        assert str(self.test_activity.id) in activity_ids
    
    def test_get_persona_activity_link(self):
        """Test getting specific persona-activity link."""
        # Create link first
        link = ActivityPersonaLinkModel(
            persona_id=self.test_persona.id,
            activity_id=self.test_activity.id,
            priority="high",
            notes="Direct link test"
        )
        self.db.add(link)
        self.db.commit()
        
        url = f"/api/v1/personas/{self.test_persona.id}/activities/{self.test_activity.id}"
        response = self.client.get(url)
        
        assert response.status_code == 200
        
        link_data = response.json()
        assert link_data["persona_id"] == str(self.test_persona.id)
        assert link_data["activity_id"] == str(self.test_activity.id)
        assert link_data["priority"] == "high"
        assert link_data["notes"] == "Direct link test"
    
    def test_delete_persona_activity_link(self):
        """Test removing persona-activity link."""
        # Create link first
        link = ActivityPersonaLinkModel(
            persona_id=self.test_persona.id,
            activity_id=self.test_activity.id,
            priority="medium"
        )
        self.db.add(link)
        self.db.commit()
        
        url = f"/api/v1/personas/{self.test_persona.id}/activities/{self.test_activity.id}"
        response = self.client.delete(url)
        
        assert response.status_code == 204
        
        # Verify link is removed
        get_response = self.client.get(url)
        assert get_response.status_code == 404
    
    def test_persona_activity_statistics(self):
        """Test getting persona activity statistics."""
        url = f"/api/v1/personas/{self.test_persona.id}/activities/statistics"
        response = self.client.get(url)
        
        assert response.status_code == 200
        
        data = response.json()
        assert "persona_id" in data
        assert "statistics" in data
        assert data["persona_id"] == str(self.test_persona.id)
    
    def test_activity_recommendations(self):
        """Test getting activity recommendations for persona."""
        url = f"/api/v1/personas/{self.test_persona.id}/activities/recommendations?limit=5"
        response = self.client.get(url)
        
        assert response.status_code == 200
        
        recommendations = response.json()
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5