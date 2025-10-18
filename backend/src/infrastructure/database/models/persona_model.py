"""Persona database model.

SQLAlchemy model for persona persistence in the ERPNext Test Automation Meta-Framework.
"""

import os
import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base

# Conditional imports for database compatibility
# Use String(36) for both testing and production to ensure compatibility
from sqlalchemy import JSON as JSONType
from sqlalchemy import String as UUIDType

def uuid_column():
    return UUIDType(36)  # UUIDs are 36 characters

def uuid_default():
    import uuid
    return str(uuid.uuid4())


class PersonaModel(Base):
    """SQLAlchemy model for persona entities."""

    __tablename__ = "personas"

    # Primary key
    id = Column(
        uuid_column(),
        primary_key=True,
        default=uuid_default(),
        nullable=False,
        index=True,
    )

    # Business fields
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique persona name",
    )

    description = Column(
        Text,
        nullable=False,
        comment="Detailed persona description and responsibilities",
    )

    erpnext_roles = Column(
        Text, nullable=False, comment="Comma-separated list of ERPNext roles"
    )

    permissions = Column(
        Text,
        nullable=True,
        default="",
        comment="Comma-separated list of permissions (format: action:resource)",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether the persona is active and available for use",
    )

    # Metadata fields
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        index=True,
        comment="Timestamp when persona was created",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
        comment="Timestamp when persona was last updated",
    )

    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Version number for optimistic concurrency control",
    )

    def __repr__(self) -> str:
        """String representation of PersonaModel."""
        return (
            f"<PersonaModel(id={self.id}, name='{self.name}', "
            f"is_active={self.is_active}, version={self.version})>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary representation.

        Returns:
            Dictionary representation of the persona model
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "erpnext_roles": self.erpnext_roles,
            "permissions": self.permissions,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
        }

    @classmethod
    def from_domain(cls, persona) -> "PersonaModel":
        """Create model from domain entity.

        Args:
            persona: Persona domain entity

        Returns:
            PersonaModel instance
        """
        # Handle UUID conversion for testing
        if os.getenv("TESTING", "false").lower() == "true":
            persona_id = str(persona.id) if persona.id else None
        else:
            persona_id = persona.id
            
        return cls(
            id=persona_id,
            name=persona.name,
            description=persona.description,
            erpnext_roles=persona.erpnext_roles_str,
            permissions=persona.permissions,
            is_active=persona.is_active,
            created_at=persona.created_at,
            updated_at=persona.updated_at,
            version=persona.version,
        )

    def to_domain(self):
        """Convert model to domain entity.

        Returns:
            Persona domain entity
        """
        from ....domain.personas import Persona

        # Parse roles from string
        roles = [role.strip() for role in self.erpnext_roles.split(",") if role.strip()]

        # Handle UUID conversion for testing
        if os.getenv("TESTING", "false").lower() == "true":
            model_id = str(self.id) if self.id else None
        else:
            model_id = self.id

        return Persona(
            id=model_id,
            name=self.name,
            description=self.description,
            erpnext_roles=roles,
            permissions=self.permissions or "",
            is_active=self.is_active,
            version=self.version,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def update_from_domain(self, persona) -> None:
        """Update model fields from domain entity.

        Args:
            persona: Persona domain entity with updated data
        """
        self.name = persona.name
        self.description = persona.description
        self.erpnext_roles = persona.erpnext_roles_str
        self.permissions = persona.permissions
        self.is_active = persona.is_active
        self.version = persona.version
        # updated_at will be automatically set by SQLAlchemy
