"""Activity API module.

This module provides REST API endpoints for activity management.
"""

from .activities import router as activities_router

__all__ = ["activities_router"]
