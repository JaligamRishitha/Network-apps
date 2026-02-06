"""Create tickets and audit_entries tables

Revision ID: 002_create_tickets
Revises: 001_create_schemas
Create Date: 2024-01-15

Requirements: 1.1, 1.2, 1.4 - Unified ticketing with ID format, types, and audit trail
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002_create_tickets'
down_revision: Union[str, None] = '001_create_schemas'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types (IF NOT EXISTS)
    op.execute("DO $$ BEGIN CREATE TYPE core.ticket_type_enum AS ENUM ('Incident', 'Maintenance', 'Procurement', 'Finance_Approval'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE core.module_enum AS ENUM ('PM', 'MM', 'FI'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE core.priority_enum AS ENUM ('P1', 'P2', 'P3', 'P4'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE core.ticket_status_enum AS ENUM ('Open', 'Assigned', 'In_Progress', 'Closed'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create tickets table
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.tickets (
            ticket_id VARCHAR(30) PRIMARY KEY,
            ticket_type core.ticket_type_enum NOT NULL,
            module core.module_enum NOT NULL,
            priority core.priority_enum NOT NULL,
            status core.ticket_status_enum NOT NULL DEFAULT 'Open',
            title VARCHAR(255) NOT NULL,
            description TEXT,
            sla_deadline TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            created_by VARCHAR(100) NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE,
            assigned_to VARCHAR(100),
            correlation_id VARCHAR(36)
        )
    """)
    
    # Create audit_entries table
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.audit_entries (
            entry_id SERIAL PRIMARY KEY,
            ticket_id VARCHAR(30) NOT NULL REFERENCES core.tickets(ticket_id) ON DELETE CASCADE,
            previous_status core.ticket_status_enum NOT NULL,
            new_status core.ticket_status_enum NOT NULL,
            changed_by VARCHAR(100) NOT NULL,
            changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            comment TEXT
        )
    """)
    
    # Create indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_module ON core.tickets(module)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_status ON core.tickets(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_created_at ON core.tickets(created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_entries_ticket_id ON core.audit_entries(ticket_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS core.ix_audit_entries_ticket_id")
    op.execute("DROP INDEX IF EXISTS core.ix_tickets_created_at")
    op.execute("DROP INDEX IF EXISTS core.ix_tickets_status")
    op.execute("DROP INDEX IF EXISTS core.ix_tickets_module")
    op.execute("DROP TABLE IF EXISTS core.audit_entries")
    op.execute("DROP TABLE IF EXISTS core.tickets")
    op.execute("DROP TYPE IF EXISTS core.ticket_status_enum")
    op.execute("DROP TYPE IF EXISTS core.priority_enum")
    op.execute("DROP TYPE IF EXISTS core.module_enum")
    op.execute("DROP TYPE IF EXISTS core.ticket_type_enum")
