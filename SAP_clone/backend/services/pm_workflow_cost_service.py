"""
PM Workflow Cost Management Service
Requirements: 1.5, 6.4, 6.5, 6.6, 6.7

This service handles all cost-related operations for the PM workflow:
- Cost estimation
- Actual cost accumulation
- Cost variance calculation
- Cost settlement to FI
- Cost element breakdown (material, labor, external)
"""
from decimal import Decimal
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.pm_workflow_models import (
    WorkflowMaintenanceOrder,
    WorkflowCostSummary,
    WorkflowComponent,
    WorkflowOperation,
    WorkflowGoodsIssue,
    WorkflowConfirmation,
    WorkflowDocumentFlow,
    DocumentType,
    ConfirmationType
)


class CostManagementService:
    """Service for cost management operations"""
    
    # Cost rates (in real system, these would come from configuration/master data)
    DEFAULT_LABOR_RATE = Decimal("50.00")  # $ per hour
    DEFAULT_EXTERNAL_RATE = Decimal("75.00")  # $ per hour
    DEFAULT_MATERIAL_RATE = Decimal("10.00")  # $ per unit (fallback)
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_cost_estimate(
        self,
        order_number: str,
        labor_rate: Optional[Decimal] = None,
        external_rate: Optional[Decimal] = None
    ) -> Optional[WorkflowCostSummary]:
        """
        Calculate comprehensive cost estimate for order.
        Requirement 1.5
        
        Calculates estimated costs by element:
        - Material costs from components
        - Labor costs from operations
        - External costs from service operations
        
        Args:
            order_number: The maintenance order number
            labor_rate: Optional custom labor rate ($/hour)
            external_rate: Optional custom external service rate ($/hour)
            
        Returns:
            WorkflowCostSummary with estimated costs
        """
        # Get order with relationships
        result = await self.db.execute(
            select(WorkflowMaintenanceOrder)
            .where(WorkflowMaintenanceOrder.order_number == order_number)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return None
        
        # Use provided rates or defaults
        labor_rate = labor_rate or self.DEFAULT_LABOR_RATE
        external_rate = external_rate or self.DEFAULT_EXTERNAL_RATE
        
        # Calculate material costs from components
        material_cost = await self._calculate_estimated_material_cost(order_number)
        
        # Calculate labor costs from operations
        labor_cost = await self._calculate_estimated_labor_cost(order_number, labor_rate)
        
        # Calculate external costs (from service operations or POs)
        external_cost = await self._calculate_estimated_external_cost(order_number, external_rate)
        
        # Calculate total
        total_cost = material_cost + labor_cost + external_cost
        
        # Get or create cost summary
        result = await self.db.execute(
            select(WorkflowCostSummary)
            .where(WorkflowCostSummary.order_number == order_number)
        )
        cost_summary = result.scalar_one_or_none()
        
        if not cost_summary:
            cost_summary = WorkflowCostSummary(order_number=order_number)
            self.db.add(cost_summary)
        
        # Update estimates
        cost_summary.estimated_material_cost = material_cost
        cost_summary.estimated_labor_cost = labor_cost
        cost_summary.estimated_external_cost = external_cost
        cost_summary.estimated_total_cost = total_cost
        
        # Recalculate variances if actuals exist
        if cost_summary.actual_total_cost and cost_summary.actual_total_cost > 0:
            await self._recalculate_variances(cost_summary)
        
        await self.db.flush()
        
        return cost_summary
    
    async def accumulate_actual_costs(
        self,
        order_number: str
    ) -> Optional[WorkflowCostSummary]:
        """
        Accumulate actual costs from all postings.
        Requirements: 6.4
        
        Accumulates actual costs from:
        - Goods issues (material costs)
        - Confirmations (labor costs)
        - Service entries (external costs)
        
        Returns:
            WorkflowCostSummary with updated actual costs
        """
        # Get or create cost summary
        result = await self.db.execute(
            select(WorkflowCostSummary)
            .where(WorkflowCostSummary.order_number == order_number)
        )
        cost_summary = result.scalar_one_or_none()
        
        if not cost_summary:
            cost_summary = WorkflowCostSummary(order_number=order_number)
            self.db.add(cost_summary)
        
        # Accumulate material costs from goods issues
        material_cost = await self._accumulate_material_costs(order_number)
        
        # Accumulate labor costs from confirmations
        labor_cost = await self._accumulate_labor_costs(order_number)
        
        # Accumulate external costs from service entries
        external_cost = await self._accumulate_external_costs(order_number)
        
        # Update actual costs
        cost_summary.actual_material_cost = material_cost
        cost_summary.actual_labor_cost = labor_cost
        cost_summary.actual_external_cost = external_cost
        cost_summary.actual_total_cost = material_cost + labor_cost + external_cost
        
        # Recalculate variances
        await self._recalculate_variances(cost_summary)
        
        await self.db.flush()
        
        return cost_summary
    
    async def calculate_cost_variance(
        self,
        order_number: str
    ) -> Optional[Dict]:
        """
        Calculate cost variance analysis.
        Requirements: 6.5, 6.6
        
        Returns detailed variance analysis by cost element:
        - Material variance (amount and percentage)
        - Labor variance (amount and percentage)
        - External variance (amount and percentage)
        - Total variance (amount and percentage)
        
        Returns:
            Dictionary with variance analysis
        """
        # Get cost summary
        result = await self.db.execute(
            select(WorkflowCostSummary)
            .where(WorkflowCostSummary.order_number == order_number)
        )
        cost_summary = result.scalar_one_or_none()
        
        if not cost_summary:
            return None
        
        # Calculate variance percentages by element
        material_variance_pct = self._calculate_variance_percentage(
            cost_summary.actual_material_cost,
            cost_summary.estimated_material_cost
        )
        
        labor_variance_pct = self._calculate_variance_percentage(
            cost_summary.actual_labor_cost,
            cost_summary.estimated_labor_cost
        )
        
        external_variance_pct = self._calculate_variance_percentage(
            cost_summary.actual_external_cost,
            cost_summary.estimated_external_cost
        )
        
        total_variance_pct = self._calculate_variance_percentage(
            cost_summary.actual_total_cost,
            cost_summary.estimated_total_cost
        )
        
        # Determine variance status
        variance_status = self._determine_variance_status(total_variance_pct)
        
        # Build variance analysis
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
                    "percentage": float(material_variance_pct),
                    "status": self._determine_variance_status(material_variance_pct)
                },
                "labor": {
                    "amount": float(cost_summary.labor_variance),
                    "percentage": float(labor_variance_pct),
                    "status": self._determine_variance_status(labor_variance_pct)
                },
                "external": {
                    "amount": float(cost_summary.external_variance),
                    "percentage": float(external_variance_pct),
                    "status": self._determine_variance_status(external_variance_pct)
                },
                "total": {
                    "amount": float(cost_summary.total_variance),
                    "percentage": float(total_variance_pct),
                    "status": variance_status
                }
            },
            "variance_status": variance_status,
            "requires_explanation": abs(total_variance_pct) > 10  # >10% variance requires explanation
        }
    
    async def settle_costs_to_fi(
        self,
        order_number: str,
        cost_center: str,
        wbs_element: Optional[str],
        equipment_number: Optional[str],
        settled_by: str,
        settlement_notes: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Settle costs to FI (Financial Accounting).
        Requirement 6.7
        
        Posts final costs to:
        - Cost center (mandatory)
        - WBS element (optional, for project-related work)
        - Equipment (optional, for equipment-specific costs)
        
        Args:
            order_number: The maintenance order number
            cost_center: Target cost center for settlement
            wbs_element: Optional WBS element for project costs
            equipment_number: Optional equipment number for asset costs
            settled_by: User performing settlement
            settlement_notes: Optional notes about settlement
            
        Returns:
            Tuple of (success, error_message, settlement_document)
        """
        # Get order
        result = await self.db.execute(
            select(WorkflowMaintenanceOrder)
            .where(WorkflowMaintenanceOrder.order_number == order_number)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return False, f"Order not found: {order_number}", None
        
        # Verify order is TECO
        from backend.models.pm_workflow_models import WorkflowOrderStatus
        if order.status != WorkflowOrderStatus.TECO:
            return False, f"Order must be in TECO status to settle costs. Current status: {order.status.value}", None
        
        # Get cost summary
        result = await self.db.execute(
            select(WorkflowCostSummary)
            .where(WorkflowCostSummary.order_number == order_number)
        )
        cost_summary = result.scalar_one_or_none()
        
        if not cost_summary:
            return False, "Cost summary not found for order", None
        
        # Verify costs exist
        if cost_summary.actual_total_cost == 0:
            return False, "No actual costs to settle", None
        
        # Generate settlement document number
        settlement_doc = self._generate_settlement_document(order_number)
        
        # In a real system, this would:
        # 1. Create FI posting documents
        # 2. Debit cost center/WBS/equipment
        # 3. Credit maintenance order
        # 4. Update FI tables
        
        # For now, create document flow entry with settlement details
        await self._create_settlement_document_flow(
            order_number=order_number,
            settlement_doc=settlement_doc,
            cost_center=cost_center,
            wbs_element=wbs_element,
            equipment_number=equipment_number,
            settled_by=settled_by,
            settlement_notes=settlement_notes,
            cost_summary=cost_summary
        )
        
        await self.db.flush()
        
        return True, None, settlement_doc
    
    async def get_cost_element_breakdown(
        self,
        order_number: str
    ) -> Optional[Dict]:
        """
        Get detailed cost element breakdown.
        Requirements: 1.5, 6.4
        
        Returns detailed breakdown of costs by element with line items:
        - Material costs (by component/goods issue)
        - Labor costs (by operation/confirmation)
        - External costs (by service entry)
        
        Returns:
            Dictionary with detailed cost breakdown
        """
        # Get cost summary
        result = await self.db.execute(
            select(WorkflowCostSummary)
            .where(WorkflowCostSummary.order_number == order_number)
        )
        cost_summary = result.scalar_one_or_none()
        
        if not cost_summary:
            return None
        
        # Get material cost details
        material_details = await self._get_material_cost_details(order_number)
        
        # Get labor cost details
        labor_details = await self._get_labor_cost_details(order_number)
        
        # Get external cost details
        external_details = await self._get_external_cost_details(order_number)
        
        return {
            "order_number": order_number,
            "summary": {
                "estimated_total": float(cost_summary.estimated_total_cost),
                "actual_total": float(cost_summary.actual_total_cost),
                "variance_total": float(cost_summary.total_variance),
                "variance_percentage": float(cost_summary.variance_percentage)
            },
            "material_costs": {
                "estimated": float(cost_summary.estimated_material_cost),
                "actual": float(cost_summary.actual_material_cost),
                "variance": float(cost_summary.material_variance),
                "line_items": material_details
            },
            "labor_costs": {
                "estimated": float(cost_summary.estimated_labor_cost),
                "actual": float(cost_summary.actual_labor_cost),
                "variance": float(cost_summary.labor_variance),
                "line_items": labor_details
            },
            "external_costs": {
                "estimated": float(cost_summary.estimated_external_cost),
                "actual": float(cost_summary.actual_external_cost),
                "variance": float(cost_summary.external_variance),
                "line_items": external_details
            }
        }
    
    # Private helper methods
    
    async def _calculate_estimated_material_cost(self, order_number: str) -> Decimal:
        """Calculate estimated material cost from components"""
        result = await self.db.execute(
            select(WorkflowComponent)
            .where(WorkflowComponent.order_number == order_number)
        )
        components = result.scalars().all()
        
        return sum(comp.estimated_cost for comp in components)
    
    async def _calculate_estimated_labor_cost(
        self,
        order_number: str,
        labor_rate: Decimal
    ) -> Decimal:
        """Calculate estimated labor cost from operations"""
        result = await self.db.execute(
            select(WorkflowOperation)
            .where(WorkflowOperation.order_number == order_number)
        )
        operations = result.scalars().all()
        
        return sum(op.planned_hours * labor_rate for op in operations)
    
    async def _calculate_estimated_external_cost(
        self,
        order_number: str,
        external_rate: Decimal
    ) -> Decimal:
        """Calculate estimated external cost from service operations/POs"""
        # In real system, would get from service POs
        # For now, return 0 as placeholder
        return Decimal("0.00")
    
    async def _accumulate_material_costs(self, order_number: str) -> Decimal:
        """Accumulate actual material costs from goods issues"""
        result = await self.db.execute(
            select(WorkflowGoodsIssue)
            .where(WorkflowGoodsIssue.order_number == order_number)
        )
        goods_issues = result.scalars().all()
        
        # In real system, would get actual cost from inventory valuation
        # For now, use estimated cost * quantity
        total_cost = Decimal("0.00")
        for gi in goods_issues:
            # Get component to find estimated unit cost
            comp_result = await self.db.execute(
                select(WorkflowComponent)
                .where(WorkflowComponent.component_id == gi.component_id)
            )
            component = comp_result.scalar_one_or_none()
            
            if component and component.quantity_required > 0:
                unit_cost = component.estimated_cost / component.quantity_required
                total_cost += gi.quantity_issued * unit_cost
            else:
                # Fallback to default rate
                total_cost += gi.quantity_issued * self.DEFAULT_MATERIAL_RATE
        
        return total_cost
    
    async def _accumulate_labor_costs(self, order_number: str) -> Decimal:
        """Accumulate actual labor costs from confirmations"""
        result = await self.db.execute(
            select(WorkflowConfirmation)
            .where(
                WorkflowConfirmation.order_number == order_number,
                WorkflowConfirmation.confirmation_type == ConfirmationType.INTERNAL
            )
        )
        confirmations = result.scalars().all()
        
        # Calculate labor cost from actual hours
        return sum(conf.actual_hours * self.DEFAULT_LABOR_RATE for conf in confirmations)
    
    async def _accumulate_external_costs(self, order_number: str) -> Decimal:
        """Accumulate actual external costs from service entries"""
        result = await self.db.execute(
            select(WorkflowConfirmation)
            .where(
                WorkflowConfirmation.order_number == order_number,
                WorkflowConfirmation.confirmation_type == ConfirmationType.EXTERNAL
            )
        )
        external_confirmations = result.scalars().all()
        
        # Calculate external cost from actual hours
        return sum(conf.actual_hours * self.DEFAULT_EXTERNAL_RATE for conf in external_confirmations)
    
    async def _recalculate_variances(self, cost_summary: WorkflowCostSummary) -> None:
        """Recalculate all variances in cost summary"""
        # Material variance
        cost_summary.material_variance = (
            cost_summary.actual_material_cost - cost_summary.estimated_material_cost
        )
        
        # Labor variance
        cost_summary.labor_variance = (
            cost_summary.actual_labor_cost - cost_summary.estimated_labor_cost
        )
        
        # External variance
        cost_summary.external_variance = (
            cost_summary.actual_external_cost - cost_summary.estimated_external_cost
        )
        
        # Total variance
        cost_summary.total_variance = (
            cost_summary.actual_total_cost - cost_summary.estimated_total_cost
        )
        
        # Variance percentage
        if cost_summary.estimated_total_cost > 0:
            cost_summary.variance_percentage = (
                cost_summary.total_variance / cost_summary.estimated_total_cost * 100
            )
        else:
            cost_summary.variance_percentage = Decimal("0.00")
    
    def _calculate_variance_percentage(
        self,
        actual: Decimal,
        estimated: Decimal
    ) -> Decimal:
        """Calculate variance percentage"""
        if estimated == 0:
            return Decimal("0.00") if actual == 0 else Decimal("100.00")
        
        variance = actual - estimated
        return (variance / estimated) * 100
    
    def _determine_variance_status(self, variance_pct: Decimal) -> str:
        """Determine variance status based on percentage"""
        abs_variance = abs(variance_pct)
        
        if abs_variance <= 5:
            return "acceptable"
        elif abs_variance <= 10:
            return "monitor"
        elif abs_variance <= 20:
            return "review_required"
        else:
            return "critical"
    
    def _generate_settlement_document(self, order_number: str) -> str:
        """Generate settlement document number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"SETTLEMENT-{order_number}-{timestamp}"
    
    async def _create_settlement_document_flow(
        self,
        order_number: str,
        settlement_doc: str,
        cost_center: str,
        wbs_element: Optional[str],
        equipment_number: Optional[str],
        settled_by: str,
        settlement_notes: Optional[str],
        cost_summary: WorkflowCostSummary
    ) -> None:
        """Create document flow entry for cost settlement"""
        import uuid
        
        # Build settlement details
        settlement_details = {
            "cost_center": cost_center,
            "material_cost": float(cost_summary.actual_material_cost),
            "labor_cost": float(cost_summary.actual_labor_cost),
            "external_cost": float(cost_summary.actual_external_cost),
            "total_cost": float(cost_summary.actual_total_cost)
        }
        
        if wbs_element:
            settlement_details["wbs_element"] = wbs_element
        
        if equipment_number:
            settlement_details["equipment"] = equipment_number
        
        if settlement_notes:
            settlement_details["notes"] = settlement_notes
        
        # Create document flow entry
        flow_entry = WorkflowDocumentFlow(
            flow_id=f"FLOW-{uuid.uuid4().hex[:12]}",
            order_number=order_number,
            document_type=DocumentType.ORDER,
            document_number=settlement_doc,
            transaction_date=datetime.utcnow(),
            user_id=settled_by,
            status=f"costs_settled_to_{cost_center}",
            related_document=order_number
        )
        
        self.db.add(flow_entry)
    
    async def _get_material_cost_details(self, order_number: str) -> List[Dict]:
        """Get detailed material cost line items"""
        result = await self.db.execute(
            select(WorkflowGoodsIssue)
            .where(WorkflowGoodsIssue.order_number == order_number)
        )
        goods_issues = result.scalars().all()
        
        details = []
        for gi in goods_issues:
            # Get component for cost info
            comp_result = await self.db.execute(
                select(WorkflowComponent)
                .where(WorkflowComponent.component_id == gi.component_id)
            )
            component = comp_result.scalar_one_or_none()
            
            if component and component.quantity_required > 0:
                unit_cost = component.estimated_cost / component.quantity_required
                line_cost = gi.quantity_issued * unit_cost
            else:
                unit_cost = self.DEFAULT_MATERIAL_RATE
                line_cost = gi.quantity_issued * unit_cost
            
            details.append({
                "document": gi.gi_document,
                "material": gi.material_number,
                "quantity": float(gi.quantity_issued),
                "unit_cost": float(unit_cost),
                "total_cost": float(line_cost),
                "date": gi.issue_date.isoformat()
            })
        
        return details
    
    async def _get_labor_cost_details(self, order_number: str) -> List[Dict]:
        """Get detailed labor cost line items"""
        result = await self.db.execute(
            select(WorkflowConfirmation)
            .where(
                WorkflowConfirmation.order_number == order_number,
                WorkflowConfirmation.confirmation_type == ConfirmationType.INTERNAL
            )
        )
        confirmations = result.scalars().all()
        
        details = []
        for conf in confirmations:
            line_cost = conf.actual_hours * self.DEFAULT_LABOR_RATE
            
            details.append({
                "document": conf.confirmation_id,
                "operation": conf.operation_id,
                "technician": conf.technician_id,
                "hours": float(conf.actual_hours),
                "rate": float(self.DEFAULT_LABOR_RATE),
                "total_cost": float(line_cost),
                "date": conf.confirmation_date.isoformat()
            })
        
        return details
    
    async def _get_external_cost_details(self, order_number: str) -> List[Dict]:
        """Get detailed external cost line items"""
        result = await self.db.execute(
            select(WorkflowConfirmation)
            .where(
                WorkflowConfirmation.order_number == order_number,
                WorkflowConfirmation.confirmation_type == ConfirmationType.EXTERNAL
            )
        )
        external_confirmations = result.scalars().all()
        
        details = []
        for conf in external_confirmations:
            line_cost = conf.actual_hours * self.DEFAULT_EXTERNAL_RATE
            
            details.append({
                "document": conf.confirmation_id,
                "operation": conf.operation_id,
                "vendor": conf.vendor_id,
                "hours": float(conf.actual_hours),
                "rate": float(self.DEFAULT_EXTERNAL_RATE),
                "total_cost": float(line_cost),
                "date": conf.confirmation_date.isoformat()
            })
        
        return details
