"""Create PM Workflow module tables for 6-screen workflow

Revision ID: 007_create_pm_workflow_tables
Revises: 006_seed_mock_data
Create Date: 2025-01-27
"""
from typing import Sequence, Union
from alembic import op

revision: str = '007_create_pm_workflow_tables'
down_revision: Union[str, None] = '006_seed_mock_data'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create pm_workflow schema
    op.execute("CREATE SCHEMA IF NOT EXISTS pm_workflow")
    
    # Create enum types
    op.execute("DO $$ BEGIN CREATE TYPE pm_workflow.workflow_order_type_enum AS ENUM ('general', 'breakdown'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pm_workflow.workflow_order_status_enum AS ENUM ('created', 'planned', 'released', 'in_progress', 'confirmed', 'teco'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pm_workflow.priority_enum AS ENUM ('low', 'normal', 'high', 'urgent'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pm_workflow.operation_status_enum AS ENUM ('planned', 'in_progress', 'confirmed'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pm_workflow.po_type_enum AS ENUM ('material', 'service', 'combined'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pm_workflow.po_status_enum AS ENUM ('created', 'ordered', 'partially_delivered', 'delivered'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pm_workflow.confirmation_type_enum AS ENUM ('internal', 'external'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE pm_workflow.document_type_enum AS ENUM ('order', 'po', 'gr', 'gi', 'confirmation', 'service_entry', 'teco'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create workflow_maintenance_orders table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm_workflow.workflow_maintenance_orders (
            order_number VARCHAR(50) PRIMARY KEY,
            order_type pm_workflow.workflow_order_type_enum NOT NULL,
            status pm_workflow.workflow_order_status_enum NOT NULL DEFAULT 'created',
            equipment_id VARCHAR(100),
            functional_location VARCHAR(255),
            priority pm_workflow.priority_enum NOT NULL DEFAULT 'normal',
            planned_start_date TIMESTAMP WITH TIME ZONE,
            planned_end_date TIMESTAMP WITH TIME ZONE,
            actual_start_date TIMESTAMP WITH TIME ZONE,
            actual_end_date TIMESTAMP WITH TIME ZONE,
            breakdown_notification_id VARCHAR(50),
            created_by VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            released_by VARCHAR(100),
            released_at TIMESTAMP WITH TIME ZONE,
            completed_by VARCHAR(100),
            completed_at TIMESTAMP WITH TIME ZONE
        )
    """)
    
    # Create indexes for workflow_maintenance_orders
    op.execute("CREATE INDEX IF NOT EXISTS idx_workflow_orders_status ON pm_workflow.workflow_maintenance_orders(status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_workflow_orders_created_at ON pm_workflow.workflow_maintenance_orders(created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_workflow_orders_equipment ON pm_workflow.workflow_maintenance_orders(equipment_id)")
    
    # Create workflow_operations table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm_workflow.workflow_operations (
            operation_id VARCHAR(50) PRIMARY KEY,
            order_number VARCHAR(50) NOT NULL REFERENCES pm_workflow.workflow_maintenance_orders(order_number) ON DELETE CASCADE,
            operation_number VARCHAR(10) NOT NULL,
            work_center VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            planned_hours NUMERIC(10, 2) NOT NULL,
            actual_hours NUMERIC(10, 2),
            status pm_workflow.operation_status_enum NOT NULL DEFAULT 'planned',
            technician_id VARCHAR(100),
            confirmation_date TIMESTAMP WITH TIME ZONE
        )
    """)
    
    # Create workflow_components table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm_workflow.workflow_components (
            component_id VARCHAR(50) PRIMARY KEY,
            order_number VARCHAR(50) NOT NULL REFERENCES pm_workflow.workflow_maintenance_orders(order_number) ON DELETE CASCADE,
            material_number VARCHAR(50),
            description VARCHAR(255) NOT NULL,
            quantity_required NUMERIC(10, 3) NOT NULL,
            quantity_issued NUMERIC(10, 3) NOT NULL DEFAULT 0,
            unit_of_measure VARCHAR(10) NOT NULL,
            estimated_cost NUMERIC(15, 2) NOT NULL,
            actual_cost NUMERIC(15, 2),
            has_master_data BOOLEAN NOT NULL DEFAULT TRUE,
            reservation_number VARCHAR(50)
        )
    """)
    
    # Create workflow_purchase_orders table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm_workflow.workflow_purchase_orders (
            po_number VARCHAR(50) PRIMARY KEY,
            order_number VARCHAR(50) NOT NULL REFERENCES pm_workflow.workflow_maintenance_orders(order_number) ON DELETE CASCADE,
            po_type pm_workflow.po_type_enum NOT NULL,
            vendor_id VARCHAR(50) NOT NULL,
            total_value NUMERIC(15, 2) NOT NULL,
            delivery_date TIMESTAMP WITH TIME ZONE NOT NULL,
            status pm_workflow.po_status_enum NOT NULL DEFAULT 'created',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    
    # Create workflow_goods_receipts table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm_workflow.workflow_goods_receipts (
            gr_document VARCHAR(50) PRIMARY KEY,
            po_number VARCHAR(50) NOT NULL REFERENCES pm_workflow.workflow_purchase_orders(po_number) ON DELETE CASCADE,
            order_number VARCHAR(50) NOT NULL REFERENCES pm_workflow.workflow_maintenance_orders(order_number) ON DELETE CASCADE,
            material_number VARCHAR(50) NOT NULL,
            quantity_received NUMERIC(10, 3) NOT NULL,
            receipt_date TIMESTAMP WITH TIME ZONE NOT NULL,
            storage_location VARCHAR(100) NOT NULL,
            received_by VARCHAR(100) NOT NULL
        )
    """)
    
    # Create workflow_goods_issues table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm_workflow.workflow_goods_issues (
            gi_document VARCHAR(50) PRIMARY KEY,
            order_number VARCHAR(50) NOT NULL REFERENCES pm_workflow.workflow_maintenance_orders(order_number) ON DELETE CASCADE,
            component_id VARCHAR(50) NOT NULL REFERENCES pm_workflow.workflow_components(component_id) ON DELETE CASCADE,
            material_number VARCHAR(50) NOT NULL,
            quantity_issued NUMERIC(10, 3) NOT NULL,
            issue_date TIMESTAMP WITH TIME ZONE NOT NULL,
            cost_center VARCHAR(50) NOT NULL,
            issued_by VARCHAR(100) NOT NULL
        )
    """)
    
    # Create index for GI-before-confirmation validation
    op.execute("CREATE INDEX IF NOT EXISTS idx_workflow_gi_order_date ON pm_workflow.workflow_goods_issues(order_number, issue_date)")
    
    # Create workflow_confirmations table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm_workflow.workflow_confirmations (
            confirmation_id VARCHAR(50) PRIMARY KEY,
            order_number VARCHAR(50) NOT NULL REFERENCES pm_workflow.workflow_maintenance_orders(order_number) ON DELETE CASCADE,
            operation_id VARCHAR(50) NOT NULL REFERENCES pm_workflow.workflow_operations(operation_id) ON DELETE CASCADE,
            confirmation_type pm_workflow.confirmation_type_enum NOT NULL,
            actual_hours NUMERIC(10, 2) NOT NULL,
            confirmation_date TIMESTAMP WITH TIME ZONE NOT NULL,
            technician_id VARCHAR(100),
            vendor_id VARCHAR(100),
            work_notes TEXT,
            confirmed_by VARCHAR(100) NOT NULL
        )
    """)
    
    # Create index for confirmation date validation
    op.execute("CREATE INDEX IF NOT EXISTS idx_workflow_conf_order_date ON pm_workflow.workflow_confirmations(order_number, confirmation_date)")
    
    # Create workflow_malfunction_reports table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm_workflow.workflow_malfunction_reports (
            report_id VARCHAR(50) PRIMARY KEY,
            order_number VARCHAR(50) NOT NULL REFERENCES pm_workflow.workflow_maintenance_orders(order_number) ON DELETE CASCADE,
            cause_code VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            root_cause TEXT,
            corrective_action TEXT,
            reported_by VARCHAR(100) NOT NULL,
            reported_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    
    # Create workflow_document_flow table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm_workflow.workflow_document_flow (
            flow_id VARCHAR(50) PRIMARY KEY,
            order_number VARCHAR(50) NOT NULL REFERENCES pm_workflow.workflow_maintenance_orders(order_number) ON DELETE CASCADE,
            document_type pm_workflow.document_type_enum NOT NULL,
            document_number VARCHAR(50) NOT NULL,
            transaction_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            user_id VARCHAR(100) NOT NULL,
            status VARCHAR(50) NOT NULL,
            related_document VARCHAR(50)
        )
    """)
    
    # Create index for document flow queries
    op.execute("CREATE INDEX IF NOT EXISTS idx_workflow_docflow_order ON pm_workflow.workflow_document_flow(order_number, transaction_date)")
    
    # Create workflow_cost_summaries table
    op.execute("""
        CREATE TABLE IF NOT EXISTS pm_workflow.workflow_cost_summaries (
            order_number VARCHAR(50) PRIMARY KEY REFERENCES pm_workflow.workflow_maintenance_orders(order_number) ON DELETE CASCADE,
            estimated_material_cost NUMERIC(15, 2) NOT NULL DEFAULT 0,
            estimated_labor_cost NUMERIC(15, 2) NOT NULL DEFAULT 0,
            estimated_external_cost NUMERIC(15, 2) NOT NULL DEFAULT 0,
            estimated_total_cost NUMERIC(15, 2) NOT NULL DEFAULT 0,
            actual_material_cost NUMERIC(15, 2) NOT NULL DEFAULT 0,
            actual_labor_cost NUMERIC(15, 2) NOT NULL DEFAULT 0,
            actual_external_cost NUMERIC(15, 2) NOT NULL DEFAULT 0,
            actual_total_cost NUMERIC(15, 2) NOT NULL DEFAULT 0,
            material_variance NUMERIC(15, 2) NOT NULL DEFAULT 0,
            labor_variance NUMERIC(15, 2) NOT NULL DEFAULT 0,
            external_variance NUMERIC(15, 2) NOT NULL DEFAULT 0,
            total_variance NUMERIC(15, 2) NOT NULL DEFAULT 0,
            variance_percentage NUMERIC(5, 2) NOT NULL DEFAULT 0
        )
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.execute("DROP TABLE IF EXISTS pm_workflow.workflow_cost_summaries")
    op.execute("DROP TABLE IF EXISTS pm_workflow.workflow_document_flow")
    op.execute("DROP TABLE IF EXISTS pm_workflow.workflow_malfunction_reports")
    op.execute("DROP TABLE IF EXISTS pm_workflow.workflow_confirmations")
    op.execute("DROP TABLE IF EXISTS pm_workflow.workflow_goods_issues")
    op.execute("DROP TABLE IF EXISTS pm_workflow.workflow_goods_receipts")
    op.execute("DROP TABLE IF EXISTS pm_workflow.workflow_purchase_orders")
    op.execute("DROP TABLE IF EXISTS pm_workflow.workflow_components")
    op.execute("DROP TABLE IF EXISTS pm_workflow.workflow_operations")
    op.execute("DROP TABLE IF EXISTS pm_workflow.workflow_maintenance_orders")
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS pm_workflow.document_type_enum")
    op.execute("DROP TYPE IF EXISTS pm_workflow.confirmation_type_enum")
    op.execute("DROP TYPE IF EXISTS pm_workflow.po_status_enum")
    op.execute("DROP TYPE IF EXISTS pm_workflow.po_type_enum")
    op.execute("DROP TYPE IF EXISTS pm_workflow.operation_status_enum")
    op.execute("DROP TYPE IF EXISTS pm_workflow.priority_enum")
    op.execute("DROP TYPE IF EXISTS pm_workflow.workflow_order_status_enum")
    op.execute("DROP TYPE IF EXISTS pm_workflow.workflow_order_type_enum")
    
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS pm_workflow CASCADE")
