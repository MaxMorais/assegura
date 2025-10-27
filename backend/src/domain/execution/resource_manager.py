"""Resource manager for cloud execution resource allocation and monitoring."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ResourceType(str, Enum):
    """Types of execution resources."""
    
    CPU = "cpu"  # CPU cores
    MEMORY = "memory"  # RAM in MB
    STORAGE = "storage"  # Disk storage in MB
    NETWORK = "network"  # Network bandwidth in Mbps
    BROWSER_SESSION = "browser_session"  # Browser automation sessions


class ResourceUsage(BaseModel):
    """Current resource usage information."""
    
    resource_type: ResourceType = Field(..., description="Type of resource")
    total_available: int = Field(..., ge=0, description="Total available resources")
    currently_used: int = Field(0, ge=0, description="Currently allocated resources")
    reserved: int = Field(0, ge=0, description="Reserved for queued executions")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def get_available(self) -> int:
        """Get available resources (not used or reserved)."""
        return self.total_available - self.currently_used - self.reserved
    
    def get_utilization_percent(self) -> float:
        """Get resource utilization percentage."""
        if self.total_available == 0:
            return 0.0
        return (self.currently_used / self.total_available) * 100.0
    
    def can_allocate(self, amount: int) -> bool:
        """Check if requested amount can be allocated."""
        return self.get_available() >= amount
    
    def allocate(self, amount: int) -> None:
        """Allocate resources.
        
        Args:
            amount: Amount to allocate
            
        Raises:
            ValueError: If insufficient resources available
        """
        if not self.can_allocate(amount):
            raise ValueError(
                f"Insufficient {self.resource_type.value} resources. "
                f"Available: {self.get_available()}, Requested: {amount}"
            )
        self.currently_used += amount
        self.timestamp = datetime.utcnow()
    
    def reserve(self, amount: int) -> None:
        """Reserve resources for future use.
        
        Args:
            amount: Amount to reserve
            
        Raises:
            ValueError: If insufficient resources available
        """
        if self.get_available() < amount:
            raise ValueError(
                f"Insufficient {self.resource_type.value} resources for reservation. "
                f"Available: {self.get_available()}, Requested: {amount}"
            )
        self.reserved += amount
        self.timestamp = datetime.utcnow()
    
    def release(self, amount: int) -> None:
        """Release allocated resources.
        
        Args:
            amount: Amount to release
        """
        self.currently_used = max(0, self.currently_used - amount)
        self.timestamp = datetime.utcnow()
    
    def unreserve(self, amount: int) -> None:
        """Unreserve resources.
        
        Args:
            amount: Amount to unreserve
        """
        self.reserved = max(0, self.reserved - amount)
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "resource_type": self.resource_type.value,
            "total_available": self.total_available,
            "currently_used": self.currently_used,
            "reserved": self.reserved,
            "available": self.get_available(),
            "utilization_percent": round(self.get_utilization_percent(), 2),
            "timestamp": self.timestamp.isoformat(),
        }


class ResourcePool(BaseModel):
    """Pool of execution resources."""
    
    id: UUID = Field(default_factory=uuid4, description="Pool identifier")
    name: str = Field(..., description="Pool name")
    resources: Dict[ResourceType, ResourceUsage] = Field(
        default_factory=dict,
        description="Resource usage by type"
    )
    max_concurrent_executions: int = Field(
        10,
        ge=1,
        le=100,
        description="Maximum concurrent test executions"
    )
    current_executions: int = Field(
        0,
        ge=0,
        description="Currently running executions"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_resource(self, resource_type: ResourceType, total_available: int) -> None:
        """Add or update resource in pool.
        
        Args:
            resource_type: Type of resource
            total_available: Total available amount
        """
        self.resources[resource_type] = ResourceUsage(
            resource_type=resource_type,
            total_available=total_available
        )
    
    def get_resource(self, resource_type: ResourceType) -> Optional[ResourceUsage]:
        """Get resource usage information.
        
        Args:
            resource_type: Type of resource
            
        Returns:
            ResourceUsage if resource exists, None otherwise
        """
        return self.resources.get(resource_type)
    
    def can_allocate_execution(self) -> bool:
        """Check if a new execution can be started."""
        return self.current_executions < self.max_concurrent_executions
    
    def start_execution(self) -> None:
        """Increment current execution count."""
        if not self.can_allocate_execution():
            raise ValueError("Maximum concurrent executions reached")
        self.current_executions += 1
    
    def complete_execution(self) -> None:
        """Decrement current execution count."""
        self.current_executions = max(0, self.current_executions - 1)
    
    def get_overall_utilization(self) -> float:
        """Get overall resource pool utilization percentage."""
        if not self.resources:
            return 0.0
        
        total_utilization = sum(
            r.get_utilization_percent() for r in self.resources.values()
        )
        return total_utilization / len(self.resources)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "resources": {
                rt.value: ru.to_dict()
                for rt, ru in self.resources.items()
            },
            "max_concurrent_executions": self.max_concurrent_executions,
            "current_executions": self.current_executions,
            "overall_utilization_percent": round(self.get_overall_utilization(), 2),
            "created_at": self.created_at.isoformat(),
        }


class ResourceManager:
    """Manages execution resource pools and allocation.
    
    Provides:
    - Resource pool management
    - Resource allocation and deallocation
    - Resource usage monitoring
    - Execution capacity management
    """
    
    def __init__(self):
        """Initialize ResourceManager."""
        self._pools: Dict[UUID, ResourcePool] = {}
        self._default_pool: Optional[ResourcePool] = None
    
    def create_pool(
        self,
        name: str,
        cpu_cores: int = 16,
        memory_mb: int = 32768,
        storage_mb: int = 102400,
        network_mbps: int = 1000,
        browser_sessions: int = 20,
        max_concurrent: int = 10
    ) -> ResourcePool:
        """Create a new resource pool.
        
        Args:
            name: Pool name
            cpu_cores: Total CPU cores available
            memory_mb: Total memory in MB
            storage_mb: Total storage in MB
            network_mbps: Network bandwidth in Mbps
            browser_sessions: Maximum browser sessions
            max_concurrent: Maximum concurrent executions
            
        Returns:
            Created ResourcePool
        """
        pool = ResourcePool(name=name, max_concurrent_executions=max_concurrent)
        
        # Add resources to pool
        pool.add_resource(ResourceType.CPU, cpu_cores)
        pool.add_resource(ResourceType.MEMORY, memory_mb)
        pool.add_resource(ResourceType.STORAGE, storage_mb)
        pool.add_resource(ResourceType.NETWORK, network_mbps)
        pool.add_resource(ResourceType.BROWSER_SESSION, browser_sessions)
        
        self._pools[pool.id] = pool
        
        # Set as default if first pool
        if self._default_pool is None:
            self._default_pool = pool
        
        return pool
    
    def get_pool(self, pool_id: UUID) -> Optional[ResourcePool]:
        """Get resource pool by ID.
        
        Args:
            pool_id: Pool identifier
            
        Returns:
            ResourcePool if found, None otherwise
        """
        return self._pools.get(pool_id)
    
    def get_default_pool(self) -> Optional[ResourcePool]:
        """Get the default resource pool."""
        return self._default_pool
    
    def list_pools(self) -> List[ResourcePool]:
        """Get all resource pools."""
        return list(self._pools.values())
    
    def allocate_resources(
        self,
        cpu_cores: int,
        memory_mb: int,
        browser_sessions: int = 1,
        pool_id: Optional[UUID] = None
    ) -> UUID:
        """Allocate resources for execution.
        
        Args:
            cpu_cores: CPU cores needed
            memory_mb: Memory needed in MB
            browser_sessions: Browser sessions needed
            pool_id: Specific pool to use (uses default if None)
            
        Returns:
            Pool ID where resources were allocated
            
        Raises:
            ValueError: If insufficient resources or pool not found
        """
        # Get pool
        if pool_id:
            pool = self.get_pool(pool_id)
            if not pool:
                raise ValueError(f"Pool not found: {pool_id}")
        else:
            pool = self.get_default_pool()
            if not pool:
                raise ValueError("No default pool available")
        
        # Check if execution can be started
        if not pool.can_allocate_execution():
            raise ValueError("Maximum concurrent executions reached")
        
        # Allocate resources
        cpu_resource = pool.get_resource(ResourceType.CPU)
        if cpu_resource:
            cpu_resource.allocate(cpu_cores)
        
        memory_resource = pool.get_resource(ResourceType.MEMORY)
        if memory_resource:
            memory_resource.allocate(memory_mb)
        
        session_resource = pool.get_resource(ResourceType.BROWSER_SESSION)
        if session_resource:
            session_resource.allocate(browser_sessions)
        
        # Increment execution count
        pool.start_execution()
        
        return pool.id
    
    def release_resources(
        self,
        cpu_cores: int,
        memory_mb: int,
        browser_sessions: int = 1,
        pool_id: Optional[UUID] = None
    ) -> None:
        """Release allocated resources.
        
        Args:
            cpu_cores: CPU cores to release
            memory_mb: Memory to release in MB
            browser_sessions: Browser sessions to release
            pool_id: Pool to release from (uses default if None)
        """
        # Get pool
        if pool_id:
            pool = self.get_pool(pool_id)
            if not pool:
                return  # Silently ignore if pool not found
        else:
            pool = self.get_default_pool()
            if not pool:
                return
        
        # Release resources
        cpu_resource = pool.get_resource(ResourceType.CPU)
        if cpu_resource:
            cpu_resource.release(cpu_cores)
        
        memory_resource = pool.get_resource(ResourceType.MEMORY)
        if memory_resource:
            memory_resource.release(memory_mb)
        
        session_resource = pool.get_resource(ResourceType.BROWSER_SESSION)
        if session_resource:
            session_resource.release(browser_sessions)
        
        # Decrement execution count
        pool.complete_execution()
    
    def get_available_capacity(self, pool_id: Optional[UUID] = None) -> Dict[str, int]:
        """Get available capacity in pool.
        
        Args:
            pool_id: Pool to check (uses default if None)
            
        Returns:
            Dictionary of available resources by type
        """
        if pool_id:
            pool = self.get_pool(pool_id)
        else:
            pool = self.get_default_pool()
        
        if not pool:
            return {}
        
        return {
            rt.value: ru.get_available()
            for rt, ru in pool.resources.items()
        }
    
    def get_utilization_stats(self, pool_id: Optional[UUID] = None) -> Dict:
        """Get resource utilization statistics.
        
        Args:
            pool_id: Pool to check (uses default if None)
            
        Returns:
            Dictionary with utilization statistics
        """
        if pool_id:
            pool = self.get_pool(pool_id)
        else:
            pool = self.get_default_pool()
        
        if not pool:
            return {}
        
        return {
            "pool_id": str(pool.id),
            "pool_name": pool.name,
            "current_executions": pool.current_executions,
            "max_executions": pool.max_concurrent_executions,
            "execution_utilization_percent": (
                (pool.current_executions / pool.max_concurrent_executions) * 100.0
                if pool.max_concurrent_executions > 0
                else 0.0
            ),
            "overall_utilization_percent": pool.get_overall_utilization(),
            "resources": {
                rt.value: {
                    "total": ru.total_available,
                    "used": ru.currently_used,
                    "reserved": ru.reserved,
                    "available": ru.get_available(),
                    "utilization_percent": ru.get_utilization_percent(),
                }
                for rt, ru in pool.resources.items()
            },
        }


# Global resource manager instance
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get or create the global resource manager singleton.
    
    Returns:
        ResourceManager singleton instance
    """
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
        # Create default pool
        _resource_manager.create_pool(
            name="default",
            cpu_cores=16,
            memory_mb=32768,
            storage_mb=102400,
            network_mbps=1000,
            browser_sessions=20,
            max_concurrent=10
        )
    return _resource_manager
