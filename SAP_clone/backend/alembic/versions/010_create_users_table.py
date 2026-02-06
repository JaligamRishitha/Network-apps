"""Create users table

Revision ID: 010
Revises: 009
Create Date: 2026-02-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_users_table'
down_revision = '009_password_reset'
branch_labels = None
depends_on = None


def upgrade():
    """Create users table for persistent user storage"""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('roles', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better query performance
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Seed default users
    op.execute("""
        INSERT INTO users (username, email, password, roles, is_active, created_at)
        VALUES
            ('admin', 'admin@example.com', 'admin123', '["Admin"]', true, '2024-01-01 00:00:00'),
            ('engineer', 'engineer@example.com', 'engineer123', '["Maintenance_Engineer"]', true, '2024-01-01 00:00:00'),
            ('manager', 'manager@example.com', 'manager123', '["Store_Manager"]', true, '2024-01-01 00:00:00'),
            ('finance', 'finance@example.com', 'finance123', '["Finance_Officer"]', true, '2024-01-01 00:00:00')
    """)


def downgrade():
    """Drop users table"""
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
