"""Create PM module tables

Revision ID: 003_create_pm_tables
Revises: 002_create_tickets
Create Date: 2024-01-15
"""
from typing import Sequence, Union
from alembic import op

revision: str = '003_create_pm_tables'
down_revision: Union[str, None] = '002_create_tickets'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("DO $$ BEGIN CREATE TYPE pm.asset_type_enum AS ENUM ('substation', 'transformer', 'feeder'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pm.asset_status_enum AS ENUM ('operational', 'under_maintenance', 'out_of_service', 'decommissioned'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pm.order_type_enum AS ENUM ('preventive', 'corrective', 'emergency'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pm.order_status_enum AS ENUM ('planned', 'in_progress', 'completed', 'cancelled'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pm.fault_type_enum AS ENUM ('fault', 'outage', 'degradation'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create assets table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm.assets (
            asset_id VARCHAR(50) PRIMARY KEY,
            asset_type pm.asset_type_enum NOT NULL,
            name VARCHAR(255) NOT NULL,
            location VARCHAR(255) NOT NULL,
            installation_date DATE NOT NULL,
            status pm.asset_status_enum NOT NULL DEFAULT 'operational',
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """)
    
    # Create maintenance_orders table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm.maintenance_orders (
            order_id VARCHAR(50) PRIMARY KEY,
            asset_id VARCHAR(50) NOT NULL REFERENCES pm.assets(asset_id) ON DELETE CASCADE,
            ticket_id VARCHAR(30) REFERENCES core.tickets(ticket_id) ON DELETE SET NULL,
            order_type pm.order_type_enum NOT NULL,
            status pm.order_status_enum NOT NULL DEFAULT 'planned',
            description TEXT NOT NULL,
            scheduled_date TIMESTAMP WITH TIME ZONE NOT NULL,
            completed_date TIMESTAMP WITH TIME ZONE,
            created_by VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """)
    
    # Create incidents table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm.incidents (
            incident_id VARCHAR(50) PRIMARY KEY,
            asset_id VARCHAR(50) NOT NULL REFERENCES pm.assets(asset_id) ON DELETE CASCADE,
            ticket_id VARCHAR(30) REFERENCES core.tickets(ticket_id) ON DELETE SET NULL,
            fault_type pm.fault_type_enum NOT NULL,
            description TEXT NOT NULL,
            reported_by VARCHAR(100) NOT NULL,
            reported_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            resolved_at TIMESTAMP WITH TIME ZONE
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS pm.incidents")
    op.execute("DROP TABLE IF EXISTS pm.maintenance_orders")
    op.execute("DROP TABLE IF EXISTS pm.assets")
    op.execute("DROP TYPE IF EXISTS pm.fault_type_enum")
    op.execute("DROP TYPE IF EXISTS pm.order_status_enum")
    op.execute("DROP TYPE IF EXISTS pm.order_type_enum")
    op.execute("DROP TYPE IF EXISTS pm.asset_status_enum")
    op.execute("DROP TYPE IF EXISTS pm.asset_type_enum")
