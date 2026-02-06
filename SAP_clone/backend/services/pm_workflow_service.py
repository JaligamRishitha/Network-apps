"""
PM Workflow Service - Business logic for 6-screen workflow
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.pm_workflow_models import (
    WorkflowMaintenanceOrder, WorkflowOperation, WorkflowComponent,
    WorkflowCostSummary, WorkflowDocumentFlow, WorkflowPurchaseOrder,
    WorkflowOrderType, WorkflowOrderStatus, Priority, OperationStatus,
    DocumentType, POType, POStatus
)
from backend.services.pm_workflow_state_machine import get_state_machine


class PMWorkflowService:
    """Service for PM workflow operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.state_machine = get_state_machine()
    
    async def create_order(
        self,
        order_type: WorkflowOrderType,
        equipment_id: Optional[str],
        functional_location: Optional[str],
        priority: Priority,
        planned_start_date: Optional[datetime],
        planned_end_date: Optional[datetime],
        breakdown_notification_id: Optional[str],
        created_by: str
    ) -> WorkflowMaintenanceOrder:
        """
        Create a new maintenance order.
        Requirements: 1.1, 1.2, 1.7
        """
        # Generate order number
        order_number = self._generate_order_number(order_type)
        
        # Create order
        order = WorkflowMaintenanceOrder(
            order_number=order_number,
            order_type=order_type,
            status=WorkflowOrderStatus.CREATED,
            equipment_id=equipment_id,
            functional_location=functional_location,
            priority=priority,
            planned_start_date=planned_start_date,
            planned_end_date=planned_end_date,
            breakdown_notification_id=breakdown_notification_id,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        
        self.db.add(order)
        await self.db.flush()
        
        # Create document flow entry
        await self._create_document_flow_entry(
            order_number=order_number,
            document_type=DocumentType.ORDER,
            document_number=order_number,
            user_id=created_by,
            status=WorkflowOrderStatus.CREATED.value
        )
        
        return order
    
    async def get_order(self, order_number: str) -> Optional[WorkflowMaintenanceOrder]:
        """Get order with all relationships"""
        result = await self.db.execute(
            select(WorkflowMaintenanceOrder)
            .where(WorkflowMaintenanceOrder.order_number == order_number)
            .options(
                selectinload(WorkflowMaintenanceOrder.operations),
                selectinload(WorkflowMaintenanceOrder.components),
                selectinload(WorkflowMaintenanceOrder.cost_summary)
            )
        )
        return result.scalar_one_or_none()
    
    async def add_operation(
        self,
        order_number: str,
        operation_number: str,
        work_center: str,
        description: str,
        planned_hours: Decimal,
        technician_id: Optional[str] = None
    ) -> WorkflowOperation:
        """
        Add operation to order.
        Requirement 1.3
        """
        operation_id = f"{order_number}-OP-{operation_number}"
        
        operation = WorkflowOperation(
            operation_id=operation_id,
            order_number=order_number,
            operation_number=operation_number,
            work_center=work_center,
            description=description,
            planned_hours=planned_hours,
            status=OperationStatus.PLANNED,
            technician_id=technician_id
        )
        
        self.db.add(operation)
        await self.db.flush()
        
        return operation
    
    async def update_operation(
        self,
        operation_id: str,
        work_center: str,
        description: str,
        planned_hours: Decimal,
        technician_id: Optional[str] = None
    ) -> Optional[WorkflowOperation]:
        """Update operation - Requirement 1.3"""
        result = await self.db.execute(
            select(WorkflowOperation)
            .where(WorkflowOperation.operation_id == operation_id)
        )
        operation = result.scalar_one_or_none()
        
        if operation:
            operation.work_center = work_center
            operation.description = description
            operation.planned_hours = planned_hours
            operation.technician_id = technician_id
            await self.db.flush()
        
        return operation
    
    async def delete_operation(self, operation_id: str) -> bool:
        """Delete operation - Requirement 1.3"""
        result = await self.db.execute(
            select(WorkflowOperation)
            .where(WorkflowOperation.operation_id == operation_id)
        )
        operation = result.scalar_one_or_none()
        
        if operation:
            await self.db.delete(operation)
            await self.db.flush()
            return True
        
        return False
    
    async def add_component(
        self,
        order_number: str,
        material_number: Optional[str],
        description: str,
        quantity_required: Decimal,
        unit_of_measure: str,
        estimated_cost: Decimal,
        has_master_data: bool = True
    ) -> WorkflowComponent:
        """
        Add component to order.
        Requirement 1.4
        """
        component_id = f"{order_number}-COMP-{uuid.uuid4().hex[:8]}"
        
        component = WorkflowComponent(
            component_id=component_id,
            order_number=order_number,
            material_number=material_number,
            description=description,
            quantity_required=quantity_required,
            quantity_issued=Decimal(0),
            unit_of_measure=unit_of_measure,
            estimated_cost=estimated_cost,
            has_master_data=has_master_data
        )
        
        self.db.add(component)
        await self.db.flush()
        
        return component
    
    async def update_component(
        self,
        component_id: str,
        material_number: Optional[str],
        description: str,
        quantity_required: Decimal,
        unit_of_measure: str,
        estimated_cost: Decimal,
        has_master_data: bool
    ) -> Optional[WorkflowComponent]:
        """Update component - Requirement 1.4"""
        result = await self.db.execute(
            select(WorkflowComponent)
            .where(WorkflowComponent.component_id == component_id)
        )
        component = result.scalar_one_or_none()
        
        if component:
            component.material_number = material_number
            component.description = description
            component.quantity_required = quantity_required
            component.unit_of_measure = unit_of_measure
            component.estimated_cost = estimated_cost
            component.has_master_data = has_master_data
            await self.db.flush()
        
        return component
    
    async def delete_component(self, component_id: str) -> bool:
        """Delete component - Requirement 1.4"""
        result = await self.db.execute(
            select(WorkflowComponent)
            .where(WorkflowComponent.component_id == component_id)
        )
        component = result.scalar_one_or_none()
        
        if component:
            await self.db.delete(component)
            await self.db.flush()
            return True
        
        return False
    
    async def calculate_cost_estimate(
        self,
        order_number: str
    ) -> Optional[WorkflowCostSummary]:
        """
        Calculate cost estimate for order.
        Requirement 1.5
        
        Delegates to CostManagementService for comprehensive cost calculation.
        """
        from backend.services.pm_workflow_cost_service import CostManagementService
        
        cost_service = CostManagementService(self.db)
        return await cost_service.calculate_cost_estimate(order_number)
    
    async def _create_document_flow_entry(
        self,
        order_number: str,
        document_type: DocumentType,
        document_number: str,
        user_id: str,
        status: str,
        related_document: Optional[str] = None
    ) -> WorkflowDocumentFlow:
        """Create document flow entry for audit trail"""
        flow_id = f"FLOW-{uuid.uuid4().hex[:12]}"
        
        flow_entry = WorkflowDocumentFlow(
            flow_id=flow_id,
            order_number=order_number,
            document_type=document_type,
            document_number=document_number,
            transaction_date=datetime.utcnow(),
            user_id=user_id,
            status=status,
            related_document=related_document
        )
        
        self.db.add(flow_entry)
        await self.db.flush()
        
        return flow_entry
    
    def _generate_order_number(self, order_type: WorkflowOrderType) -> str:
        """Generate unique order number"""
        prefix = "BD" if order_type == WorkflowOrderType.BREAKDOWN else "PM"
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{timestamp}-{random_suffix}"
    
    # Screen 2: Procurement & Material Planning
    
    async def create_purchase_order(
        self,
        order_number: str,
        po_type: POType,
        vendor_id: str,
        total_value: Decimal,
        delivery_date: datetime,
        created_by: str
    ) -> WorkflowPurchaseOrder:
        """
        Create purchase order for materials or services.
        Requirements: 2.1, 2.2, 2.3, 2.4
        """
        # Verify order exists
        order = await self.get_order(order_number)
        if not order:
            raise ValueError(f"Order not found: {order_number}")
        
        # Generate PO number
        po_number = self._generate_po_number(po_type)
        
        # Create PO
        po = WorkflowPurchaseOrder(
            po_number=po_number,
            order_number=order_number,
            po_type=po_type,
            vendor_id=vendor_id,
            total_value=total_value,
            delivery_date=delivery_date,
            status=POStatus.CREATED,
            created_at=datetime.utcnow()
        )
        
        self.db.add(po)
        await self.db.flush()
        
        # Create document flow entry
        await self._create_document_flow_entry(
            order_number=order_number,
            document_type=DocumentType.PO,
            document_number=po_number,
            user_id=created_by,
            status=POStatus.CREATED.value,
            related_document=order_number
        )
        
        return po
    
    async def get_purchase_order(self, po_number: str) -> Optional[WorkflowPurchaseOrder]:
        """Get purchase order by number"""
        result = await self.db.execute(
            select(WorkflowPurchaseOrder)
            .where(WorkflowPurchaseOrder.po_number == po_number)
            .options(selectinload(WorkflowPurchaseOrder.order))
        )
        return result.scalar_one_or_none()
    
    async def get_order_purchase_orders(self, order_number: str) -> List[WorkflowPurchaseOrder]:
        """
        Get all purchase orders for a maintenance order.
        Requirement 2.5
        """
        result = await self.db.execute(
            select(WorkflowPurchaseOrder)
            .where(WorkflowPurchaseOrder.order_number == order_number)
            .order_by(WorkflowPurchaseOrder.created_at)
        )
        return list(result.scalars().all())
    
    async def update_po_status(
        self,
        po_number: str,
        status: POStatus,
        updated_by: str
    ) -> Optional[WorkflowPurchaseOrder]:
        """
        Update purchase order status.
        Requirement 2.5
        """
        po = await self.get_purchase_order(po_number)
        
        if not po:
            return None
        
        old_status = po.status
        po.status = status
        await self.db.flush()
        
        # Create document flow entry for status change
        await self._create_document_flow_entry(
            order_number=po.order_number,
            document_type=DocumentType.PO,
            document_number=po_number,
            user_id=updated_by,
            status=f"{old_status.value} -> {status.value}",
            related_document=po.order_number
        )
        
        return po
    
    async def get_procurement_document_flow(self, order_number: str) -> List[WorkflowDocumentFlow]:
        """
        Get procurement-related document flow for order.
        Requirement 2.6
        """
        result = await self.db.execute(
            select(WorkflowDocumentFlow)
            .where(
                WorkflowDocumentFlow.order_number == order_number,
                WorkflowDocumentFlow.document_type.in_([DocumentType.PO, DocumentType.GR, DocumentType.SERVICE_ENTRY])
            )
            .order_by(WorkflowDocumentFlow.transaction_date)
        )
        return list(result.scalars().all())
    
    def _generate_po_number(self, po_type: POType) -> str:
        """Generate unique PO number"""
        prefix_map = {
            POType.MATERIAL: "PO-MAT",
            POType.SERVICE: "PO-SRV",
            POType.COMBINED: "PO-CMB"
        }
        prefix = prefix_map[po_type]
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{timestamp}-{random_suffix}"
    
    # Screen 4: Material Receipt & Service Entry
    
    async def create_goods_receipt(
        self,
        po_number: str,
        material_number: str,
        quantity_received: Decimal,
        storage_location: str,
        received_by: str,
        quality_passed: bool = True,
        quality_notes: Optional[str] = None
    ) -> tuple[bool, Optional[str], Optional["WorkflowGoodsReceipt"]]:
        """
        Create goods receipt for delivered materials.
        Requirements: 4.1, 4.2
        
        Returns:
            Tuple of (success, error_message, goods_receipt)
        """
        from backend.models.pm_workflow_models import WorkflowGoodsReceipt
        
        # Verify PO exists
        po = await self.get_purchase_order(po_number)
        if not po:
            return False, f"Purchase order not found: {po_number}", None
        
        # Verify PO type is material or combined
        if po.po_type not in [POType.MATERIAL, POType.COMBINED]:
            return False, f"Cannot post goods receipt for service-only PO: {po_number}", None
        
        # Generate GR document number
        gr_document = self._generate_gr_document()
        
        # Create goods receipt
        gr = WorkflowGoodsReceipt(
            gr_document=gr_document,
            po_number=po_number,
            order_number=po.order_number,
            material_number=material_number,
            quantity_received=quantity_received,
            receipt_date=datetime.utcnow(),
            storage_location=storage_location,
            received_by=received_by
        )
        
        self.db.add(gr)
        await self.db.flush()
        
        # Update PO status based on delivery
        # For simplicity, mark as delivered (in real system would check quantities)
        if po.status == POStatus.CREATED or po.status == POStatus.ORDERED:
            po.status = POStatus.DELIVERED
        
        # Create document flow entry
        await self._create_document_flow_entry(
            order_number=po.order_number,
            document_type=DocumentType.GR,
            document_number=gr_document,
            user_id=received_by,
            status="posted" if quality_passed else "quality_hold",
            related_document=po_number
        )
        
        # Update order cost summary with actual material cost
        # In real system, would get actual cost from PO price
        await self._update_actual_material_cost(po.order_number, quantity_received * Decimal("10.00"))
        
        return True, None, gr
    
    async def create_service_entry(
        self,
        po_number: str,
        service_description: str,
        hours_or_units: Decimal,
        acceptance_date: datetime,
        acceptor: str,
        service_quality: str = "acceptable"
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Create service entry for external work performed.
        Requirements: 4.3, 4.4
        
        Returns:
            Tuple of (success, error_message, service_entry_document)
        """
        # Verify PO exists
        po = await self.get_purchase_order(po_number)
        if not po:
            return False, f"Purchase order not found: {po_number}", None
        
        # Verify PO type is service or combined
        if po.po_type not in [POType.SERVICE, POType.COMBINED]:
            return False, f"Cannot post service entry for material-only PO: {po_number}", None
        
        # Generate service entry document number
        service_entry_doc = self._generate_service_entry_document()
        
        # Update PO status
        if po.status == POStatus.CREATED or po.status == POStatus.ORDERED:
            po.status = POStatus.DELIVERED
        
        # Create document flow entry
        await self._create_document_flow_entry(
            order_number=po.order_number,
            document_type=DocumentType.SERVICE_ENTRY,
            document_number=service_entry_doc,
            user_id=acceptor,
            status=f"accepted - {service_quality}",
            related_document=po_number
        )
        
        # Update order cost summary with actual external cost
        # In real system, would get actual cost from PO price
        service_cost = hours_or_units * Decimal("75.00")  # Assume $75/hour
        await self._update_actual_external_cost(po.order_number, service_cost)
        
        return True, None, service_entry_doc
    
    async def get_goods_receipts_for_order(
        self,
        order_number: str
    ) -> List["WorkflowGoodsReceipt"]:
        """Get all goods receipts for an order - Requirement 4.2"""
        from backend.models.pm_workflow_models import WorkflowGoodsReceipt
        
        result = await self.db.execute(
            select(WorkflowGoodsReceipt)
            .where(WorkflowGoodsReceipt.order_number == order_number)
            .order_by(WorkflowGoodsReceipt.receipt_date)
        )
        return list(result.scalars().all())
    
    async def get_service_entries_for_order(
        self,
        order_number: str
    ) -> List[WorkflowDocumentFlow]:
        """Get all service entries for an order - Requirement 4.3"""
        result = await self.db.execute(
            select(WorkflowDocumentFlow)
            .where(
                WorkflowDocumentFlow.order_number == order_number,
                WorkflowDocumentFlow.document_type == DocumentType.SERVICE_ENTRY
            )
            .order_by(WorkflowDocumentFlow.transaction_date)
        )
        return list(result.scalars().all())
    
    async def _update_actual_material_cost(
        self,
        order_number: str,
        additional_cost: Decimal
    ) -> None:
        """Update actual material cost in cost summary"""
        result = await self.db.execute(
            select(WorkflowCostSummary)
            .where(WorkflowCostSummary.order_number == order_number)
        )
        cost_summary = result.scalar_one_or_none()
        
        if cost_summary:
            cost_summary.actual_material_cost += additional_cost
            cost_summary.actual_total_cost = (
                cost_summary.actual_material_cost +
                cost_summary.actual_labor_cost +
                cost_summary.actual_external_cost
            )
            cost_summary.material_variance = (
                cost_summary.actual_material_cost - cost_summary.estimated_material_cost
            )
            cost_summary.total_variance = (
                cost_summary.actual_total_cost - cost_summary.estimated_total_cost
            )
            if cost_summary.estimated_total_cost > 0:
                cost_summary.variance_percentage = (
                    cost_summary.total_variance / cost_summary.estimated_total_cost * 100
                )
            await self.db.flush()
    
    async def _update_actual_external_cost(
        self,
        order_number: str,
        additional_cost: Decimal
    ) -> None:
        """Update actual external cost in cost summary"""
        result = await self.db.execute(
            select(WorkflowCostSummary)
            .where(WorkflowCostSummary.order_number == order_number)
        )
        cost_summary = result.scalar_one_or_none()
        
        if cost_summary:
            cost_summary.actual_external_cost += additional_cost
            cost_summary.actual_total_cost = (
                cost_summary.actual_material_cost +
                cost_summary.actual_labor_cost +
                cost_summary.actual_external_cost
            )
            cost_summary.external_variance = (
                cost_summary.actual_external_cost - cost_summary.estimated_external_cost
            )
            cost_summary.total_variance = (
                cost_summary.actual_total_cost - cost_summary.estimated_total_cost
            )
            if cost_summary.estimated_total_cost > 0:
                cost_summary.variance_percentage = (
                    cost_summary.total_variance / cost_summary.estimated_total_cost * 100
                )
            await self.db.flush()
    
    def _generate_gr_document(self) -> str:
        """Generate unique GR document number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"GR-{timestamp}-{random_suffix}"
    
    def _generate_service_entry_document(self) -> str:
        """Generate unique service entry document number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"SE-{timestamp}-{random_suffix}"
    
    # Screen 3: Order Release & Execution Readiness
    
    async def release_order(
        self,
        order_number: str,
        released_by: str,
        override_blocks: bool = False,
        override_reason: Optional[str] = None
    ) -> tuple[bool, Optional[str], Optional[WorkflowMaintenanceOrder]]:
        """
        Release order for execution.
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        
        Returns:
            Tuple of (success, error_message, order)
        """
        # Get order with all relationships
        order = await self.get_order(order_number)
        
        if not order:
            return False, f"Order not found: {order_number}", None
        
        # Check current status
        if order.status != WorkflowOrderStatus.PLANNED:
            return False, f"Order must be in Planned status to release. Current status: {order.status.value}", None
        
        # Build order data for state machine validation
        order_data = await self._build_order_data_for_validation(order)
        
        # Check if transition is allowed
        can_transition, blocking_reasons = self.state_machine.can_transition(
            WorkflowOrderStatus.PLANNED,
            WorkflowOrderStatus.RELEASED,
            order_data
        )
        
        # If blocked and no override, return error
        if not can_transition and not override_blocks:
            return False, "; ".join(blocking_reasons), None
        
        # If override, check that only overridable blocks exist
        if override_blocks:
            # Technician requirement cannot be overridden
            has_technician = any(op.technician_id for op in order.operations)
            if not has_technician:
                return False, "Technician assignment is required and cannot be overridden", None
            
            # Log override
            if blocking_reasons:
                await self._create_document_flow_entry(
                    order_number=order_number,
                    document_type=DocumentType.ORDER,
                    document_number=order_number,
                    user_id=released_by,
                    status=f"Override: {override_reason or 'No reason provided'}",
                    related_document=None
                )
        
        # Update order status
        order.status = WorkflowOrderStatus.RELEASED
        order.released_by = released_by
        order.released_at = datetime.utcnow()
        
        # Create document flow entry
        await self._create_document_flow_entry(
            order_number=order_number,
            document_type=DocumentType.ORDER,
            document_number=order_number,
            user_id=released_by,
            status=WorkflowOrderStatus.RELEASED.value,
            related_document=None
        )
        
        await self.db.flush()
        
        return True, None, order
    
    async def get_readiness_checklist(
        self,
        order_number: str
    ) -> dict:
        """
        Get readiness checklist for order release.
        Requirement 3.4
        """
        order = await self.get_order(order_number)
        
        if not order:
            return {"error": "Order not found"}
        
        # Build order data
        order_data = await self._build_order_data_for_validation(order)
        
        # Check each prerequisite
        is_breakdown = order.order_type == WorkflowOrderType.BREAKDOWN
        
        # Permits check
        permits_status = "not_required"
        permits_detail = []
        if not is_breakdown:
            permits = order_data.get("permits", [])
            required_permits = [p for p in permits if p.get("required", False)]
            if required_permits:
                all_approved = all(p.get("approved", False) for p in required_permits)
                permits_status = "approved" if all_approved else "pending"
                permits_detail = [
                    {
                        "permit_id": p.get("permit_id"),
                        "permit_type": p.get("permit_type"),
                        "approved": p.get("approved", False),
                        "approver": p.get("approver")
                    }
                    for p in required_permits
                ]
        
        # Materials check
        materials_status = "not_required"
        materials_detail = []
        if not is_breakdown:
            components = order.components
            critical_components = [c for c in components if order_data.get("components", [])]
            # Find critical components from order_data
            critical_comp_data = [
                c for c in order_data.get("components", [])
                if c.get("critical", False)
            ]
            if critical_comp_data:
                all_available = all(
                    c.get("available", False) or c.get("on_order", False)
                    for c in critical_comp_data
                )
                materials_status = "available" if all_available else "unavailable"
                materials_detail = [
                    {
                        "component_id": c.get("component_id"),
                        "material_number": c.get("material_number"),
                        "available": c.get("available", False),
                        "on_order": c.get("on_order", False)
                    }
                    for c in critical_comp_data
                ]
        
        # Technician check
        has_technician = any(op.technician_id for op in order.operations)
        technician_status = "assigned" if has_technician else "not_assigned"
        technician_detail = [
            {
                "operation_id": op.operation_id,
                "operation_number": op.operation_number,
                "technician_id": op.technician_id
            }
            for op in order.operations
        ]
        
        # Overall readiness
        can_release, blocking_reasons = self.state_machine.can_transition(
            WorkflowOrderStatus.PLANNED,
            WorkflowOrderStatus.RELEASED,
            order_data
        )
        
        return {
            "order_number": order_number,
            "order_type": order.order_type.value,
            "current_status": order.status.value,
            "can_release": can_release,
            "blocking_reasons": blocking_reasons,
            "checklist": {
                "permits": {
                    "status": permits_status,
                    "detail": permits_detail
                },
                "materials": {
                    "status": materials_status,
                    "detail": materials_detail
                },
                "technician": {
                    "status": technician_status,
                    "detail": technician_detail
                }
            }
        }
    
    async def assign_technician(
        self,
        operation_id: str,
        technician_id: str,
        assigned_by: str
    ) -> Optional[WorkflowOperation]:
        """
        Assign technician to operation.
        Requirement 3.3
        """
        result = await self.db.execute(
            select(WorkflowOperation)
            .where(WorkflowOperation.operation_id == operation_id)
        )
        operation = result.scalar_one_or_none()
        
        if not operation:
            return None
        
        operation.technician_id = technician_id
        await self.db.flush()
        
        return operation
    
    async def _build_order_data_for_validation(
        self,
        order: WorkflowMaintenanceOrder
    ) -> dict:
        """Build order data dictionary for state machine validation"""
        # Build operations data
        operations = [
            {
                "operation_id": op.operation_id,
                "status": op.status.value,
                "technician_id": op.technician_id
            }
            for op in order.operations
        ]
        
        # Build components data
        components = [
            {
                "component_id": comp.component_id,
                "material_number": comp.material_number,
                "quantity_required": float(comp.quantity_required),
                "quantity_issued": float(comp.quantity_issued),
                "critical": False,  # Default - would come from material master data
                "available": True,  # Default - would come from inventory check
                "on_order": False   # Default - would come from PO status
            }
            for comp in order.components
        ]
        
        # Build permits data (placeholder - would come from permit system)
        permits = []
        
        # Build confirmations data
        confirmations = [
            {"confirmation_id": conf.confirmation_id}
            for conf in order.confirmations
        ]
        
        # Build cost summary data
        cost_summary = {}
        if order.cost_summary:
            cost_summary = {
                "estimated_total_cost": float(order.cost_summary.estimated_total_cost)
            }
        
        return {
            "order_type": order.order_type.value,
            "operations": operations,
            "components": components,
            "permits": permits,
            "confirmations": confirmations,
            "cost_summary": cost_summary
        }


    # Screen 6: Completion & Cost Settlement
    
    async def teco_order(
        self,
        order_number: str,
        completed_by: str
    ) -> tuple[bool, Optional[str], Optional[WorkflowMaintenanceOrder]]:
        """
        Technically complete order (TECO).
        Requirements: 6.1, 6.2, 6.3
        
        Returns:
            Tuple of (success, error_message, order)
        """
        # Get order with all relationships
        order = await self.get_order(order_number)
        
        if not order:
            return False, f"Order not found: {order_number}", None
        
        # Check current status
        if order.status != WorkflowOrderStatus.CONFIRMED:
            return False, f"Order must be in Confirmed status to TECO. Current status: {order.status.value}", None
        
        # Build order data for state machine validation
        order_data = await self._build_order_data_for_validation(order)
        
        # Check if transition is allowed
        can_transition, blocking_reasons = self.state_machine.can_transition(
            WorkflowOrderStatus.CONFIRMED,
            WorkflowOrderStatus.TECO,
            order_data
        )
        
        if not can_transition:
            return False, "; ".join(blocking_reasons), None
        
        # Update order status
        order.status = WorkflowOrderStatus.TECO
        order.completed_by = completed_by
        order.completed_at = datetime.utcnow()
        order.actual_end_date = datetime.utcnow()
        
        # Create document flow entry
        await self._create_document_flow_entry(
            order_number=order_number,
            document_type=DocumentType.TECO,
            document_number=order_number,
            user_id=completed_by,
            status=WorkflowOrderStatus.TECO.value,
            related_document=None
        )
        
        await self.db.flush()
        
        return True, None, order
    
    async def get_completion_checklist(
        self,
        order_number: str
    ) -> dict:
        """
        Get completion checklist for TECO validation.
        Requirements: 6.1, 6.2, 6.3
        """
        order = await self.get_order(order_number)
        
        if not order:
            return {"error": "Order not found"}
        
        # Build order data
        order_data = await self._build_order_data_for_validation(order)
        
        # Check each prerequisite
        
        # Operations confirmation check
        all_operations_confirmed = all(
            op.status == OperationStatus.CONFIRMED
            for op in order.operations
        )
        operations_status = "confirmed" if all_operations_confirmed else "pending"
        operations_detail = [
            {
                "operation_id": op.operation_id,
                "operation_number": op.operation_number,
                "status": op.status.value,
                "confirmed": op.status == OperationStatus.CONFIRMED
            }
            for op in order.operations
        ]
        
        # Goods movements check
        all_components_issued = all(
            comp.quantity_issued >= comp.quantity_required
            for comp in order.components
        )
        goods_movements_status = "complete" if all_components_issued else "incomplete"
        goods_movements_detail = [
            {
                "component_id": comp.component_id,
                "material_number": comp.material_number,
                "quantity_required": float(comp.quantity_required),
                "quantity_issued": float(comp.quantity_issued),
                "complete": comp.quantity_issued >= comp.quantity_required
            }
            for comp in order.components
        ]
        
        # Cost capture check
        cost_summary = order.cost_summary
        costs_captured = cost_summary is not None and cost_summary.actual_total_cost > 0
        costs_status = "captured" if costs_captured else "not_captured"
        costs_detail = {}
        if cost_summary:
            costs_detail = {
                "actual_material_cost": float(cost_summary.actual_material_cost),
                "actual_labor_cost": float(cost_summary.actual_labor_cost),
                "actual_external_cost": float(cost_summary.actual_external_cost),
                "actual_total_cost": float(cost_summary.actual_total_cost)
            }
        
        # Overall readiness
        can_teco, blocking_reasons = self.state_machine.can_transition(
            WorkflowOrderStatus.CONFIRMED,
            WorkflowOrderStatus.TECO,
            order_data
        )
        
        return {
            "order_number": order_number,
            "order_type": order.order_type.value,
            "current_status": order.status.value,
            "can_teco": can_teco,
            "blocking_reasons": blocking_reasons,
            "checklist": {
                "operations": {
                    "status": operations_status,
                    "detail": operations_detail
                },
                "goods_movements": {
                    "status": goods_movements_status,
                    "detail": goods_movements_detail
                },
                "costs": {
                    "status": costs_status,
                    "detail": costs_detail
                }
            }
        }
    
    async def get_cost_analysis(
        self,
        order_number: str
    ) -> dict:
        """
        Get cost analysis with variance details.
        Requirements: 6.4, 6.5, 6.6
        """
        order = await self.get_order(order_number)
        
        if not order:
            return {"error": "Order not found"}
        
        cost_summary = order.cost_summary
        
        if not cost_summary:
            return {
                "error": "Cost summary not available",
                "order_number": order_number
            }
        
        # Calculate variance percentages by element
        material_variance_pct = Decimal(0)
        if cost_summary.estimated_material_cost > 0:
            material_variance_pct = (
                cost_summary.material_variance / cost_summary.estimated_material_cost * 100
            )
        
        labor_variance_pct = Decimal(0)
        if cost_summary.estimated_labor_cost > 0:
            labor_variance_pct = (
                cost_summary.labor_variance / cost_summary.estimated_labor_cost * 100
            )
        
        external_variance_pct = Decimal(0)
        if cost_summary.estimated_external_cost > 0:
            external_variance_pct = (
                cost_summary.external_variance / cost_summary.estimated_external_cost * 100
            )
        
        return {
            "order_number": order_number,
            "estimated_costs": {
                "material": float(cost_summary.estimated_material_cost),
                "labor": float(cost_summary.estimated_labor_cost),
                "external": float(cost_summary.estimated_external_cost),
                "total": float(cost_summary.estimated_total_cost)
            },
            "actual_costs": {
                "material": float(cost_summary.actual_material_cost),
                "labor": float(cost_summary.actual_labor_cost),
                "external": float(cost_summary.actual_external_cost),
                "total": float(cost_summary.actual_total_cost)
            },
            "variances": {
                "material": {
                    "amount": float(cost_summary.material_variance),
                    "percentage": float(material_variance_pct)
                },
                "labor": {
                    "amount": float(cost_summary.labor_variance),
                    "percentage": float(labor_variance_pct)
                },
                "external": {
                    "amount": float(cost_summary.external_variance),
                    "percentage": float(external_variance_pct)
                },
                "total": {
                    "amount": float(cost_summary.total_variance),
                    "percentage": float(cost_summary.variance_percentage)
                }
            }
        }
    
    async def settle_costs(
        self,
        order_number: str,
        cost_center: str,
        settled_by: str
    ) -> tuple[bool, Optional[str]]:
        """
        Settle costs to cost center.
        Requirement 6.7
        
        Returns:
            Tuple of (success, error_message)
        """
        order = await self.get_order(order_number)
        
        if not order:
            return False, f"Order not found: {order_number}"
        
        # Verify order is TECO
        if order.status != WorkflowOrderStatus.TECO:
            return False, f"Order must be in TECO status to settle costs. Current status: {order.status.value}"
        
        # In a real system, this would post to FI module
        # For now, just create a document flow entry
        await self._create_document_flow_entry(
            order_number=order_number,
            document_type=DocumentType.ORDER,
            document_number=f"SETTLEMENT-{order_number}",
            user_id=settled_by,
            status=f"costs_settled_to_{cost_center}",
            related_document=order_number
        )
        
        await self.db.flush()
        
        return True, None
    
    
    # Task 11: Breakdown Maintenance Differentiation
    
    async def create_breakdown_order_from_notification(
        self,
        notification_id: str,
        equipment_id: str,
        functional_location: str,
        notification_description: str,
        created_by: str
    ) -> WorkflowMaintenanceOrder:
        """
        Auto-create breakdown order from notification.
        Requirements: 7.1, 7.2
        
        Breakdown orders are automatically created with:
        - Highest priority (URGENT)
        - Pre-populated equipment and functional location
        - Reference to breakdown notification
        - Status set to CREATED
        """
        # Create breakdown order with highest priority
        order = await self.create_order(
            order_type=WorkflowOrderType.BREAKDOWN,
            equipment_id=equipment_id,
            functional_location=functional_location,
            priority=Priority.URGENT,
            planned_start_date=datetime.utcnow(),  # Immediate start
            planned_end_date=None,  # To be determined
            breakdown_notification_id=notification_id,
            created_by=created_by
        )
        
        # Auto-create a default operation based on notification
        await self.add_operation(
            order_number=order.order_number,
            operation_number="0010",
            work_center="EMERGENCY",
            description=f"Emergency repair: {notification_description}",
            planned_hours=Decimal("4.0")  # Default estimate
        )
        
        # Create document flow entry noting auto-creation
        await self._create_document_flow_entry(
            order_number=order.order_number,
            document_type=DocumentType.ORDER,
            document_number=order.order_number,
            user_id=created_by,
            status=f"auto_created_from_notification_{notification_id}",
            related_document=notification_id
        )
        
        await self.db.flush()
        
        return order
    
    async def release_breakdown_order(
        self,
        order_number: str,
        released_by: str,
        emergency_permit_id: Optional[str] = None
    ) -> tuple[bool, Optional[str], Optional[WorkflowMaintenanceOrder]]:
        """
        Release breakdown order with reduced validation.
        Requirements: 7.3, 7.4
        
        Breakdown orders have reduced validation:
        - Emergency permits accepted instead of full permits
        - Material availability not strictly enforced
        - Can proceed with emergency stock
        """
        # Get order
        order = await self.get_order(order_number)
        
        if not order:
            return False, f"Order not found: {order_number}", None
        
        # Verify it's a breakdown order
        if order.order_type != WorkflowOrderType.BREAKDOWN:
            return False, "This method is only for breakdown orders", None
        
        # Check current status
        if order.status != WorkflowOrderStatus.PLANNED:
            return False, f"Order must be in Planned status to release. Current status: {order.status.value}", None
        
        # For breakdown orders, only check technician assignment
        has_technician = any(op.technician_id for op in order.operations)
        if not has_technician:
            return False, "At least one operation must have a technician assigned", None
        
        # Update order status
        order.status = WorkflowOrderStatus.RELEASED
        order.released_by = released_by
        order.released_at = datetime.utcnow()
        
        # Create document flow entry noting reduced validation
        status_msg = "released_breakdown_reduced_validation"
        if emergency_permit_id:
            status_msg += f"_emergency_permit_{emergency_permit_id}"
        
        await self._create_document_flow_entry(
            order_number=order_number,
            document_type=DocumentType.ORDER,
            document_number=order_number,
            user_id=released_by,
            status=status_msg,
            related_document=emergency_permit_id
        )
        
        await self.db.flush()
        
        return True, None, order
    
    async def create_emergency_goods_issue(
        self,
        order_number: str,
        material_number: str,
        quantity_issued: Decimal,
        cost_center: str,
        issued_by: str,
        emergency_stock_location: str = "EMERGENCY"
    ) -> tuple[bool, Optional[str], Optional["WorkflowGoodsIssue"]]:
        """
        Create goods issue from emergency stock without PO.
        Requirements: 7.4
        
        For breakdown orders, materials can be issued from emergency stock
        without going through the full procurement cycle.
        """
        from backend.models.pm_workflow_models import WorkflowGoodsIssue
        
        # Get order
        order = await self.get_order(order_number)
        
        if not order:
            return False, f"Order not found: {order_number}", None
        
        # Verify it's a breakdown order
        if order.order_type != WorkflowOrderType.BREAKDOWN:
            return False, "Emergency stock GI is only allowed for breakdown orders", None
        
        # Find or create component for this material
        component = None
        for comp in order.components:
            if comp.material_number == material_number:
                component = comp
                break
        
        if not component:
            # Auto-create component for emergency material
            component = await self.add_component(
                order_number=order_number,
                material_number=material_number,
                description=f"Emergency stock: {material_number}",
                quantity_required=quantity_issued,
                unit_of_measure="EA",
                estimated_cost=Decimal("0.00"),  # Will be updated with actual cost
                has_master_data=False
            )
        
        # Generate GI document number
        gi_document = self._generate_gi_document()
        
        # Create goods issue
        gi = WorkflowGoodsIssue(
            gi_document=gi_document,
            order_number=order_number,
            component_id=component.component_id,
            material_number=material_number,
            quantity_issued=quantity_issued,
            issue_date=datetime.utcnow(),
            cost_center=cost_center,
            issued_by=issued_by
        )
        
        self.db.add(gi)
        
        # Update component quantity issued
        component.quantity_issued += quantity_issued
        
        # Create document flow entry noting emergency stock
        await self._create_document_flow_entry(
            order_number=order_number,
            document_type=DocumentType.GI,
            document_number=gi_document,
            user_id=issued_by,
            status=f"emergency_stock_{emergency_stock_location}",
            related_document=order_number
        )
        
        # Update actual material cost (estimate for emergency stock)
        emergency_cost = quantity_issued * Decimal("15.00")  # Estimated cost per unit
        await self._update_actual_material_cost(order_number, emergency_cost)
        
        await self.db.flush()
        
        return True, None, gi
    
    async def validate_malfunction_report_required(
        self,
        order_number: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if malfunction report is required for breakdown order.
        Requirement 7.5
        
        Returns:
            Tuple of (required, reason)
        """
        order = await self.get_order(order_number)
        
        if not order:
            return False, "Order not found"
        
        # Malfunction report is mandatory for breakdown orders
        if order.order_type == WorkflowOrderType.BREAKDOWN:
            # Check if malfunction report exists
            if len(order.malfunction_reports) == 0:
                return True, "Malfunction report is mandatory for breakdown orders"
        
        return False, None
    
    async def create_malfunction_report(
        self,
        order_number: str,
        cause_code: str,
        description: str,
        root_cause: Optional[str],
        corrective_action: Optional[str],
        reported_by: str
    ) -> tuple[bool, Optional[str], Optional["WorkflowMalfunctionReport"]]:
        """
        Create malfunction report.
        Requirements: 5.5, 7.5
        
        For breakdown orders, this is mandatory before TECO.
        """
        from backend.models.pm_workflow_models import WorkflowMalfunctionReport
        
        # Get order
        order = await self.get_order(order_number)
        
        if not order:
            return False, f"Order not found: {order_number}", None
        
        # Generate report ID
        report_id = f"MAL-{uuid.uuid4().hex[:12].upper()}"
        
        # Create malfunction report
        report = WorkflowMalfunctionReport(
            report_id=report_id,
            order_number=order_number,
            cause_code=cause_code,
            description=description,
            root_cause=root_cause,
            corrective_action=corrective_action,
            reported_by=reported_by,
            reported_at=datetime.utcnow()
        )
        
        self.db.add(report)
        
        # Create document flow entry
        await self._create_document_flow_entry(
            order_number=order_number,
            document_type=DocumentType.ORDER,
            document_number=report_id,
            user_id=reported_by,
            status=f"malfunction_reported_{cause_code}",
            related_document=order_number
        )
        
        await self.db.flush()
        
        return True, None, report
    
    async def teco_breakdown_order(
        self,
        order_number: str,
        completed_by: str,
        post_review_required: bool = True
    ) -> tuple[bool, Optional[str], Optional[WorkflowMaintenanceOrder]]:
        """
        Technically complete breakdown order with mandatory post-review.
        Requirements: 7.6
        
        Breakdown orders require:
        - Mandatory malfunction report
        - Post-completion review flag
        - Root cause analysis
        """
        # Get order
        order = await self.get_order(order_number)
        
        if not order:
            return False, f"Order not found: {order_number}", None
        
        # Verify it's a breakdown order
        if order.order_type != WorkflowOrderType.BREAKDOWN:
            return False, "This method is only for breakdown orders", None
        
        # Check for mandatory malfunction report
        if len(order.malfunction_reports) == 0:
            return False, "Malfunction report is mandatory for breakdown orders before TECO", None
        
        # Use standard TECO logic
        success, error_msg, order = await self.teco_order(order_number, completed_by)
        
        if not success:
            return False, error_msg, None
        
        # Create document flow entry for post-completion review
        if post_review_required:
            await self._create_document_flow_entry(
                order_number=order_number,
                document_type=DocumentType.ORDER,
                document_number=f"REVIEW-{order_number}",
                user_id=completed_by,
                status="post_completion_review_required",
                related_document=order_number
            )
        
        await self.db.flush()
        
        return True, None, order
    
    async def get_breakdown_order_summary(
        self,
        order_number: str
    ) -> dict:
        """
        Get summary of breakdown order for post-completion review.
        Requirement 7.6
        """
        order = await self.get_order(order_number)
        
        if not order:
            return {"error": "Order not found"}
        
        if order.order_type != WorkflowOrderType.BREAKDOWN:
            return {"error": "Not a breakdown order"}
        
        # Get malfunction reports
        malfunction_reports = [
            {
                "report_id": report.report_id,
                "cause_code": report.cause_code,
                "description": report.description,
                "root_cause": report.root_cause,
                "corrective_action": report.corrective_action,
                "reported_by": report.reported_by,
                "reported_at": report.reported_at.isoformat()
            }
            for report in order.malfunction_reports
        ]
        
        # Get cost analysis
        cost_analysis = await self.get_cost_analysis(order_number)
        
        # Get document flow
        document_flow = await self.get_document_flow(order_number)
        
        # Calculate response time
        response_time_hours = None
        if order.created_at and order.released_at:
            response_time = order.released_at - order.created_at
            response_time_hours = response_time.total_seconds() / 3600
        
        # Calculate completion time
        completion_time_hours = None
        if order.released_at and order.completed_at:
            completion_time = order.completed_at - order.released_at
            completion_time_hours = completion_time.total_seconds() / 3600
        
        return {
            "order_number": order_number,
            "order_type": order.order_type.value,
            "status": order.status.value,
            "priority": order.priority.value,
            "breakdown_notification_id": order.breakdown_notification_id,
            "equipment_id": order.equipment_id,
            "functional_location": order.functional_location,
            "created_at": order.created_at.isoformat(),
            "released_at": order.released_at.isoformat() if order.released_at else None,
            "completed_at": order.completed_at.isoformat() if order.completed_at else None,
            "response_time_hours": response_time_hours,
            "completion_time_hours": completion_time_hours,
            "malfunction_reports": malfunction_reports,
            "cost_analysis": cost_analysis,
            "document_flow_count": len(document_flow),
            "post_review_required": True
        }
    
    def _generate_gi_document(self) -> str:
        """Generate unique GI document number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"GI-{timestamp}-{random_suffix}"
    
    
# Document Flow Tracking (Task 9)
    
    async def get_document_flow(self, order_number: str) -> List[WorkflowDocumentFlow]:
        """
        Get complete document flow for an order.
        Requirements: 9.1, 9.2, 9.4, 9.5
        
        Returns all document flow entries in chronological order.
        """
        result = await self.db.execute(
            select(WorkflowDocumentFlow)
            .where(WorkflowDocumentFlow.order_number == order_number)
            .order_by(WorkflowDocumentFlow.transaction_date)
        )
        return list(result.scalars().all())
    
    async def get_document_flow_by_type(
        self,
        order_number: str,
        document_type: DocumentType
    ) -> List[WorkflowDocumentFlow]:
        """
        Get document flow entries filtered by document type.
        Requirement 9.4
        """
        result = await self.db.execute(
            select(WorkflowDocumentFlow)
            .where(
                WorkflowDocumentFlow.order_number == order_number,
                WorkflowDocumentFlow.document_type == document_type
            )
            .order_by(WorkflowDocumentFlow.transaction_date)
        )
        return list(result.scalars().all())
