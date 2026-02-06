"""Create FI module tables

Revision ID: 005_create_fi_tables
Revises: 004_create_mm_tables
Create Date: 2024-01-15
"""
from typing import Sequence, Union
from alembic import op

revision: str = '005_create_fi_tables'
down_revision: Union[str, None] = '004_create_mm_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("DO $$ BEGIN CREATE TYPE fi.cost_type_enum AS ENUM ('CAPEX', 'OPEX'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE fi.approval_decision_enum AS ENUM ('pending', 'approved', 'rejected'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create cost_centers table
    op.execute("""
        CREATE TABLE IF NOT EXISTS fi.cost_centers (
            cost_center_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            budget_amount NUMERIC(15, 2) NOT NULL,
            fiscal_year INTEGER NOT NULL,
            responsible_manager VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """)
    
    # Create cost_entries table
    op.execute("""
        CREATE TABLE IF NOT EXISTS fi.cost_entries (
            entry_id VARCHAR(50) PRIMARY KEY,
            ticket_id VARCHAR(30) REFERENCES core.tickets(ticket_id) ON DELETE SET NULL,
            cost_center_id VARCHAR(50) NOT NULL REFERENCES fi.cost_centers(cost_center_id) ON DELETE CASCADE,
            amount NUMERIC(15, 2) NOT NULL,
            cost_type fi.cost_type_enum NOT NULL,
            description TEXT,
            entry_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            created_by VARCHAR(100) NOT NULL
        )
    """)
    
    # Create approvals table
    op.execute("""
        CREATE TABLE IF NOT EXISTS fi.approvals (
            approval_id VARCHAR(50) PRIMARY KEY,
            ticket_id VARCHAR(30) REFERENCES core.tickets(ticket_id) ON DELETE SET NULL,
            cost_center_id VARCHAR(50) NOT NULL REFERENCES fi.cost_centers(cost_center_id) ON DELETE CASCADE,
            amount NUMERIC(15, 2) NOT NULL,
            justification TEXT NOT NULL,
            approval_hierarchy JSONB,
            decision fi.approval_decision_enum NOT NULL DEFAULT 'pending',
            requested_by VARCHAR(100) NOT NULL,
            requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            decided_by VARCHAR(100),
            decided_at TIMESTAMP WITH TIME ZONE,
            decision_comment TEXT
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS fi.approvals")
    op.execute("DROP TABLE IF EXISTS fi.cost_entries")
    op.execute("DROP TABLE IF EXISTS fi.cost_centers")
    op.execute("DROP TYPE IF EXISTS fi.approval_decision_enum")
    op.execute("DROP TYPE IF EXISTS fi.cost_type_enum")
