from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import random

from . import db_models as models
from . import schemas
from . import crud


class AssignmentService:
    """Service for handling lead/case assignment rules."""

    def __init__(self, db: Session):
        self.db = db
        self._sales_pool: List[int] = []
        self._pool_index = 0

    def get_sales_pool(self) -> List[int]:
        """Get list of sales user IDs for round-robin assignment."""
        if not self._sales_pool:
            users = self.db.query(models.User).filter(
                models.User.role == "user",
                models.User.is_active == True
            ).all()
            self._sales_pool = [u.id for u in users]
        return self._sales_pool

    def round_robin_assign(self) -> Optional[int]:
        """Get next user in round-robin rotation."""
        pool = self.get_sales_pool()
        if not pool:
            return None
        user_id = pool[self._pool_index % len(pool)]
        self._pool_index += 1
        return user_id

    def apply_lead_assignment(self, lead: models.Lead) -> int:
        """
        Apply assignment rules to a lead.
        Rules:
        - High score leads (>= 80) go to top performers
        - Leads from specific regions go to regional reps
        - Default: round-robin assignment
        """
        # If lead already has an owner, keep it
        if lead.owner_id:
            return lead.owner_id

        # High score leads - assign to first available user (simulating top performer)
        if lead.score and lead.score >= 80:
            pool = self.get_sales_pool()
            if pool:
                return pool[0]

        # Region-based assignment could be added here
        # For now, use round-robin
        return self.round_robin_assign()

    def apply_case_assignment(self, case: models.Case) -> int:
        """
        Apply assignment rules to a case.
        Rules:
        - Critical cases go to senior reps
        - Default: round-robin assignment
        """
        if case.owner_id:
            return case.owner_id

        # Critical priority - assign to first available (simulating senior rep)
        if case.priority == "Critical":
            pool = self.get_sales_pool()
            if pool:
                return pool[0]

        return self.round_robin_assign()


class LeadConversionService:
    """Service for converting leads to accounts, contacts, and opportunities."""

    def __init__(self, db: Session):
        self.db = db

    def convert_lead(
        self,
        lead_id: int,
        conversion_data: schemas.LeadConvert,
        user_id: int
    ) -> Tuple[Optional[models.Account], Optional[models.Contact], Optional[models.Opportunity]]:
        """
        Convert a lead to account, contact, and optionally opportunity.
        Returns tuple of (account, contact, opportunity).
        """
        lead = crud.get_lead(self.db, lead_id)
        if not lead:
            raise ValueError("Lead not found")

        if lead.is_converted:
            raise ValueError("Lead already converted")

        account = None
        contact = None
        opportunity = None
        owner_id = conversion_data.owner_id or lead.owner_id or user_id

        # Create Account
        if conversion_data.create_account:
            account_name = conversion_data.account_name or lead.company or f"{lead.full_name} Account"
            account_data = schemas.AccountCreate(
                name=account_name,
                phone=lead.phone,
                owner_id=owner_id
            )
            account = crud.create_account(self.db, account_data)

        # Create Contact
        contact_data = schemas.ContactCreate(
            first_name=lead.first_name,
            last_name=lead.last_name,
            account_id=account.id if account else None,
            title=lead.title,
            phone=lead.phone,
            email=lead.email,
            owner_id=owner_id
        )
        contact = crud.create_contact(self.db, contact_data)

        # Create Opportunity
        if conversion_data.create_opportunity:
            opp_name = conversion_data.opportunity_name or f"{lead.company or lead.full_name} - Opportunity"
            opp_data = schemas.OpportunityCreate(
                name=opp_name,
                account_id=account.id if account else None,
                amount=conversion_data.opportunity_amount or 0,
                stage="Qualification",
                owner_id=owner_id
            )
            opportunity = crud.create_opportunity(self.db, opp_data)

        # Mark lead as converted
        lead.is_converted = True
        lead.status = "Converted"
        lead.converted_account_id = account.id if account else None
        lead.converted_contact_id = contact.id if contact else None
        lead.converted_opportunity_id = opportunity.id if opportunity else None
        self.db.commit()

        # Create activity log
        crud.create_activity(
            self.db,
            schemas.ActivityCreate(
                record_type="lead",
                record_id=lead_id,
                activity_type="conversion",
                subject="Lead Converted",
                details=f"Lead converted to Contact: {contact.id}" +
                       (f", Account: {account.id}" if account else "") +
                       (f", Opportunity: {opportunity.id}" if opportunity else "")
            ),
            user_id
        )

        return account, contact, opportunity


class CaseEscalationService:
    """Service for handling case SLA and escalation."""

    def __init__(self, db: Session):
        self.db = db

    def check_sla_breach(self, case: models.Case) -> bool:
        """Check if a case has breached its SLA."""
        if not case.sla_due_date:
            return False
        return datetime.utcnow() > case.sla_due_date

    def escalate_case(self, case_id: int, user_id: int) -> models.Case:
        """Manually escalate a case."""
        case = crud.get_case(self.db, case_id)
        if not case:
            raise ValueError("Case not found")

        case.is_escalated = True
        case.escalated_at = datetime.utcnow()
        case.status = "Escalated"
        self.db.commit()

        # Create activity log
        crud.create_activity(
            self.db,
            schemas.ActivityCreate(
                record_type="case",
                record_id=case_id,
                activity_type="escalation",
                subject="Case Escalated",
                details="Case was manually escalated"
            ),
            user_id
        )

        return case

    def check_and_escalate_overdue_cases(self) -> List[models.Case]:
        """Check all cases and escalate those that have breached SLA."""
        overdue_cases = self.db.query(models.Case).filter(
            models.Case.is_escalated == False,
            models.Case.status.notin_(["Closed"]),
            models.Case.sla_due_date < datetime.utcnow()
        ).all()

        escalated = []
        for case in overdue_cases:
            case.is_escalated = True
            case.escalated_at = datetime.utcnow()
            case.status = "Escalated"
            escalated.append(case)

        if escalated:
            self.db.commit()

        return escalated


class CaseMergeService:
    """Service for merging duplicate cases."""

    def __init__(self, db: Session):
        self.db = db

    def merge_cases(
        self,
        case_ids: List[int],
        master_case_id: int,
        user_id: int
    ) -> models.Case:
        """
        Merge multiple cases into a master case.
        The master case keeps all its data, and duplicate cases are closed.
        """
        if master_case_id not in case_ids:
            raise ValueError("Master case must be in the list of cases to merge")

        if len(case_ids) < 2:
            raise ValueError("Need at least 2 cases to merge")

        master_case = crud.get_case(self.db, master_case_id)
        if not master_case:
            raise ValueError("Master case not found")

        # Close duplicate cases
        merged_details = []
        for case_id in case_ids:
            if case_id == master_case_id:
                continue

            case = crud.get_case(self.db, case_id)
            if case:
                # Add activity to master case with merged case info
                merged_details.append(f"Case {case.case_number}: {case.subject}")

                # Close the duplicate case
                case.status = "Closed"
                case.description = f"{case.description or ''}\n\n[Merged into {master_case.case_number}]"

        self.db.commit()

        # Log activity on master case
        crud.create_activity(
            self.db,
            schemas.ActivityCreate(
                record_type="case",
                record_id=master_case_id,
                activity_type="merge",
                subject="Cases Merged",
                details=f"Merged cases:\n" + "\n".join(merged_details)
            ),
            user_id
        )

        return master_case


class DuplicateDetectionService:
    """Service for detecting potential duplicate records."""

    def __init__(self, db: Session):
        self.db = db

    def check_contact_duplicates(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> schemas.DuplicateWarning:
        """Check for duplicate contacts by email or phone."""
        duplicates = crud.check_contact_duplicates(self.db, email, phone)
        matching_records = []

        for c in duplicates:
            matching_records.append({
                "id": c.id,
                "name": c.full_name,
                "email": c.email,
                "phone": c.phone
            })

        return schemas.DuplicateWarning(
            field="email" if email else "phone",
            value=email or phone or "",
            matching_records=matching_records
        )

    def check_lead_duplicates(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> schemas.DuplicateWarning:
        """Check for duplicate leads by email or phone."""
        duplicates = crud.check_lead_duplicates(self.db, email, phone)
        matching_records = []

        for l in duplicates:
            matching_records.append({
                "id": l.id,
                "name": l.full_name,
                "email": l.email,
                "phone": l.phone,
                "company": l.company
            })

        return schemas.DuplicateWarning(
            field="email" if email else "phone",
            value=email or phone or "",
            matching_records=matching_records
        )
