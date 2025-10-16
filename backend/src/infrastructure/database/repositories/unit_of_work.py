"""Unit of Work pattern implementation for transaction management.

Implements the Unit of Work pattern for managing database transactions
and coordinating repository operations with constitutional compliance.
"""

from abc import ABC
from abc import abstractmethod
from contextlib import asynccontextmanager
from contextlib import contextmanager
from typing import Any
from typing import AsyncGenerator
from typing import Dict
from typing import Generator
from typing import Optional
from typing import Type
from uuid import UUID

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session
except ImportError as e:
    print(f"SQLAlchemy dependencies not installed: {e}")

from .base import BaseRepository
from .base import MultiTenantRepository
from .auth_repositories import create_consultant_repository
from .auth_repositories import create_tenant_repository
from ...auth.repositories import ConsultantRepository
from ...auth.repositories import TenantRepository


class UnitOfWork(ABC):
    """Abstract Unit of Work for managing database transactions."""
    
    @abstractmethod
    def __enter__(self) -> 'UnitOfWork':
        """Enter context manager."""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager with transaction handling."""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        pass


class SqlUnitOfWork(UnitOfWork):
    """SQLAlchemy implementation of Unit of Work pattern."""
    
    def __init__(self, session: Session, tenant_id: Optional[UUID] = None) -> None:
        """Initialize SQL Unit of Work.
        
        Args:
            session: SQLAlchemy session for transaction management
            tenant_id: Optional tenant ID for multi-tenant repositories
        """
        self.session = session
        self.tenant_id = tenant_id
        self._repositories: Dict[str, Any] = {}
    
    def __enter__(self) -> 'SqlUnitOfWork':
        """Enter context manager and begin transaction."""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager with proper transaction handling."""
        if exc_type is not None:
            self.rollback()
        else:
            try:
                self.commit()
            except Exception:
                self.rollback()
                raise
    
    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            self.session.commit()
        except Exception as e:
            self.rollback()
            raise RuntimeError(f"Failed to commit transaction: {e}")
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        try:
            self.session.rollback()
        except Exception as e:
            raise RuntimeError(f"Failed to rollback transaction: {e}")
    
    def flush(self) -> None:
        """Flush pending changes to database without committing."""
        try:
            self.session.flush()
        except Exception as e:
            raise RuntimeError(f"Failed to flush session: {e}")
    
    def refresh(self, entity: Any) -> None:
        """Refresh entity from database.
        
        Args:
            entity: Entity to refresh
        """
        try:
            self.session.refresh(entity)
        except Exception as e:
            raise RuntimeError(f"Failed to refresh entity: {e}")
    
    @property
    def tenants(self) -> TenantRepository:
        """Get tenant repository.
        
        Returns:
            TenantRepository instance
        """
        if 'tenants' not in self._repositories:
            self._repositories['tenants'] = create_tenant_repository(self.session)
        return self._repositories['tenants']
    
    @property 
    def consultants(self) -> ConsultantRepository:
        """Get consultant repository.
        
        Returns:
            ConsultantRepository instance
            
        Raises:
            ValueError: If tenant_id is not set for multi-tenant repository
        """
        if 'consultants' not in self._repositories:
            if not self.tenant_id:
                raise ValueError("tenant_id is required for consultant repository")
            self._repositories['consultants'] = create_consultant_repository(
                self.session, self.tenant_id
            )
        return self._repositories['consultants']
    
    def get_repository(self, repository_class: Type[BaseRepository], *args, **kwargs) -> BaseRepository:
        """Get custom repository instance.
        
        Args:
            repository_class: Repository class to instantiate
            *args: Additional arguments for repository
            **kwargs: Additional keyword arguments for repository
            
        Returns:
            Repository instance
        """
        repo_key = f"{repository_class.__name__}_{hash((args, tuple(kwargs.items())))}"
        
        if repo_key not in self._repositories:
            if issubclass(repository_class, MultiTenantRepository):
                if not self.tenant_id:
                    raise ValueError(f"tenant_id is required for multi-tenant repository {repository_class.__name__}")
                self._repositories[repo_key] = repository_class(self.session, self.tenant_id, *args, **kwargs)
            else:
                self._repositories[repo_key] = repository_class(self.session, *args, **kwargs)
        
        return self._repositories[repo_key]


class AsyncUnitOfWork(ABC):
    """Abstract async Unit of Work for managing database transactions."""
    
    @abstractmethod
    async def __aenter__(self) -> 'AsyncUnitOfWork':
        """Enter async context manager."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager with transaction handling."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        pass


class AsyncSqlUnitOfWork(AsyncUnitOfWork):
    """Async SQLAlchemy implementation of Unit of Work pattern."""
    
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None) -> None:
        """Initialize async SQL Unit of Work.
        
        Args:
            session: SQLAlchemy async session for transaction management
            tenant_id: Optional tenant ID for multi-tenant repositories
        """
        self.session = session
        self.tenant_id = tenant_id
        self._repositories: Dict[str, Any] = {}
    
    async def __aenter__(self) -> 'AsyncSqlUnitOfWork':
        """Enter async context manager."""
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager with proper transaction handling."""
        if exc_type is not None:
            await self.rollback()
        else:
            try:
                await self.commit()
            except Exception:
                await self.rollback()
                raise
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        try:
            await self.session.commit()
        except Exception as e:
            await self.rollback()
            raise RuntimeError(f"Failed to commit async transaction: {e}")
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        try:
            await self.session.rollback()
        except Exception as e:
            raise RuntimeError(f"Failed to rollback async transaction: {e}")
    
    async def flush(self) -> None:
        """Flush pending changes to database without committing."""
        try:
            await self.session.flush()
        except Exception as e:
            raise RuntimeError(f"Failed to flush async session: {e}")
    
    async def refresh(self, entity: Any) -> None:
        """Refresh entity from database.
        
        Args:
            entity: Entity to refresh
        """
        try:
            await self.session.refresh(entity)
        except Exception as e:
            raise RuntimeError(f"Failed to refresh entity: {e}")


# Factory functions for creating Unit of Work instances
@contextmanager
def create_unit_of_work(session: Session, tenant_id: Optional[UUID] = None) -> Generator[SqlUnitOfWork, None, None]:
    """Create SQL Unit of Work context manager.
    
    Args:
        session: SQLAlchemy session
        tenant_id: Optional tenant ID for multi-tenant operations
        
    Yields:
        SqlUnitOfWork instance
    """
    uow = SqlUnitOfWork(session, tenant_id)
    try:
        yield uow
    finally:
        session.close()


@asynccontextmanager
async def create_async_unit_of_work(
    session: AsyncSession, 
    tenant_id: Optional[UUID] = None
) -> AsyncGenerator[AsyncSqlUnitOfWork, None]:
    """Create async SQL Unit of Work context manager.
    
    Args:
        session: SQLAlchemy async session
        tenant_id: Optional tenant ID for multi-tenant operations
        
    Yields:
        AsyncSqlUnitOfWork instance
    """
    uow = AsyncSqlUnitOfWork(session, tenant_id)
    try:
        yield uow
    finally:
        await session.close()


class UnitOfWorkFactory:
    """Factory for creating Unit of Work instances."""
    
    def __init__(self, session_factory: callable, async_session_factory: Optional[callable] = None) -> None:
        """Initialize Unit of Work factory.
        
        Args:
            session_factory: Function that creates synchronous database sessions
            async_session_factory: Optional function that creates async database sessions
        """
        self.session_factory = session_factory
        self.async_session_factory = async_session_factory
    
    @contextmanager
    def create_uow(self, tenant_id: Optional[UUID] = None) -> Generator[SqlUnitOfWork, None, None]:
        """Create synchronous Unit of Work.
        
        Args:
            tenant_id: Optional tenant ID for multi-tenant operations
            
        Yields:
            SqlUnitOfWork instance
        """
        session = self.session_factory()
        with create_unit_of_work(session, tenant_id) as uow:
            yield uow
    
    @asynccontextmanager
    async def create_async_uow(
        self, 
        tenant_id: Optional[UUID] = None
    ) -> AsyncGenerator[AsyncSqlUnitOfWork, None]:
        """Create asynchronous Unit of Work.
        
        Args:
            tenant_id: Optional tenant ID for multi-tenant operations
            
        Yields:
            AsyncSqlUnitOfWork instance
            
        Raises:
            ValueError: If async session factory is not configured
        """
        if not self.async_session_factory:
            raise ValueError("Async session factory not configured")
        
        session = self.async_session_factory()
        async with create_async_unit_of_work(session, tenant_id) as uow:
            yield uow