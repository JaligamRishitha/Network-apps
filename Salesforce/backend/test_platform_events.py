"""
Test script for Salesforce Platform Event processing
Demonstrates various event types and validation scenarios
"""
import requests
import json
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
PLATFORM_EVENTS_URL = f"{BASE_URL}/api/platform-events"

def generate_event_id():
    """Generate a unique event ID"""
    return str(uuid.uuid4())

def test_customer_billing_adjustment_event():
    """Test Customer Billing Adjustment Event"""
    event_payload = {
        "Event_UUID__c": generate_event_id(),
        "Event_Type__c": "CUSTOMER_BILLING_ADJUSTMENT",
        "Source_System__c": "Salesforce",
        "Event_Timestamp__c": datetime.utcnow().isoformat() + "Z",
        "Correlation_Id__c": "corr-ukpn-000123",
        "Severity__c": "HIGH",
        "Customer_Id__c": "0015g00000UKPN77",
        "Account_Id__c": "0015g00000UKPN77",
        "Billing_Account__c": "ISU-88901234",
        "Case_Id__c": "5005g00000CRM88",
        "Case_Type__c": "Billing Dispute",
        "Case_Status__c": "Escalated",
        "Priority__c": "P1",
        "SLA_Target_Hours__c": 48,
        "Target_System__c": "SAP_ISU",
        "Operation__c": "CREATE_BILLING_ADJUSTMENT",
        "Integration_Status__c": "IN_PROGRESS",
        "Billing_Amount__c": 1250.75,
        "Currency_Code__c": "USD",
        "Customer_Name__c": "UKPN Energy Solutions",
        "Customer_Email__c": "billing@ukpn.com"
    }
    
    print("Testing Customer Billing Adjustment Event...")
    response = requests.post(f"{PLATFORM_EVENTS_URL}/process", json=event_payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json().get("event_id")

def test_case_escalation_event():
    """Test Case Escalation Event"""
    event_payload = {
        "Event_UUID__c": generate_event_id(),
        "Event_Type__c": "CASE_ESCALATED",
        "Source_System__c": "Salesforce",
        "Event_Timestamp__c": datetime.utcnow().isoformat() + "Z",
        "Correlation_Id__c": "corr-case-escalation-001",
        "Severity__c": "CRITICAL",
        "Case_Id__c": "5005g00000ESCAL01",
        "Case_Number__c": "CASE-2025-001234",
        "Case_Type__c": "Technical Issue",
        "Case_Status__c": "Escalated",
        "Priority__c": "P1",
        "Case_Subject__c": "Critical system outage affecting multiple customers",
        "Case_Description__c": "Multiple customers reporting service disruption in the North region",
        "SLA_Target_Hours__c": 4,
        "SLA_Due_Date__c": (datetime.utcnow() + timedelta(hours=4)).isoformat() + "Z",
        "Customer_Id__c": "0015g00000CUST001",
        "Account_Id__c": "0015g00000CUST001",
        "Target_System__c": "ServiceNow",
        "Operation__c": "ESCALATE_CASE"
    }
    
    print("\nTesting Case Escalation Event...")
    response = requests.post(f"{PLATFORM_EVENTS_URL}/process", json=event_payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json().get("event_id")

def test_sla_breach_event():
    """Test SLA Breach Event"""
    event_payload = {
        "Event_UUID__c": generate_event_id(),
        "Event_Type__c": "SLA_BREACH",
        "Source_System__c": "Salesforce",
        "Event_Timestamp__c": datetime.utcnow().isoformat() + "Z",
        "Correlation_Id__c": "corr-sla-breach-001",
        "Severity__c": "CRITICAL",
        "Case_Id__c": "5005g00000SLA001",
        "Case_Number__c": "CASE-2025-005678",
        "Case_Type__c": "Service Request",
        "Case_Status__c": "Working",
        "Priority__c": "P2",
        "Case_Subject__c": "Service restoration request",
        "SLA_Target_Hours__c": 24,
        "SLA_Due_Date__c": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",  # Past due
        "Customer_Id__c": "0015g00000CUST002",
        "Account_Id__c": "0015g00000CUST002",
        "Customer_Name__c": "Enterprise Customer Ltd",
        "Target_System__c": "ServiceNow",
        "Operation__c": "SLA_BREACH_NOTIFICATION"
    }
    
    print("\nTesting SLA Breach Event...")
    response = requests.post(f"{PLATFORM_EVENTS_URL}/process", json=event_payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json().get("event_id")

def test_invalid_event():
    """Test Invalid Event (missing required fields)"""
    event_payload = {
        "Event_UUID__c": generate_event_id(),
        # Missing Event_Type__c
        "Source_System__c": "Salesforce",
        "Event_Timestamp__c": datetime.utcnow().isoformat() + "Z",
        "Severity__c": "LOW"
    }
    
    print("\nTesting Invalid Event (missing Event_Type__c)...")
    response = requests.post(f"{PLATFORM_EVENTS_URL}/process", json=event_payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_p1_without_sla():
    """Test P1 priority without SLA details (should fail validation)"""
    event_payload = {
        "Event_UUID__c": generate_event_id(),
        "Event_Type__c": "CASE_CREATED",
        "Source_System__c": "Salesforce",
        "Event_Timestamp__c": datetime.utcnow().isoformat() + "Z",
        "Severity__c": "HIGH",
        "Case_Id__c": "5005g00000P1TEST",
        "Priority__c": "P1"
        # Missing SLA_Target_Hours__c
    }
    
    print("\nTesting P1 Priority without SLA details...")
    response = requests.post(f"{PLATFORM_EVENTS_URL}/process", json=event_payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_duplicate_event():
    """Test Duplicate Event"""
    event_id = generate_event_id()
    
    event_payload = {
        "Event_UUID__c": event_id,
        "Event_Type__c": "CUSTOMER_CREATED",
        "Source_System__c": "Salesforce",
        "Event_Timestamp__c": datetime.utcnow().isoformat() + "Z",
        "Severity__c": "LOW",
        "Customer_Id__c": "0015g00000NEWCUST",
        "Customer_Name__c": "New Customer Inc"
    }
    
    print("\nTesting Duplicate Event...")
    
    # Send first event
    print("Sending first event...")
    response1 = requests.post(f"{PLATFORM_EVENTS_URL}/process", json=event_payload)
    print(f"First event - Status: {response1.status_code}")
    print(f"First event - Response: {response1.json()}")
    
    # Send duplicate event
    print("Sending duplicate event...")
    response2 = requests.post(f"{PLATFORM_EVENTS_URL}/process", json=event_payload)
    print(f"Duplicate event - Status: {response2.status_code}")
    print(f"Duplicate event - Response: {response2.json()}")

def get_event_status(event_id):
    """Get event status"""
    if not event_id:
        return
        
    print(f"\nGetting status for event: {event_id}")
    response = requests.get(f"{PLATFORM_EVENTS_URL}/status/{event_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Event Status: {response.json()}")
    else:
        print(f"Error: {response.text}")

def get_event_details(event_id):
    """Get detailed event information"""
    if not event_id:
        return
        
    print(f"\nGetting details for event: {event_id}")
    response = requests.get(f"{PLATFORM_EVENTS_URL}/events/{event_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        details = response.json()
        print("Event Details:")
        print(f"  Metadata: {details.get('metadata', {})}")
        print(f"  Customer: {details.get('customer', {})}")
        print(f"  Case Context: {details.get('case_context', {})}")
        print(f"  Business Context: {details.get('business_context', {})}")
        print(f"  Status: {details.get('status', {})}")
    else:
        print(f"Error: {response.text}")

def get_processing_metrics():
    """Get processing metrics"""
    print("\nGetting processing metrics...")
    response = requests.get(f"{PLATFORM_EVENTS_URL}/metrics?hours=1")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        metrics = response.json()
        print("Processing Metrics:")
        print(f"  Total Events: {metrics.get('total_events', 0)}")
        print(f"  Events by Type: {metrics.get('events_by_type', {})}")
        print(f"  Events by Status: {metrics.get('events_by_status', {})}")
        print(f"  Average Processing Time: {metrics.get('average_processing_time_ms', 0):.2f}ms")
        print(f"  Error Rate: {metrics.get('error_rate', 0):.2f}%")
    else:
        print(f"Error: {response.text}")

def test_batch_processing():
    """Test batch processing of multiple events"""
    events = [
        {
            "Event_UUID__c": generate_event_id(),
            "Event_Type__c": "CUSTOMER_CREATED",
            "Source_System__c": "Salesforce",
            "Event_Timestamp__c": datetime.utcnow().isoformat() + "Z",
            "Severity__c": "LOW",
            "Customer_Id__c": "0015g00000BATCH01",
            "Customer_Name__c": "Batch Customer 1"
        },
        {
            "Event_UUID__c": generate_event_id(),
            "Event_Type__c": "CUSTOMER_CREATED",
            "Source_System__c": "Salesforce",
            "Event_Timestamp__c": datetime.utcnow().isoformat() + "Z",
            "Severity__c": "LOW",
            "Customer_Id__c": "0015g00000BATCH02",
            "Customer_Name__c": "Batch Customer 2"
        },
        {
            "Event_UUID__c": generate_event_id(),
            "Event_Type__c": "INVALID_TYPE",  # This should fail
            "Source_System__c": "Salesforce",
            "Event_Timestamp__c": datetime.utcnow().isoformat() + "Z",
            "Severity__c": "LOW"
        }
    ]
    
    print("\nTesting Batch Processing...")
    response = requests.post(f"{PLATFORM_EVENTS_URL}/process-batch", json=events)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    print("=== Salesforce Platform Event Processing Tests ===\n")
    
    # Test valid events
    event_id_1 = test_customer_billing_adjustment_event()
    event_id_2 = test_case_escalation_event()
    event_id_3 = test_sla_breach_event()
    
    # Test validation failures
    test_invalid_event()
    test_p1_without_sla()
    
    # Test duplicate handling
    test_duplicate_event()
    
    # Test batch processing
    test_batch_processing()
    
    # Get event details
    get_event_status(event_id_1)
    get_event_details(event_id_1)
    
    # Get processing metrics
    get_processing_metrics()
    
    print("\n=== Tests Completed ===")