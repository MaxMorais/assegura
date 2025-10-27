"""
Test Generation Service - Application Layer

This module implements the TestGenerationService for managing test generation
use cases and business logic. It coordinates between the domain layer and
infrastructure layer, handling test suite generation, task management, and
Robot Framework code generation.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from src.application.dto.test_generation_schemas import (
    GenerateTestsRequest,
    GenerateTestsResponse,
    GenerationStatistics,
    GenerationStatsResponse,
    GenerationTaskStatus,
    GenerationTaskStatusResponse,
    RegenerateTestsRequest,
    TestCaseInfo,
    TestFramework,
    TestSuiteAnalysisResponse,
    TestSuiteListResponse,
    TestSuiteMetadata,
    TestSuiteResponse,
)
from src.domain.test_generation.robot_generator import RobotFrameworkGenerator
from src.domain.test_generation.test_suite import TestSuite


class TestGenerationRepositoryInterface(ABC):
    """Abstract interface for test generation data persistence."""

    @abstractmethod
    async def create_test_suite(self, test_suite: TestSuite) -> TestSuite:
        """Create a new test suite."""
        pass

    @abstractmethod
    async def get_test_suite_by_id(self, test_suite_id: UUID) -> Optional[TestSuite]:
        """Get test suite by ID."""
        pass

    @abstractmethod
    async def list_test_suites(
        self,
        consultant_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[TestSuite], int]:
        """List test suites with pagination."""
        pass

    @abstractmethod
    async def update_test_suite(self, test_suite: TestSuite) -> TestSuite:
        """Update existing test suite."""
        pass

    @abstractmethod
    async def delete_test_suite(self, test_suite_id: UUID) -> bool:
        """Delete test suite."""
        pass


class GenerationTaskRepositoryInterface(ABC):
    """Abstract interface for generation task persistence."""

    @abstractmethod
    async def create_task(
        self,
        task_id: UUID,
        journey_id: UUID,
        consultant_id: UUID,
        status: GenerationTaskStatus,
    ) -> Dict:
        """Create a new generation task."""
        pass

    @abstractmethod
    async def get_task_by_id(self, task_id: UUID) -> Optional[Dict]:
        """Get task by ID."""
        pass

    @abstractmethod
    async def update_task_status(
        self,
        task_id: UUID,
        status: GenerationTaskStatus,
        progress: int,
        test_suite_id: Optional[UUID] = None,
        error_message: Optional[str] = None,
    ) -> Dict:
        """Update task status and progress."""
        pass


class TestGenerationService:
    """Service for managing test generation operations.
    
    Provides:
    - Test suite generation from journeys
    - Generation task management
    - Test suite CRUD operations
    - Test suite analysis
    - Generation statistics
    """

    def __init__(
        self,
        test_suite_repository: TestGenerationRepositoryInterface,
        task_repository: GenerationTaskRepositoryInterface,
        robot_generator: RobotFrameworkGenerator,
    ):
        """Initialize TestGenerationService.
        
        Args:
            test_suite_repository: Repository for test suite persistence
            task_repository: Repository for generation task persistence
            robot_generator: Robot Framework code generator
        """
        self._test_suite_repo = test_suite_repository
        self._task_repo = task_repository
        self._robot_generator = robot_generator

    async def generate_tests_from_journey(
        self,
        request: GenerateTestsRequest,
        consultant_id: UUID,
    ) -> GenerateTestsResponse:
        """Initiate test generation from a journey.
        
        Args:
            request: Test generation request
            consultant_id: Consultant identifier
            
        Returns:
            Response with task ID and estimated completion
        """
        # Create generation task
        task_id = uuid4()
        estimated_completion = datetime.utcnow() + timedelta(minutes=5)
        
        await self._task_repo.create_task(
            task_id=task_id,
            journey_id=request.journey_id,
            consultant_id=consultant_id,
            status=GenerationTaskStatus.PENDING,
        )
        
        # TODO: Queue async generation task (would use Celery/background worker)
        # For now, generate synchronously in background
        
        return GenerateTestsResponse(
            task_id=task_id,
            journey_id=request.journey_id,
            estimated_completion=estimated_completion,
            status=GenerationTaskStatus.PENDING,
        )

    async def get_generation_task_status(
        self,
        task_id: UUID,
    ) -> Optional[GenerationTaskStatusResponse]:
        """Get generation task status.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status response or None if not found
        """
        task = await self._task_repo.get_task_by_id(task_id)
        if not task:
            return None
        
        return GenerationTaskStatusResponse(
            task_id=task_id,
            status=GenerationTaskStatus(task["status"]),
            progress=task.get("progress", 0),
            started_at=task.get("started_at"),
            completed_at=task.get("completed_at"),
            error_message=task.get("error_message"),
            test_suite_id=task.get("test_suite_id"),
        )

    async def get_test_suite(
        self,
        test_suite_id: UUID,
        include_content: bool = True,
    ) -> Optional[TestSuiteResponse]:
        """Get test suite by ID.
        
        Args:
            test_suite_id: Test suite identifier
            include_content: Whether to include test suite content
            
        Returns:
            Test suite response or None if not found
        """
        test_suite = await self._test_suite_repo.get_test_suite_by_id(test_suite_id)
        if not test_suite:
            return None
        
        metadata = TestSuiteMetadata(
            id=test_suite.id,
            journey_id=test_suite.journey_id,
            name=test_suite.name,
            description=test_suite.description,
            test_framework=TestFramework.ROBOT_FRAMEWORK,
            test_count=len(test_suite.test_cases),
            generation_timestamp=test_suite.generated_at,
            file_size_bytes=len(test_suite.robot_code) if test_suite.robot_code else None,
        )
        
        return TestSuiteResponse(
            metadata=metadata,
            content=test_suite.robot_code if include_content else None,
            test_data=test_suite.test_data if include_content else None,
        )

    async def list_test_suites(
        self,
        consultant_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> TestSuiteListResponse:
        """List test suites for a consultant.
        
        Args:
            consultant_id: Consultant identifier
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Paginated list of test suites
        """
        offset = (page - 1) * page_size
        test_suites, total = await self._test_suite_repo.list_test_suites(
            consultant_id=consultant_id,
            offset=offset,
            limit=page_size,
        )
        
        metadata_list = [
            TestSuiteMetadata(
                id=ts.id,
                journey_id=ts.journey_id,
                name=ts.name,
                description=ts.description,
                test_framework=TestFramework.ROBOT_FRAMEWORK,
                test_count=len(ts.test_cases),
                generation_timestamp=ts.generated_at,
                file_size_bytes=len(ts.robot_code) if ts.robot_code else None,
            )
            for ts in test_suites
        ]
        
        return TestSuiteListResponse(
            test_suites=metadata_list,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def analyze_test_suite(
        self,
        test_suite_id: UUID,
    ) -> Optional[TestSuiteAnalysisResponse]:
        """Analyze test suite complexity and metrics.
        
        Args:
            test_suite_id: Test suite identifier
            
        Returns:
            Test suite analysis or None if not found
        """
        test_suite = await self._test_suite_repo.get_test_suite_by_id(test_suite_id)
        if not test_suite:
            return None
        
        # Analyze test cases
        test_cases = []
        total_duration = 0
        complexity_score = 0.0
        
        for test_case in test_suite.test_cases:
            duration = test_case.estimated_duration or 60  # Default 60s
            total_duration += duration
            
            # Calculate complexity based on steps
            step_count = len(test_case.steps)
            test_complexity = min(10.0, step_count / 5.0)  # Scale 0-10
            complexity_score += test_complexity
            
            test_cases.append(
                TestCaseInfo(
                    name=test_case.name,
                    description=test_case.description,
                    tags=test_case.tags,
                    estimated_duration=duration,
                )
            )
        
        # Average complexity
        if test_cases:
            complexity_score = complexity_score / len(test_cases)
        
        return TestSuiteAnalysisResponse(
            test_suite_id=test_suite_id,
            total_tests=len(test_cases),
            test_cases=test_cases,
            estimated_total_duration=total_duration,
            complexity_score=round(complexity_score, 2),
        )

    async def regenerate_test_suite(
        self,
        request: RegenerateTestsRequest,
        consultant_id: UUID,
    ) -> GenerateTestsResponse:
        """Regenerate an existing test suite.
        
        Args:
            request: Regeneration request
            consultant_id: Consultant identifier
            
        Returns:
            Response with new task ID
        """
        # Get existing test suite
        test_suite = await self._test_suite_repo.get_test_suite_by_id(
            request.test_suite_id
        )
        if not test_suite:
            raise ValueError(f"Test suite not found: {request.test_suite_id}")
        
        # Create new generation task
        task_id = uuid4()
        estimated_completion = datetime.utcnow() + timedelta(minutes=5)
        
        await self._task_repo.create_task(
            task_id=task_id,
            journey_id=test_suite.journey_id,
            consultant_id=consultant_id,
            status=GenerationTaskStatus.PENDING,
        )
        
        # TODO: Queue regeneration task with customization preservation
        
        return GenerateTestsResponse(
            task_id=task_id,
            journey_id=test_suite.journey_id,
            estimated_completion=estimated_completion,
            status=GenerationTaskStatus.PENDING,
        )

    async def get_generation_statistics(
        self,
        consultant_id: UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> GenerationStatsResponse:
        """Get generation statistics for a consultant.
        
        Args:
            consultant_id: Consultant identifier
            period_start: Statistics period start
            period_end: Statistics period end
            
        Returns:
            Generation statistics
        """
        # TODO: Query database for statistics
        # For now, return mock data
        
        statistics = GenerationStatistics(
            total_generated=0,
            successful=0,
            failed=0,
            average_duration_seconds=0.0,
        )
        
        return GenerationStatsResponse(
            consultant_id=consultant_id,
            period_start=period_start,
            period_end=period_end,
            statistics=statistics,
        )

    async def delete_test_suite(
        self,
        test_suite_id: UUID,
        consultant_id: UUID,
    ) -> bool:
        """Delete a test suite.
        
        Args:
            test_suite_id: Test suite identifier
            consultant_id: Consultant identifier (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        # TODO: Verify consultant owns the test suite
        return await self._test_suite_repo.delete_test_suite(test_suite_id)

    def _calculate_complexity_score(self, test_suite: TestSuite) -> float:
        """Calculate test suite complexity score.
        
        Args:
            test_suite: Test suite to analyze
            
        Returns:
            Complexity score (0-10)
        """
        if not test_suite.test_cases:
            return 0.0
        
        total_complexity = 0.0
        for test_case in test_suite.test_cases:
            # Base complexity on number of steps
            step_count = len(test_case.steps)
            test_complexity = min(10.0, step_count / 5.0)
            total_complexity += test_complexity
        
        return round(total_complexity / len(test_suite.test_cases), 2)
