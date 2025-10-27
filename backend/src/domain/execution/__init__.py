"""Domain entities for test execution management."""

from .execution_queue import (
    CloudExecutionQueue,
    ExecutionPriority,
    QueueStatus,
    ResourceAllocation,
)
from .execution_result import (
    ExecutionMetrics,
    ExecutionResult,
    ExecutionStatus,
    StepTiming,
)
from .resource_manager import (
    ResourceManager,
    ResourcePool,
    ResourceType,
    ResourceUsage,
)

__all__ = [
    # Execution Queue
    "CloudExecutionQueue",
    "ExecutionPriority",
    "QueueStatus",
    "ResourceAllocation",
    # Execution Result
    "ExecutionResult",
    "ExecutionStatus",
    "ExecutionMetrics",
    "StepTiming",
    # Resource Manager
    "ResourceManager",
    "ResourcePool",
    "ResourceType",
    "ResourceUsage",
]
