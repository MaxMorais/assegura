"""Repository pattern base classes for database access.

Implements DDD repository pattern with multi-tenant support and
constitutional compliance for the ERPNext Test Automation Meta-Framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

try:
    from sqlalchemy import and_, delete, func, or_, select, update
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session
    from sqlalchemy.sql import Select
except ImportError as e:
    print(f"SQLAlchemy dependencies not installed: {e}")

from ...domain.base import Entity, Repository

# Type variables for generic repository implementations
EntityType = TypeVar("EntityType", bound=Entity)
ModelType = TypeVar("ModelType")


class BaseRepository(Repository[EntityType], Generic[EntityType, ModelType], ABC):
    """Base repository implementation with common CRUD operations.

    Provides standard repository operations following DDD patterns
    with multi-tenant support and constitutional compliance.
    """

    def __init__(self, session: Session, model_class: type[ModelType]) -> None:
        """Initialize repository with database session and model class.

        Args:
            session: SQLAlchemy session for database operations
            model_class: SQLAlchemy model class for this repository
        """
        self.session = session
        self.model_class = model_class

    @abstractmethod
    def _model_to_entity(self, model: ModelType) -> EntityType:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: SQLAlchemy model instance

        Returns:
            Domain entity instance
        """
        pass

    @abstractmethod
    def _entity_to_model(self, entity: EntityType) -> ModelType:
        """Convert domain entity to SQLAlchemy model.

        Args:
            entity: Domain entity instance

        Returns:
            SQLAlchemy model instance
        """
        pass

    async def find_by_id(self, entity_id: UUID) -> Optional[EntityType]:
        """Find entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """
        try:
            stmt = select(self.model_class).where(self.model_class.id == entity_id)
            result = self.session.execute(stmt)
            model = result.scalar_one_or_none()

            return self._model_to_entity(model) if model else None
        except Exception as e:
            raise RuntimeError(f"Failed to find entity by ID {entity_id}: {e}")

    async def find_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> list[EntityType]:
        """Find all entities with optional pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities
        """
        try:
            stmt = select(self.model_class)

            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)

            result = self.session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RuntimeError(f"Failed to find all entities: {e}")

    async def save(self, entity: EntityType) -> EntityType:
        """Save entity to database.

        Args:
            entity: Entity to save

        Returns:
            Saved entity with updated metadata
        """
        try:
            model = self._entity_to_model(entity)

            # Add or merge model
            if hasattr(model, "id") and model.id:
                model = self.session.merge(model)
            else:
                self.session.add(model)

            self.session.flush()  # Flush to get generated IDs
            return self._model_to_entity(model)
        except Exception as e:
            raise RuntimeError(f"Failed to save entity: {e}")

    async def save_all(self, entities: list[EntityType]) -> list[EntityType]:
        """Save multiple entities to database.

        Args:
            entities: List of entities to save

        Returns:
            List of saved entities
        """
        try:
            saved_entities = []
            for entity in entities:
                saved_entity = await self.save(entity)
                saved_entities.append(saved_entity)

            return saved_entities
        except Exception as e:
            raise RuntimeError(f"Failed to save entities: {e}")

    async def delete_by_id(self, entity_id: UUID) -> bool:
        """Delete entity by ID.

        Args:
            entity_id: ID of entity to delete

        Returns:
            True if entity was deleted, False if not found
        """
        try:
            stmt = delete(self.model_class).where(self.model_class.id == entity_id)
            result = self.session.execute(stmt)

            return result.rowcount > 0
        except Exception as e:
            raise RuntimeError(f"Failed to delete entity by ID {entity_id}: {e}")

    async def delete(self, entity: EntityType) -> bool:
        """Delete entity from database.

        Args:
            entity: Entity to delete

        Returns:
            True if entity was deleted
        """
        return await self.delete_by_id(entity.id)

    async def count(self) -> int:
        """Count total number of entities.

        Returns:
            Total entity count
        """
        try:
            stmt = select(func.count(self.model_class.id))
            result = self.session.execute(stmt)

            return result.scalar() or 0
        except Exception as e:
            raise RuntimeError(f"Failed to count entities: {e}")

    async def exists_by_id(self, entity_id: UUID) -> bool:
        """Check if entity exists by ID.

        Args:
            entity_id: Entity ID to check

        Returns:
            True if entity exists
        """
        try:
            stmt = select(self.model_class.id).where(self.model_class.id == entity_id)
            result = self.session.execute(stmt)

            return result.scalar_one_or_none() is not None
        except Exception as e:
            raise RuntimeError(f"Failed to check existence of entity {entity_id}: {e}")

    def _build_where_clause(self, filters: dict[str, Any]) -> Any:
        """Build WHERE clause from filter dictionary.

        Args:
            filters: Dictionary of field names and values

        Returns:
            SQLAlchemy WHERE clause
        """
        clauses = []

        for field, value in filters.items():
            if hasattr(self.model_class, field):
                column = getattr(self.model_class, field)

                if isinstance(value, list):
                    clauses.append(column.in_(value))
                elif isinstance(value, dict):
                    # Handle operators like {'gt': 10}, {'like': '%test%'}
                    for op, op_value in value.items():
                        if op == "gt":
                            clauses.append(column > op_value)
                        elif op == "gte":
                            clauses.append(column >= op_value)
                        elif op == "lt":
                            clauses.append(column < op_value)
                        elif op == "lte":
                            clauses.append(column <= op_value)
                        elif op == "like":
                            clauses.append(column.like(op_value))
                        elif op == "ilike":
                            clauses.append(column.ilike(op_value))
                        elif op == "ne":
                            clauses.append(column != op_value)
                else:
                    clauses.append(column == value)

        return and_(*clauses) if clauses else None

    async def find_by_filters(
        self,
        filters: dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> list[EntityType]:
        """Find entities by filter criteria.

        Args:
            filters: Filter criteria as field-value pairs
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field name to order by
            order_desc: Whether to order in descending order

        Returns:
            List of matching entities
        """
        try:
            stmt = select(self.model_class)

            # Apply filters
            where_clause = self._build_where_clause(filters)
            if where_clause is not None:
                stmt = stmt.where(where_clause)

            # Apply ordering
            if order_by and hasattr(self.model_class, order_by):
                column = getattr(self.model_class, order_by)
                stmt = stmt.order_by(column.desc() if order_desc else column.asc())

            # Apply pagination
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)

            result = self.session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RuntimeError(f"Failed to find entities by filters: {e}")

    async def count_by_filters(self, filters: dict[str, Any]) -> int:
        """Count entities matching filter criteria.

        Args:
            filters: Filter criteria as field-value pairs

        Returns:
            Count of matching entities
        """
        try:
            stmt = select(func.count(self.model_class.id))

            where_clause = self._build_where_clause(filters)
            if where_clause is not None:
                stmt = stmt.where(where_clause)

            result = self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            raise RuntimeError(f"Failed to count entities by filters: {e}")


class MultiTenantRepository(
    BaseRepository[EntityType, ModelType], Generic[EntityType, ModelType], ABC
):
    """Multi-tenant aware repository base class.

    Extends BaseRepository with tenant-scoped operations for data isolation
    following constitutional multi-tenant requirements.
    """

    def __init__(
        self, session: Session, model_class: type[ModelType], tenant_id: UUID
    ) -> None:
        """Initialize multi-tenant repository.

        Args:
            session: SQLAlchemy session
            model_class: SQLAlchemy model class
            tenant_id: Tenant ID for data isolation
        """
        super().__init__(session, model_class)
        self.tenant_id = tenant_id

    def _add_tenant_filter(self, stmt: Select) -> Select:
        """Add tenant filter to query statement.

        Args:
            stmt: SQLAlchemy select statement

        Returns:
            Statement with tenant filter applied
        """
        if hasattr(self.model_class, "tenant_id"):
            return stmt.where(self.model_class.tenant_id == self.tenant_id)
        return stmt

    async def find_by_id(self, entity_id: UUID) -> Optional[EntityType]:
        """Find entity by ID within tenant scope.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity if found within tenant, None otherwise
        """
        try:
            stmt = select(self.model_class).where(self.model_class.id == entity_id)
            stmt = self._add_tenant_filter(stmt)

            result = self.session.execute(stmt)
            model = result.scalar_one_or_none()

            return self._model_to_entity(model) if model else None
        except Exception as e:
            raise RuntimeError(
                f"Failed to find entity by ID {entity_id} in tenant {self.tenant_id}: {e}"
            )

    async def find_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> list[EntityType]:
        """Find all entities within tenant scope.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of tenant-scoped entities
        """
        try:
            stmt = select(self.model_class)
            stmt = self._add_tenant_filter(stmt)

            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)

            result = self.session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RuntimeError(
                f"Failed to find all entities for tenant {self.tenant_id}: {e}"
            )

    async def count(self) -> int:
        """Count entities within tenant scope.

        Returns:
            Count of tenant-scoped entities
        """
        try:
            stmt = select(func.count(self.model_class.id))
            stmt = self._add_tenant_filter(stmt)

            result = self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            raise RuntimeError(
                f"Failed to count entities for tenant {self.tenant_id}: {e}"
            )

    async def find_by_filters(
        self,
        filters: dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> list[EntityType]:
        """Find entities by filters within tenant scope.

        Args:
            filters: Filter criteria as field-value pairs
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Field name to order by
            order_desc: Whether to order in descending order

        Returns:
            List of matching tenant-scoped entities
        """
        try:
            stmt = select(self.model_class)
            stmt = self._add_tenant_filter(stmt)

            # Apply additional filters
            where_clause = self._build_where_clause(filters)
            if where_clause is not None:
                stmt = stmt.where(where_clause)

            # Apply ordering
            if order_by and hasattr(self.model_class, order_by):
                column = getattr(self.model_class, order_by)
                stmt = stmt.order_by(column.desc() if order_desc else column.asc())

            # Apply pagination
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)

            result = self.session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RuntimeError(
                f"Failed to find entities by filters for tenant {self.tenant_id}: {e}"
            )

    async def count_by_filters(self, filters: dict[str, Any]) -> int:
        """Count entities by filters within tenant scope.

        Args:
            filters: Filter criteria as field-value pairs

        Returns:
            Count of matching tenant-scoped entities
        """
        try:
            stmt = select(func.count(self.model_class.id))
            stmt = self._add_tenant_filter(stmt)

            where_clause = self._build_where_clause(filters)
            if where_clause is not None:
                stmt = stmt.where(where_clause)

            result = self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            raise RuntimeError(
                f"Failed to count entities by filters for tenant {self.tenant_id}: {e}"
            )


class AsyncBaseRepository(Repository[EntityType], Generic[EntityType, ModelType], ABC):
    """Async repository base class for high-performance operations.

    Provides async/await database operations for improved performance
    and scalability in constitutional compliance.
    """

    def __init__(self, session: AsyncSession, model_class: type[ModelType]) -> None:
        """Initialize async repository.

        Args:
            session: SQLAlchemy async session
            model_class: SQLAlchemy model class
        """
        self.session = session
        self.model_class = model_class

    @abstractmethod
    def _model_to_entity(self, model: ModelType) -> EntityType:
        """Convert SQLAlchemy model to domain entity."""
        pass

    @abstractmethod
    def _entity_to_model(self, entity: EntityType) -> ModelType:
        """Convert domain entity to SQLAlchemy model."""
        pass

    async def find_by_id(self, entity_id: UUID) -> Optional[EntityType]:
        """Find entity by ID asynchronously."""
        try:
            stmt = select(self.model_class).where(self.model_class.id == entity_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            return self._model_to_entity(model) if model else None
        except Exception as e:
            raise RuntimeError(f"Failed to find entity by ID {entity_id}: {e}")

    async def save(self, entity: EntityType) -> EntityType:
        """Save entity asynchronously."""
        try:
            model = self._entity_to_model(entity)

            if hasattr(model, "id") and model.id:
                model = await self.session.merge(model)
            else:
                self.session.add(model)

            await self.session.flush()
            return self._model_to_entity(model)
        except Exception as e:
            raise RuntimeError(f"Failed to save entity: {e}")


# Repository factory for dependency injection
class RepositoryFactory:
    """Factory for creating repository instances with proper session management."""

    def __init__(self, session_factory: callable) -> None:
        """Initialize repository factory.

        Args:
            session_factory: Function that creates database sessions
        """
        self.session_factory = session_factory

    def create_repository(self, repository_class: type, *args, **kwargs) -> Any:
        """Create repository instance with session.

        Args:
            repository_class: Repository class to instantiate
            *args: Additional arguments for repository
            **kwargs: Additional keyword arguments for repository

        Returns:
            Repository instance
        """
        session = self.session_factory()
        return repository_class(session, *args, **kwargs)
