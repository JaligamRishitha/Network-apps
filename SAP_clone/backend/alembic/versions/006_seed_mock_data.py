"""Seed mock data for PM, MM, FI modules

Revision ID: 006_seed_mock_data
Revises: 005_create_fi_tables
Create Date: 2024-01-15
"""
from typing import Sequence, Union
from alembic import op

revision: str = '006_seed_mock_data'
down_revision: Union[str, None] = '005_create_fi_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PM Assets
    op.execute("""
        INSERT INTO pm.assets (asset_id, asset_type, name, location, installation_date, status, description, created_at) VALUES
        ('AST-001', 'substation', 'Main Substation Alpha', 'Building A, Floor 1', '2020-03-15', 'operational', 'Primary power distribution substation', NOW()),
        ('AST-002', 'transformer', 'Transformer T1-500kVA', 'Building A, Basement', '2019-06-20', 'operational', '500kVA step-down transformer', NOW()),
        ('AST-003', 'transformer', 'Transformer T2-250kVA', 'Building B, Ground Floor', '2021-01-10', 'under_maintenance', '250kVA backup transformer', NOW()),
        ('AST-004', 'feeder', 'Feeder Line F1', 'External Grid Connection', '2018-11-05', 'operational', 'Main feeder from grid', NOW()),
        ('AST-005', 'substation', 'Secondary Substation Beta', 'Building C, Floor 2', '2022-07-22', 'operational', 'Secondary distribution point', NOW())
        ON CONFLICT (asset_id) DO NOTHING
    """)

    # PM Maintenance Orders
    op.execute("""
        INSERT INTO pm.maintenance_orders (order_id, asset_id, order_type, status, description, scheduled_date, created_by, created_at) VALUES
        ('MO-001', 'AST-001', 'preventive', 'planned', 'Quarterly inspection of main substation', '2026-02-01 09:00:00+00', 'engineer', NOW()),
        ('MO-002', 'AST-002', 'corrective', 'in_progress', 'Replace cooling fan on transformer', '2026-01-20 10:00:00+00', 'engineer', NOW()),
        ('MO-003', 'AST-003', 'emergency', 'completed', 'Emergency repair after voltage spike', '2026-01-10 14:00:00+00', 'admin', NOW()),
        ('MO-004', 'AST-004', 'preventive', 'planned', 'Annual feeder line inspection', '2026-03-15 08:00:00+00', 'engineer', NOW())
        ON CONFLICT (order_id) DO NOTHING
    """)
    
    # PM Incidents
    op.execute("""
        INSERT INTO pm.incidents (incident_id, asset_id, fault_type, description, reported_by, reported_at) VALUES
        ('INC-001', 'AST-003', 'fault', 'Transformer overheating detected during routine check', 'engineer', NOW()),
        ('INC-002', 'AST-004', 'outage', 'Brief power outage due to grid fluctuation', 'manager', NOW()),
        ('INC-003', 'AST-002', 'degradation', 'Unusual noise from transformer cooling system', 'engineer', NOW())
        ON CONFLICT (incident_id) DO NOTHING
    """)

    # MM Materials
    op.execute("""
        INSERT INTO mm.materials (material_id, description, quantity, unit_of_measure, reorder_level, storage_location, created_at) VALUES
        ('MAT-001', 'Copper Wire 10mm', 500, 'meters', 100, 'Warehouse A, Shelf 1', NOW()),
        ('MAT-002', 'Circuit Breaker 100A', 25, 'pieces', 10, 'Warehouse A, Shelf 2', NOW()),
        ('MAT-003', 'Transformer Oil', 200, 'liters', 50, 'Warehouse B, Tank 1', NOW()),
        ('MAT-004', 'Insulation Tape', 150, 'rolls', 30, 'Warehouse A, Shelf 3', NOW()),
        ('MAT-005', 'Fuse 30A', 80, 'pieces', 20, 'Warehouse A, Shelf 4', NOW()),
        ('MAT-006', 'Safety Gloves', 45, 'pairs', 15, 'Warehouse C, Locker 1', NOW()),
        ('MAT-007', 'Cable Ties Pack', 300, 'packs', 50, 'Warehouse A, Shelf 5', NOW())
        ON CONFLICT (material_id) DO NOTHING
    """)
    
    # MM Stock Transactions
    op.execute("""
        INSERT INTO mm.stock_transactions (transaction_id, material_id, quantity_change, transaction_type, transaction_date, performed_by, reference_doc, notes) VALUES
        ('TXN-001', 'MAT-001', 200, 'receipt', NOW(), 'manager', 'PO-2026-001', 'Initial stock receipt'),
        ('TXN-002', 'MAT-002', 15, 'receipt', NOW(), 'manager', 'PO-2026-002', 'Restocking circuit breakers'),
        ('TXN-003', 'MAT-001', -50, 'issue', NOW(), 'engineer', 'WO-001', 'Issued for maintenance work'),
        ('TXN-004', 'MAT-003', -30, 'issue', NOW(), 'engineer', 'MO-002', 'Transformer oil change'),
        ('TXN-005', 'MAT-005', 10, 'adjustment', NOW(), 'manager', NULL, 'Inventory correction after audit')
        ON CONFLICT (transaction_id) DO NOTHING
    """)

    # FI Cost Centers
    op.execute("""
        INSERT INTO fi.cost_centers (cost_center_id, name, budget_amount, fiscal_year, responsible_manager, description, created_at) VALUES
        ('CC-001', 'Plant Maintenance Operations', 500000.00, 2026, 'John Smith', 'Budget for all PM activities', NOW()),
        ('CC-002', 'Materials & Procurement', 300000.00, 2026, 'Jane Doe', 'Budget for inventory and purchasing', NOW()),
        ('CC-003', 'Emergency Repairs', 150000.00, 2026, 'John Smith', 'Reserved for emergency maintenance', NOW()),
        ('CC-004', 'Capital Projects', 1000000.00, 2026, 'Mike Johnson', 'Major infrastructure upgrades', NOW()),
        ('CC-005', 'Training & Safety', 75000.00, 2026, 'Sarah Wilson', 'Staff training and safety equipment', NOW())
        ON CONFLICT (cost_center_id) DO NOTHING
    """)
    
    # FI Cost Entries
    op.execute("""
        INSERT INTO fi.cost_entries (entry_id, cost_center_id, amount, cost_type, description, created_by, entry_date) VALUES
        ('CE-001', 'CC-001', 15000.00, 'OPEX', 'Quarterly maintenance supplies', 'finance', NOW()),
        ('CE-002', 'CC-002', 8500.00, 'OPEX', 'Circuit breaker procurement', 'finance', NOW()),
        ('CE-003', 'CC-003', 25000.00, 'OPEX', 'Emergency transformer repair', 'finance', NOW()),
        ('CE-004', 'CC-004', 150000.00, 'CAPEX', 'New substation installation', 'finance', NOW()),
        ('CE-005', 'CC-001', 5000.00, 'OPEX', 'Routine inspection costs', 'finance', NOW())
        ON CONFLICT (entry_id) DO NOTHING
    """)
    
    # FI Approvals
    op.execute("""
        INSERT INTO fi.approvals (approval_id, cost_center_id, amount, justification, decision, requested_by, requested_at) VALUES
        ('APR-001', 'CC-004', 250000.00, 'New transformer purchase for Building D expansion', 'pending', 'engineer', NOW()),
        ('APR-002', 'CC-002', 45000.00, 'Bulk purchase of safety equipment', 'approved', 'manager', NOW()),
        ('APR-003', 'CC-003', 80000.00, 'Emergency generator installation', 'pending', 'engineer', NOW())
        ON CONFLICT (approval_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM fi.approvals WHERE approval_id IN ('APR-001', 'APR-002', 'APR-003')")
    op.execute("DELETE FROM fi.cost_entries WHERE entry_id IN ('CE-001', 'CE-002', 'CE-003', 'CE-004', 'CE-005')")
    op.execute("DELETE FROM fi.cost_centers WHERE cost_center_id IN ('CC-001', 'CC-002', 'CC-003', 'CC-004', 'CC-005')")
    op.execute("DELETE FROM mm.stock_transactions WHERE transaction_id IN ('TXN-001', 'TXN-002', 'TXN-003', 'TXN-004', 'TXN-005')")
    op.execute("DELETE FROM mm.materials WHERE material_id IN ('MAT-001', 'MAT-002', 'MAT-003', 'MAT-004', 'MAT-005', 'MAT-006', 'MAT-007')")
    op.execute("DELETE FROM pm.incidents WHERE incident_id IN ('INC-001', 'INC-002', 'INC-003')")
    op.execute("DELETE FROM pm.maintenance_orders WHERE order_id IN ('MO-001', 'MO-002', 'MO-003', 'MO-004')")
    op.execute("DELETE FROM pm.assets WHERE asset_id IN ('AST-001', 'AST-002', 'AST-003', 'AST-004', 'AST-005')")
