"""
Account approval integration with MuleSoft MCP.

Salesforce only sends the request to MuleSoft and sets status to PENDING.
The user manually validates and deploys from MuleSoft, which calls back
to update the status.

Integration statuses (MuleSoft only):
  PENDING   - Request sent to MuleSoft
  VALIDATED - User validated the request in MuleSoft
  COMPLETED - User deployed the request in MuleSoft
  FAILED    - An error occurred
"""
from __future__ import annotations

import os
import uuid
import logging
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from .. import crud
from ..db_models import AccountCreationRequest, User

logger = logging.getLogger(__name__)

# MuleSoft MCP API Configuration
MULESOFT_API_URL = os.getenv("MULESOFT_BASE_URL", "http://mulesoft-backend:4797")
MULESOFT_TIMEOUT_SECONDS = float(os.getenv("MULESOFT_TIMEOUT_SECONDS", "30"))

# Salesforce callback URL for MuleSoft to call back
SALESFORCE_CALLBACK_URL = os.getenv("SALESFORCE_CALLBACK_URL", "http://207.180.217.117:4799")

# ServiceNow API Configuration
SERVICENOW_API_URL = os.getenv("SERVICENOW_BASE_URL", "http://servicenow-backend:4780")


def _new_external_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


async def _get_salesforce_connector_id(client: httpx.AsyncClient, token: str) -> Optional[int]:
    """Look up the Salesforce connector ID from MuleSoft."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"{MULESOFT_API_URL}/api/connectors/", headers=headers)
        if response.is_success:
            connectors = response.json()
            if isinstance(connectors, dict):
                connectors = connectors.get("connectors", connectors.get("items", []))
            for c in connectors:
                ctype = (c.get("connector_type") or c.get("type") or "").lower()
                if ctype == "salesforce":
                    return c.get("id")
    except Exception as e:
        logger.error(f"Failed to look up Salesforce connector: {e}")
    return None


async def _get_mulesoft_auth_token(client: httpx.AsyncClient) -> Optional[str]:
    """Authenticate with MuleSoft and get access token."""
    try:
        response = await client.post(
            f"{MULESOFT_API_URL}/api/auth/login",
            json={"email": "admin@mulesoft.io", "password": "admin123"}
        )
        if response.is_success:
            data = response.json()
            return data.get("access_token") or data.get("token")
    except Exception as e:
        logger.error(f"Failed to authenticate with MuleSoft: {e}")
    return None


async def _create_servicenow_ticket(request: AccountCreationRequest) -> Optional[str]:
    """Create a ServiceNow ticket for the account creation request.
    Returns the ticket ID on success, None on failure.
    This is supplementary - failures are logged but don't block the request."""
    try:
        async with httpx.AsyncClient(verify=False, timeout=15) as client:
            # Authenticate with ServiceNow
            auth_response = await client.post(
                f"{SERVICENOW_API_URL}/token",
                data={"username": "admin@company.com", "password": "admin123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if auth_response.status_code != 200:
                logger.warning(f"ServiceNow auth failed: HTTP {auth_response.status_code}")
                return None

            sn_token = auth_response.json().get("access_token", "")

            # Create ticket
            ticket_payload = {
                "title": f"Account Creation Approval - {request.name}",
                "description": (
                    f"New account creation request from Salesforce.\n\n"
                    f"Account Name: {request.name}\n"
                    f"Correlation ID: {request.correlation_id}\n"
                    f"Salesforce Request ID: {request.id}\n"
                    f"Requested By: User ID {request.requested_by_id}\n"
                ),
                "ticket_type": "service_request",
                "priority": "medium",
                "category": "Account Management",
                "subcategory": "New Account Creation",
                "urgency": "medium",
            }
            ticket_response = await client.post(
                f"{SERVICENOW_API_URL}/tickets/",
                headers={
                    "Authorization": f"Bearer {sn_token}",
                    "Content-Type": "application/json",
                },
                json=ticket_payload,
            )
            if ticket_response.status_code in (200, 201):
                ticket_data = ticket_response.json()
                ticket_id = ticket_data.get("ticket_number") or f"TKT{ticket_data.get('id')}"
                logger.info(f"ServiceNow ticket {ticket_id} created for request {request.id}")
                return ticket_id
            else:
                logger.warning(f"ServiceNow ticket creation failed: HTTP {ticket_response.status_code}")
                return None
    except Exception as e:
        logger.warning(f"Failed to create ServiceNow ticket for request {request.id}: {e}")
        return None


async def _set_pending(
    db: Session,
    request: AccountCreationRequest,
) -> AccountCreationRequest:
    """
    Set the account creation request to PENDING.
    Also creates a ServiceNow ticket simultaneously.
    The user will manually validate and deploy from MuleSoft.
    MuleSoft calls back to Salesforce to update status:
      validate-single-request  -> VALIDATED
      deploy-to-salesforce     -> COMPLETED
    """
    logger.info(f"Request {request.id} created with status PENDING")

    # Create ServiceNow ticket (supplementary - don't block on failure)
    sn_ticket_id = await _create_servicenow_ticket(request)

    update_kwargs = {"integration_status": "PENDING"}
    if sn_ticket_id:
        update_kwargs["servicenow_ticket_id"] = sn_ticket_id

    return crud.update_account_request_integration(
        db, request, **update_kwargs,
    )


async def record_manager_audit(
    db: Session,
    request: AccountCreationRequest,
    requested_by: User,
) -> AccountCreationRequest:
    """Manager/admin flow: set request to PENDING for MuleSoft processing."""
    return await _set_pending(db, request)


async def record_user_submission(
    db: Session,
    request: AccountCreationRequest,
    requested_by: User,
) -> AccountCreationRequest:
    """User flow: set request to PENDING for MuleSoft processing."""
    return await _set_pending(db, request)
