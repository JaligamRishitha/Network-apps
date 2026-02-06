"""
SAP Integration Service
Handles case synchronization business logic between CRM and SAP
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..db_models import Case, Account, Contact, User, CRMEventMetadata, CRMEventStatus
from .mulesoft_client import get_mulesoft_client, MuleSoftResponse

logger = logging.getLogger(__name__)


class SAPIntegrationService:
    """Service for managing SAP integrations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.mulesoft_client = get_mulesoft_client()
    
    async def sync_case_to_sap(
        self, 
        case_id: int, 
        operation: str = "CREATE"
    ) -> Dict[str, Any]:
        """
        Synchronize a case to SAP via MuleSoft
        
        Args:
            case_id: CRM case ID
            operation: CREATE, UPDATE, or DELETE
            
        Returns:
            Integration result with success status and details
        """
        try:
            # Get case with related data
            case = self.db.query(Case).filter(Case.id == case_id).first()
            if not case:
                return {
                    "success": False,
                    "message": f"Case {case_id} not found",
                    "case_id": case_id
                }
            
            # Get related account, contact, and owner
            account = None
            if case.account_id:
                account = self.db.query(Account).filter(Account.id == case.account_id).first()
            
            contact = None
            if case.contact_id:
                contact = self.db.query(Contact).filter(Contact.id == case.contact_id).first()
            
            owner = None
            if case.owner_id:
                owner = self.db.query(User).filter(User.id == case.owner_id).first()
            
            # Perform the integration based on operation
            if operation == "CREATE":
                result = await self._create_case_in_sap(case, account, contact, owner)
            elif operation == "UPDATE":
                result = await self._update_case_in_sap(case, account, contact, owner)
            else:
                return {
                    "success": False,
                    "message": f"Unsupported operation: {operation}",
                    "case_id": case_id
                }
            
            # Log the integration attempt
            await self._log_integration_event(case, operation, result)
            
            return {
                "success": result.success,
                "message": result.message,
                "case_id": case_id,
                "case_number": case.case_number,
                "sap_case_id": result.sap_case_id,
                "correlation_id": result.correlation_id,
                "timestamp": result.timestamp,
                "errors": result.errors
            }
            
        except Exception as e:
            error_msg = f"Error syncing case {case_id} to SAP: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "case_id": case_id
            }
    
    async def _create_case_in_sap(
        self,
        case: Case,
        account: Optional[Account],
        contact: Optional[Contact],
        owner: Optional[User]
    ) -> MuleSoftResponse:
        """Create case in SAP via MuleSoft"""
        return await self.mulesoft_client.create_case_in_sap(case, account, contact, owner)
    
    async def _update_case_in_sap(
        self,
        case: Case,
        account: Optional[Account],
        contact: Optional[Contact],
        owner: Optional[User]
    ) -> MuleSoftResponse:
        """Update case in SAP via MuleSoft"""
        # In a real implementation, you'd store the SAP case ID in your database
        # For now, we'll simulate getting it from a custom field or separate table
        sap_case_id = f"SAP-{case.case_number}"  # This should come from your database
        
        return await self.mulesoft_client.update_case_in_sap(
            case, sap_case_id, account, contact, owner
        )
    
    async def _log_integration_event(
        self,
        case: Case,
        operation: str,
        result: MuleSoftResponse
    ):
        """Log integration event for audit trail"""
        try:
            # Create platform event for the integration
            event_metadata = CRMEventMetadata(
                event_id=result.correlation_id or f"SAP-INT-{case.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                event_type=f"SAP_CASE_{operation}",
                event_source="CRM_INTEGRATION",
                event_timestamp=datetime.utcnow(),
                correlation_id=result.correlation_id,
                severity="HIGH" if not result.success else "MEDIUM",
                target_system="SAP_ISU",
                operation=f"{operation}_CASE_VIA_MULESOFT",
                integration_status="COMPLETED" if result.success else "FAILED",
                raw_payload={
                    "case_id": case.id,
                    "case_number": case.case_number,
                    "operation": operation,
                    "sap_case_id": result.sap_case_id,
                    "success": result.success,
                    "message": result.message,
                    "errors": result.errors
                }
            )
            self.db.add(event_metadata)
            
            # Create event status
            event_status = CRMEventStatus(
                event_id=event_metadata.event_id,
                current_status="PROCESSED" if result.success else "FAILED",
                validation_passed=True,
                normalization_completed=True,
                persistence_completed=True,
                error_count=1 if not result.success else 0,
                last_error_message=result.message if not result.success else None,
                completed_at=datetime.utcnow()
            )
            self.db.add(event_status)
            
            self.db.commit()
            logger.info(f"Logged integration event for case {case.case_number}")
            
        except Exception as e:
            logger.error(f"Error logging integration event: {str(e)}")
            self.db.rollback()
    
    async def sync_multiple_cases_to_sap(
        self, 
        case_ids: list[int], 
        operation: str = "CREATE"
    ) -> Dict[str, Any]:
        """
        Synchronize multiple cases to SAP
        
        Args:
            case_ids: List of CRM case IDs
            operation: CREATE, UPDATE, or DELETE
            
        Returns:
            Batch integration results
        """
        results = []
        successful = 0
        failed = 0
        
        for case_id in case_ids:
            result = await self.sync_case_to_sap(case_id, operation)
            results.append(result)
            
            if result["success"]:
                successful += 1
            else:
                failed += 1
        
        return {
            "total_cases": len(case_ids),
            "successful": successful,
            "failed": failed,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_sap_case_status(self, sap_case_id: str) -> Dict[str, Any]:
        """Get case status from SAP"""
        try:
            result = await self.mulesoft_client.get_case_status_from_sap(sap_case_id)
            
            return {
                "success": result.success,
                "message": result.message,
                "sap_case_id": sap_case_id,
                "timestamp": result.timestamp,
                "errors": result.errors
            }
            
        except Exception as e:
            error_msg = f"Error getting SAP case status: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "sap_case_id": sap_case_id
            }
    
    def get_integration_history(self, case_id: int) -> list[Dict[str, Any]]:
        """Get integration history for a case"""
        try:
            # Query platform events related to this case
            events = self.db.query(CRMEventMetadata).filter(
                CRMEventMetadata.raw_payload.contains(f'"case_id": {case_id}'),
                CRMEventMetadata.target_system == "SAP_ISU"
            ).order_by(CRMEventMetadata.created_at.desc()).all()
            
            history = []
            for event in events:
                status = self.db.query(CRMEventStatus).filter(
                    CRMEventStatus.event_id == event.event_id
                ).first()
                
                history.append({
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "operation": event.operation,
                    "status": status.current_status if status else "UNKNOWN",
                    "success": status.error_count == 0 if status else False,
                    "timestamp": event.created_at.isoformat(),
                    "correlation_id": event.correlation_id,
                    "message": status.last_error_message if status and status.error_count > 0 else "Success"
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting integration history for case {case_id}: {str(e)}")
            return []


def get_sap_integration_service(db: Session) -> SAPIntegrationService:
    """Get SAP integration service instance"""
    return SAPIntegrationService(db)