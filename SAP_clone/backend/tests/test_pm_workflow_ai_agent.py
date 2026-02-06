"""
Unit tests for PM Workflow AI Agent Framework
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.services.pm_workflow_ai_agent import (
    PMWorkflowAIAgent,
    ValidationEngine,
    SuggestionEngine,
    AlertEngine,
    AnalyticsEngine,
    ValidationResult,
    Suggestion,
    Alert,
    AlertSeverity,
    AnalyticsResult
)
from backend.models.pm_workflow_models import (
    WorkflowMaintenanceOrder,
    WorkflowOperation,
    WorkflowComponent,
    WorkflowPurchaseOrder,
    WorkflowGoodsIssue,
    WorkflowConfirmation,
    WorkflowMalfunctionReport,
    WorkflowDocumentFlow,
    WorkflowCostSummary,
    WorkflowOrderType,
    WorkflowOrderStatus,
    OperationStatus,
    POType,
    POStatus,
    ConfirmationType,
    DocumentType,
    Priority
)
from backend.db.database import Base


@pytest.fixture(scope="function")
def db():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_order(db: Session) -> WorkflowMaintenanceOrder:
    """Create a sample maintenance order for testing"""
    order = WorkflowMaintenanceOrder(
        order_number="TEST-001",
        order_type=WorkflowOrderType.GENERAL,
        status=WorkflowOrderStatus.PLANNED,
        equipment_id="EQ-001",
        functional_location="FL-001",
        priority=Priority.NORMAL,
        planned_start_date=datetime.utcnow() + timedelta(days=1),
        planned_end_date=datetime.utcnow() + timedelta(days=3),
        created_by="test_user",
        created_at=datetime.utcnow()
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@pytest.fixture
def sample_operation(db: Session, sample_order: WorkflowMaintenanceOrder) -> WorkflowOperation:
    """Create a sample operation"""
    operation = WorkflowOperation(
        operation_id="OP-001",
        order_number=sample_order.order_number,
        operation_number="0010",
        work_center="WC-001",
        description="Test operation",
        planned_hours=Decimal("8.0"),
        status=OperationStatus.PLANNED
    )
    db.add(operation)
    db.commit()
    db.refresh(operation)
    return operation


@pytest.fixture
def sample_component(db: Session, sample_order: WorkflowMaintenanceOrder) -> WorkflowComponent:
    """Create a sample component"""
    component = WorkflowComponent(
        component_id="COMP-001",
        order_number=sample_order.order_number,
        material_number="MAT-001",
        description="Test material",
        quantity_required=Decimal("10.0"),
        quantity_issued=Decimal("0.0"),
        unit_of_measure="EA",
        estimated_cost=Decimal("100.0"),
        has_master_data=True
    )
    db.add(component)
    db.commit()
    db.refresh(component)
    return component


@pytest.fixture
def sample_cost_summary(db: Session, sample_order: WorkflowMaintenanceOrder) -> WorkflowCostSummary:
    """Create a sample cost summary"""
    cost_summary = WorkflowCostSummary(
        order_number=sample_order.order_number,
        estimated_material_cost=Decimal("1000.0"),
        estimated_labor_cost=Decimal("500.0"),
        estimated_external_cost=Decimal("200.0"),
        estimated_total_cost=Decimal("1700.0"),
        actual_material_cost=Decimal("1200.0"),
        actual_labor_cost=Decimal("600.0"),
        actual_external_cost=Decimal("250.0"),
        actual_total_cost=Decimal("2050.0"),
        material_variance=Decimal("200.0"),
        labor_variance=Decimal("100.0"),
        external_variance=Decimal("50.0"),
        total_variance=Decimal("350.0"),
        variance_percentage=Decimal("20.59")
    )
    db.add(cost_summary)
    db.commit()
    db.refresh(cost_summary)
    return cost_summary


class TestValidationEngine:
    """Test validation engine - Requirement 8.4"""

    def test_validate_order_release_success(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_operation: WorkflowOperation, sample_component: WorkflowComponent
    ):
        """Test successful order release validation"""
        engine = ValidationEngine(db)
        result = engine.validate_order_release(sample_order)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.blocking_reasons) == 0

    def test_validate_order_release_wrong_status(self, db: Session, sample_order: WorkflowMaintenanceOrder):
        """Test order release validation with wrong status"""
        sample_order.status = WorkflowOrderStatus.CREATED
        db.commit()
        
        engine = ValidationEngine(db)
        result = engine.validate_order_release(sample_order)
        
        assert result.is_valid is False
        assert any("PLANNED status" in reason for reason in result.blocking_reasons)

    def test_validate_order_release_no_operations(self, db: Session, sample_order: WorkflowMaintenanceOrder):
        """Test order release validation without operations"""
        engine = ValidationEngine(db)
        result = engine.validate_order_release(sample_order)
        
        assert result.is_valid is False
        assert any("operation" in reason.lower() for reason in result.blocking_reasons)

    def test_validate_order_release_breakdown_reduced_validation(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_operation: WorkflowOperation
    ):
        """Test breakdown orders have reduced validation - Requirement 7.3"""
        sample_order.order_type = WorkflowOrderType.BREAKDOWN
        db.commit()
        
        engine = ValidationEngine(db)
        result = engine.validate_order_release(sample_order)
        
        # Breakdown orders should have suggestions about emergency stock
        assert any("emergency stock" in s.lower() for s in result.suggestions)

    def test_validate_gi_before_confirmation_no_gi(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_operation: WorkflowOperation
    ):
        """Test GI before confirmation validation - Requirement 8.5"""
        engine = ValidationEngine(db)
        result = engine.validate_goods_issue_before_confirmation(
            sample_order, sample_operation.operation_id
        )
        
        assert result.is_valid is False
        assert any("goods issue" in reason.lower() for reason in result.blocking_reasons)

    def test_validate_gi_before_confirmation_with_gi(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_operation: WorkflowOperation, sample_component: WorkflowComponent
    ):
        """Test GI before confirmation validation with GI posted"""
        # Add goods issue
        gi = WorkflowGoodsIssue(
            gi_document="GI-001",
            order_number=sample_order.order_number,
            component_id=sample_component.component_id,
            material_number=sample_component.material_number,
            quantity_issued=Decimal("10.0"),
            issue_date=datetime.utcnow(),
            cost_center="CC-001",
            issued_by="test_user"
        )
        db.add(gi)
        db.commit()
        
        engine = ValidationEngine(db)
        result = engine.validate_goods_issue_before_confirmation(
            sample_order, sample_operation.operation_id
        )
        
        assert result.is_valid is True
        assert len(result.blocking_reasons) == 0

    def test_validate_teco_prerequisites_success(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_operation: WorkflowOperation, sample_component: WorkflowComponent
    ):
        """Test TECO validation with all prerequisites met - Requirement 6.1, 6.2"""
        # Set operation as confirmed
        sample_operation.status = OperationStatus.CONFIRMED
        sample_component.quantity_issued = sample_component.quantity_required
        db.commit()
        
        engine = ValidationEngine(db)
        result = engine.validate_teco_prerequisites(sample_order)
        
        assert result.is_valid is True
        assert len(result.blocking_reasons) == 0

    def test_validate_teco_prerequisites_unconfirmed_operations(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_operation: WorkflowOperation
    ):
        """Test TECO validation with unconfirmed operations"""
        engine = ValidationEngine(db)
        result = engine.validate_teco_prerequisites(sample_order)
        
        assert result.is_valid is False
        assert any("not confirmed" in reason.lower() for reason in result.blocking_reasons)

    def test_validate_teco_prerequisites_breakdown_requires_malfunction(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_operation: WorkflowOperation, sample_component: WorkflowComponent
    ):
        """Test breakdown orders require malfunction report - Requirement 7.5"""
        sample_order.order_type = WorkflowOrderType.BREAKDOWN
        sample_operation.status = OperationStatus.CONFIRMED
        sample_component.quantity_issued = sample_component.quantity_required
        db.commit()
        
        engine = ValidationEngine(db)
        result = engine.validate_teco_prerequisites(sample_order)
        
        assert result.is_valid is False
        assert any("malfunction" in reason.lower() for reason in result.blocking_reasons)


class TestSuggestionEngine:
    """Test suggestion engine - Requirements 8.1, 8.2"""

    def test_suggest_similar_orders(self, db: Session):
        """Test similar order suggestions - Requirement 8.1"""
        # Create completed orders
        for i in range(3):
            order = WorkflowMaintenanceOrder(
                order_number=f"HIST-{i:03d}",
                order_type=WorkflowOrderType.GENERAL,
                status=WorkflowOrderStatus.TECO,
                equipment_id="EQ-001",
                priority=Priority.NORMAL,
                created_by="test_user",
                created_at=datetime.utcnow() - timedelta(days=30 + i),
                completed_at=datetime.utcnow() - timedelta(days=20 + i)
            )
            db.add(order)
            
            cost_summary = WorkflowCostSummary(
                order_number=order.order_number,
                estimated_total_cost=Decimal("1000.0"),
                actual_total_cost=Decimal("1100.0") + Decimal(i * 50),
                total_variance=Decimal("100.0") + Decimal(i * 50),
                variance_percentage=Decimal("10.0")
            )
            db.add(cost_summary)
        
        db.commit()
        
        engine = SuggestionEngine(db)
        suggestions = engine.suggest_similar_orders("EQ-001", WorkflowOrderType.GENERAL)
        
        assert len(suggestions) > 0
        # Should include cost benchmark
        assert any("benchmark" in s.title.lower() for s in suggestions)
        # Should include similar orders
        assert any("similar order" in s.title.lower() for s in suggestions)

    def test_suggest_material_alternatives(self, db: Session):
        """Test material alternative suggestions - Requirement 8.2"""
        engine = SuggestionEngine(db)
        suggestions = engine.suggest_material_alternatives("MAT-001", Decimal("10"))
        
        assert len(suggestions) > 0
        assert any("material" in s.title.lower() for s in suggestions)

    def test_suggest_next_actions_created_status(
        self, db: Session, sample_order: WorkflowMaintenanceOrder
    ):
        """Test next action suggestions for created order - Requirement 8.7"""
        sample_order.status = WorkflowOrderStatus.CREATED
        db.commit()
        
        engine = SuggestionEngine(db)
        suggestions = engine.suggest_next_actions(sample_order)
        
        assert len(suggestions) > 0
        assert any("operation" in s.title.lower() for s in suggestions)
        assert any("component" in s.title.lower() for s in suggestions)

    def test_suggest_next_actions_planned_status(
        self, db: Session, sample_order: WorkflowMaintenanceOrder
    ):
        """Test next action suggestions for planned order"""
        engine = SuggestionEngine(db)
        suggestions = engine.suggest_next_actions(sample_order)
        
        assert len(suggestions) > 0
        assert any("release" in s.title.lower() or "purchase" in s.title.lower() for s in suggestions)

    def test_suggest_next_actions_released_status(
        self, db: Session, sample_order: WorkflowMaintenanceOrder
    ):
        """Test next action suggestions for released order"""
        sample_order.status = WorkflowOrderStatus.RELEASED
        db.commit()
        
        engine = SuggestionEngine(db)
        suggestions = engine.suggest_next_actions(sample_order)
        
        assert len(suggestions) > 0
        assert any("goods issue" in s.title.lower() or "confirm" in s.title.lower() for s in suggestions)


class TestAlertEngine:
    """Test alert engine - Requirements 8.3, 8.6"""

    def test_check_procurement_delays(
        self, db: Session, sample_order: WorkflowMaintenanceOrder
    ):
        """Test procurement delay alerts - Requirement 8.3"""
        # Create overdue PO
        po = WorkflowPurchaseOrder(
            po_number="PO-001",
            order_number=sample_order.order_number,
            po_type=POType.MATERIAL,
            vendor_id="V-001",
            total_value=Decimal("1000.0"),
            delivery_date=datetime.utcnow() - timedelta(days=5),
            status=POStatus.ORDERED
        )
        db.add(po)
        db.commit()
        
        engine = AlertEngine(db)
        alerts = engine.check_procurement_delays(sample_order)
        
        assert len(alerts) > 0
        assert any("overdue" in alert.title.lower() for alert in alerts)
        assert any(alert.action_required for alert in alerts)

    def test_check_cost_variance(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_cost_summary: WorkflowCostSummary
    ):
        """Test cost variance alerts - Requirement 8.6"""
        engine = AlertEngine(db)
        alerts = engine.check_cost_variance(sample_order)
        
        assert len(alerts) > 0
        assert any("variance" in alert.title.lower() for alert in alerts)
        assert any(alert.severity in [AlertSeverity.WARNING, AlertSeverity.ERROR] for alert in alerts)

    def test_check_missing_prerequisites(
        self, db: Session, sample_order: WorkflowMaintenanceOrder
    ):
        """Test missing prerequisite alerts - Requirement 8.5"""
        validation_result = ValidationResult(
            is_valid=False,
            blocking_reasons=["Test blocking reason"],
            warnings=[],
            suggestions=["Test suggestion"]
        )
        
        engine = AlertEngine(db)
        alerts = engine.check_missing_prerequisites(sample_order, validation_result)
        
        assert len(alerts) > 0
        assert any(alert.severity == AlertSeverity.ERROR for alert in alerts)
        assert any("prerequisite" in alert.title.lower() for alert in alerts)


class TestAnalyticsEngine:
    """Test analytics engine - Requirement 8.6"""

    def test_analyze_cost_variance(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_cost_summary: WorkflowCostSummary
    ):
        """Test cost variance analysis - Requirement 8.6"""
        engine = AnalyticsEngine(db)
        results = engine.analyze_cost_variance(sample_order)
        
        assert len(results) > 0
        # Should have material, labor, and total variance
        assert any("material" in r.metric_name.lower() for r in results)
        assert any("labor" in r.metric_name.lower() for r in results)
        assert any("total" in r.metric_name.lower() for r in results)
        
        # Each result should have insights
        for result in results:
            assert len(result.insights) > 0

    def test_analyze_cost_variance_no_cost_summary(
        self, db: Session, sample_order: WorkflowMaintenanceOrder
    ):
        """Test cost variance analysis without cost summary"""
        engine = AnalyticsEngine(db)
        results = engine.analyze_cost_variance(sample_order)
        
        assert len(results) == 0


class TestPMWorkflowAIAgent:
    """Test main AI agent - Requirements 8.1-8.7"""

    def test_validate_release(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_operation: WorkflowOperation
    ):
        """Test AI agent validation"""
        agent = PMWorkflowAIAgent(db)
        result = agent.validate({
            "validation_type": "release",
            "order": sample_order
        })
        
        assert isinstance(result, ValidationResult)

    def test_suggest_similar_orders(self, db: Session):
        """Test AI agent suggestions"""
        agent = PMWorkflowAIAgent(db)
        suggestions = agent.suggest({
            "suggestion_type": "similar_orders",
            "equipment_id": "EQ-001",
            "order_type": WorkflowOrderType.GENERAL
        })
        
        assert isinstance(suggestions, list)

    def test_alert_on_order(
        self, db: Session, sample_order: WorkflowMaintenanceOrder
    ):
        """Test AI agent alerts"""
        agent = PMWorkflowAIAgent(db)
        alerts = agent.alert({"order": sample_order})
        
        assert isinstance(alerts, list)

    def test_analyze_order(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_cost_summary: WorkflowCostSummary
    ):
        """Test AI agent analytics"""
        agent = PMWorkflowAIAgent(db)
        results = agent.analyze({"order": sample_order})
        
        assert isinstance(results, list)
        assert len(results) > 0

    def test_get_comprehensive_assistance(
        self, db: Session, sample_order: WorkflowMaintenanceOrder,
        sample_operation: WorkflowOperation, sample_cost_summary: WorkflowCostSummary
    ):
        """Test comprehensive AI assistance"""
        agent = PMWorkflowAIAgent(db)
        assistance = agent.get_comprehensive_assistance(
            sample_order, validation_type="release"
        )
        
        assert "validation" in assistance
        assert "suggestions" in assistance
        assert "alerts" in assistance
        assert "analytics" in assistance
        
        assert isinstance(assistance["suggestions"], list)
        assert isinstance(assistance["alerts"], list)
        assert isinstance(assistance["analytics"], list)
