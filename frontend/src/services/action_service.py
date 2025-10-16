"""
Action API Client Service

Client service for interacting with action-related API endpoints
in the ERPNext test automation framework. Provides methods for
action library CRUD operations and management.
"""

from typing import Any, Dict, List, Optional

from .api_client import APIClient


class ActionAPIClient(APIClient):
    """API client for action operations."""

    def __init__(self):
        super().__init__()
        self.base_endpoint = "/actions"

    async def create_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new action.

        Args:
            action_data: Action creation data

        Returns:
            Created action data
        """
        return await self.post(self.base_endpoint, json=action_data)

    async def get_action(self, action_id: str) -> Dict[str, Any]:
        """
        Get action by ID.

        Args:
            action_id: Action UUID

        Returns:
            Action data
        """
        return await self.get(f"{self.base_endpoint}/{action_id}")

    async def list_actions(
        self,
        skip: int = 0,
        limit: int = 50,
        action_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List actions with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            action_type: Filter by action type (given/when/then)
            search: Search term for action name or description

        Returns:
            Paginated list of actions
        """
        params = {"skip": skip, "limit": limit}
        if action_type:
            params["action_type"] = action_type
        if search:
            params["search"] = search

        return await self.get(self.base_endpoint, params=params)

    async def update_action(self, action_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing action.

        Args:
            action_id: Action UUID
            action_data: Updated action data

        Returns:
            Updated action data
        """
        return await self.put(f"{self.base_endpoint}/{action_id}", json=action_data)

    async def delete_action(self, action_id: str) -> None:
        """
        Delete an action.

        Args:
            action_id: Action UUID
        """
        await self.delete(f"{self.base_endpoint}/{action_id}")

    async def get_action_types(self) -> List[str]:
        """
        Get available action types.

        Returns:
            List of action type names
        """
        response = await self.get(f"{self.base_endpoint}/types")
        return response.get("types", [])

    async def validate_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate action data.

        Args:
            action_data: Action data to validate

        Returns:
            Validation result
        """
        return await self.post(f"{self.base_endpoint}/validate", json=action_data)