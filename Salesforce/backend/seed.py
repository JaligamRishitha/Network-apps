"""
Seed script to populate the database with demo data.
Run with: python seed.py
"""
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.db_models import User, Account, Contact, Lead, Opportunity, Case
from app.auth import get_password_hash
from datetime import datetime, timedelta
import random


def seed_database():
    # Create tables
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).first():
            print("Database already seeded. Skipping...")
            return

        print("Seeding database...")

        # Create users
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            role="admin"
        )
        db.add(admin)

        sales_rep1 = User(
            username="stalin",
            email="stalin@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Stalin",
            last_name="Johnson",
            role="user"
        )
        db.add(sales_rep1)

        sales_rep2 = User(
            username="sarah",
            email="sarah@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Sarah",
            last_name="Williams",
            role="user"
        )
        db.add(sales_rep2)

        sales_rep3 = User(
            username="mike",
            email="mike@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Mike",
            last_name="Davis",
            role="user"
        )
        db.add(sales_rep3)

        db.commit()

        users = [sales_rep1, sales_rep2, sales_rep3]

        # Create sample accounts
        accounts_data = [
            {"name": "Acme Corporation", "phone": "555-0100", "website": "www.acme.com", "industry": "Technology"},
            {"name": "Global Industries", "phone": "555-0101", "website": "www.global.com", "industry": "Manufacturing"},
            {"name": "Tech Solutions Ltd", "phone": "555-0102", "website": "www.techsol.com", "industry": "Technology"},
            {"name": "Sunrise Healthcare", "phone": "555-0103", "website": "www.sunrise.com", "industry": "Healthcare"},
            {"name": "Metro Financial", "phone": "555-0104", "website": "www.metrofin.com", "industry": "Finance"},
        ]

        accounts = []
        for acc_data in accounts_data:
            account = Account(**acc_data, owner_id=random.choice(users).id)
            db.add(account)
            accounts.append(account)

        db.commit()

        # Create sample contacts
        contacts_data = [
            {"first_name": "John", "last_name": "Smith", "title": "CEO", "email": "john.smith@acme.com", "phone": "555-1001"},
            {"first_name": "Emily", "last_name": "Johnson", "title": "CFO", "email": "emily.j@global.com", "phone": "555-1002"},
            {"first_name": "David", "last_name": "Brown", "title": "CTO", "email": "david.b@techsol.com", "phone": "555-1003"},
            {"first_name": "Lisa", "last_name": "Anderson", "title": "VP Sales", "email": "lisa.a@sunrise.com", "phone": "555-1004"},
            {"first_name": "Robert", "last_name": "Wilson", "title": "Director", "email": "robert.w@metrofin.com", "phone": "555-1005"},
            {"first_name": "Jennifer", "last_name": "Taylor", "title": "Manager", "email": "jen.t@acme.com", "phone": "555-1006"},
            {"first_name": "Michael", "last_name": "Lee", "title": "Engineer", "email": "mike.l@techsol.com", "phone": "555-1007"},
        ]

        for i, con_data in enumerate(contacts_data):
            contact = Contact(
                **con_data,
                account_id=accounts[i % len(accounts)].id,
                owner_id=random.choice(users).id
            )
            db.add(contact)

        db.commit()

        # Create sample leads
        leads_data = [
            {"first_name": "Alex", "last_name": "Martinez", "company": "StartupX", "title": "Founder", "email": "alex@startupx.com", "phone": "555-2001", "status": "New", "score": 85},
            {"first_name": "Chris", "last_name": "Thompson", "company": "InnovateCo", "title": "CEO", "email": "chris@innovateco.com", "phone": "555-2002", "status": "Contacted", "score": 65},
            {"first_name": "Amanda", "last_name": "White", "company": "GrowthLabs", "title": "VP", "email": "amanda@growthlabs.com", "phone": "555-2003", "status": "Qualified", "score": 90},
            {"first_name": "Brian", "last_name": "Garcia", "company": "DataDriven", "title": "Director", "email": "brian@datadriven.com", "phone": "555-2004", "status": "New", "score": 45},
            {"first_name": "Nicole", "last_name": "Clark", "company": "CloudFirst", "title": "CTO", "email": "nicole@cloudfirst.com", "phone": "555-2005", "status": "Contacted", "score": 70},
        ]

        for lead_data in leads_data:
            lead = Lead(**lead_data, owner_id=random.choice(users).id)
            db.add(lead)

        db.commit()

        # Create sample opportunities
        stages = ["Prospecting", "Qualification", "Needs Analysis", "Proposal", "Negotiation"]
        opps_data = [
            {"name": "Acme Enterprise Deal", "amount": 150000, "stage": "Proposal"},
            {"name": "Global Industries Expansion", "amount": 75000, "stage": "Qualification"},
            {"name": "Tech Solutions Partnership", "amount": 250000, "stage": "Negotiation"},
            {"name": "Healthcare Software License", "amount": 50000, "stage": "Needs Analysis"},
            {"name": "Financial Services Integration", "amount": 100000, "stage": "Prospecting"},
        ]

        for i, opp_data in enumerate(opps_data):
            opp = Opportunity(
                **opp_data,
                account_id=accounts[i % len(accounts)].id,
                owner_id=random.choice(users).id,
                close_date=datetime.utcnow() + timedelta(days=random.randint(30, 90))
            )
            db.add(opp)

        db.commit()

        # Create sample cases
        priorities = ["Low", "Medium", "High", "Critical"]
        statuses = ["New", "Working", "Escalated"]
        cases_data = [
            {"subject": "Login issues reported", "description": "Multiple users unable to login", "priority": "High", "status": "Working"},
            {"subject": "Feature request: Dark mode", "description": "Customer requested dark mode option", "priority": "Low", "status": "New"},
            {"subject": "Data sync error", "description": "Data not syncing properly between systems", "priority": "Critical", "status": "Escalated"},
            {"subject": "Billing inquiry", "description": "Question about invoice", "priority": "Medium", "status": "New"},
            {"subject": "Performance degradation", "description": "System running slow during peak hours", "priority": "High", "status": "Working"},
        ]

        for i, case_data in enumerate(cases_data):
            from app.crud import generate_case_number
            case = Case(
                **case_data,
                case_number=generate_case_number(),
                account_id=accounts[i % len(accounts)].id,
                owner_id=random.choice(users).id,
                sla_due_date=datetime.utcnow() + timedelta(hours=random.choice([4, 8, 24, 48]))
            )
            db.add(case)

        db.commit()

        print("Database seeded successfully!")
        print("\nDemo accounts:")
        print("  Admin: admin / admin123")
        print("  User:  stalin / password123")
        print("  User:  sarah / password123")
        print("  User:  mike / password123")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
