"""
Base Database Models

Base classes and mixins for SQLAlchemy models in the ERPNext test automation framework.
Provides common functionality, timestamp tracking, and standard model patterns.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import Column, DateTime, Integer, event
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, declared_attr

# For SQLite compatibility, use String for UUIDs in tests
from sqlalchemy import String as UUIDType

# Create the declarative base
Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model providing common functionality for all database models.
    """

    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name if not explicitly set."""
        return cls.__name__.lower()

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary representation."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Handle UUID serialization
            if isinstance(value, UUID):
                value = str(value)
            # Handle datetime serialization
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update model instance from dictionary data."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """Generate string representation of model instance."""
        if hasattr(self, "id"):
            return f"<{self.__class__.__name__}(id={self.id})>"
        return f"<{self.__class__.__name__}()>"


class TimestampMixin:
    """
    Mixin class for adding created_at and updated_at timestamp fields.
    Automatically manages timestamp values on insert and update operations.
    """

    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        index=True,
    )


class SoftDeleteMixin:
    """
    Mixin class for soft delete functionality.
    Adds deleted_at timestamp field for soft delete operations.
    """

    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark the record as soft deleted."""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None


class AuditMixin:
    """
    Mixin class for audit trail functionality.
    Tracks who created and last modified the record.
    """

    created_by = Column(UUIDType(36), nullable=True, index=True)
    updated_by = Column(UUIDType(36), nullable=True, index=True)

    def set_created_by(self, user_id: UUID) -> None:
        """Set the user who created the record."""
        self.created_by = user_id

    def set_updated_by(self, user_id: UUID) -> None:
        """Set the user who last updated the record."""
        self.updated_by = user_id


class VersionMixin:
    """
    Mixin class for optimistic locking using version numbers.
    """

    version = Column("version", Integer, nullable=False, default=1)

    def increment_version(self) -> None:
        """Increment the version number."""
        self.version += 1


# Event listeners for automatic timestamp management
@event.listens_for(TimestampMixin, "before_insert", propagate=True)
def set_created_timestamp(mapper, connection, target):
    """Set created_at timestamp on insert."""
    target.created_at = datetime.now(timezone.utc)
    target.updated_at = datetime.now(timezone.utc)


@event.listens_for(TimestampMixin, "before_update", propagate=True)
def set_updated_timestamp(mapper, connection, target):
    """Set updated_at timestamp on update."""
    target.updated_at = datetime.now(timezone.utc)


# Event listeners for audit trail management
@event.listens_for(AuditMixin, "before_insert", propagate=True)
def set_audit_created(mapper, connection, target):
    """Set audit fields on insert."""
    # In a real application, this would get the current user from context
    # For now, we'll leave it as None and set it in the application layer
    pass


@event.listens_for(AuditMixin, "before_update", propagate=True)
def set_audit_updated(mapper, connection, target):
    """Set audit fields on update."""
    # In a real application, this would get the current user from context
    # For now, we'll leave it as None and set it in the application layer
    pass


# Event listeners for version management
@event.listens_for(VersionMixin, "before_update", propagate=True)
def increment_version_on_update(mapper, connection, target):
    """Increment version number on update."""
    target.increment_version()


def get_model_by_tablename(table_name: str) -> type[BaseModel] | None:
    """
    Get model class by table name.

    Args:
        table_name: Name of the database table

    Returns:
        Model class if found, None otherwise
    """
    for model_class in Base.registry._class_registry.values():
        if (
            hasattr(model_class, "__tablename__")
            and model_class.__tablename__ == table_name
        ):
            return model_class
    return None


def create_all_tables(engine) -> None:
    """
    Create all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine) -> None:
    """
    Drop all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.drop_all(bind=engine)
