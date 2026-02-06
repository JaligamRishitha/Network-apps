"""
API routes for Salesforce Platform Event processing
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ..platform_event_processor import PlatformEventProcessor
from ..platform_event_schemas import (
    EventProcessingResponse, EventStatusResponse, ProcessingMetrics,
    SalesforceGenericEvent
)
from ..db_models import (
    CRMEventMetadata, CRMEventStatus, CRMEventProcessingLog
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/platform-events", tags=["Platform Events"])


@router.get("/")
async def platform_events_index():
    """
    Platform Events API Index - Lists available endpoints
    """
    return {
        "service": "Salesforce Platform Events API",
        "version": "1.0.0",
        "description": "Process, validate, and store Salesforce Platform Events for CRM activities",
        "endpoints": {
            "POST /process": "Process a single platform event",
            "POST /process-batch": "Process multiple platform events",
            "GET /status/{event_id}": "Get event processing status",
            "GET /events": "List platform events with filtering",
            "GET /events/{event_id}": "Get detailed event information",
            "GET /events/{event_id}/logs": "Get event processing logs",
            "POST /events/{event_id}/retry": "Retry failed event processing",
            "GET /metrics": "Get processing metrics",
            "GET /health": "Health check endpoint"
        },
        "supported_event_types": [
            "CUSTOMER_CREATED", "CUSTOMER_UPDATED", "CUSTOMER_BILLING_ADJUSTMENT",
            "CASE_CREATED", "CASE_UPDATED", "CASE_ESCALATED", "CASE_CLOSED",
            "CONTACT_CREATED", "CONTACT_UPDATED",
            "BILLING_DISPUTE", "BILLING_PAYMENT_RECEIVED",
            "COMPLAINT_FILED", "COMPLAINT_RESOLVED",
            "SLA_BREACH", "SLA_WARNING", "SLA_RESTORED"
        ],
        "documentation": "/docs"
    }


@router.post("/process", response_model=EventProcessingResponse)
async def process_platform_event(
    event_payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process a Salesforce Platform Event
    
    This endpoint receives platform events from Salesforce and processes them
    according to the CRM event processing workflow.
    """
    start_time = datetime.utcnow()
    
    try:
        processor = PlatformEventProcessor(db)
        success, event_id, errors = processor.process_event(event_payload)
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if success:
            # Schedule background tasks for downstream processing if needed
            # background_tasks.add_task(notify_downstream_systems, event_id)
            
            return EventProcessingResponse(
                event_id=event_id,
                status="PROCESSED",
                message="Event processed successfully",
                processing_time_ms=processing_time,
                created_at=datetime.utcnow()
            )
        else:
            return EventProcessingResponse(
                event_id=event_id or "unknown",
                status="FAILED",
                message="Event processing failed",
                validation_errors=errors,
                processing_time_ms=processing_time,
                created_at=datetime.utcnow()
            )
            
    except Exception as e:
        logger.exception(f"Unexpected error processing platform event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/process-batch")
async def process_platform_events_batch(
    events: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process multiple platform events in batch
    """
    results = []
    processor = PlatformEventProcessor(db)
    
    for event_payload in events:
        try:
            success, event_id, errors = processor.process_event(event_payload)
            results.append({
                "event_id": event_id,
                "status": "PROCESSED" if success else "FAILED",
                "errors": errors if not success else None
            })
        except Exception as e:
            results.append({
                "event_id": event_payload.get('Event_UUID__c', 'unknown'),
                "status": "ERROR",
                "errors": [str(e)]
            })
    
    return {
        "total_events": len(events),
        "results": results,
        "processed_at": datetime.utcnow()
    }


@router.get("/status/{event_id}", response_model=EventStatusResponse)
async def get_event_status(
    event_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the processing status of a specific event
    """
    processor = PlatformEventProcessor(db)
    status_info = processor.get_event_status(event_id)
    
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    
    return EventStatusResponse(**status_info)


@router.get("/events")
async def list_events(
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List platform events with optional filtering
    """
    query = db.query(CRMEventMetadata)
    
    if event_type:
        query = query.filter(CRMEventMetadata.event_type == event_type)
    
    if severity:
        query = query.filter(CRMEventMetadata.severity == severity)
    
    if status:
        query = query.join(CRMEventStatus).filter(CRMEventStatus.current_status == status)
    
    total = query.count()
    events = query.order_by(CRMEventMetadata.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "events": [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "severity": event.severity,
                "event_timestamp": event.event_timestamp,
                "correlation_id": event.correlation_id,
                "integration_status": event.integration_status,
                "created_at": event.created_at
            }
            for event in events
        ],
        "limit": limit,
        "offset": offset
    }


@router.get("/events/{event_id}")
async def get_event_details(
    event_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific event
    """
    # Get event metadata
    metadata = db.query(CRMEventMetadata).filter(
        CRMEventMetadata.event_id == event_id
    ).first()
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    
    # Get related data
    customer = metadata.customer
    case_context = metadata.case_context
    business_context = metadata.business_context
    event_status = metadata.event_status
    
    return {
        "metadata": {
            "event_id": metadata.event_id,
            "event_type": metadata.event_type,
            "event_source": metadata.event_source,
            "event_timestamp": metadata.event_timestamp,
            "correlation_id": metadata.correlation_id,
            "severity": metadata.severity,
            "target_system": metadata.target_system,
            "operation": metadata.operation,
            "integration_status": metadata.integration_status,
            "raw_payload": metadata.raw_payload,
            "created_at": metadata.created_at,
            "updated_at": metadata.updated_at
        },
        "customer": {
            "customer_id": customer.customer_id if customer else None,
            "account_id": customer.account_id if customer else None,
            "billing_account": customer.billing_account if customer else None,
            "customer_name": customer.customer_name if customer else None,
            "customer_email": customer.customer_email if customer else None,
            "customer_phone": customer.customer_phone if customer else None,
            "customer_type": customer.customer_type if customer else None,
            "customer_status": customer.customer_status if customer else None
        } if customer else None,
        "case_context": {
            "case_id": case_context.case_id if case_context else None,
            "case_number": case_context.case_number if case_context else None,
            "case_type": case_context.case_type if case_context else None,
            "case_status": case_context.case_status if case_context else None,
            "case_priority": case_context.case_priority if case_context else None,
            "case_subject": case_context.case_subject if case_context else None,
            "sla_target_hours": case_context.sla_target_hours if case_context else None,
            "sla_due_date": case_context.sla_due_date if case_context else None,
            "is_escalated": case_context.is_escalated if case_context else None
        } if case_context else None,
        "business_context": {
            "billing_amount": business_context.billing_amount if business_context else None,
            "currency_code": business_context.currency_code if business_context else None,
            "payment_terms": business_context.payment_terms if business_context else None,
            "custom_fields": business_context.custom_fields if business_context else None
        } if business_context else None,
        "status": {
            "current_status": event_status.current_status if event_status else None,
            "validation_passed": event_status.validation_passed if event_status else None,
            "normalization_completed": event_status.normalization_completed if event_status else None,
            "persistence_completed": event_status.persistence_completed if event_status else None,
            "error_count": event_status.error_count if event_status else None,
            "retry_count": event_status.retry_count if event_status else None,
            "completed_at": event_status.completed_at if event_status else None
        } if event_status else None
    }


@router.get("/events/{event_id}/logs")
async def get_event_logs(
    event_id: str,
    db: Session = Depends(get_db)
):
    """
    Get processing logs for a specific event
    """
    logs = db.query(CRMEventProcessingLog).filter(
        CRMEventProcessingLog.event_id == event_id
    ).order_by(CRMEventProcessingLog.logged_at.desc()).all()
    
    if not logs:
        # Check if event exists
        metadata = db.query(CRMEventMetadata).filter(
            CRMEventMetadata.event_id == event_id
        ).first()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )
    
    return {
        "event_id": event_id,
        "logs": [
            {
                "log_level": log.log_level,
                "log_message": log.log_message,
                "log_context": log.log_context,
                "processing_step": log.processing_step,
                "logged_at": log.logged_at
            }
            for log in logs
        ]
    }


@router.get("/metrics", response_model=ProcessingMetrics)
async def get_processing_metrics(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Get processing metrics for the specified time period
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Get events in time period
    events = db.query(CRMEventMetadata).filter(
        CRMEventMetadata.created_at >= start_time,
        CRMEventMetadata.created_at <= end_time
    ).all()
    
    total_events = len(events)
    
    # Count by event type
    events_by_type = {}
    for event in events:
        events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1
    
    # Count by status
    events_by_status = {}
    for event in events:
        if event.event_status:
            status = event.event_status.current_status
            events_by_status[status] = events_by_status.get(status, 0) + 1
    
    # Calculate average processing time
    processing_times = []
    error_count = 0
    
    for event in events:
        if event.event_status:
            if event.event_status.completion_duration_ms:
                processing_times.append(event.event_status.completion_duration_ms)
            if event.event_status.error_count > 0:
                error_count += 1
    
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    error_rate = (error_count / total_events * 100) if total_events > 0 else 0
    
    return ProcessingMetrics(
        total_events=total_events,
        events_by_type=events_by_type,
        events_by_status=events_by_status,
        average_processing_time_ms=avg_processing_time,
        error_rate=error_rate,
        period_start=start_time,
        period_end=end_time
    )


@router.post("/events/{event_id}/retry")
async def retry_event_processing(
    event_id: str,
    db: Session = Depends(get_db)
):
    """
    Retry processing for a failed event
    """
    # Get the original event
    metadata = db.query(CRMEventMetadata).filter(
        CRMEventMetadata.event_id == event_id
    ).first()
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    
    # Check if event can be retried
    event_status = metadata.event_status
    if not event_status or event_status.current_status not in ["FAILED", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event {event_id} cannot be retried (current status: {event_status.current_status if event_status else 'UNKNOWN'})"
        )
    
    if event_status.retry_count >= event_status.max_retries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event {event_id} has exceeded maximum retry attempts"
        )
    
    # Retry processing
    try:
        processor = PlatformEventProcessor(db)
        success, _, errors = processor.process_event(metadata.raw_payload)
        
        # Update retry count
        event_status.retry_count += 1
        event_status.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "event_id": event_id,
            "retry_successful": success,
            "retry_count": event_status.retry_count,
            "errors": errors if not success else None,
            "retried_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.exception(f"Error retrying event {event_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retry failed: {str(e)}"
        )


@router.get("/health")
async def platform_events_health_check():
    """
    Health check endpoint for platform events service
    """
    return {
        "service": "platform-events",
        "status": "healthy",
        "timestamp": datetime.utcnow()
    }