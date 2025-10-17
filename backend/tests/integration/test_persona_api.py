"""Integration tests for persona API endpoints.

Tests the full integration of persona management functionality
including API endpoints, database operations, and business logic.
"""

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.application.dto.persona_schemas import PersonaResponse


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
            "permissions": "read:sales_order,write:sales_order",
            "is_active": True,
        }

    @pytest.fixture
    def sample_persona_response(self):
        """Sample persona response data."""
        persona_id = uuid.uuid4()
        return PersonaResponse(
            id=persona_id,
            name="Test Sales Manager",
            description="A test persona for sales operations",
            erpnext_roles="Sales Manager,Customer",
            permissions="read:sales_order,write:sales_order",
            is_active=True,
            created_at="2024-01-15T10:30:00Z",
            updated_at="2024-01-15T10:30:00Z",
            version=1,
            erpnext_roles_list=["Sales Manager", "Customer"],
            permissions_list=["read:sales_order", "write:sales_order"],
            effective_permissions_count=15,
        )

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_create_persona_success(
        self,
        mock_get_consultant,
        mock_get_db,
        client,
        mock_db_session,
        sample_persona_data,
        sample_persona_response,
    ):
        """Test successful persona creation."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        # Mock service response
        with patch(
            "src.api.personas.persona_routes.PersonaService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.create_persona = AsyncMock(
                return_value=sample_persona_response
            )

            # Make request
            response = client.post("/api/v1/personas/", json=sample_persona_data)

            # Assertions
            assert response.status_code == 201
            response_data = response.json()
            assert response_data["name"] == sample_persona_data["name"]
            assert response_data["description"] == sample_persona_data["description"]
            assert response_data["is_active"] == sample_persona_data["is_active"]
            assert "id" in response_data
            assert "created_at" in response_data
            assert "updated_at" in response_data

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_create_persona_validation_error(
        self, mock_get_consultant, mock_get_db, client, mock_db_session
    ):
        """Test persona creation with validation errors."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        # Invalid data (missing required fields)
        invalid_data = {
            "name": "",  # Empty name
            "description": "Test description"
            # Missing erpnext_roles
        }

        # Make request
        response = client.post("/api/v1/personas/", json=invalid_data)

        # Assertions
        assert response.status_code == 422  # Validation error
        response_data = response.json()
        assert "detail" in response_data

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_get_persona_success(
        self,
        mock_get_consultant,
        mock_get_db,
        client,
        mock_db_session,
        sample_persona_response,
    ):
        """Test successful persona retrieval."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        persona_id = sample_persona_response.id

        # Mock service response
        with patch(
            "src.api.personas.persona_routes.PersonaService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_persona = AsyncMock(return_value=sample_persona_response)

            # Make request
            response = client.get(f"/api/v1/personas/{persona_id}")

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["id"] == str(persona_id)
            assert response_data["name"] == sample_persona_response.name

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_get_persona_not_found(
        self, mock_get_consultant, mock_get_db, client, mock_db_session
    ):
        """Test persona retrieval with non-existent ID."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        non_existent_id = str(uuid.uuid4())

        # Mock service to raise not found error
        with patch(
            "src.api.personas.persona_routes.PersonaService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            from src.domain.personas.exceptions import PersonaNotFoundError

            mock_service.get_persona = AsyncMock(
                side_effect=PersonaNotFoundError(non_existent_id)
            )

            # Make request
            response = client.get(f"/api/v1/personas/{non_existent_id}")

            # Assertions
            assert response.status_code == 404
            response_data = response.json()
            assert "detail" in response_data
            assert non_existent_id in response_data["detail"]

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_list_personas_success(
        self,
        mock_get_consultant,
        mock_get_db,
        client,
        mock_db_session,
        sample_persona_response,
    ):
        """Test successful persona listing."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        # Mock service response
        from src.application.dto.persona_schemas import PersonaListResponse
        list_response = PersonaListResponse(
            items=[sample_persona_response],
            total=1,
            page=1,
            page_size=50,
            has_next=False,
            has_previous=False,
        )

        with patch(
            "src.api.personas.persona_routes.PersonaService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.list_personas = AsyncMock(return_value=list_response)

            # Make request
            response = client.get("/api/v1/personas/")

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert "items" in response_data
            assert "total" in response_data
            assert len(response_data["items"]) == 1
            assert response_data["total"] == 1

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_list_personas_with_filters(
        self, mock_get_consultant, mock_get_db, client, mock_db_session
    ):
        """Test persona listing with various filters."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        # Mock service response
        from src.application.dto.persona_schemas import PersonaListResponse
        list_response = PersonaListResponse(
            items=[],
            total=0,
            page=1,
            page_size=25,
            has_next=False,
            has_previous=False,
        )

        with patch(
            "src.api.personas.persona_routes.PersonaService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.list_personas = AsyncMock(return_value=list_response)

            # Make request with filters
            response = client.get(
                "/api/v1/personas/?limit=25&offset=0&search=sales&is_active=true&erpnext_role=Sales Manager"
            )

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["page_size"] == 25
            assert response_data["page"] == 1

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_update_persona_success(
        self,
        mock_get_consultant,
        mock_get_db,
        client,
        mock_db_session,
        sample_persona_response,
    ):
        """Test successful persona update."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        persona_id = sample_persona_response.id
        update_data = {
            "name": "Updated Sales Manager",
            "description": "Updated description",
            "is_active": False,
        }

        # Create expected response with updates
        updated_response = sample_persona_response.model_copy(update={
            **update_data,
            "updated_at": "2024-01-15T11:30:00Z",
            "version": 2
        })

        # Mock service response
        with patch(
            "src.api.personas.persona_routes.PersonaService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.update_persona = AsyncMock(return_value=updated_response)

            # Make request
            response = client.put(f"/api/v1/personas/{persona_id}", json=update_data)

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["name"] == update_data["name"]
            assert response_data["description"] == update_data["description"]
            assert response_data["is_active"] == update_data["is_active"]
            assert response_data["version"] == 2

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_delete_persona_success(
        self, mock_get_consultant, mock_get_db, client, mock_db_session
    ):
        """Test successful persona deletion."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        persona_id = str(uuid.uuid4())

        # Mock service response
        with patch(
            "src.api.personas.persona_routes.PersonaService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.delete_persona = AsyncMock(return_value=None)

            # Make request
            response = client.delete(f"/api/v1/personas/{persona_id}")

            # Assertions
            assert response.status_code == 204
            assert response.content == b""  # No content for successful deletion

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_validate_persona_data_success(
        self,
        mock_get_consultant,
        mock_get_db,
        client,
        mock_db_session,
        sample_persona_data,
    ):
        """Test successful persona data validation."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        # Mock service response
        validation_response = {
            "is_valid": True,
            "errors": [],
            "warnings": [
                "Consider adding Item Manager role for complete sales workflow"
            ],
            "suggestions": [],
        }

        with patch(
            "src.api.personas.persona_routes.PersonaService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.validate_persona_data = AsyncMock(
                return_value=validation_response
            )

            # Make request
            response = client.post("/api/v1/personas/validate", json=sample_persona_data)

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["is_valid"] is True
            assert len(response_data["warnings"]) == 1
            assert len(response_data["errors"]) == 0

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_get_persona_statistics_success(
        self, mock_get_consultant, mock_get_db, client, mock_db_session
    ):
        """Test successful persona statistics retrieval."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        # Mock service response
        stats_response = {
            "total_personas": 15,
            "active_personas": 12,
            "inactive_personas": 3,
            "roles_distribution": {
                "Sales Manager": 4,
                "Purchase Manager": 3,
                "Stock User": 2,
            },
            "permissions_distribution": {
                "read:sales": 5,
                "write:sales": 3,
                "read:purchase": 2,
            },
            "creation_trend": [
                {"month": "2024-01", "count": 5},
                {"month": "2024-02", "count": 10},
            ],
            "complexity_metrics": {
                "avg_roles_per_persona": 2.5,
                "avg_permissions_per_persona": 1.8,
                "most_complex_persona": "Sales Manager",
                "least_complex_persona": "Stock User",
            },
        }

        with patch(
            "src.api.personas.persona_routes.PersonaService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_persona_statistics = AsyncMock(return_value=stats_response)

            # Make request
            response = client.get("/api/v1/personas/statistics/overview")

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["total_personas"] == 15
            assert response_data["active_personas"] == 12
            assert response_data["inactive_personas"] == 3
            assert "roles_distribution" in response_data
            assert "permissions_distribution" in response_data
            assert "creation_trend" in response_data
            assert "complexity_metrics" in response_data

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_activate_persona_success(
        self,
        mock_get_consultant,
        mock_get_db,
        client,
        mock_db_session,
        sample_persona_response,
    ):
        """Test successful persona activation."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        persona_id = sample_persona_response.id

        # Create activated response
        activated_response = sample_persona_response.model_copy(update={
            "is_active": True,
            "updated_at": "2024-01-15T12:00:00Z"
        })

        # Mock service response
        with patch(
            "src.api.personas.persona_routes.PersonaService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.activate_persona = AsyncMock(return_value=activated_response)

            # Make request
            response = client.post(f"/api/v1/personas/{persona_id}/activate")

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["is_active"] is True

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_find_similar_personas_success(
        self,
        mock_get_consultant,
        mock_get_db,
        client,
        mock_db_session,
        sample_persona_response,
    ):
        """Test successful similar personas search."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_db.return_value = iter([mock_db_session])  # get_sync_db returns a generator

        persona_id = sample_persona_response.id

        # Mock similar personas response
        similar_response = [
            {
                "id": str(uuid.uuid4()),
                "name": "Senior Sales Manager",
                "description": "Senior sales manager with team leadership",
                "erpnext_roles_count": 3,
                "permissions_count": 5,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Sales Representative",
                "description": "Individual contributor in sales",
                "erpnext_roles_count": 2,
                "permissions_count": 3,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
            },
        ]

        # Mock service response
        with patch(
            "src.api.personas.persona_routes.PersonaService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.find_similar_personas = AsyncMock(
                return_value=similar_response
            )

            # Make request
            response = client.get(
                f"/api/v1/personas/{persona_id}/similar?similarity_threshold=0.7"
            )

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert len(response_data) == 2
            # Verify all returned personas have the expected fields
            for persona in response_data:
                assert "id" in persona
                assert "name" in persona
                assert "description" in persona
                assert "erpnext_roles_count" in persona
                assert "permissions_count" in persona
                assert "is_active" in persona
                assert "created_at" in persona

    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "healthy"
        assert "version" in response_data
        assert "timestamp" in response_data
        assert "database" in response_data
        assert "redis" in response_data


class TestPersonaAPIErrorHandling:
    """Test error handling in persona API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch("src.api.personas.persona_routes.get_persona_service")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_internal_server_error_handling(
        self, mock_get_consultant, mock_get_persona_service, client
    ):
        """Test handling of unexpected internal server errors."""
        # Setup mocks
        mock_get_consultant.return_value = uuid.uuid4()
        mock_get_persona_service.side_effect = Exception("Database connection failed")

        # Make request
        response = client.get("/api/v1/personas/")

        # Assertions
        assert response.status_code == 500
        response_data = response.json()
        assert "detail" in response_data

    @patch("src.infrastructure.database.get_sync_db")
    @patch("src.api.personas.persona_routes.get_current_consultant_id")
    def test_authentication_error_handling(
        self, mock_get_consultant, mock_get_db, client
    ):
        """Test handling of authentication errors."""
        # Setup mocks - simulate authentication failure
        mock_get_consultant.side_effect = Exception("Authentication failed")

        # Make request
        response = client.get("/api/v1/personas/")

        # Assertions - Should be handled by authentication middleware
        # The exact status code depends on authentication middleware implementation
        assert response.status_code in [401, 403, 500]

    def test_invalid_uuid_format(self, client):
        """Test handling of invalid UUID format in path parameters."""
        invalid_id = "not-a-valid-uuid"

        response = client.get(f"/api/v1/personas/{invalid_id}")

        # Should return validation error for invalid UUID format
        assert response.status_code == 422
        response_data = response.json()
        assert "detail" in response_data


if __name__ == "__main__":
    pytest.main([__file__])
