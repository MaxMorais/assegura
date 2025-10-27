"""Cloud Execution Queue domain entity for managing test execution scheduling."""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class QueueStatus(str, Enum):
    """Status of execution queue item."""
    
    PENDING = "pending"  # Waiting to be processed
    PROCESSING = "processing"  # Currently executing
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Execution failed
    CANCELLED = "cancelled"  # Execution cancelled


class ExecutionPriority(int, Enum):
    """Priority levels for test execution (1=highest, 10=lowest)."""
    
    CRITICAL = 1  # Critical tests, execute immediately
    HIGH = 3  # High priority tests
    NORMAL = 5  # Normal priority tests (default)
    LOW = 7  # Low priority tests
    BACKGROUND = 10  # Background/bulk tests


class ResourceAllocation(BaseModel):
    """Resource allocation for test execution."""
    
    cpu_cores: int = Field(1, ge=1, le=16, description="Number of CPU cores")
    memory_mb: int = Field(512, ge=256, le=16384, description="Memory in MB")
    max_duration_seconds: int = Field(3600, ge=60, le=86400, description="Max execution time")
    parallel_sessions: int = Field(1, ge=1, le=10, description="Parallel browser sessions")
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "cpu_cores": self.cpu_cores,
            "memory_mb": self.memory_mb,
            "max_duration_seconds": self.max_duration_seconds,
            "parallel_sessions": self.parallel_sessions,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "ResourceAllocation":
        """Create from dictionary."""
        return cls(**data)
    
    @classmethod
    def default(cls) -> "ResourceAllocation":
        """Get default resource allocation."""
        return cls()
    
    @classmethod
    def for_priority(cls, priority: ExecutionPriority) -> "ResourceAllocation":
        """Get resource allocation based on priority."""
        if priority == ExecutionPriority.CRITICAL:
            return cls(
                cpu_cores=4,
                memory_mb=2048,
                max_duration_seconds=7200,
                parallel_sessions=4
            )
        elif priority == ExecutionPriority.HIGH:
            return cls(
                cpu_cores=2,
                memory_mb=1024,
                max_duration_seconds=3600,
                parallel_sessions=2
            )
        elif priority == ExecutionPriority.NORMAL:
            return cls()  # Default
        elif priority == ExecutionPriority.LOW:
            return cls(
                cpu_cores=1,
                memory_mb=512,
                max_duration_seconds=1800,
                parallel_sessions=1
            )
        else:  # BACKGROUND
            return cls(
                cpu_cores=1,
                memory_mb=256,
                max_duration_seconds=900,
                parallel_sessions=1
            )


class CloudExecutionQueue(BaseModel):
    """Cloud Execution Queue domain entity.
    
    Manages test execution scheduling and resource allocation for cloud-based
    test execution. Supports priority-based queuing and resource management.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Unique queue item identifier")
    test_suite_id: UUID = Field(..., description="Test suite to execute")
    priority: ExecutionPriority = Field(
        ExecutionPriority.NORMAL,
        description="Execution priority (1=highest, 10=lowest)"
    )
    queue_status: QueueStatus = Field(
        QueueStatus.PENDING,
        description="Current status in queue"
    )
    allocated_resources: ResourceAllocation = Field(
        default_factory=ResourceAllocation.default,
        description="Assigned execution resources"
    )
    estimated_duration: int = Field(
        300,
        ge=1,
        le=86400,
        description="Expected runtime in seconds"
    )
    consultant_id: UUID = Field(..., description="Owning consultant")
    queued_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When item was queued"
    )
    started_at: Optional[datetime] = Field(
        None,
        description="When execution started"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="When execution completed"
    )
    retry_count: int = Field(
        0,
        ge=0,
        le=5,
        description="Number of retry attempts"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if failed"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    
    def start_processing(self) -> None:
        """Mark queue item as processing."""
        if self.queue_status != QueueStatus.PENDING:
            raise ValueError(f"Cannot start processing from status: {self.queue_status}")
        
        self.queue_status = QueueStatus.PROCESSING
        self.started_at = datetime.utcnow()
    
    def complete(self) -> None:
        """Mark queue item as completed."""
        if self.queue_status != QueueStatus.PROCESSING:
            raise ValueError(f"Cannot complete from status: {self.queue_status}")
        
        self.queue_status = QueueStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def fail(self, error_message: str) -> None:
        """Mark queue item as failed.
        
        Args:
            error_message: Description of the failure
        """
        if self.queue_status not in (QueueStatus.PENDING, QueueStatus.PROCESSING):
            raise ValueError(f"Cannot fail from status: {self.queue_status}")
        
        self.queue_status = QueueStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def cancel(self) -> None:
        """Cancel queue item."""
        if self.queue_status in (QueueStatus.COMPLETED, QueueStatus.FAILED):
            raise ValueError(f"Cannot cancel from status: {self.queue_status}")
        
        self.queue_status = QueueStatus.CANCELLED
        self.completed_at = datetime.utcnow()
    
    def retry(self) -> None:
        """Retry failed execution."""
        if self.queue_status != QueueStatus.FAILED:
            raise ValueError(f"Cannot retry from status: {self.queue_status}")
        
        if self.retry_count >= 5:
            raise ValueError("Maximum retry attempts exceeded")
        
        self.queue_status = QueueStatus.PENDING
        self.retry_count += 1
        self.started_at = None
        self.completed_at = None
        self.error_message = None
    
    def update_resources(self, resources: ResourceAllocation) -> None:
        """Update resource allocation.
        
        Args:
            resources: New resource allocation
        """
        if self.queue_status == QueueStatus.PROCESSING:
            raise ValueError("Cannot update resources during processing")
        
        self.allocated_resources = resources
    
    def increase_priority(self) -> None:
        """Increase execution priority (decrease priority value)."""
        if self.priority.value > 1:
            self.priority = ExecutionPriority(self.priority.value - 1)
            # Update resources based on new priority
            self.allocated_resources = ResourceAllocation.for_priority(self.priority)
    
    def decrease_priority(self) -> None:
        """Decrease execution priority (increase priority value)."""
        if self.priority.value < 10:
            self.priority = ExecutionPriority(self.priority.value + 1)
            # Update resources based on new priority
            self.allocated_resources = ResourceAllocation.for_priority(self.priority)
    
    def is_pending(self) -> bool:
        """Check if queue item is pending."""
        return self.queue_status == QueueStatus.PENDING
    
    def is_processing(self) -> bool:
        """Check if queue item is processing."""
        return self.queue_status == QueueStatus.PROCESSING
    
    def is_completed(self) -> bool:
        """Check if queue item is completed."""
        return self.queue_status == QueueStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if queue item is failed."""
        return self.queue_status == QueueStatus.FAILED
    
    def is_cancelled(self) -> bool:
        """Check if queue item is cancelled."""
        return self.queue_status == QueueStatus.CANCELLED
    
    def is_active(self) -> bool:
        """Check if queue item is active (pending or processing)."""
        return self.queue_status in (QueueStatus.PENDING, QueueStatus.PROCESSING)
    
    def get_duration(self) -> Optional[int]:
        """Get execution duration in seconds.
        
        Returns:
            Duration in seconds if execution has started, None otherwise
        """
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        duration = (end_time - self.started_at).total_seconds()
        return int(duration)
    
    def get_wait_time(self) -> int:
        """Get time spent waiting in queue.
        
        Returns:
            Wait time in seconds
        """
        end_time = self.started_at or datetime.utcnow()
        wait_time = (end_time - self.queued_at).total_seconds()
        return int(wait_time)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "test_suite_id": str(self.test_suite_id),
            "priority": self.priority.value,
            "queue_status": self.queue_status.value,
            "allocated_resources": self.allocated_resources.to_dict(),
            "estimated_duration": self.estimated_duration,
            "consultant_id": str(self.consultant_id),
            "queued_at": self.queued_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CloudExecutionQueue(id={self.id}, "
            f"test_suite_id={self.test_suite_id}, "
            f"priority={self.priority.value}, "
            f"status={self.queue_status.value})"
        )
