"""
CRM Integration API Routes.
Receives work orders from Salesforce CRM (via MuleSoft) and triggers PM → MM → FI workflow.

Integration Flow:
1. Salesforce Case created → MuleSoft sync_case_to_sap → This endpoint
2. This endpoint creates work order and triggers material check
3. Returns SAP work order ID back to MuleSoft for correlation
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.services.work_order_flow_service import (
    WorkOrderFlowService,
    WorkOrderNotFoundError,
    InvalidWorkOrderStateError,
    WorkOrderFlowError,
)


router = APIRouter(prefix="/crm-integration", tags=["CRM Integration (Salesforce → SAP)"])


# =====================
# Request/Response Models for Salesforce Integration
# =====================

class SalesforceMaterial(BaseModel):
    """Material from Salesforce Case"""
    product_id: str  # Salesforce Product ID
    product_name: str
    quantity: int
    unit: str = "EA"
    unit_price: Optional[float] = None


class SalesforceCase(BaseModel):
    """Salesforce Case mapped to SAP Work Order"""
    case_id: str  # Salesforce Case ID
    case_number: str
    subject: str
    description: str
    account_name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    priority: str = "Medium"  # Low, Medium, High, Urgent
    status: str = "New"
    type: Optional[str] = None  # Service, Installation, Maintenance, etc.
    origin: Optional[str] = None  # Web, Phone, Email

    # Location info
    site_address: str

    # Required materials (Products from Case)
    materials: List[SalesforceMaterial] = []

    # Assignment
    owner_name: Optional[str] = None

    # Cost center for material procurement
    cost_center_id: str = "CC-DEFAULT"

    # Requested date
    requested_date: Optional[datetime] = None


class SyncRequest(BaseModel):
    """MuleSoft sync request"""
    operation: str  # CREATE, UPDATE, DELETE
    case: SalesforceCase
    correlation_id: Optional[str] = None
    sync_timestamp: Optional[datetime] = None


class SyncResponse(BaseModel):
    """Response to MuleSoft sync"""
    success: bool
    message: str
    sap_work_order_id: Optional[str] = None
    sap_ticket_id: Optional[str] = None
    flow_status: Optional[str] = None
    materials_check: Optional[dict] = None
    correlation_id: Optional[str] = None


class WorkOrderStatusResponse(BaseModel):
    """Work order status for MuleSoft query"""
    sap_work_order_id: str
    salesforce_case_id: str
    flow_status: str
    materials_available: Optional[bool] = None
    fi_approval_status: Optional[str] = None
    last_updated: str


# =====================
# Helper Functions
# =====================

def map_salesforce_priority(sf_priority: str) -> str:
    """Map Salesforce priority to SAP priority"""
    mapping = {
        "Low": "low",
        "Medium": "medium",
        "High": "high",
        "Urgent": "urgent",
    }
    return mapping.get(sf_priority, "medium")


def map_salesforce_materials(sf_materials: List[SalesforceMaterial]) -> List[dict]:
    """Map Salesforce materials to SAP work order materials"""
    return [
        {
            "material_id": mat.product_id,
            "material_description": mat.product_name,
            "quantity_required": mat.quantity,
            "unit_of_measure": mat.unit,
            "unit_price": mat.unit_price,
        }
        for mat in sf_materials
    ]


# =====================
# Integration Endpoints
# =====================

@router.post("/sync-case", response_model=SyncResponse)
async def sync_salesforce_case(
    request: SyncRequest,
    x_mulesoft_correlation_id: Optional[str] = Header(None),
    x_salesforce_org_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive Salesforce Case from MuleSoft and create/update SAP Work Order.

    This is the main integration endpoint called by MuleSoft's sync_case_to_sap tool.

    Flow:
    1. Receive Case from Salesforce (via MuleSoft)
    2. Create Work Order in SAP with materials
    3. Automatically trigger material availability check (MM)
    4. If materials shortage, automatically raise FI ticket
    5. Return SAP Work Order ID for correlation
    """
    correlation_id = request.correlation_id or x_mulesoft_correlation_id

    service = WorkOrderFlowService(db)

    try:
        if request.operation == "CREATE":
            # Create work order from Salesforce Case
            materials = map_salesforce_materials(request.case.materials)

            work_order = await service.create_work_order_from_crm(
                title=request.case.subject,
                description=request.case.description,
                customer_name=request.case.account_name,
                site_location=request.case.site_address,
                requested_date=request.case.requested_date or datetime.utcnow(),
                cost_center_id=request.case.cost_center_id,
                created_by=f"CRM:{request.case.owner_name or 'system'}",
                materials=materials,
                crm_reference_id=request.case.case_id,
                customer_contact=request.case.contact_name,
                priority=map_salesforce_priority(request.case.priority),
                assigned_to=request.case.owner_name,
            )

            await db.commit()

            # Automatically check materials if materials are provided
            materials_check = None
            if materials:
                work_order, check_results = await service.send_to_mm_for_material_check(
                    work_order_id=work_order.work_order_id,
                    performed_by="SYSTEM:AUTO_CHECK",
                )

                all_available = all(r.is_available for r in check_results)

                materials_check = {
                    "all_available": all_available,
                    "total_materials": len(check_results),
                    "available_count": sum(1 for r in check_results if r.is_available),
                    "shortage_count": sum(1 for r in check_results if not r.is_available),
                }

                # If shortage, automatically raise FI ticket
                if not all_available:
                    work_order, fi_approval_id, fi_ticket_id = await service.raise_fi_ticket_for_purchase(
                        work_order_id=work_order.work_order_id,
                        performed_by="SYSTEM:AUTO_PURCHASE_REQUEST",
                        justification=f"Auto-generated purchase request for Salesforce Case {request.case.case_number}",
                    )
                    materials_check["fi_approval_id"] = fi_approval_id
                    materials_check["fi_ticket_id"] = fi_ticket_id

                await db.commit()

            # Reload work order to get latest status
            work_order = await service.get_work_order(work_order.work_order_id)

            return SyncResponse(
                success=True,
                message=f"Work order created successfully from Salesforce Case {request.case.case_number}",
                sap_work_order_id=work_order.work_order_id,
                sap_ticket_id=work_order.pm_ticket_id,
                flow_status=work_order.flow_status.value,
                materials_check=materials_check,
                correlation_id=correlation_id,
            )

        elif request.operation == "UPDATE":
            # Find existing work order by CRM reference
            work_orders, _ = await service.list_work_orders(limit=1)
            existing = None
            for wo in work_orders:
                if wo.crm_reference_id == request.case.case_id:
                    existing = wo
                    break

            if not existing:
                return SyncResponse(
                    success=False,
                    message=f"No work order found for Salesforce Case {request.case.case_id}",
                    correlation_id=correlation_id,
                )

            # Update work order (limited updates supported)
            # In a full implementation, you'd update more fields
            return SyncResponse(
                success=True,
                message=f"Work order update noted for Case {request.case.case_number}",
                sap_work_order_id=existing.work_order_id,
                flow_status=existing.flow_status.value,
                correlation_id=correlation_id,
            )

        elif request.operation == "DELETE":
            # Typically don't delete, just cancel
            return SyncResponse(
                success=True,
                message="Delete operation noted - work orders are cancelled, not deleted",
                correlation_id=correlation_id,
            )

        else:
            return SyncResponse(
                success=False,
                message=f"Unknown operation: {request.operation}",
                correlation_id=correlation_id,
            )

    except WorkOrderFlowError as e:
        return SyncResponse(
            success=False,
            message=str(e),
            correlation_id=correlation_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/case-status/{case_id}", response_model=WorkOrderStatusResponse)
async def get_case_status(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get SAP Work Order status for a Salesforce Case.

    Called by MuleSoft's get_sap_case_status tool.
    """
    service = WorkOrderFlowService(db)

    # Find work order by CRM reference ID
    work_orders, _ = await service.list_work_orders(limit=100)

    for wo in work_orders:
        if wo.crm_reference_id == case_id:
            # Determine FI approval status
            fi_status = None
            if wo.fi_approval_id:
                if wo.flow_status.value == "purchase_approved":
                    fi_status = "approved"
                elif wo.flow_status.value == "purchase_rejected":
                    fi_status = "rejected"
                else:
                    fi_status = "pending"

            return WorkOrderStatusResponse(
                sap_work_order_id=wo.work_order_id,
                salesforce_case_id=case_id,
                flow_status=wo.flow_status.value,
                materials_available=wo.materials_check_summary.get("all_available") if wo.materials_check_summary else None,
                fi_approval_status=fi_status,
                last_updated=wo.updated_at.isoformat() if wo.updated_at else wo.created_at.isoformat(),
            )

    raise HTTPException(status_code=404, detail=f"No work order found for Case ID: {case_id}")


@router.post("/webhook/case-created")
async def webhook_case_created(
    case: SalesforceCase,
    x_salesforce_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Direct webhook for Salesforce Case creation.

    Can be configured as Salesforce Outbound Message or Platform Event listener.
    """
    # Create sync request and process
    sync_request = SyncRequest(
        operation="CREATE",
        case=case,
        sync_timestamp=datetime.utcnow(),
    )

    return await sync_salesforce_case(sync_request, db=db)


@router.post("/webhook/case-updated")
async def webhook_case_updated(
    case: SalesforceCase,
    x_salesforce_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Direct webhook for Salesforce Case update.
    """
    sync_request = SyncRequest(
        operation="UPDATE",
        case=case,
        sync_timestamp=datetime.utcnow(),
    )

    return await sync_salesforce_case(sync_request, db=db)


@router.get("/health")
async def crm_integration_health():
    """Health check for CRM integration endpoint"""
    return {
        "status": "healthy",
        "service": "crm-integration",
        "supported_operations": ["CREATE", "UPDATE", "DELETE"],
        "supported_sources": ["Salesforce", "MuleSoft"],
    }
