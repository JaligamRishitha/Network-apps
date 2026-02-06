"""Create Work Order Flow tables for PM → MM → FI workflow

Revision ID: 008_create_work_order_flow_tables
Revises: 007_create_pm_workflow_tables
Create Date: 2024-01-29
"""
from typing import Sequence, Union
from alembic import op

revision: str = '008_work_order_flow'
down_revision: Union[str, None] = '007_create_pm_workflow_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create work order flow status enum in pm schema
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE pm.work_order_flow_status_enum AS ENUM (
                'received',
                'pending_material_check',
                'materials_available',
                'materials_shortage',
                'purchase_requested',
                'purchase_approved',
                'purchase_rejected',
                'ready_to_proceed',
                'in_progress',
                'completed',
                'cancelled'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create CRM Work Orders table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm.crm_work_orders (
            work_order_id VARCHAR(50) PRIMARY KEY,
            crm_reference_id VARCHAR(100),
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            customer_name VARCHAR(255) NOT NULL,
            customer_contact VARCHAR(255),
            site_location VARCHAR(500) NOT NULL,
            priority VARCHAR(20) NOT NULL DEFAULT 'medium',
            flow_status pm.work_order_flow_status_enum NOT NULL DEFAULT 'received',
            requested_date TIMESTAMP WITH TIME ZONE NOT NULL,
            scheduled_date TIMESTAMP WITH TIME ZONE,
            completed_date TIMESTAMP WITH TIME ZONE,
            pm_maintenance_order_id VARCHAR(50),
            pm_ticket_id VARCHAR(30),
            fi_approval_id VARCHAR(50),
            fi_ticket_id VARCHAR(30),
            cost_center_id VARCHAR(50) NOT NULL,
            estimated_material_cost NUMERIC(15, 2),
            created_by VARCHAR(100) NOT NULL,
            assigned_to VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            materials_check_summary JSONB
        )
    """)

    # Create Work Order Materials table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm.work_order_materials (
            id SERIAL PRIMARY KEY,
            work_order_id VARCHAR(50) NOT NULL REFERENCES pm.crm_work_orders(work_order_id) ON DELETE CASCADE,
            material_id VARCHAR(50) NOT NULL,
            material_description VARCHAR(500) NOT NULL,
            quantity_required INTEGER NOT NULL,
            unit_of_measure VARCHAR(20) NOT NULL,
            quantity_available INTEGER,
            is_available BOOLEAN,
            shortage_quantity INTEGER,
            requisition_id VARCHAR(50),
            unit_price NUMERIC(15, 2),
            checked_at TIMESTAMP WITH TIME ZONE
        )
    """)

    # Create Work Order Flow History table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm.work_order_flow_history (
            id SERIAL PRIMARY KEY,
            work_order_id VARCHAR(50) NOT NULL REFERENCES pm.crm_work_orders(work_order_id) ON DELETE CASCADE,
            from_status pm.work_order_flow_status_enum NOT NULL,
            to_status pm.work_order_flow_status_enum NOT NULL,
            triggered_by_module VARCHAR(20) NOT NULL,
            performed_by VARCHAR(100) NOT NULL,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)

    # Create indexes for better query performance
    op.execute("CREATE INDEX IF NOT EXISTS idx_crm_work_orders_status ON pm.crm_work_orders(flow_status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_crm_work_orders_customer ON pm.crm_work_orders(customer_name)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_crm_work_orders_created_at ON pm.crm_work_orders(created_at DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_work_order_materials_work_order ON pm.work_order_materials(work_order_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_work_order_materials_material ON pm.work_order_materials(material_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_work_order_flow_history_work_order ON pm.work_order_flow_history(work_order_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS pm.idx_work_order_flow_history_work_order")
    op.execute("DROP INDEX IF EXISTS pm.idx_work_order_materials_material")
    op.execute("DROP INDEX IF EXISTS pm.idx_work_order_materials_work_order")
    op.execute("DROP INDEX IF EXISTS pm.idx_crm_work_orders_created_at")
    op.execute("DROP INDEX IF EXISTS pm.idx_crm_work_orders_customer")
    op.execute("DROP INDEX IF EXISTS pm.idx_crm_work_orders_status")
    op.execute("DROP TABLE IF EXISTS pm.work_order_flow_history")
    op.execute("DROP TABLE IF EXISTS pm.work_order_materials")
    op.execute("DROP TABLE IF EXISTS pm.crm_work_orders")
    op.execute("DROP TYPE IF EXISTS pm.work_order_flow_status_enum")
