"""FastAPI application bootstrap and configuration.

Main entry point for the ERPNext Test Automation Meta-Framework API,
implementing constitutional requirements and DDD architecture patterns.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any
from typing import AsyncGenerator

try:
    from fastapi import FastAPI
    from fastapi import HTTPException
    from fastapi import Request
    from fastapi import status
    from fastapi.exceptions import RequestValidationError
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import ValidationError
    import uvicorn
except ImportError as e:
    # Dependencies not installed yet - expected during initial setup
    print(f"FastAPI dependencies not installed: {e}")
    print("Run 'pip install -r requirements.txt' in backend directory")

from ..application.dto import ErrorResponse
from ..application.dto import HealthResponse
from ..application.dto import ValidationErrorResponse
from ..infrastructure.database import db_manager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
    # CORS middleware for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8501",  # Streamlit frontend
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
            "*.assegura.com",
            "*.herokuapp.com",  # For deployment
        ]
    )


def _configure_error_handlers(app: "FastAPI") -> None:
    """Configure custom error handlers.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: "Request", exc: HTTPException) -> "JSONResponse":
        """Handle HTTP exceptions with standardized format."""
        error_response = ErrorResponse(
            error=exc.__class__.__name__,
            message=str(exc.detail),
            details={"status_code": exc.status_code}
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: "Request", 
        exc: RequestValidationError
    ) -> "JSONResponse":
        """Handle Pydantic validation errors with detailed field information."""
        validation_errors = []
        
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append({
                "field": field_path,
                "message": error["msg"],
                "value": error.get("input")
            })
        
        error_response = ValidationErrorResponse(
            message="Request validation failed",
            validation_errors=validation_errors
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: "Request",
        exc: ValidationError
    ) -> "JSONResponse":
        """Handle Pydantic model validation errors."""
        validation_errors = []
        
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            validation_errors.append({
                "field": field_path,
                "message": error["msg"],
                "value": error.get("input")
            })
        
        error_response = ValidationErrorResponse(
            message="Data validation failed",
            validation_errors=validation_errors
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: "Request", exc: Exception) -> "JSONResponse":
        """Handle unexpected exceptions with logging."""
        logger.error(f"Unexpected error in {request.url}: {str(exc)}", exc_info=True)
        
        error_response = ErrorResponse(
            error="InternalServerError",
            message="An internal server error occurred",
            details={"url": str(request.url), "method": request.method}
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
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
                "git_workflow": True
            }
        }
    
    @app.get("/health", response_model=HealthResponse, summary="Health check")
    async def health_check() -> HealthResponse:
        """Health check endpoint for monitoring and load balancers."""
        # Test database connectivity
        database_status = "connected"
        try:
            with db_manager.get_sync_session() as session:
                session.execute("SELECT 1")
        except Exception as e:
            database_status = f"error: {str(e)}"
            logger.error(f"Database health check failed: {e}")
        
        # Test Redis connectivity (placeholder - to be implemented with actual Redis)
        redis_status = "not_configured"  # Will be updated when Redis is configured
        
        return HealthResponse(
            status="healthy" if database_status == "connected" else "degraded",
            version="1.0.0",
            database=database_status,
            redis=redis_status
        )
    
    # Add route includes for domain modules
    try:
        from .activities import activities_router
        app.include_router(activities_router, prefix="/api/v1")
    except ImportError:
        pass  # Activities module not ready yet
    
    # TODO: Add remaining route includes when implemented
    # app.include_router(personas.router, prefix="/personas", tags=["Personas"])
    # app.include_router(journeys.router, prefix="/journeys", tags=["Journeys"])
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
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )