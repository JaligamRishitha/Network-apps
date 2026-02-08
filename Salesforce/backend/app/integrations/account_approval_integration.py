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


async def _set_pending(
    db: Session,
    request: AccountCreationRequest,
) -> AccountCreationRequest:
    """
    Set the account creation request to PENDING.
    The user will manually validate and deploy from MuleSoft.
    MuleSoft calls back to Salesforce to update status:
      validate-single-request  -> VALIDATED
      send-single-to-servicenow -> COMPLETED
    """
    logger.info(f"Request {request.id} created with status PENDING")
    return crud.update_account_request_integration(
        db, request, integration_status="PENDING",
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
