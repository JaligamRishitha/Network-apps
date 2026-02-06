from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from ..database import get_db
from ..auth import get_current_user
from ..db_models import User, AccountCreationRequest, SchedulingRequest, WorkOrder

router = APIRouter(prefix="/api/integration-tracking", tags=["integration-tracking"])


@router.get("/{tracking_id}")
async def get_integration_tracking(
    tracking_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search for integration tracking data by correlation_id or servicenow_ticket_id.
    Searches across account requests, scheduling requests, and work orders.
    """

    # Search in Account Creation Requests
    account_request = db.query(AccountCreationRequest).filter(
        or_(
            AccountCreationRequest.correlation_id == tracking_id,
            AccountCreationRequest.servicenow_ticket_id == tracking_id,
        )
    ).first()

    if account_request:
        return {
            "type": "account_creation",
            "id": account_request.id,
            "name": account_request.name,
            "status": account_request.status,
            "integration_status": account_request.integration_status,
            "correlation_id": account_request.correlation_id,
            "servicenow_ticket_id": account_request.servicenow_ticket_id,
            "servicenow_status": account_request.servicenow_status,
            "mulesoft_transaction_id": account_request.mulesoft_transaction_id,
            "error_message": account_request.error_message,
            "message": f"Account creation request for {account_request.name}",
            "sap_customer_id": getattr(account_request, 'sap_customer_id', None),
            "created_account_id": account_request.created_account_id,
            "created_at": account_request.created_at.isoformat() if account_request.created_at else None,
            "updated_at": account_request.updated_at.isoformat() if account_request.updated_at else None,
        }

    # Search in Scheduling Requests (Service Appointments)
    scheduling_request = db.query(SchedulingRequest).filter(
        SchedulingRequest.correlation_id == tracking_id
    ).first()

    if scheduling_request:
        return {
            "type": "scheduling",
            "id": scheduling_request.id,
            "subject": getattr(scheduling_request, 'appointment_number', f"Appointment #{scheduling_request.id}"),
            "status": scheduling_request.status,
            "integration_status": scheduling_request.integration_status,
            "correlation_id": scheduling_request.correlation_id,
            "servicenow_ticket_id": None,
            "servicenow_status": None,
            "mulesoft_transaction_id": scheduling_request.mulesoft_transaction_id,
            "error_message": scheduling_request.error_message,
            "message": f"Scheduling request #{scheduling_request.id}",
            "appointment_id": scheduling_request.appointment_id,
            "assigned_technician_id": getattr(scheduling_request, 'assigned_technician_id', None),
            "technician_name": getattr(scheduling_request, 'technician_name', None),
            "parts_available": getattr(scheduling_request, 'parts_available', None),
            "created_at": scheduling_request.created_at.isoformat() if scheduling_request.created_at else None,
            "updated_at": scheduling_request.updated_at.isoformat() if scheduling_request.updated_at else None,
        }

    # Search in Work Orders
    work_order = db.query(WorkOrder).filter(
        WorkOrder.correlation_id == tracking_id
    ).first()

    if work_order:
        return {
            "type": "work_order",
            "id": work_order.id,
            "subject": work_order.subject,
            "status": work_order.status,
            "integration_status": work_order.integration_status,
            "correlation_id": work_order.correlation_id,
            "servicenow_ticket_id": None,
            "servicenow_status": None,
            "mulesoft_transaction_id": work_order.mulesoft_transaction_id,
            "error_message": getattr(work_order, 'error_message', None),
            "message": f"Work order: {work_order.subject}",
            "sap_order_id": getattr(work_order, 'sap_order_id', None),
            "sap_notification_id": getattr(work_order, 'sap_notification_id', None),
            "entitlement_verified": getattr(work_order, 'entitlement_verified', None),
            "created_at": work_order.created_at.isoformat() if work_order.created_at else None,
            "updated_at": work_order.updated_at.isoformat() if work_order.updated_at else None,
        }

    # Not found in any table
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Correlation ID or Ticket not found"
    )
