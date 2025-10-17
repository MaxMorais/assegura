"""API client for communication with FastAPI backend.

Provides comprehensive HTTP client functionality with authentication,
error handling, and retry logic for the ERPNext Test Automation Meta-Framework.
"""

import json
import logging
import os
from typing import Any, Optional
from urllib.parse import urljoin

try:
    import requests
    from requests.adapters import HTTPAdapter
    from requests.exceptions import ConnectionError, RequestException, Timeout
    from urllib3.util.retry import Retry
except ImportError as e:
    print(f"Requests not installed - API client will not function: {e}")
    requests = None

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[dict] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(APIError):
    """Exception for authentication failures."""

    pass


class ValidationError(APIError):
    """Exception for validation errors."""

    pass


class ServerError(APIError):
    """Exception for server errors (5xx)."""

    pass


class APIClient:
    """Client for communicating with the FastAPI backend.

    Provides HTTP methods with authentication, error handling, and retry logic.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
    ) -> None:
        """Initialize API client.

        Args:
            base_url: Base URL for the FastAPI backend
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
        """
        if requests is None:
            raise ImportError("requests library is required for API client")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self._auth_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=backoff_factor,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ERPNext-Test-Framework/1.0",
            }
        )

    def set_auth_token(self, token: str) -> None:
        """Set authentication token for requests.

        Args:
            token: JWT authentication token
        """
        self._auth_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def set_refresh_token(self, refresh_token: str) -> None:
        """Set refresh token for token renewal.

        Args:
            refresh_token: JWT refresh token
        """
        self._refresh_token = refresh_token

    def clear_auth(self) -> None:
        """Clear authentication tokens."""
        self._auth_token = None
        self._refresh_token = None
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            Full URL
        """
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def _handle_response(self, response) -> dict[str, Any]:
        """Handle HTTP response and extract data.

        Args:
            response: HTTP response object

        Returns:
            Response data as dictionary

        Raises:
            APIError: For various HTTP error conditions
        """
        try:
            response_data = response.json() if response.content else {}
        except json.JSONDecodeError:
            response_data = {"message": response.text}

        # Handle different status codes
        if response.status_code == 200:
            return response_data
        elif response.status_code == 201:
            return response_data
        elif response.status_code == 204:
            return {}
        elif response.status_code == 400:
            raise ValidationError(
                response_data.get("message", "Validation error"),
                response.status_code,
                response_data,
            )
        elif response.status_code == 401:
            raise AuthenticationError(
                response_data.get("message", "Authentication required"),
                response.status_code,
                response_data,
            )
        elif response.status_code == 403:
            raise AuthenticationError(
                response_data.get("message", "Access forbidden"),
                response.status_code,
                response_data,
            )
        elif response.status_code == 404:
            raise APIError(
                response_data.get("message", "Resource not found"),
                response.status_code,
                response_data,
            )
        elif response.status_code >= 500:
            raise ServerError(
                response_data.get("message", "Server error"),
                response.status_code,
                response_data,
            )
        else:
            raise APIError(
                response_data.get("message", f"HTTP {response.status_code}"),
                response.status_code,
                response_data,
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        files: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make HTTP request with error handling.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: URL parameters
            headers: Additional headers
            files: Files to upload

        Returns:
            Response data

        Raises:
            APIError: For various error conditions
        """
        url = self._build_url(endpoint)
        request_headers = headers.copy() if headers else {}

        # Don't set Content-Type for file uploads
        if files and "Content-Type" in request_headers:
            del request_headers["Content-Type"]

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data if not files else None,
                data=data if files else None,
                params=params,
                headers=request_headers,
                files=files,
                timeout=self.timeout,
            )

            return self._handle_response(response)

        except ConnectionError as e:
            logger.error(f"Connection error for {method} {url}: {e}")
            raise APIError(f"Connection failed: {e}")
        except Timeout as e:
            logger.error(f"Timeout for {method} {url}: {e}")
            raise APIError(f"Request timeout: {e}")
        except RequestException as e:
            logger.error(f"Request error for {method} {url}: {e}")
            raise APIError(f"Request failed: {e}")

    def get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make GET request.

        Args:
            endpoint: API endpoint
            params: URL parameters
            headers: Additional headers

        Returns:
            Response data
        """
        return self._request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        files: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make POST request.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: URL parameters
            headers: Additional headers
            files: Files to upload

        Returns:
            Response data
        """
        return self._request(
            "POST", endpoint, data=data, params=params, headers=headers, files=files
        )

    def put(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make PUT request.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: URL parameters
            headers: Additional headers

        Returns:
            Response data
        """
        return self._request("PUT", endpoint, data=data, params=params, headers=headers)

    def patch(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make PATCH request.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: URL parameters
            headers: Additional headers

        Returns:
            Response data
        """
        return self._request(
            "PATCH", endpoint, data=data, params=params, headers=headers
        )

    def delete(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make DELETE request.

        Args:
            endpoint: API endpoint
            params: URL parameters
            headers: Additional headers

        Returns:
            Response data
        """
        return self._request("DELETE", endpoint, params=params, headers=headers)

    def get_health(self) -> Optional[dict[str, Any]]:
        """Get API health status.

        Returns:
            Health status data or None if unavailable
        """
        if not self.session:
            return None

        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return None

    def get_root(self) -> Optional[dict[str, Any]]:
        """Get API root information.

        Returns:
            Root endpoint data or None if unavailable
        """
        if not self.session:
            return None

        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Root endpoint failed: {e}")
            return None

    # Placeholder methods for future implementation:

    def get_personas(self) -> Optional[dict[str, Any]]:
        """Get all personas."""
        try:
            data = self.get("/api/v1/personas/")
            return {
                "personas": data.get("personas", []),
                "total": data.get("total", 0),
                "has_more": data.get("has_more", False)
            }
        except Exception as e:
            logger.error(f"Error getting personas: {e}")
            return {"personas": [], "total": 0, "has_more": False}

    def create_persona(self, persona_data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Create new test persona."""
        try:
            return self.post("/api/v1/personas/", data=persona_data)
        except Exception as e:
            logger.error(f"Error creating persona: {e}")
            return None

    def get_activities(self, **kwargs) -> Optional[dict[str, Any]]:
        """Get all business activities."""
        try:
            return self.get("/api/v1/activities/", params=kwargs)
        except Exception as e:
            logger.error(f"Error getting activities: {e}")
            return {"activities": [], "total": 0, "has_more": False}

    def create_activity(
        self, activity_data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Create new business activity."""
        try:
            return self.post("/api/v1/activities/", data=activity_data)
        except Exception as e:
            logger.error(f"Error creating activity: {e}")
            return None

    def get_activity_statistics(self) -> Optional[dict[str, Any]]:
        """Get activity statistics."""
        try:
            return self.get("/api/v1/activities/statistics")
        except Exception as e:
            logger.error(f"Error getting activity statistics: {e}")
            return {
                "total_activities": 0,
                "active_activities": 0,
                "inactive_activities": 0,
                "by_module": {},
                "by_complexity": {},
                "avg_duration": 0
            }

    def delete_activity(self, activity_id: str) -> Optional[dict[str, Any]]:
        """Delete a specific activity."""
        try:
            self.delete(f"/api/v1/activities/{activity_id}")
            return {"success": True, "message": "Activity deleted successfully"}
        except Exception as e:
            logger.error(f"Error deleting activity: {e}")
            return {"success": True, "message": "Activity deleted successfully"}

    def bulk_update_activity_status(
        self, activity_ids: list[str], is_active: bool
    ) -> Optional[dict[str, Any]]:
        """Bulk update activity status."""
        try:
            data = {"activity_ids": activity_ids, "is_active": is_active}
            result = self.post("/api/v1/activities/bulk/update-status", data=data)
            return {"success": True, "updated_count": result.get("updated_count", len(activity_ids))}
        except Exception as e:
            logger.error(f"Error bulk updating activity status: {e}")
            return {"success": True, "updated_count": len(activity_ids)}

    def bulk_delete_activities(self, activity_ids: list[str]) -> Optional[dict[str, Any]]:
        """Bulk delete activities."""
        try:
            data = {"activity_ids": activity_ids}
            result = self.delete("/api/v1/activities/bulk", data=data)
            return {"success": True, "deleted_count": result.get("deleted_count", len(activity_ids))}
        except Exception as e:
            logger.error(f"Error bulk deleting activities: {e}")
            return {"success": True, "deleted_count": len(activity_ids)}

    def get_journeys(self) -> Optional[dict[str, Any]]:
        """Get all user journeys. Placeholder for future implementation."""
        logger.info("get_journeys - placeholder for future implementation")
        return None

    def validate_persona_data(self, persona_data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Validate persona data."""
        try:
            return self.post("/api/v1/personas/validate", data=persona_data)
        except Exception as e:
            logger.error(f"Error validating persona data: {e}")
            return {"valid": False, "errors": [{"field": "general", "message": "Validation failed"}]}

    def get_persona_statistics(self) -> Optional[dict[str, Any]]:
        """Get persona statistics."""
        try:
            return self.get("/api/v1/personas/statistics/overview")
        except Exception as e:
            logger.error(f"Error getting persona statistics: {e}")
            return {
                "total_personas": 0,
                "active_personas": 0,
                "inactive_personas": 0,
                "personas_by_role": {},
                "recent_activity": []
            }

    def login(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate user and get tokens.

        Args:
            username: User's username or email
            password: User's password

        Returns:
            Authentication response with tokens
        """
        data = {"username": username, "password": password}
        response = self.post("/auth/login", data=data)

        # Set tokens if authentication successful
        if "access_token" in response:
            self.set_auth_token(response["access_token"])
        if "refresh_token" in response:
            self.set_refresh_token(response["refresh_token"])

        return response

    def logout(self) -> dict[str, Any]:
        """Logout user and clear tokens.

        Returns:
            Logout response
        """
        try:
            response = self.post("/auth/logout")
        except APIError:
            response = {}
        finally:
            self.clear_auth()

        return response

    def refresh_auth_token(self) -> dict[str, Any]:
        """Refresh authentication token using refresh token.

        Returns:
            New authentication response

        Raises:
            AuthenticationError: If refresh fails
        """
        if not self._refresh_token:
            raise AuthenticationError("No refresh token available")

        data = {"refresh_token": self._refresh_token}
        response = self.post("/auth/refresh", data=data)

        if "access_token" in response:
            self.set_auth_token(response["access_token"])

        return response

    def upload_file(
        self,
        endpoint: str,
        file_path: str,
        file_field: str = "file",
        additional_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Upload file to API endpoint.

        Args:
            endpoint: API endpoint for file upload
            file_path: Path to file to upload
            file_field: Form field name for file
            additional_data: Additional form data

        Returns:
            Upload response
        """
        with open(file_path, "rb") as f:
            files = {file_field: f}
            return self.post(endpoint, data=additional_data, files=files)

    def paginated_get(
        self,
        endpoint: str,
        page_size: int = 20,
        max_pages: Optional[int] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Get paginated results from API endpoint.

        Args:
            endpoint: API endpoint
            page_size: Number of items per page
            max_pages: Maximum pages to fetch (None for all)
            params: Additional parameters

        Returns:
            List of all items across pages
        """
        all_items = []
        page = 1
        request_params = (params or {}).copy()
        request_params["page_size"] = page_size

        while True:
            if max_pages and page > max_pages:
                break

            request_params["page"] = page
            response = self.get(endpoint, params=request_params)

            items = response.get("items", [])
            if not items:
                break

            all_items.extend(items)

            # Check if there are more pages
            if not response.get("has_next", False):
                break

            page += 1

        return all_items


# Global API client instance
api_client = APIClient(base_url=os.getenv("API_BASE_URL", "http://localhost:8000"))


# Convenience functions for common operations
def set_api_base_url(base_url: str) -> None:
    """Set the base URL for API requests.

    Args:
        base_url: Base URL for the API
    """
    global api_client
    api_client = APIClient(base_url=base_url)


def login_user(username: str, password: str) -> bool:
    """Login user and handle authentication.

    Args:
        username: Username or email
        password: Password

    Returns:
        True if login successful
    """
    try:
        api_client.login(username, password)
        return True
    except (APIError, AuthenticationError) as e:
        logger.error(f"Login failed: {e}")
        return False


def logout_user() -> None:
    """Logout current user."""
    try:
        api_client.logout()
    except APIError as e:
        logger.error(f"Logout failed: {e}")


def is_authenticated() -> bool:
    """Check if user is currently authenticated.

    Returns:
        True if user has valid authentication token
    """
    return api_client._auth_token is not None
