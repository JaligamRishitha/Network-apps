"""
Test script for electricity load request integration
Demonstrates MuleSoft integration with JSON and XML payloads
"""
import requests
import json

# Base URL - adjust if needed
BASE_URL = "http://localhost:8000/api/integration"

# Sample JSON payload
json_payload = {
    "RequestID": "SF-REQ-10021",
    "CustomerID": "CUST-88991",
    "CurrentLoad": 5,
    "RequestedLoad": 10,
    "ConnectionType": "RESIDENTIAL",
    "City": "Hyderabad",
    "PinCode": "500081"
}

# Sample XML payload
xml_payload = """<ElectricityLoadRequest>
    <RequestID>SF-REQ-10022</RequestID>
    <CustomerID>CUST-88992</CustomerID>
    <CurrentLoad>10</CurrentLoad>
    <RequestedLoad>25</RequestedLoad>
    <ConnectionType>COMMERCIAL</ConnectionType>
    <City>Bangalore</City>
    <PinCode>560001</PinCode>
</ElectricityLoadRequest>"""


def test_json_endpoint():
    """Test JSON endpoint"""
    print("=" * 60)
    print("Testing JSON Endpoint: POST /api/integration/mulesoft/load-request")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/mulesoft/load-request",
            json=json_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ Request processed successfully!")
            print(f"  - PM Ticket: {data['tickets_created']['pm_ticket']}")
            print(f"  - FI Ticket: {data['tickets_created']['fi_ticket']}")
            print(f"  - MM Ticket: {data['tickets_created']['mm_ticket']}")
            print(f"  - Estimated Cost: ₹{data['estimated_cost']:,.2f}")
            print(f"  - Priority: {data['priority']}")
        
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to backend. Is the server running?")
    except Exception as e:
        print(f"✗ Error: {e}")


def test_xml_endpoint():
    """Test XML endpoint"""
    print("\n" + "=" * 60)
    print("Testing XML Endpoint: POST /api/integration/mulesoft/load-request/xml")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/mulesoft/load-request/xml",
            data=xml_payload,
            headers={"Content-Type": "application/xml"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ Request processed successfully!")
            print(f"  - PM Ticket: {data['tickets_created']['pm_ticket']}")
            print(f"  - FI Ticket: {data['tickets_created']['fi_ticket']}")
            print(f"  - MM Ticket: {data['tickets_created']['mm_ticket']}")
            print(f"  - Estimated Cost: ₹{data['estimated_cost']:,.2f}")
            print(f"  - Priority: {data['priority']}")
        
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to backend. Is the server running?")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("\n🔌 Electricity Load Request Integration Test\n")
    
    test_json_endpoint()
    test_xml_endpoint()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
