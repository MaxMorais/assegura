"""DTO schemas for test execution operations."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExecutionPriorityLevel(int, Enum):
    """Priority levels for test execution."""
    
    CRITICAL = 1  # Highest priority
    HIGH = 3
    NORMAL = 5  # Default
    LOW = 7
    BACKGROUND = 10  # Lowest priority


class ExecutionStatusEnum(str, Enum):
    """Status of test execution."""
    
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


# Request DTOs

class ExecuteTestSuiteRequest(BaseModel):
    """Request to execute a test suite."""
    
    erpnext_instance_id: UUID = Field(..., description="ERPNext instance to test against")
    priority: ExecutionPriorityLevel = Field(
        ExecutionPriorityLevel.NORMAL,
        description="Execution priority (1-10, 1=highest)"
    )
    timeout_minutes: int = Field(
        30,
        ge=1,
        le=180,
        description="Maximum execution time in minutes"
    )
    environment_variables: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional environment variables"
    )
    parallel_execution: bool = Field(
        False,
        description="Execute tests in parallel"
    )
    max_parallel_sessions: int = Field(
        1,
        ge=1,
        le=10,
        description="Maximum parallel browser sessions"
    )
    retry_on_failure: bool = Field(
        False,
        description="Automatically retry failed tests"
    )
    max_retries: int = Field(
        0,
        ge=0,
        le=3,
        description="Maximum number of retries per test"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True


class CancelExecutionRequest(BaseModel):
    """Request to cancel an execution."""
    
    execution_id: UUID = Field(..., description="Execution to cancel")
    reason: Optional[str] = Field(None, description="Cancellation reason")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            UUID: lambda v: str(v),
        }


class RetryExecutionRequest(BaseModel):
    """Request to retry a failed execution."""
    
    execution_id: UUID = Field(..., description="Execution to retry")
    retry_failed_only: bool = Field(
        True,
        description="Only retry failed tests (not all tests)"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            UUID: lambda v: str(v),
        }


# Response DTOs

class ExecuteTestSuiteResponse(BaseModel):
    """Response from initiating test execution."""
    
    execution_id: UUID = Field(..., description="Execution identifier")
    test_suite_id: UUID = Field(..., description="Test suite being executed")
    queue_position: int = Field(..., ge=1, description="Position in execution queue")
    estimated_start: datetime = Field(..., description="Estimated start time")
    estimated_duration: int = Field(..., ge=0, description="Estimated duration in seconds")
    status: ExecutionStatusEnum = Field(
        ExecutionStatusEnum.QUEUED,
        description="Initial execution status"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class ExecutionStatusResponse(BaseModel):
    """Response with execution status details."""
    
    execution_id: UUID = Field(..., description="Execution identifier")
    test_suite_id: UUID = Field(..., description="Test suite being executed")
    status: ExecutionStatusEnum = Field(..., description="Current status")
    progress_percent: int = Field(0, ge=0, le=100, description="Progress percentage")
    started_at: Optional[datetime] = Field(None, description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    current_test: Optional[str] = Field(None, description="Currently executing test")
    tests_completed: int = Field(0, ge=0, description="Number of tests completed")
    tests_total: int = Field(0, ge=0, description="Total number of tests")
    tests_passed: int = Field(0, ge=0, description="Number of passed tests")
    tests_failed: int = Field(0, ge=0, description="Number of failed tests")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class TestResultDetail(BaseModel):
    """Detailed result for a single test case."""
    
    test_name: str = Field(..., description="Test case name")
    status: str = Field(..., description="Test status (PASS/FAIL/SKIP)")
    duration_ms: int = Field(..., ge=0, description="Execution duration in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    screenshot_url: Optional[str] = Field(None, description="Screenshot URL if captured")
    log_output: Optional[str] = Field(None, description="Test log output")
    tags: List[str] = Field(default_factory=list, description="Test tags")
    
    class Config:
        """Pydantic model configuration."""
        pass


class ExecutionMetricsResponse(BaseModel):
    """Response with execution performance metrics."""
    
    execution_id: UUID = Field(..., description="Execution identifier")
    total_duration_ms: int = Field(..., ge=0, description="Total execution duration")
    average_test_duration_ms: int = Field(..., ge=0, description="Average test duration")
    peak_memory_mb: int = Field(..., ge=0, description="Peak memory usage in MB")
    peak_cpu_percent: float = Field(..., ge=0.0, le=100.0, description="Peak CPU usage")
    erpnext_api_calls: int = Field(..., ge=0, description="Number of ERPNext API calls")
    erpnext_avg_response_ms: int = Field(..., ge=0, description="Average API response time")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            UUID: lambda v: str(v),
        }


class ExecutionResultResponse(BaseModel):
    """Response with complete execution results."""
    
    execution_id: UUID = Field(..., description="Execution identifier")
    test_suite_id: UUID = Field(..., description="Executed test suite")
    status: ExecutionStatusEnum = Field(..., description="Final execution status")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: datetime = Field(..., description="Execution completion time")
    duration_seconds: int = Field(..., ge=0, description="Total duration in seconds")
    total_tests: int = Field(..., ge=0, description="Total number of tests")
    passed_tests: int = Field(..., ge=0, description="Number of passed tests")
    failed_tests: int = Field(..., ge=0, description="Number of failed tests")
    skipped_tests: int = Field(0, ge=0, description="Number of skipped tests")
    pass_rate: float = Field(..., ge=0.0, le=100.0, description="Pass rate percentage")
    test_results: List[TestResultDetail] = Field(
        default_factory=list,
        description="Individual test results"
    )
    metrics: Optional[ExecutionMetricsResponse] = Field(
        None,
        description="Performance metrics"
    )
    log_url: Optional[str] = Field(None, description="URL to full execution log")
    report_url: Optional[str] = Field(None, description="URL to HTML report")
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class ExecutionListResponse(BaseModel):
    """Response with list of executions."""
    
    executions: List[ExecutionStatusResponse] = Field(
        default_factory=list,
        description="List of executions"
    )
    total: int = Field(0, ge=0, description="Total number of executions")
    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class QueueStatusResponse(BaseModel):
    """Response with execution queue status."""
    
    queue_length: int = Field(..., ge=0, description="Number of queued executions")
    running_count: int = Field(..., ge=0, description="Number of running executions")
    available_capacity: int = Field(..., ge=0, description="Available execution slots")
    estimated_wait_time_minutes: int = Field(
        ...,
        ge=0,
        description="Estimated wait time for new executions"
    )
    
    class Config:
        """Pydantic model configuration."""
        pass


class ResourceUsageResponse(BaseModel):
    """Response with resource usage information."""
    
    cpu_cores_used: int = Field(..., ge=0, description="CPU cores in use")
    cpu_cores_available: int = Field(..., ge=0, description="Available CPU cores")
    memory_mb_used: int = Field(..., ge=0, description="Memory in use (MB)")
    memory_mb_available: int = Field(..., ge=0, description="Available memory (MB)")
    browser_sessions_active: int = Field(..., ge=0, description="Active browser sessions")
    browser_sessions_max: int = Field(..., ge=1, description="Max browser sessions")
    utilization_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall resource utilization"
    )
    
    class Config:
        """Pydantic model configuration."""
        pass


class CancelExecutionResponse(BaseModel):
    """Response from cancelling an execution."""
    
    execution_id: UUID = Field(..., description="Cancelled execution ID")
    previous_status: ExecutionStatusEnum = Field(..., description="Status before cancellation")
    cancelled_at: datetime = Field(..., description="Cancellation timestamp")
    message: str = Field(..., description="Cancellation message")
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class ExecutionStatistics(BaseModel):
    """Execution statistics for a consultant."""
    
    total_executions: int = Field(0, ge=0, description="Total executions")
    successful_executions: int = Field(0, ge=0, description="Successful executions")
    failed_executions: int = Field(0, ge=0, description="Failed executions")
    cancelled_executions: int = Field(0, ge=0, description="Cancelled executions")
    average_duration_seconds: float = Field(0.0, ge=0.0, description="Average duration")
    average_pass_rate: float = Field(0.0, ge=0.0, le=100.0, description="Average pass rate")
    total_tests_executed: int = Field(0, ge=0, description="Total tests executed")
    
    class Config:
        """Pydantic model configuration."""
        pass


class ExecutionStatsResponse(BaseModel):
    """Response with execution statistics."""
    
    consultant_id: UUID = Field(..., description="Consultant identifier")
    period_start: datetime = Field(..., description="Statistics period start")
    period_end: datetime = Field(..., description="Statistics period end")
    statistics: ExecutionStatistics = Field(..., description="Execution statistics")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
