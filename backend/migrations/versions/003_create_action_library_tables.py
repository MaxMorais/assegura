"""
Create action library tables

Revision ID: 003_create_action_library_tables
Revises: 002_create_journey_tables  
Create Date: 2025-10-16 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_create_action_library_tables'
down_revision = '002_create_journey_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create action library tables with comprehensive structure and indexes."""
    
    # Enable trigram extension for text search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    # Create action_library table
    op.create_table(
        'action_library',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('bdd_step_type', sa.String(20), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('implementation', postgresql.JSONB(), nullable=False),
        sa.Column('parameters_schema', postgresql.JSONB(), nullable=True),
        sa.Column('expected_outputs_schema', postgresql.JSONB(), nullable=True),
        sa.Column('default_timeout_seconds', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('default_retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('prerequisites', postgresql.JSONB(), nullable=True),
        sa.Column('postconditions', postgresql.JSONB(), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('erpnext_doctype', sa.String(255), nullable=True),
        sa.Column('ui_selectors', postgresql.JSONB(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('average_execution_time_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Check constraints
        sa.CheckConstraint(
            "default_timeout_seconds > 0",
            name='ck_action_positive_timeout'
        ),
        sa.CheckConstraint(
            "default_retry_count >= 0",
            name='ck_action_non_negative_retry'
        ),
        sa.CheckConstraint(
            "action_type IN ('ui_interaction', 'data_manipulation', 'verification', 'api_call', 'navigation', 'setup', 'cleanup', 'wait', 'assertion', 'file_operation', 'database_operation')",
            name='ck_action_valid_action_type'
        ),
        sa.CheckConstraint(
            "bdd_step_type IN ('given', 'when', 'then', 'and', 'but')",
            name='ck_action_valid_bdd_step_type'
        ),
        sa.CheckConstraint(
            "category IN ('navigation', 'form_filling', 'data_entry', 'reporting', 'user_management', 'inventory', 'sales', 'purchase', 'accounting', 'hr', 'project', 'setup', 'verification', 'utility')",
            name='ck_action_valid_category'
        ),
        sa.CheckConstraint(
            "usage_count >= 0",
            name='ck_action_non_negative_usage_count'
        ),
        sa.CheckConstraint(
            "success_rate IS NULL OR (success_rate >= 0 AND success_rate <= 100)",
            name='ck_action_valid_success_rate'
        ),
        sa.CheckConstraint(
            "average_execution_time_seconds IS NULL OR average_execution_time_seconds >= 0",
            name='ck_action_non_negative_execution_time'
        ),
    )
    
    # Create action_execution_metrics table
    op.create_table(
        'action_execution_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('action_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('total_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_duration_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('min_duration_seconds', sa.Float(), nullable=True),
        sa.Column('max_duration_seconds', sa.Float(), nullable=True),
        sa.Column('last_execution_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failure_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('common_failure_reasons', postgresql.JSONB(), nullable=True),
        sa.Column('failure_patterns', postgresql.JSONB(), nullable=True),
        sa.Column('performance_trends', postgresql.JSONB(), nullable=True),
        sa.Column('resource_usage_stats', postgresql.JSONB(), nullable=True),
        sa.Column('reliability_score', sa.Float(), nullable=True),
        sa.Column('stability_rating', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['action_id'], ['action_library.id'], ondelete='CASCADE'),
        
        # Check constraints
        sa.CheckConstraint(
            "total_executions >= 0",
            name='ck_metrics_non_negative_total'
        ),
        sa.CheckConstraint(
            "successful_executions >= 0",
            name='ck_metrics_non_negative_successful'
        ),
        sa.CheckConstraint(
            "failed_executions >= 0",
            name='ck_metrics_non_negative_failed'
        ),
        sa.CheckConstraint(
            "total_executions = successful_executions + failed_executions",
            name='ck_metrics_execution_sum'
        ),
        sa.CheckConstraint(
            "average_duration_seconds >= 0",
            name='ck_metrics_non_negative_avg_duration'
        ),
        sa.CheckConstraint(
            "min_duration_seconds IS NULL OR min_duration_seconds >= 0",
            name='ck_metrics_non_negative_min_duration'
        ),
        sa.CheckConstraint(
            "max_duration_seconds IS NULL OR max_duration_seconds >= 0",
            name='ck_metrics_non_negative_max_duration'
        ),
        sa.CheckConstraint(
            "min_duration_seconds IS NULL OR max_duration_seconds IS NULL OR min_duration_seconds <= max_duration_seconds",
            name='ck_metrics_valid_duration_range'
        ),
        sa.CheckConstraint(
            "reliability_score IS NULL OR (reliability_score >= 0 AND reliability_score <= 100)",
            name='ck_metrics_valid_reliability_score'
        ),
        sa.CheckConstraint(
            "stability_rating IS NULL OR stability_rating IN ('stable', 'unstable', 'unreliable', 'unknown')",
            name='ck_metrics_valid_stability_rating'
        ),
    )
    
    # Create action_versions table
    op.create_table(
        'action_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('action_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_tag', sa.String(100), nullable=True),
        sa.Column('implementation_hash', sa.String(64), nullable=False),
        sa.Column('parameters_schema_hash', sa.String(64), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('change_details', postgresql.JSONB(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_stable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('backward_compatible', sa.Boolean(), nullable=True),
        sa.Column('breaking_changes', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['action_id'], ['action_library.id'], ondelete='CASCADE'),
        
        # Check constraints
        sa.CheckConstraint(
            "version_number > 0",
            name='ck_version_positive_number'
        ),
        
        # Unique constraints
        sa.UniqueConstraint('action_id', 'version_number', name='uq_action_version_number'),
    )
    
    # Create action_relationships table
    op.create_table(
        'action_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('source_action_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_action_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False),
        sa.Column('relationship_strength', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('conditions', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('context_tags', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['source_action_id'], ['action_library.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_action_id'], ['action_library.id'], ondelete='CASCADE'),
        
        # Check constraints
        sa.CheckConstraint(
            "source_action_id != target_action_id",
            name='ck_relationship_no_self_reference'
        ),
        sa.CheckConstraint(
            "relationship_type IN ('depends_on', 'follows', 'alternative_to', 'part_of', 'conflicts_with', 'enhances', 'supersedes', 'similar_to')",
            name='ck_relationship_valid_type'
        ),
        sa.CheckConstraint(
            "relationship_strength IN ('weak', 'medium', 'strong', 'required')",
            name='ck_relationship_valid_strength'
        ),
        
        # Unique constraints
        sa.UniqueConstraint('source_action_id', 'target_action_id', 'relationship_type', name='uq_action_relationship'),
    )
    
    # Create action_usage_tracking table
    op.create_table(
        'action_usage_tracking',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('action_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('journey_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('usage_context', sa.String(100), nullable=False),
        sa.Column('usage_environment', sa.String(50), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('parameters_used', postgresql.JSONB(), nullable=True),
        sa.Column('execution_result', sa.String(50), nullable=True),
        sa.Column('execution_duration_seconds', sa.Float(), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['action_id'], ['action_library.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['journey_id'], ['journeys.id'], ondelete='CASCADE'),
        
        # Check constraints
        sa.CheckConstraint(
            "usage_context IN ('journey', 'test', 'manual', 'api', 'batch', 'scheduled')",
            name='ck_usage_valid_context'
        ),
        sa.CheckConstraint(
            "usage_environment IS NULL OR usage_environment IN ('dev', 'staging', 'prod', 'test')",
            name='ck_usage_valid_environment'
        ),
        sa.CheckConstraint(
            "execution_result IS NULL OR execution_result IN ('success', 'failure', 'error', 'timeout', 'cancelled')",
            name='ck_usage_valid_result'
        ),
        sa.CheckConstraint(
            "execution_duration_seconds IS NULL OR execution_duration_seconds >= 0",
            name='ck_usage_non_negative_duration'
        ),
    )
    
    # Create indexes for action_library table
    op.create_index('ix_action_library_id', 'action_library', ['id'])
    op.create_index('ix_action_library_name', 'action_library', ['name'])
    op.create_index('ix_action_library_action_type', 'action_library', ['action_type'])
    op.create_index('ix_action_library_bdd_step_type', 'action_library', ['bdd_step_type'])
    op.create_index('ix_action_library_category', 'action_library', ['category'])
    op.create_index('ix_action_library_is_active', 'action_library', ['is_active'])
    op.create_index('ix_action_library_erpnext_doctype', 'action_library', ['erpnext_doctype'])
    op.create_index('ix_action_library_usage_count', 'action_library', ['usage_count'])
    op.create_index('ix_action_library_last_used_date', 'action_library', ['last_used_date'])
    op.create_index('ix_action_library_success_rate', 'action_library', ['success_rate'])
    op.create_index('ix_action_library_created_at', 'action_library', ['created_at'])
    op.create_index('ix_action_library_updated_at', 'action_library', ['updated_at'])
    
    # Composite indexes for action_library
    op.create_index('ix_action_classification', 'action_library', ['action_type', 'bdd_step_type', 'category'])
    op.create_index('ix_action_usage_metrics', 'action_library', ['usage_count', 'last_used_date'])
    op.create_index('ix_action_quality_metrics', 'action_library', ['success_rate', 'average_execution_time_seconds'])
    op.create_index('ix_action_execution_config', 'action_library', ['default_timeout_seconds', 'default_retry_count'])
    op.create_index('ix_action_status_active', 'action_library', ['is_active', 'created_at'])
    
    # JSON indexes for action_library
    op.create_index('ix_action_implementation_gin', 'action_library', ['implementation'], postgresql_using='gin')
    op.create_index('ix_action_parameters_schema_gin', 'action_library', ['parameters_schema'], postgresql_using='gin')
    op.create_index('ix_action_expected_outputs_gin', 'action_library', ['expected_outputs_schema'], postgresql_using='gin')
    op.create_index('ix_action_prerequisites_gin', 'action_library', ['prerequisites'], postgresql_using='gin')
    op.create_index('ix_action_postconditions_gin', 'action_library', ['postconditions'], postgresql_using='gin')
    op.create_index('ix_action_tags_gin', 'action_library', ['tags'], postgresql_using='gin')
    op.create_index('ix_action_metadata_gin', 'action_library', ['metadata'], postgresql_using='gin')
    op.create_index('ix_action_ui_selectors_gin', 'action_library', ['ui_selectors'], postgresql_using='gin')
    
    # Text search indexes for action_library
    op.create_index('ix_action_name_text', 'action_library', ['name'], postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.create_index('ix_action_description_text', 'action_library', ['description'], postgresql_using='gin', postgresql_ops={'description': 'gin_trgm_ops'})
    
    # Create indexes for action_execution_metrics table
    op.create_index('ix_metrics_id', 'action_execution_metrics', ['id'])
    op.create_index('ix_metrics_action_id', 'action_execution_metrics', ['action_id'])
    op.create_index('ix_metrics_last_execution_date', 'action_execution_metrics', ['last_execution_date'])
    op.create_index('ix_metrics_last_success_date', 'action_execution_metrics', ['last_success_date'])
    op.create_index('ix_metrics_last_failure_date', 'action_execution_metrics', ['last_failure_date'])
    op.create_index('ix_metrics_stability_rating', 'action_execution_metrics', ['stability_rating'])
    
    # Composite indexes for action_execution_metrics
    op.create_index('ix_metrics_execution_stats', 'action_execution_metrics', ['total_executions', 'successful_executions', 'failed_executions'])
    op.create_index('ix_metrics_timing', 'action_execution_metrics', ['average_duration_seconds', 'last_execution_date'])
    op.create_index('ix_metrics_reliability', 'action_execution_metrics', ['reliability_score', 'stability_rating'])
    
    # JSON indexes for action_execution_metrics
    op.create_index('ix_metrics_failure_reasons_gin', 'action_execution_metrics', ['common_failure_reasons'], postgresql_using='gin')
    op.create_index('ix_metrics_failure_patterns_gin', 'action_execution_metrics', ['failure_patterns'], postgresql_using='gin')
    op.create_index('ix_metrics_performance_trends_gin', 'action_execution_metrics', ['performance_trends'], postgresql_using='gin')
    op.create_index('ix_metrics_resource_usage_gin', 'action_execution_metrics', ['resource_usage_stats'], postgresql_using='gin')
    
    # Create indexes for action_versions table
    op.create_index('ix_version_id', 'action_versions', ['id'])
    op.create_index('ix_version_action_id', 'action_versions', ['action_id'])
    op.create_index('ix_version_version_number', 'action_versions', ['version_number'])
    op.create_index('ix_version_implementation_hash', 'action_versions', ['implementation_hash'])
    op.create_index('ix_version_parameters_schema_hash', 'action_versions', ['parameters_schema_hash'])
    op.create_index('ix_version_is_current', 'action_versions', ['is_current'])
    op.create_index('ix_version_is_stable', 'action_versions', ['is_stable'])
    op.create_index('ix_version_backward_compatible', 'action_versions', ['backward_compatible'])
    
    # Composite indexes for action_versions
    op.create_index('ix_version_action_number', 'action_versions', ['action_id', 'version_number'])
    op.create_index('ix_version_hashes', 'action_versions', ['implementation_hash', 'parameters_schema_hash'])
    op.create_index('ix_version_status', 'action_versions', ['is_current', 'is_stable'])
    
    # JSON indexes for action_versions
    op.create_index('ix_version_change_details_gin', 'action_versions', ['change_details'], postgresql_using='gin')
    op.create_index('ix_version_breaking_changes_gin', 'action_versions', ['breaking_changes'], postgresql_using='gin')
    
    # Create indexes for action_relationships table
    op.create_index('ix_relationship_id', 'action_relationships', ['id'])
    op.create_index('ix_relationship_source_action_id', 'action_relationships', ['source_action_id'])
    op.create_index('ix_relationship_target_action_id', 'action_relationships', ['target_action_id'])
    op.create_index('ix_relationship_relationship_type', 'action_relationships', ['relationship_type'])
    op.create_index('ix_relationship_relationship_strength', 'action_relationships', ['relationship_strength'])
    op.create_index('ix_relationship_is_active', 'action_relationships', ['is_active'])
    
    # Composite indexes for action_relationships
    op.create_index('ix_relationship_source_target', 'action_relationships', ['source_action_id', 'target_action_id'])
    op.create_index('ix_relationship_type_strength', 'action_relationships', ['relationship_type', 'relationship_strength'])
    
    # JSON indexes for action_relationships
    op.create_index('ix_relationship_conditions_gin', 'action_relationships', ['conditions'], postgresql_using='gin')
    op.create_index('ix_relationship_metadata_gin', 'action_relationships', ['metadata'], postgresql_using='gin')
    op.create_index('ix_relationship_context_tags_gin', 'action_relationships', ['context_tags'], postgresql_using='gin')
    
    # Create indexes for action_usage_tracking table
    op.create_index('ix_usage_id', 'action_usage_tracking', ['id'])
    op.create_index('ix_usage_action_id', 'action_usage_tracking', ['action_id'])
    op.create_index('ix_usage_journey_id', 'action_usage_tracking', ['journey_id'])
    op.create_index('ix_usage_usage_context', 'action_usage_tracking', ['usage_context'])
    op.create_index('ix_usage_usage_environment', 'action_usage_tracking', ['usage_environment'])
    op.create_index('ix_usage_used_at', 'action_usage_tracking', ['used_at'])
    op.create_index('ix_usage_execution_result', 'action_usage_tracking', ['execution_result'])
    op.create_index('ix_usage_session_id', 'action_usage_tracking', ['session_id'])
    
    # Composite indexes for action_usage_tracking (for analytics)
    op.create_index('ix_usage_action_time', 'action_usage_tracking', ['action_id', 'used_at'])
    op.create_index('ix_usage_journey_time', 'action_usage_tracking', ['journey_id', 'used_at'])
    op.create_index('ix_usage_context_environment', 'action_usage_tracking', ['usage_context', 'usage_environment'])
    op.create_index('ix_usage_result_duration', 'action_usage_tracking', ['execution_result', 'execution_duration_seconds'])
    op.create_index('ix_usage_session', 'action_usage_tracking', ['session_id', 'used_at'])
    op.create_index('ix_usage_time_partitioning', 'action_usage_tracking', ['used_at'])  # For time-based partitioning
    
    # JSON indexes for action_usage_tracking
    op.create_index('ix_usage_parameters_gin', 'action_usage_tracking', ['parameters_used'], postgresql_using='gin')
    op.create_index('ix_usage_metadata_gin', 'action_usage_tracking', ['metadata'], postgresql_using='gin')


def downgrade():
    """Drop action library tables and indexes."""
    
    # Drop tables in reverse dependency order
    op.drop_table('action_usage_tracking')
    op.drop_table('action_relationships')
    op.drop_table('action_versions')
    op.drop_table('action_execution_metrics')
    op.drop_table('action_library')
    
    # Drop extension if no other tables use it
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")