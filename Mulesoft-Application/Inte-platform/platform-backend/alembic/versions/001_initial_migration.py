"""Initial migration for Mulesoft Integration Platform

Revision ID: 001
Revises:
Create Date: 2026-02-06 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create all initial tables"""

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('ADMIN', 'DEVELOPER', 'VIEWER', name='userrole'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create integrations table
    op.create_table(
        'integrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('flow_config', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'DEPLOYED', 'STOPPED', 'ERROR', name='integrationstatus'), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_integrations_id'), 'integrations', ['id'], unique=False)
    op.create_index(op.f('ix_integrations_name'), 'integrations', ['name'], unique=False)

    # Create integration_logs table
    op.create_table(
        'integration_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=True),
        sa.Column('level', sa.String(length=20), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_integration_logs_id'), 'integration_logs', ['id'], unique=False)

    # Create api_endpoints table
    op.create_table(
        'api_endpoints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('path', sa.String(length=255), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('ip_whitelist', sa.JSON(), nullable=True),
        sa.Column('requires_auth', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_endpoints_id'), 'api_endpoints', ['id'], unique=False)

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)
    op.create_index(op.f('ix_api_keys_key'), 'api_keys', ['key'], unique=True)

    # Create connectors table
    op.create_table(
        'connectors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connector_name', sa.String(length=255), nullable=True),
        sa.Column('connector_type', sa.String(length=50), nullable=True),
        sa.Column('connection_config', sa.JSON(), nullable=True),
        sa.Column('credentials_ref', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('health_check_url', sa.String(length=500), nullable=True),
        sa.Column('last_health_check', sa.DateTime(), nullable=True),
        sa.Column('health_status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_connectors_id'), 'connectors', ['id'], unique=False)
    op.create_index(op.f('ix_connectors_connector_name'), 'connectors', ['connector_name'], unique=True)

    # Create salesforce_cases table
    op.create_table(
        'salesforce_cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('salesforce_id', sa.String(length=18), nullable=True),
        sa.Column('case_number', sa.String(length=50), nullable=True),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=True),
        sa.Column('origin', sa.String(length=50), nullable=True),
        sa.Column('account_id', sa.String(length=18), nullable=True),
        sa.Column('account_name', sa.String(length=255), nullable=True),
        sa.Column('contact_id', sa.String(length=18), nullable=True),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('owner_id', sa.String(length=18), nullable=True),
        sa.Column('owner_name', sa.String(length=255), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=True),
        sa.Column('closed_date', sa.DateTime(), nullable=True),
        sa.Column('last_modified_date', sa.DateTime(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_salesforce_cases_id'), 'salesforce_cases', ['id'], unique=False)
    op.create_index(op.f('ix_salesforce_cases_salesforce_id'), 'salesforce_cases', ['salesforce_id'], unique=True)

    # Create password_reset_tickets table
    op.create_table(
        'password_reset_tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('servicenow_ticket_id', sa.String(length=255), nullable=True),
        sa.Column('sap_ticket_id', sa.String(length=255), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('requester_name', sa.String(length=255), nullable=True),
        sa.Column('requester_email', sa.String(length=255), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('sap_status', sa.String(length=50), nullable=True),
        sa.Column('servicenow_updated', sa.Boolean(), nullable=True),
        sa.Column('history', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_reset_tickets_correlation_id'), 'password_reset_tickets', ['correlation_id'], unique=True)
    op.create_index(op.f('ix_password_reset_tickets_servicenow_ticket_id'), 'password_reset_tickets', ['servicenow_ticket_id'], unique=False)
    op.create_index(op.f('ix_password_reset_tickets_sap_ticket_id'), 'password_reset_tickets', ['sap_ticket_id'], unique=False)

    # Create user_creation_approvals table
    op.create_table(
        'user_creation_approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('sap_username', sa.String(length=255), nullable=True),
        sa.Column('sap_roles', sa.JSON(), nullable=True),
        sa.Column('servicenow_ticket_number', sa.String(length=255), nullable=True),
        sa.Column('servicenow_ticket_id', sa.String(length=255), nullable=True),
        sa.Column('approval_status', sa.String(length=50), nullable=True),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('sap_event_id', sa.String(length=255), nullable=True),
        sa.Column('history', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_creation_approvals_correlation_id'), 'user_creation_approvals', ['correlation_id'], unique=True)
    op.create_index(op.f('ix_user_creation_approvals_sap_username'), 'user_creation_approvals', ['sap_username'], unique=False)
    op.create_index(op.f('ix_user_creation_approvals_servicenow_ticket_number'), 'user_creation_approvals', ['servicenow_ticket_number'], unique=False)


def downgrade():
    """Drop all tables"""
    op.drop_index(op.f('ix_user_creation_approvals_servicenow_ticket_number'), table_name='user_creation_approvals')
    op.drop_index(op.f('ix_user_creation_approvals_sap_username'), table_name='user_creation_approvals')
    op.drop_index(op.f('ix_user_creation_approvals_correlation_id'), table_name='user_creation_approvals')
    op.drop_table('user_creation_approvals')

    op.drop_index(op.f('ix_password_reset_tickets_sap_ticket_id'), table_name='password_reset_tickets')
    op.drop_index(op.f('ix_password_reset_tickets_servicenow_ticket_id'), table_name='password_reset_tickets')
    op.drop_index(op.f('ix_password_reset_tickets_correlation_id'), table_name='password_reset_tickets')
    op.drop_table('password_reset_tickets')

    op.drop_index(op.f('ix_salesforce_cases_salesforce_id'), table_name='salesforce_cases')
    op.drop_index(op.f('ix_salesforce_cases_id'), table_name='salesforce_cases')
    op.drop_table('salesforce_cases')

    op.drop_index(op.f('ix_connectors_connector_name'), table_name='connectors')
    op.drop_index(op.f('ix_connectors_id'), table_name='connectors')
    op.drop_table('connectors')

    op.drop_index(op.f('ix_api_keys_key'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')
    op.drop_table('api_keys')

    op.drop_index(op.f('ix_api_endpoints_id'), table_name='api_endpoints')
    op.drop_table('api_endpoints')

    op.drop_index(op.f('ix_integration_logs_id'), table_name='integration_logs')
    op.drop_table('integration_logs')

    op.drop_index(op.f('ix_integrations_name'), table_name='integrations')
    op.drop_index(op.f('ix_integrations_id'), table_name='integrations')
    op.drop_table('integrations')

    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
