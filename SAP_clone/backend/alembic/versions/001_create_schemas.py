"""Create database schemas for PM, MM, FI, and core modules

Revision ID: 001_create_schemas
Revises: 
Create Date: 2024-01-15

Requirements: 9.1 - Create separate schemas for pm, mm, and fi modules
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_create_schemas'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schemas for each module
    op.execute('CREATE SCHEMA IF NOT EXISTS core')
    op.execute('CREATE SCHEMA IF NOT EXISTS pm')
    op.execute('CREATE SCHEMA IF NOT EXISTS mm')
    op.execute('CREATE SCHEMA IF NOT EXISTS fi')


def downgrade() -> None:
    # Drop schemas in reverse order
    op.execute('DROP SCHEMA IF EXISTS fi CASCADE')
    op.execute('DROP SCHEMA IF EXISTS mm CASCADE')
    op.execute('DROP SCHEMA IF EXISTS pm CASCADE')
    op.execute('DROP SCHEMA IF EXISTS core CASCADE')
