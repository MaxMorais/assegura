"""Domain layer package.

This package contains the core domain logic following Domain-Driven Design (DDD)
principles. It includes entities, value objects, domain services, and repository
interfaces that represent the business rules and concepts.

The domain layer is technology-agnostic and contains no external dependencies
beyond basic Python libraries and Pydantic for data validation.
"""

from .base_entity import (
    AggregateRoot,
    BaseEntity,
    DomainService,
    Repository,
    ValueObject,
)

# Alias for backward compatibility
Entity = AggregateRoot

__all__ = [
    "BaseEntity",
    "AggregateRoot",
    "Entity",  # Alias for AggregateRoot
    "ValueObject",
    "DomainService",
    "Repository",
]
