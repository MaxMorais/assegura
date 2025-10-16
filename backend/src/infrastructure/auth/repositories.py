"""Repository interfaces for authentication entities.

Defines repository contracts for Tenant and Consultant entities following
DDD repository pattern and constitutional requirements.
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from ...domain.base import Repository
from .models import Consultant, ConsultantRole, Tenant, TenantStatus


class TenantRepository(Repository[Tenant], ABC):
    """Repository interface for Tenant aggregate."""

    @abstractmethod
    async def find_by_subdomain(self, subdomain: str) -> Optional[Tenant]:
        """Find tenant by subdomain.

        Args:
            subdomain: Tenant subdomain to search for

        Returns:
            Tenant if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_active_tenants(self) -> list[Tenant]:
        """Find all active tenants.

        Returns:
            List of active tenants
        """
        pass

    @abstractmethod
    async def find_by_status(self, status: TenantStatus) -> list[Tenant]:
        """Find tenants by status.

        Args:
            status: Tenant status to filter by

        Returns:
            List of tenants with specified status
        """
        pass

    @abstractmethod
    async def exists_by_subdomain(self, subdomain: str) -> bool:
        """Check if tenant exists with given subdomain.

        Args:
            subdomain: Subdomain to check

        Returns:
            True if tenant exists
        """
        pass


class ConsultantRepository(Repository[Consultant], ABC):
    """Repository interface for Consultant entity."""

    @abstractmethod
    async def find_by_email(self, email: str, tenant_id: UUID) -> Optional[Consultant]:
        """Find consultant by email within tenant.

        Args:
            email: Consultant email
            tenant_id: Tenant ID to search within

        Returns:
            Consultant if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_tenant(self, tenant_id: UUID) -> list[Consultant]:
        """Find all consultants for a tenant.

        Args:
            tenant_id: Tenant ID to search within

        Returns:
            List of consultants in the tenant
        """
        pass

    @abstractmethod
    async def find_active_by_tenant(self, tenant_id: UUID) -> list[Consultant]:
        """Find active consultants for a tenant.

        Args:
            tenant_id: Tenant ID to search within

        Returns:
            List of active consultants in the tenant
        """
        pass

    @abstractmethod
    async def find_by_role(
        self, role: ConsultantRole, tenant_id: UUID
    ) -> list[Consultant]:
        """Find consultants by role within tenant.

        Args:
            role: Consultant role to filter by
            tenant_id: Tenant ID to search within

        Returns:
            List of consultants with specified role
        """
        pass

    @abstractmethod
    async def exists_by_email(self, email: str, tenant_id: UUID) -> bool:
        """Check if consultant exists with email in tenant.

        Args:
            email: Email to check
            tenant_id: Tenant ID to check within

        Returns:
            True if consultant exists
        """
        pass

    @abstractmethod
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count consultants in tenant.

        Args:
            tenant_id: Tenant ID to count within

        Returns:
            Number of consultants in tenant
        """
        pass

    @abstractmethod
    async def count_by_role(self, role: ConsultantRole, tenant_id: UUID) -> int:
        """Count consultants by role within tenant.

        Args:
            role: Role to count
            tenant_id: Tenant ID to count within

        Returns:
            Number of consultants with specified role
        """
        pass
