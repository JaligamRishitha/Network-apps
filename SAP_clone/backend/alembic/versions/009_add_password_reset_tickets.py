"""Add password reset tickets table

Revision ID: 009
Revises: 008
Create Date: 2026-02-06 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_password_reset'
down_revision = '008_work_order_flow'
branch_labels = None
depends_on = None


def upgrade():
    """Create password_reset_tickets table"""
    op.create_table(
        'password_reset_tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sap_ticket_id', sa.String(length=255), nullable=True),
        sa.Column('servicenow_ticket_id', sa.String(length=255), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('requester_name', sa.String(length=255), nullable=True),
        sa.Column('requester_email', sa.String(length=255), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('callback_url', sa.String(length=500), nullable=True),
        sa.Column('temp_password', sa.String(length=255), nullable=True),
        sa.Column('comments', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better query performance
    op.create_index(op.f('ix_password_reset_tickets_id'), 'password_reset_tickets', ['id'], unique=False)
    op.create_index(op.f('ix_password_reset_tickets_sap_ticket_id'), 'password_reset_tickets', ['sap_ticket_id'], unique=True)
    op.create_index(op.f('ix_password_reset_tickets_servicenow_ticket_id'), 'password_reset_tickets', ['servicenow_ticket_id'], unique=False)
    op.create_index(op.f('ix_password_reset_tickets_username'), 'password_reset_tickets', ['username'], unique=False)
    op.create_index(op.f('ix_password_reset_tickets_correlation_id'), 'password_reset_tickets', ['correlation_id'], unique=False)


def downgrade():
    """Drop password_reset_tickets table"""
    op.drop_index(op.f('ix_password_reset_tickets_correlation_id'), table_name='password_reset_tickets')
    op.drop_index(op.f('ix_password_reset_tickets_username'), table_name='password_reset_tickets')
    op.drop_index(op.f('ix_password_reset_tickets_servicenow_ticket_id'), table_name='password_reset_tickets')
    op.drop_index(op.f('ix_password_reset_tickets_sap_ticket_id'), table_name='password_reset_tickets')
    op.drop_index(op.f('ix_password_reset_tickets_id'), table_name='password_reset_tickets')
    op.drop_table('password_reset_tickets')
