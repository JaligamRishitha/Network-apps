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
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
    ))
    table_exists = result.scalar()

    if not table_exists:
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

    # Create indexes if they don't exist
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)"))
    op.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
    op.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))

    # Seed default users (skip if already exist)
    op.execute(sa.text("""
        INSERT INTO users (username, email, password, roles, is_active, created_at)
        VALUES
            ('David Philips', 'admin@example.com', 'admin123', '["Admin"]', true, '2024-01-01 00:00:00'),
            ('engineer', 'engineer@example.com', 'engineer123', '["Maintenance_Engineer"]', true, '2024-01-01 00:00:00'),
            ('manager', 'manager@example.com', 'manager123', '["Store_Manager"]', true, '2024-01-01 00:00:00'),
            ('finance', 'finance@example.com', 'finance123', '["Finance_Officer"]', true, '2024-01-01 00:00:00')
        ON CONFLICT (username) DO NOTHING
    """))


def downgrade():
    """Drop users table"""
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
