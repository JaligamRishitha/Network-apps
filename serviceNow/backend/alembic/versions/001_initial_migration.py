"""Initial migration for ServiceNow backend - Create all tables

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
    """Create all initial tables for ServiceNow backend"""

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('role', sa.Enum('admin', 'agent', 'user', name='userrole'), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create incidents table
    op.create_table(
        'incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='incidentpriority'), nullable=True),
        sa.Column('status', sa.Enum('new', 'in_progress', 'resolved', 'closed', name='incidentstatus'), nullable=True),
        sa.Column('reporter_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incidents_id'), 'incidents', ['id'], unique=False)
    op.create_index(op.f('ix_incidents_title'), 'incidents', ['title'], unique=False)

    # Create service_catalog_items table
    op.create_table(
        'service_catalog_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_catalog_items_id'), 'service_catalog_items', ['id'], unique=False)
    op.create_index(op.f('ix_service_catalog_items_name'), 'service_catalog_items', ['name'], unique=False)

    # Create knowledge_articles table
    op.create_table(
        'knowledge_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('tags', sa.String(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('helpful_votes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_articles_id'), 'knowledge_articles', ['id'], unique=False)
    op.create_index(op.f('ix_knowledge_articles_title'), 'knowledge_articles', ['title'], unique=False)
    op.create_index(op.f('ix_knowledge_articles_category'), 'knowledge_articles', ['category'], unique=False)

    # Create tickets table
    op.create_table(
        'tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_number', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ticket_type', sa.Enum('incident', 'service_request', 'change_request', 'problem', name='tickettype'), nullable=True),
        sa.Column('status', sa.Enum('draft', 'submitted', 'pending_approval', 'approved', 'rejected', 'in_progress', 'resolved', 'closed', 'cancelled', name='ticketstatus'), nullable=True),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='incidentpriority'), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('subcategory', sa.String(), nullable=True),
        sa.Column('requester_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('contact_number', sa.String(), nullable=True),
        sa.Column('preferred_contact', sa.String(), nullable=True),
        sa.Column('urgency', sa.String(), nullable=True),
        sa.Column('business_justification', sa.Text(), nullable=True),
        sa.Column('estimated_cost', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('servicenow_sys_id', sa.String(), nullable=True),
        sa.Column('servicenow_number', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tickets_id'), 'tickets', ['id'], unique=False)
    op.create_index(op.f('ix_tickets_ticket_number'), 'tickets', ['ticket_number'], unique=True)
    op.create_index(op.f('ix_tickets_title'), 'tickets', ['title'], unique=False)
    op.create_index(op.f('ix_tickets_servicenow_sys_id'), 'tickets', ['servicenow_sys_id'], unique=False)
    op.create_index(op.f('ix_tickets_servicenow_number'), 'tickets', ['servicenow_number'], unique=False)

    # Create approvals table
    op.create_table(
        'approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=True),
        sa.Column('approver_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='approvalstatus'), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approvals_id'), 'approvals', ['id'], unique=False)

    # Create assignment_groups table
    op.create_table(
        'assignment_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assignment_groups_name'), 'assignment_groups', ['name'], unique=True)
    op.create_index(op.f('ix_assignment_groups_id'), 'assignment_groups', ['id'], unique=False)

    # Create assignment_group_members table
    op.create_table(
        'assignment_group_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.String(), nullable=True),
        sa.Column('assignment_count', sa.Integer(), nullable=True),
        sa.Column('last_assigned_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['assignment_groups.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assignment_group_members_id'), 'assignment_group_members', ['id'], unique=False)

    # Create category_assignment_mappings table
    op.create_table(
        'category_assignment_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('subcategory', sa.String(), nullable=True),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.Column('priority_override', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['assignment_groups.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_category_assignment_mappings_category'), 'category_assignment_mappings', ['category'], unique=False)
    op.create_index(op.f('ix_category_assignment_mappings_id'), 'category_assignment_mappings', ['id'], unique=False)

    # Create sla_definitions table
    op.create_table(
        'sla_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('response_time_minutes', sa.Integer(), nullable=True),
        sa.Column('resolution_time_hours', sa.Integer(), nullable=True),
        sa.Column('business_hours_only', sa.String(), nullable=True),
        sa.Column('warning_threshold_percent', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sla_definitions_name'), 'sla_definitions', ['name'], unique=False)
    op.create_index(op.f('ix_sla_definitions_priority'), 'sla_definitions', ['priority'], unique=False)
    op.create_index(op.f('ix_sla_definitions_id'), 'sla_definitions', ['id'], unique=False)

    # Create ticket_slas table
    op.create_table(
        'ticket_slas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=True),
        sa.Column('sla_definition_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('active', 'paused', 'breached', 'achieved', 'cancelled', name='slastatus'), nullable=True),
        sa.Column('response_due_at', sa.DateTime(), nullable=True),
        sa.Column('response_met_at', sa.DateTime(), nullable=True),
        sa.Column('response_breached', sa.String(), nullable=True),
        sa.Column('resolution_due_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_met_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_breached', sa.String(), nullable=True),
        sa.Column('pause_start_at', sa.DateTime(), nullable=True),
        sa.Column('total_pause_minutes', sa.Integer(), nullable=True),
        sa.Column('warning_sent', sa.String(), nullable=True),
        sa.Column('breach_notified', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ),
        sa.ForeignKeyConstraint(['sla_definition_id'], ['sla_definitions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ticket_slas_ticket_id'), 'ticket_slas', ['ticket_id'], unique=False)
    op.create_index(op.f('ix_ticket_slas_id'), 'ticket_slas', ['id'], unique=False)

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.Enum('sla_warning', 'sla_breach', 'ticket_assigned', 'ticket_updated', 'ticket_resolved', 'approval_required', 'approval_completed', name='notificationtype'), nullable=True),
        sa.Column('status', sa.Enum('pending', 'sent', 'failed', 'cancelled', name='notificationstatus'), nullable=True),
        sa.Column('recipient_id', sa.Integer(), nullable=True),
        sa.Column('recipient_email', sa.String(), nullable=True),
        sa.Column('recipient_group_id', sa.Integer(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('ticket_id', sa.Integer(), nullable=True),
        sa.Column('sla_id', sa.Integer(), nullable=True),
        sa.Column('webhook_url', sa.String(), nullable=True),
        sa.Column('webhook_payload', sa.Text(), nullable=True),
        sa.Column('webhook_response', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['recipient_group_id'], ['assignment_groups.id'], ),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ),
        sa.ForeignKeyConstraint(['sla_id'], ['ticket_slas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)


def downgrade():
    """Drop all tables"""
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')

    op.drop_index(op.f('ix_ticket_slas_id'), table_name='ticket_slas')
    op.drop_index(op.f('ix_ticket_slas_ticket_id'), table_name='ticket_slas')
    op.drop_table('ticket_slas')

    op.drop_index(op.f('ix_sla_definitions_id'), table_name='sla_definitions')
    op.drop_index(op.f('ix_sla_definitions_priority'), table_name='sla_definitions')
    op.drop_index(op.f('ix_sla_definitions_name'), table_name='sla_definitions')
    op.drop_table('sla_definitions')

    op.drop_index(op.f('ix_category_assignment_mappings_id'), table_name='category_assignment_mappings')
    op.drop_index(op.f('ix_category_assignment_mappings_category'), table_name='category_assignment_mappings')
    op.drop_table('category_assignment_mappings')

    op.drop_index(op.f('ix_assignment_group_members_id'), table_name='assignment_group_members')
    op.drop_table('assignment_group_members')

    op.drop_index(op.f('ix_assignment_groups_id'), table_name='assignment_groups')
    op.drop_index(op.f('ix_assignment_groups_name'), table_name='assignment_groups')
    op.drop_table('assignment_groups')

    op.drop_index(op.f('ix_approvals_id'), table_name='approvals')
    op.drop_table('approvals')

    op.drop_index(op.f('ix_tickets_servicenow_number'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_servicenow_sys_id'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_title'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_ticket_number'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_id'), table_name='tickets')
    op.drop_table('tickets')

    op.drop_index(op.f('ix_knowledge_articles_category'), table_name='knowledge_articles')
    op.drop_index(op.f('ix_knowledge_articles_title'), table_name='knowledge_articles')
    op.drop_index(op.f('ix_knowledge_articles_id'), table_name='knowledge_articles')
    op.drop_table('knowledge_articles')

    op.drop_index(op.f('ix_service_catalog_items_name'), table_name='service_catalog_items')
    op.drop_index(op.f('ix_service_catalog_items_id'), table_name='service_catalog_items')
    op.drop_table('service_catalog_items')

    op.drop_index(op.f('ix_incidents_title'), table_name='incidents')
    op.drop_index(op.f('ix_incidents_id'), table_name='incidents')
    op.drop_table('incidents')

    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
