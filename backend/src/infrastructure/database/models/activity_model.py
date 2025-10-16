"""SQLAlchemy models for activities and activity-persona links.

This module defines the database models for ERPNext business activities
and their relationships with personas.
"""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..config import Base


class ActivityModel(Base):
    """SQLAlchemy model for Activity entities.

    Represents ERPNext business activities with comprehensive
    metadata and validation rules.
    """

    __tablename__ = "activities"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic information
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)

    # ERPNext context
    erpnext_module = Column(String(100), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    target_doctype = Column(String(100), nullable=False, index=True)

    # Activity configuration
    required_fields = Column(Text)  # Comma-separated list
    validation_rules = Column(JSONB, default={})
    success_criteria = Column(Text)  # Comma-separated list

    # Execution metadata
    complexity_score = Column(Integer, nullable=False, index=True)
    estimated_duration = Column(Integer, nullable=False)  # seconds
    prerequisites = Column(Text)  # Comma-separated list
    postconditions = Column(Text)  # Comma-separated list

    # Test configuration
    test_data_requirements = Column(JSONB, default={})

    # Organization
    tags = Column(Text)  # Comma-separated list
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    version = Column(String(20), nullable=False, default="1.0.0")

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    # Relationships
    persona_links = relationship(
        "ActivityPersonaLinkModel",
        back_populates="activity",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "complexity_score >= 1 AND complexity_score <= 5",
            name="check_complexity_score",
        ),
        CheckConstraint("estimated_duration > 0", name="check_estimated_duration"),
        CheckConstraint(
            "action_type IN ('create', 'read', 'update', 'delete', 'list', 'search', 'filter', 'export', 'import', 'approve', 'reject', 'submit', 'cancel', 'duplicate', 'print', 'email', 'share', 'assign', 'comment', 'attachment', 'workflow', 'permission', 'custom')",
            name="check_action_type",
        ),
        Index("idx_activity_module_type", "erpnext_module", "action_type"),
        Index(
            "idx_activity_complexity_duration", "complexity_score", "estimated_duration"
        ),
        Index("idx_activity_active_updated", "is_active", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<ActivityModel(id={self.id}, name='{self.name}', module='{self.erpnext_module}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "erpnext_module": self.erpnext_module,
            "action_type": self.action_type,
            "target_doctype": self.target_doctype,
            "required_fields": self.required_fields,
            "validation_rules": self.validation_rules,
            "success_criteria": self.success_criteria,
            "complexity_score": self.complexity_score,
            "estimated_duration": self.estimated_duration,
            "prerequisites": self.prerequisites,
            "postconditions": self.postconditions,
            "test_data_requirements": self.test_data_requirements,
            "tags": self.tags,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ActivityPersonaLinkModel(Base):
    """SQLAlchemy model for activity-persona relationships.

    Represents the many-to-many relationship between activities
    and personas with additional metadata.
    """

    __tablename__ = "activity_persona_links"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    persona_id = Column(
        UUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Link metadata
    priority = Column(String(20), nullable=False, default="medium", index=True)
    notes = Column(Text)
    is_primary = Column(Boolean, default=False, nullable=False)
    execution_order = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    activity = relationship("ActivityModel", back_populates="persona_links")
    # Note: PersonaModel relationship would be defined in persona_model.py to avoid circular imports

    # Constraints
    __table_args__ = (
        UniqueConstraint("persona_id", "activity_id", name="uq_persona_activity"),
        CheckConstraint(
            "priority IN ('high', 'medium', 'low', 'critical')", name="check_priority"
        ),
        CheckConstraint("execution_order >= 0", name="check_execution_order"),
        Index("idx_persona_priority", "persona_id", "priority"),
        Index("idx_activity_order", "activity_id", "execution_order"),
        Index("idx_link_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ActivityPersonaLinkModel(persona_id={self.persona_id}, activity_id={self.activity_id}, priority='{self.priority}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "persona_id": str(self.persona_id),
            "activity_id": str(self.activity_id),
            "priority": self.priority,
            "notes": self.notes,
            "is_primary": self.is_primary,
            "execution_order": self.execution_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
