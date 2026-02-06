"""
MuleSoft Integration Client for SAP Connectivity
Handles case synchronization between CRM and SAP via MuleSoft
"""
import httpx
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from ..db_models import Case, Account, Contact, User

logger = logging.getLogger(__name__)


class MuleSoftConfig(BaseModel):
    """MuleSoft configuration settings"""
    base_url: str = "https://your-mulesoft-instance.cloudhub.io"
    client_id: str = "your-client-id"
    client_secret: str = "your-client-secret"
    timeout: int = 30
    retry_attempts: int = 3


class SAPCasePayload(BaseModel):
    """SAP Case payload structure"""
    case_number: str
    subject: str
    description: Optional[str] = None
    priority: str
    status: str
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    created_date: str
    updated_date: Optional[str] = None
    owner_name: Optional[str] = None
    category: str = "TECHNICAL"
    urgency: str = "MEDIUM"
    impact: str = "MEDIUM"
    sla_due_date: Optional[str] = None
    business_unit: str = "UKPN"
    region: Optional[str] = None
    external_system: str = "SALESFORCE_CRM"
    correlation_id: Optional[str] = None


class MuleSoftResponse(BaseModel):
    """MuleSoft API response structure"""
    success: bool
    message: str
    sap_case_id: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: str
    errors: Optional[List[str]] = None


class MuleSoftClient:
    """MuleSoft integration client for SAP connectivity"""
    
    def __init__(self, config: MuleSoftConfig):
        self.config = config
        self.access_token = None
        self.token_expires_at = None
    
    async def authenticate(self) -> bool:
        """Authenticate with MuleSoft using OAuth2"""
        try:
            auth_url = f"{self.config.base_url}/api/auth/token"
            auth_payload = {
                "grant_type": "client_credentials",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "scope": "sap:cases:write sap:cases:read"
            }
            
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    auth_url,
                    data=auth_payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.utcnow().timestamp() + expires_in
                    logger.info("Successfully authenticated with MuleSoft")
                    return True
                else:
                    logger.error(f"MuleSoft authentication failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"MuleSoft authentication error: {str(e)}")
            return False
    
    async def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid access token"""
        if not self.access_token or (
            self.token_expires_at and 
            datetime.utcnow().timestamp() >= self.token_expires_at - 300  # Refresh 5 minutes early
        ):
            return await self.authenticate()
        return True
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Source-System": "SALESFORCE_CRM",
            "X-Correlation-ID": f"CRM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        }
    
    def _map_priority_to_sap(self, crm_priority: str) -> Dict[str, str]:
        """Map CRM priority to SAP urgency and impact"""
        priority_mapping = {
            "Critical": {"urgency": "HIGH", "impact": "HIGH"},
            "High": {"urgency": "HIGH", "impact": "MEDIUM"},
            "Medium": {"urgency": "MEDIUM", "impact": "MEDIUM"},
            "Low": {"urgency": "LOW", "impact": "LOW"}
        }
        return priority_mapping.get(crm_priority, {"urgency": "MEDIUM", "impact": "MEDIUM"})
    
    def _determine_region(self, account_name: str) -> str:
        """Determine region based on account name"""
        if "London" in account_name:
            return "LONDON"
        elif "Eastern" in account_name:
            return "EASTERN"
        elif "South Eastern" in account_name:
            return "SOUTH_EASTERN"
        else:
            return "GENERAL"
    
    async def create_case_in_sap(
        self, 
        case: Case, 
        account: Optional[Account] = None,
        contact: Optional[Contact] = None,
        owner: Optional[User] = None
    ) -> MuleSoftResponse:
        """Create a new case in SAP via MuleSoft"""
        
        if not await self._ensure_authenticated():
            return MuleSoftResponse(
                success=False,
                message="Authentication failed",
                timestamp=datetime.utcnow().isoformat()
            )
        
        try:
            # Map CRM priority to SAP urgency/impact
            sap_priority = self._map_priority_to_sap(case.priority)
            
            # Build SAP case payload
            sap_payload = SAPCasePayload(
                case_number=case.case_number,
                subject=case.subject,
                description=case.description,
                priority=case.priority,
                status=case.status,
                customer_id=str(account.id) if account else None,
                customer_name=account.name if account else None,
                contact_email=contact.email if contact else None,
                contact_phone=contact.phone if contact else None,
                created_date=case.created_at.isoformat(),
                updated_date=case.updated_at.isoformat() if case.updated_at else None,
                owner_name=owner.full_name if owner else None,
                urgency=sap_priority["urgency"],
                impact=sap_priority["impact"],
                sla_due_date=case.sla_due_date.isoformat() if case.sla_due_date else None,
                region=self._determine_region(account.name) if account else None,
                correlation_id=f"CRM-CASE-{case.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            )
            
            # Send to MuleSoft
            create_url = f"{self.config.base_url}/api/sap/cases"
            
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    create_url,
                    json=sap_payload.dict(),
                    headers=self._get_headers()
                )
                
                if response.status_code in [200, 201]:
                    response_data = response.json()
                    logger.info(f"Successfully created case {case.case_number} in SAP via MuleSoft")
                    
                    return MuleSoftResponse(
                        success=True,
                        message="Case successfully created in SAP",
                        sap_case_id=response_data.get("sap_case_id"),
                        correlation_id=sap_payload.correlation_id,
                        timestamp=datetime.utcnow().isoformat()
                    )
                else:
                    error_msg = f"MuleSoft API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    return MuleSoftResponse(
                        success=False,
                        message=error_msg,
                        correlation_id=sap_payload.correlation_id,
                        timestamp=datetime.utcnow().isoformat(),
                        errors=[error_msg]
                    )
                    
        except httpx.TimeoutException:
            error_msg = "MuleSoft API timeout"
            logger.error(error_msg)
            return MuleSoftResponse(
                success=False,
                message=error_msg,
                timestamp=datetime.utcnow().isoformat(),
                errors=[error_msg]
            )
            
        except Exception as e:
            error_msg = f"Unexpected error creating case in SAP: {str(e)}"
            logger.error(error_msg)
            return MuleSoftResponse(
                success=False,
                message=error_msg,
                timestamp=datetime.utcnow().isoformat(),
                errors=[error_msg]
            )
    
    async def update_case_in_sap(
        self,
        case: Case,
        sap_case_id: str,
        account: Optional[Account] = None,
        contact: Optional[Contact] = None,
        owner: Optional[User] = None
    ) -> MuleSoftResponse:
        """Update an existing case in SAP via MuleSoft"""
        
        if not await self._ensure_authenticated():
            return MuleSoftResponse(
                success=False,
                message="Authentication failed",
                timestamp=datetime.utcnow().isoformat()
            )
        
        try:
            # Map CRM priority to SAP urgency/impact
            sap_priority = self._map_priority_to_sap(case.priority)
            
            # Build update payload
            update_payload = {
                "sap_case_id": sap_case_id,
                "case_number": case.case_number,
                "subject": case.subject,
                "description": case.description,
                "priority": case.priority,
                "status": case.status,
                "urgency": sap_priority["urgency"],
                "impact": sap_priority["impact"],
                "updated_date": case.updated_at.isoformat() if case.updated_at else datetime.utcnow().isoformat(),
                "owner_name": owner.full_name if owner else None,
                "sla_due_date": case.sla_due_date.isoformat() if case.sla_due_date else None,
                "correlation_id": f"CRM-UPDATE-{case.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            }
            
            # Send update to MuleSoft
            update_url = f"{self.config.base_url}/api/sap/cases/{sap_case_id}"
            
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.put(
                    update_url,
                    json=update_payload,
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(f"Successfully updated case {case.case_number} in SAP via MuleSoft")
                    
                    return MuleSoftResponse(
                        success=True,
                        message="Case successfully updated in SAP",
                        sap_case_id=sap_case_id,
                        correlation_id=update_payload["correlation_id"],
                        timestamp=datetime.utcnow().isoformat()
                    )
                else:
                    error_msg = f"MuleSoft update error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    return MuleSoftResponse(
                        success=False,
                        message=error_msg,
                        correlation_id=update_payload["correlation_id"],
                        timestamp=datetime.utcnow().isoformat(),
                        errors=[error_msg]
                    )
                    
        except Exception as e:
            error_msg = f"Unexpected error updating case in SAP: {str(e)}"
            logger.error(error_msg)
            return MuleSoftResponse(
                success=False,
                message=error_msg,
                timestamp=datetime.utcnow().isoformat(),
                errors=[error_msg]
            )
    
    async def get_case_status_from_sap(self, sap_case_id: str) -> MuleSoftResponse:
        """Get case status from SAP via MuleSoft"""
        
        if not await self._ensure_authenticated():
            return MuleSoftResponse(
                success=False,
                message="Authentication failed",
                timestamp=datetime.utcnow().isoformat()
            )
        
        try:
            status_url = f"{self.config.base_url}/api/sap/cases/{sap_case_id}/status"
            
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    status_url,
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(f"Successfully retrieved case status from SAP: {sap_case_id}")
                    
                    return MuleSoftResponse(
                        success=True,
                        message="Case status retrieved successfully",
                        sap_case_id=sap_case_id,
                        timestamp=datetime.utcnow().isoformat()
                    )
                else:
                    error_msg = f"MuleSoft status query error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    return MuleSoftResponse(
                        success=False,
                        message=error_msg,
                        timestamp=datetime.utcnow().isoformat(),
                        errors=[error_msg]
                    )
                    
        except Exception as e:
            error_msg = f"Unexpected error querying case status: {str(e)}"
            logger.error(error_msg)
            return MuleSoftResponse(
                success=False,
                message=error_msg,
                timestamp=datetime.utcnow().isoformat(),
                errors=[error_msg]
            )


# Global MuleSoft client instance
mulesoft_client = None

def get_mulesoft_client() -> MuleSoftClient:
    """Get or create MuleSoft client instance"""
    global mulesoft_client
    if mulesoft_client is None:
        config = MuleSoftConfig()  # Load from environment variables in production
        mulesoft_client = MuleSoftClient(config)
    return mulesoft_client