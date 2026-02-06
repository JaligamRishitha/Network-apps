"""
Pydantic schemas for Salesforce Platform Event processing
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class EventTypeEnum(str, Enum):
    """Valid CRM Event Types"""
    CUSTOMER_CREATED = "CUSTOMER_CREATED"
    CUSTOMER_UPDATED = "CUSTOMER_UPDATED"
    CUSTOMER_BILLING_ADJUSTMENT = "CUSTOMER_BILLING_ADJUSTMENT"
    CASE_CREATED = "CASE_CREATED"
    CASE_UPDATED = "CASE_UPDATED"
    CASE_ESCALATED = "CASE_ESCALATED"
    CASE_CLOSED = "CASE_CLOSED"
    CONTACT_CREATED = "CONTACT_CREATED"
    CONTACT_UPDATED = "CONTACT_UPDATED"
    BILLING_DISPUTE = "BILLING_DISPUTE"
    BILLING_PAYMENT_RECEIVED = "BILLING_PAYMENT_RECEIVED"
    COMPLAINT_FILED = "COMPLAINT_FILED"
    COMPLAINT_RESOLVED = "COMPLAINT_RESOLVED"
    SLA_BREACH = "SLA_BREACH"
    SLA_WARNING = "SLA_WARNING"
    SLA_RESTORED = "SLA_RESTORED"


class SeverityEnum(str, Enum):
    """Event Severity Levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PriorityEnum(str, Enum):
    """Case Priority Levels"""
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


# Input Schemas (from Salesforce)
class SalesforcePlatformEventBase(BaseModel):
    """Base Salesforce Platform Event structure"""
    Event_UUID__c: str = Field(..., description="Unique event identifier")
    Event_Type__c: EventTypeEnum = Field(..., description="Type of CRM event")
    Source_System__c: str = Field(default="Salesforce", description="Source system")
    Event_Timestamp__c: datetime = Field(..., description="Event timestamp")
    Correlation_Id__c: Optional[str] = Field(None, description="Correlation ID for tracking")
    Severity__c: SeverityEnum = Field(..., description="Event severity")
    
    @validator('Source_System__c')
    def validate_source_system(cls, v):
        if v != "Salesforce":
            raise ValueError("Source system must be Salesforce")
        return v


class SalesforceCustomerEvent(SalesforcePlatformEventBase):
    """Customer-related platform events"""
    Customer_Id__c: str = Field(..., description="Salesforce Customer ID")
    Account_Id__c: Optional[str] = Field(None, description="Salesforce Account ID")
    Billing_Account__c: Optional[str] = Field(None, description="Billing system account ID")
    Customer_Name__c: Optional[str] = Field(None, description="Customer name")
    Customer_Email__c: Optional[str] = Field(None, description="Customer email")
    Customer_Phone__c: Optional[str] = Field(None, description="Customer phone")
    Customer_Type__c: Optional[str] = Field(None, description="Customer type")
    Customer_Status__c: Optional[str] = Field(None, description="Customer status")


class SalesforceCaseEvent(SalesforcePlatformEventBase):
    """Case-related platform events"""
    Case_Id__c: str = Field(..., description="Salesforce Case ID")
    Case_Number__c: Optional[str] = Field(None, description="Case number")
    Case_Type__c: Optional[str] = Field(None, description="Case type")
    Case_Status__c: Optional[str] = Field(None, description="Case status")
    Priority__c: Optional[PriorityEnum] = Field(None, description="Case priority")
    Case_Subject__c: Optional[str] = Field(None, description="Case subject")
    Case_Description__c: Optional[str] = Field(None, description="Case description")
    Customer_Id__c: Optional[str] = Field(None, description="Related customer ID")
    Account_Id__c: Optional[str] = Field(None, description="Related account ID")
    SLA_Target_Hours__c: Optional[int] = Field(None, description="SLA target in hours")
    SLA_Due_Date__c: Optional[datetime] = Field(None, description="SLA due date")
    
    @validator('Priority__c')
    def validate_p1_sla(cls, v, values):
        if v == "P1" and not values.get('SLA_Target_Hours__c'):
            raise ValueError("P1 priority cases must have SLA details")
        return v


class SalesforceBillingEvent(SalesforcePlatformEventBase):
    """Billing-related platform events"""
    Customer_Id__c: str = Field(..., description="Customer ID")
    Billing_Account__c: str = Field(..., description="Billing account ID")
    Billing_Amount__c: Optional[float] = Field(None, description="Billing amount")
    Currency_Code__c: Optional[str] = Field(None, description="Currency code")
    Payment_Terms__c: Optional[str] = Field(None, description="Payment terms")
    Case_Id__c: Optional[str] = Field(None, description="Related case ID")


class SalesforceGenericEvent(SalesforcePlatformEventBase):
    """Generic platform event for flexible handling"""
    # Core required fields inherited from base
    # Additional fields stored as dynamic attributes
    
    class Config:
        extra = "allow"  # Allow additional fields


# Canonical CRM Event Model (normalized)
class CanonicalEventMetadata(BaseModel):
    """Canonical event metadata structure"""
    event_id: str
    event_type: EventTypeEnum
    event_source: str = "Salesforce"
    event_timestamp: datetime
    correlation_id: Optional[str] = None
    severity: SeverityEnum
    target_system: Optional[str] = None
    operation: Optional[str] = None
    integration_status: str = "PENDING"


class CanonicalCustomer(BaseModel):
    """Canonical customer structure"""
    customer_id: Optional[str] = None
    account_id: Optional[str] = None
    billing_account: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_type: Optional[str] = None
    customer_status: Optional[str] = None
    billing_address: Optional[str] = None
    service_address: Optional[str] = None


class CanonicalCRMContext(BaseModel):
    """Canonical CRM context structure"""
    case_id: Optional[str] = None
    case_number: Optional[str] = None
    case_type: Optional[str] = None
    case_status: Optional[str] = None
    case_priority: Optional[str] = None
    case_subject: Optional[str] = None
    case_description: Optional[str] = None
    sla_target_hours: Optional[int] = None
    sla_due_date: Optional[datetime] = None
    is_escalated: bool = False
    escalation_level: int = 0


class CanonicalBusinessContext(BaseModel):
    """Canonical business context structure"""
    business_unit: Optional[str] = None
    region: Optional[str] = None
    territory: Optional[str] = None
    product_line: Optional[str] = None
    service_type: Optional[str] = None
    contract_number: Optional[str] = None
    billing_amount: Optional[float] = None
    currency_code: Optional[str] = None
    payment_terms: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class CanonicalEventStatus(BaseModel):
    """Canonical event status structure"""
    current_status: str = "RECEIVED"
    validation_passed: bool = False
    normalization_completed: bool = False
    persistence_completed: bool = False
    error_count: int = 0
    retry_count: int = 0
    max_retries: int = 3


class CanonicalCRMEvent(BaseModel):
    """Complete canonical CRM event structure"""
    eventMetadata: CanonicalEventMetadata
    customer: Optional[CanonicalCustomer] = None
    crmContext: Optional[CanonicalCRMContext] = None
    businessContext: Optional[CanonicalBusinessContext] = None
    status: CanonicalEventStatus


# Response Schemas
class EventProcessingResponse(BaseModel):
    """Response from event processing"""
    event_id: str
    status: str
    message: str
    validation_errors: Optional[List[str]] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime


class EventStatusResponse(BaseModel):
    """Event status query response"""
    event_id: str
    event_type: str
    current_status: str
    validation_passed: bool
    normalization_completed: bool
    persistence_completed: bool
    error_count: int
    retry_count: int
    last_error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    error_type: str
    message: str
    value: Optional[Any] = None


class ProcessingMetrics(BaseModel):
    """Processing metrics and statistics"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_status: Dict[str, int]
    average_processing_time_ms: float
    error_rate: float
    period_start: datetime
    period_end: datetime