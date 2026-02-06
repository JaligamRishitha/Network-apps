"""
Account approval integration with MuleSoft MCP.

These functions handle the MuleSoft -> ServiceNow workflow for account
creation requests. Requests are sent to MuleSoft which creates ServiceNow
tickets for approval.
"""
from __future__ import annotations

import os
import uuid
import logging
from typing import Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from .. import crud
from ..db_models import AccountCreationRequest, User

logger = logging.getLogger(__name__)

# MuleSoft MCP API Configuration
MULESOFT_API_URL = os.getenv("MULESOFT_API_URL", "http://149.102.158.71:8091")
MULESOFT_TIMEOUT_SECONDS = float(os.getenv("MULESOFT_TIMEOUT_SECONDS", "30"))

# Salesforce callback URL for MuleSoft to call back after approval
SALESFORCE_CALLBACK_URL = os.getenv("SALESFORCE_CALLBACK_URL", "http://149.102.158.71:4799")


def _new_external_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _get_mulesoft_auth_token() -> Optional[str]:
    """Authenticate with MuleSoft and get access token."""
    try:
        with httpx.Client(timeout=MULESOFT_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{MULESOFT_API_URL}/api/auth/login",
                json={"email": "admin@example.com", "password": "admin123"}
            )
            if response.is_success:
                data = response.json()
                return data.get("access_token")
    except Exception as e:
        logger.error(f"Failed to authenticate with MuleSoft: {e}")
    return None


def _build_mulesoft_payload(request: AccountCreationRequest, requested_by: User) -> dict:
    """Build payload for MuleSoft validation request."""
    client_data = dict(request.requested_payload or {})
    client_data.setdefault("name", request.name)
    client_data.setdefault("billingAddress", client_data.get("billing_address"))

    return {
        "request_id": request.id,
        "account_name": request.name,
        "request_data": {
            "sourceSystem": "Salesforce",
            "requestType": "NEW_CLIENT",
            "requestedBy": (requested_by.role or "user").upper(),
            "requestedById": str(requested_by.id),
            "requestedByUsername": requested_by.username,
            "correlationId": request.correlation_id,
            "clientData": client_data,
            "callbackUrl": f"{SALESFORCE_CALLBACK_URL}/api/accounts/requests/{request.id}/mulesoft-callback",
        }
    }


def _validate_with_mulesoft(request: AccountCreationRequest, requested_by: User, token: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate the account request with MuleSoft."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "request_id": request.id,
            "account_name": request.name
        }

        with httpx.Client(timeout=MULESOFT_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{MULESOFT_API_URL}/api/cases/validate-single-request",
                params={"connector_id": 1},
                json=payload,
                headers=headers
            )

            if response.is_success:
                data = response.json()
                tx_id = data.get("mulesoft_transaction_id")
                logger.info(f"MuleSoft validation successful for request {request.id}: {data}")
                return True, tx_id, None
            else:
                error_msg = f"MuleSoft validation failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, None, error_msg

    except Exception as e:
        error_msg = f"Error validating with MuleSoft: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


def _send_to_servicenow_via_mulesoft(request: AccountCreationRequest, requested_by: User, token: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Send the account request to ServiceNow via MuleSoft for approval."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = _build_mulesoft_payload(request, requested_by)

        with httpx.Client(timeout=MULESOFT_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{MULESOFT_API_URL}/api/cases/send-single-to-servicenow",
                params={"connector_id": 1},
                json=payload,
                headers=headers
            )

            if response.is_success:
                data = response.json()
                ticket_number = data.get("ticket_number")
                logger.info(f"ServiceNow ticket created via MuleSoft for request {request.id}: {ticket_number}")
                return True, ticket_number, None
            else:
                error_msg = f"Failed to send to ServiceNow via MuleSoft: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, None, error_msg

    except Exception as e:
        error_msg = f"Error sending to ServiceNow via MuleSoft: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


def _send_request_to_mulesoft(request: AccountCreationRequest, requested_by: User) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Send account creation request to MuleSoft for validation and ServiceNow ticket creation.
    Returns: (success, mulesoft_transaction_id, servicenow_ticket_id, error_message)
    """
    # Get auth token from MuleSoft
    token = _get_mulesoft_auth_token()
    if not token:
        return False, None, None, "Failed to authenticate with MuleSoft"

    # Step 1: Validate with MuleSoft
    valid, tx_id, error = _validate_with_mulesoft(request, requested_by, token)
    if not valid:
        return False, tx_id, None, error

    # Step 2: Send to ServiceNow via MuleSoft
    success, ticket_id, error = _send_to_servicenow_via_mulesoft(request, requested_by, token)
    if not success:
        return False, tx_id, None, error

    return True, tx_id, ticket_id, None


def record_manager_audit(
    db: Session,
    request: AccountCreationRequest,
    requested_by: User,
) -> AccountCreationRequest:
    """
    Manager/admin flow:
    - Manager creates account request
    - Still requires MuleSoft validation and ServiceNow approval
    - Account is NOT created until approval is received
    """
    # Set initial pending status
    request = crud.update_account_request_integration(
        db,
        request,
        servicenow_status="PENDING_MULESOFT",
        integration_status="PENDING_MULESOFT",
    )

    # Send to MuleSoft for validation and ServiceNow ticket creation
    success, tx_id, ticket_id, error_message = _send_request_to_mulesoft(request, requested_by)

    if success:
        logger.info(f"Manager request {request.id} sent to MuleSoft successfully. Ticket: {ticket_id}")
        return crud.update_account_request_integration(
            db,
            request,
            mulesoft_transaction_id=tx_id,
            servicenow_ticket_id=ticket_id,
            servicenow_status="PENDING_APPROVAL",
            integration_status="PENDING_SERVICENOW_APPROVAL",
        )

    logger.error(f"Manager request {request.id} failed to send to MuleSoft: {error_message}")
    return crud.update_account_request_integration(
        db,
        request,
        mulesoft_transaction_id=tx_id or _new_external_id("MULE"),
        integration_status="MULESOFT_SEND_FAILED",
        error_message=error_message or "Failed to send to MuleSoft",
    )


def record_user_submission(
    db: Session,
    request: AccountCreationRequest,
    requested_by: User,
) -> AccountCreationRequest:
    """
    User flow:
    - Salesforce does not create the account yet
    - Request is sent to MuleSoft for validation
    - MuleSoft creates a ServiceNow ticket for approval
    - Account is created only after ServiceNow approval callback
    """
    # Set initial pending status
    request = crud.update_account_request_integration(
        db,
        request,
        servicenow_status="PENDING_MULESOFT",
        integration_status="PENDING_MULESOFT",
    )

    # Send to MuleSoft for validation and ServiceNow ticket creation
    success, tx_id, ticket_id, error_message = _send_request_to_mulesoft(request, requested_by)

    if success:
        logger.info(f"Request {request.id} sent to MuleSoft successfully. Transaction: {tx_id}, Ticket: {ticket_id}")
        return crud.update_account_request_integration(
            db,
            request,
            mulesoft_transaction_id=tx_id,
            servicenow_ticket_id=ticket_id,
            servicenow_status="PENDING_APPROVAL",
            integration_status="PENDING_SERVICENOW_APPROVAL",
        )

    logger.error(f"Request {request.id} failed to send to MuleSoft: {error_message}")
    return crud.update_account_request_integration(
        db,
        request,
        mulesoft_transaction_id=tx_id or _new_external_id("MULE"),
        integration_status="MULESOFT_SEND_FAILED",
        error_message=error_message or "Failed to send to MuleSoft",
    )


def record_approval_outcome(
    db: Session,
    request: AccountCreationRequest,
    *,
    approved: bool,
    error_message: Optional[str] = None,
) -> AccountCreationRequest:
    if approved:
        return crud.update_account_request_integration(
            db,
            request,
            servicenow_status="APPROVED",
            integration_status="APPROVED",
        )

    return crud.update_account_request_integration(
        db,
        request,
        servicenow_status="REJECTED",
        integration_status="REJECTED",
        error_message=error_message,
    )
