"""Migration script template for ERPNext Test Automation Meta-Framework.

Constitutional Compliance:
✓ Multi-tenant data isolation
✓ DDD architecture alignment  
✓ Python 3.11+ compatibility

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade database schema.
    
    Apply changes to upgrade the database to this revision.
    Ensure multi-tenant data isolation is maintained.
    """
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade database schema.
    
    Revert changes to downgrade the database from this revision.
    Ensure data consistency during rollback.
    """
    ${downgrades if downgrades else "pass"}