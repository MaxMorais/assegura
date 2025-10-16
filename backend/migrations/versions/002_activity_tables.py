"""Create activities and activity_persona_links tables

Revision ID: 002_activity_tables
Revises: 001_initial_auth_tables
Create Date: 2024-01-15 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "002_activity_tables"
down_revision = "001_initial_auth_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create activities and activity_persona_links tables."""

    # Create activities table
    op.create_table(
        "activities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("erpnext_module", sa.String(100), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("target_doctype", sa.String(100), nullable=False),
        sa.Column("required_fields", sa.Text),
        sa.Column("validation_rules", JSONB, default={}),
        sa.Column("success_criteria", sa.Text),
        sa.Column("complexity_score", sa.Integer, nullable=False),
        sa.Column("estimated_duration", sa.Integer, nullable=False),
        sa.Column("prerequisites", sa.Text),
        sa.Column("postconditions", sa.Text),
        sa.Column("test_data_requirements", JSONB, default={}),
        sa.Column("tags", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("version", sa.String(20), nullable=False, default="1.0.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create activity_persona_links table
    op.create_table(
        "activity_persona_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("persona_id", UUID(as_uuid=True), nullable=False),
        sa.Column("activity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, default="medium"),
        sa.Column("notes", sa.Text),
        sa.Column("is_primary", sa.Boolean, default=False, nullable=False),
        sa.Column("execution_order", sa.Integer, default=0, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create indexes for activities table
    op.create_index("idx_activities_name", "activities", ["name"])
    op.create_index("idx_activities_erpnext_module", "activities", ["erpnext_module"])
    op.create_index("idx_activities_action_type", "activities", ["action_type"])
    op.create_index("idx_activities_target_doctype", "activities", ["target_doctype"])
    op.create_index(
        "idx_activities_complexity_score", "activities", ["complexity_score"]
    )
    op.create_index("idx_activities_is_active", "activities", ["is_active"])
    op.create_index("idx_activities_created_at", "activities", ["created_at"])
    op.create_index("idx_activities_updated_at", "activities", ["updated_at"])
    op.create_index(
        "idx_activity_module_type", "activities", ["erpnext_module", "action_type"]
    )
    op.create_index(
        "idx_activity_complexity_duration",
        "activities",
        ["complexity_score", "estimated_duration"],
    )
    op.create_index(
        "idx_activity_active_updated", "activities", ["is_active", "updated_at"]
    )

    # Create indexes for activity_persona_links table
    op.create_index(
        "idx_activity_persona_links_persona_id",
        "activity_persona_links",
        ["persona_id"],
    )
    op.create_index(
        "idx_activity_persona_links_activity_id",
        "activity_persona_links",
        ["activity_id"],
    )
    op.create_index(
        "idx_activity_persona_links_priority", "activity_persona_links", ["priority"]
    )
    op.create_index(
        "idx_persona_priority", "activity_persona_links", ["persona_id", "priority"]
    )
    op.create_index(
        "idx_activity_order",
        "activity_persona_links",
        ["activity_id", "execution_order"],
    )
    op.create_index("idx_link_created", "activity_persona_links", ["created_at"])

    # Create unique constraint for activity name
    op.create_unique_constraint("uq_activity_name", "activities", ["name"])

    # Create unique constraint for persona-activity combination
    op.create_unique_constraint(
        "uq_persona_activity", "activity_persona_links", ["persona_id", "activity_id"]
    )

    # Create foreign key constraints
    op.create_foreign_key(
        "fk_activity_persona_links_activity_id",
        "activity_persona_links",
        "activities",
        ["activity_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Create check constraints
    op.create_check_constraint(
        "check_complexity_score",
        "activities",
        "complexity_score >= 1 AND complexity_score <= 5",
    )

    op.create_check_constraint(
        "check_estimated_duration", "activities", "estimated_duration > 0"
    )

    op.create_check_constraint(
        "check_action_type",
        "activities",
        "action_type IN ('create', 'read', 'update', 'delete', 'list', 'search', 'filter', 'export', 'import', 'approve', 'reject', 'submit', 'cancel', 'duplicate', 'print', 'email', 'share', 'assign', 'comment', 'attachment', 'workflow', 'permission', 'custom')",
    )

    op.create_check_constraint(
        "check_priority",
        "activity_persona_links",
        "priority IN ('high', 'medium', 'low', 'critical')",
    )

    op.create_check_constraint(
        "check_execution_order", "activity_persona_links", "execution_order >= 0"
    )


def downgrade() -> None:
    """Drop activities and activity_persona_links tables."""

    # Drop tables (foreign keys will be dropped automatically)
    op.drop_table("activity_persona_links")
    op.drop_table("activities")
