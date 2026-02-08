from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, desc
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import uuid

from . import db_models as models
from . import schemas
from .auth import get_password_hash


# User CRUD
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        avatar_url=user.avatar_url
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Account CRUD
def get_account(db: Session, account_id: int) -> Optional[models.Account]:
    return db.query(models.Account).options(
        joinedload(models.Account.owner)
    ).filter(models.Account.id == account_id).first()


def get_accounts(
    db: Session,
    skip: int = 0,
    limit: int = 25,
    search: Optional[str] = None,
    owner_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[models.Account], int]:
    query = db.query(models.Account).options(joinedload(models.Account.owner)).distinct()

    # Only show accounts that have a linked creation request (any status)
    # or legacy accounts with no request at all
    pending_only_request_exists = (
        db.query(models.AccountCreationRequest.id)
        .filter(
            models.AccountCreationRequest.created_account_id == models.Account.id,
            models.AccountCreationRequest.status == models.AccountRequestStatus.PENDING.value,
        )
        .exists()
    )
    query = query.filter(~pending_only_request_exists)

    if search:
        query = query.filter(
            or_(
                models.Account.name.ilike(f"%{search}%"),
                models.Account.phone.ilike(f"%{search}%")
            )
        )

    if owner_id:
        query = query.filter(models.Account.owner_id == owner_id)

    total = query.count()

    if sort_order == "desc":
        query = query.order_by(desc(getattr(models.Account, sort_by, models.Account.created_at)))
    else:
        query = query.order_by(getattr(models.Account, sort_by, models.Account.created_at))

    accounts = query.offset(skip).limit(limit).all()
    # Deduplicate by ID (in case of any join-related duplicates)
    seen_ids = set()
    unique_accounts = []
    for account in accounts:
        if account.id not in seen_ids:
            seen_ids.add(account.id)
            unique_accounts.append(account)
    return unique_accounts, total


def create_account(db: Session, account: schemas.AccountCreate) -> models.Account:
    db_account = models.Account(**account.model_dump())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def create_account_request(
    db: Session,
    account: schemas.AccountCreate,
    requested_by: models.User,
    status: str = models.AccountRequestStatus.PENDING.value,
    auto_approved: bool = False,
) -> models.AccountCreationRequest:
    payload = account.model_dump()
    correlation_id = str(uuid.uuid4())
    request = models.AccountCreationRequest(
        name=payload.get("name"),
        requested_payload=payload,
        status=status,
        auto_approved=auto_approved,
        correlation_id=correlation_id,
        requested_by_id=requested_by.id,
        integration_status="PENDING",
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def get_account_request(db: Session, request_id: int) -> Optional[models.AccountCreationRequest]:
    return (
        db.query(models.AccountCreationRequest)
        .options(
            joinedload(models.AccountCreationRequest.requested_by),
            joinedload(models.AccountCreationRequest.approved_by),
            joinedload(models.AccountCreationRequest.created_account),
        )
        .filter(models.AccountCreationRequest.id == request_id)
        .first()
    )


def list_account_requests(
    db: Session,
    status: Optional[str] = None,
    requested_by_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[models.AccountCreationRequest], int]:
    query = db.query(models.AccountCreationRequest).options(
        joinedload(models.AccountCreationRequest.requested_by),
        joinedload(models.AccountCreationRequest.approved_by),
        joinedload(models.AccountCreationRequest.created_account),
    )

    if status:
        query = query.filter(models.AccountCreationRequest.status == status)
    if requested_by_id:
        query = query.filter(models.AccountCreationRequest.requested_by_id == requested_by_id)

    total = query.count()
    items = query.order_by(desc(models.AccountCreationRequest.created_at)).offset(skip).limit(limit).all()
    return items, total


def update_account_request_integration(
    db: Session,
    request: models.AccountCreationRequest,
    *,
    servicenow_ticket_id: Optional[str] = None,
    servicenow_status: Optional[str] = None,
    mulesoft_transaction_id: Optional[str] = None,
    integration_status: Optional[str] = None,
    error_message: Optional[str] = None,
) -> models.AccountCreationRequest:
    if servicenow_ticket_id is not None:
        request.servicenow_ticket_id = servicenow_ticket_id
    if servicenow_status is not None:
        request.servicenow_status = servicenow_status
    if mulesoft_transaction_id is not None:
        request.mulesoft_transaction_id = mulesoft_transaction_id
    if integration_status is not None:
        request.integration_status = integration_status
    if error_message is not None:
        request.error_message = error_message

    db.commit()
    db.refresh(request)
    return request


def complete_account_request_with_account(
    db: Session,
    request: models.AccountCreationRequest,
    account: models.Account,
    approver: models.User,
) -> models.AccountCreationRequest:
    request.status = models.AccountRequestStatus.COMPLETED.value
    request.approved_by_id = approver.id
    request.created_account_id = account.id
    request.integration_status = "COMPLETED"
    db.commit()
    db.refresh(request)
    
    # Create MuleSoft tracking request when account is created
    mulesoft_request = models.MulesoftRequest(
        account_id=account.id,
        request_type="create",
        status="approved",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(mulesoft_request)
    db.commit()
    
    return request


def fail_account_request(
    db: Session,
    request: models.AccountCreationRequest,
    error_message: str,
) -> models.AccountCreationRequest:
    request.status = models.AccountRequestStatus.FAILED.value
    request.integration_status = "FAILED"
    request.error_message = error_message
    db.commit()
    db.refresh(request)
    return request


def reject_account_request(
    db: Session,
    request: models.AccountCreationRequest,
    approver: models.User,
    reason: Optional[str] = None,
) -> models.AccountCreationRequest:
    request.status = models.AccountRequestStatus.REJECTED.value
    request.approved_by_id = approver.id
    request.integration_status = "REJECTED"
    if reason:
        request.error_message = reason
    db.commit()
    db.refresh(request)
    return request


def delete_account_request(db: Session, request_id: int) -> bool:
    request = db.query(models.AccountCreationRequest).filter(models.AccountCreationRequest.id == request_id).first()
    if request:
        db.delete(request)
        db.commit()
        return True
    return False


def delete_account_requests_by_name(db: Session, names: list[str]) -> int:
    """Delete account requests by name. Returns count of deleted records."""
    requests = db.query(models.AccountCreationRequest).filter(
        models.AccountCreationRequest.name.in_(names)
    ).all()
    count = len(requests)
    for req in requests:
        db.delete(req)
    db.commit()
    return count


def update_account(db: Session, account_id: int, account: schemas.AccountUpdate) -> Optional[models.Account]:
    db_account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if db_account:
        update_data = account.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_account, key, value)
        db.commit()
        db.refresh(db_account)
    return db_account


def delete_account(db: Session, account_id: int) -> bool:
    db_account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if db_account:
        db.delete(db_account)
        db.commit()
        return True
    return False


# Contact CRUD
def get_contact(db: Session, contact_id: int) -> Optional[models.Contact]:
    return db.query(models.Contact).options(
        joinedload(models.Contact.owner),
        joinedload(models.Contact.account)
    ).filter(models.Contact.id == contact_id).first()


def get_contacts(
    db: Session,
    skip: int = 0,
    limit: int = 25,
    search: Optional[str] = None,
    owner_id: Optional[int] = None,
    account_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[models.Contact], int]:
    query = db.query(models.Contact).options(
        joinedload(models.Contact.owner),
        joinedload(models.Contact.account)
    )

    if search:
        query = query.filter(
            or_(
                models.Contact.first_name.ilike(f"%{search}%"),
                models.Contact.last_name.ilike(f"%{search}%"),
                models.Contact.email.ilike(f"%{search}%"),
                models.Contact.phone.ilike(f"%{search}%")
            )
        )

    if owner_id:
        query = query.filter(models.Contact.owner_id == owner_id)

    if account_id:
        query = query.filter(models.Contact.account_id == account_id)

    total = query.count()

    if sort_order == "desc":
        query = query.order_by(desc(getattr(models.Contact, sort_by, models.Contact.created_at)))
    else:
        query = query.order_by(getattr(models.Contact, sort_by, models.Contact.created_at))

    contacts = query.offset(skip).limit(limit).all()
    return contacts, total


def create_contact(db: Session, contact: schemas.ContactCreate) -> models.Contact:
    db_contact = models.Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def update_contact(db: Session, contact_id: int, contact: schemas.ContactUpdate) -> Optional[models.Contact]:
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if db_contact:
        update_data = contact.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, contact_id: int) -> bool:
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if db_contact:
        db.delete(db_contact)
        db.commit()
        return True
    return False


def check_contact_duplicates(db: Session, email: Optional[str], phone: Optional[str]) -> List[models.Contact]:
    if not email and not phone:
        return []

    query = db.query(models.Contact)
    filters = []

    if email:
        filters.append(models.Contact.email == email)
    if phone:
        filters.append(models.Contact.phone == phone)

    return query.filter(or_(*filters)).limit(5).all()


# Lead CRUD
def get_lead(db: Session, lead_id: int) -> Optional[models.Lead]:
    return db.query(models.Lead).options(
        joinedload(models.Lead.owner)
    ).filter(models.Lead.id == lead_id).first()


def get_leads(
    db: Session,
    skip: int = 0,
    limit: int = 25,
    search: Optional[str] = None,
    owner_id: Optional[int] = None,
    status: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[models.Lead], int]:
    query = db.query(models.Lead).options(joinedload(models.Lead.owner))

    # Exclude converted leads by default
    query = query.filter(models.Lead.is_converted == False)

    if search:
        query = query.filter(
            or_(
                models.Lead.first_name.ilike(f"%{search}%"),
                models.Lead.last_name.ilike(f"%{search}%"),
                models.Lead.email.ilike(f"%{search}%"),
                models.Lead.company.ilike(f"%{search}%"),
                models.Lead.phone.ilike(f"%{search}%")
            )
        )

    if owner_id:
        query = query.filter(models.Lead.owner_id == owner_id)

    if status:
        query = query.filter(models.Lead.status == status)

    total = query.count()

    if sort_order == "desc":
        query = query.order_by(desc(getattr(models.Lead, sort_by, models.Lead.created_at)))
    else:
        query = query.order_by(getattr(models.Lead, sort_by, models.Lead.created_at))

    leads = query.offset(skip).limit(limit).all()
    return leads, total


def create_lead(db: Session, lead: schemas.LeadCreate) -> models.Lead:
    db_lead = models.Lead(**lead.model_dump())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


def update_lead(db: Session, lead_id: int, lead: schemas.LeadUpdate) -> Optional[models.Lead]:
    db_lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if db_lead:
        update_data = lead.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_lead, key, value)
        db.commit()
        db.refresh(db_lead)
    return db_lead


def delete_lead(db: Session, lead_id: int) -> bool:
    db_lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if db_lead:
        db.delete(db_lead)
        db.commit()
        return True
    return False


def check_lead_duplicates(db: Session, email: Optional[str], phone: Optional[str]) -> List[models.Lead]:
    if not email and not phone:
        return []

    query = db.query(models.Lead).filter(models.Lead.is_converted == False)
    filters = []

    if email:
        filters.append(models.Lead.email == email)
    if phone:
        filters.append(models.Lead.phone == phone)

    return query.filter(or_(*filters)).limit(5).all()


# Opportunity CRUD
def get_opportunity(db: Session, opportunity_id: int) -> Optional[models.Opportunity]:
    return db.query(models.Opportunity).options(
        joinedload(models.Opportunity.owner),
        joinedload(models.Opportunity.account)
    ).filter(models.Opportunity.id == opportunity_id).first()


def get_opportunities(
    db: Session,
    skip: int = 0,
    limit: int = 25,
    search: Optional[str] = None,
    owner_id: Optional[int] = None,
    account_id: Optional[int] = None,
    stage: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[models.Opportunity], int]:
    query = db.query(models.Opportunity).options(
        joinedload(models.Opportunity.owner),
        joinedload(models.Opportunity.account)
    )

    if search:
        query = query.filter(models.Opportunity.name.ilike(f"%{search}%"))

    if owner_id:
        query = query.filter(models.Opportunity.owner_id == owner_id)

    if account_id:
        query = query.filter(models.Opportunity.account_id == account_id)

    if stage:
        query = query.filter(models.Opportunity.stage == stage)

    total = query.count()

    if sort_order == "desc":
        query = query.order_by(desc(getattr(models.Opportunity, sort_by, models.Opportunity.created_at)))
    else:
        query = query.order_by(getattr(models.Opportunity, sort_by, models.Opportunity.created_at))

    opportunities = query.offset(skip).limit(limit).all()
    return opportunities, total


def create_opportunity(db: Session, opportunity: schemas.OpportunityCreate) -> models.Opportunity:
    db_opportunity = models.Opportunity(**opportunity.model_dump())
    db.add(db_opportunity)
    db.commit()
    db.refresh(db_opportunity)
    return db_opportunity


def update_opportunity(db: Session, opportunity_id: int, opportunity: schemas.OpportunityUpdate) -> Optional[models.Opportunity]:
    db_opportunity = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if db_opportunity:
        update_data = opportunity.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_opportunity, key, value)
        db.commit()
        db.refresh(db_opportunity)
    return db_opportunity


def delete_opportunity(db: Session, opportunity_id: int) -> bool:
    db_opportunity = db.query(models.Opportunity).filter(models.Opportunity.id == opportunity_id).first()
    if db_opportunity:
        db.delete(db_opportunity)
        db.commit()
        return True
    return False


# Case CRUD
def generate_case_number() -> str:
    return f"CS-{uuid.uuid4().hex[:8].upper()}"


def get_case(db: Session, case_id: int) -> Optional[models.Case]:
    return db.query(models.Case).options(
        joinedload(models.Case.owner),
        joinedload(models.Case.account),
        joinedload(models.Case.contact)
    ).filter(models.Case.id == case_id).first()


def get_cases(
    db: Session,
    skip: int = 0,
    limit: int = 25,
    search: Optional[str] = None,
    owner_id: Optional[int] = None,
    account_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[models.Case], int]:
    query = db.query(models.Case).options(
        joinedload(models.Case.owner),
        joinedload(models.Case.account),
        joinedload(models.Case.contact)
    )

    if search:
        query = query.filter(
            or_(
                models.Case.case_number.ilike(f"%{search}%"),
                models.Case.subject.ilike(f"%{search}%")
            )
        )

    if owner_id:
        query = query.filter(models.Case.owner_id == owner_id)

    if account_id:
        query = query.filter(models.Case.account_id == account_id)

    if status:
        query = query.filter(models.Case.status == status)

    if priority:
        query = query.filter(models.Case.priority == priority)

    total = query.count()

    if sort_order == "desc":
        query = query.order_by(desc(getattr(models.Case, sort_by, models.Case.created_at)))
    else:
        query = query.order_by(getattr(models.Case, sort_by, models.Case.created_at))

    cases = query.offset(skip).limit(limit).all()
    return cases, total


def get_cases_by_priority(db: Session, owner_id: Optional[int] = None) -> dict:
    query = db.query(
        models.Case.priority,
        func.count(models.Case.id)
    ).filter(models.Case.status != "Closed")

    if owner_id:
        query = query.filter(models.Case.owner_id == owner_id)

    result = query.group_by(models.Case.priority).all()
    return {priority: count for priority, count in result}


def create_case(db: Session, case: schemas.CaseCreate) -> models.Case:
    case_data = case.model_dump()
    case_data["case_number"] = generate_case_number()

    # Set SLA based on priority
    sla_hours = {"Critical": 4, "High": 8, "Medium": 24, "Low": 48}
    priority = case_data.get("priority", "Medium")
    case_data["sla_due_date"] = datetime.utcnow() + timedelta(hours=sla_hours.get(priority, 24))

    db_case = models.Case(**case_data)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


def update_case(db: Session, case_id: int, case: schemas.CaseUpdate) -> Optional[models.Case]:
    db_case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if db_case:
        update_data = case.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_case, key, value)
        db.commit()
        db.refresh(db_case)
    return db_case


def delete_case(db: Session, case_id: int) -> bool:
    db_case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if db_case:
        db.delete(db_case)
        db.commit()
        return True
    return False


# Activity CRUD
def get_activities(
    db: Session,
    record_type: str,
    record_id: int,
    skip: int = 0,
    limit: int = 50
) -> List[models.Activity]:
    return db.query(models.Activity).options(
        joinedload(models.Activity.created_by_user)
    ).filter(
        models.Activity.record_type == record_type,
        models.Activity.record_id == record_id
    ).order_by(desc(models.Activity.created_at)).offset(skip).limit(limit).all()


def create_activity(db: Session, activity: schemas.ActivityCreate, user_id: int) -> models.Activity:
    db_activity = models.Activity(**activity.model_dump(), created_by=user_id)
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity


# Recent Records
def add_recent_record(
    db: Session,
    user_id: int,
    record_type: str,
    record_id: int,
    record_name: str
):
    # Check if record already exists
    existing = db.query(models.RecentRecord).filter(
        models.RecentRecord.user_id == user_id,
        models.RecentRecord.record_type == record_type,
        models.RecentRecord.record_id == record_id
    ).first()

    if existing:
        existing.accessed_at = datetime.utcnow()
        existing.record_name = record_name
    else:
        db_record = models.RecentRecord(
            user_id=user_id,
            record_type=record_type,
            record_id=record_id,
            record_name=record_name
        )
        db.add(db_record)

    db.commit()

    # Keep only last 20 recent records per user
    recent_ids = db.query(models.RecentRecord.id).filter(
        models.RecentRecord.user_id == user_id
    ).order_by(desc(models.RecentRecord.accessed_at)).limit(20).subquery()

    db.query(models.RecentRecord).filter(
        models.RecentRecord.user_id == user_id,
        ~models.RecentRecord.id.in_(recent_ids)
    ).delete(synchronize_session=False)
    db.commit()


def get_recent_records(db: Session, user_id: int, limit: int = 10) -> List[models.RecentRecord]:
    return db.query(models.RecentRecord).filter(
        models.RecentRecord.user_id == user_id
    ).order_by(desc(models.RecentRecord.accessed_at)).limit(limit).all()


# Global Search
def global_search(db: Session, query: str, limit: int = 20) -> List[schemas.SearchResult]:
    results = []

    # Search Contacts
    contacts = db.query(models.Contact).filter(
        or_(
            models.Contact.first_name.ilike(f"%{query}%"),
            models.Contact.last_name.ilike(f"%{query}%"),
            models.Contact.email.ilike(f"%{query}%")
        )
    ).limit(5).all()

    for c in contacts:
        results.append(schemas.SearchResult(
            record_type="contact",
            record_id=c.id,
            name=f"{c.first_name or ''} {c.last_name}".strip(),
            subtitle=c.email,
            icon="contact"
        ))

    # Search Accounts
    accounts = db.query(models.Account).filter(
        models.Account.name.ilike(f"%{query}%")
    ).limit(5).all()

    for a in accounts:
        results.append(schemas.SearchResult(
            record_type="account",
            record_id=a.id,
            name=a.name,
            subtitle=a.phone,
            icon="account"
        ))

    # Search Leads
    leads = db.query(models.Lead).filter(
        models.Lead.is_converted == False,
        or_(
            models.Lead.first_name.ilike(f"%{query}%"),
            models.Lead.last_name.ilike(f"%{query}%"),
            models.Lead.company.ilike(f"%{query}%"),
            models.Lead.email.ilike(f"%{query}%")
        )
    ).limit(5).all()

    for l in leads:
        results.append(schemas.SearchResult(
            record_type="lead",
            record_id=l.id,
            name=f"{l.first_name or ''} {l.last_name}".strip(),
            subtitle=l.company,
            icon="lead"
        ))

    # Search Opportunities
    opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.name.ilike(f"%{query}%")
    ).limit(5).all()

    for o in opportunities:
        results.append(schemas.SearchResult(
            record_type="opportunity",
            record_id=o.id,
            name=o.name,
            subtitle=o.stage,
            icon="opportunity"
        ))

    # Search Cases
    cases = db.query(models.Case).filter(
        or_(
            models.Case.case_number.ilike(f"%{query}%"),
            models.Case.subject.ilike(f"%{query}%")
        )
    ).limit(5).all()

    for cs in cases:
        results.append(schemas.SearchResult(
            record_type="case",
            record_id=cs.id,
            name=cs.case_number,
            subtitle=cs.subject,
            icon="case"
        ))

    return results[:limit]
