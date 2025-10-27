"""DTO schemas for test generation operations."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GenerationTaskStatus(str, Enum):
    """Status of a test generation task."""
    
    PENDING = "pending"  # Task is queued
    RUNNING = "running"  # Generation in progress
    COMPLETED = "completed"  # Generation successful
    FAILED = "failed"  # Generation failed


class TestFramework(str, Enum):
    """Supported test frameworks."""
    
    ROBOT_FRAMEWORK = "robot_framework"


class TestSuiteFormat(str, Enum):
    """Format for generated test suite."""
    
    ROBOT = "robot"  # Robot Framework .robot format
    JSON = "json"  # JSON representation
    YAML = "yaml"  # YAML representation


# Request DTOs

class GenerateTestsRequest(BaseModel):
    """Request to generate tests from a journey."""
    
    journey_id: UUID = Field(..., description="Journey to generate tests from")
    test_framework: TestFramework = Field(
        TestFramework.ROBOT_FRAMEWORK,
        description="Target test framework"
    )
    include_comments: bool = Field(
        True,
        description="Include documentation comments in generated tests"
    )
    include_logging: bool = Field(
        True,
        description="Include logging statements in tests"
    )
    parallel_execution: bool = Field(
        False,
        description="Generate tests for parallel execution"
    )
    test_data_inline: bool = Field(
        False,
        description="Embed test data inline vs external file"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True


class TestSuiteDownloadRequest(BaseModel):
    """Request to download a generated test suite."""
    
    test_suite_id: UUID = Field(..., description="Test suite to download")
    format: TestSuiteFormat = Field(
        TestSuiteFormat.ROBOT,
        description="Output format"
    )
    include_data: bool = Field(
        True,
        description="Include test data files"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True


class RegenerateTestsRequest(BaseModel):
    """Request to regenerate tests for a test suite."""
    
    test_suite_id: UUID = Field(..., description="Test suite to regenerate")
    preserve_customizations: bool = Field(
        False,
        description="Attempt to preserve manual customizations"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True


# Response DTOs

class GenerateTestsResponse(BaseModel):
    """Response from initiating test generation."""
    
    task_id: UUID = Field(..., description="Generation task identifier")
    journey_id: UUID = Field(..., description="Source journey")
    estimated_completion: datetime = Field(
        ...,
        description="Estimated completion time"
    )
    status: GenerationTaskStatus = Field(
        GenerationTaskStatus.PENDING,
        description="Initial task status"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class GenerationTaskStatusResponse(BaseModel):
    """Response with generation task status."""
    
    task_id: UUID = Field(..., description="Task identifier")
    status: GenerationTaskStatus = Field(..., description="Current status")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    error_message: Optional[str] = Field(None, description="Error if failed")
    test_suite_id: Optional[UUID] = Field(
        None,
        description="Generated test suite ID (if completed)"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class TestSuiteMetadata(BaseModel):
    """Metadata for a generated test suite."""
    
    id: UUID = Field(..., description="Test suite identifier")
    journey_id: UUID = Field(..., description="Source journey")
    name: str = Field(..., description="Test suite name")
    description: Optional[str] = Field(None, description="Test suite description")
    test_framework: TestFramework = Field(..., description="Test framework used")
    test_count: int = Field(0, ge=0, description="Number of test cases")
    generation_timestamp: datetime = Field(..., description="When generated")
    file_size_bytes: Optional[int] = Field(None, description="Test file size")
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class TestSuiteResponse(BaseModel):
    """Response with test suite details."""
    
    metadata: TestSuiteMetadata = Field(..., description="Test suite metadata")
    content: Optional[str] = Field(None, description="Test suite content")
    test_data: Optional[Dict] = Field(None, description="Associated test data")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class TestSuiteListResponse(BaseModel):
    """Response with list of test suites."""
    
    test_suites: List[TestSuiteMetadata] = Field(
        default_factory=list,
        description="List of test suites"
    )
    total: int = Field(0, ge=0, description="Total number of test suites")
    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class TestCaseInfo(BaseModel):
    """Information about a single test case."""
    
    name: str = Field(..., description="Test case name")
    description: Optional[str] = Field(None, description="Test case description")
    tags: List[str] = Field(default_factory=list, description="Test tags")
    estimated_duration: Optional[int] = Field(
        None,
        description="Estimated duration in seconds"
    )
    
    class Config:
        """Pydantic model configuration."""
        pass


class TestSuiteAnalysisResponse(BaseModel):
    """Response with test suite analysis."""
    
    test_suite_id: UUID = Field(..., description="Test suite identifier")
    total_tests: int = Field(..., ge=0, description="Total test cases")
    test_cases: List[TestCaseInfo] = Field(
        default_factory=list,
        description="List of test cases"
    )
    estimated_total_duration: int = Field(
        0,
        ge=0,
        description="Estimated total duration in seconds"
    )
    complexity_score: float = Field(
        0.0,
        ge=0.0,
        le=10.0,
        description="Test complexity score (0-10)"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            UUID: lambda v: str(v),
        }


class GenerationStatistics(BaseModel):
    """Statistics for test generation operations."""
    
    total_generated: int = Field(0, ge=0, description="Total tests generated")
    successful: int = Field(0, ge=0, description="Successful generations")
    failed: int = Field(0, ge=0, description="Failed generations")
    average_duration_seconds: float = Field(
        0.0,
        ge=0.0,
        description="Average generation time"
    )
    
    class Config:
        """Pydantic model configuration."""
        pass


class GenerationStatsResponse(BaseModel):
    """Response with generation statistics."""
    
    consultant_id: UUID = Field(..., description="Consultant identifier")
    period_start: datetime = Field(..., description="Statistics period start")
    period_end: datetime = Field(..., description="Statistics period end")
    statistics: GenerationStatistics = Field(
        ...,
        description="Generation statistics"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
