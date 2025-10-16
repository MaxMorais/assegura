"""
Journey Database Models

SQLAlchemy models for journey management in the ERPNext test automation framework.
Provides comprehensive data persistence for journeys, steps, and execution plans
with proper relationships, constraints, and JSON field support.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import BaseModel, TimestampMixin


class JourneyModel(BaseModel, TimestampMixin):
    """
    Journey model for test automation journeys.

    A journey represents a complete end-to-end test scenario that combines
    multiple actions to achieve a specific business outcome within ERPNext.
    """

    __tablename__ = "journeys"

    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Basic journey information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Associations
    persona_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Journey execution properties
    execution_status = Column(
        String(50), nullable=False, default="not_started", index=True
    )
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Journey characteristics
    estimated_duration_minutes = Column(Integer, nullable=True)
    complexity_level = Column(String(50), nullable=False, default="medium", index=True)

    # Journey content (JSON fields for flexibility)
    prerequisites = Column(JSONB, nullable=True, default=list)
    expected_outcomes = Column(JSONB, nullable=True, default=list)
    metadata = Column(JSONB, nullable=True, default=dict)

    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    persona = relationship("PersonaModel", back_populates="journeys")
    activity = relationship("ActivityModel", back_populates="journeys")
    steps = relationship(
        "JourneyStepModel",
        back_populates="journey",
        cascade="all, delete-orphan",
        order_by="JourneyStepModel.step_number",
    )
    execution_plan = relationship(
        "JourneyExecutionPlanModel",
        back_populates="journey",
        cascade="all, delete-orphan",
        uselist=False,
    )
    execution_history = relationship(
        "JourneyExecutionModel", back_populates="journey", cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        # Unique constraint on name within persona-activity combination
        UniqueConstraint(
            "name", "persona_id", "activity_id", name="uq_journey_name_persona_activity"
        ),
        # Check constraints for data integrity
        CheckConstraint(
            "estimated_duration_minutes IS NULL OR estimated_duration_minutes > 0",
            name="ck_journey_positive_duration",
        ),
        CheckConstraint(
            "complexity_level IN ('simple', 'medium', 'complex', 'advanced')",
            name="ck_journey_valid_complexity",
        ),
        CheckConstraint(
            "execution_status IN ('not_started', 'ready', 'running', 'suspended', 'completed', 'failed', 'cancelled')",
            name="ck_journey_valid_execution_status",
        ),
        CheckConstraint("usage_count >= 0", name="ck_journey_positive_usage_count"),
        # Indexes for performance
        Index("ix_journey_persona_activity", "persona_id", "activity_id"),
        Index("ix_journey_execution_status_active", "execution_status", "is_active"),
        Index(
            "ix_journey_complexity_duration",
            "complexity_level",
            "estimated_duration_minutes",
        ),
        Index("ix_journey_usage_tracking", "usage_count", "last_used_date"),
        Index("ix_journey_created_updated", "created_at", "updated_at"),
        # JSON indexes for metadata queries
        Index("ix_journey_metadata_gin", "metadata", postgresql_using="gin"),
        Index("ix_journey_prerequisites_gin", "prerequisites", postgresql_using="gin"),
        Index(
            "ix_journey_expected_outcomes_gin",
            "expected_outcomes",
            postgresql_using="gin",
        ),
    )

    def __repr__(self):
        return f"<Journey(id={self.id}, name='{self.name}', status='{self.execution_status}')>"


class JourneyStepModel(BaseModel, TimestampMixin):
    """
    Journey step model representing individual actions within a journey.

    Each step corresponds to a specific action from the action library
    with customized parameters and execution settings for the journey context.
    """

    __tablename__ = "journey_steps"

    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Foreign keys
    journey_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("journeys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("action_library.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Step properties
    step_number = Column(Integer, nullable=False, index=True)
    step_description = Column(Text, nullable=True)

    # Step execution configuration (JSON for flexibility)
    parameters = Column(JSONB, nullable=True, default=dict)
    expected_outputs = Column(JSONB, nullable=True, default=list)

    # Execution overrides
    timeout_override = Column(Integer, nullable=True)
    retry_override = Column(Integer, nullable=True)

    # Step dependencies and parallelization
    depends_on_steps = Column(
        JSONB, nullable=True, default=list
    )  # Array of step numbers
    can_run_parallel = Column(Boolean, nullable=False, default=False)
    is_critical = Column(Boolean, nullable=False, default=True)

    # Step execution status
    execution_status = Column(String(50), nullable=False, default="pending", index=True)
    execution_result = Column(JSONB, nullable=True, default=dict)
    execution_duration_seconds = Column(Float, nullable=True)
    execution_error_message = Column(Text, nullable=True)

    # Relationships
    journey = relationship("JourneyModel", back_populates="steps")
    action = relationship("ActionLibraryModel", back_populates="journey_steps")

    # Table constraints
    __table_args__ = (
        # Unique constraint on step number within journey
        UniqueConstraint("journey_id", "step_number", name="uq_journey_step_number"),
        # Check constraints
        CheckConstraint("step_number > 0", name="ck_journey_step_positive_number"),
        CheckConstraint(
            "timeout_override IS NULL OR timeout_override > 0",
            name="ck_journey_step_positive_timeout",
        ),
        CheckConstraint(
            "retry_override IS NULL OR retry_override >= 0",
            name="ck_journey_step_non_negative_retry",
        ),
        CheckConstraint(
            "execution_status IN ('pending', 'running', 'completed', 'failed', 'skipped', 'cancelled')",
            name="ck_journey_step_valid_execution_status",
        ),
        CheckConstraint(
            "execution_duration_seconds IS NULL OR execution_duration_seconds >= 0",
            name="ck_journey_step_non_negative_duration",
        ),
        # Indexes for performance
        Index("ix_journey_step_journey_order", "journey_id", "step_number"),
        Index("ix_journey_step_action_lookup", "action_id"),
        Index("ix_journey_step_execution_status", "execution_status"),
        Index("ix_journey_step_parallelization", "can_run_parallel", "is_critical"),
        # JSON indexes
        Index("ix_journey_step_parameters_gin", "parameters", postgresql_using="gin"),
        Index(
            "ix_journey_step_expected_outputs_gin",
            "expected_outputs",
            postgresql_using="gin",
        ),
        Index(
            "ix_journey_step_depends_on_gin", "depends_on_steps", postgresql_using="gin"
        ),
        Index(
            "ix_journey_step_execution_result_gin",
            "execution_result",
            postgresql_using="gin",
        ),
    )

    def __repr__(self):
        return f"<JourneyStep(id={self.id}, journey_id={self.journey_id}, step_number={self.step_number})>"


class JourneyExecutionPlanModel(BaseModel, TimestampMixin):
    """
    Journey execution plan model for optimized journey execution.

    Contains pre-calculated execution strategy, timing estimates,
    parallelization opportunities, and resource requirements.
    """

    __tablename__ = "journey_execution_plans"

    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Foreign key
    journey_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("journeys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One-to-one relationship
    )

    # Execution plan properties
    total_steps = Column(Integer, nullable=False)
    estimated_duration_seconds = Column(Integer, nullable=False)
    complexity_score = Column(Float, nullable=False, default=0.0)

    # Parallelization analysis
    can_execute_parallel = Column(Boolean, nullable=False, default=False)
    parallel_executable_steps = Column(JSONB, nullable=True, default=list)
    critical_path_steps = Column(JSONB, nullable=True, default=list)

    # Execution strategy
    rollback_points = Column(JSONB, nullable=True, default=list)
    resource_requirements = Column(JSONB, nullable=True, default=dict)

    # Plan metadata
    plan_version = Column(Integer, nullable=False, default=1)
    plan_generated_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    is_current = Column(Boolean, nullable=False, default=True, index=True)

    # Relationships
    journey = relationship("JourneyModel", back_populates="execution_plan")

    # Table constraints
    __table_args__ = (
        # Check constraints
        CheckConstraint("total_steps > 0", name="ck_execution_plan_positive_steps"),
        CheckConstraint(
            "estimated_duration_seconds > 0", name="ck_execution_plan_positive_duration"
        ),
        CheckConstraint(
            "complexity_score >= 0", name="ck_execution_plan_non_negative_complexity"
        ),
        CheckConstraint("plan_version > 0", name="ck_execution_plan_positive_version"),
        # Indexes
        Index("ix_execution_plan_journey", "journey_id"),
        Index("ix_execution_plan_current", "is_current"),
        Index(
            "ix_execution_plan_duration_complexity",
            "estimated_duration_seconds",
            "complexity_score",
        ),
        Index("ix_execution_plan_parallelization", "can_execute_parallel"),
        # JSON indexes
        Index(
            "ix_execution_plan_parallel_steps_gin",
            "parallel_executable_steps",
            postgresql_using="gin",
        ),
        Index(
            "ix_execution_plan_critical_path_gin",
            "critical_path_steps",
            postgresql_using="gin",
        ),
        Index(
            "ix_execution_plan_rollback_points_gin",
            "rollback_points",
            postgresql_using="gin",
        ),
        Index(
            "ix_execution_plan_resource_requirements_gin",
            "resource_requirements",
            postgresql_using="gin",
        ),
    )

    def __repr__(self):
        return f"<JourneyExecutionPlan(id={self.id}, journey_id={self.journey_id}, version={self.plan_version})>"


class JourneyExecutionModel(BaseModel, TimestampMixin):
    """
    Journey execution history model for tracking execution runs.

    Stores complete execution history including timing, results,
    errors, and performance metrics for analysis and optimization.
    """

    __tablename__ = "journey_executions"

    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Foreign key
    journey_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("journeys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Execution identification
    execution_number = Column(Integer, nullable=False, index=True)
    execution_batch_id = Column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )  # For batch executions

    # Execution timing
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    total_duration_seconds = Column(Float, nullable=True)

    # Execution status and results
    execution_status = Column(String(50), nullable=False, default="running", index=True)
    final_result = Column(
        String(50), nullable=True, index=True
    )  # success, failure, partial_success, cancelled

    # Step execution summary
    total_steps_executed = Column(Integer, nullable=False, default=0)
    steps_passed = Column(Integer, nullable=False, default=0)
    steps_failed = Column(Integer, nullable=False, default=0)
    steps_skipped = Column(Integer, nullable=False, default=0)

    # Execution context and results
    execution_context = Column(
        JSONB, nullable=True, default=dict
    )  # Environment, user, etc.
    execution_results = Column(JSONB, nullable=True, default=dict)  # Detailed results
    error_summary = Column(Text, nullable=True)

    # Performance metrics
    performance_metrics = Column(JSONB, nullable=True, default=dict)

    # Execution environment
    executed_by_user_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    execution_environment = Column(
        String(100), nullable=True, index=True
    )  # dev, staging, prod

    # Relationships
    journey = relationship("JourneyModel", back_populates="execution_history")
    step_executions = relationship(
        "JourneyStepExecutionModel",
        back_populates="journey_execution",
        cascade="all, delete-orphan",
    )

    # Table constraints
    __table_args__ = (
        # Unique constraint on execution number within journey
        UniqueConstraint(
            "journey_id", "execution_number", name="uq_journey_execution_number"
        ),
        # Check constraints
        CheckConstraint(
            "execution_number > 0", name="ck_journey_execution_positive_number"
        ),
        CheckConstraint(
            "total_duration_seconds IS NULL OR total_duration_seconds >= 0",
            name="ck_journey_execution_non_negative_duration",
        ),
        CheckConstraint(
            "execution_status IN ('running', 'completed', 'failed', 'cancelled', 'timeout')",
            name="ck_journey_execution_valid_status",
        ),
        CheckConstraint(
            "final_result IS NULL OR final_result IN ('success', 'failure', 'partial_success', 'cancelled', 'timeout')",
            name="ck_journey_execution_valid_result",
        ),
        CheckConstraint(
            "total_steps_executed >= 0", name="ck_journey_execution_non_negative_steps"
        ),
        CheckConstraint(
            "steps_passed >= 0 AND steps_failed >= 0 AND steps_skipped >= 0",
            name="ck_journey_execution_non_negative_step_counts",
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="ck_journey_execution_valid_completion_time",
        ),
        # Indexes
        Index("ix_journey_execution_journey_number", "journey_id", "execution_number"),
        Index("ix_journey_execution_batch", "execution_batch_id"),
        Index("ix_journey_execution_timing", "started_at", "completed_at"),
        Index("ix_journey_execution_status_result", "execution_status", "final_result"),
        Index("ix_journey_execution_environment", "execution_environment"),
        Index("ix_journey_execution_user", "executed_by_user_id"),
        Index("ix_journey_execution_performance", "total_duration_seconds"),
        # JSON indexes
        Index(
            "ix_journey_execution_context_gin",
            "execution_context",
            postgresql_using="gin",
        ),
        Index(
            "ix_journey_execution_results_gin",
            "execution_results",
            postgresql_using="gin",
        ),
        Index(
            "ix_journey_execution_performance_gin",
            "performance_metrics",
            postgresql_using="gin",
        ),
    )

    def __repr__(self):
        return f"<JourneyExecution(id={self.id}, journey_id={self.journey_id}, execution_number={self.execution_number})>"


class JourneyStepExecutionModel(BaseModel, TimestampMixin):
    """
    Journey step execution model for detailed step-level execution tracking.

    Tracks individual step execution within journey runs including
    timing, results, outputs, and error details.
    """

    __tablename__ = "journey_step_executions"

    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Foreign keys
    journey_execution_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("journey_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    journey_step_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("journey_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Step execution properties
    step_number = Column(Integer, nullable=False, index=True)
    execution_order = Column(
        Integer, nullable=False, index=True
    )  # Actual execution order (may differ from step_number for parallel execution)

    # Execution timing
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_seconds = Column(Float, nullable=True)

    # Execution status and results
    execution_status = Column(String(50), nullable=False, default="running", index=True)
    execution_result = Column(
        String(50), nullable=True, index=True
    )  # passed, failed, skipped, error

    # Step execution data
    input_parameters = Column(JSONB, nullable=True, default=dict)
    actual_outputs = Column(JSONB, nullable=True, default=dict)
    step_artifacts = Column(
        JSONB, nullable=True, default=dict
    )  # Screenshots, logs, etc.

    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True, default=dict)
    retry_count = Column(Integer, nullable=False, default=0)

    # Performance data
    performance_data = Column(JSONB, nullable=True, default=dict)

    # Relationships
    journey_execution = relationship(
        "JourneyExecutionModel", back_populates="step_executions"
    )
    journey_step = relationship("JourneyStepModel")

    # Table constraints
    __table_args__ = (
        # Unique constraint on step execution within journey execution
        UniqueConstraint(
            "journey_execution_id", "step_number", name="uq_journey_step_execution"
        ),
        # Check constraints
        CheckConstraint(
            "step_number > 0", name="ck_step_execution_positive_step_number"
        ),
        CheckConstraint("execution_order > 0", name="ck_step_execution_positive_order"),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="ck_step_execution_non_negative_duration",
        ),
        CheckConstraint(
            "execution_status IN ('running', 'completed', 'failed', 'skipped', 'timeout')",
            name="ck_step_execution_valid_status",
        ),
        CheckConstraint(
            "execution_result IS NULL OR execution_result IN ('passed', 'failed', 'skipped', 'error', 'timeout')",
            name="ck_step_execution_valid_result",
        ),
        CheckConstraint(
            "retry_count >= 0", name="ck_step_execution_non_negative_retry"
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="ck_step_execution_valid_completion_time",
        ),
        # Indexes
        Index("ix_step_execution_journey_execution", "journey_execution_id"),
        Index("ix_step_execution_journey_step", "journey_step_id"),
        Index("ix_step_execution_step_order", "step_number", "execution_order"),
        Index("ix_step_execution_timing", "started_at", "completed_at"),
        Index(
            "ix_step_execution_status_result", "execution_status", "execution_result"
        ),
        Index("ix_step_execution_performance", "duration_seconds"),
        Index("ix_step_execution_retry", "retry_count"),
        # JSON indexes
        Index(
            "ix_step_execution_input_parameters_gin",
            "input_parameters",
            postgresql_using="gin",
        ),
        Index(
            "ix_step_execution_actual_outputs_gin",
            "actual_outputs",
            postgresql_using="gin",
        ),
        Index(
            "ix_step_execution_artifacts_gin", "step_artifacts", postgresql_using="gin"
        ),
        Index(
            "ix_step_execution_error_details_gin",
            "error_details",
            postgresql_using="gin",
        ),
        Index(
            "ix_step_execution_performance_gin",
            "performance_data",
            postgresql_using="gin",
        ),
    )

    def __repr__(self):
        return f"<JourneyStepExecution(id={self.id}, step_number={self.step_number}, status='{self.execution_status}')>"
