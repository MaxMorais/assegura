"""Create personas table

Revision ID: 001_create_personas_table
Revises: 001_initial_auth_tables
Create Date: 2025-10-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '002_create_personas_table'
down_revision = '001_initial_auth_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create personas table and related indexes."""
    
    # Create personas table
    op.create_table(
        'personas',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('erpnext_roles', sa.Text(), nullable=False),
        sa.Column('permissions', sa.Text(), nullable=True, default=''),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='personas_name_key'),
        sa.CheckConstraint("name != ''", name='personas_name_not_empty'),
        sa.CheckConstraint("description != ''", name='personas_description_not_empty'),
        sa.CheckConstraint("erpnext_roles != ''", name='personas_erpnext_roles_not_empty'),
        sa.CheckConstraint("version > 0", name='personas_version_positive'),
        
        # Comments
        comment='Test personas for ERPNext automation framework'
    )
    
    # Create indexes for performance
    op.create_index('ix_personas_id', 'personas', ['id'])
    op.create_index('ix_personas_name', 'personas', ['name'])
    op.create_index('ix_personas_is_active', 'personas', ['is_active'])
    op.create_index('ix_personas_created_at', 'personas', ['created_at'])
    
    # Create composite indexes for common queries
    op.create_index('ix_personas_active_name', 'personas', ['is_active', 'name'])
    op.create_index('ix_personas_created_active', 'personas', ['created_at', 'is_active'])
    
    # Create GIN index for text search on name and description
    op.execute("""
        CREATE INDEX ix_personas_text_search 
        ON personas 
        USING gin(to_tsvector('english', name || ' ' || description))
    """)
    
    # Create trigger to automatically update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_personas_updated_at 
        BEFORE UPDATE ON personas
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop personas table and related objects."""
    
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS update_personas_updated_at ON personas;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop indexes
    op.drop_index('ix_personas_text_search', 'personas')
    op.drop_index('ix_personas_created_active', 'personas')
    op.drop_index('ix_personas_active_name', 'personas')
    op.drop_index('ix_personas_created_at', 'personas')
    op.drop_index('ix_personas_is_active', 'personas')
    op.drop_index('ix_personas_name', 'personas')
    op.drop_index('ix_personas_id', 'personas')
    
    # Drop table
    op.drop_table('personas')