"""
Create journey tables

Revision ID: 002_create_journey_tables
Revises: 001_initial_auth_tables
Create Date: 2025-10-16 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_create_journey_tables'
down_revision = '001_initial_auth_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create journey-related tables with comprehensive structure and indexes."""
    
    # Create journeys table
    op.create_table(
        'journeys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('persona_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('activity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_status', sa.String(50), nullable=False, server_default='not_started'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('complexity_level', sa.String(50), nullable=False, server_default='medium'),
        sa.Column('prerequisites', postgresql.JSONB(), nullable=True),
        sa.Column('expected_outcomes', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ondelete='CASCADE'),
        
        # Check constraints
        sa.CheckConstraint(
            "estimated_duration_minutes IS NULL OR estimated_duration_minutes > 0",
            name='ck_journey_positive_duration'
        ),
        sa.CheckConstraint(
            "complexity_level IN ('simple', 'medium', 'complex', 'advanced')",
            name='ck_journey_valid_complexity'
        ),
        sa.CheckConstraint(
            "execution_status IN ('not_started', 'ready', 'running', 'suspended', 'completed', 'failed', 'cancelled')",
            name='ck_journey_valid_execution_status'
        ),
        sa.CheckConstraint(
            "usage_count >= 0",
            name='ck_journey_positive_usage_count'
        ),
        
        # Unique constraints
        sa.UniqueConstraint('name', 'persona_id', 'activity_id', name='uq_journey_name_persona_activity'),
    )
    
    # Create journey_steps table
    op.create_table(
        'journey_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('journey_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('step_description', sa.Text(), nullable=True),
        sa.Column('parameters', postgresql.JSONB(), nullable=True),
        sa.Column('expected_outputs', postgresql.JSONB(), nullable=True),
        sa.Column('timeout_override', sa.Integer(), nullable=True),
        sa.Column('retry_override', sa.Integer(), nullable=True),
        sa.Column('depends_on_steps', postgresql.JSONB(), nullable=True),
        sa.Column('can_run_parallel', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_critical', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('execution_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('execution_result', postgresql.JSONB(), nullable=True),
        sa.Column('execution_duration_seconds', sa.Float(), nullable=True),
        sa.Column('execution_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['journey_id'], ['journeys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['action_id'], ['action_library.id'], ondelete='RESTRICT'),
        
        # Check constraints
        sa.CheckConstraint(
            "step_number > 0",
            name='ck_journey_step_positive_number'
        ),
        sa.CheckConstraint(
            "timeout_override IS NULL OR timeout_override > 0",
            name='ck_journey_step_positive_timeout'
        ),
        sa.CheckConstraint(
            "retry_override IS NULL OR retry_override >= 0",
            name='ck_journey_step_non_negative_retry'
        ),
        sa.CheckConstraint(
            "execution_status IN ('pending', 'running', 'completed', 'failed', 'skipped', 'cancelled')",
            name='ck_journey_step_valid_execution_status'
        ),
        sa.CheckConstraint(
            "execution_duration_seconds IS NULL OR execution_duration_seconds >= 0",
            name='ck_journey_step_non_negative_duration'
        ),
        
        # Unique constraints
        sa.UniqueConstraint('journey_id', 'step_number', name='uq_journey_step_number'),
    )
    
    # Create journey_execution_plans table
    op.create_table(
        'journey_execution_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('journey_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('total_steps', sa.Integer(), nullable=False),
        sa.Column('estimated_duration_seconds', sa.Integer(), nullable=False),
        sa.Column('complexity_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('can_execute_parallel', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parallel_executable_steps', postgresql.JSONB(), nullable=True),
        sa.Column('critical_path_steps', postgresql.JSONB(), nullable=True),
        sa.Column('rollback_points', postgresql.JSONB(), nullable=True),
        sa.Column('resource_requirements', postgresql.JSONB(), nullable=True),
        sa.Column('plan_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('plan_generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['journey_id'], ['journeys.id'], ondelete='CASCADE'),
        
        # Check constraints
        sa.CheckConstraint(
            "total_steps > 0",
            name='ck_execution_plan_positive_steps'
        ),
        sa.CheckConstraint(
            "estimated_duration_seconds > 0",
            name='ck_execution_plan_positive_duration'
        ),
        sa.CheckConstraint(
            "complexity_score >= 0",
            name='ck_execution_plan_non_negative_complexity'
        ),
        sa.CheckConstraint(
            "plan_version > 0",
            name='ck_execution_plan_positive_version'
        ),
    )
    
    # Create journey_executions table
    op.create_table(
        'journey_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('journey_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_number', sa.Integer(), nullable=False),
        sa.Column('execution_batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_duration_seconds', sa.Float(), nullable=True),
        sa.Column('execution_status', sa.String(50), nullable=False, server_default='running'),
        sa.Column('final_result', sa.String(50), nullable=True),
        sa.Column('total_steps_executed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('steps_passed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('steps_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('steps_skipped', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('execution_context', postgresql.JSONB(), nullable=True),
        sa.Column('execution_results', postgresql.JSONB(), nullable=True),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('performance_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('executed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('execution_environment', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['journey_id'], ['journeys.id'], ondelete='CASCADE'),
        
        # Check constraints
        sa.CheckConstraint(
            "execution_number > 0",
            name='ck_journey_execution_positive_number'
        ),
        sa.CheckConstraint(
            "total_duration_seconds IS NULL OR total_duration_seconds >= 0",
            name='ck_journey_execution_non_negative_duration'
        ),
        sa.CheckConstraint(
            "execution_status IN ('running', 'completed', 'failed', 'cancelled', 'timeout')",
            name='ck_journey_execution_valid_status'
        ),
        sa.CheckConstraint(
            "final_result IS NULL OR final_result IN ('success', 'failure', 'partial_success', 'cancelled', 'timeout')",
            name='ck_journey_execution_valid_result'
        ),
        sa.CheckConstraint(
            "total_steps_executed >= 0",
            name='ck_journey_execution_non_negative_steps'
        ),
        sa.CheckConstraint(
            "steps_passed >= 0 AND steps_failed >= 0 AND steps_skipped >= 0",
            name='ck_journey_execution_non_negative_step_counts'
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name='ck_journey_execution_valid_completion_time'
        ),
        
        # Unique constraints
        sa.UniqueConstraint('journey_id', 'execution_number', name='uq_journey_execution_number'),
    )
    
    # Create journey_step_executions table
    op.create_table(
        'journey_step_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('journey_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('journey_step_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('execution_order', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('execution_status', sa.String(50), nullable=False, server_default='running'),
        sa.Column('execution_result', sa.String(50), nullable=True),
        sa.Column('input_parameters', postgresql.JSONB(), nullable=True),
        sa.Column('actual_outputs', postgresql.JSONB(), nullable=True),
        sa.Column('step_artifacts', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('performance_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(['journey_execution_id'], ['journey_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['journey_step_id'], ['journey_steps.id'], ondelete='CASCADE'),
        
        # Check constraints
        sa.CheckConstraint(
            "step_number > 0",
            name='ck_step_execution_positive_step_number'
        ),
        sa.CheckConstraint(
            "execution_order > 0",
            name='ck_step_execution_positive_order'
        ),
        sa.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name='ck_step_execution_non_negative_duration'
        ),
        sa.CheckConstraint(
            "execution_status IN ('running', 'completed', 'failed', 'skipped', 'timeout')",
            name='ck_step_execution_valid_status'
        ),
        sa.CheckConstraint(
            "execution_result IS NULL OR execution_result IN ('passed', 'failed', 'skipped', 'error', 'timeout')",
            name='ck_step_execution_valid_result'
        ),
        sa.CheckConstraint(
            "retry_count >= 0",
            name='ck_step_execution_non_negative_retry'
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name='ck_step_execution_valid_completion_time'
        ),
        
        # Unique constraints
        sa.UniqueConstraint('journey_execution_id', 'step_number', name='uq_journey_step_execution'),
    )
    
    # Create indexes for journeys table
    op.create_index('ix_journey_id', 'journeys', ['id'])
    op.create_index('ix_journey_name', 'journeys', ['name'])
    op.create_index('ix_journey_persona_id', 'journeys', ['persona_id'])
    op.create_index('ix_journey_activity_id', 'journeys', ['activity_id'])
    op.create_index('ix_journey_execution_status', 'journeys', ['execution_status'])
    op.create_index('ix_journey_is_active', 'journeys', ['is_active'])
    op.create_index('ix_journey_complexity_level', 'journeys', ['complexity_level'])
    op.create_index('ix_journey_usage_count', 'journeys', ['usage_count'])
    op.create_index('ix_journey_last_used_date', 'journeys', ['last_used_date'])
    op.create_index('ix_journey_created_at', 'journeys', ['created_at'])
    op.create_index('ix_journey_updated_at', 'journeys', ['updated_at'])
    
    # Composite indexes for journeys
    op.create_index('ix_journey_persona_activity', 'journeys', ['persona_id', 'activity_id'])
    op.create_index('ix_journey_execution_status_active', 'journeys', ['execution_status', 'is_active'])
    op.create_index('ix_journey_complexity_duration', 'journeys', ['complexity_level', 'estimated_duration_minutes'])
    op.create_index('ix_journey_usage_tracking', 'journeys', ['usage_count', 'last_used_date'])
    op.create_index('ix_journey_created_updated', 'journeys', ['created_at', 'updated_at'])
    
    # JSON indexes for journeys
    op.create_index('ix_journey_metadata_gin', 'journeys', ['metadata'], postgresql_using='gin')
    op.create_index('ix_journey_prerequisites_gin', 'journeys', ['prerequisites'], postgresql_using='gin')
    op.create_index('ix_journey_expected_outcomes_gin', 'journeys', ['expected_outcomes'], postgresql_using='gin')
    
    # Create indexes for journey_steps table
    op.create_index('ix_journey_step_id', 'journey_steps', ['id'])
    op.create_index('ix_journey_step_journey_id', 'journey_steps', ['journey_id'])
    op.create_index('ix_journey_step_action_id', 'journey_steps', ['action_id'])
    op.create_index('ix_journey_step_step_number', 'journey_steps', ['step_number'])
    op.create_index('ix_journey_step_execution_status', 'journey_steps', ['execution_status'])
    op.create_index('ix_journey_step_can_run_parallel', 'journey_steps', ['can_run_parallel'])
    op.create_index('ix_journey_step_is_critical', 'journey_steps', ['is_critical'])
    
    # Composite indexes for journey_steps
    op.create_index('ix_journey_step_journey_order', 'journey_steps', ['journey_id', 'step_number'])
    op.create_index('ix_journey_step_action_lookup', 'journey_steps', ['action_id'])
    op.create_index('ix_journey_step_parallelization', 'journey_steps', ['can_run_parallel', 'is_critical'])
    
    # JSON indexes for journey_steps
    op.create_index('ix_journey_step_parameters_gin', 'journey_steps', ['parameters'], postgresql_using='gin')
    op.create_index('ix_journey_step_expected_outputs_gin', 'journey_steps', ['expected_outputs'], postgresql_using='gin')
    op.create_index('ix_journey_step_depends_on_gin', 'journey_steps', ['depends_on_steps'], postgresql_using='gin')
    op.create_index('ix_journey_step_execution_result_gin', 'journey_steps', ['execution_result'], postgresql_using='gin')
    
    # Create indexes for journey_execution_plans table
    op.create_index('ix_execution_plan_id', 'journey_execution_plans', ['id'])
    op.create_index('ix_execution_plan_journey', 'journey_execution_plans', ['journey_id'])
    op.create_index('ix_execution_plan_current', 'journey_execution_plans', ['is_current'])
    op.create_index('ix_execution_plan_duration_complexity', 'journey_execution_plans', ['estimated_duration_seconds', 'complexity_score'])
    op.create_index('ix_execution_plan_parallelization', 'journey_execution_plans', ['can_execute_parallel'])
    
    # JSON indexes for journey_execution_plans
    op.create_index('ix_execution_plan_parallel_steps_gin', 'journey_execution_plans', ['parallel_executable_steps'], postgresql_using='gin')
    op.create_index('ix_execution_plan_critical_path_gin', 'journey_execution_plans', ['critical_path_steps'], postgresql_using='gin')
    op.create_index('ix_execution_plan_rollback_points_gin', 'journey_execution_plans', ['rollback_points'], postgresql_using='gin')
    op.create_index('ix_execution_plan_resource_requirements_gin', 'journey_execution_plans', ['resource_requirements'], postgresql_using='gin')
    
    # Create indexes for journey_executions table
    op.create_index('ix_journey_execution_id', 'journey_executions', ['id'])
    op.create_index('ix_journey_execution_journey_id', 'journey_executions', ['journey_id'])
    op.create_index('ix_journey_execution_execution_number', 'journey_executions', ['execution_number'])
    op.create_index('ix_journey_execution_execution_batch_id', 'journey_executions', ['execution_batch_id'])
    op.create_index('ix_journey_execution_started_at', 'journey_executions', ['started_at'])
    op.create_index('ix_journey_execution_completed_at', 'journey_executions', ['completed_at'])
    op.create_index('ix_journey_execution_execution_status', 'journey_executions', ['execution_status'])
    op.create_index('ix_journey_execution_final_result', 'journey_executions', ['final_result'])
    op.create_index('ix_journey_execution_execution_environment', 'journey_executions', ['execution_environment'])
    op.create_index('ix_journey_execution_executed_by_user_id', 'journey_executions', ['executed_by_user_id'])
    
    # Composite indexes for journey_executions
    op.create_index('ix_journey_execution_journey_number', 'journey_executions', ['journey_id', 'execution_number'])
    op.create_index('ix_journey_execution_batch', 'journey_executions', ['execution_batch_id'])
    op.create_index('ix_journey_execution_timing', 'journey_executions', ['started_at', 'completed_at'])
    op.create_index('ix_journey_execution_status_result', 'journey_executions', ['execution_status', 'final_result'])
    op.create_index('ix_journey_execution_performance', 'journey_executions', ['total_duration_seconds'])
    
    # JSON indexes for journey_executions
    op.create_index('ix_journey_execution_context_gin', 'journey_executions', ['execution_context'], postgresql_using='gin')
    op.create_index('ix_journey_execution_results_gin', 'journey_executions', ['execution_results'], postgresql_using='gin')
    op.create_index('ix_journey_execution_performance_gin', 'journey_executions', ['performance_metrics'], postgresql_using='gin')
    
    # Create indexes for journey_step_executions table
    op.create_index('ix_step_execution_id', 'journey_step_executions', ['id'])
    op.create_index('ix_step_execution_journey_execution_id', 'journey_step_executions', ['journey_execution_id'])
    op.create_index('ix_step_execution_journey_step_id', 'journey_step_executions', ['journey_step_id'])
    op.create_index('ix_step_execution_step_number', 'journey_step_executions', ['step_number'])
    op.create_index('ix_step_execution_execution_order', 'journey_step_executions', ['execution_order'])
    op.create_index('ix_step_execution_started_at', 'journey_step_executions', ['started_at'])
    op.create_index('ix_step_execution_completed_at', 'journey_step_executions', ['completed_at'])
    op.create_index('ix_step_execution_execution_status', 'journey_step_executions', ['execution_status'])
    op.create_index('ix_step_execution_execution_result', 'journey_step_executions', ['execution_result'])
    op.create_index('ix_step_execution_retry_count', 'journey_step_executions', ['retry_count'])
    
    # Composite indexes for journey_step_executions
    op.create_index('ix_step_execution_journey_execution', 'journey_step_executions', ['journey_execution_id'])
    op.create_index('ix_step_execution_journey_step', 'journey_step_executions', ['journey_step_id'])
    op.create_index('ix_step_execution_step_order', 'journey_step_executions', ['step_number', 'execution_order'])
    op.create_index('ix_step_execution_timing', 'journey_step_executions', ['started_at', 'completed_at'])
    op.create_index('ix_step_execution_status_result', 'journey_step_executions', ['execution_status', 'execution_result'])
    op.create_index('ix_step_execution_performance', 'journey_step_executions', ['duration_seconds'])
    
    # JSON indexes for journey_step_executions
    op.create_index('ix_step_execution_input_parameters_gin', 'journey_step_executions', ['input_parameters'], postgresql_using='gin')
    op.create_index('ix_step_execution_actual_outputs_gin', 'journey_step_executions', ['actual_outputs'], postgresql_using='gin')
    op.create_index('ix_step_execution_artifacts_gin', 'journey_step_executions', ['step_artifacts'], postgresql_using='gin')
    op.create_index('ix_step_execution_error_details_gin', 'journey_step_executions', ['error_details'], postgresql_using='gin')
    op.create_index('ix_step_execution_performance_gin', 'journey_step_executions', ['performance_data'], postgresql_using='gin')


def downgrade():
    """Drop journey-related tables and indexes."""
    
    # Drop tables in reverse dependency order
    op.drop_table('journey_step_executions')
    op.drop_table('journey_executions')
    op.drop_table('journey_execution_plans')
    op.drop_table('journey_steps')
    op.drop_table('journeys')