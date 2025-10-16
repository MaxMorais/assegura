"""Database models for the ERPNext Test Framework.

This module exports all database models for easy importing.
"""

from .activity_model import ActivityModel, ActivityPersonaLinkModel

__all__ = [
    "ActivityModel",
    "ActivityPersonaLinkModel",
]
