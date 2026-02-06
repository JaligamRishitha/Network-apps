"""
Work Order Flow Service - Orchestrates the PM → MM → FI workflow.

Flow:
1. PM receives work order from CRM (via API)
2. Work order contains materials required
3. PM sends material requirements to MM
4. MM checks if materials are available
   - If materials ARE available → work order proceeds
   - If materials are NOT available → MM raises a ticket to FI for purchasing
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.work_order_flow_models import (
    CRMWorkOrder, WorkOrderMaterial, WorkOrderFlowHistory, WorkOrderFlowStatus
)
from backend.models.mm_models import Material
from backend.models.ticket_models import Module, TicketType, Priority
from backend.services.ticket_service import TicketService
from backend.services.event_service import EventService, EventType
from backend.services.mm_service import MMService
from backend.services.fi_service import FIService


class WorkOrderFlowError(Exception):
    """Base exception for Work Order Flow errors"""
    pass


class WorkOrderNotFoundError(WorkOrderFlowError):
    """Raised when a work order is not found"""
    pass


class InvalidWorkOrderStateError(WorkOrderFlowError):
    """Raised when work order is in invalid state for the operation"""
    pass


class MaterialCheckResult:
    """Result of material availability check"""

    def __init__(
        self,
        material_id: str,
        material_description: str,
        quantity_required: int,
        quantity_available: int,
        is_available: bool,
        shortage_quantity: int = 0,
        unit_price: Optional[Decimal] = None,
    ):
        self.material_id = material_id
        self.material_description = material_description
        self.quantity_required = quantity_required
        self.quantity_available = quantity_available
        self.is_available = is_available
        self.shortage_quantity = shortage_quantity
        self.unit_price = unit_price

    def to_dict(self) -> dict:
        return {
            "material_id": self.material_id,
            "material_description": self.material_description,
            "quantity_required": self.quantity_required,
            "quantity_available": self.quantity_available,
            "is_available": self.is_available,
            "shortage_quantity": self.shortage_quantity,
            "unit_price": float(self.unit_price) if self.unit_price else None,
        }


class WorkOrderFlowService:
    """
    Service class for Work Order Flow orchestration.
    Manages the flow: PM → MM → FI
    """

    def __init__(
        self,
        session: AsyncSession,
        ticket_service: Optional[TicketService] = None,
        event_service: Optional[EventService] = None,
        mm_service: Optional[MMService] = None,
        fi_service: Optional[FIService] = None,
    ):
        self.session = session
        self.ticket_service = ticket_service or TicketService(session)
        self.event_service = event_service or EventService()
        self.mm_service = mm_service or MMService(session, self.ticket_service, self.event_service)
        self.fi_service = fi_service or FIService(session, self.ticket_service, self.event_service)

    # =====================
    # Work Order CRUD
    # =====================

    async def create_work_order_from_crm(
        self,
        title: str,
        description: str,
        customer_name: str,
        site_location: str,
        requested_date: datetime,
        cost_center_id: str,
        created_by: str,
        materials: List[dict],  # List of {material_id, material_description, quantity_required, unit_of_measure}
        crm_reference_id: Optional[str] = None,
        customer_contact: Optional[str] = None,
        priority: str = "medium",
        assigned_to: Optional[str] = None,
    ) -> CRMWorkOrder:
        """
        Create a new work order received from CRM.
        This is the entry point for the PM → MM → FI workflow.
        """
        work_order_id = f"WO-{uuid.uuid4().hex[:8].upper()}"

        work_order = CRMWorkOrder(
            work_order_id=work_order_id,
            crm_reference_id=crm_reference_id,
            title=title,
            description=description,
            customer_name=customer_name,
            customer_contact=customer_contact,
            site_location=site_location,
            priority=priority,
            flow_status=WorkOrderFlowStatus.RECEIVED,
            requested_date=requested_date,
            cost_center_id=cost_center_id,
            created_by=created_by,
            assigned_to=assigned_to,
        )

        self.session.add(work_order)
        await self.session.flush()

        # Add materials
        for mat in materials:
            material = WorkOrderMaterial(
                work_order_id=work_order_id,
                material_id=mat["material_id"],
                material_description=mat.get("material_description", ""),
                quantity_required=mat["quantity_required"],
                unit_of_measure=mat.get("unit_of_measure", "EA"),
                unit_price=Decimal(str(mat.get("unit_price", 0))) if mat.get("unit_price") else None,
            )
            self.session.add(material)

        # Add flow history
        await self._add_flow_history(
            work_order_id=work_order_id,
            from_status=WorkOrderFlowStatus.RECEIVED,
            to_status=WorkOrderFlowStatus.RECEIVED,
            triggered_by_module="CRM",
            performed_by=created_by,
            notes="Work order received from CRM",
        )

        # Emit event
        self.event_service.create_event(event_type=EventType.PM_TICKET_CREATED,
        payload={
            "work_order_id": work_order_id,
            "crm_reference_id": crm_reference_id,
            "title": title,
            "materials_count": len(materials),
        },)

        await self.session.flush()
        return work_order

    async def get_work_order(self, work_order_id: str) -> Optional[CRMWorkOrder]:
        """Get a work order by ID with materials loaded."""
        result = await self.session.execute(
            select(CRMWorkOrder)
            .options(selectinload(CRMWorkOrder.materials))
            .options(selectinload(CRMWorkOrder.flow_history))
            .where(CRMWorkOrder.work_order_id == work_order_id)
        )
        return result.scalar_one_or_none()

    async def get_work_order_or_raise(self, work_order_id: str) -> CRMWorkOrder:
        """Get a work order by ID or raise WorkOrderNotFoundError."""
        work_order = await self.get_work_order(work_order_id)
        if not work_order:
            raise WorkOrderNotFoundError(f"Work order not found: {work_order_id}")
        return work_order

    async def list_work_orders(
        self,
        flow_status: Optional[WorkOrderFlowStatus] = None,
        customer_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[CRMWorkOrder], int]:
        """List work orders with optional filtering."""
        query = select(CRMWorkOrder).options(selectinload(CRMWorkOrder.materials))
        count_query = select(func.count(CRMWorkOrder.work_order_id))

        if flow_status:
            query = query.where(CRMWorkOrder.flow_status == flow_status)
            count_query = count_query.where(CRMWorkOrder.flow_status == flow_status)
        if customer_name:
            query = query.where(CRMWorkOrder.customer_name.ilike(f"%{customer_name}%"))
            count_query = count_query.where(CRMWorkOrder.customer_name.ilike(f"%{customer_name}%"))

        query = query.order_by(CRMWorkOrder.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(query)
        work_orders = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return work_orders, total

    # =====================
    # PM → MM: Material Check
    # =====================

    async def send_to_mm_for_material_check(
        self,
        work_order_id: str,
        performed_by: str,
    ) -> Tuple[CRMWorkOrder, List[MaterialCheckResult]]:
        """
        PM sends work order materials to MM for availability check.
        This is Step 2 of the workflow.
        """
        work_order = await self.get_work_order_or_raise(work_order_id)

        if work_order.flow_status not in [WorkOrderFlowStatus.RECEIVED, WorkOrderFlowStatus.PENDING_MATERIAL_CHECK]:
            raise InvalidWorkOrderStateError(
                f"Work order {work_order_id} is in state {work_order.flow_status.value}, "
                f"cannot send to MM for material check"
            )

        # Update status to pending material check
        old_status = work_order.flow_status
        work_order.flow_status = WorkOrderFlowStatus.PENDING_MATERIAL_CHECK

        # Check each material in MM
        check_results = []
        all_available = True
        total_shortage_cost = Decimal("0")

        for wo_material in work_order.materials:
            result = await self._check_material_availability(wo_material)
            check_results.append(result)

            # Update work order material with check result
            wo_material.quantity_available = result.quantity_available
            wo_material.is_available = result.is_available
            wo_material.shortage_quantity = result.shortage_quantity
            wo_material.checked_at = datetime.utcnow()

            if not result.is_available:
                all_available = False
                if result.unit_price:
                    total_shortage_cost += result.unit_price * result.shortage_quantity

        # Update work order with check summary
        work_order.materials_check_summary = {
            "checked_at": datetime.utcnow().isoformat(),
            "all_available": all_available,
            "total_materials": len(check_results),
            "available_count": sum(1 for r in check_results if r.is_available),
            "shortage_count": sum(1 for r in check_results if not r.is_available),
            "total_shortage_cost": float(total_shortage_cost),
        }

        # Update status based on availability
        if all_available:
            work_order.flow_status = WorkOrderFlowStatus.MATERIALS_AVAILABLE
            notes = "All materials are available"
        else:
            work_order.flow_status = WorkOrderFlowStatus.MATERIALS_SHORTAGE
            notes = f"Material shortage detected. {sum(1 for r in check_results if not r.is_available)} materials not available"

        work_order.estimated_material_cost = total_shortage_cost if not all_available else Decimal("0")

        # Add flow history
        await self._add_flow_history(
            work_order_id=work_order_id,
            from_status=old_status,
            to_status=work_order.flow_status,
            triggered_by_module="MM",
            performed_by=performed_by,
            notes=notes,
        )

        # Emit event
        self.event_service.create_event(event_type=EventType.MM_STOCK_CHANGED,
        payload={
            "work_order_id": work_order_id,
            "all_materials_available": all_available,
            "check_results": [r.to_dict() for r in check_results],
        },)

        await self.session.flush()
        return work_order, check_results

    async def _check_material_availability(
        self,
        wo_material: WorkOrderMaterial,
    ) -> MaterialCheckResult:
        """Check a single material availability in MM."""
        # Get material from MM
        mm_material = await self.mm_service.get_material(wo_material.material_id)

        if mm_material:
            quantity_available = mm_material.quantity
            is_available = quantity_available >= wo_material.quantity_required
            shortage = max(0, wo_material.quantity_required - quantity_available)

            return MaterialCheckResult(
                material_id=wo_material.material_id,
                material_description=wo_material.material_description,
                quantity_required=wo_material.quantity_required,
                quantity_available=quantity_available,
                is_available=is_available,
                shortage_quantity=shortage,
                unit_price=wo_material.unit_price,
            )
        else:
            # Material not found in MM - treat as shortage
            return MaterialCheckResult(
                material_id=wo_material.material_id,
                material_description=wo_material.material_description,
                quantity_required=wo_material.quantity_required,
                quantity_available=0,
                is_available=False,
                shortage_quantity=wo_material.quantity_required,
                unit_price=wo_material.unit_price,
            )

    # =====================
    # MM → FI: Purchase Request
    # =====================

    async def raise_fi_ticket_for_purchase(
        self,
        work_order_id: str,
        performed_by: str,
        justification: Optional[str] = None,
    ) -> Tuple[CRMWorkOrder, str, str]:
        """
        MM raises a ticket to FI for purchasing materials that are not available.
        This is triggered when materials are not available.

        Returns: (work_order, fi_approval_id, fi_ticket_id)
        """
        work_order = await self.get_work_order_or_raise(work_order_id)

        if work_order.flow_status != WorkOrderFlowStatus.MATERIALS_SHORTAGE:
            raise InvalidWorkOrderStateError(
                f"Work order {work_order_id} is in state {work_order.flow_status.value}, "
                f"cannot raise FI ticket for purchase"
            )

        # Calculate total cost for shortage materials
        shortage_materials = [m for m in work_order.materials if not m.is_available]
        if not shortage_materials:
            raise WorkOrderFlowError("No shortage materials found")

        total_cost = Decimal("0")
        shortage_details = []
        for mat in shortage_materials:
            mat_cost = (mat.unit_price or Decimal("0")) * mat.shortage_quantity
            total_cost += mat_cost
            shortage_details.append({
                "material_id": mat.material_id,
                "description": mat.material_description,
                "shortage_quantity": mat.shortage_quantity,
                "unit_price": float(mat.unit_price) if mat.unit_price else 0,
                "total_cost": float(mat_cost),
            })

        # Create justification
        if not justification:
            justification = (
                f"Material purchase required for Work Order {work_order_id}\n"
                f"Customer: {work_order.customer_name}\n"
                f"Site: {work_order.site_location}\n\n"
                f"Shortage Materials:\n"
            )
            for det in shortage_details:
                justification += f"- {det['material_id']}: {det['shortage_quantity']} units (${det['total_cost']:.2f})\n"

        # Create FI approval request
        approval, ticket = await self.fi_service.create_approval_request(
            cost_center_id=work_order.cost_center_id,
            amount=total_cost,
            justification=justification,
            requested_by=performed_by,
            approval_hierarchy=[performed_by],
        )

        # Update work order
        old_status = work_order.flow_status
        work_order.flow_status = WorkOrderFlowStatus.PURCHASE_REQUESTED
        work_order.fi_approval_id = approval.approval_id
        work_order.fi_ticket_id = ticket.ticket_id
        work_order.estimated_material_cost = total_cost

        # Add flow history
        await self._add_flow_history(
            work_order_id=work_order_id,
            from_status=old_status,
            to_status=work_order.flow_status,
            triggered_by_module="FI",
            performed_by=performed_by,
            notes=f"FI approval request created: {approval.approval_id}. Amount: ${total_cost:.2f}",
        )

        # Emit event
        self.event_service.create_event(event_type=EventType.FI_APPROVAL_REQUESTED,
        payload={
            "work_order_id": work_order_id,
            "approval_id": approval.approval_id,
            "ticket_id": ticket.ticket_id,
            "amount": float(total_cost),
            "shortage_materials": shortage_details,
        },)

        await self.session.flush()
        return work_order, approval.approval_id, ticket.ticket_id

    # =====================
    # FI → Work Order: Approval Handling
    # =====================

    async def handle_fi_approval_decision(
        self,
        work_order_id: str,
        approved: bool,
        decided_by: str,
        comment: Optional[str] = None,
    ) -> CRMWorkOrder:
        """
        Handle FI approval decision for material purchase.
        Called when FI approves or rejects the purchase request.
        """
        work_order = await self.get_work_order_or_raise(work_order_id)

        if work_order.flow_status != WorkOrderFlowStatus.PURCHASE_REQUESTED:
            raise InvalidWorkOrderStateError(
                f"Work order {work_order_id} is in state {work_order.flow_status.value}, "
                f"cannot handle FI approval decision"
            )

        old_status = work_order.flow_status

        if approved:
            work_order.flow_status = WorkOrderFlowStatus.PURCHASE_APPROVED

            # Create purchase requisitions for shortage materials
            shortage_materials = [m for m in work_order.materials if not m.is_available]
            for mat in shortage_materials:
                requisition, ticket = await self.mm_service.create_purchase_requisition(
                    material_id=mat.material_id,
                    quantity=mat.shortage_quantity,
                    cost_center_id=work_order.cost_center_id,
                    justification=f"Purchase for Work Order {work_order_id}",
                    requested_by=decided_by,
                )
                mat.requisition_id = requisition.requisition_id

            notes = f"FI approved purchase. Comment: {comment}" if comment else "FI approved purchase"
        else:
            work_order.flow_status = WorkOrderFlowStatus.PURCHASE_REJECTED
            notes = f"FI rejected purchase. Comment: {comment}" if comment else "FI rejected purchase"

        # Add flow history
        await self._add_flow_history(
            work_order_id=work_order_id,
            from_status=old_status,
            to_status=work_order.flow_status,
            triggered_by_module="FI",
            performed_by=decided_by,
            notes=notes,
        )

        await self.session.flush()
        return work_order

    # =====================
    # Work Order Progression
    # =====================

    async def proceed_with_work_order(
        self,
        work_order_id: str,
        performed_by: str,
    ) -> CRMWorkOrder:
        """
        Proceed with work order after materials are confirmed available.
        This moves the work order to READY_TO_PROCEED status.
        """
        work_order = await self.get_work_order_or_raise(work_order_id)

        valid_states = [
            WorkOrderFlowStatus.MATERIALS_AVAILABLE,
            WorkOrderFlowStatus.PURCHASE_APPROVED,
        ]
        if work_order.flow_status not in valid_states:
            raise InvalidWorkOrderStateError(
                f"Work order {work_order_id} is in state {work_order.flow_status.value}, "
                f"cannot proceed. Valid states: {[s.value for s in valid_states]}"
            )

        old_status = work_order.flow_status
        work_order.flow_status = WorkOrderFlowStatus.READY_TO_PROCEED

        # Add flow history
        await self._add_flow_history(
            work_order_id=work_order_id,
            from_status=old_status,
            to_status=work_order.flow_status,
            triggered_by_module="PM",
            performed_by=performed_by,
            notes="Work order is ready to proceed",
        )

        await self.session.flush()
        return work_order

    async def start_work_order(
        self,
        work_order_id: str,
        performed_by: str,
        scheduled_date: Optional[datetime] = None,
    ) -> CRMWorkOrder:
        """Start working on the work order."""
        work_order = await self.get_work_order_or_raise(work_order_id)

        if work_order.flow_status != WorkOrderFlowStatus.READY_TO_PROCEED:
            raise InvalidWorkOrderStateError(
                f"Work order {work_order_id} is in state {work_order.flow_status.value}, "
                f"cannot start work order"
            )

        old_status = work_order.flow_status
        work_order.flow_status = WorkOrderFlowStatus.IN_PROGRESS
        work_order.scheduled_date = scheduled_date or datetime.utcnow()

        # Add flow history
        await self._add_flow_history(
            work_order_id=work_order_id,
            from_status=old_status,
            to_status=work_order.flow_status,
            triggered_by_module="PM",
            performed_by=performed_by,
            notes="Work order started",
        )

        await self.session.flush()
        return work_order

    async def complete_work_order(
        self,
        work_order_id: str,
        performed_by: str,
    ) -> CRMWorkOrder:
        """Complete the work order."""
        work_order = await self.get_work_order_or_raise(work_order_id)

        if work_order.flow_status != WorkOrderFlowStatus.IN_PROGRESS:
            raise InvalidWorkOrderStateError(
                f"Work order {work_order_id} is in state {work_order.flow_status.value}, "
                f"cannot complete work order"
            )

        old_status = work_order.flow_status
        work_order.flow_status = WorkOrderFlowStatus.COMPLETED
        work_order.completed_date = datetime.utcnow()

        # Add flow history
        await self._add_flow_history(
            work_order_id=work_order_id,
            from_status=old_status,
            to_status=work_order.flow_status,
            triggered_by_module="PM",
            performed_by=performed_by,
            notes="Work order completed",
        )

        await self.session.flush()
        return work_order

    # =====================
    # Helper Methods
    # =====================

    async def _add_flow_history(
        self,
        work_order_id: str,
        from_status: WorkOrderFlowStatus,
        to_status: WorkOrderFlowStatus,
        triggered_by_module: str,
        performed_by: str,
        notes: Optional[str] = None,
    ) -> WorkOrderFlowHistory:
        """Add a flow history entry."""
        history = WorkOrderFlowHistory(
            work_order_id=work_order_id,
            from_status=from_status,
            to_status=to_status,
            triggered_by_module=triggered_by_module,
            performed_by=performed_by,
            notes=notes,
        )
        self.session.add(history)
        return history

    async def get_flow_history(
        self,
        work_order_id: str,
    ) -> List[WorkOrderFlowHistory]:
        """Get the flow history for a work order."""
        result = await self.session.execute(
            select(WorkOrderFlowHistory)
            .where(WorkOrderFlowHistory.work_order_id == work_order_id)
            .order_by(WorkOrderFlowHistory.created_at.asc())
        )
        return list(result.scalars().all())
