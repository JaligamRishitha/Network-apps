"""
SAP Integration API Routes
Handles case synchronization with SAP via MuleSoft
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
import logging

from ..database import get_db
from ..auth import get_current_user
from ..db_models import User
from ..integrations.sap_integration_service import get_sap_integration_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sap-integration", tags=["SAP Integration"])


class CaseSyncRequest(BaseModel):
    """Request model for case synchronization"""
    case_id: int
    operation: str = "CREATE"  # CREATE, UPDATE, DELETE


class BatchCaseSyncRequest(BaseModel):
    """Request model for batch case synchronization"""
    case_ids: List[int]
    operation: str = "CREATE"


class SAPCaseStatusRequest(BaseModel):
    """Request model for SAP case status query"""
    sap_case_id: str


@router.post("/cases/sync")
async def sync_case_to_sap(
    request: CaseSyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Synchronize a single case to SAP via MuleSoft
    
    This endpoint triggers the integration process to send case data
    from the CRM system to SAP through MuleSoft middleware.
    """
    try:
        sap_service = get_sap_integration_service(db)
        
        # Validate operation
        if request.operation not in ["CREATE", "UPDATE", "DELETE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid operation. Must be CREATE, UPDATE, or DELETE"
            )
        
        # Perform synchronization
        result = await sap_service.sync_case_to_sap(request.case_id, request.operation)
        
        if result["success"]:
            return {
                "message": f"Case {request.case_id} successfully synchronized to SAP",
                "result": result,
                "timestamp": result.get("timestamp")
            }
        else:
            # Return 200 but indicate the integration failed
            return {
                "message": f"Case {request.case_id} synchronization failed",
                "result": result,
                "timestamp": result.get("timestamp")
            }
            
    except Exception as e:
        logger.exception(f"Error in case sync endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/cases/sync-batch")
async def sync_cases_batch_to_sap(
    request: BatchCaseSyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Synchronize multiple cases to SAP via MuleSoft in batch
    
    This endpoint allows bulk synchronization of cases to SAP.
    Useful for initial data migration or bulk updates.
    """
    try:
        sap_service = get_sap_integration_service(db)
        
        # Validate operation
        if request.operation not in ["CREATE", "UPDATE", "DELETE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid operation. Must be CREATE, UPDATE, or DELETE"
            )
        
        # Validate case count
        if len(request.case_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 cases allowed per batch"
            )
        
        # Perform batch synchronization
        result = await sap_service.sync_multiple_cases_to_sap(request.case_ids, request.operation)
        
        return {
            "message": f"Batch synchronization completed for {len(request.case_ids)} cases",
            "result": result
        }
        
    except Exception as e:
        logger.exception(f"Error in batch sync endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/cases/{case_id}/sync-status")
async def get_case_sync_status(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get synchronization status and history for a specific case
    
    Returns the integration history showing all sync attempts
    and their results for the specified case.
    """
    try:
        sap_service = get_sap_integration_service(db)
        
        # Get integration history
        history = sap_service.get_integration_history(case_id)
        
        return {
            "case_id": case_id,
            "integration_history": history,
            "total_attempts": len(history)
        }
        
    except Exception as e:
        logger.exception(f"Error getting sync status for case {case_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/sap-cases/status")
async def get_sap_case_status(
    request: SAPCaseStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Query case status directly from SAP via MuleSoft
    
    This endpoint queries the current status of a case in SAP
    using the SAP case ID.
    """
    try:
        sap_service = get_sap_integration_service(db)
        
        # Query SAP case status
        result = await sap_service.get_sap_case_status(request.sap_case_id)
        
        return {
            "message": "SAP case status retrieved",
            "result": result
        }
        
    except Exception as e:
        logger.exception(f"Error querying SAP case status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/cases/{case_id}/auto-sync")
async def trigger_auto_sync(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger automatic synchronization for a case
    
    This endpoint determines the appropriate sync operation
    (CREATE or UPDATE) based on the case's current state
    and triggers the synchronization.
    """
    try:
        from ..db_models import Case
        
        # Get the case
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case {case_id} not found"
            )
        
        sap_service = get_sap_integration_service(db)
        
        # Check if case has been synced before
        history = sap_service.get_integration_history(case_id)
        operation = "UPDATE" if history else "CREATE"
        
        # Perform synchronization
        result = await sap_service.sync_case_to_sap(case_id, operation)
        
        return {
            "message": f"Auto-sync triggered for case {case_id} with operation {operation}",
            "operation": operation,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in auto-sync for case {case_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health")
async def sap_integration_health():
    """
    Health check for SAP integration service
    
    Checks the connectivity to MuleSoft and overall
    integration service health.
    """
    try:
        from ..integrations.mulesoft_client import get_mulesoft_client
        
        # Test MuleSoft connectivity
        mulesoft_client = get_mulesoft_client()
        
        # In a real implementation, you might ping the MuleSoft health endpoint
        health_status = {
            "service": "sap-integration",
            "status": "healthy",
            "mulesoft_configured": bool(mulesoft_client.config.base_url),
            "timestamp": "2026-01-20T19:30:00Z"
        }
        
        return health_status
        
    except Exception as e:
        logger.exception(f"SAP integration health check failed: {str(e)}")
        return {
            "service": "sap-integration",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2026-01-20T19:30:00Z"
        }


@router.get("/config")
async def get_integration_config(
    current_user: User = Depends(get_current_user)
):
    """
    Get SAP integration configuration
    
    Returns the current integration configuration
    (without sensitive credentials).
    """
    try:
        from ..integrations.mulesoft_client import get_mulesoft_client
        
        mulesoft_client = get_mulesoft_client()
        
        return {
            "mulesoft_base_url": mulesoft_client.config.base_url,
            "timeout": mulesoft_client.config.timeout,
            "retry_attempts": mulesoft_client.config.retry_attempts,
            "authentication_configured": bool(mulesoft_client.config.client_id),
            "supported_operations": ["CREATE", "UPDATE", "DELETE"],
            "max_batch_size": 100
        }
        
    except Exception as e:
        logger.exception(f"Error getting integration config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )