"""Create MM module tables

Revision ID: 004_create_mm_tables
Revises: 003_create_pm_tables
Create Date: 2024-01-15
"""
from typing import Sequence, Union
from alembic import op

revision: str = '004_create_mm_tables'
down_revision: Union[str, None] = '003_create_pm_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("DO $$ BEGIN CREATE TYPE mm.transaction_type_enum AS ENUM ('receipt', 'issue', 'adjustment'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE mm.requisition_status_enum AS ENUM ('pending', 'approved', 'rejected', 'ordered', 'received'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create materials table
    op.execute("""
        CREATE TABLE IF NOT EXISTS mm.materials (
            material_id VARCHAR(50) PRIMARY KEY,
            description VARCHAR(500) NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            unit_of_measure VARCHAR(20) NOT NULL,
            reorder_level INTEGER NOT NULL DEFAULT 0,
            storage_location VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """)
    
    # Create stock_transactions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS mm.stock_transactions (
            transaction_id VARCHAR(50) PRIMARY KEY,
            material_id VARCHAR(50) NOT NULL REFERENCES mm.materials(material_id) ON DELETE CASCADE,
            quantity_change INTEGER NOT NULL,
            transaction_type mm.transaction_type_enum NOT NULL,
            transaction_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            performed_by VARCHAR(100) NOT NULL,
            reference_doc VARCHAR(100),
            notes TEXT
        )
    """)
    
    # Create requisitions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS mm.requisitions (
            requisition_id VARCHAR(50) PRIMARY KEY,
            material_id VARCHAR(50) NOT NULL REFERENCES mm.materials(material_id) ON DELETE CASCADE,
            ticket_id VARCHAR(30) REFERENCES core.tickets(ticket_id) ON DELETE SET NULL,
            cost_center_id VARCHAR(50) NOT NULL,
            quantity INTEGER NOT NULL,
            justification TEXT NOT NULL,
            status mm.requisition_status_enum NOT NULL DEFAULT 'pending',
            requested_by VARCHAR(100) NOT NULL,
            requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            approved_by VARCHAR(100),
            approved_at TIMESTAMP WITH TIME ZONE
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS mm.requisitions")
    op.execute("DROP TABLE IF EXISTS mm.stock_transactions")
    op.execute("DROP TABLE IF EXISTS mm.materials")
    op.execute("DROP TYPE IF EXISTS mm.requisition_status_enum")
    op.execute("DROP TYPE IF EXISTS mm.transaction_type_enum")
