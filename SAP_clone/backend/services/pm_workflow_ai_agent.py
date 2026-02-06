"""
AI Agent Framework for PM Workflow
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7

This module provides AI-powered assistance for the 6-screen PM workflow,
including validation, suggestions, alerts, and analytics.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.models.pm_workflow_models import (
    WorkflowMaintenanceOrder, WorkflowOperation, WorkflowComponent,
    WorkflowPurchaseOrder, WorkflowGoodsIssue, WorkflowConfirmation,
    WorkflowDocumentFlow, WorkflowCostSummary, WorkflowOrderStatus,
    WorkflowOrderType, POStatus, DocumentType, OperationStatus
)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    blocking_reasons: List[str]
    warnings: List[str]
    suggestions: List[str]


@dataclass
class Suggestion:
    """AI-generated suggestion"""
    title: str
    description: str
    confidence: float
    action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class Alert:
    """AI-generated alert"""
    severity: AlertSeverity
    title: str
    message: str
    action_required: bool
    suggested_actions: List[str]
    related_documents: List[str]


@dataclass
class AnalyticsResult:
    """Result of analytics analysis"""
    metric_name: str
    value: Any
    comparison: Optional[str]
    trend: Optional[str]
    insights: List[str]


class AIAgentBase(ABC):
    """Base class for AI agents - Requirements: 8.1-8.7"""
    
    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        """Perform validation checks - Requirement 8.4"""
        pass

    @abstractmethod
    def suggest(self, context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions - Requirements 8.1, 8.2"""
        pass

    @abstractmethod
    def alert(self, context: Dict[str, Any]) -> List[Alert]:
        """Generate alerts - Requirements 8.3, 8.6"""
        pass

    @abstractmethod
    def analyze(self, context: Dict[str, Any]) -> List[AnalyticsResult]:
        """Perform analytics - Requirement 8.6"""
        pass



class ValidationEngine:
    """Engine for prerequisite validation - Requirements 8.4, 8.5"""
    
    def __init__(self, db: Session):
        self.db = db

    def validate_order_release(self, order: WorkflowMaintenanceOrder) -> ValidationResult:
        """Validate order release prerequisites - Requirements: 3.1, 3.2, 8.4"""
        blocking_reasons = []
        warnings = []
        suggestions = []

        if order.status != WorkflowOrderStatus.PLANNED:
            blocking_reasons.append(f"Order must be in PLANNED status, currently {order.status}")

        if not order.operations:
            blocking_reasons.append("At least one operation must be defined")
        
        if not order.components:
            warnings.append("No components defined - verify if materials are required")

        critical_materials_unavailable = []
        for component in order.components:
            if component.has_master_data and component.quantity_issued == 0:
                has_po = any(po.status in [POStatus.ORDERED, POStatus.DELIVERED] for po in order.purchase_orders)
                if not has_po:
                    critical_materials_unavailable.append(component.description)

        if critical_materials_unavailable:
            warnings.append(f"Materials not on order: {', '.join(critical_materials_unavailable)}")
            suggestions.append("Create purchase orders for required materials")

        if order.order_type == WorkflowOrderType.BREAKDOWN:
            warnings = [w for w in warnings if "components" not in w.lower()]
            suggestions.append("Breakdown order: Emergency stock can be used")

        return ValidationResult(
            is_valid=len(blocking_reasons) == 0,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            suggestions=suggestions
        )

    def validate_goods_issue_before_confirmation(
        self, order: WorkflowMaintenanceOrder, operation_id: str
    ) -> ValidationResult:
        """Validate GI before confirmation - Requirements: 5.1, 5.6, 8.5"""
        blocking_reasons = []
        warnings = []
        suggestions = []

        if not order.goods_issues:
            blocking_reasons.append("Goods issue must be posted before confirmation")
            suggestions.append("Post goods issue for required components first")
        else:
            gi_dates = [gi.issue_date for gi in order.goods_issues]
            if gi_dates:
                latest_gi = max(gi_dates)
                suggestions.append(f"Latest goods issue posted on {latest_gi.strftime('%Y-%m-%d %H:%M')}")

        return ValidationResult(
            is_valid=len(blocking_reasons) == 0,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            suggestions=suggestions
        )

    def validate_teco_prerequisites(self, order: WorkflowMaintenanceOrder) -> ValidationResult:
        """Validate TECO prerequisites - Requirements: 6.1, 6.2, 6.3, 8.4"""
        blocking_reasons = []
        warnings = []
        suggestions = []

        unconfirmed_operations = [op for op in order.operations if op.status != OperationStatus.CONFIRMED]
        if unconfirmed_operations:
            blocking_reasons.append(f"{len(unconfirmed_operations)} operation(s) not confirmed")
            suggestions.append("Confirm all operations before TECO")

        total_required = sum(c.quantity_required for c in order.components)
        total_issued = sum(c.quantity_issued for c in order.components)
        
        if total_required > 0 and total_issued < total_required:
            blocking_reasons.append(f"Not all materials issued: {total_issued}/{total_required}")
            suggestions.append("Post remaining goods issues")

        if order.order_type == WorkflowOrderType.BREAKDOWN:
            if not order.malfunction_reports:
                blocking_reasons.append("Malfunction report required for breakdown orders")
                suggestions.append("Submit malfunction report with cause code")

        required_doc_types = {DocumentType.ORDER, DocumentType.GI, DocumentType.CONFIRMATION}
        existing_doc_types = {doc.document_type for doc in order.document_flow}
        missing_docs = required_doc_types - existing_doc_types
        
        if missing_docs:
            warnings.append(f"Missing document types: {', '.join(str(d.value) for d in missing_docs)}")

        return ValidationResult(
            is_valid=len(blocking_reasons) == 0,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            suggestions=suggestions
        )



class SuggestionEngine:
    """Engine for intelligent suggestions - Requirements 8.1, 8.2"""
    
    def __init__(self, db: Session):
        self.db = db

    def suggest_similar_orders(
        self, equipment_id: Optional[str], order_type: WorkflowOrderType
    ) -> List[Suggestion]:
        """Suggest similar historical orders - Requirement 8.1"""
        suggestions = []
        if not equipment_id:
            return suggestions

        similar_orders = (
            self.db.query(WorkflowMaintenanceOrder)
            .filter(and_(
                WorkflowMaintenanceOrder.equipment_id == equipment_id,
                WorkflowMaintenanceOrder.order_type == order_type,
                WorkflowMaintenanceOrder.status == WorkflowOrderStatus.TECO
            ))
            .order_by(WorkflowMaintenanceOrder.completed_at.desc())
            .limit(5)
            .all()
        )

        for order in similar_orders:
            if order.cost_summary:
                suggestions.append(Suggestion(
                    title=f"Similar Order: {order.order_number}",
                    description=f"Completed on {order.completed_at.strftime('%Y-%m-%d')}",
                    confidence=0.8,
                    data={
                        "order_number": order.order_number,
                        "estimated_cost": float(order.cost_summary.estimated_total_cost),
                        "actual_cost": float(order.cost_summary.actual_total_cost),
                        "variance": float(order.cost_summary.total_variance),
                        "operations_count": len(order.operations),
                        "components_count": len(order.components)
                    }
                ))

        if suggestions:
            avg_cost = sum(s.data["actual_cost"] for s in suggestions if s.data) / len(suggestions)
            suggestions.insert(0, Suggestion(
                title="Cost Benchmark",
                description=f"Average cost for similar work: ${avg_cost:,.2f}",
                confidence=0.9,
                data={"average_cost": avg_cost}
            ))

        return suggestions

    def suggest_material_alternatives(self, material_number: str, quantity: Decimal) -> List[Suggestion]:
        """Suggest material alternatives - Requirement 8.2"""
        return [Suggestion(
            title="Check Material Availability",
            description=f"Verify stock for material {material_number}",
            confidence=0.7,
            action="check_inventory",
            data={"material_number": material_number, "quantity": float(quantity)}
        )]

    def suggest_next_actions(self, order: WorkflowMaintenanceOrder) -> List[Suggestion]:
        """Suggest next actions - Requirement 8.7"""
        suggestions = []

        if order.status == WorkflowOrderStatus.CREATED:
            suggestions.extend([
                Suggestion("Add Operations", "Define work operations and assign work centers", 1.0, "add_operations"),
                Suggestion("Add Components", "Specify required materials and quantities", 1.0, "add_components")
            ])
        elif order.status == WorkflowOrderStatus.PLANNED:
            if not order.purchase_orders:
                suggestions.append(Suggestion("Create Purchase Orders", "Procure materials for execution", 0.9, "create_po"))
            suggestions.append(Suggestion("Release Order", "Validate prerequisites and release for execution", 0.8, "release_order"))
        elif order.status == WorkflowOrderStatus.RELEASED:
            if not order.goods_issues:
                suggestions.append(Suggestion("Post Goods Issue", "Issue materials before starting work", 1.0, "post_gi"))
            else:
                suggestions.append(Suggestion("Confirm Work", "Record work completion and actual hours", 0.9, "confirm_work"))
        elif order.status == WorkflowOrderStatus.CONFIRMED:
            suggestions.append(Suggestion("Technical Completion", "Review costs and complete the order", 0.9, "teco"))

        return suggestions



class AlertEngine:
    """Engine for alerts - Requirements 8.3, 8.6"""
    
    def __init__(self, db: Session):
        self.db = db

    def check_procurement_delays(self, order: WorkflowMaintenanceOrder) -> List[Alert]:
        """Alert on procurement delays - Requirement 8.3"""
        alerts = []
        now = datetime.utcnow()

        for po in order.purchase_orders:
            if po.status not in [POStatus.DELIVERED, POStatus.PARTIALLY_DELIVERED]:
                if po.delivery_date < now:
                    days_overdue = (now - po.delivery_date).days
                    alerts.append(Alert(
                        severity=AlertSeverity.WARNING if days_overdue < 7 else AlertSeverity.ERROR,
                        title=f"PO {po.po_number} Overdue",
                        message=f"Delivery was due {days_overdue} days ago",
                        action_required=True,
                        suggested_actions=[
                            "Contact vendor for status update",
                            "Consider alternative suppliers",
                            "Expedite delivery if critical"
                        ],
                        related_documents=[po.po_number]
                    ))

        return alerts

    def check_cost_variance(self, order: WorkflowMaintenanceOrder) -> List[Alert]:
        """Alert on cost variances - Requirement 8.6"""
        alerts = []
        if not order.cost_summary:
            return alerts

        cost_summary = order.cost_summary
        variance_threshold = Decimal("10.0")

        if abs(cost_summary.variance_percentage) > variance_threshold:
            severity = AlertSeverity.WARNING if abs(cost_summary.variance_percentage) < 20 else AlertSeverity.ERROR
            alerts.append(Alert(
                severity=severity,
                title="Significant Cost Variance",
                message=f"Cost variance of {cost_summary.variance_percentage}% detected",
                action_required=True,
                suggested_actions=[
                    "Review actual costs vs estimates",
                    "Provide variance explanation",
                    "Update future estimates based on actuals"
                ],
                related_documents=[order.order_number]
            ))

        return alerts

    def check_missing_prerequisites(
        self, order: WorkflowMaintenanceOrder, validation_result: ValidationResult
    ) -> List[Alert]:
        """Alert on missing prerequisites - Requirement 8.5"""
        alerts = []
        if validation_result.blocking_reasons:
            alerts.append(Alert(
                severity=AlertSeverity.ERROR,
                title="Prerequisites Not Met",
                message="; ".join(validation_result.blocking_reasons),
                action_required=True,
                suggested_actions=validation_result.suggestions,
                related_documents=[order.order_number]
            ))
        return alerts



class AnalyticsEngine:
    """Engine for analytics - Requirement 8.6"""
    
    def __init__(self, db: Session):
        self.db = db

    def analyze_cost_variance(self, order: WorkflowMaintenanceOrder) -> List[AnalyticsResult]:
        """Analyze cost variance - Requirement 8.6"""
        results = []
        if not order.cost_summary:
            return results

        cs = order.cost_summary

        if cs.estimated_material_cost > 0:
            material_variance_pct = (
                (cs.actual_material_cost - cs.estimated_material_cost) / cs.estimated_material_cost * 100
            )
            results.append(AnalyticsResult(
                metric_name="Material Cost Variance",
                value=f"{material_variance_pct:.1f}%",
                comparison=f"${cs.actual_material_cost} vs ${cs.estimated_material_cost}",
                trend="over" if material_variance_pct > 0 else "under",
                insights=self._generate_variance_insights("material", material_variance_pct)
            ))

        if cs.estimated_labor_cost > 0:
            labor_variance_pct = (
                (cs.actual_labor_cost - cs.estimated_labor_cost) / cs.estimated_labor_cost * 100
            )
            results.append(AnalyticsResult(
                metric_name="Labor Cost Variance",
                value=f"{labor_variance_pct:.1f}%",
                comparison=f"${cs.actual_labor_cost} vs ${cs.estimated_labor_cost}",
                trend="over" if labor_variance_pct > 0 else "under",
                insights=self._generate_variance_insights("labor", labor_variance_pct)
            ))

        results.append(AnalyticsResult(
            metric_name="Total Cost Variance",
            value=f"{cs.variance_percentage:.1f}%",
            comparison=f"${cs.actual_total_cost} vs ${cs.estimated_total_cost}",
            trend="over" if cs.variance_percentage > 0 else "under",
            insights=self._generate_variance_insights("total", float(cs.variance_percentage))
        ))

        return results

    def _generate_variance_insights(self, cost_type: str, variance_pct: float) -> List[str]:
        """Generate insights based on variance percentage"""
        insights = []

        if abs(variance_pct) < 5:
            insights.append(f"{cost_type.capitalize()} costs within acceptable range")
        elif abs(variance_pct) < 15:
            insights.append(f"Moderate {cost_type} variance - review estimates")
        else:
            insights.append(f"Significant {cost_type} variance - investigation required")

        if variance_pct > 0:
            insights.append(f"Actual {cost_type} costs exceeded estimates")
            insights.append("Consider updating future estimates upward")
        else:
            insights.append(f"Actual {cost_type} costs below estimates")
            insights.append("Estimates may be conservative")

        return insights



class PMWorkflowAIAgent(AIAgentBase):
    """Main AI Agent for PM Workflow - Requirements: 8.1-8.7"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.validation_engine = ValidationEngine(db)
        self.suggestion_engine = SuggestionEngine(db)
        self.alert_engine = AlertEngine(db)
        self.analytics_engine = AnalyticsEngine(db)

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        """Perform validation - Requirement 8.4"""
        validation_type = context.get("validation_type")
        order = context.get("order")

        if not order:
            return ValidationResult(False, ["Order not provided"], [], [])

        if validation_type == "release":
            return self.validation_engine.validate_order_release(order)
        elif validation_type == "confirmation":
            operation_id = context.get("operation_id")
            return self.validation_engine.validate_goods_issue_before_confirmation(order, operation_id)
        elif validation_type == "teco":
            return self.validation_engine.validate_teco_prerequisites(order)
        else:
            return ValidationResult(True, [], [], [])

    def suggest(self, context: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions - Requirements 8.1, 8.2, 8.7"""
        suggestion_type = context.get("suggestion_type")
        suggestions = []

        if suggestion_type == "similar_orders":
            equipment_id = context.get("equipment_id")
            order_type = context.get("order_type", WorkflowOrderType.GENERAL)
            suggestions = self.suggestion_engine.suggest_similar_orders(equipment_id, order_type)
        elif suggestion_type == "material_alternatives":
            material_number = context.get("material_number")
            quantity = context.get("quantity", Decimal("1"))
            suggestions = self.suggestion_engine.suggest_material_alternatives(material_number, quantity)
        elif suggestion_type == "next_actions":
            order = context.get("order")
            if order:
                suggestions = self.suggestion_engine.suggest_next_actions(order)

        return suggestions

    def alert(self, context: Dict[str, Any]) -> List[Alert]:
        """Generate alerts - Requirements 8.3, 8.5, 8.6"""
        order = context.get("order")
        if not order:
            return []

        alerts = []
        alerts.extend(self.alert_engine.check_procurement_delays(order))
        alerts.extend(self.alert_engine.check_cost_variance(order))

        validation_result = context.get("validation_result")
        if validation_result:
            alerts.extend(self.alert_engine.check_missing_prerequisites(order, validation_result))

        return alerts

    def analyze(self, context: Dict[str, Any]) -> List[AnalyticsResult]:
        """Perform analytics - Requirement 8.6"""
        order = context.get("order")
        if not order:
            return []
        return self.analytics_engine.analyze_cost_variance(order)

    def get_comprehensive_assistance(
        self, order: WorkflowMaintenanceOrder, validation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive AI assistance for an order"""
        validation_result = None
        if validation_type:
            validation_result = self.validate({"validation_type": validation_type, "order": order})

        suggestions = self.suggest({"suggestion_type": "next_actions", "order": order})

        if order.equipment_id:
            similar_suggestions = self.suggest({
                "suggestion_type": "similar_orders",
                "equipment_id": order.equipment_id,
                "order_type": order.order_type
            })
            suggestions.extend(similar_suggestions)

        alerts = self.alert({"order": order, "validation_result": validation_result})

        analytics = []
        if order.cost_summary:
            analytics = self.analyze({"order": order})

        return {
            "validation": validation_result,
            "suggestions": suggestions,
            "alerts": alerts,
            "analytics": analytics
        }
