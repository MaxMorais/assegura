"""Execution Result domain entity for capturing test run outcomes."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Status of test execution."""
    
    QUEUED = "queued"  # Test is queued for execution
    RUNNING = "running"  # Test is currently running
    COMPLETED = "completed"  # Test completed successfully
    FAILED = "failed"  # Test execution failed
    CANCELLED = "cancelled"  # Test execution was cancelled
    TIMEOUT = "timeout"  # Test execution timed out


class StepTiming(BaseModel):
    """Timing information for individual test steps."""
    
    step_name: str = Field(..., description="Name of the test step")
    start_time: datetime = Field(..., description="Step start time")
    end_time: datetime = Field(..., description="Step end time")
    duration_ms: int = Field(..., ge=0, description="Duration in milliseconds")
    status: str = Field(..., description="Step status (PASS/FAIL/SKIP)")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "step_name": self.step_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "status": self.status,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "StepTiming":
        """Create from dictionary."""
        return cls(
            step_name=data["step_name"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            duration_ms=data["duration_ms"],
            status=data["status"],
        )


class ExecutionMetrics(BaseModel):
    """Metrics tracked during test execution."""
    
    total_duration_ms: int = Field(0, ge=0, description="Total execution duration")
    step_timings: List[StepTiming] = Field(
        default_factory=list,
        description="Individual step timings"
    )
    memory_peak_mb: Optional[int] = Field(
        None,
        ge=0,
        description="Peak memory usage in MB"
    )
    cpu_peak_percent: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Peak CPU usage percentage"
    )
    erpnext_api_calls: int = Field(
        0,
        ge=0,
        description="Number of ERPNext API calls"
    )
    erpnext_avg_response_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Average ERPNext API response time"
    )
    erpnext_max_response_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum ERPNext API response time"
    )
    
    def add_step_timing(self, timing: StepTiming) -> None:
        """Add step timing to metrics."""
        self.step_timings.append(timing)
        self.total_duration_ms += timing.duration_ms
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total_duration_ms": self.total_duration_ms,
            "step_timings": [t.to_dict() for t in self.step_timings],
            "memory_peak_mb": self.memory_peak_mb,
            "cpu_peak_percent": self.cpu_peak_percent,
            "erpnext_api_calls": self.erpnext_api_calls,
            "erpnext_avg_response_ms": self.erpnext_avg_response_ms,
            "erpnext_max_response_ms": self.erpnext_max_response_ms,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ExecutionMetrics":
        """Create from dictionary."""
        step_timings = [StepTiming.from_dict(t) for t in data.get("step_timings", [])]
        return cls(
            total_duration_ms=data.get("total_duration_ms", 0),
            step_timings=step_timings,
            memory_peak_mb=data.get("memory_peak_mb"),
            cpu_peak_percent=data.get("cpu_peak_percent"),
            erpnext_api_calls=data.get("erpnext_api_calls", 0),
            erpnext_avg_response_ms=data.get("erpnext_avg_response_ms"),
            erpnext_max_response_ms=data.get("erpnext_max_response_ms"),
        )


class ExecutionResult(BaseModel):
    """Execution Result domain entity.
    
    Captures test run outcomes and metrics from cloud execution. Tracks
    execution status, timing, pass/fail counts, and detailed error information.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Unique result identifier")
    test_suite_id: UUID = Field(..., description="Executed test suite")
    execution_status: ExecutionStatus = Field(
        ExecutionStatus.QUEUED,
        description="Current execution status"
    )
    start_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="Execution start time"
    )
    end_time: Optional[datetime] = Field(
        None,
        description="Execution completion time"
    )
    pass_count: int = Field(
        0,
        ge=0,
        description="Number of passed tests"
    )
    fail_count: int = Field(
        0,
        ge=0,
        description="Number of failed tests"
    )
    skip_count: int = Field(
        0,
        ge=0,
        description="Number of skipped tests"
    )
    execution_log: str = Field(
        "",
        description="Detailed execution output"
    )
    error_details: Dict = Field(
        default_factory=dict,
        description="Structured error information"
    )
    metrics: ExecutionMetrics = Field(
        default_factory=ExecutionMetrics,
        description="Execution metrics and timing"
    )
    consultant_id: UUID = Field(..., description="Owning consultant")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record creation time"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    
    def start_execution(self) -> None:
        """Mark execution as running."""
        if self.execution_status != ExecutionStatus.QUEUED:
            raise ValueError(f"Cannot start from status: {self.execution_status}")
        
        self.execution_status = ExecutionStatus.RUNNING
        self.start_time = datetime.utcnow()
    
    def complete_execution(self) -> None:
        """Mark execution as completed."""
        if self.execution_status != ExecutionStatus.RUNNING:
            raise ValueError(f"Cannot complete from status: {self.execution_status}")
        
        self.execution_status = ExecutionStatus.COMPLETED
        self.end_time = datetime.utcnow()
    
    def fail_execution(self, error_message: str, error_details: Optional[Dict] = None) -> None:
        """Mark execution as failed.
        
        Args:
            error_message: Description of the failure
            error_details: Structured error information (optional)
        """
        if self.execution_status not in (ExecutionStatus.QUEUED, ExecutionStatus.RUNNING):
            raise ValueError(f"Cannot fail from status: {self.execution_status}")
        
        self.execution_status = ExecutionStatus.FAILED
        self.end_time = datetime.utcnow()
        self.execution_log += f"\nERROR: {error_message}"
        if error_details:
            self.error_details.update(error_details)
    
    def cancel_execution(self) -> None:
        """Cancel execution."""
        if self.execution_status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED):
            raise ValueError(f"Cannot cancel from status: {self.execution_status}")
        
        self.execution_status = ExecutionStatus.CANCELLED
        self.end_time = datetime.utcnow()
    
    def timeout_execution(self) -> None:
        """Mark execution as timed out."""
        if self.execution_status != ExecutionStatus.RUNNING:
            raise ValueError(f"Cannot timeout from status: {self.execution_status}")
        
        self.execution_status = ExecutionStatus.TIMEOUT
        self.end_time = datetime.utcnow()
        self.execution_log += "\nERROR: Execution timed out"
    
    def add_test_result(self, passed: bool, test_name: str, duration_ms: int) -> None:
        """Add individual test result.
        
        Args:
            passed: Whether the test passed
            test_name: Name of the test
            duration_ms: Test duration in milliseconds
        """
        if passed:
            self.pass_count += 1
        else:
            self.fail_count += 1
        
        # Add step timing
        end_time = datetime.utcnow()
        start_time = end_time  # Simplified - would calculate from duration
        timing = StepTiming(
            step_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            status="PASS" if passed else "FAIL"
        )
        self.metrics.add_step_timing(timing)
    
    def append_log(self, log_message: str) -> None:
        """Append to execution log.
        
        Args:
            log_message: Log message to append
        """
        timestamp = datetime.utcnow().isoformat()
        self.execution_log += f"\n[{timestamp}] {log_message}"
    
    def update_metrics(
        self,
        memory_mb: Optional[int] = None,
        cpu_percent: Optional[float] = None,
        api_call_time_ms: Optional[int] = None
    ) -> None:
        """Update execution metrics.
        
        Args:
            memory_mb: Current memory usage
            cpu_percent: Current CPU usage
            api_call_time_ms: Latest API call response time
        """
        if memory_mb is not None:
            if self.metrics.memory_peak_mb is None or memory_mb > self.metrics.memory_peak_mb:
                self.metrics.memory_peak_mb = memory_mb
        
        if cpu_percent is not None:
            if self.metrics.cpu_peak_percent is None or cpu_percent > self.metrics.cpu_peak_percent:
                self.metrics.cpu_peak_percent = cpu_percent
        
        if api_call_time_ms is not None:
            self.metrics.erpnext_api_calls += 1
            
            # Update average response time
            if self.metrics.erpnext_avg_response_ms is None:
                self.metrics.erpnext_avg_response_ms = api_call_time_ms
            else:
                total_time = (
                    self.metrics.erpnext_avg_response_ms * (self.metrics.erpnext_api_calls - 1)
                    + api_call_time_ms
                )
                self.metrics.erpnext_avg_response_ms = int(
                    total_time / self.metrics.erpnext_api_calls
                )
            
            # Update max response time
            if (self.metrics.erpnext_max_response_ms is None 
                or api_call_time_ms > self.metrics.erpnext_max_response_ms):
                self.metrics.erpnext_max_response_ms = api_call_time_ms
    
    def get_duration_seconds(self) -> Optional[int]:
        """Get execution duration in seconds.
        
        Returns:
            Duration in seconds if execution has started, None otherwise
        """
        if not self.start_time:
            return None
        
        end_time = self.end_time or datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        return int(duration)
    
    def get_total_tests(self) -> int:
        """Get total number of tests executed.
        
        Returns:
            Total test count (pass + fail + skip)
        """
        return self.pass_count + self.fail_count + self.skip_count
    
    def get_pass_rate(self) -> float:
        """Get test pass rate as percentage.
        
        Returns:
            Pass rate percentage (0.0 to 100.0)
        """
        total = self.get_total_tests()
        if total == 0:
            return 0.0
        return (self.pass_count / total) * 100.0
    
    def is_successful(self) -> bool:
        """Check if execution was successful (all tests passed)."""
        return (
            self.execution_status == ExecutionStatus.COMPLETED
            and self.fail_count == 0
            and self.pass_count > 0
        )
    
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return self.execution_status == ExecutionStatus.RUNNING
    
    def is_finished(self) -> bool:
        """Check if execution has finished (completed, failed, cancelled, or timed out)."""
        return self.execution_status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "test_suite_id": str(self.test_suite_id),
            "execution_status": self.execution_status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "skip_count": self.skip_count,
            "execution_log": self.execution_log,
            "error_details": self.error_details,
            "metrics": self.metrics.to_dict(),
            "consultant_id": str(self.consultant_id),
            "created_at": self.created_at.isoformat(),
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExecutionResult(id={self.id}, "
            f"test_suite_id={self.test_suite_id}, "
            f"status={self.execution_status.value}, "
            f"pass={self.pass_count}, fail={self.fail_count})"
        )
