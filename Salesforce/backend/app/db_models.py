from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    user = "user"


class LeadStatus(str, enum.Enum):
    new = "New"
    contacted = "Contacted"
    qualified = "Qualified"
    unqualified = "Unqualified"
    converted = "Converted"


class CaseStatus(str, enum.Enum):
    new = "New"
    working = "Working"
    escalated = "Escalated"
    closed = "Closed"


class CasePriority(str, enum.Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class OpportunityStage(str, enum.Enum):
    prospecting = "Prospecting"
    qualification = "Qualification"
    needs_analysis = "Needs Analysis"
    proposal = "Proposal"
    negotiation = "Negotiation"
    closed_won = "Closed Won"
    closed_lost = "Closed Lost"


# Platform Event Enums
class EventType(str, enum.Enum):
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


class EventSeverity(str, enum.Enum):
    """Event Severity Levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventStatus(str, enum.Enum):
    """Event Processing Status"""
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(20), default="user")
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owned_accounts = relationship("Account", back_populates="owner")
    owned_contacts = relationship("Contact", back_populates="owner")
    owned_leads = relationship("Lead", back_populates="owner")
    owned_opportunities = relationship("Opportunity", back_populates="owner")
    owned_cases = relationship("Case", back_populates="owner")
    activities = relationship("Activity", back_populates="created_by_user")

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.username

    @property
    def alias(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(50))
    website = Column(String(255))
    industry = Column(String(100))
    description = Column(Text)
    billing_address = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    correlation_id = Column(String(255), nullable=True)
    integration_status = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_accounts")
    contacts = relationship("Contact", back_populates="account")
    opportunities = relationship("Opportunity", back_populates="account")
    cases = relationship("Case", back_populates="account")


class AccountRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class AccountCreationRequest(Base):
    """
    Tracks account creation requests for approval/audit workflows.
    - Managers/admins auto-complete but still record an audit request.
    - Regular users create a PENDING request that must be approved.
    """
    __tablename__ = "account_creation_requests"

    id = Column(Integer, primary_key=True, index=True)

    # Snapshot of requested data
    name = Column(String(255), nullable=False, index=True)
    requested_payload = Column(JSON, nullable=False)

    # Request metadata
    status = Column(String(20), nullable=False, default=AccountRequestStatus.PENDING.value, index=True)
    auto_approved = Column(Boolean, default=False)
    correlation_id = Column(String(255), index=True)

    # User context
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"))

    # Downstream integration/audit details (MuleSoft/ServiceNow placeholders)
    servicenow_ticket_id = Column(String(255), index=True)
    servicenow_status = Column(String(50))
    mulesoft_transaction_id = Column(String(255), index=True)
    integration_status = Column(String(50))
    error_message = Column(Text)

    # Created resource linkage
    created_account_id = Column(Integer, ForeignKey("accounts.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    created_account = relationship("Account")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    title = Column(String(100))
    phone = Column(String(50))
    email = Column(String(255), index=True)
    mailing_address = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_contacts")
    account = relationship("Account", back_populates="contacts")
    cases = relationship("Case", back_populates="contact")

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100), nullable=False)
    company = Column(String(255))
    title = Column(String(100))
    phone = Column(String(50))
    email = Column(String(255), index=True)
    status = Column(String(50), default="New")
    score = Column(Integer, default=0)
    region = Column(String(100))
    source = Column(String(100))
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_converted = Column(Boolean, default=False)
    converted_account_id = Column(Integer, ForeignKey("accounts.id"))
    converted_contact_id = Column(Integer, ForeignKey("contacts.id"))
    converted_opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_leads")

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    amount = Column(Float, default=0)
    stage = Column(String(50), default="Prospecting")
    probability = Column(Integer, default=0)
    close_date = Column(DateTime(timezone=True))
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_opportunities")
    account = relationship("Account", back_populates="opportunities")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="New")
    priority = Column(String(50), default="Medium")
    account_id = Column(Integer, ForeignKey("accounts.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_escalated = Column(Boolean, default=False)
    escalated_at = Column(DateTime(timezone=True))
    sla_due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="owned_cases")
    account = relationship("Account", back_populates="cases")
    contact = relationship("Contact", back_populates="cases")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(50), nullable=False)  # contact, account, lead, opportunity, case
    record_id = Column(Integer, nullable=False)
    activity_type = Column(String(50), nullable=False)  # call, email, meeting, note, task
    subject = Column(String(255))
    details = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    created_by_user = relationship("User", back_populates="activities")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), nullable=False)  # create, update, delete, view
    target_table = Column(String(50), nullable=False)
    target_id = Column(Integer)
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class RecentRecord(Base):
    __tablename__ = "recent_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_type = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    record_name = Column(String(255))
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())


class ServiceAccount(Base):
    __tablename__ = "service_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    warranty_status = Column(String(50), default="Active")  # Active, Expired, Extended
    warranty_start_date = Column(DateTime(timezone=True))
    warranty_end_date = Column(DateTime(timezone=True))
    warranty_extended_until = Column(DateTime(timezone=True))
    service_level = Column(String(50))  # Gold, Silver, Bronze
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account")
    owner = relationship("User")


class ServiceLevelAgreement(Base):
    __tablename__ = "service_level_agreements"

    id = Column(Integer, primary_key=True, index=True)
    service_account_id = Column(Integer, ForeignKey("service_accounts.id"), nullable=False)
    name = Column(String(255), nullable=False)
    response_time_hours = Column(Integer)  # Hours to respond
    resolution_time_hours = Column(Integer)  # Hours to resolve
    uptime_percentage = Column(Float, default=99.9)
    support_hours = Column(String(100))  # 24/7, 9-5, etc.
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    service_account = relationship("ServiceAccount")


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    quotation_number = Column(String(50), unique=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    service_account_id = Column(Integer, ForeignKey("service_accounts.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    amount = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    status = Column(String(50), default="Draft")  # Draft, Sent, Accepted, Rejected
    valid_until = Column(DateTime(timezone=True))
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account")
    service_account = relationship("ServiceAccount")
    owner = relationship("User")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    service_account_id = Column(Integer, ForeignKey("service_accounts.id"))
    quotation_id = Column(Integer, ForeignKey("quotations.id"))
    invoice_type = Column(String(50), default="Standard")  # Standard, Proforma, Credit Note
    description = Column(Text)
    amount = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    status = Column(String(50), default="Draft")  # Draft, Sent, Paid, Overdue
    invoice_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    paid_date = Column(DateTime(timezone=True))
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account")
    service_account = relationship("ServiceAccount")
    quotation = relationship("Quotation")
    owner = relationship("User")


class WarrantyExtension(Base):
    __tablename__ = "warranty_extensions"

    id = Column(Integer, primary_key=True, index=True)
    service_account_id = Column(Integer, ForeignKey("service_accounts.id"), nullable=False)
    extension_start_date = Column(DateTime(timezone=True), nullable=False)
    extension_end_date = Column(DateTime(timezone=True), nullable=False)
    extension_cost = Column(Float, default=0)
    status = Column(String(50), default="Active")  # Active, Expired, Cancelled
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    service_account = relationship("ServiceAccount")
    owner = relationship("User")


# Platform Event Models
class CRMEventMetadata(Base):
    """
    Core event metadata table - stores essential event information
    Maps to eventMetadata in canonical model
    """
    __tablename__ = "crm_event_metadata"

    # Primary key - Salesforce Event UUID
    event_id = Column(String(255), primary_key=True, index=True)
    
    # Core event fields
    event_type = Column(String(100), nullable=False, index=True)
    event_source = Column(String(50), nullable=False, default="Salesforce")
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    correlation_id = Column(String(255), index=True)
    severity = Column(String(20), nullable=False)
    
    # Processing metadata
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    processing_duration_ms = Column(Integer)
    
    # Integration tracking
    target_system = Column(String(100))
    operation = Column(String(100))
    integration_status = Column(String(50), default="PENDING")
    
    # Raw payload for audit
    raw_payload = Column(JSON)
    
    # Validation and error tracking
    validation_errors = Column(JSON)
    processing_errors = Column(JSON)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("CRMCustomer", back_populates="event_metadata", uselist=False)
    case_context = relationship("CRMCaseContext", back_populates="event_metadata", uselist=False)
    business_context = relationship("CRMBusinessContext", back_populates="event_metadata", uselist=False)
    event_status = relationship("CRMEventStatus", back_populates="event_metadata", uselist=False)


class CRMCustomer(Base):
    """
    Customer information extracted from platform events
    Maps to customer in canonical model
    """
    __tablename__ = "crm_customer"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), ForeignKey("crm_event_metadata.event_id"), nullable=False, index=True)
    
    # Salesforce Customer IDs
    customer_id = Column(String(100), index=True)  # Salesforce Customer ID
    account_id = Column(String(100), index=True)   # Salesforce Account ID
    billing_account = Column(String(100), index=True)  # External billing system ID
    
    # Customer details
    customer_name = Column(String(255))
    customer_email = Column(String(255))
    customer_phone = Column(String(50))
    customer_type = Column(String(50))  # Individual, Business, etc.
    
    # Address information
    billing_address = Column(Text)
    service_address = Column(Text)
    
    # Customer status
    customer_status = Column(String(50))
    account_status = Column(String(50))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    event_metadata = relationship("CRMEventMetadata", back_populates="customer")


class CRMCaseContext(Base):
    """
    Case-related context from platform events
    Maps to crmContext in canonical model
    """
    __tablename__ = "crm_case_context"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), ForeignKey("crm_event_metadata.event_id"), nullable=False, index=True)
    
    # Case identification
    case_id = Column(String(100), index=True)
    case_number = Column(String(100), index=True)
    
    # Case details
    case_type = Column(String(100))
    case_status = Column(String(50))
    case_priority = Column(String(20))
    case_subject = Column(String(500))
    case_description = Column(Text)
    
    # Case ownership and assignment
    case_owner_id = Column(String(100))
    case_owner_name = Column(String(255))
    assigned_team = Column(String(100))
    
    # SLA information
    sla_target_hours = Column(Integer)
    sla_due_date = Column(DateTime(timezone=True))
    sla_breach_risk = Column(Boolean, default=False)
    
    # Case resolution
    resolution_code = Column(String(100))
    resolution_description = Column(Text)
    resolved_at = Column(DateTime(timezone=True))
    
    # Escalation tracking
    is_escalated = Column(Boolean, default=False)
    escalation_level = Column(Integer, default=0)
    escalated_at = Column(DateTime(timezone=True))
    escalation_reason = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    event_metadata = relationship("CRMEventMetadata", back_populates="case_context")


class CRMBusinessContext(Base):
    """
    Business context and additional metadata
    Maps to businessContext in canonical model
    """
    __tablename__ = "crm_business_context"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), ForeignKey("crm_event_metadata.event_id"), nullable=False, index=True)
    
    # Business identifiers
    business_unit = Column(String(100))
    region = Column(String(100))
    territory = Column(String(100))
    
    # Product/Service context
    product_line = Column(String(100))
    service_type = Column(String(100))
    contract_number = Column(String(100))
    
    # Financial context
    billing_amount = Column(Float)
    currency_code = Column(String(10))
    payment_terms = Column(String(100))
    
    # Compliance and regulatory
    regulatory_requirements = Column(JSON)
    compliance_flags = Column(JSON)
    
    # Additional metadata
    custom_fields = Column(JSON)
    tags = Column(JSON)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    event_metadata = relationship("CRMEventMetadata", back_populates="business_context")


class CRMEventStatus(Base):
    """
    Event processing status and lifecycle tracking
    Maps to status in canonical model
    """
    __tablename__ = "crm_event_status"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), ForeignKey("crm_event_metadata.event_id"), nullable=False, index=True)
    
    # Processing status
    current_status = Column(String(50), nullable=False, default="RECEIVED")
    previous_status = Column(String(50))
    status_changed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Processing metrics
    validation_passed = Column(Boolean, default=False)
    normalization_completed = Column(Boolean, default=False)
    persistence_completed = Column(Boolean, default=False)
    
    # Error tracking
    error_count = Column(Integer, default=0)
    last_error_message = Column(Text)
    last_error_at = Column(DateTime(timezone=True))
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True))
    
    # Downstream system status
    downstream_systems = Column(JSON)  # Track status per target system
    
    # Completion tracking
    completed_at = Column(DateTime(timezone=True))
    completion_duration_ms = Column(Integer)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    event_metadata = relationship("CRMEventMetadata", back_populates="event_status")


class CRMEventProcessingLog(Base):
    """
    Detailed processing log for audit and debugging
    """
    __tablename__ = "crm_event_processing_log"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(255), ForeignKey("crm_event_metadata.event_id"), nullable=False, index=True)
    
    # Log entry details
    log_level = Column(String(20), nullable=False)  # DEBUG, INFO, WARN, ERROR
    log_message = Column(Text, nullable=False)
    log_context = Column(JSON)  # Additional context data
    
    # Processing step
    processing_step = Column(String(100))  # validation, normalization, persistence, etc.
    step_duration_ms = Column(Integer)
    
    # Error details (if applicable)
    error_code = Column(String(50))
    error_details = Column(JSON)
    stack_trace = Column(Text)
    
    # Timestamp
    logged_at = Column(DateTime(timezone=True), server_default=func.now())


class SAPCaseMapping(Base):
    """
    Mapping table to store SAP case IDs for CRM cases
    Tracks integration status between CRM and SAP systems
    """
    __tablename__ = "sap_case_mapping"

    id = Column(Integer, primary_key=True, index=True)
    
    # CRM case reference
    crm_case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    crm_case_number = Column(String(100), nullable=False, index=True)
    
    # SAP case reference
    sap_case_id = Column(String(100), nullable=False, index=True)
    sap_case_number = Column(String(100), index=True)
    
    # Integration metadata
    integration_status = Column(String(50), nullable=False, default="PENDING")  # PENDING, SYNCED, FAILED, DELETED
    last_sync_operation = Column(String(20))  # CREATE, UPDATE, DELETE
    last_sync_at = Column(DateTime(timezone=True))
    last_sync_success = Column(Boolean, default=False)
    
    # MuleSoft correlation
    correlation_id = Column(String(255), index=True)
    mulesoft_transaction_id = Column(String(255))
    
    # Error tracking
    sync_error_count = Column(Integer, default=0)
    last_error_message = Column(Text)
    last_error_at = Column(DateTime(timezone=True))
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime(timezone=True))
    
    # Data consistency
    crm_last_modified = Column(DateTime(timezone=True))
    sap_last_modified = Column(DateTime(timezone=True))
    data_hash = Column(String(64))  # Hash of case data for change detection
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))
    
    # Relationships
    case = relationship("Case", backref="sap_mapping")


class SAPIntegrationLog(Base):
    """
    Detailed log of SAP integration activities
    Provides audit trail for all SAP synchronization operations
    """
    __tablename__ = "sap_integration_log"

    id = Column(Integer, primary_key=True, index=True)
    
    # Reference to case mapping
    case_mapping_id = Column(Integer, ForeignKey("sap_case_mapping.id"), nullable=False, index=True)
    
    # Integration operation details
    operation_type = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE, QUERY
    operation_status = Column(String(20), nullable=False)  # SUCCESS, FAILED, PENDING
    
    # Request/Response data
    request_payload = Column(JSON)
    response_payload = Column(JSON)
    
    # MuleSoft details
    mulesoft_endpoint = Column(String(255))
    mulesoft_method = Column(String(10))  # GET, POST, PUT, DELETE
    mulesoft_status_code = Column(Integer)
    mulesoft_response_time_ms = Column(Integer)
    
    # Error details
    error_code = Column(String(50))
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Correlation and tracing
    correlation_id = Column(String(255), index=True)
    trace_id = Column(String(255))
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    
    # User context
    initiated_by = Column(String(100))
    user_agent = Column(String(255))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case_mapping = relationship("SAPCaseMapping", backref="integration_logs")


class MulesoftRequest(Base):
    __tablename__ = "mulesoft_requests"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, index=True)
    name = Column(String(255), nullable=True)  # Store account name for create requests
    request_type = Column(String(50), nullable=False)  # create, update, delete
    status = Column(String(50), nullable=False, default="pending")  # pending, sent, approved, rejected, failed
    mulesoft_response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account", backref="mulesoft_requests")


class ServiceAppointment(Base):
    """
    Service Appointments for field service scheduling (Scenario 2)
    """
    __tablename__ = "service_appointments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_number = Column(String(50), unique=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)

    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    appointment_type = Column(String(50), default="Field Service")

    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(50), default="Scheduled")
    priority = Column(String(20), default="Normal")

    assigned_technician_id = Column(Integer, nullable=True)
    technician_name = Column(String(100), nullable=True)

    location = Column(String(255), nullable=True)
    required_skills = Column(String(255), nullable=True)
    required_parts = Column(Text, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account", backref="service_appointments")
    case = relationship("Case", backref="service_appointments")
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_appointments")


class SchedulingRequest(Base):
    """
    Track MuleSoft scheduling requests (Scenario 2)
    """
    __tablename__ = "scheduling_requests"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("service_appointments.id"), nullable=True, index=True)
    appointment_number = Column(String(50), nullable=True)

    request_type = Column(String(50), nullable=False)
    status = Column(String(50), default="PENDING")
    integration_status = Column(String(50), nullable=True)

    assigned_technician_id = Column(Integer, nullable=True)
    technician_name = Column(String(100), nullable=True)
    parts_available = Column(Boolean, default=True)
    parts_status = Column(Text, nullable=True)

    mulesoft_transaction_id = Column(String(255), nullable=True)
    correlation_id = Column(String(255), nullable=True)

    sap_hr_response = Column(Text, nullable=True)
    sap_inventory_response = Column(Text, nullable=True)

    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    appointment = relationship("ServiceAppointment", backref="scheduling_requests")
    requested_by = relationship("User", foreign_keys=[requested_by_id])


class WorkOrder(Base):
    """
    Work Orders for service requests (Scenario 3)
    """
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    work_order_number = Column(String(50), unique=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)

    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), default="Medium")
    service_type = Column(String(50), default="Warranty")
    product = Column(String(255), nullable=True)

    status = Column(String(50), default="PENDING")
    integration_status = Column(String(50), nullable=True)

    entitlement_verified = Column(Boolean, default=False)
    entitlement_type = Column(String(50), nullable=True)
    entitlement_end_date = Column(DateTime(timezone=True), nullable=True)

    sap_order_id = Column(String(100), nullable=True)
    sap_notification_id = Column(String(100), nullable=True)

    mulesoft_transaction_id = Column(String(255), nullable=True)
    correlation_id = Column(String(255), nullable=True)

    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    error_message = Column(Text, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account", backref="work_orders")
    case = relationship("Case", backref="work_orders")
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_work_orders")
    requested_by = relationship("User", foreign_keys=[requested_by_id])


class AppointmentRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AppointmentRequest(Base):
    """Appointment request awaiting approval via ServiceNow"""
    __tablename__ = "appointment_requests"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), nullable=False)
    requested_payload = Column(JSON, nullable=True)
    status = Column(String(50), default="PENDING")
    correlation_id = Column(String(255), nullable=True, index=True)
    servicenow_ticket_id = Column(String(255), nullable=True)
    servicenow_ticket_number = Column(String(255), nullable=True)
    sap_validation_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    requested_by = relationship("User", foreign_keys=[requested_by_id])


class WorkOrderRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ClientUser(Base):
    """Client portal users linked to Salesforce accounts"""
    __tablename__ = "client_users"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    password_expired = Column(Boolean, default=True)
    is_active = Column(Boolean, default=False)
    servicenow_ticket_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    account = relationship("Account", backref="client_users")


class WorkOrderRequest(Base):
    """Work order request awaiting approval via ServiceNow"""
    __tablename__ = "work_order_requests"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), nullable=False)
    requested_payload = Column(JSON, nullable=True)
    status = Column(String(50), default="PENDING")
    correlation_id = Column(String(255), nullable=True, index=True)
    servicenow_ticket_id = Column(String(255), nullable=True)
    servicenow_ticket_number = Column(String(255), nullable=True)
    sap_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    requested_by = relationship("User", foreign_keys=[requested_by_id])
