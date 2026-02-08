from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from models import UserRole, IncidentPriority, IncidentStatus, TicketType, TicketStatus, ApprovalStatus

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.user

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class IncidentBase(BaseModel):
    title: str
    description: str
    priority: IncidentPriority = IncidentPriority.medium

class IncidentCreate(IncidentBase):
    pass

class IncidentResponse(IncidentBase):
    id: int
    status: IncidentStatus
    reporter_id: int
    assigned_to_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ServiceCatalogItemResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    created_at: datetime

    class Config:
        from_attributes = True

class KnowledgeArticleBase(BaseModel):
    title: str
    content: str
    summary: str
    category: str
    tags: str

class KnowledgeArticleCreate(KnowledgeArticleBase):
    pass

class KnowledgeArticleResponse(KnowledgeArticleBase):
    id: int
    author_id: int
    views: int
    helpful_votes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TicketBase(BaseModel):
    title: str
    description: str
    ticket_type: TicketType = TicketType.service_request
    priority: IncidentPriority = IncidentPriority.medium
    category: Optional[str] = None
    subcategory: Optional[str] = None
    contact_number: Optional[str] = None
    preferred_contact: str = "email"
    urgency: str = "medium"
    business_justification: Optional[str] = None
    estimated_cost: Optional[str] = None

class TicketCreate(TicketBase):
    # Salesforce integration fields (optional)
    correlation_id: Optional[str] = None
    source_system: Optional[str] = None
    source_request_id: Optional[str] = None
    source_request_type: Optional[str] = None

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[IncidentPriority] = None
    assigned_to_id: Optional[int] = None
    resolution_notes: Optional[str] = None

class TicketResponse(TicketBase):
    id: int
    ticket_number: str
    status: TicketStatus
    requester_id: int
    assigned_to_id: Optional[int] = None
    correlation_id: Optional[str] = None
    source_system: Optional[str] = None
    source_request_id: Optional[str] = None
    source_request_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    requester_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    # ServiceNow integration fields
    servicenow_sys_id: Optional[str] = None
    servicenow_number: Optional[str] = None

    class Config:
        from_attributes = True

class ApprovalBase(BaseModel):
    comments: Optional[str] = None

class ApprovalCreate(ApprovalBase):
    ticket_id: int
    approver_id: int

class ApprovalUpdate(BaseModel):
    status: ApprovalStatus
    comments: Optional[str] = None

class ApprovalResponse(ApprovalBase):
    id: int
    ticket_id: int
    approver_id: int
    status: ApprovalStatus
    approved_at: Optional[datetime] = None
    created_at: datetime               
    ticket_number: Optional[str] = None                  
    ticket_title: Optional[str] = None
    requester_name: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str


# ============================================================================
# ASSIGNMENT GROUP SCHEMAS
# ============================================================================

class AssignmentGroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    email: Optional[str] = None


class AssignmentGroupCreate(AssignmentGroupBase):
    manager_id: Optional[int] = None


class AssignmentGroupResponse(AssignmentGroupBase):
    id: int
    manager_id: Optional[int] = None
    is_active: str
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = None

    class Config:
        from_attributes = True


class AssignmentGroupMemberCreate(BaseModel):
    group_id: int
    user_id: int


class AssignmentGroupMemberResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    is_active: str
    assignment_count: int
    last_assigned_at: Optional[datetime] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True


class CategoryAssignmentMappingCreate(BaseModel):
    category: str
    subcategory: Optional[str] = None
    group_id: int
    priority_override: Optional[str] = None


class CategoryAssignmentMappingResponse(BaseModel):
    id: int
    category: str
    subcategory: Optional[str] = None
    group_id: int
    priority_override: Optional[str] = None
    group_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SLA SCHEMAS
# ============================================================================

class SLADefinitionBase(BaseModel):
    name: str
    description: Optional[str] = None
    priority: str
    category: Optional[str] = None
    response_time_minutes: int = 60
    resolution_time_hours: int = 24
    business_hours_only: str = "true"
    warning_threshold_percent: int = 80


class SLADefinitionCreate(SLADefinitionBase):
    pass


class SLADefinitionResponse(SLADefinitionBase):
    id: int
    is_active: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketSLAResponse(BaseModel):
    id: int
    ticket_id: int
    sla_definition_id: int
    status: str
    response_due_at: datetime
    response_met_at: Optional[datetime] = None
    response_breached: str
    resolution_due_at: datetime
    resolution_met_at: Optional[datetime] = None
    resolution_breached: str
    warning_sent: str
    breach_notified: str
    created_at: datetime
    updated_at: datetime
    # Computed fields
    ticket_number: Optional[str] = None
    sla_name: Optional[str] = None
    time_to_response_breach_minutes: Optional[int] = None
    time_to_resolution_breach_minutes: Optional[int] = None

    class Config:
        from_attributes = True


class SLABreachResponse(BaseModel):
    ticket_id: int
    ticket_number: str
    title: str
    priority: str
    sla_type: str  # response or resolution
    due_at: datetime
    breached_at: Optional[datetime] = None
    minutes_overdue: int
    assigned_to: Optional[str] = None
    assignment_group: Optional[str] = None


# ============================================================================
# NOTIFICATION SCHEMAS
# ============================================================================

class NotificationBase(BaseModel):
    notification_type: str
    subject: str
    message: str
    recipient_email: Optional[str] = None
    webhook_url: Optional[str] = None


class NotificationCreate(NotificationBase):
    recipient_id: Optional[int] = None
    recipient_group_id: Optional[int] = None
    ticket_id: Optional[int] = None
    sla_id: Optional[int] = None
    webhook_payload: Optional[str] = None


class NotificationResponse(NotificationBase):
    id: int
    status: str
    recipient_id: Optional[int] = None
    recipient_group_id: Optional[int] = None
    ticket_id: Optional[int] = None
    sla_id: Optional[int] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# AUTO-CREATE TICKET SCHEMAS
# ============================================================================

class AutoCreateTicketRequest(BaseModel):
    """Request schema for auto-creating tickets from system events"""
    event_type: str
    source_system: str
    title: str
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    priority: str = "medium"
    assignment_group: str
    ticket_type: str = "incident"
    sla_hours: int = 24
    affected_user: Optional[str] = None
    affected_ci: Optional[str] = None
    metadata: Optional[dict] = None
    requires_approval: bool = False
    auto_assign: bool = True
    event_id: Optional[str] = None
    callback_url: Optional[str] = None


class AutoCreateTicketResponse(BaseModel):
    """Response schema for auto-created tickets"""
    ticket_id: int
    ticket_number: str
    title: str
    category: str
    subcategory: Optional[str] = None
    priority: str
    status: str
    assignment_group: Optional[str] = None
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    sla_response_due: Optional[datetime] = None
    sla_resolution_due: Optional[datetime] = None
    created_at: datetime
    event_id: Optional[str] = None
    message: str

    class Config:
        from_attributes = True