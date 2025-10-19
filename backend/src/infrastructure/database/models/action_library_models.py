"""
Action Library Database Models

SQLAlchemy models for action library management in the ERPNext test automation framework.
Provides comprehensive data persistence for actions, classifications, execution metrics,
versioning, and relationships with proper BDD support and search optimization.
"""

import os
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

# Conditional imports for database compatibility
# Use String(36) for both testing and production to ensure compatibility
from sqlalchemy import JSON as JSONType
from sqlalchemy import String as UUIDType

def uuid_column():
    return UUIDType(36)  # UUIDs are 36 characters

def uuid_default():
    return str(uuid4())

from sqlalchemy.orm import relationship

from .base import (
    AuditMixin,
    BaseModel,
    TimestampMixin,
)


class ActionLibraryModel(BaseModel, TimestampMixin, AuditMixin):
    """
    Action library model for reusable test automation actions.

    Represents individual actions that can be composed into journeys,
    with comprehensive BDD classification, parameter schemas, and execution tracking.
    """

    __tablename__ = "action_library"

    # Primary key
    id = Column(uuid_column(), primary_key=True, default=uuid_default, index=True)

    # Basic action information
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)

    # Action classification
    action_type = Column(
        String(50), nullable=False, index=True
    )  # ui_interaction, data_manipulation, verification, api_call, etc.

    bdd_step_type = Column(
        String(20), nullable=False, index=True
    )  # given, when, then, and

    category = Column(
        String(100), nullable=False, index=True
    )  # navigation, form_filling, data_entry, reporting, etc.

    # Action implementation (JSON for flexibility)
    implementation = Column(JSONType, nullable=False, default=dict)

    # Parameter and output schemas (JSON Schema format)
    parameters_schema = Column(JSONType, nullable=True, default=dict)
    expected_outputs_schema = Column(JSONType, nullable=True, default=dict)

    # Execution configuration
    default_timeout_seconds = Column(Integer, nullable=False, default=30)
    default_retry_count = Column(Integer, nullable=False, default=0)

    # Action status
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Action prerequisites and postconditions
    prerequisites = Column(JSONType, nullable=True, default=list)
    postconditions = Column(JSONType, nullable=True, default=list)

    # Tagging and metadata
    tags = Column(JSONType, nullable=True, default=list)  # Array of string tags
    action_metadata = Column(JSONType, nullable=True, default=dict)

    # ERPNext specific fields
    erpnext_doctype = Column(String(255), nullable=True, index=True)
    ui_selectors = Column(JSONType, nullable=True, default=dict)

    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=0, index=True)
    last_used_date = Column(DateTime(timezone=True), nullable=True, index=True)

    # Quality metrics
    success_rate = Column(Float, nullable=True, index=True)  # Percentage 0-100
    average_execution_time_seconds = Column(Float, nullable=True)

    # Relationships
    execution_metrics = relationship(
        "ActionExecutionMetricsModel",
        back_populates="action",
        cascade="all, delete-orphan",
        uselist=False,
    )
    versions = relationship(
        "ActionVersionModel",
        back_populates="action",
        cascade="all, delete-orphan",
        order_by="ActionVersionModel.version_number.desc()",
    )
    relationships = relationship(
        "ActionRelationshipModel",
        foreign_keys="ActionRelationshipModel.source_action_id",
        back_populates="source_action",
        cascade="all, delete-orphan",
    )
    journey_steps = relationship("JourneyStepModel", back_populates="action")
    parameters = relationship("ActionParameterModel", back_populates="action", cascade="all, delete-orphan")
    outputs = relationship("ActionOutputModel", back_populates="action", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        # Check constraints for data integrity
        CheckConstraint(
            "default_timeout_seconds > 0", name="ck_action_positive_timeout"
        ),
        CheckConstraint(
            "default_retry_count >= 0", name="ck_action_non_negative_retry"
        ),
        CheckConstraint(
            "action_type IN ('ui_interaction', 'data_manipulation', 'verification', 'api_call', 'navigation', 'setup', 'cleanup', 'wait', 'assertion', 'file_operation', 'database_operation', 'robot_framework')",
            name="ck_action_valid_action_type",
        ),
        CheckConstraint(
            "bdd_step_type IN ('given', 'when', 'then', 'and', 'but')",
            name="ck_action_valid_bdd_step_type",
        ),
        CheckConstraint(
            "category IN ('navigation', 'form_filling', 'data_entry', 'reporting', 'user_management', 'inventory', 'sales', 'purchase', 'accounting', 'hr', 'project', 'setup', 'verification', 'utility')",
            name="ck_action_valid_category",
        ),
        CheckConstraint("usage_count >= 0", name="ck_action_non_negative_usage_count"),
        CheckConstraint(
            "success_rate IS NULL OR (success_rate >= 0 AND success_rate <= 100)",
            name="ck_action_valid_success_rate",
        ),
        CheckConstraint(
            "average_execution_time_seconds IS NULL OR average_execution_time_seconds >= 0",
            name="ck_action_non_negative_execution_time",
        ),
        # Indexes for performance
        Index("ix_action_classification", "action_type", "bdd_step_type", "category"),
        Index("ix_action_erpnext_doctype", "erpnext_doctype"),
        Index("ix_action_usage_metrics", "usage_count", "last_used_date"),
        Index(
            "ix_action_quality_metrics",
            "success_rate",
            "average_execution_time_seconds",
        ),
        Index(
            "ix_action_execution_config",
            "default_timeout_seconds",
            "default_retry_count",
        ),
        Index("ix_action_status_active", "is_active", "created_at"),
        # JSON indexes for search and filtering
        Index("ix_action_implementation_gin", "implementation", postgresql_using="gin"),
        Index(
            "ix_action_parameters_schema_gin",
            "parameters_schema",
            postgresql_using="gin",
        ),
        Index(
            "ix_action_expected_outputs_gin",
            "expected_outputs_schema",
            postgresql_using="gin",
        ),
        Index("ix_action_prerequisites_gin", "prerequisites", postgresql_using="gin"),
        Index("ix_action_postconditions_gin", "postconditions", postgresql_using="gin"),
        Index("ix_action_tags_gin", "tags", postgresql_using="gin"),
        Index("ix_action_metadata_gin", "action_metadata", postgresql_using="gin"),
        Index("ix_action_ui_selectors_gin", "ui_selectors", postgresql_using="gin"),
        # Text search indexes
        Index(
            "ix_action_name_text",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index(
            "ix_action_description_text",
            "description",
            postgresql_using="gin",
            postgresql_ops={"description": "gin_trgm_ops"},
        ),
    )

    def __repr__(self):
        return f"<ActionLibrary(id={self.id}, name='{self.name}', type='{self.action_type}')>"


class ActionExecutionMetricsModel(BaseModel, TimestampMixin):
    """
    Action execution metrics model for tracking performance and reliability.

    Stores aggregated execution statistics for actions to support
    optimization, reliability analysis, and performance monitoring.
    """

    __tablename__ = "action_execution_metrics"

    # Primary key
    id = Column(uuid_column(), primary_key=True, default=uuid_default, index=True)

    # Foreign key
    action_id = Column(
        uuid_column(),
        ForeignKey("action_library.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One-to-one relationship
    )

    # Execution statistics
    total_executions = Column(Integer, nullable=False, default=0)
    successful_executions = Column(Integer, nullable=False, default=0)
    failed_executions = Column(Integer, nullable=False, default=0)

    # Timing statistics
    average_duration_seconds = Column(Float, nullable=False, default=0.0)
    min_duration_seconds = Column(Float, nullable=True)
    max_duration_seconds = Column(Float, nullable=True)

    # Performance trends
    last_execution_date = Column(DateTime(timezone=True), nullable=True, index=True)
    last_success_date = Column(DateTime(timezone=True), nullable=True, index=True)
    last_failure_date = Column(DateTime(timezone=True), nullable=True, index=True)

    # Failure analysis
    common_failure_reasons = Column(JSONType, nullable=True, default=list)
    failure_patterns = Column(JSONType, nullable=True, default=dict)

    # Performance analysis
    performance_trends = Column(JSONType, nullable=True, default=dict)
    resource_usage_stats = Column(JSONType, nullable=True, default=dict)

    # Reliability metrics
    reliability_score = Column(Float, nullable=True)  # 0-100 calculated score
    stability_rating = Column(
        String(20), nullable=True, index=True
    )  # stable, unstable, unreliable

    # Relationships
    action = relationship("ActionLibraryModel", back_populates="execution_metrics")

    # Table constraints
    __table_args__ = (
        # Check constraints
        CheckConstraint("total_executions >= 0", name="ck_metrics_non_negative_total"),
        CheckConstraint(
            "successful_executions >= 0", name="ck_metrics_non_negative_successful"
        ),
        CheckConstraint(
            "failed_executions >= 0", name="ck_metrics_non_negative_failed"
        ),
        CheckConstraint(
            "total_executions = successful_executions + failed_executions",
            name="ck_metrics_execution_sum",
        ),
        CheckConstraint(
            "average_duration_seconds >= 0", name="ck_metrics_non_negative_avg_duration"
        ),
        CheckConstraint(
            "min_duration_seconds IS NULL OR min_duration_seconds >= 0",
            name="ck_metrics_non_negative_min_duration",
        ),
        CheckConstraint(
            "max_duration_seconds IS NULL OR max_duration_seconds >= 0",
            name="ck_metrics_non_negative_max_duration",
        ),
        CheckConstraint(
            "min_duration_seconds IS NULL OR max_duration_seconds IS NULL OR min_duration_seconds <= max_duration_seconds",
            name="ck_metrics_valid_duration_range",
        ),
        CheckConstraint(
            "reliability_score IS NULL OR (reliability_score >= 0 AND reliability_score <= 100)",
            name="ck_metrics_valid_reliability_score",
        ),
        CheckConstraint(
            "stability_rating IS NULL OR stability_rating IN ('stable', 'unstable', 'unreliable', 'unknown')",
            name="ck_metrics_valid_stability_rating",
        ),
        # Indexes
        Index("ix_metrics_action", "action_id"),
        Index(
            "ix_metrics_execution_stats",
            "total_executions",
            "successful_executions",
            "failed_executions",
        ),
        Index("ix_metrics_timing", "average_duration_seconds", "last_execution_date"),
        Index("ix_metrics_reliability", "reliability_score", "stability_rating"),
        # JSON indexes
        Index(
            "ix_metrics_failure_reasons_gin",
            "common_failure_reasons",
            postgresql_using="gin",
        ),
        Index(
            "ix_metrics_failure_patterns_gin",
            "failure_patterns",
            postgresql_using="gin",
        ),
        Index(
            "ix_metrics_performance_trends_gin",
            "performance_trends",
            postgresql_using="gin",
        ),
        Index(
            "ix_metrics_resource_usage_gin",
            "resource_usage_stats",
            postgresql_using="gin",
        ),
    )

    def __repr__(self):
        return f"<ActionExecutionMetrics(action_id={self.action_id}, total={self.total_executions})>"


class ActionVersionModel(BaseModel, TimestampMixin):
    """
    Action version model for tracking action changes over time.

    Maintains version history of actions to support rollback,
    change tracking, and implementation evolution analysis.
    """

    __tablename__ = "action_versions"

    # Primary key
    id = Column(uuid_column(), primary_key=True, default=uuid_default, index=True)

    # Foreign key
    action_id = Column(
        uuid_column(),
        ForeignKey("action_library.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Version information
    version_number = Column(Integer, nullable=False, index=True)
    version_tag = Column(String(100), nullable=True)  # e.g., "v1.0.0", "stable", "beta"

    # Version content hashes for change detection
    implementation_hash = Column(String(64), nullable=False, index=True)
    parameters_schema_hash = Column(String(64), nullable=True, index=True)

    # Version metadata
    change_summary = Column(Text, nullable=True)
    change_details = Column(JSONType, nullable=True, default=dict)

    # Version status
    is_current = Column(Boolean, nullable=False, default=False, index=True)
    is_stable = Column(Boolean, nullable=False, default=False, index=True)

    # Compatibility information
    backward_compatible = Column(Boolean, nullable=True)
    breaking_changes = Column(JSONType, nullable=True, default=list)

    # Relationships
    action = relationship("ActionLibraryModel", back_populates="versions")

    # Table constraints
    __table_args__ = (
        # Unique constraint on version number within action
        UniqueConstraint(
            "action_id", "version_number", name="uq_action_version_number"
        ),
        # Check constraints
        CheckConstraint("version_number > 0", name="ck_version_positive_number"),
        # Indexes
        Index("ix_version_action_number", "action_id", "version_number"),
        Index("ix_version_hashes", "implementation_hash", "parameters_schema_hash"),
        Index("ix_version_status", "is_current", "is_stable"),
        Index("ix_version_compatibility", "backward_compatible"),
        # JSON indexes
        Index(
            "ix_version_change_details_gin", "change_details", postgresql_using="gin"
        ),
        Index(
            "ix_version_breaking_changes_gin",
            "breaking_changes",
            postgresql_using="gin",
        ),
    )

    def __repr__(self):
        return f"<ActionVersion(action_id={self.action_id}, version={self.version_number})>"


class ActionRelationshipModel(BaseModel, TimestampMixin):
    """
    Action relationship model for defining dependencies and associations.

    Tracks relationships between actions such as dependencies, sequences,
    alternatives, and hierarchical groupings for intelligent orchestration.
    """

    __tablename__ = "action_relationships"

    # Primary key
    id = Column(uuid_column(), primary_key=True, default=uuid_default, index=True)

    # Relationship endpoints
    source_action_id = Column(
        uuid_column(),
        ForeignKey("action_library.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_action_id = Column(
        uuid_column(),
        ForeignKey("action_library.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationship type and properties
    relationship_type = Column(
        String(50), nullable=False, index=True
    )  # depends_on, follows, alternative_to, part_of, conflicts_with, enhances

    relationship_strength = Column(
        String(20), nullable=False, default="medium", index=True
    )  # weak, medium, strong, required

    # Relationship metadata
    description = Column(Text, nullable=True)
    conditions = Column(
        JSONType, nullable=True, default=dict
    )  # When this relationship applies
    relationship_metadata = Column(JSONType, nullable=True, default=dict)

    # Relationship status
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Relationship context
    context_tags = Column(
        JSONType, nullable=True, default=list
    )  # Contexts where relationship applies

    # Relationships
    source_action = relationship(
        "ActionLibraryModel",
        foreign_keys=[source_action_id],
        back_populates="relationships",
    )
    target_action = relationship("ActionLibraryModel", foreign_keys=[target_action_id])

    # Table constraints
    __table_args__ = (
        # Prevent self-relationships
        CheckConstraint(
            "source_action_id != target_action_id",
            name="ck_relationship_no_self_reference",
        ),
        # Unique constraint on relationship
        UniqueConstraint(
            "source_action_id",
            "target_action_id",
            "relationship_type",
            name="uq_action_relationship",
        ),
        # Check constraints
        CheckConstraint(
            "relationship_type IN ('depends_on', 'follows', 'alternative_to', 'part_of', 'conflicts_with', 'enhances', 'supersedes', 'similar_to')",
            name="ck_relationship_valid_type",
        ),
        CheckConstraint(
            "relationship_strength IN ('weak', 'medium', 'strong', 'required')",
            name="ck_relationship_valid_strength",
        ),
        # Indexes
        Index("ix_relationship_source_target", "source_action_id", "target_action_id"),
        Index(
            "ix_relationship_type_strength",
            "relationship_type",
            "relationship_strength",
        ),
        Index("ix_relationship_active", "is_active"),
        # JSON indexes
        Index("ix_relationship_conditions_gin", "conditions", postgresql_using="gin"),
        Index("ix_relationship_metadata_gin", "relationship_metadata", postgresql_using="gin"),
        Index(
            "ix_relationship_context_tags_gin", "context_tags", postgresql_using="gin"
        ),
    )

    def __repr__(self):
        return f"<ActionRelationship(source={self.source_action_id}, target={self.target_action_id}, type='{self.relationship_type}')>"


class ActionUsageTrackingModel(BaseModel, TimestampMixin):
    """
    Action usage tracking model for detailed usage analytics.

    Tracks individual usage instances of actions within journeys
    for detailed analytics, pattern recognition, and optimization insights.
    """

    __tablename__ = "action_usage_tracking"

    # Primary key
    id = Column(uuid_column(), primary_key=True, default=uuid_default, index=True)

    # Foreign keys
    action_id = Column(
        uuid_column(),
        ForeignKey("action_library.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    journey_id = Column(
        uuid_column(),
        ForeignKey("journeys.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for standalone usage
        index=True,
    )

    # Usage context
    usage_context = Column(
        String(100), nullable=False, index=True
    )  # journey, test, manual, api
    usage_environment = Column(
        String(50), nullable=True, index=True
    )  # dev, staging, prod

    # Usage timing
    used_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Usage details
    parameters_used = Column(JSONType, nullable=True, default=dict)
    execution_result = Column(
        String(50), nullable=True, index=True
    )  # success, failure, error
    execution_duration_seconds = Column(Float, nullable=True)

    # Usage metadata
    user_agent = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    usage_metadata = Column(JSONType, nullable=True, default=dict)

    # Relationships
    action = relationship("ActionLibraryModel")
    journey = relationship("JourneyModel")

    # Table constraints
    __table_args__ = (
        # Check constraints
        CheckConstraint(
            "usage_context IN ('journey', 'test', 'manual', 'api', 'batch', 'scheduled')",
            name="ck_usage_valid_context",
        ),
        CheckConstraint(
            "usage_environment IS NULL OR usage_environment IN ('dev', 'staging', 'prod', 'test')",
            name="ck_usage_valid_environment",
        ),
        CheckConstraint(
            "execution_result IS NULL OR execution_result IN ('success', 'failure', 'error', 'timeout', 'cancelled')",
            name="ck_usage_valid_result",
        ),
        CheckConstraint(
            "execution_duration_seconds IS NULL OR execution_duration_seconds >= 0",
            name="ck_usage_non_negative_duration",
        ),
        # Indexes for analytics
        Index("ix_usage_action_time", "action_id", "used_at"),
        Index("ix_usage_journey_time", "journey_id", "used_at"),
        Index("ix_usage_context_environment", "usage_context", "usage_environment"),
        Index(
            "ix_usage_result_duration", "execution_result", "execution_duration_seconds"
        ),
        Index("ix_usage_session", "session_id", "used_at"),
        Index("ix_usage_time_partitioning", "used_at"),  # For time-based partitioning
        # JSON indexes
        Index("ix_usage_parameters_gin", "parameters_used", postgresql_using="gin"),
        Index("ix_usage_metadata_gin", "usage_metadata", postgresql_using="gin"),
    )

    def __repr__(self):
        return (
            f"<ActionUsageTracking(action_id={self.action_id}, used_at={self.used_at})>"
        )


class ActionParameterModel(BaseModel, TimestampMixin):
    """
    Action parameter model for storing action input parameters.

    Links parameters to their parent actions with full metadata support.
    """

    __tablename__ = "action_parameters"

    # Primary key
    id = Column(UUIDType(36), primary_key=True, default=uuid_default)

    # Foreign key to action
    action_id = Column(
        UUIDType(36), ForeignKey("action_library.id"), nullable=False, index=True
    )

    # Parameter definition
    name = Column(String(255), nullable=False, index=True)
    parameter_type = Column(String(50), nullable=False, index=True)  # string, number, boolean, etc.
    description = Column(Text, nullable=True)
    is_required = Column(Boolean, nullable=False, default=True, index=True)
    default_value = Column(JSONType, nullable=True)
    validation_rules = Column(JSONType, nullable=True, default=dict)
    example_values = Column(JSONType, nullable=True, default=list)

    # Relationships
    action = relationship("ActionLibraryModel", back_populates="parameters")

    # Table constraints
    __table_args__ = (
        # Unique constraint
        UniqueConstraint("action_id", "name", name="uq_action_parameter_name"),
        # Indexes
        Index("ix_action_parameter_type", "parameter_type"),
        Index("ix_action_parameter_required", "is_required"),
        # JSON indexes
        Index("ix_parameter_validation_gin", "validation_rules", postgresql_using="gin"),
        Index("ix_parameter_examples_gin", "example_values", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<ActionParameter(action_id={self.action_id}, name={self.name})>"


class ActionOutputModel(BaseModel, TimestampMixin):
    """
    Action output model for storing action output definitions.

    Defines expected outputs from action execution with validation schemas.
    """

    __tablename__ = "action_outputs"

    # Primary key
    id = Column(UUIDType(36), primary_key=True, default=uuid_default)

    # Foreign key to action
    action_id = Column(
        UUIDType(36), ForeignKey("action_library.id"), nullable=False, index=True
    )

    # Output definition
    name = Column(String(255), nullable=False, index=True)
    output_type = Column(String(50), nullable=False, index=True)  # string, number, boolean, etc.
    description = Column(Text, nullable=True)
    data_path = Column(String(500), nullable=True)  # JSON path or field reference
    validation_schema = Column(JSONType, nullable=True, default=dict)

    # Relationships
    action = relationship("ActionLibraryModel", back_populates="outputs")

    # Table constraints
    __table_args__ = (
        # Unique constraint
        UniqueConstraint("action_id", "name", name="uq_action_output_name"),
        # Indexes
        Index("ix_action_output_type", "output_type"),
        # JSON indexes
        Index("ix_output_validation_gin", "validation_schema", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<ActionOutput(action_id={self.action_id}, name={self.name})>"
