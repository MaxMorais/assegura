"""SQLAlchemy database models for all domain entities.

Centralized model registry for Alembic migration autogeneration
with multi-tenant support and constitutional compliance.
"""

from sqlalchemy.ext.declarative import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()

# Import all model classes to register them with SQLAlchemy
# This ensures Alembic can discover them for migration generation

# Import auth models
try:
    from ..auth.sql_models import AuthAuditLogModel, ConsultantModel, TenantModel
except ImportError:
    print("Auth SQLAlchemy models not yet implemented")

# TODO: Import domain models as they are created
# from ...domain.personas.sql_models import TestPersonaModel
# from ...domain.activities.sql_models import BusinessActivityModel
# from ...domain.journeys.sql_models import UserJourneyModel

# Export Base for use in other modules
__all__ = ["Base"]
