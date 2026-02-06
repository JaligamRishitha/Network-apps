"""
Password Reset Orchestration Router - Orchestrates password reset flow across SAP and ServiceNow.

Flow:
1. User initiates password reset request (from Salesforce/ServiceNow/Self-service)
2. MuleSoft validates user identity against SAP User Management
3. MuleSoft invokes SAP password change API
4. Confirmation sent back to requesting system
5. ServiceNow ticket auto-created for audit/compliance
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import httpx
import uuid
import os
import secrets
import string

from app.database import get_db
from app.models import IntegrationLog

router = APIRouter(prefix="/password-reset", tags=["Password Reset"])

# Backend URLs - Use Docker container names for internal communication
SAP_URL = os.getenv("SAP_URL", "http://sap-backend:4798")
SERVICENOW_URL = os.getenv("SERVICENOW_URL", "http://servicenow-backend:4780")
SALESFORCE_URL = os.getenv("SALESFORCE_URL", "http://salesforce-backend:8000")


class ResetRequestSource(str, Enum):
    """Source system for password reset request"""
    SALESFORCE = "salesforce"
    SERVICENOW = "servicenow"
    SELF_SERVICE = "self_service"
    SAP = "sap"


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    username: str = Field(..., description="SAP username to reset password for")
    email: Optional[str] = Field(None, description="User's email for verification")
    source_system: ResetRequestSource = Field(default=ResetRequestSource.SELF_SERVICE)
    requester_id: Optional[str] = Field(None, description="ID of person requesting reset")
    requester_name: Optional[str] = Field(None, description="Name of person requesting reset")
    reason: Optional[str] = Field(None, description="Reason for password reset")
    generate_temp_password: bool = Field(default=True, description="Generate temporary password")
    new_password: Optional[str] = Field(None, description="New password (if not generating)")
    callback_url: Optional[str] = Field(None, description="URL to call with result")


class PasswordResetResponse(BaseModel):
    """Password reset response schema"""
    request_id: str
    status: str
    username: str
    message: str
    temp_password: Optional[str] = None  # Only returned if generate_temp_password=True
    ticket_number: Optional[str] = None
    timestamp: str


class UserValidationResult(BaseModel):
    """Result of user validation against SAP"""
    valid: bool
    username: str
    user_exists: bool
    roles: Optional[list] = None
    error: Optional[str] = None


# In-memory request tracking
reset_requests: Dict[str, Dict[str, Any]] = {}


def generate_temp_password(length: int = 12) -> str:
    """Generate a secure temporary password."""
    # Ensure at least one of each required character type
    lowercase = secrets.choice(string.ascii_lowercase)
    uppercase = secrets.choice(string.ascii_uppercase)
    digit = secrets.choice(string.digits)
    special = secrets.choice("!@#$%^&*")

    # Fill the rest randomly
    remaining_length = length - 4
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    remaining = ''.join(secrets.choice(all_chars) for _ in range(remaining_length))

    # Combine and shuffle
    password_list = list(lowercase + uppercase + digit + special + remaining)
    secrets.SystemRandom().shuffle(password_list)

    return ''.join(password_list)


def validate_user_in_sap_sync(username: str) -> UserValidationResult:
    """
    Validate user exists in SAP User Management Engine (sync version).

    Step 2: MuleSoft validates user identity against SAP
    """
    try:
        with httpx.Client(timeout=30) as client:
            # First, authenticate with SAP to get admin token
            auth_response = client.post(
                f"{SAP_URL}/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"}
            )

            if auth_response.status_code != 200:
                return UserValidationResult(
                    valid=False,
                    username=username,
                    user_exists=False,
                    error="Failed to authenticate with SAP"
                )

            token = auth_response.json().get("access_token", "")
            headers = {"Authorization": f"Bearer {token}"}

            # Get user details from SAP
            user_response = client.get(
                f"{SAP_URL}/api/v1/users/{username}",
                headers=headers
            )

            if user_response.status_code == 200:
                user_data = user_response.json()
                return UserValidationResult(
                    valid=True,
                    username=username,
                    user_exists=True,
                    roles=user_data.get("roles", [])
                )
            elif user_response.status_code == 404:
                return UserValidationResult(
                    valid=False,
                    username=username,
                    user_exists=False,
                    error=f"User '{username}' not found in SAP"
                )
            else:
                return UserValidationResult(
                    valid=False,
                    username=username,
                    user_exists=False,
                    error=f"SAP returned status {user_response.status_code}"
                )

    except Exception as e:
        return UserValidationResult(
            valid=False,
            username=username,
            user_exists=False,
            error=str(e)
        )


async def validate_user_in_sap(username: str) -> UserValidationResult:
    """Async wrapper for validate_user_in_sap_sync."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, validate_user_in_sap_sync, username)


def change_password_in_sap_sync(username: str, new_password: str) -> Dict[str, Any]:
    """
    Invoke SAP_USER_CHANGE to reset password in SAP system (sync version).

    Step 3: MuleSoft invokes SAP password change API
    """
    try:
        with httpx.Client(timeout=30) as client:
            # Authenticate with SAP
            auth_response = client.post(
                f"{SAP_URL}/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"}
            )

            if auth_response.status_code != 200:
                return {
                    "success": False,
                    "error": "Failed to authenticate with SAP"
                }

            token = auth_response.json().get("access_token", "")
            headers = {"Authorization": f"Bearer {token}"}

            # Call SAP password change API (SAP_USER_CHANGE equivalent)
            change_response = client.patch(
                f"{SAP_URL}/api/v1/users/{username}/password",
                headers=headers,
                json={
                    "username": username,
                    "new_password": new_password
                }
            )

            if change_response.status_code == 200:
                return {
                    "success": True,
                    "message": change_response.json().get("message", "Password changed successfully")
                }
            else:
                return {
                    "success": False,
                    "error": f"SAP returned status {change_response.status_code}: {change_response.text}"
                }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def change_password_in_sap(username: str, new_password: str) -> Dict[str, Any]:
    """Async wrapper for change_password_in_sap_sync."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        change_password_in_sap_sync,
        username,
        new_password
    )


def create_audit_ticket_sync(
    request_id: str,
    username: str,
    source_system: str,
    requester_name: Optional[str],
    reason: Optional[str],
    success: bool
) -> Optional[str]:
    """
    Create ServiceNow ticket for audit and compliance tracking (sync version).

    Step 5: ServiceNow ticket automatically created
    """
    try:
        # Use sync httpx client for better container-to-container communication
        with httpx.Client(timeout=30) as client:
            # Create ticket via ServiceNow auto-create endpoint
            ticket_payload = {
                "event_type": "password_reset",
                "source_system": source_system,
                "title": f"Password Reset: {username}",
                "description": f"""Password reset request processed.

Request ID: {request_id}
Username: {username}
Source System: {source_system}
Requested By: {requester_name or 'Self-service'}
Reason: {reason or 'User requested password reset'}
Status: {'Completed Successfully' if success else 'Failed'}
Timestamp: {datetime.utcnow().isoformat()}Z

This ticket is auto-generated for audit and compliance purposes.""",
                "category": "User Account",
                "subcategory": "Password Reset",
                "priority": "medium",
                "assignment_group": "IT Service Desk",
                "ticket_type": "incident",
                "sla_hours": 4,
                "affected_user": username,
                "requires_approval": False,
                "auto_assign": True,
                "event_id": request_id,
                "metadata": {
                    "password_reset": True,
                    "source_system": source_system,
                    "success": success
                }
            }

            response = client.post(
                f"{SERVICENOW_URL}/api/tickets/auto-create",
                json=ticket_payload
            )

            if response.status_code in [200, 201]:
                result = response.json()
                return result.get("ticket_number")
            else:
                print(f"Failed to create audit ticket: {response.status_code}")
                return None

    except Exception as e:
        print(f"Error creating audit ticket: {e}")
        return None


async def create_audit_ticket(
    request_id: str,
    username: str,
    source_system: str,
    requester_name: Optional[str],
    reason: Optional[str],
    success: bool
) -> Optional[str]:
    """
    Create ServiceNow ticket for audit and compliance tracking.
    Wraps sync call for async compatibility.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        create_audit_ticket_sync,
        request_id,
        username,
        source_system,
        requester_name,
        reason,
        success
    )


async def send_callback(callback_url: str, payload: Dict[str, Any]) -> bool:
    """
    Send callback to requesting system with result.

    Step 4: Confirmation sent back through integration layer
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                callback_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            return response.status_code in [200, 201, 202]
    except Exception as e:
        print(f"Callback failed: {e}")
        return False


async def notify_salesforce(username: str, success: bool, message: str) -> bool:
    """Notify Salesforce about password reset result."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{SALESFORCE_URL}/api/webhooks/password-reset-result",
                json={
                    "username": username,
                    "success": success,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
            return response.status_code in [200, 201, 202]
    except:
        return False


@router.post("/request", response_model=PasswordResetResponse)
async def initiate_password_reset(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Initiate password reset orchestration.

    This endpoint orchestrates the complete password reset flow:
    1. Validates user exists in SAP
    2. Changes password in SAP (SAP_USER_CHANGE)
    3. Creates audit ticket in ServiceNow
    4. Sends confirmation to requesting system

    Can be called from:
    - Salesforce Service Cloud
    - ServiceNow self-service portal
    - Direct API call
    """
    request_id = f"PWR-{uuid.uuid4().hex[:12].upper()}"
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Log the request
    log = IntegrationLog(
        integration_id=1,
        level="INFO",
        message=f"Password reset initiated: {request_id} for user {request.username} from {request.source_system}"
    )
    db.add(log)
    db.commit()

    # Store request for tracking
    reset_requests[request_id] = {
        "request_id": request_id,
        "username": request.username,
        "source_system": request.source_system,
        "status": "processing",
        "created_at": timestamp,
        "updated_at": timestamp
    }

    # Step 2: Validate user in SAP
    validation_result = await validate_user_in_sap(request.username)

    if not validation_result.valid:
        # User validation failed
        reset_requests[request_id]["status"] = "failed"
        reset_requests[request_id]["error"] = validation_result.error

        # Still create audit ticket for failed attempt
        background_tasks.add_task(
            create_audit_ticket,
            request_id,
            request.username,
            request.source_system.value,
            request.requester_name,
            request.reason,
            False
        )

        raise HTTPException(
            status_code=400,
            detail={
                "request_id": request_id,
                "error": validation_result.error,
                "message": f"User validation failed: {validation_result.error}"
            }
        )

    # Step 3: Generate or use provided password
    if request.generate_temp_password:
        new_password = generate_temp_password()
    else:
        if not request.new_password:
            raise HTTPException(
                status_code=400,
                detail="new_password required when generate_temp_password is False"
            )
        new_password = request.new_password

    # Step 3: Change password in SAP (SAP_USER_CHANGE)
    change_result = await change_password_in_sap(request.username, new_password)

    if not change_result["success"]:
        reset_requests[request_id]["status"] = "failed"
        reset_requests[request_id]["error"] = change_result["error"]

        # Create audit ticket for failed attempt
        background_tasks.add_task(
            create_audit_ticket,
            request_id,
            request.username,
            request.source_system.value,
            request.requester_name,
            request.reason,
            False
        )

        raise HTTPException(
            status_code=500,
            detail={
                "request_id": request_id,
                "error": change_result["error"],
                "message": "Password change failed in SAP"
            }
        )

    # Step 5: Create audit ticket in ServiceNow (background)
    ticket_number = await create_audit_ticket(
        request_id=request_id,
        username=request.username,
        source_system=request.source_system.value,
        requester_name=request.requester_name,
        reason=request.reason,
        success=True
    )

    # Update request status
    reset_requests[request_id]["status"] = "completed"
    reset_requests[request_id]["ticket_number"] = ticket_number
    reset_requests[request_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"

    # Step 4: Send callback if provided
    if request.callback_url:
        callback_payload = {
            "request_id": request_id,
            "username": request.username,
            "status": "completed",
            "ticket_number": ticket_number,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        background_tasks.add_task(send_callback, request.callback_url, callback_payload)

    # Notify Salesforce if request came from there
    if request.source_system == ResetRequestSource.SALESFORCE:
        background_tasks.add_task(
            notify_salesforce,
            request.username,
            True,
            "Password reset completed successfully"
        )

    # Log success
    log = IntegrationLog(
        integration_id=1,
        level="INFO",
        message=f"Password reset completed: {request_id} for user {request.username}, ticket: {ticket_number}"
    )
    db.add(log)
    db.commit()

    return PasswordResetResponse(
        request_id=request_id,
        status="completed",
        username=request.username,
        message="Password reset successful. User must change password on next login.",
        temp_password=new_password if request.generate_temp_password else None,
        ticket_number=ticket_number,
        timestamp=timestamp
    )


@router.get("/request/{request_id}")
async def get_reset_request_status(request_id: str):
    """Get the status of a password reset request."""
    if request_id not in reset_requests:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")

    return reset_requests[request_id]


@router.get("/requests")
async def list_reset_requests(
    limit: int = 50,
    status: Optional[str] = None
):
    """List recent password reset requests."""
    requests = list(reset_requests.values())

    if status:
        requests = [r for r in requests if r.get("status") == status]

    # Sort by created_at descending
    requests.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {
        "requests": requests[:limit],
        "total": len(requests)
    }


@router.post("/validate-user")
async def validate_user(username: str):
    """
    Validate if a user exists in SAP before initiating password reset.

    Useful for pre-validation in UI.
    """
    result = await validate_user_in_sap(username)

    return {
        "username": username,
        "valid": result.valid,
        "exists": result.user_exists,
        "roles": result.roles,
        "error": result.error
    }


@router.get("/health")
async def password_reset_health():
    """Health check for password reset service."""
    # Check SAP connectivity
    sap_healthy = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{SAP_URL}/health")
            sap_healthy = response.status_code == 200
    except:
        pass

    # Check ServiceNow connectivity
    servicenow_healthy = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{SERVICENOW_URL}/health")
            servicenow_healthy = response.status_code == 200
    except:
        pass

    return {
        "status": "healthy" if (sap_healthy and servicenow_healthy) else "degraded",
        "service": "password-reset-orchestration",
        "dependencies": {
            "sap": "healthy" if sap_healthy else "unhealthy",
            "servicenow": "healthy" if servicenow_healthy else "unhealthy"
        },
        "pending_requests": len([r for r in reset_requests.values() if r.get("status") == "processing"]),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
