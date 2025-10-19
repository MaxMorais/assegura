"""FastAPI application bootstrap and configuration.

Main entry point for the ERPNext Test Automation Meta-Framework API,
implementing constitutional requirements and DDD architecture patterns.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, Request, status
    from fastapi.exceptions import RequestValidationError
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import ValidationError
except ImportError as e:
    # Dependencies not installed yet - expected during initial setup
    print(f"FastAPI dependencies not installed: {e}")
    print("Run 'pip install -r requirements.txt' in backend directory")

from sqlalchemy import text

from src.application.dto import ErrorResponse, HealthResponse, ValidationErrorResponse
from src.infrastructure.database import db_manager
from src.api.middleware.error_handler import ErrorHandlingMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: "FastAPI") -> AsyncGenerator[None, None]:
    """Application lifespan management.

    Handles startup and shutdown events for proper resource management.
    """
    # Startup
    logger.info("Starting ERPNext Test Automation Meta-Framework API")
    logger.info("Database connection initialized")

    yield

    # Shutdown
    logger.info("Shutting down application")
    db_manager.close_connections()
    logger.info("Database connections closed")


def create_app() -> "FastAPI":
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    try:
        app = FastAPI(
            title="ERPNext Test Automation Meta-Framework API",
            description=(
                "RESTful API for managing test personas, business activities, "
                "journeys, and automated Robot Framework test generation. "
                "Built following Domain-Driven Design principles and "
                "constitutional requirements."
            ),
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
            lifespan=lifespan,
            # Constitutional compliance metadata
            contact={
                "name": "Assegura Development Team",
                "url": "https://github.com/assegura/erpnext-test-automation",
            },
            license_info={
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT",
            },
        )

        # Configure middleware
        _configure_middleware(app)

        # Configure error handlers
        _configure_error_handlers(app)

        # Configure routes
        _configure_routes(app)

        return app
    except NameError:
        raise ImportError("FastAPI not available. Install dependencies first.")


def _configure_middleware(app: "FastAPI") -> None:
    """Configure application middleware.

    Args:
        app: FastAPI application instance
    """
    # Error handling middleware (must be first)
    app.add_middleware(ErrorHandlingMiddleware, debug=True, include_trace=True)

    # CORS middleware for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8501",  # Streamlit frontend
            "http://frontend:8501",  # Docker service name
            "http://erpnext-test-frontend:8501",  # Docker container name
            "http://localhost:3000",  # Development frontend
            "https://test.assegura.com",  # Production frontend
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )

    # Trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "localhost",
            "127.0.0.1", 
            "backend",  # Docker service name
            "erpnext-test-backend",  # Docker container name
            "testserver",  # FastAPI TestClient
            "*.assegura.com",
            "*.herokuapp.com",  # For deployment
        ],
    )


def _configure_error_handlers(app: "FastAPI") -> None:
    """Configure custom error handlers.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: "Request", exc: HTTPException
    ) -> "JSONResponse":
        """Handle HTTP exceptions with standardized format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc.detail)}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: "Request", exc: RequestValidationError
    ) -> "JSONResponse":
        """Handle Pydantic validation errors with detailed field information."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: "Request", exc: Exception
    ) -> "JSONResponse":
        """Handle unexpected exceptions with logging."""
        logger.error(f"Unexpected error in {request.url}: {str(exc)}", exc_info=True)

        error_response = ErrorResponse(
            error="InternalServerError",
            message="An internal server error occurred",
            details={"url": str(request.url), "method": request.method},
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(mode='json'),
        )


def _configure_routes(app: "FastAPI") -> None:
    """Configure application routes.

    Args:
        app: FastAPI application instance
    """

    @app.get("/", summary="Root endpoint")
    async def root() -> dict[str, Any]:
        """Root endpoint with API information."""
        return {
            "name": "ERPNext Test Automation Meta-Framework API",
            "version": "1.0.0",
            "description": "RESTful API for test automation workflow management",
            "documentation": "/docs",
            "health": "/health",
            "constitutional_compliance": {
                "ddd_architecture": True,
                "python_3_11_plus": True,
                "fastapi_framework": True,
                "robot_framework_testing": True,
                "git_workflow": True,
            },
        }

    @app.get("/health", response_model=HealthResponse, summary="Health check")
    async def health_check() -> HealthResponse:
        """Health check endpoint for monitoring and load balancers."""
        # Test database connectivity
        database_status = "connected"
        try:
            with db_manager.get_sync_session() as session:
                session.execute(text("SELECT 1"))
        except Exception as e:
            database_status = f"error: {str(e)}"
            logger.error(f"Database health check failed: {e}")

        # Test Redis connectivity (placeholder - to be implemented with actual Redis)
        redis_status = "not_configured"  # Will be updated when Redis is configured

        return HealthResponse(
            status="healthy" if database_status == "connected" else "degraded",
            version="1.0.0",
            database=database_status,
            redis=redis_status,
        )

    # Add route includes for domain modules
    try:
        from .activities import router as activities_router
        logger.info(f"About to include activities router with {len(activities_router.routes)} routes")
        logger.info(f"Activities router routes: {[route.path for route in activities_router.routes]}")
        app.include_router(activities_router, prefix="/api/v1")
        logger.info("Activities router included successfully")
        logger.info(f"App routes after including activities: {len(app.routes)}")
    except Exception as e:
        logger.error(f"Failed to include activities router: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        pass  # Activities module not ready yet

    try:
        from .personas.persona_routes import router as personas_router

        app.include_router(personas_router, prefix="/api/v1")
        logger.info("Personas router included successfully")
        logger.info(f"Personas router routes: {[route.path for route in personas_router.routes]}")
        logger.info(f"App routes after including personas: {len(app.routes)}")
    except ImportError as e:
        logger.warning(f"Personas module not ready yet: {e}")
        import traceback
        logger.error(f"Full traceback for personas import: {traceback.format_exc()}")
        # Try to import with minimal dependencies
        try:
            # Import just the router definition without dependencies
            import sys
            sys.path.insert(0, '/app/src')
            from api.personas.persona_routes import router as personas_router
            app.include_router(personas_router, prefix="/api/v1")
            logger.info("Personas router included with fallback import")
        except Exception as e2:
            logger.error(f"Failed to include personas router: {e2}")
        pass  # Personas module not ready yet

    try:
        from .journeys.journey_routes import router as journeys_router
        app.include_router(journeys_router, prefix="/api/v1")
        logger.info("Journeys router included successfully")
    except Exception as e:
        logger.error(f"Failed to include journeys router: {e}")
        pass  # Journeys module not ready yet

    try:
        from .actions.action_routes import router as actions_router
        app.include_router(actions_router, prefix="/api/v1")
        logger.info("Actions router included successfully")
    except Exception as e:
        logger.error(f"Failed to include actions router: {e}")
        pass  # Actions module not ready yet

    # TODO: Add remaining route includes when implemented
    # app.include_router(test_generation.router, prefix="/test-generation", tags=["Test Generation"])


# Create application instance (only if dependencies are available)
try:
    app = create_app()
except ImportError:
    app = None  # Will be None until dependencies are installed


if __name__ == "__main__":
    if app is None:
        print("Cannot start server: FastAPI dependencies not installed")
        print("Run 'pip install -r requirements.txt' in backend directory")
        exit(1)

    # Run application in development mode
    uvicorn.run(
        "src.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
