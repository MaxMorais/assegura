"""Integration tests for activity management system.

This module provides comprehensive integration tests for the activity domain,
testing the complete flow from API endpoints through application services
to repository implementations.
"""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from src.application.dto.activity_schemas import (
    ActivityCreateRequestDTO,
    ActivityResponseDTO,
    ActivityUpdateRequestDTO,
    ActivityFilterDTO,
)
from src.domain.activities.exceptions import ActivityNotFoundError
from src.application.services.activity_service import ActivityApplicationService
from src.infrastructure.database.repositories.activity_repository import (
    SQLAlchemyActivityPersonaLinkRepository,
    SQLAlchemyActivityRepository,
)
from src.infrastructure.database.repositories.persona_repository import (
    SQLAlchemyPersonaRepository,
)


class TestActivityIntegration:
    """Integration tests for activity management system."""

    @pytest.fixture
    def sample_activity_data(self) -> dict[str, Any]:
        """Sample activity data for testing."""
        return {
            "name": "Test Create Sales Invoice",
            "description": "Create a new sales invoice for customer with items and pricing",
            "erpnext_module": "Accounts",
            "action_type": "create",
            "target_doctype": "Sales Invoice",
            "required_fields": ["customer", "items"],
            "validation_rules": {"customer": {"required": True}},
            "success_criteria": ["Document created", "Status is Draft"],
            "complexity_score": 3,
            "estimated_duration": 120,
            "prerequisites": ["Customer exists", "Items available"],
            "postconditions": ["Invoice saved", "Account updated"],
            "test_data_requirements": {"customer": "test_customer"},
            "tags": ["automation", "sales"],
            "is_active": True,
            "version": "1.0.0",
        }

    @pytest.fixture
    def activity_repository(self, db_session: Session) -> SQLAlchemyActivityRepository:
        """Activity repository fixture."""
        return SQLAlchemyActivityRepository(db_session)

    @pytest.fixture
    def link_repository(
        self, db_session: Session
    ) -> SQLAlchemyActivityPersonaLinkRepository:
        """Activity-persona link repository fixture."""
        return SQLAlchemyActivityPersonaLinkRepository(db_session)

    @pytest.fixture
    def persona_repository(self, db_session: Session) -> SQLAlchemyPersonaRepository:
        """Persona repository fixture."""
        return SQLAlchemyPersonaRepository(db_session)

    @pytest.fixture
    def activity_service(
        self,
        activity_repository: SQLAlchemyActivityRepository,
        persona_repository: SQLAlchemyPersonaRepository,
        link_repository: SQLAlchemyActivityPersonaLinkRepository,
    ) -> ActivityApplicationService:
        """Activity application service fixture."""
        return ActivityApplicationService(activity_repository, persona_repository, link_repository)

    async def test_create_activity_flow(
        self,
        activity_service: ActivityApplicationService,
        sample_activity_data: dict[str, Any],
    ):
        """Test complete activity creation flow."""

        # Create activity through application service
        create_request = ActivityCreateRequestDTO(**sample_activity_data)
        created_activity = await activity_service.create_activity(create_request)

        # Verify activity was created
        assert created_activity.name == sample_activity_data["name"]
        assert created_activity.erpnext_module == sample_activity_data["erpnext_module"]
        assert created_activity.action_type == sample_activity_data["action_type"]
        assert (
            created_activity.complexity_score
            == sample_activity_data["complexity_score"]
        )
        assert created_activity.is_active is True
        assert created_activity.id is not None
        assert created_activity.created_at is not None
        assert created_activity.updated_at is not None

        # Verify activity can be retrieved
        retrieved_activity = await activity_service.get_activity_by_id(
            created_activity.id
        )
        assert retrieved_activity is not None
        assert retrieved_activity.name == created_activity.name
        assert retrieved_activity.description == created_activity.description

    async def test_activity_crud_operations(
        self,
        activity_service: ActivityApplicationService,
        sample_activity_data: dict[str, Any],
    ):
        """Test complete CRUD operations for activities."""

        # Create
        create_request = ActivityCreateRequestDTO(**sample_activity_data)
        created_activity = await activity_service.create_activity(create_request)
        activity_id = created_activity.id

        # Read
        retrieved_activity = await activity_service.get_activity_by_id(activity_id)
        assert retrieved_activity is not None
        assert retrieved_activity.name == sample_activity_data["name"]

        # Update
        update_data = {
            "name": "Updated Test Activity",
            "description": "Updated description",
            "complexity_score": 4,
            "estimated_duration": 180,
            "tags": ["updated", "test"],
            "is_active": False,
        }
        update_request = ActivityUpdateRequestDTO(**update_data)
        updated_activity = await activity_service.update_activity(
            activity_id, update_request
        )

        assert updated_activity.name == update_data["name"]
        assert updated_activity.description == update_data["description"]
        assert updated_activity.complexity_score == update_data["complexity_score"]
        assert updated_activity.estimated_duration == update_data["estimated_duration"]
        assert updated_activity.tags == update_data["tags"]
        assert updated_activity.is_active == update_data["is_active"]
        assert updated_activity.updated_at > created_activity.updated_at

        # Delete
        await activity_service.delete_activity(activity_id)

        # Verify deletion
        with pytest.raises(ActivityNotFoundError):
            await activity_service.get_activity_by_id(activity_id)

    async def test_activity_filtering_and_search(
        self,
        activity_service: ActivityApplicationService,
        sample_activity_data: dict[str, Any],
    ):
        """Test activity filtering and search functionality."""

        # Create multiple test activities
        activities_data = [
            {
                **sample_activity_data,
                "name": "Sales Invoice Create",
                "erpnext_module": "Accounts",
                "action_type": "create",
                "complexity_score": 3,
            },
            {
                **sample_activity_data,
                "name": "Purchase Order Update",
                "erpnext_module": "Buying",
                "action_type": "update",
                "complexity_score": 2,
            },
            {
                **sample_activity_data,
                "name": "Customer List View",
                "erpnext_module": "CRM",
                "action_type": "list",
                "complexity_score": 1,
            },
            {
                **sample_activity_data,
                "name": "Invoice Delete",
                "erpnext_module": "Accounts",
                "action_type": "delete",
                "complexity_score": 4,
                "is_active": False,
            },
        ]

        created_activities = []
        for data in activities_data:
            request = ActivityCreateRequestDTO(**data)
            activity = await activity_service.create_activity(request)
            created_activities.append(activity)

        # Test module filter
        accounts_filter = ActivityFilterDTO(erpnext_module="Accounts")
        accounts_result = await activity_service.list_activities(
            accounts_filter, page=1, per_page=10
        )
        assert accounts_result.total == 2
        assert all(a.erpnext_module == "Accounts" for a in accounts_result.items)

        # Test action type filter
        create_filter = ActivityFilterDTO(action_type="create")
        create_result = await activity_service.list_activities(
            create_filter, page=1, per_page=10
        )
        assert create_result.total == 1
        assert create_result.items[0].action_type == "create"

        # Test complexity filter
        low_complexity_filter = ActivityFilterDTO(complexity_score=1)
        low_complexity_result = await activity_service.list_activities(
            low_complexity_filter, page=1, per_page=10
        )
        assert low_complexity_result.total == 1
        assert low_complexity_result.items[0].complexity_score == 1

        # Test active status filter
        active_filter = ActivityFilterDTO(is_active=True)
        active_result = await activity_service.list_activities(
            active_filter, page=1, per_page=10
        )
        assert active_result.total == 3
        assert all(a.is_active for a in active_result.items)

        # Test search
        search_filter = ActivityFilterDTO(search="invoice")
        search_result = await activity_service.list_activities(
            search_filter, page=1, per_page=10
        )
        assert search_result.total >= 2  # Should find activities with "invoice" in name

        # Test combined filters
        combined_filter = ActivityFilterDTO(
            erpnext_module="Accounts", is_active=True
        )
        combined_result = await activity_service.list_activities(
            combined_filter, page=1, per_page=10
        )
        assert combined_result.total == 1
        assert combined_result.items[0].erpnext_module == "Accounts"
        assert combined_result.items[0].is_active is True

    async def test_activity_bulk_operations(
        self,
        activity_service: ActivityApplicationService,
        sample_activity_data: dict[str, Any],
    ):
        """Test bulk operations on activities."""

        # Create multiple activities
        activity_ids = []
        for i in range(5):
            data = {**sample_activity_data, "name": f"Bulk Test Activity {i+1}"}
            request = ActivityCreateRequestDTO(**data)
            activity = await activity_service.create_activity(request)
            activity_ids.append(activity.id)

        # Test bulk status update
        updated_count = await activity_service.bulk_update_activity_status(
            activity_ids[:3], False
        )
        assert updated_count == 3

        # Verify status updates
        for activity_id in activity_ids[:3]:
            activity = await activity_service.get_activity_by_id(activity_id)
            assert activity.is_active is False

        for activity_id in activity_ids[3:]:
            activity = await activity_service.get_activity_by_id(activity_id)
            assert activity.is_active is True

        # Test bulk delete
        deleted_count = await activity_service.bulk_delete_activities(activity_ids[2:])
        assert deleted_count == 3

        # Verify deletions
        for activity_id in activity_ids[2:]:
            activity = await activity_service.get_activity_by_id(activity_id)
            assert activity is None

        # Verify remaining activities
        for activity_id in activity_ids[:2]:
            activity = await activity_service.get_activity_by_id(activity_id)
            assert activity is not None

    async def test_activity_statistics(
        self,
        activity_service: ActivityApplicationService,
        sample_activity_data: dict[str, Any],
    ):
        """Test activity statistics calculation."""

        # Create test activities with different characteristics
        activities_data = [
            {
                **sample_activity_data,
                "name": "Stats Test 1",
                "erpnext_module": "Accounts",
                "action_type": "create",
                "complexity_score": 1,
                "estimated_duration": 60,
            },
            {
                **sample_activity_data,
                "name": "Stats Test 2",
                "erpnext_module": "Accounts",
                "action_type": "update",
                "complexity_score": 2,
                "estimated_duration": 90,
            },
            {
                **sample_activity_data,
                "name": "Stats Test 3",
                "erpnext_module": "Stock",
                "action_type": "create",
                "complexity_score": 3,
                "estimated_duration": 120,
                "is_active": False,
            },
            {
                **sample_activity_data,
                "name": "Stats Test 4",
                "erpnext_module": "Stock",
                "action_type": "delete",
                "complexity_score": 4,
                "estimated_duration": 150,
            },
        ]

        for data in activities_data:
            request = ActivityCreateRequestDTO(**data)
            await activity_service.create_activity(request)

        # Get statistics
        stats = await activity_service.get_activity_statistics()

        # Verify basic counts
        assert stats["total"] >= 4
        assert stats["active"] >= 3
        assert stats["inactive"] >= 1

        # Verify module distribution
        assert "Accounts" in stats["by_module"]
        assert "Stock" in stats["by_module"]
        assert stats["by_module"]["Accounts"] >= 2
        assert stats["by_module"]["Stock"] >= 2

        # Verify action type distribution
        assert "create" in stats["by_action_type"]
        assert "update" in stats["by_action_type"]
        assert "delete" in stats["by_action_type"]

        # Verify complexity distribution
        assert stats["by_complexity"][1] >= 1
        assert stats["by_complexity"][2] >= 1
        assert stats["by_complexity"][3] >= 1
        assert stats["by_complexity"][4] >= 1

        # Verify duration calculations
        assert stats["avg_duration"] > 0
        assert stats["total_duration"] > 0

    async def test_activity_validation_and_business_rules(
        self, activity_service: ActivityApplicationService
    ):
        """Test activity validation and business rule enforcement."""

        # Test duplicate name validation
        activity_data = {
            "name": "Duplicate Test Activity",
            "description": "Test activity for duplicate validation",
            "erpnext_module": "Accounts",
            "action_type": "create",
            "target_doctype": "Sales Invoice",
            "complexity_score": 3,
            "estimated_duration": 120,
            "required_fields": [],
            "validation_rules": {},
            "success_criteria": [],
            "prerequisites": [],
            "postconditions": [],
            "test_data_requirements": {},
            "tags": [],
            "is_active": True,
            "version": "1.0.0",
        }

        # Create first activity
        first_request = ActivityCreateRequestDTO(**activity_data)
        first_activity = await activity_service.create_activity(first_request)

        # Try to create duplicate
        with pytest.raises(Exception):  # Should raise ActivityAlreadyExistsError
            second_request = ActivityCreateRequestDTO(**activity_data)
            await activity_service.create_activity(second_request)

        # Test invalid complexity score
        invalid_data = {
            **activity_data,
            "name": "Invalid Complexity",
            "complexity_score": 6,
        }
        with pytest.raises(Exception):  # Should raise ValidationError
            invalid_request = ActivityCreateRequestDTO(**invalid_data)
            await activity_service.create_activity(invalid_request)

        # Test invalid duration
        invalid_data = {
            **activity_data,
            "name": "Invalid Duration",
            "estimated_duration": 0,
        }
        with pytest.raises(Exception):  # Should raise ValidationError
            invalid_request = ActivityCreateRequestDTO(**invalid_data)
            await activity_service.create_activity(invalid_request)

        # Test empty name
        invalid_data = {**activity_data, "name": ""}
        with pytest.raises(Exception):  # Should raise ValidationError
            invalid_request = ActivityCreateRequestDTO(**invalid_data)
            await activity_service.create_activity(invalid_request)

    async def test_activity_persona_relationships(
        self,
        activity_service: ActivityApplicationService,
        sample_activity_data: dict[str, Any],
    ):
        """Test activity-persona relationship management."""

        # Create test activity
        activity_request = ActivityCreateRequestDTO(**sample_activity_data)
        activity = await activity_service.create_activity(activity_request)

        # Create mock persona IDs for testing
        persona_id_1 = uuid.uuid4()
        persona_id_2 = uuid.uuid4()

        # Create activity-persona links
        from src.application.dto.activity_schemas import (
            ActivityPersonaLinkCreateRequest,
        )

        link1_request = ActivityPersonaLinkCreateRequest(
            persona_id=persona_id_1,
            activity_id=activity.id,
            priority="high",
            notes="Primary persona for this activity",
            is_primary=True,
            execution_order=1,
        )
        link1 = await activity_service.create_activity_persona_link(link1_request)

        link2_request = ActivityPersonaLinkCreateRequest(
            persona_id=persona_id_2,
            activity_id=activity.id,
            priority="medium",
            notes="Secondary persona",
            is_primary=False,
            execution_order=2,
        )
        link2 = await activity_service.create_activity_persona_link(link2_request)

        # Verify links were created
        activity_personas = await activity_service.get_activity_personas(activity.id)
        assert len(activity_personas) == 2

        # Verify link properties
        high_priority_link = next(
            (l for l in activity_personas if l.priority == "high"), None
        )
        assert high_priority_link is not None
        assert high_priority_link.is_primary is True
        assert high_priority_link.execution_order == 1

        # Test duplicate link prevention
        with pytest.raises(
            Exception
        ):  # Should raise ActivityPersonaLinkAlreadyExistsError
            duplicate_request = ActivityPersonaLinkCreateRequest(
                persona_id=persona_id_1, activity_id=activity.id, priority="low"
            )
            await activity_service.create_activity_persona_link(duplicate_request)

        # Test link deletion
        await activity_service.delete_activity_persona_link(persona_id_1, activity.id)

        # Verify deletion
        remaining_personas = await activity_service.get_activity_personas(activity.id)
        assert len(remaining_personas) == 1
        assert remaining_personas[0].persona_id == persona_id_2


class TestActivityAPIIntegration:
    """Integration tests for activity API endpoints."""

    @pytest.fixture
    def sample_activity_data(self) -> dict[str, Any]:
        """Sample activity data for API testing."""
        return {
            "name": "API Test Create Customer",
            "description": "Create a new customer via API integration test",
            "erpnext_module": "CRM",
            "action_type": "create",
            "target_doctype": "Customer",
            "required_fields": ["customer_name", "customer_type"],
            "validation_rules": {"customer_name": {"required": True, "min_length": 3}},
            "success_criteria": [
                "Customer created successfully",
                "Customer ID generated",
            ],
            "complexity_score": 2,
            "estimated_duration": 90,
            "prerequisites": ["Customer group configured"],
            "postconditions": ["Customer saved in database"],
            "test_data_requirements": {"customer_type": "Individual"},
            "tags": ["api", "integration"],
            "is_active": True,
            "version": "1.0.0",
        }

    async def test_create_activity_api(
        self, async_client: AsyncClient, sample_activity_data: dict[str, Any]
    ):
        """Test activity creation via API."""

        response = await async_client.post(
            "/api/v1/activities/", json=sample_activity_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_activity_data["name"]
        assert data["erpnext_module"] == sample_activity_data["erpnext_module"]
        assert data["action_type"] == sample_activity_data["action_type"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        return data

    async def test_get_activity_api(
        self, async_client: AsyncClient, sample_activity_data: dict[str, Any]
    ):
        """Test activity retrieval via API."""

        # Create activity first with unique name
        activity_data = {**sample_activity_data, "name": "Test Get Activity API"}
        create_response = await async_client.post(
            "/api/v1/activities/", json=activity_data
        )
        created_activity = create_response.json()
        activity_id = created_activity["id"]

        # Get activity
        get_response = await async_client.get(f"/api/v1/activities/{activity_id}")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == activity_id
        assert data["name"] == sample_activity_data["name"]
        assert data["description"] == sample_activity_data["description"]

    async def test_list_activities_api(
        self, async_client: AsyncClient, sample_activity_data: dict[str, Any]
    ):
        """Test activity listing with filters via API."""

        # Create multiple activities
        activities_data = [
            {
                **sample_activity_data,
                "name": "API List Test 1",
                "erpnext_module": "CRM",
            },
            {
                **sample_activity_data,
                "name": "API List Test 2",
                "erpnext_module": "Accounts",
            },
            {
                **sample_activity_data,
                "name": "API List Test 3",
                "erpnext_module": "CRM",
                "action_type": "update",
            },
        ]

        for data in activities_data:
            await async_client.post("/api/v1/activities/", json=data)

        # Test basic listing
        response = await async_client.get("/api/v1/activities/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert data["total"] >= 3

        # Test filtering by module
        response = await async_client.get("/api/v1/activities/?erpnext_module=CRM")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert all(
            activity["erpnext_module"] == "CRM" for activity in data["items"]
        )

        # Test search
        response = await async_client.get("/api/v1/activities/?search=API List")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    async def test_update_activity_api(
        self, async_client: AsyncClient, sample_activity_data: dict[str, Any]
    ):
        """Test activity update via API."""

        # Create activity with unique name
        activity_data = {**sample_activity_data, "name": "Test Update Activity API"}
        create_response = await async_client.post(
            "/api/v1/activities/", json=activity_data
        )
        created_activity = create_response.json()
        activity_id = created_activity["id"]

        # Update activity
        update_data = {
            "name": "Updated API Test Activity",
            "description": "Updated description via API",
            "complexity_score": 4,
            "is_active": False,
        }

        update_response = await async_client.put(
            f"/api/v1/activities/{activity_id}", json=update_data
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["complexity_score"] == update_data["complexity_score"]
        assert data["is_active"] == update_data["is_active"]
        assert data["updated_at"] > created_activity["updated_at"]

    async def test_delete_activity_api(
        self, async_client: AsyncClient, sample_activity_data: dict[str, Any]
    ):
        """Test activity deletion via API."""

        # Create activity with unique name
        activity_data = {**sample_activity_data, "name": "Test Delete Activity API"}
        create_response = await async_client.post(
            "/api/v1/activities/", json=activity_data
        )
        created_activity = create_response.json()
        activity_id = created_activity["id"]

        # Delete activity
        delete_response = await async_client.delete(f"/api/v1/activities/{activity_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        get_response = await async_client.get(f"/api/v1/activities/{activity_id}")
        assert get_response.status_code == 404

    async def test_bulk_operations_api(
        self, async_client: AsyncClient, sample_activity_data: dict[str, Any]
    ):
        """Test bulk operations via API."""

        # Create multiple activities
        activity_ids = []
        for i in range(3):
            data = {**sample_activity_data, "name": f"Bulk API Test {i+1}"}
            response = await async_client.post("/api/v1/activities/", json=data)
            activity_ids.append(response.json()["id"])

        # Test bulk status update
        bulk_update_data = {"activity_ids": activity_ids, "action": "deactivate"}
        response = await async_client.post(
            "/api/v1/activities/bulk/update-status", json=bulk_update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 3

        # Verify updates
        for activity_id in activity_ids:
            get_response = await async_client.get(f"/api/v1/activities/{activity_id}")
            assert get_response.json()["is_active"] is False

        # Test bulk delete
        delete_response = await async_client.request(
            "DELETE", "/api/v1/activities/bulk", json=activity_ids
        )
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["deleted_count"] == 3

        # Verify deletions
        for activity_id in activity_ids:
            get_response = await async_client.get(f"/api/v1/activities/{activity_id}")
            assert get_response.status_code == 404

    async def test_activity_statistics_api(self, async_client: AsyncClient):
        """Test activity statistics endpoint."""

        response = await async_client.get("/api/v1/activities/statistics")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "total" in data
        assert "active" in data
        assert "inactive" in data
        assert "by_module" in data
        assert "by_action_type" in data
        assert "complexity_distribution" in data
        assert "avg_duration" in data
        assert "total_duration" in data

        # Verify data types
        assert isinstance(data["total"], int)
        assert isinstance(data["active"], int)
        assert isinstance(data["inactive"], int)
        assert isinstance(data["by_module"], dict)
        assert isinstance(data["by_action_type"], dict)
        assert isinstance(data["by_complexity"], dict)
        assert isinstance(data["avg_duration"], (int, float))
        assert isinstance(data["total_duration"], (int, float))
