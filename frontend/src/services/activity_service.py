"""Activity API client service.

This module provides a client interface for interacting with the activity
API endpoints from the frontend Streamlit application.
"""

import logging
import uuid
from typing import Any, Optional

import httpx
import streamlit as st

from .api_client import APIClient

logger = logging.getLogger(__name__)


class ActivityService:
    """Service for activity-related API operations."""

    def __init__(self, api_client: APIClient):
        """
        Initialize activity service.

        Args:
            api_client: Configured API client instance
        """
        self.client = api_client
        self.base_path = "/activities"

    # Cache for frequently accessed data
    @st.cache_data(ttl=300)  # 5 minute cache
    def list_activities(
        self,
        skip: int = 0,
        limit: int = 50,
        erpnext_module: Optional[str] = None,
        action_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        complexity_min: Optional[int] = None,
        complexity_max: Optional[int] = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List activities with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            erpnext_module: Filter by ERPNext module
            action_type: Filter by action type
            is_active: Filter by active status
            complexity_min: Minimum complexity score
            complexity_max: Maximum complexity score

        Returns:
            Tuple of (activities list, total count)
        """
        try:
            params = {"skip": skip, "limit": limit}

            # Add optional filters
            if erpnext_module:
                params["erpnext_module"] = erpnext_module
            if action_type:
                params["action_type"] = action_type
            if is_active is not None:
                params["is_active"] = is_active
            if complexity_min is not None:
                params["complexity_min"] = complexity_min
            if complexity_max is not None:
                params["complexity_max"] = complexity_max

            response = self.client.get(self.base_path, params=params)

            if response.status_code == 200:
                data = response.json()
                return data.get("activities", []), data.get("total", 0)
            else:
                logger.error(f"Failed to list activities: {response.status_code}")
                return [], 0

        except Exception as e:
            logger.error(f"Error listing activities: {e}")
            st.error(f"Failed to load activities: {e}")
            return [], 0

    def get_activity(self, activity_id: uuid.UUID) -> Optional[dict[str, Any]]:
        """
        Get activity by ID.

        Args:
            activity_id: Activity ID

        Returns:
            Activity data or None if not found
        """
        try:
            response = self.client.get(f"{self.base_path}/{activity_id}")

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.error(
                    f"Failed to get activity {activity_id}: {response.status_code}"
                )
                return None

        except Exception as e:
            logger.error(f"Error getting activity {activity_id}: {e}")
            st.error(f"Failed to load activity: {e}")
            return None

    def create_activity(
        self, activity_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """
        Create a new activity.

        Args:
            activity_data: Activity creation data

        Returns:
            Created activity data or None if failed
        """
        try:
            response = self.client.post(self.base_path, json=activity_data)

            if response.status_code == 201:
                st.success("Activity created successfully!")
                # Clear cache
                self.list_activities.clear()
                return response.json()
            else:
                error_detail = self._extract_error_detail(response)
                st.error(f"Failed to create activity: {error_detail}")
                return None

        except Exception as e:
            logger.error(f"Error creating activity: {e}")
            st.error(f"Failed to create activity: {e}")
            return None

    def update_activity(
        self, activity_id: uuid.UUID, activity_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """
        Update an existing activity.

        Args:
            activity_id: Activity ID to update
            activity_data: Updated activity data

        Returns:
            Updated activity data or None if failed
        """
        try:
            response = self.client.put(
                f"{self.base_path}/{activity_id}", json=activity_data
            )

            if response.status_code == 200:
                st.success("Activity updated successfully!")
                # Clear cache
                self.list_activities.clear()
                return response.json()
            elif response.status_code == 404:
                st.error("Activity not found")
                return None
            else:
                error_detail = self._extract_error_detail(response)
                st.error(f"Failed to update activity: {error_detail}")
                return None

        except Exception as e:
            logger.error(f"Error updating activity {activity_id}: {e}")
            st.error(f"Failed to update activity: {e}")
            return None

    def delete_activity(self, activity_id: uuid.UUID) -> bool:
        """
        Delete an activity.

        Args:
            activity_id: Activity ID to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            response = self.client.delete(f"{self.base_path}/{activity_id}")

            if response.status_code == 204:
                st.success("Activity deleted successfully!")
                # Clear cache
                self.list_activities.clear()
                return True
            elif response.status_code == 404:
                st.error("Activity not found")
                return False
            else:
                error_detail = self._extract_error_detail(response)
                st.error(f"Failed to delete activity: {error_detail}")
                return False

        except Exception as e:
            logger.error(f"Error deleting activity {activity_id}: {e}")
            st.error(f"Failed to delete activity: {e}")
            return False

    def search_activities(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[dict[str, Any]] = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Search activities by query.

        Args:
            query: Search query
            page: Page number (1-based)
            per_page: Results per page
            filters: Additional filters

        Returns:
            Tuple of (activities list, total count)
        """
        try:
            search_data = {"query": query, "page": page, "per_page": per_page}

            if filters:
                search_data.update(filters)

            response = self.client.post(f"{self.base_path}/search", json=search_data)

            if response.status_code == 200:
                data = response.json()
                return data.get("activities", []), data.get("total", 0)
            else:
                logger.error(f"Failed to search activities: {response.status_code}")
                return [], 0

        except Exception as e:
            logger.error(f"Error searching activities: {e}")
            st.error(f"Failed to search activities: {e}")
            return [], 0

    @st.cache_data(ttl=600)  # 10 minute cache
    def get_activity_statistics(self) -> dict[str, Any]:
        """
        Get activity statistics.

        Returns:
            Statistics data
        """
        try:
            response = self.client.get(f"{self.base_path}/statistics")

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to get activity statistics: {response.status_code}"
                )
                return {}

        except Exception as e:
            logger.error(f"Error getting activity statistics: {e}")
            return {}

    def validate_activity(self, activity_id: uuid.UUID) -> dict[str, Any]:
        """
        Validate activity configuration.

        Args:
            activity_id: Activity ID to validate

        Returns:
            Validation results
        """
        try:
            response = self.client.get(f"{self.base_path}/{activity_id}/validation")

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"error": "Activity not found"}
            else:
                return {"error": "Validation failed"}

        except Exception as e:
            logger.error(f"Error validating activity {activity_id}: {e}")
            return {"error": str(e)}

    def find_similar_activities(
        self, activity_id: uuid.UUID, limit: int = 10, min_similarity: float = 0.7
    ) -> list[dict[str, Any]]:
        """
        Find similar activities.

        Args:
            activity_id: Reference activity ID
            limit: Maximum number of results
            min_similarity: Minimum similarity score

        Returns:
            List of similar activities
        """
        try:
            params = {"limit": limit, "min_similarity": min_similarity}

            response = self.client.get(
                f"{self.base_path}/{activity_id}/similar", params=params
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to find similar activities: {response.status_code}"
                )
                return []

        except Exception as e:
            logger.error(f"Error finding similar activities: {e}")
            return []

    @st.cache_data(ttl=3600)  # 1 hour cache
    def get_erpnext_modules(self) -> list[str]:
        """
        Get available ERPNext modules.

        Returns:
            List of module names
        """
        try:
            response = self.client.get(f"{self.base_path}/modules")

            if response.status_code == 200:
                return response.json().get("modules", [])
            else:
                # Fallback to common modules
                return [
                    "Accounts",
                    "Stock",
                    "Selling",
                    "Buying",
                    "CRM",
                    "Projects",
                    "Manufacturing",
                    "HR",
                    "Payroll",
                    "Assets",
                    "Support",
                    "Website",
                    "E Commerce",
                ]

        except Exception as e:
            logger.error(f"Error getting ERPNext modules: {e}")
            return []

    @st.cache_data(ttl=3600)  # 1 hour cache
    def get_action_types(self) -> list[str]:
        """
        Get available action types.

        Returns:
            List of action type names
        """
        try:
            response = self.client.get(f"{self.base_path}/action-types")

            if response.status_code == 200:
                return response.json().get("action_types", [])
            else:
                # Fallback to default action types
                return [
                    "create",
                    "read",
                    "update",
                    "delete",
                    "list",
                    "search",
                    "filter",
                    "export",
                    "import",
                    "approve",
                    "submit",
                    "cancel",
                    "validate",
                    "calculate",
                ]

        except Exception as e:
            logger.error(f"Error getting action types: {e}")
            return []

    def bulk_operations(
        self,
        operation: str,
        activity_ids: list[uuid.UUID],
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Perform bulk operations on activities.

        Args:
            operation: Operation type (activate, deactivate, delete, etc.)
            activity_ids: List of activity IDs
            data: Additional operation data

        Returns:
            Operation results
        """
        try:
            bulk_data = {
                "operation": operation,
                "activity_ids": [str(aid) for aid in activity_ids],
            }

            if data:
                bulk_data.update(data)

            response = self.client.post(f"{self.base_path}/bulk", json=bulk_data)

            if response.status_code == 200:
                result = response.json()
                st.success(
                    f"Bulk operation completed: {result.get('processed', 0)} activities"
                )
                # Clear cache
                self.list_activities.clear()
                return result
            else:
                error_detail = self._extract_error_detail(response)
                st.error(f"Bulk operation failed: {error_detail}")
                return {}

        except Exception as e:
            logger.error(f"Error in bulk operation: {e}")
            st.error(f"Bulk operation failed: {e}")
            return {}

    def _extract_error_detail(self, response: httpx.Response) -> str:
        """Extract error detail from API response."""
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                return error_data.get("detail", f"HTTP {response.status_code}")
            else:
                return str(error_data)
        except:
            return f"HTTP {response.status_code}"


# Persona-Activity relationship methods
class PersonaActivityService:
    """Service for persona-activity relationship operations."""

    def __init__(self, api_client: APIClient):
        """Initialize persona-activity service."""
        self.client = api_client

    def list_persona_activities(
        self,
        persona_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        priority: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """List activities for a specific persona."""
        try:
            params = {"skip": skip, "limit": limit}

            if priority:
                params["priority"] = priority
            if is_active is not None:
                params["is_active"] = is_active

            response = self.client.get(
                f"/personas/{persona_id}/activities", params=params
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("activities", []), data.get("total", 0)
            else:
                return [], 0

        except Exception as e:
            logger.error(f"Error listing persona activities: {e}")
            return [], 0

    def link_persona_to_activity(
        self,
        persona_id: uuid.UUID,
        activity_id: uuid.UUID,
        priority: str = "medium",
        notes: str = "",
    ) -> Optional[dict[str, Any]]:
        """Link persona to activity."""
        try:
            link_data = {"priority": priority, "notes": notes}

            response = self.client.post(
                f"/personas/{persona_id}/activities/{activity_id}", json=link_data
            )

            if response.status_code == 201:
                return response.json()
            else:
                return None

        except Exception as e:
            logger.error(f"Error linking persona to activity: {e}")
            return None

    def get_activity_recommendations(
        self, persona_id: uuid.UUID, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get activity recommendations for persona."""
        try:
            params = {"limit": limit}

            response = self.client.get(
                f"/personas/{persona_id}/activities/recommendations", params=params
            )

            if response.status_code == 200:
                return response.json()
            else:
                return []

        except Exception as e:
            logger.error(f"Error getting activity recommendations: {e}")
            return []


def get_activity_service() -> ActivityService:
    """Get configured activity service instance."""
    api_client = APIClient()
    return ActivityService(api_client)


def get_persona_activity_service() -> PersonaActivityService:
    """Get configured persona-activity service instance."""
    api_client = APIClient()
    return PersonaActivityService(api_client)
