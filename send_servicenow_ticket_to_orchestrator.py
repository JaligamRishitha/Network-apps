#!/usr/bin/env python3
"""
Send ServiceNow tickets to the Ticket Orchestrator
This simulates ServiceNow's webhook or can be used to manually forward tickets
"""

import httpx
import asyncio
import json
from datetime import datetime

ORCHESTRATOR_URL = "http://localhost:2486"
SERVICENOW_URL = "http://149.102.158.71:4780"

async def fetch_servicenow_tickets():
    """Fetch open incidents from ServiceNow"""
    try:
        # First, get auth token
        async with httpx.AsyncClient() as client:
            # Login to get token
            login_response = await client.post(
                f"{SERVICENOW_URL}/token",
                data={"username": "admin", "password": "admin123"},
                timeout=30.0
            )
            login_response.raise_for_status()
            token = login_response.json().get("access_token")

            # Get incidents with token
            response = await client.get(
                f"{SERVICENOW_URL}/api/servicenow/incidents",
                params={
                    "limit": 10,
                    "skip": 0
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

            # Handle both direct array and result object
            if isinstance(data, list):
                return data
            return data.get("result", [])
    except Exception as e:
        print(f"Error fetching tickets from ServiceNow: {e}")
        return []

async def send_ticket_to_orchestrator(ticket):
    """Send a single ticket to the orchestrator"""
    # Transform ServiceNow ticket to orchestrator format
    orchestrator_ticket = {
        "sys_id": ticket.get("sys_id", ""),
        "number": ticket.get("number", ""),
        "short_description": ticket.get("short_description", ""),
        "description": ticket.get("description", ""),
        "priority": ticket.get("priority", "3"),
        "state": ticket.get("state", "1"),
        "assigned_to": ticket.get("assigned_to", ""),
        "category": ticket.get("category", ""),
        "subcategory": ticket.get("subcategory", "")
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/api/webhook/servicenow",
                json=orchestrator_ticket,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            print(f"✅ Sent ticket {ticket['number']} to orchestrator")
            print(f"   Category: {result['category']}")
            print(f"   Auto-resolve: {result['auto_resolve']}")
            print(f"   Orchestration ID: {result['orchestration_ticket_id']}")
            print(f"   Message: {result['message']}\n")

            return result
    except Exception as e:
        print(f"❌ Failed to send ticket {ticket.get('number', 'UNKNOWN')}: {e}\n")
        return None

async def send_all_open_tickets():
    """Fetch all open tickets from ServiceNow and send to orchestrator"""
    print("🔍 Fetching open tickets from ServiceNow...\n")

    tickets = await fetch_servicenow_tickets()

    if not tickets:
        print("No open tickets found in ServiceNow.")
        return

    print(f"Found {len(tickets)} open tickets. Sending to orchestrator...\n")

    results = []
    for ticket in tickets:
        result = await send_ticket_to_orchestrator(ticket)
        if result:
            results.append(result)
        await asyncio.sleep(0.5)  # Small delay between tickets

    print(f"\n📊 Summary:")
    print(f"   Total tickets sent: {len(results)}")
    print(f"   Auto-resolve: {sum(1 for r in results if r['auto_resolve'])}")
    print(f"   Manual intervention: {sum(1 for r in results if not r['auto_resolve'])}")

async def send_single_test_ticket():
    """Send a single test ticket for testing"""
    test_ticket = {
        "sys_id": "test_" + datetime.now().strftime("%Y%m%d%H%M%S"),
        "number": "INC" + datetime.now().strftime("%Y%m%d%H%M%S"),
        "short_description": "Password reset needed for user john.doe@example.com",
        "description": "User john.doe@example.com cannot login to Salesforce. Need to reset password.",
        "priority": "3",
        "state": "2",
        "assigned_to": "",
        "category": "User Account",
        "subcategory": "Password Reset"
    }

    print("📤 Sending test ticket to orchestrator...\n")
    result = await send_ticket_to_orchestrator(test_ticket)

    if result:
        print("\n✅ Test successful!")

async def main():
    print("=" * 60)
    print("ServiceNow → Orchestrator Ticket Forwarder")
    print("=" * 60)
    print()

    print("Options:")
    print("1. Send all open ServiceNow tickets to orchestrator")
    print("2. Send a single test ticket")
    print()

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        await send_all_open_tickets()
    elif choice == "2":
        await send_single_test_ticket()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())
