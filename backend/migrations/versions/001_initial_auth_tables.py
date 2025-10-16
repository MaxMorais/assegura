"""Initial database migration for multi-tenant authentication.

Creates core tables for Tenant and Consultant entities with proper
multi-tenant isolation and constitutional compliance.

Constitutional Compliance:
✓ Multi-tenant data isolation with tenant_id foreign keys
✓ DDD architecture alignment with aggregate boundaries  
✓ Python 3.11+ compatibility with UUID primary keys

Revision ID: 001_initial_auth_tables
Revises: 
Create Date: 2025-10-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_auth_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema.
    
    Apply changes to upgrade the database to this revision.
    Creates core multi-tenant authentication tables.
    """
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('subdomain', sa.String(length=100), nullable=False, unique=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('settings', postgresql.JSONB, nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('version', sa.Integer, nullable=False, default=1),
        
        # Indexes for performance
        sa.Index('ix_tenants_subdomain', 'subdomain'),
        sa.Index('ix_tenants_status', 'status'),
        sa.Index('ix_tenants_created_at', 'created_at'),
        
        # Constraints
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'pending', 'inactive')",
            name='ck_tenants_status'
        ),
        sa.CheckConstraint(
            "char_length(subdomain) >= 3",
            name='ck_tenants_subdomain_length'
        ),
        sa.CheckConstraint(
            "char_length(name) >= 1",
            name='ck_tenants_name_length'
        ),
    )
    
    # Create consultants table
    op.create_table(
        'consultants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, default='consultant'),
        sa.Column('permissions', postgresql.JSONB, nullable=True, default=[]),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('version', sa.Integer, nullable=False, default=1),
        
        # Foreign key with cascade for multi-tenant isolation
        sa.ForeignKeyConstraint(
            ['tenant_id'], 
            ['tenants.id'], 
            name='fk_consultants_tenant_id',
            ondelete='CASCADE'
        ),
        
        # Indexes for performance and multi-tenant queries
        sa.Index('ix_consultants_tenant_id', 'tenant_id'),
        sa.Index('ix_consultants_email_tenant', 'email', 'tenant_id'),
        sa.Index('ix_consultants_role_tenant', 'role', 'tenant_id'),
        sa.Index('ix_consultants_active_tenant', 'is_active', 'tenant_id'),
        sa.Index('ix_consultants_created_at', 'created_at'),
        sa.Index('ix_consultants_last_login', 'last_login'),
        
        # Unique constraint for email within tenant (multi-tenant isolation)
        sa.UniqueConstraint(
            'email', 'tenant_id',
            name='uq_consultants_email_tenant'
        ),
        
        # Constraints
        sa.CheckConstraint(
            "role IN ('admin', 'consultant', 'viewer')",
            name='ck_consultants_role'
        ),
        sa.CheckConstraint(
            "char_length(email) >= 5",
            name='ck_consultants_email_length'
        ),
        sa.CheckConstraint(
            "char_length(first_name) >= 1",
            name='ck_consultants_first_name_length'
        ),
        sa.CheckConstraint(
            "char_length(last_name) >= 1",
            name='ck_consultants_last_name_length'
        ),
        sa.CheckConstraint(
            "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name='ck_consultants_email_format'
        ),
    )
    
    # Create audit log table for security compliance
    op.create_table(
        'auth_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('consultant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=True),
        sa.Column('details', postgresql.JSONB, nullable=True, default={}),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        
        # Foreign keys
        sa.ForeignKeyConstraint(
            ['tenant_id'], 
            ['tenants.id'], 
            name='fk_auth_audit_log_tenant_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['consultant_id'], 
            ['consultants.id'], 
            name='fk_auth_audit_log_consultant_id',
            ondelete='SET NULL'
        ),
        
        # Indexes for audit queries
        sa.Index('ix_auth_audit_log_tenant_timestamp', 'tenant_id', 'timestamp'),
        sa.Index('ix_auth_audit_log_consultant_timestamp', 'consultant_id', 'timestamp'),
        sa.Index('ix_auth_audit_log_action', 'action'),
        sa.Index('ix_auth_audit_log_timestamp', 'timestamp'),
        
        # Partitioning preparation (can be added later)
        postgresql_partition_by='RANGE (timestamp)',
    )


def downgrade() -> None:
    """Downgrade database schema.
    
    Revert changes to downgrade the database from this revision.
    Drops all authentication-related tables.
    """
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('auth_audit_log')
    op.drop_table('consultants')
    op.drop_table('tenants')