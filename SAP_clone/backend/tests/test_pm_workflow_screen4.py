"""
Unit tests for PM Workflow Screen 4: Material Receipt & Service Entry
Requirements: 4.1, 4.2, 4.3, 4.4
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.pm_workflow_service import PMWorkflowService
from backend.models.pm_workflow_models import (
    WorkflowMaintenanceOrder, WorkflowPurchaseOrder, WorkflowGoodsReceipt,
    WorkflowOrderType, WorkflowOrderStatus, Priority, POType, POStatus
)


@pytest.mark.asyncio
class TestGoodsReceiptPosting:
    """Test goods receipt posting - Requirements 4.1, 4.2"""
    
    async def test_create_goods_receipt_for_material_po(self, db: AsyncSession):
        """Test posting goods receipt for material PO"""
        service = PMWorkflowService(db)
        
        # Create order
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        # Create material PO
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.MATERIAL,
            vendor_id="VENDOR-001",
            total_value=Decimal("500.00"),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Create goods receipt
        success, error_message, gr = await service.create_goods_receipt(
            po_number=po.po_number,
            material_number="MAT-001",
            quantity_received=Decimal("10.0"),
            storage_location="WH-01",
            received_by="warehouse_user",
            quality_passed=True,
            quality_notes=None
        )
        
        await db.commit()
        
        assert success is True
        assert error_message is None
        assert gr is not None
        assert gr.po_number == po.po_number
        assert gr.order_number == order.order_number
        assert gr.material_number == "MAT-001"
        assert gr.quantity_received == Decimal("10.0")
        assert gr.storage_location == "WH-01"
        assert gr.received_by == "warehouse_user"
        assert gr.gr_document.startswith("GR-")
    
    async def test_goods_receipt_updates_po_status(self, db: AsyncSession):
        """Test that goods receipt updates PO status to delivered"""
        service = PMWorkflowService(db)
        
        # Create order and PO
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.MATERIAL,
            vendor_id="VENDOR-001",
            total_value=Decimal("300.00"),
            delivery_date=datetime.utcnow() + timedelta(days=5),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Verify initial status
        assert po.status == POStatus.CREATED
        
        # Post goods receipt
        success, error_message, gr = await service.create_goods_receipt(
            po_number=po.po_number,
            material_number="MAT-002",
            quantity_received=Decimal("5.0"),
            storage_location="WH-02",
            received_by="warehouse_user",
            quality_passed=True,
            quality_notes=None
        )
        
        await db.commit()
        await db.refresh(po)
        
        assert success is True
        assert po.status == POStatus.DELIVERED
    
    async def test_goods_receipt_fails_for_service_only_po(self, db: AsyncSession):
        """Test that goods receipt cannot be posted for service-only PO"""
        service = PMWorkflowService(db)
        
        # Create order and service PO
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.SERVICE,
            vendor_id="VENDOR-002",
            total_value=Decimal("1000.00"),
            delivery_date=datetime.utcnow() + timedelta(days=10),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Attempt to post goods receipt
        success, error_message, gr = await service.create_goods_receipt(
            po_number=po.po_number,
            material_number="MAT-003",
            quantity_received=Decimal("1.0"),
            storage_location="WH-01",
            received_by="warehouse_user",
            quality_passed=True,
            quality_notes=None
        )
        
        assert success is False
        assert error_message is not None
        assert "service-only" in error_message.lower()
        assert gr is None
    
    async def test_goods_receipt_with_quality_inspection(self, db: AsyncSession):
        """Test goods receipt with quality inspection notes"""
        service = PMWorkflowService(db)
        
        # Create order and PO
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.MATERIAL,
            vendor_id="VENDOR-001",
            total_value=Decimal("750.00"),
            delivery_date=datetime.utcnow() + timedelta(days=3),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Post goods receipt with quality notes
        success, error_message, gr = await service.create_goods_receipt(
            po_number=po.po_number,
            material_number="MAT-CRITICAL",
            quantity_received=Decimal("20.0"),
            storage_location="QC-HOLD",
            received_by="qc_inspector",
            quality_passed=False,
            quality_notes="Minor surface defects detected, requires vendor review"
        )
        
        await db.commit()
        
        assert success is True
        assert gr is not None
        assert gr.storage_location == "QC-HOLD"
        assert gr.received_by == "qc_inspector"
    
    async def test_get_goods_receipts_for_order(self, db: AsyncSession):
        """Test retrieving all goods receipts for an order"""
        service = PMWorkflowService(db)
        
        # Create order and PO
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.MATERIAL,
            vendor_id="VENDOR-001",
            total_value=Decimal("1000.00"),
            delivery_date=datetime.utcnow() + timedelta(days=5),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Post multiple goods receipts
        await service.create_goods_receipt(
            po_number=po.po_number,
            material_number="MAT-001",
            quantity_received=Decimal("5.0"),
            storage_location="WH-01",
            received_by="user1",
            quality_passed=True,
            quality_notes=None
        )
        
        await service.create_goods_receipt(
            po_number=po.po_number,
            material_number="MAT-002",
            quantity_received=Decimal("10.0"),
            storage_location="WH-01",
            received_by="user2",
            quality_passed=True,
            quality_notes=None
        )
        
        await db.commit()
        
        # Retrieve all goods receipts
        grs = await service.get_goods_receipts_for_order(order.order_number)
        
        assert len(grs) == 2
        assert all(gr.order_number == order.order_number for gr in grs)


@pytest.mark.asyncio
class TestServiceEntryPosting:
    """Test service entry posting - Requirements 4.3, 4.4"""
    
    async def test_create_service_entry_for_service_po(self, db: AsyncSession):
        """Test posting service entry for service PO"""
        service = PMWorkflowService(db)
        
        # Create order
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        # Create service PO
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.SERVICE,
            vendor_id="VENDOR-SERVICE-001",
            total_value=Decimal("2000.00"),
            delivery_date=datetime.utcnow() + timedelta(days=14),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Create service entry
        acceptance_date = datetime.utcnow()
        success, error_message, se_doc = await service.create_service_entry(
            po_number=po.po_number,
            service_description="Equipment calibration and testing",
            hours_or_units=Decimal("16.0"),
            acceptance_date=acceptance_date,
            acceptor="supervisor_user",
            service_quality="excellent"
        )
        
        await db.commit()
        
        assert success is True
        assert error_message is None
        assert se_doc is not None
        assert se_doc.startswith("SE-")
    
    async def test_service_entry_updates_po_status(self, db: AsyncSession):
        """Test that service entry updates PO status to delivered"""
        service = PMWorkflowService(db)
        
        # Create order and service PO
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.SERVICE,
            vendor_id="VENDOR-SERVICE-002",
            total_value=Decimal("1500.00"),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Verify initial status
        assert po.status == POStatus.CREATED
        
        # Post service entry
        success, error_message, se_doc = await service.create_service_entry(
            po_number=po.po_number,
            service_description="Preventive maintenance service",
            hours_or_units=Decimal("8.0"),
            acceptance_date=datetime.utcnow(),
            acceptor="supervisor_user",
            service_quality="good"
        )
        
        await db.commit()
        await db.refresh(po)
        
        assert success is True
        assert po.status == POStatus.DELIVERED
    
    async def test_service_entry_fails_for_material_only_po(self, db: AsyncSession):
        """Test that service entry cannot be posted for material-only PO"""
        service = PMWorkflowService(db)
        
        # Create order and material PO
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.MATERIAL,
            vendor_id="VENDOR-MAT-001",
            total_value=Decimal("800.00"),
            delivery_date=datetime.utcnow() + timedelta(days=5),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Attempt to post service entry
        success, error_message, se_doc = await service.create_service_entry(
            po_number=po.po_number,
            service_description="This should fail",
            hours_or_units=Decimal("4.0"),
            acceptance_date=datetime.utcnow(),
            acceptor="supervisor_user",
            service_quality="acceptable"
        )
        
        assert success is False
        assert error_message is not None
        assert "material-only" in error_message.lower()
        assert se_doc is None
    
    async def test_service_entry_for_combined_po(self, db: AsyncSession):
        """Test posting service entry for combined PO"""
        service = PMWorkflowService(db)
        
        # Create order and combined PO
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.COMBINED,
            vendor_id="VENDOR-COMBINED-001",
            total_value=Decimal("3000.00"),
            delivery_date=datetime.utcnow() + timedelta(days=10),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Post service entry for combined PO
        success, error_message, se_doc = await service.create_service_entry(
            po_number=po.po_number,
            service_description="Installation and commissioning service",
            hours_or_units=Decimal("24.0"),
            acceptance_date=datetime.utcnow(),
            acceptor="project_manager",
            service_quality="excellent"
        )
        
        await db.commit()
        
        assert success is True
        assert se_doc is not None
    
    async def test_get_service_entries_for_order(self, db: AsyncSession):
        """Test retrieving all service entries for an order"""
        service = PMWorkflowService(db)
        
        # Create order and service PO
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.SERVICE,
            vendor_id="VENDOR-SERVICE-001",
            total_value=Decimal("2500.00"),
            delivery_date=datetime.utcnow() + timedelta(days=15),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Post multiple service entries
        await service.create_service_entry(
            po_number=po.po_number,
            service_description="Phase 1 service",
            hours_or_units=Decimal("10.0"),
            acceptance_date=datetime.utcnow(),
            acceptor="supervisor1",
            service_quality="good"
        )
        
        await service.create_service_entry(
            po_number=po.po_number,
            service_description="Phase 2 service",
            hours_or_units=Decimal("12.0"),
            acceptance_date=datetime.utcnow(),
            acceptor="supervisor2",
            service_quality="excellent"
        )
        
        await db.commit()
        
        # Retrieve all service entries
        entries = await service.get_service_entries_for_order(order.order_number)
        
        assert len(entries) == 2
        assert all(entry.order_number == order.order_number for entry in entries)


@pytest.mark.asyncio
class TestDeliveryVarianceHandling:
    """Test delivery variance handling - Requirement 4.4"""
    
    async def test_goods_receipt_with_quantity_variance(self, db: AsyncSession):
        """Test handling quantity variance in goods receipt"""
        service = PMWorkflowService(db)
        
        # Create order and PO
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.MATERIAL,
            vendor_id="VENDOR-001",
            total_value=Decimal("1000.00"),
            delivery_date=datetime.utcnow() + timedelta(days=5),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Post goods receipt with different quantity than ordered
        # (In real system, PO would have line items with quantities)
        success, error_message, gr = await service.create_goods_receipt(
            po_number=po.po_number,
            material_number="MAT-001",
            quantity_received=Decimal("8.0"),  # Received less than ordered
            storage_location="WH-01",
            received_by="warehouse_user",
            quality_passed=True,
            quality_notes="Partial delivery - 8 of 10 units received"
        )
        
        await db.commit()
        
        assert success is True
        assert gr is not None
        assert gr.quantity_received == Decimal("8.0")
    
    async def test_multiple_partial_deliveries(self, db: AsyncSession):
        """Test handling multiple partial deliveries for same PO"""
        service = PMWorkflowService(db)
        
        # Create order and PO
        order = await service.create_order(
            order_type=WorkflowOrderType.GENERAL,
            equipment_id="EQ-12345",
            functional_location=None,
            priority=Priority.NORMAL,
            planned_start_date=None,
            planned_end_date=None,
            breakdown_notification_id=None,
            created_by="test_user"
        )
        
        po = await service.create_purchase_order(
            order_number=order.order_number,
            po_type=POType.MATERIAL,
            vendor_id="VENDOR-001",
            total_value=Decimal("1500.00"),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            created_by="test_user"
        )
        
        await db.commit()
        
        # Post first partial delivery
        success1, _, gr1 = await service.create_goods_receipt(
            po_number=po.po_number,
            material_number="MAT-001",
            quantity_received=Decimal("5.0"),
            storage_location="WH-01",
            received_by="user1",
            quality_passed=True,
            quality_notes="First partial delivery"
        )
        
        # Post second partial delivery
        success2, _, gr2 = await service.create_goods_receipt(
            po_number=po.po_number,
            material_number="MAT-001",
            quantity_received=Decimal("5.0"),
            storage_location="WH-01",
            received_by="user2",
            quality_passed=True,
            quality_notes="Second partial delivery - complete"
        )
        
        await db.commit()
        
        assert success1 is True
        assert success2 is True
        assert gr1.gr_document != gr2.gr_document
        
        # Verify both receipts exist
        all_grs = await service.get_goods_receipts_for_order(order.order_number)
        assert len(all_grs) == 2
        total_received = sum(gr.quantity_received for gr in all_grs)
        assert total_received == Decimal("10.0")
