from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    user = "user"


class LeadStatus(str, Enum):
    new = "New"
    contacted = "Contacted"
    qualified = "Qualified"
    unqualified = "Unqualified"
    converted = "Converted"


class CaseStatus(str, Enum):
    new = "New"
    working = "Working"
    escalated = "Escalated"
    closed = "Closed"


class CasePriority(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class OpportunityStage(str, Enum):
    prospecting = "Prospecting"
    qualification = "Qualification"
    needs_analysis = "Needs Analysis"
    proposal = "Proposal"
    negotiation = "Negotiation"
    closed_won = "Closed Won"
    closed_lost = "Closed Lost"


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    alias: Optional[str] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None


# Account Schemas
class AccountBase(BaseModel):
    name: str
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    billing_address: Optional[str] = None


class AccountCreate(AccountBase):
    owner_id: Optional[int] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    billing_address: Optional[str] = None
    owner_id: Optional[int] = None


class AccountResponse(AccountBase):
    id: int
    owner_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    owner_alias: Optional[str] = None
    # Request/audit details (latest related request, if any)
    request_id: Optional[int] = None
    request_status: Optional[str] = None
    servicenow_ticket_id: Optional[str] = None
    integration_status: Optional[str] = None
    correlation_id: Optional[str] = None

    class Config:
        from_attributes = True


class AccountRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class AccountRequestResponse(BaseModel):
    id: int
    name: str
    status: AccountRequestStatus
    auto_approved: bool = False
    correlation_id: Optional[str] = None
    requested_by_id: int
    approved_by_id: Optional[int] = None
    servicenow_ticket_id: Optional[str] = None
    servicenow_status: Optional[str] = None
    mulesoft_transaction_id: Optional[str] = None
    integration_status: Optional[str] = None
    error_message: Optional[str] = None
    created_account_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccountCreateResult(BaseModel):
    """
    Unified response for account creation flows:
    - manager/admin: `account` is set and flow is auto-create
    - user: `request` is set and flow is pending approval
    """
    flow: str
    account: Optional[AccountResponse] = None
    request: Optional[AccountRequestResponse] = None


class MuleSoftAccountCallback(BaseModel):
    """
    Callback payload MuleSoft can send back to Salesforce.
    """
    accepted: bool = True
    status: Optional[str] = None
    message: Optional[str] = None


# Contact Schemas
class ContactBase(BaseModel):
    first_name: Optional[str] = None
    last_name: str
    title: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    mailing_address: Optional[str] = None


class ContactCreate(ContactBase):
    account_id: Optional[int] = None
    owner_id: Optional[int] = None


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    account_id: Optional[int] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    mailing_address: Optional[str] = None
    owner_id: Optional[int] = None


class ContactResponse(ContactBase):
    id: int
    account_id: Optional[int]
    owner_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    full_name: Optional[str] = None
    account_name: Optional[str] = None
    owner_alias: Optional[str] = None

    class Config:
        from_attributes = True


# Lead Schemas
class LeadBase(BaseModel):
    first_name: Optional[str] = None
    last_name: str
    company: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    status: str = "New"
    score: int = 0
    region: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None


class LeadCreate(LeadBase):
    owner_id: Optional[int] = None


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[str] = None
    score: Optional[int] = None
    region: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None


class LeadResponse(LeadBase):
    id: int
    owner_id: Optional[int]
    is_converted: bool
    created_at: datetime
    updated_at: Optional[datetime]
    full_name: Optional[str] = None
    owner_alias: Optional[str] = None

    class Config:
        from_attributes = True


class LeadConvert(BaseModel):
    create_account: bool = True
    create_opportunity: bool = True
    account_name: Optional[str] = None
    opportunity_name: Optional[str] = None
    opportunity_amount: Optional[float] = None
    owner_id: Optional[int] = None


# Opportunity Schemas
class OpportunityBase(BaseModel):
    name: str
    amount: float = 0
    stage: str = "Prospecting"
    probability: int = 0
    close_date: Optional[datetime] = None
    description: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    account_id: Optional[int] = None
    owner_id: Optional[int] = None


class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    account_id: Optional[int] = None
    amount: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    close_date: Optional[datetime] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None


class OpportunityResponse(OpportunityBase):
    id: int
    account_id: Optional[int]
    owner_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    account_name: Optional[str] = None
    owner_alias: Optional[str] = None

    class Config:
        from_attributes = True


# Case Schemas
class CaseBase(BaseModel):
    subject: str
    description: Optional[str] = None
    status: str = "New"
    priority: str = "Medium"


class CaseCreate(CaseBase):
    account_id: Optional[int] = None
    contact_id: Optional[int] = None
    owner_id: Optional[int] = None


class CaseUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    account_id: Optional[int] = None
    contact_id: Optional[int] = None
    owner_id: Optional[int] = None


class CaseResponse(CaseBase):
    id: int
    case_number: str
    account_id: Optional[int]
    contact_id: Optional[int]
    owner_id: Optional[int]
    is_escalated: bool
    escalated_at: Optional[datetime]
    sla_due_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    account_name: Optional[str] = None
    contact_name: Optional[str] = None
    owner_alias: Optional[str] = None

    class Config:
        from_attributes = True


class CaseMerge(BaseModel):
    case_ids: List[int]
    master_case_id: int


# Activity Schemas
class ActivityBase(BaseModel):
    record_type: str
    record_id: int
    activity_type: str
    subject: Optional[str] = None
    details: Optional[str] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityResponse(ActivityBase):
    id: int
    created_by: Optional[int]
    created_at: datetime
    created_by_name: Optional[str] = None

    class Config:
        from_attributes = True


# Search Schemas
class SearchResult(BaseModel):
    record_type: str
    record_id: int
    name: str
    subtitle: Optional[str] = None
    icon: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int


# List Response
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


# Recent Records
class RecentRecordResponse(BaseModel):
    id: int
    record_type: str
    record_id: int
    record_name: str
    accessed_at: datetime

    class Config:
        from_attributes = True


# Dashboard Stats
class DashboardStats(BaseModel):
    leads_count: int
    opportunities_count: int
    contacts_count: int
    cases_by_priority: dict
    recent_records: List[RecentRecordResponse]


# Duplicate Check
class DuplicateWarning(BaseModel):
    field: str
    value: str
    matching_records: List[dict]
