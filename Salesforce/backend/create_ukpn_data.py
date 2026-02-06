"""
Create UKPN (UK Power Networks) mock data for CRM system
"""
import os
import sys
from datetime import datetime, timedelta
import uuid
import random

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.db_models import (
    User, Account, Contact, Lead, Opportunity, Case,
    CRMEventMetadata, CRMCustomer, CRMCaseContext, 
    CRMBusinessContext, CRMEventStatus
)

def create_ukpn_data():
    """Create UKPN-specific mock data"""
    db = SessionLocal()
    
    try:
        print("Creating UKPN mock data...")
        
        # Get existing users for ownership
        users = db.query(User).all()
        if not users:
            print("No users found. Please create users first.")
            return
        
        # UKPN Accounts (Energy Distribution Companies and Large Customers)
        ukpn_accounts = [
            {
                "name": "UKPN Eastern Power Networks",
                "phone": "+44 800 316 3105",
                "website": "www.ukpowernetworks.co.uk",
                "industry": "Energy Distribution",
                "description": "Eastern region electricity distribution network operator covering Essex, Hertfordshire, Bedfordshire, Buckinghamshire, Oxfordshire and parts of London",
                "billing_address": "Newington House, 237 Southwark Bridge Road, London SE1 6NP"
            },
            {
                "name": "UKPN London Power Networks", 
                "phone": "+44 800 316 3105",
                "website": "www.ukpowernetworks.co.uk",
                "industry": "Energy Distribution",
                "description": "London electricity distribution network operator covering central and south London",
                "billing_address": "Newington House, 237 Southwark Bridge Road, London SE1 6NP"
            },
            {
                "name": "UKPN South Eastern Power Networks",
                "phone": "+44 800 316 3105", 
                "website": "www.ukpowernetworks.co.uk",
                "industry": "Energy Distribution",
                "description": "South Eastern region electricity distribution network operator covering Kent, Surrey, Sussex and parts of London",
                "billing_address": "Newington House, 237 Southwark Bridge Road, London SE1 6NP"
            },
            {
                "name": "Thames Water Utilities Ltd",
                "phone": "+44 800 980 8800",
                "website": "www.thameswater.co.uk", 
                "industry": "Water Utilities",
                "description": "Major water and wastewater services company serving London and Thames Valley",
                "billing_address": "Clearwater Court, Vastern Road, Reading RG1 8DB"
            },
            {
                "name": "Canary Wharf Group",
                "phone": "+44 20 7418 2000",
                "website": "www.canarywharf.com",
                "industry": "Commercial Real Estate",
                "description": "Major commercial property developer and manager in London's financial district",
                "billing_address": "One Canada Square, Canary Wharf, London E14 5AB"
            },
            {
                "name": "Heathrow Airport Holdings",
                "phone": "+44 844 335 1801",
                "website": "www.heathrow.com",
                "industry": "Aviation",
                "description": "Owner and operator of Heathrow Airport, major electricity consumer",
                "billing_address": "The Compass Centre, Nelson Road, Hounslow TW6 2GW"
            },
            {
                "name": "Tesco Stores Limited",
                "phone": "+44 800 505 555",
                "website": "www.tesco.com",
                "industry": "Retail",
                "description": "Major UK retailer with significant electricity consumption across store network",
                "billing_address": "Tesco House, Shire Park, Kestrel Way, Welwyn Garden City AL7 1GA"
            },
            {
                "name": "London Borough of Tower Hamlets",
                "phone": "+44 20 7364 5000",
                "website": "www.towerhamlets.gov.uk",
                "industry": "Local Government",
                "description": "Local authority with significant public infrastructure electricity requirements",
                "billing_address": "Town Hall, Mulberry Place, 5 Clove Crescent, London E14 2BG"
            }
        ]
        
        accounts = []
        for acc_data in ukpn_accounts:
            account = Account(**acc_data, owner_id=random.choice(users).id)
            db.add(account)
            accounts.append(account)
        
        db.commit()
        print(f"Created {len(accounts)} UKPN accounts")
        
        # UKPN Contacts (Key personnel at customer organizations)
        ukpn_contacts = [
            # UKPN Internal Contacts
            {"first_name": "Sarah", "last_name": "Mitchell", "title": "Network Operations Manager", "email": "sarah.mitchell@ukpowernetworks.co.uk", "phone": "+44 20 7654 3210", "account_id": accounts[0].id},
            {"first_name": "James", "last_name": "Thompson", "title": "Customer Services Director", "email": "james.thompson@ukpowernetworks.co.uk", "phone": "+44 20 7654 3211", "account_id": accounts[1].id},
            {"first_name": "Emma", "last_name": "Davies", "title": "Major Connections Manager", "email": "emma.davies@ukpowernetworks.co.uk", "phone": "+44 20 7654 3212", "account_id": accounts[2].id},
            
            # Customer Contacts
            {"first_name": "Michael", "last_name": "Roberts", "title": "Facilities Manager", "email": "michael.roberts@thameswater.co.uk", "phone": "+44 118 987 6543", "account_id": accounts[3].id},
            {"first_name": "Lisa", "last_name": "Chen", "title": "Energy Manager", "email": "lisa.chen@canarywharf.com", "phone": "+44 20 7418 2100", "account_id": accounts[4].id},
            {"first_name": "David", "last_name": "Wilson", "title": "Infrastructure Director", "email": "david.wilson@heathrow.com", "phone": "+44 20 8745 7000", "account_id": accounts[5].id},
            {"first_name": "Rachel", "last_name": "Brown", "title": "Property Services Manager", "email": "rachel.brown@tesco.com", "phone": "+44 1707 918 000", "account_id": accounts[6].id},
            {"first_name": "Andrew", "last_name": "Taylor", "title": "Head of Facilities", "email": "andrew.taylor@towerhamlets.gov.uk", "phone": "+44 20 7364 5100", "account_id": accounts[7].id}
        ]
        
        contacts = []
        for con_data in ukpn_contacts:
            contact = Contact(**con_data, owner_id=random.choice(users).id)
            db.add(contact)
            contacts.append(contact)
        
        db.commit()
        print(f"Created {len(contacts)} UKPN contacts")
        
        # UKPN Cases (Typical power network issues)
        ukpn_cases = [
            {
                "subject": "Planned Power Outage - Canary Wharf Substation Maintenance",
                "description": "Scheduled maintenance on primary substation serving Canary Wharf area. Customer notification and coordination required for 4-hour outage window.",
                "status": "Working",
                "priority": "High",
                "account_id": accounts[4].id,
                "contact_id": contacts[4].id,
                "sla_due_date": datetime.utcnow() + timedelta(hours=24)
            },
            {
                "subject": "Emergency Fault - Underground Cable Failure Thames Water Site",
                "description": "11kV underground cable fault affecting Thames Water pumping station. Emergency repair crew dispatched. Temporary supply being arranged.",
                "status": "Escalated", 
                "priority": "Critical",
                "account_id": accounts[3].id,
                "contact_id": contacts[3].id,
                "sla_due_date": datetime.utcnow() + timedelta(hours=2)
            },
            {
                "subject": "New Connection Request - Heathrow Terminal Expansion",
                "description": "Major new connection required for Heathrow Terminal 6 expansion project. 33kV supply with 15MVA capacity. Design and quotation phase.",
                "status": "New",
                "priority": "Medium", 
                "account_id": accounts[5].id,
                "contact_id": contacts[5].id,
                "sla_due_date": datetime.utcnow() + timedelta(days=14)
            },
            {
                "subject": "Voltage Quality Issue - Tesco Distribution Center",
                "description": "Customer reporting voltage fluctuations affecting refrigeration systems at main distribution center. Power quality investigation required.",
                "status": "Working",
                "priority": "High",
                "account_id": accounts[6].id,
                "contact_id": contacts[6].id,
                "sla_due_date": datetime.utcnow() + timedelta(hours=48)
            },
            {
                "subject": "Billing Dispute - Tower Hamlets Street Lighting",
                "description": "Local authority disputing electricity charges for street lighting. Meter readings and tariff verification required.",
                "status": "New",
                "priority": "Medium",
                "account_id": accounts[7].id,
                "contact_id": contacts[7].id,
                "sla_due_date": datetime.utcnow() + timedelta(days=7)
            },
            {
                "subject": "Storm Damage Assessment - Eastern Region",
                "description": "Post-storm damage assessment and repair prioritization across Eastern Power Networks region. Multiple overhead line faults reported.",
                "status": "Working",
                "priority": "Critical",
                "account_id": accounts[0].id,
                "contact_id": contacts[0].id,
                "sla_due_date": datetime.utcnow() + timedelta(hours=12)
            }
        ]
        
        cases = []
        for case_data in ukpn_cases:
            from app.crud import generate_case_number
            case = Case(
                **case_data,
                case_number=generate_case_number(),
                owner_id=random.choice(users).id
            )
            db.add(case)
            cases.append(case)
        
        db.commit()
        print(f"Created {len(cases)} UKPN cases")
        
        # UKPN Opportunities (Business development opportunities)
        ukpn_opportunities = [
            {
                "name": "Thames Water - Backup Power Solutions",
                "amount": 2500000.0,
                "stage": "Proposal",
                "probability": 75,
                "close_date": datetime.utcnow() + timedelta(days=45),
                "description": "Comprehensive backup power infrastructure for critical water treatment facilities",
                "account_id": accounts[3].id
            },
            {
                "name": "Canary Wharf - Smart Grid Integration",
                "amount": 1800000.0,
                "stage": "Negotiation", 
                "probability": 85,
                "close_date": datetime.utcnow() + timedelta(days=30),
                "description": "Advanced smart grid technology implementation for commercial district",
                "account_id": accounts[4].id
            },
            {
                "name": "Heathrow - Renewable Energy Connection",
                "amount": 5000000.0,
                "stage": "Qualification",
                "probability": 60,
                "close_date": datetime.utcnow() + timedelta(days=90),
                "description": "Large-scale renewable energy connection and grid reinforcement project",
                "account_id": accounts[5].id
            }
        ]
        
        opportunities = []
        for opp_data in ukpn_opportunities:
            opportunity = Opportunity(**opp_data, owner_id=random.choice(users).id)
            db.add(opportunity)
            opportunities.append(opportunity)
        
        db.commit()
        print(f"Created {len(opportunities)} UKPN opportunities")
        
        # UKPN Platform Events (Realistic power network events)
        ukpn_platform_events = [
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "CUSTOMER_BILLING_ADJUSTMENT",
                "event_source": "Salesforce",
                "event_timestamp": datetime.utcnow() - timedelta(hours=2),
                "correlation_id": "UKPN-BILL-2025-001",
                "severity": "HIGH",
                "target_system": "SAP_ISU",
                "operation": "CREATE_BILLING_ADJUSTMENT",
                "integration_status": "COMPLETED",
                "raw_payload": {
                    "Event_UUID__c": str(uuid.uuid4()),
                    "Event_Type__c": "CUSTOMER_BILLING_ADJUSTMENT",
                    "Customer_Id__c": "UKPN-CUST-001",
                    "Billing_Account__c": "ISU-UKPN-001",
                    "Billing_Amount__c": 15750.50,
                    "Currency_Code__c": "GBP",
                    "Adjustment_Reason__c": "Meter reading correction"
                }
            },
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "CASE_ESCALATED", 
                "event_source": "Salesforce",
                "event_timestamp": datetime.utcnow() - timedelta(hours=1),
                "correlation_id": "UKPN-ESC-2025-001",
                "severity": "CRITICAL",
                "target_system": "ServiceNow",
                "operation": "ESCALATE_CASE",
                "integration_status": "IN_PROGRESS",
                "raw_payload": {
                    "Event_UUID__c": str(uuid.uuid4()),
                    "Event_Type__c": "CASE_ESCALATED",
                    "Case_Id__c": cases[1].case_number if cases else "CASE-2025-001",
                    "Priority__c": "P1",
                    "SLA_Target_Hours__c": 2,
                    "Escalation_Reason__c": "Critical infrastructure failure"
                }
            },
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "SLA_BREACH",
                "event_source": "Salesforce", 
                "event_timestamp": datetime.utcnow() - timedelta(minutes=30),
                "correlation_id": "UKPN-SLA-2025-001",
                "severity": "CRITICAL",
                "target_system": "ServiceNow",
                "operation": "SLA_BREACH_NOTIFICATION",
                "integration_status": "PENDING",
                "raw_payload": {
                    "Event_UUID__c": str(uuid.uuid4()),
                    "Event_Type__c": "SLA_BREACH",
                    "Case_Id__c": cases[0].case_number if cases else "CASE-2025-002",
                    "SLA_Target_Hours__c": 24,
                    "Breach_Duration_Hours__c": 2.5,
                    "Impact_Level__c": "High"
                }
            }
        ]
        
        # Create platform event records
        for event_data in ukpn_platform_events:
            # Create metadata
            metadata = CRMEventMetadata(
                event_id=event_data["event_id"],
                event_type=event_data["event_type"],
                event_source=event_data["event_source"],
                event_timestamp=event_data["event_timestamp"],
                correlation_id=event_data["correlation_id"],
                severity=event_data["severity"],
                target_system=event_data["target_system"],
                operation=event_data["operation"],
                integration_status=event_data["integration_status"],
                raw_payload=event_data["raw_payload"]
            )
            db.add(metadata)
            
            # Create customer record for billing events
            if event_data["event_type"] == "CUSTOMER_BILLING_ADJUSTMENT":
                customer = CRMCustomer(
                    event_id=event_data["event_id"],
                    customer_id="UKPN-CUST-001",
                    billing_account="ISU-UKPN-001",
                    customer_name="Thames Water Utilities Ltd",
                    customer_email="billing@thameswater.co.uk",
                    customer_type="Commercial"
                )
                db.add(customer)
            
            # Create case context for case events
            if "CASE" in event_data["event_type"]:
                case_context = CRMCaseContext(
                    event_id=event_data["event_id"],
                    case_id=cases[0].case_number if cases else "CASE-2025-001",
                    case_type="Infrastructure",
                    case_status="Escalated" if "ESCALATED" in event_data["event_type"] else "Working",
                    case_priority="P1" if event_data["severity"] == "CRITICAL" else "P2",
                    sla_target_hours=2 if event_data["severity"] == "CRITICAL" else 24,
                    is_escalated="ESCALATED" in event_data["event_type"]
                )
                db.add(case_context)
            
            # Create business context
            business_context = CRMBusinessContext(
                event_id=event_data["event_id"],
                business_unit="UKPN Operations",
                region="London" if "London" in event_data.get("operation", "") else "Eastern",
                service_type="Electricity Distribution",
                billing_amount=event_data["raw_payload"].get("Billing_Amount__c"),
                currency_code=event_data["raw_payload"].get("Currency_Code__c", "GBP")
            )
            db.add(business_context)
            
            # Create event status
            event_status = CRMEventStatus(
                event_id=event_data["event_id"],
                current_status="PROCESSED",
                validation_passed=True,
                normalization_completed=True,
                persistence_completed=True,
                completed_at=datetime.utcnow()
            )
            db.add(event_status)
        
        db.commit()
        print(f"Created {len(ukpn_platform_events)} UKPN platform events")
        
        # UKPN Leads (Potential new customers)
        ukpn_leads = [
            {
                "first_name": "Jennifer",
                "last_name": "Williams",
                "company": "London City Airport",
                "title": "Operations Director",
                "email": "j.williams@londoncityairport.com",
                "phone": "+44 20 7646 0000",
                "status": "Qualified",
                "score": 85,
                "region": "London",
                "source": "Trade Show",
                "description": "Interested in backup power solutions for critical airport operations"
            },
            {
                "first_name": "Robert",
                "last_name": "Johnson",
                "company": "Westfield Shopping Centre",
                "title": "Facilities Manager", 
                "email": "r.johnson@westfield.com",
                "phone": "+44 20 8749 8000",
                "status": "Contacted",
                "score": 70,
                "region": "London",
                "source": "Website Inquiry",
                "description": "Exploring energy efficiency upgrades for retail complex"
            },
            {
                "first_name": "Amanda",
                "last_name": "Clarke",
                "company": "Queen Elizabeth Olympic Park",
                "title": "Energy Manager",
                "email": "a.clarke@queenelizabetholympicpark.co.uk", 
                "phone": "+44 20 3288 1800",
                "status": "New",
                "score": 60,
                "region": "London",
                "source": "Referral",
                "description": "Investigating renewable energy integration for park facilities"
            }
        ]
        
        leads = []
        for lead_data in ukpn_leads:
            lead = Lead(**lead_data, owner_id=random.choice(users).id)
            db.add(lead)
            leads.append(lead)
        
        db.commit()
        print(f"Created {len(leads)} UKPN leads")
        
        print("\n=== UKPN Mock Data Creation Summary ===")
        print(f"✅ Accounts: {len(accounts)}")
        print(f"✅ Contacts: {len(contacts)}")
        print(f"✅ Cases: {len(cases)}")
        print(f"✅ Opportunities: {len(opportunities)}")
        print(f"✅ Platform Events: {len(ukpn_platform_events)}")
        print(f"✅ Leads: {len(leads)}")
        print("\nUKPN CRM data created successfully!")
        
    except Exception as e:
        print(f"Error creating UKPN data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_ukpn_data()