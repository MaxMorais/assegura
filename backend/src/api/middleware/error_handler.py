"""Advanced error handling middleware for FastAPI.

Provides comprehensive error handling, logging, and response standardization
for the ERPNext Test Automation Meta-Framework API with constitutional compliance.
"""

import logging
import traceback
from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import uuid4

try:
    from fastapi import HTTPException, Request, Response, status
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from pydantic import ValidationError
    from starlette.middleware.base import BaseHTTPMiddleware
except ImportError as e:
    print(f"FastAPI dependencies not installed: {e}")

from ...application.dto import ErrorResponse, ValidationErrorResponse
from ...domain.activities.exceptions import ActivityAlreadyExistsError

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Advanced error handling middleware with logging and monitoring."""

    def __init__(
        self,
        app: Any,
        debug: bool = False,
        include_trace: bool = False,
        log_errors: bool = True,
        enable_monitoring: bool = True,
    ) -> None:
        """Initialize error handling middleware.

        Args:
            app: FastAPI application instance
            debug: Whether to include debug information in responses
            include_trace: Whether to include stack traces in responses
            log_errors: Whether to log errors
            enable_monitoring: Whether to enable error monitoring/metrics
        """
        self.app = app
        self.debug = debug
        self.include_trace = include_trace
        self.log_errors = log_errors
        self.enable_monitoring = enable_monitoring

        # Error tracking for monitoring
        self.error_counts: dict[str, int] = {}
        self.last_errors: dict[str, datetime] = {}

    async def dispatch_func(self, request: "Request", call_next: Callable) -> "Response":
        """Process request with comprehensive error handling.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response with proper error handling
        """
        # Generate request ID for tracing
        request_id = str(uuid4())
        request.state.request_id = request_id

        try:
            # Process request
            response = await call_next(request)
            return response

        except HTTPException as exc:
            return await self._handle_http_exception(request, exc, request_id)

        except RequestValidationError as exc:
            return await self._handle_validation_error(request, exc, request_id)

        except ValidationError as exc:
            return await self._handle_pydantic_validation_error(
                request, exc, request_id
            )

        except PermissionError as exc:
            return await self._handle_permission_error(request, exc, request_id)

        except ValueError as exc:
            return await self._handle_value_error(request, exc, request_id)

        except RuntimeError as exc:
            return await self._handle_runtime_error(request, exc, request_id)

        except ActivityAlreadyExistsError as exc:
            return await self._handle_activity_already_exists_error(request, exc, request_id)

        except Exception as exc:
            return await self._handle_unexpected_error(request, exc, request_id)

    async def _handle_http_exception(
        self, request: "Request", exc: "HTTPException", request_id: str
    ) -> "JSONResponse":
        """Handle HTTP exceptions with standardized format.

        Args:
            request: FastAPI request object
            exc: HTTP exception
            request_id: Request tracking ID

        Returns:
            Standardized JSON error response
        """
        if self.log_errors and exc.status_code >= 500:
            logger.error(
                f"HTTP {exc.status_code} in {request.method} {request.url}: {exc.detail}",
                extra={
                    "request_id": request_id,
                    "status_code": exc.status_code,
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": self._get_client_ip(request),
                },
            )

        error_response = ErrorResponse(
            error=exc.__class__.__name__,
            message=str(exc.detail),
            details={"status_code": exc.status_code, "request_id": request_id},
        )

        if self.debug:
            error_response.details.update(
                {
                    "method": request.method,
                    "url": str(request.url),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        self._track_error(exc.__class__.__name__)

        try:
            return JSONResponse(
                status_code=exc.status_code, content=error_response.model_dump()
            )
        except NameError:
            # Fallback if JSONResponse not available
            return {"error": str(exc.detail), "status_code": exc.status_code}

    async def _handle_validation_error(
        self, request: "Request", exc: "RequestValidationError", request_id: str
    ) -> "JSONResponse":
        """Handle request validation errors with detailed field information.

        Args:
            request: FastAPI request object
            exc: Request validation error
            request_id: Request tracking ID

        Returns:
            Standardized validation error response
        """
        if self.log_errors:
            logger.warning(
                f"Validation error in {request.method} {request.url}: {len(exc.errors())} errors",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "validation_errors": exc.errors(),
                    "client_ip": self._get_client_ip(request),
                },
            )

        validation_errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append(
                {
                    "field": field_path,
                    "message": error["msg"],
                    "value": error.get("input"),
                    "type": error.get("type"),
                }
            )

        error_response = ValidationErrorResponse(
            message="Request validation failed",
            validation_errors=validation_errors,
            request_id=request_id,
        )

        if self.debug:
            error_response.details = {
                "method": request.method,
                "raw_errors": exc.errors(),
                "timestamp": datetime.utcnow().isoformat(),
            }

        self._track_error("RequestValidationError")

        try:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=error_response.model_dump(),
            )
        except NameError:
            return {"error": "Validation failed", "details": validation_errors}

    async def _handle_pydantic_validation_error(
        self, request: "Request", exc: "ValidationError", request_id: str
    ) -> "JSONResponse":
        """Handle Pydantic model validation errors.

        Args:
            request: FastAPI request object
            exc: Pydantic validation error
            request_id: Request tracking ID

        Returns:
            Standardized validation error response
        """
        if self.log_errors:
            logger.warning(
                f"Pydantic validation error in {request.method} {request.url}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "validation_errors": exc.errors(),
                    "client_ip": self._get_client_ip(request),
                },
            )

        validation_errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append(
                {
                    "field": field_path,
                    "message": error["msg"],
                    "value": error.get("input"),
                    "type": error.get("type"),
                }
            )

        error_response = ValidationErrorResponse(
            message="Data validation failed",
            validation_errors=validation_errors,
            request_id=request_id,
        )

        if self.debug:
            error_response.details = {
                "method": request.method,
                "raw_errors": exc.errors(),
                "timestamp": datetime.utcnow().isoformat(),
            }

        self._track_error("PydanticValidationError")

        try:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.model_dump(),
            )
        except NameError:
            return {"error": "Validation failed", "details": validation_errors}

    async def _handle_permission_error(
        self, request: "Request", exc: PermissionError, request_id: str
    ) -> "JSONResponse":
        """Handle permission/authorization errors.

        Args:
            request: FastAPI request object
            exc: Permission error
            request_id: Request tracking ID

        Returns:
            Standardized permission error response
        """
        if self.log_errors:
            logger.warning(
                f"Permission denied in {request.method} {request.url}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": self._get_client_ip(request),
                    "user_agent": request.headers.get("user-agent"),
                },
            )

        error_response = ErrorResponse(
            error="PermissionDenied",
            message="Insufficient permissions to access this resource",
            details={"request_id": request_id, "resource": str(request.url.path)},
        )

        if self.debug:
            error_response.details.update(
                {
                    "method": request.method,
                    "original_error": str(exc),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        self._track_error("PermissionError")

        try:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=error_response.model_dump(),
            )
        except NameError:
            return {"error": "Permission denied", "status_code": 403}

    async def _handle_value_error(
        self, request: "Request", exc: ValueError, request_id: str
    ) -> "JSONResponse":
        """Handle value errors (bad input data).

        Args:
            request: FastAPI request object
            exc: Value error
            request_id: Request tracking ID

        Returns:
            Standardized value error response
        """
        if self.log_errors:
            logger.warning(
                f"Value error in {request.method} {request.url}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": self._get_client_ip(request),
                },
            )

        error_response = ErrorResponse(
            error="InvalidValue",
            message=str(exc) if str(exc) else "Invalid input value provided",
            details={"request_id": request_id, "error_type": "ValueError"},
        )

        if self.debug:
            error_response.details.update(
                {
                    "method": request.method,
                    "url": str(request.url),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        self._track_error("ValueError")

        try:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.model_dump(),
            )
        except NameError:
            return {"error": str(exc), "status_code": 400}

    async def _handle_runtime_error(
        self, request: "Request", exc: RuntimeError, request_id: str
    ) -> "JSONResponse":
        """Handle runtime errors (system/infrastructure issues).

        Args:
            request: FastAPI request object
            exc: Runtime error
            request_id: Request tracking ID

        Returns:
            Standardized runtime error response
        """
        if self.log_errors:
            logger.error(
                f"Runtime error in {request.method} {request.url}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": self._get_client_ip(request),
                },
                exc_info=self.include_trace,
            )

        error_response = ErrorResponse(
            error="RuntimeError",
            message="A system error occurred while processing your request",
            details={"request_id": request_id, "error_type": "RuntimeError"},
        )

        if self.debug:
            error_response.details.update(
                {
                    "method": request.method,
                    "url": str(request.url),
                    "original_error": str(exc),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        if self.include_trace:
            error_response.details["trace"] = traceback.format_exc()

        self._track_error("RuntimeError")

        try:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(),
            )
        except NameError:
            return {"error": "Runtime error", "status_code": 500}

    async def _handle_activity_already_exists_error(
        self, request: "Request", exc: ActivityAlreadyExistsError, request_id: str
    ) -> "JSONResponse":
        """Handle activity already exists domain errors.

        Args:
            request: FastAPI request object
            exc: Activity already exists error
            request_id: Request tracking ID

        Returns:
            Standardized conflict error response
        """
        if self.log_errors:
            logger.warning(
                f"Activity already exists error in {request.method} {request.url}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "field": exc.field,
                    "value": exc.value,
                    "client_ip": self._get_client_ip(request),
                },
            )

        error_response = ErrorResponse(
            error="ActivityAlreadyExists",
            detail=str(exc),
            details={
                "request_id": request_id,
                "field": exc.field,
                "value": exc.value,
                "error_type": "ActivityAlreadyExistsError"
            },
        )

        if self.debug:
            error_response.details.update(
                {
                    "method": request.method,
                    "url": str(request.url),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        self._track_error("ActivityAlreadyExistsError")

        try:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=error_response.model_dump(),
            )
        except NameError:
            return {"error": str(exc), "status_code": 409}

    async def _handle_unexpected_error(
        self, request: "Request", exc: Exception, request_id: str
    ) -> "JSONResponse":
        """Handle unexpected/unhandled errors.

        Args:
            request: FastAPI request object
            exc: Unexpected exception
            request_id: Request tracking ID

        Returns:
            Standardized unexpected error response
        """
        if self.log_errors:
            logger.error(
                f"Unexpected error in {request.method} {request.url}: {exc.__class__.__name__}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "exception_type": exc.__class__.__name__,
                    "client_ip": self._get_client_ip(request),
                    "user_agent": request.headers.get("user-agent"),
                },
                exc_info=True,  # Always include full trace for unexpected errors
            )

        error_response = ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred while processing your request",
            details={"request_id": request_id, "error_type": exc.__class__.__name__},
        )

        if self.debug:
            error_response.details.update(
                {
                    "method": request.method,
                    "url": str(request.url),
                    "original_error": str(exc),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        if self.include_trace:
            error_response.details["trace"] = traceback.format_exc()

        self._track_error(exc.__class__.__name__)

        try:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(),
            )
        except NameError:
            return {"error": "Internal server error", "status_code": 500}

    def _get_client_ip(self, request: "Request") -> str:
        """Extract client IP address from request.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check for forwarded headers (load balancer/proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host

        return "unknown"

    def _track_error(self, error_type: str) -> None:
        """Track error for monitoring and metrics.

        Args:
            error_type: Type of error that occurred
        """
        if not self.enable_monitoring:
            return

        # Update error counts
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_errors[error_type] = datetime.utcnow()

    def get_error_stats(self) -> dict[str, Any]:
        """Get error statistics for monitoring.

        Returns:
            Dictionary with error statistics
        """
        return {
            "error_counts": self.error_counts.copy(),
            "last_errors": {k: v.isoformat() for k, v in self.last_errors.items()},
            "total_errors": sum(self.error_counts.values()),
            "unique_error_types": len(self.error_counts),
        }

    def reset_error_stats(self) -> None:
        """Reset error statistics."""
        self.error_counts.clear()
        self.last_errors.clear()


# Compatibility class for BaseHTTPMiddleware usage
class ErrorHandlingHTTPMiddleware(
    BaseHTTPMiddleware if "BaseHTTPMiddleware" in globals() else object
):
    """HTTP middleware wrapper for ErrorHandlingMiddleware."""

    def __init__(
        self,
        app: Any,
        debug: bool = False,
        include_trace: bool = False,
        log_errors: bool = True,
        enable_monitoring: bool = True,
    ) -> None:
        """Initialize HTTP middleware wrapper.

        Args:
            app: FastAPI application
            debug: Enable debug mode
            include_trace: Include stack traces
            log_errors: Enable error logging
            enable_monitoring: Enable error monitoring
        """
        if "BaseHTTPMiddleware" in globals():
            super().__init__(app)

        self.error_handler = ErrorHandlingMiddleware(
            app=app,
            debug=debug,
            include_trace=include_trace,
            log_errors=log_errors,
            enable_monitoring=enable_monitoring,
        )

    async def dispatch(self, request: "Request", call_next: Callable) -> "Response":
        """Dispatch request through error handling middleware.

        Args:
            request: FastAPI request
            call_next: Next handler in chain

        Returns:
            Response with error handling
        """
        return await self.error_handler(request, call_next)


# Factory function for easy middleware creation
def create_error_handling_middleware(
    debug: bool = False,
    include_trace: bool = False,
    log_errors: bool = True,
    enable_monitoring: bool = True,
) -> type:
    """Create error handling middleware class with configuration.

    Args:
        debug: Enable debug mode
        include_trace: Include stack traces in responses
        log_errors: Enable error logging
        enable_monitoring: Enable error monitoring

    Returns:
        Configured middleware class
    """

    class ConfiguredErrorHandlingMiddleware:
        def __init__(self, app: Any):
            self.error_handler = ErrorHandlingMiddleware(
                app=app,
                debug=debug,
                include_trace=include_trace,
                log_errors=log_errors,
                enable_monitoring=enable_monitoring,
            )

        async def __call__(self, request: "Request", call_next: Callable) -> "Response":
            return await self.error_handler(request, call_next)

    return ConfiguredErrorHandlingMiddleware
