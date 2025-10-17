"""ERPNext connection validation service for ERPNext Test Automation Meta-Framework.

Provides services for validating ERPNext instance connections, testing authentication,
and managing connection health monitoring.
"""

import asyncio
import time
from typing import Optional
from urllib.parse import urljoin
from uuid import UUID

import httpx

from .authentication import (
    ConnectionTestResult,
    ERPNextConnectionInfo,
    ERPNextCredentials,
)
from .erpnext_instance import ERPNextInstance


class ERPNextConnectionService:
    """Service for validating and managing ERPNext connections."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """Initialize the connection service.

        Args:
            timeout: Default timeout for connections in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )

    async def cleanup(self) -> None:
        """Clean up the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def test_connection(
        self,
        instance: ERPNextInstance,
        credentials: Optional[ERPNextCredentials] = None
    ) -> ConnectionTestResult:
        """Test connection to an ERPNext instance.

        Args:
            instance: ERPNext instance to test
            credentials: Optional credentials to use for authentication

        Returns:
            Connection test result
        """
        if not self._client:
            await self.initialize()

        start_time = time.time()
        error_message = None
        erpnext_version = None

        try:
            # Test basic connectivity first
            await self._test_basic_connectivity(instance.base_url)

            # Test authentication if credentials provided
            if credentials:
                auth_result = await self._test_authentication(
                    instance.base_url, credentials
                )
                if not auth_result["authenticated"]:
                    error_message = auth_result.get("error", "Authentication failed")
                else:
                    # Get ERPNext version if authenticated
                    erpnext_version = await self._get_erpnext_version(
                        instance.base_url, credentials
                    )

        except httpx.TimeoutException:
            error_message = f"Connection timeout after {self.timeout} seconds"
        except httpx.ConnectError:
            error_message = "Failed to connect to ERPNext instance"
        except httpx.HTTPStatusError as e:
            error_message = f"HTTP error: {e.response.status_code} - {e.response.reason_phrase}"
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"

        response_time = time.time() - start_time
        is_connected = error_message is None

        return ConnectionTestResult(
            instance_id=instance.id,
            is_connected=is_connected,
            response_time=round(response_time, 2) if is_connected else None,
            error_message=error_message,
            erpnext_version=erpnext_version,
        )

    async def _test_basic_connectivity(self, base_url: str) -> None:
        """Test basic HTTP connectivity to ERPNext instance.

        Args:
            base_url: Base URL of the ERPNext instance

        Raises:
            httpx.HTTPError: If connectivity test fails
        """
        # Try to access a public endpoint that doesn't require authentication
        test_url = urljoin(base_url + "/", "api/method/frappe.ping")

        response = await self._client.get(test_url)
        response.raise_for_status()

    async def _test_authentication(
        self,
        base_url: str,
        credentials: ERPNextCredentials
    ) -> dict:
        """Test authentication with ERPNext instance.

        Args:
            base_url: Base URL of the ERPNext instance
            credentials: API credentials

        Returns:
            Authentication test result
        """
        auth_url = urljoin(base_url + "/", "api/method/login")

        auth_data = {
            "usr": credentials.api_key,
            "pwd": credentials.api_secret,
        }

        try:
            response = await self._client.post(
                auth_url,
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("message") == "Logged In":
                    return {"authenticated": True}
                else:
                    return {
                        "authenticated": False,
                        "error": response_data.get("message", "Login failed")
                    }
            else:
                return {
                    "authenticated": False,
                    "error": f"HTTP {response.status_code}: {response.reason_phrase}"
                }

        except httpx.HTTPError as e:
            return {"authenticated": False, "error": str(e)}

    async def _get_erpnext_version(
        self,
        base_url: str,
        credentials: ERPNextCredentials
    ) -> Optional[str]:
        """Get ERPNext version information.

        Args:
            base_url: Base URL of the ERPNext instance
            credentials: API credentials

        Returns:
            ERPNext version string or None if unable to determine
        """
        try:
            # First authenticate to get session
            auth_url = urljoin(base_url + "/", "api/method/login")
            auth_data = {
                "usr": credentials.api_key,
                "pwd": credentials.api_secret,
            }

            auth_response = await self._client.post(
                auth_url,
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if auth_response.status_code != 200:
                return None

            # Get system info
            info_url = urljoin(base_url + "/", "api/method/frappe.utils.get_system_info")
            info_response = await self._client.get(info_url)

            if info_response.status_code == 200:
                info_data = info_response.json()
                return info_data.get("message", {}).get("erpnext_version")

        except Exception:
            # Silently fail if version detection fails
            pass

        return None

    async def validate_connection_info(
        self,
        connection_info: ERPNextConnectionInfo
    ) -> ConnectionTestResult:
        """Validate connection using connection info object.

        Args:
            connection_info: Connection information

        Returns:
            Connection test result
        """
        # Create a temporary instance object for testing
        temp_instance = ERPNextInstance(
            id=connection_info.instance_id,
            name="temp_validation_instance",
            base_url=connection_info.base_url,
            api_key="temp",  # Will be overridden by credentials
            api_secret="temp",  # Will be overridden by credentials
            consultant_id=UUID("00000000-0000-0000-0000-000000000000"),  # Dummy UUID
        )

        return await self.test_connection(temp_instance, connection_info.credentials)

    async def test_multiple_connections(
        self,
        instances: list[ERPNextInstance],
        credentials_list: Optional[list[ERPNextCredentials]] = None
    ) -> list[ConnectionTestResult]:
        """Test connections to multiple ERPNext instances concurrently.

        Args:
            instances: List of ERPNext instances to test
            credentials_list: Optional list of credentials (same order as instances)

        Returns:
            List of connection test results
        """
        if credentials_list and len(credentials_list) != len(instances):
            raise ValueError("Credentials list must match instances list length")

        tasks = []
        for i, instance in enumerate(instances):
            credentials = credentials_list[i] if credentials_list else None
            task = self.test_connection(instance, credentials)
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def monitor_connection_health(
        self,
        instance: ERPNextInstance,
        credentials: Optional[ERPNextCredentials] = None,
        interval_seconds: int = 300  # 5 minutes
    ) -> None:
        """Monitor connection health continuously.

        Args:
            instance: ERPNext instance to monitor
            credentials: Optional credentials for authentication
            interval_seconds: Monitoring interval in seconds
        """
        while True:
            try:
                result = await self.test_connection(instance, credentials)

                if not result.is_connected:
                    # Log connection failure
                    print(f"Connection health check failed for {instance.name}: {result.error_message}")
                else:
                    # Update instance last_connected timestamp
                    instance.mark_connected()
                    print(f"Connection health check passed for {instance.name}")

            except Exception as e:
                print(f"Error during health check for {instance.name}: {e}")

            await asyncio.sleep(interval_seconds)