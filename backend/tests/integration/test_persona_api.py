"""Integration tests for persona API endpoints.

Tests the full integration of persona management functionality
including API endpoints, database operations, and business logic.
"""

import pytest
import asyncio
import uuid
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.infrastructure.database.config import get_database_session
from src.infrastructure.database.models.persona_model import PersonaModel
from src.domain.personas.persona import Persona
from src.application.services.persona_service import PersonaService


class TestPersonaAPIIntegration:
    """Integration tests for persona API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = Mock(spec=Session)
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        return session
    
    @pytest.fixture
    def sample_persona_data(self):
        """Sample persona data for testing."""
        return {
            "name": "Test Sales Manager",
            "description": "A test persona for sales operations",
            "erpnext_roles": "Sales Manager,Customer",
            "permissions": "read_sales_order,write_sales_order",
            "is_active": True
        }
    
    @pytest.fixture
    def sample_persona_response(self):
        """Sample persona response data."""
        return {
            "id": str(uuid.uuid4()),
            "name": "Test Sales Manager",
            "description": "A test persona for sales operations",
            "erpnext_roles": "Sales Manager,Customer",
            "permissions": "read_sales_order,write_sales_order",
            "is_active": True,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "version": 1,
            "erpnext_roles_list": ["Sales Manager", "Customer"],
            "permissions_list": ["read_sales_order", "write_sales_order"],
            "effective_permissions_count": 15
        }
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_create_persona_success(self, mock_get_consultant, mock_get_db, 
                                  client, mock_db_session, sample_persona_data, sample_persona_response):
        """Test successful persona creation."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        # Mock service response
        with patch('src.api.personas.persona_routes.PersonaService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.create_persona = AsyncMock(return_value=sample_persona_response)
            
            # Make request
            response = client.post("/personas/", json=sample_persona_data)
            
            # Assertions
            assert response.status_code == 201
            response_data = response.json()
            assert response_data["name"] == sample_persona_data["name"]
            assert response_data["description"] == sample_persona_data["description"]
            assert response_data["is_active"] == sample_persona_data["is_active"]
            assert "id" in response_data
            assert "created_at" in response_data
            assert "updated_at" in response_data
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_create_persona_validation_error(self, mock_get_consultant, mock_get_db, 
                                           client, mock_db_session):
        """Test persona creation with validation errors."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        # Invalid data (missing required fields)
        invalid_data = {
            "name": "",  # Empty name
            "description": "Test description"
            # Missing erpnext_roles
        }
        
        # Make request
        response = client.post("/personas/", json=invalid_data)
        
        # Assertions
        assert response.status_code == 422  # Validation error
        response_data = response.json()
        assert "detail" in response_data
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_get_persona_success(self, mock_get_consultant, mock_get_db, 
                                client, mock_db_session, sample_persona_response):
        """Test successful persona retrieval."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        persona_id = sample_persona_response["id"]
        
        # Mock service response
        with patch('src.api.personas.persona_routes.PersonaService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_persona = AsyncMock(return_value=sample_persona_response)
            
            # Make request
            response = client.get(f"/personas/{persona_id}")
            
            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["id"] == persona_id
            assert response_data["name"] == sample_persona_response["name"]
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_get_persona_not_found(self, mock_get_consultant, mock_get_db, 
                                  client, mock_db_session):
        """Test persona retrieval with non-existent ID."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        non_existent_id = str(uuid.uuid4())
        
        # Mock service to raise not found error
        with patch('src.api.personas.persona_routes.PersonaService') as mock_service_class:
            mock_service = mock_service_class.return_value
            from src.domain.personas.exceptions import PersonaNotFoundError
            mock_service.get_persona = AsyncMock(side_effect=PersonaNotFoundError(non_existent_id))
            
            # Make request
            response = client.get(f"/personas/{non_existent_id}")
            
            # Assertions
            assert response.status_code == 404
            response_data = response.json()
            assert "detail" in response_data
            assert non_existent_id in response_data["detail"]
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_list_personas_success(self, mock_get_consultant, mock_get_db, 
                                  client, mock_db_session, sample_persona_response):
        """Test successful persona listing."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        # Mock service response
        list_response = {
            "personas": [sample_persona_response],
            "total": 1,
            "limit": 50,
            "offset": 0,
            "has_more": False
        }
        
        with patch('src.api.personas.persona_routes.PersonaService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.list_personas = AsyncMock(return_value=list_response)
            
            # Make request
            response = client.get("/personas/")
            
            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert "personas" in response_data
            assert "total" in response_data
            assert len(response_data["personas"]) == 1
            assert response_data["total"] == 1
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_list_personas_with_filters(self, mock_get_consultant, mock_get_db, 
                                       client, mock_db_session):
        """Test persona listing with various filters."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        # Mock service response
        list_response = {
            "personas": [],
            "total": 0,
            "limit": 25,
            "offset": 0,
            "has_more": False
        }
        
        with patch('src.api.personas.persona_routes.PersonaService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.list_personas = AsyncMock(return_value=list_response)
            
            # Make request with filters
            response = client.get("/personas/?limit=25&offset=0&search=sales&is_active=true&erpnext_role=Sales Manager")
            
            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["limit"] == 25
            assert response_data["offset"] == 0
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_update_persona_success(self, mock_get_consultant, mock_get_db, 
                                   client, mock_db_session, sample_persona_response):
        """Test successful persona update."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        persona_id = sample_persona_response["id"]
        update_data = {
            "name": "Updated Sales Manager",
            "description": "Updated description",
            "is_active": False
        }
        
        # Create expected response with updates
        updated_response = sample_persona_response.copy()
        updated_response.update(update_data)
        updated_response["updated_at"] = "2024-01-15T11:30:00Z"
        updated_response["version"] = 2
        
        # Mock service response
        with patch('src.api.personas.persona_routes.PersonaService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.update_persona = AsyncMock(return_value=updated_response)
            
            # Make request
            response = client.put(f"/personas/{persona_id}", json=update_data)
            
            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["name"] == update_data["name"]
            assert response_data["description"] == update_data["description"]
            assert response_data["is_active"] == update_data["is_active"]
            assert response_data["version"] == 2
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_delete_persona_success(self, mock_get_consultant, mock_get_db, 
                                   client, mock_db_session):
        """Test successful persona deletion."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        persona_id = str(uuid.uuid4())
        
        # Mock service response
        with patch('src.api.personas.persona_routes.PersonaService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.delete_persona = AsyncMock(return_value=None)
            
            # Make request
            response = client.delete(f"/personas/{persona_id}")
            
            # Assertions
            assert response.status_code == 204
            assert response.content == b""  # No content for successful deletion
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_validate_persona_data_success(self, mock_get_consultant, mock_get_db, 
                                          client, mock_db_session, sample_persona_data):
        """Test successful persona data validation."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        # Mock service response
        validation_response = {
            "is_valid": True,
            "errors": [],
            "warnings": [
                {
                    "field": "erpnext_roles",
                    "message": "Consider adding Item Manager role for complete sales workflow",
                    "code": "role_suggestion"
                }
            ],
            "suggestions": []
        }
        
        with patch('src.api.personas.persona_routes.PersonaService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.validate_persona_data = AsyncMock(return_value=validation_response)
            
            # Make request
            response = client.post("/personas/validate", json=sample_persona_data)
            
            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["is_valid"] is True
            assert len(response_data["warnings"]) == 1
            assert len(response_data["errors"]) == 0
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_get_persona_statistics_success(self, mock_get_consultant, mock_get_db, 
                                           client, mock_db_session):
        """Test successful persona statistics retrieval."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        # Mock service response
        stats_response = {
            "total_personas": 15,
            "active_personas": 12,
            "inactive_personas": 3,
            "total_activities": 47,
            "personas_by_module": {
                "Sales": 5,
                "Purchase": 3,
                "Stock": 4,
                "Accounts": 2
            },
            "most_used_roles": [
                {"role": "Sales Manager", "count": 4},
                {"role": "Purchase Manager", "count": 3}
            ]
        }
        
        with patch('src.api.personas.persona_routes.PersonaService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_persona_statistics = AsyncMock(return_value=stats_response)
            
            # Make request
            response = client.get("/personas/statistics/overview")
            
            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["total_personas"] == 15
            assert response_data["active_personas"] == 12
            assert response_data["inactive_personas"] == 3
            assert "personas_by_module" in response_data
            assert "most_used_roles" in response_data
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_activate_persona_success(self, mock_get_consultant, mock_get_db, 
                                     client, mock_db_session, sample_persona_response):
        """Test successful persona activation."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        persona_id = sample_persona_response["id"]
        
        # Create activated response
        activated_response = sample_persona_response.copy()
        activated_response["is_active"] = True
        activated_response["updated_at"] = "2024-01-15T12:00:00Z"
        
        # Mock service response
        with patch('src.api.personas.persona_routes.PersonaService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.activate_persona = AsyncMock(return_value=activated_response)
            
            # Make request
            response = client.post(f"/personas/{persona_id}/activate")
            
            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["is_active"] is True
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_find_similar_personas_success(self, mock_get_consultant, mock_get_db, 
                                          client, mock_db_session, sample_persona_response):
        """Test successful similar personas search."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = mock_db_session
        
        persona_id = sample_persona_response["id"]
        
        # Mock similar personas response
        similar_response = [
            {
                "id": str(uuid.uuid4()),
                "name": "Senior Sales Manager",
                "description": "Senior sales manager with team leadership",
                "similarity_score": 0.85,
                "erpnext_roles_count": 3,
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Sales Representative",
                "description": "Individual contributor in sales",
                "similarity_score": 0.72,
                "erpnext_roles_count": 2,
                "is_active": True
            }
        ]
        
        # Mock service response
        with patch('src.api.personas.persona_routes.PersonaService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.find_similar_personas = AsyncMock(return_value=similar_response)
            
            # Make request
            response = client.get(f"/personas/{persona_id}/similar?similarity_threshold=0.7")
            
            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert len(response_data) == 2
            assert all(p["similarity_score"] >= 0.7 for p in response_data)
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/personas/health")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "healthy"
        assert response_data["service"] == "persona-api"
        assert "version" in response_data
        assert "timestamp" in response_data


class TestPersonaAPIErrorHandling:
    """Test error handling in persona API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_internal_server_error_handling(self, mock_get_consultant, mock_get_db, client):
        """Test handling of unexpected internal server errors."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.side_effect = Exception("Database connection failed")
        
        # Make request
        response = client.get("/personas/")
        
        # Assertions
        assert response.status_code == 500
        response_data = response.json()
        assert "detail" in response_data
    
    @patch('src.api.personas.persona_routes.get_database_session')
    @patch('src.api.personas.persona_routes.get_current_consultant_id')
    def test_authentication_error_handling(self, mock_get_consultant, mock_get_db, client):
        """Test handling of authentication errors."""
        # Setup mocks - simulate authentication failure
        mock_get_consultant.side_effect = Exception("Authentication failed")
        
        # Make request
        response = client.get("/personas/")
        
        # Assertions - Should be handled by authentication middleware
        # The exact status code depends on authentication middleware implementation
        assert response.status_code in [401, 403, 500]
    
    def test_invalid_uuid_format(self, client):
        """Test handling of invalid UUID format in path parameters."""
        invalid_id = "not-a-valid-uuid"
        
        response = client.get(f"/personas/{invalid_id}")
        
        # Should return validation error for invalid UUID format
        assert response.status_code == 422
        response_data = response.json()
        assert "detail" in response_data


if __name__ == "__main__":
    pytest.main([__file__])