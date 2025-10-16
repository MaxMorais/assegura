"""
Journey API Client Service

Client service for interacting with journey-related API endpoints
in the ERPNext test automation framework. Provides methods for
journey CRUD operations, validation, and management.
"""

from typing import Any, Dict, List, Optional
import uuid

from .api_client import APIClient


class JourneyAPIClient(APIClient):
    """API client for journey operations."""

    def __init__(self):
        super().__init__()
        self.base_endpoint = "/journeys"

    async def create_journey(self, journey_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new journey.
        
        Args:
            journey_data: Journey creation data
            
        Returns:
            Created journey data
        """
        return await self.post(self.base_endpoint, json=journey_data)

    async def get_journey(self, journey_id: str) -> Dict[str, Any]:
        """
        Get journey by ID.
        
        Args:
            journey_id: Journey UUID
            
        Returns:
            Journey data
        """
        return await self.get(f"{self.base_endpoint}/{journey_id}")

    def list_journeys(
        self,
        skip: int = 0,
        limit: int = 50,
        persona_id: Optional[str] = None,
        activity_id: Optional[str] = None,
        execution_status: Optional[str] = None,
        complexity_level: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List journeys with filtering.
        
        Args:
            skip: Number of journeys to skip
            limit: Maximum number of journeys to return
            persona_id: Filter by persona ID
            activity_id: Filter by activity ID
            execution_status: Filter by execution status
            complexity_level: Filter by complexity level
            is_active: Filter by active status
            search: Text search in name/description
            
        Returns:
            Paginated journey list response
        """
        # Return mock data for now since backend is not ready
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Returning mock journey data")
        
        mock_journeys = [
            {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "name": "Sales Order to Invoice Journey",
                "description": "Complete journey from sales quotation to invoice generation",
                "persona_id": "550e8400-e29b-41d4-a716-446655440000",
                "persona_name": "Sales Manager",
                "activities": [
                    {
                        "id": "770e8400-e29b-41d4-a716-446655440000",
                        "name": "Create Sales Quotation",
                        "sequence": 1
                    },
                    {
                        "id": "770e8400-e29b-41d4-a716-446655440001",
                        "name": "Convert to Sales Order",
                        "sequence": 2
                    },
                    {
                        "id": "770e8400-e29b-41d4-a716-446655440002",
                        "name": "Create Delivery Note",
                        "sequence": 3
                    },
                    {
                        "id": "770e8400-e29b-41d4-a716-446655440003",
                        "name": "Generate Sales Invoice",
                        "sequence": 4
                    }
                ],
                "step_count": 4,
                "execution_status": "ready",
                "complexity_level": "medium",
                "estimated_duration": 45,
                "is_active": True,
                "is_complete_scenario": True,
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z"
            },
            {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "name": "Purchase Order Processing",
                "description": "Journey for processing purchase orders from request to payment",
                "persona_id": "550e8400-e29b-41d4-a716-446655440001",
                "persona_name": "Purchase User",
                "activities": [
                    {
                        "id": "770e8400-e29b-41d4-a716-446655440004",
                        "name": "Create Purchase Request",
                        "sequence": 1
                    },
                    {
                        "id": "770e8400-e29b-41d4-a716-446655440005",
                        "name": "Approve Purchase Request",
                        "sequence": 2
                    },
                    {
                        "id": "770e8400-e29b-41d4-a716-446655440006",
                        "name": "Create Purchase Order",
                        "sequence": 3
                    },
                    {
                        "id": "770e8400-e29b-41d4-a716-446655440007",
                        "name": "Receive Goods",
                        "sequence": 4
                    }
                ],
                "step_count": 4,
                "execution_status": "not_started",
                "complexity_level": "high",
                "estimated_duration": 60,
                "is_active": True,
                "is_complete_scenario": False,
                "created_at": "2025-01-16T14:30:00Z",
                "updated_at": "2025-01-16T14:30:00Z"
            }
        ]
        
        # Apply filters
        filtered_journeys = mock_journeys
        
        if persona_id:
            filtered_journeys = [j for j in filtered_journeys if j["persona_id"] == persona_id]
        
        if execution_status:
            filtered_journeys = [j for j in filtered_journeys if j["execution_status"] == execution_status]
            
        if complexity_level:
            filtered_journeys = [j for j in filtered_journeys if j["complexity_level"] == complexity_level]
            
        if is_active is not None:
            filtered_journeys = [j for j in filtered_journeys if j["is_active"] == is_active]
            
        if search:
            search_lower = search.lower()
            filtered_journeys = [
                j for j in filtered_journeys 
                if search_lower in j["name"].lower() or search_lower in j["description"].lower()
            ]
        
        # Apply pagination
        total = len(filtered_journeys)
        paginated_journeys = filtered_journeys[skip:skip + limit]
        
        return {
            "items": paginated_journeys,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": skip + limit < total
        }

    async def update_journey(self, journey_id: str, journey_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing journey.
        
        Args:
            journey_id: Journey UUID
            journey_data: Journey update data
            
        Returns:
            Updated journey data
        """
        return await self.put(f"{self.base_endpoint}/{journey_id}", json=journey_data)

    async def delete_journey(self, journey_id: str) -> None:
        """
        Delete a journey.
        
        Args:
            journey_id: Journey UUID
        """
        await self.delete(f"{self.base_endpoint}/{journey_id}")

    async def validate_journey(self, journey_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a journey configuration.
        
        Args:
            journey_data: Journey data to validate
            
        Returns:
            Validation results
        """
        return await self.post(f"{self.base_endpoint}/validate", json=journey_data)

    async def get_journey_statistics(self, activity_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get journey statistics.
        
        Args:
            activity_id: Optional activity ID to filter statistics
            
        Returns:
            Journey statistics data
        """
        params = {}
        if activity_id:
            params["activity_id"] = activity_id
        
        return await self.get(f"{self.base_endpoint}/statistics", params=params)

    # Journey Steps Management
    async def get_journey_steps(self, journey_id: str) -> List[Dict[str, Any]]:
        """
        Get steps for a specific journey.
        
        Args:
            journey_id: Journey UUID
            
        Returns:
            List of journey steps
        """
        response = await self.get(f"{self.base_endpoint}/{journey_id}/steps")
        return response.get("steps", [])

    async def add_journey_step(self, journey_id: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a step to a journey.
        
        Args:
            journey_id: Journey UUID
            step_data: Step data
            
        Returns:
            Created step data
        """
        return await self.post(f"{self.base_endpoint}/{journey_id}/steps", json=step_data)

    async def update_journey_step(
        self, journey_id: str, step_id: str, step_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a journey step.
        
        Args:
            journey_id: Journey UUID
            step_id: Step UUID
            step_data: Step update data
            
        Returns:
            Updated step data
        """
        return await self.put(f"{self.base_endpoint}/{journey_id}/steps/{step_id}", json=step_data)

    async def delete_journey_step(self, journey_id: str, step_id: str) -> None:
        """
        Delete a journey step.
        
        Args:
            journey_id: Journey UUID
            step_id: Step UUID
        """
        await self.delete(f"{self.base_endpoint}/{journey_id}/steps/{step_id}")

    async def reorder_journey_steps(self, journey_id: str, step_order: List[str]) -> Dict[str, Any]:
        """
        Reorder journey steps.
        
        Args:
            journey_id: Journey UUID
            step_order: List of step IDs in desired order
            
        Returns:
            Updated journey data
        """
        return await self.put(
            f"{self.base_endpoint}/{journey_id}/steps/reorder",
            json={"step_order": step_order}
        )

    # Journey Execution
    async def execute_journey(self, journey_id: str, execution_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a journey.
        
        Args:
            journey_id: Journey UUID
            execution_config: Optional execution configuration
            
        Returns:
            Execution result data
        """
        config = execution_config or {}
        return await self.post(f"{self.base_endpoint}/{journey_id}/execute", json=config)

    async def get_journey_execution_status(self, journey_id: str, execution_id: str) -> Dict[str, Any]:
        """
        Get journey execution status.
        
        Args:
            journey_id: Journey UUID
            execution_id: Execution UUID
            
        Returns:
            Execution status data
        """
        return await self.get(f"{self.base_endpoint}/{journey_id}/executions/{execution_id}")

    async def cancel_journey_execution(self, journey_id: str, execution_id: str) -> None:
        """
        Cancel a journey execution.
        
        Args:
            journey_id: Journey UUID
            execution_id: Execution UUID
        """
        await self.post(f"{self.base_endpoint}/{journey_id}/executions/{execution_id}/cancel")

    # Journey Templates
    async def create_journey_from_template(self, template_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a journey from a template.
        
        Args:
            template_name: Template name
            parameters: Template parameters
            
        Returns:
            Created journey data
        """
        return await self.post(
            f"{self.base_endpoint}/from-template",
            json={"template_name": template_name, "parameters": parameters}
        )

    async def save_journey_as_template(self, journey_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a journey as a template.
        
        Args:
            journey_id: Journey UUID
            template_data: Template data
            
        Returns:
            Created template data
        """
        return await self.post(
            f"{self.base_endpoint}/{journey_id}/save-as-template",
            json=template_data
        )

    # Bulk Operations
    async def bulk_update_journeys(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform bulk operations on journeys.
        
        Args:
            operation_data: Bulk operation data
            
        Returns:
            Bulk operation results
        """
        return await self.post(f"{self.base_endpoint}/bulk", json=operation_data)

    async def export_journey(self, journey_id: str, export_format: str = "json") -> Dict[str, Any]:
        """
        Export a journey.
        
        Args:
            journey_id: Journey UUID
            export_format: Export format (json, yaml, robot)
            
        Returns:
            Exported journey data
        """
        return await self.get(
            f"{self.base_endpoint}/{journey_id}/export",
            params={"format": export_format}
        )

    async def import_journey(self, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import a journey.
        
        Args:
            import_data: Journey import data
            
        Returns:
            Imported journey data
        """
        return await self.post(f"{self.base_endpoint}/import", json=import_data)

    # Activity-Journey Operations
    async def list_activity_journeys(
        self,
        activity_id: str,
        skip: int = 0,
        limit: int = 50,
        persona_id: Optional[str] = None,
        execution_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List journeys for a specific activity.
        
        Args:
            activity_id: Activity UUID
            skip: Number of journeys to skip
            limit: Maximum number of journeys to return
            persona_id: Filter by persona ID
            execution_status: Filter by execution status
            
        Returns:
            Paginated journey list response
        """
        params = {"skip": skip, "limit": limit}
        
        if persona_id:
            params["persona_id"] = persona_id
        if execution_status:
            params["execution_status"] = execution_status
        
        return await self.get(f"/activities/{activity_id}/journeys", params=params)

    async def create_activity_journey(self, activity_id: str, journey_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a journey for a specific activity.
        
        Args:
            activity_id: Activity UUID
            journey_data: Journey creation data
            
        Returns:
            Created journey data
        """
        return await self.post(f"/activities/{activity_id}/journeys", json=journey_data)

    async def get_activity_journey(self, activity_id: str, journey_id: str) -> Dict[str, Any]:
        """
        Get a specific journey for an activity.
        
        Args:
            activity_id: Activity UUID
            journey_id: Journey UUID
            
        Returns:
            Journey data
        """
        return await self.get(f"/activities/{activity_id}/journeys/{journey_id}")

    async def update_activity_journey(
        self, activity_id: str, journey_id: str, journey_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a journey for a specific activity.
        
        Args:
            activity_id: Activity UUID
            journey_id: Journey UUID
            journey_data: Journey update data
            
        Returns:
            Updated journey data
        """
        return await self.put(f"/activities/{activity_id}/journeys/{journey_id}", json=journey_data)

    async def delete_activity_journey(self, activity_id: str, journey_id: str) -> None:
        """
        Delete a journey for a specific activity.
        
        Args:
            activity_id: Activity UUID
            journey_id: Journey UUID
        """
        await self.delete(f"/activities/{activity_id}/journeys/{journey_id}")

    async def get_activity_journey_statistics(self, activity_id: str) -> Dict[str, Any]:
        """
        Get journey statistics for a specific activity.
        
        Args:
            activity_id: Activity UUID
            
        Returns:
            Journey statistics data
        """
        return await self.get(f"/activities/{activity_id}/journeys/statistics")

    async def validate_activity_journey(self, activity_id: str, journey_id: str) -> Dict[str, Any]:
        """
        Validate a journey for a specific activity.
        
        Args:
            activity_id: Activity UUID
            journey_id: Journey UUID
            
        Returns:
            Validation results
        """
        return await self.post(f"/activities/{activity_id}/journeys/{journey_id}/validate")


# Convenience functions for backward compatibility
def create_journey(journey_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new journey."""
    client = JourneyAPIClient()
    return client.create_journey(journey_data)


def get_journey(journey_id: str) -> Dict[str, Any]:
    """Get journey by ID."""
    client = JourneyAPIClient()
    return client.get_journey(journey_id)


def list_journeys(**kwargs) -> Dict[str, Any]:
    """List journeys with filtering."""
    client = JourneyAPIClient()
    return client.list_journeys(**kwargs)


def update_journey(journey_id: str, journey_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing journey."""
    client = JourneyAPIClient()
    return client.update_journey(journey_id, journey_data)


def delete_journey(journey_id: str) -> None:
    """Delete a journey."""
    client = JourneyAPIClient()
    return client.delete_journey(journey_id)