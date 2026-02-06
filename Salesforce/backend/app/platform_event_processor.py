"""
Salesforce Platform Event Processor
Handles validation, normalization, and storage of CRM platform events
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from .db_models import (
    CRMEventMetadata, CRMCustomer, CRMCaseContext, 
    CRMBusinessContext, CRMEventStatus, CRMEventProcessingLog,
    EventType, EventSeverity, EventStatus
)
from .platform_event_schemas import (
    SalesforcePlatformEventBase, SalesforceCustomerEvent, SalesforceCaseEvent,
    SalesforceBillingEvent, SalesforceGenericEvent, CanonicalCRMEvent,
    CanonicalEventMetadata, CanonicalCustomer, CanonicalCRMContext,
    CanonicalBusinessContext, CanonicalEventStatus, ValidationError
)

logger = logging.getLogger(__name__)


class PlatformEventProcessor:
    """Main processor for Salesforce Platform Events"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validation_rules = self._load_validation_rules()
    
    def process_event(self, event_payload: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        """
        Main entry point for processing platform events
        
        Args:
            event_payload: Raw Salesforce platform event payload
            
        Returns:
            Tuple of (success, event_id, errors)
        """
        start_time = datetime.utcnow()
        event_id = None
        errors = []
        
        try:
            # Step 1: Extract event ID and check for duplicates
            event_id = event_payload.get('Event_UUID__c')
            if not event_id:
                return False, None, ["Missing Event_UUID__c in payload"]
            
            if self._is_duplicate_event(event_id):
                return False, event_id, [f"Duplicate event: {event_id}"]
            
            # Step 2: Validate the event payload
            validation_result = self._validate_event(event_payload)
            if not validation_result.is_valid:
                self._log_processing_step(event_id, "ERROR", "Validation failed", 
                                        {"errors": validation_result.errors})
                return False, event_id, validation_result.errors
            
            # Step 3: Normalize to canonical format
            canonical_event = self._normalize_event(event_payload)
            
            # Step 4: Persist to database
            self._persist_event(canonical_event, event_payload)
            
            # Step 5: Update processing status
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._update_event_status(event_id, EventStatus.PROCESSED, processing_time)
            
            self._log_processing_step(event_id, "INFO", "Event processed successfully",
                                    {"processing_time_ms": processing_time})
            
            return True, event_id, []
            
        except Exception as e:
            logger.exception(f"Error processing event {event_id}: {str(e)}")
            if event_id:
                self._update_event_status(event_id, EventStatus.FAILED)
                self._log_processing_step(event_id, "ERROR", f"Processing failed: {str(e)}")
            return False, event_id, [str(e)]
    
    def _is_duplicate_event(self, event_id: str) -> bool:
        """Check if event already exists"""
        existing = self.db.query(CRMEventMetadata).filter(
            CRMEventMetadata.event_id == event_id
        ).first()
        return existing is not None
    
    def _validate_event(self, payload: Dict[str, Any]) -> 'ValidationResult':
        """Validate event payload against business rules"""
        errors = []
        
        # Required field validation
        required_fields = ['Event_UUID__c', 'Event_Type__c', 'Event_Timestamp__c', 'Severity__c']
        for field in required_fields:
            if field not in payload or payload[field] is None:
                errors.append(f"Required field missing: {field}")
        
        # Event type validation
        event_type = payload.get('Event_Type__c')
        if event_type and event_type not in [e.value for e in EventType]:
            errors.append(f"Invalid event type: {event_type}")
        
        # Source system validation
        source_system = payload.get('Source_System__c', 'Salesforce')
        if source_system != 'Salesforce':
            errors.append(f"Invalid source system: {source_system}")
        
        # Case-specific validation
        if event_type and 'CASE' in event_type:
            if not payload.get('Case_Id__c'):
                errors.append("Case_Id__c is mandatory for case-related events")
        
        # P1 priority SLA validation
        if payload.get('Priority__c') == 'P1':
            if not payload.get('SLA_Target_Hours__c'):
                errors.append("P1 priority requires SLA details")
        
        # Severity validation
        severity = payload.get('Severity__c')
        if severity and severity not in [s.value for s in EventSeverity]:
            errors.append(f"Invalid severity: {severity}")
        
        return ValidationResult(len(errors) == 0, errors)
    
    def _normalize_event(self, payload: Dict[str, Any]) -> CanonicalCRMEvent:
        """Normalize Salesforce payload to canonical CRM event format"""
        
        # Extract metadata
        metadata = CanonicalEventMetadata(
            event_id=payload['Event_UUID__c'],
            event_type=payload['Event_Type__c'],
            event_source=payload.get('Source_System__c', 'Salesforce'),
            event_timestamp=self._parse_datetime(payload['Event_Timestamp__c']),
            correlation_id=payload.get('Correlation_Id__c'),
            severity=payload['Severity__c'],
            target_system=payload.get('Target_System__c'),
            operation=payload.get('Operation__c'),
            integration_status=payload.get('Integration_Status__c', 'PENDING')
        )
        
        # Extract customer information
        customer = None
        if any(field in payload for field in ['Customer_Id__c', 'Account_Id__c', 'Billing_Account__c']):
            customer = CanonicalCustomer(
                customer_id=payload.get('Customer_Id__c'),
                account_id=payload.get('Account_Id__c'),
                billing_account=payload.get('Billing_Account__c'),
                customer_name=payload.get('Customer_Name__c'),
                customer_email=payload.get('Customer_Email__c'),
                customer_phone=payload.get('Customer_Phone__c'),
                customer_type=payload.get('Customer_Type__c'),
                customer_status=payload.get('Customer_Status__c')
            )
        
        # Extract CRM context (case information)
        crm_context = None
        if any(field in payload for field in ['Case_Id__c', 'Case_Number__c']):
            crm_context = CanonicalCRMContext(
                case_id=payload.get('Case_Id__c'),
                case_number=payload.get('Case_Number__c'),
                case_type=payload.get('Case_Type__c'),
                case_status=payload.get('Case_Status__c'),
                case_priority=payload.get('Priority__c'),
                case_subject=payload.get('Case_Subject__c'),
                case_description=payload.get('Case_Description__c'),
                sla_target_hours=payload.get('SLA_Target_Hours__c'),
                sla_due_date=self._parse_datetime(payload.get('SLA_Due_Date__c')) if payload.get('SLA_Due_Date__c') else None,
                is_escalated=payload.get('Case_Status__c') == 'Escalated'
            )
        
        # Extract business context
        business_context = CanonicalBusinessContext(
            billing_amount=payload.get('Billing_Amount__c'),
            currency_code=payload.get('Currency_Code__c'),
            payment_terms=payload.get('Payment_Terms__c'),
            custom_fields=self._extract_custom_fields(payload)
        )
        
        # Create status
        status = CanonicalEventStatus(
            current_status="VALIDATED",
            validation_passed=True
        )
        
        return CanonicalCRMEvent(
            eventMetadata=metadata,
            customer=customer,
            crmContext=crm_context,
            businessContext=business_context,
            status=status
        )
    
    def _persist_event(self, canonical_event: CanonicalCRMEvent, raw_payload: Dict[str, Any]):
        """Persist canonical event to database tables"""
        
        try:
            # Create event metadata record
            metadata = CRMEventMetadata(
                event_id=canonical_event.eventMetadata.event_id,
                event_type=canonical_event.eventMetadata.event_type,
                event_source=canonical_event.eventMetadata.event_source,
                event_timestamp=canonical_event.eventMetadata.event_timestamp,
                correlation_id=canonical_event.eventMetadata.correlation_id,
                severity=canonical_event.eventMetadata.severity,
                target_system=canonical_event.eventMetadata.target_system,
                operation=canonical_event.eventMetadata.operation,
                integration_status=canonical_event.eventMetadata.integration_status,
                raw_payload=raw_payload
            )
            self.db.add(metadata)
            
            # Create customer record if present
            if canonical_event.customer:
                customer = CRMCustomer(
                    event_id=canonical_event.eventMetadata.event_id,
                    customer_id=canonical_event.customer.customer_id,
                    account_id=canonical_event.customer.account_id,
                    billing_account=canonical_event.customer.billing_account,
                    customer_name=canonical_event.customer.customer_name,
                    customer_email=canonical_event.customer.customer_email,
                    customer_phone=canonical_event.customer.customer_phone,
                    customer_type=canonical_event.customer.customer_type,
                    customer_status=canonical_event.customer.customer_status
                )
                self.db.add(customer)
            
            # Create case context record if present
            if canonical_event.crmContext:
                case_context = CRMCaseContext(
                    event_id=canonical_event.eventMetadata.event_id,
                    case_id=canonical_event.crmContext.case_id,
                    case_number=canonical_event.crmContext.case_number,
                    case_type=canonical_event.crmContext.case_type,
                    case_status=canonical_event.crmContext.case_status,
                    case_priority=canonical_event.crmContext.case_priority,
                    case_subject=canonical_event.crmContext.case_subject,
                    case_description=canonical_event.crmContext.case_description,
                    sla_target_hours=canonical_event.crmContext.sla_target_hours,
                    sla_due_date=canonical_event.crmContext.sla_due_date,
                    is_escalated=canonical_event.crmContext.is_escalated,
                    escalation_level=canonical_event.crmContext.escalation_level
                )
                self.db.add(case_context)
            
            # Create business context record
            if canonical_event.businessContext:
                business_context = CRMBusinessContext(
                    event_id=canonical_event.eventMetadata.event_id,
                    billing_amount=canonical_event.businessContext.billing_amount,
                    currency_code=canonical_event.businessContext.currency_code,
                    payment_terms=canonical_event.businessContext.payment_terms,
                    custom_fields=canonical_event.businessContext.custom_fields
                )
                self.db.add(business_context)
            
            # Create event status record
            event_status = CRMEventStatus(
                event_id=canonical_event.eventMetadata.event_id,
                current_status=canonical_event.status.current_status,
                validation_passed=canonical_event.status.validation_passed,
                normalization_completed=True,
                persistence_completed=True
            )
            self.db.add(event_status)
            
            # Commit all changes
            self.db.commit()
            
            self._log_processing_step(
                canonical_event.eventMetadata.event_id,
                "INFO",
                "Event persisted successfully"
            )
            
        except IntegrityError as e:
            self.db.rollback()
            raise Exception(f"Database integrity error: {str(e)}")
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Database persistence error: {str(e)}")
    
    def _update_event_status(self, event_id: str, status: EventStatus, processing_time_ms: Optional[int] = None):
        """Update event processing status"""
        try:
            event_status = self.db.query(CRMEventStatus).filter(
                CRMEventStatus.event_id == event_id
            ).first()
            
            if event_status:
                event_status.previous_status = event_status.current_status
                event_status.current_status = status.value
                event_status.status_changed_at = datetime.utcnow()
                
                if status == EventStatus.PROCESSED:
                    event_status.completed_at = datetime.utcnow()
                    if processing_time_ms:
                        event_status.completion_duration_ms = processing_time_ms
                
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Failed to update event status for {event_id}: {str(e)}")
    
    def _log_processing_step(self, event_id: str, level: str, message: str, context: Optional[Dict] = None):
        """Log processing step for audit trail"""
        try:
            log_entry = CRMEventProcessingLog(
                event_id=event_id,
                log_level=level,
                log_message=message,
                log_context=context or {}
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log processing step: {str(e)}")
    
    def _parse_datetime(self, dt_str: Any) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not dt_str:
            return None
        
        if isinstance(dt_str, datetime):
            return dt_str
        
        try:
            # Handle ISO format with timezone
            if isinstance(dt_str, str):
                if dt_str.endswith('Z'):
                    dt_str = dt_str[:-1] + '+00:00'
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"Failed to parse datetime {dt_str}: {str(e)}")
            return None
    
    def _extract_custom_fields(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract custom fields from payload"""
        custom_fields = {}
        
        # Extract fields that end with __c (Salesforce custom fields)
        for key, value in payload.items():
            if key.endswith('__c') and key not in [
                'Event_UUID__c', 'Event_Type__c', 'Source_System__c', 
                'Event_Timestamp__c', 'Correlation_Id__c', 'Severity__c',
                'Customer_Id__c', 'Account_Id__c', 'Case_Id__c'
            ]:
                custom_fields[key] = value
        
        return custom_fields if custom_fields else None
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules from database or configuration"""
        # This could be loaded from database or configuration file
        # For now, return empty dict - rules are hardcoded in _validate_event
        return {}
    
    def get_event_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an event"""
        try:
            metadata = self.db.query(CRMEventMetadata).filter(
                CRMEventMetadata.event_id == event_id
            ).first()
            
            if not metadata:
                return None
            
            status = self.db.query(CRMEventStatus).filter(
                CRMEventStatus.event_id == event_id
            ).first()
            
            return {
                "event_id": event_id,
                "event_type": metadata.event_type,
                "current_status": status.current_status if status else "UNKNOWN",
                "validation_passed": status.validation_passed if status else False,
                "normalization_completed": status.normalization_completed if status else False,
                "persistence_completed": status.persistence_completed if status else False,
                "error_count": status.error_count if status else 0,
                "retry_count": status.retry_count if status else 0,
                "created_at": metadata.created_at,
                "updated_at": metadata.updated_at
            }
            
        except Exception as e:
            logger.error(f"Failed to get event status for {event_id}: {str(e)}")
            return None


class ValidationResult:
    """Validation result container"""
    def __init__(self, is_valid: bool, errors: List[str]):
        self.is_valid = is_valid
        self.errors = errors