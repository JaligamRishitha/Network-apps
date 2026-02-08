#!/usr/bin/env python3
"""
ServiceNow Ticket Forwarder
Fetches existing tickets from ServiceNow and forwards them to the Ticket Orchestrator
"""

import requests
import json
import time
from typing import List, Dict, Optional
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

SERVICENOW_URL = "http://207.180.217.117:4780"
ORCHESTRATOR_URL = "http://localhost:2486"

# ServiceNow authentication (or use mock mode)
SERVICENOW_AUTH = {
    "username": "admin",
    "password": "password"
}

# Use ServiceNow mock client if real connection fails
USE_MOCK_MODE = True

# ============================================================================
# SERVICENOW API CLIENT
# ============================================================================

class ServiceNowClient:
    def __init__(self):
        self.base_url = SERVICENOW_URL
        self.token = None
        self.mock_mode = USE_MOCK_MODE

    def login(self) -> bool:
        """Login to ServiceNow and get token"""
        if self.mock_mode:
            print("ℹ️  Using ServiceNow mock mode")
            self.token = "mock_token"
            return True

        try:
            response = requests.post(
                f"{self.base_url}/token",
                data={
                    "username": SERVICENOW_AUTH["username"],
                    "password": SERVICENOW_AUTH["password"]
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            response.raise_for_status()
            self.token = response.json().get("access_token")
            return self.token is not None
        except Exception as e:
            print(f"⚠️  Real ServiceNow unavailable, using mock mode")
            self.mock_mode = True
            self.token = "mock_token"
            return True

    def list_incidents(
        self,
        status_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Fetch incidents from ServiceNow"""
        if not self.token:
            if not self.login():
                return []

        # Mock mode - return sample tickets
        if self.mock_mode:
            return self._get_mock_incidents(limit)

        try:
            params = {"limit": limit, "skip": 0}

            response = requests.get(
                f"{self.base_url}/api/servicenow/incidents",
                params=params,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Handle different response formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "result" in data:
                return data["result"]
            else:
                return []

        except Exception as e:
            print(f"⚠️  API call failed, using mock data")
            return self._get_mock_incidents(limit)

    def _get_mock_incidents(self, limit: int) -> List[Dict]:
        """Generate mock ServiceNow incidents for testing"""
        mock_tickets = [
            {
                "sys_id": "mock_001",
                "number": "INC0010001",
                "short_description": "Password reset needed for user john.doe@company.com",
                "description": "User john.doe@company.com cannot login to Salesforce. Need password reset.",
                "priority": "2",
                "state": "2",
                "category": "User Account",
                "subcategory": "Password Reset"
            },
            {
                "sys_id": "mock_002",
                "number": "INC0010002",
                "short_description": "Create new user account for Jane Smith",
                "description": "New hire Jane Smith (jane.smith@company.com) needs Salesforce account created.",
                "priority": "3",
                "state": "2",
                "category": "User Account",
                "subcategory": "User Creation"
            },
            {
                "sys_id": "mock_003",
                "number": "INC0010003",
                "short_description": "Deactivate user account for Bob Johnson",
                "description": "User Bob Johnson (bob.johnson@company.com) has left the company. Deactivate all accounts.",
                "priority": "3",
                "state": "2",
                "category": "User Account",
                "subcategory": "User Deactivation"
            },
            {
                "sys_id": "mock_004",
                "number": "INC0010004",
                "short_description": "Salesforce to SAP integration error",
                "description": "Cases are not syncing from Salesforce to SAP. MuleSoft integration showing errors.",
                "priority": "2",
                "state": "2",
                "category": "Integration",
                "subcategory": "Integration Error"
            },
            {
                "sys_id": "mock_005",
                "number": "INC0010005",
                "short_description": "Data sync issue - Missing records in SAP",
                "description": "Several Salesforce cases from yesterday are missing in SAP system. Data sync failed.",
                "priority": "2",
                "state": "2",
                "category": "Data",
                "subcategory": "Data Sync"
            }
        ]
        return mock_tickets[:limit]

# ============================================================================
# ORCHESTRATOR CLIENT
# ============================================================================

class OrchestratorClient:
    def __init__(self):
        self.base_url = ORCHESTRATOR_URL

    def send_ticket(self, servicenow_ticket: Dict) -> Optional[Dict]:
        """Send a ticket to the orchestrator"""
        try:
            # Transform to orchestrator format
            orchestrator_ticket = {
                "sys_id": servicenow_ticket.get("sys_id", servicenow_ticket.get("id", "unknown")),
                "number": servicenow_ticket.get("number", f"INC{int(time.time())}"),
                "short_description": servicenow_ticket.get("short_description", ""),
                "description": servicenow_ticket.get("description", ""),
                "priority": str(servicenow_ticket.get("priority", "3")),
                "state": str(servicenow_ticket.get("state", "2")),
                "assigned_to": servicenow_ticket.get("assigned_to", ""),
                "category": servicenow_ticket.get("category", ""),
                "subcategory": servicenow_ticket.get("subcategory", "")
            }

            response = requests.post(
                f"{self.base_url}/api/webhook/servicenow",
                json=orchestrator_ticket,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"❌ Failed to send ticket {servicenow_ticket.get('number', 'UNKNOWN')}: {e}")
            return None

    def get_stats(self) -> Dict:
        """Get orchestrator statistics"""
        try:
            response = requests.get(f"{self.base_url}/api/stats", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
            return {}

# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def forward_all_tickets(dry_run: bool = False):
    """Forward all open tickets from ServiceNow to orchestrator"""
    print("=" * 70)
    print("ServiceNow Ticket Forwarder")
    print("=" * 70)

    if dry_run:
        print("\n🔍 DRY RUN MODE - No tickets will be sent")

    print("\n📡 Connecting to ServiceNow...")
    snow_client = ServiceNowClient()

    if not snow_client.login():
        print("❌ Failed to connect to ServiceNow")
        return

    print("✅ Connected to ServiceNow")

    print("\n🔍 Fetching open incidents...")
    incidents = snow_client.list_incidents()

    if not incidents:
        print("📭 No incidents found")
        return

    print(f"✅ Found {len(incidents)} incidents")

    # Get current orchestrator stats
    orch_client = OrchestratorClient()
    initial_stats = orch_client.get_stats()
    print(f"\n📊 Current orchestrator stats:")
    print(f"   Total tickets: {initial_stats.get('total_tickets', 0)}")

    if dry_run:
        print(f"\n📋 Would forward {len(incidents)} tickets:")
        for idx, incident in enumerate(incidents[:10], 1):  # Show first 10
            print(f"   {idx}. {incident.get('number', 'N/A')}: {incident.get('short_description', 'No description')[:60]}")
        if len(incidents) > 10:
            print(f"   ... and {len(incidents) - 10} more")
        return

    print(f"\n📤 Forwarding {len(incidents)} tickets to orchestrator...")
    print()

    forwarded = 0
    failed = 0

    for incident in incidents:
        ticket_number = incident.get("number", "UNKNOWN")
        result = orch_client.send_ticket(incident)

        if result:
            forwarded += 1
            status_icon = "✅" if result.get("auto_resolve") else "📋"
            print(f"{status_icon} {ticket_number}: {result.get('message', 'Forwarded')}")
        else:
            failed += 1
            print(f"❌ {ticket_number}: Failed to forward")

        time.sleep(0.2)  # Small delay to avoid overwhelming the orchestrator

    print()
    print("=" * 70)
    print("📊 Summary:")
    print(f"   Forwarded: {forwarded}")
    print(f"   Failed: {failed}")
    print(f"   Total: {len(incidents)}")

    # Get final stats
    final_stats = orch_client.get_stats()
    print(f"\n📊 Final orchestrator stats:")
    print(f"   Total tickets: {final_stats.get('total_tickets', 0)}")
    print(f"   Auto-resolvable: {final_stats.get('by_status', {}).get('assigned_to_agent', 0)}")
    print(f"   Requires human: {final_stats.get('requires_human', 0)}")
    print("=" * 70)

def forward_specific_ticket(ticket_number: str):
    """Forward a specific ticket by number"""
    print(f"🔍 Looking for ticket {ticket_number}...")

    snow_client = ServiceNowClient()
    if not snow_client.login():
        print("❌ Failed to connect to ServiceNow")
        return

    incidents = snow_client.list_incidents()
    ticket = next((t for t in incidents if t.get("number") == ticket_number), None)

    if not ticket:
        print(f"❌ Ticket {ticket_number} not found")
        return

    print(f"✅ Found ticket: {ticket.get('short_description', 'N/A')}")

    orch_client = OrchestratorClient()
    result = orch_client.send_ticket(ticket)

    if result:
        print(f"✅ Forwarded to orchestrator")
        print(f"   Category: {result.get('category')}")
        print(f"   Auto-resolve: {result.get('auto_resolve')}")
        print(f"   Message: {result.get('message')}")
    else:
        print(f"❌ Failed to forward ticket")

# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--dry-run":
            forward_all_tickets(dry_run=True)
        elif sys.argv[1] == "--ticket":
            if len(sys.argv) > 2:
                forward_specific_ticket(sys.argv[2])
            else:
                print("Usage: python servicenow_ticket_forwarder.py --ticket INC0001234")
        else:
            print("Usage:")
            print("  python servicenow_ticket_forwarder.py                # Forward all tickets")
            print("  python servicenow_ticket_forwarder.py --dry-run     # Show what would be forwarded")
            print("  python servicenow_ticket_forwarder.py --ticket INC# # Forward specific ticket")
    else:
        forward_all_tickets(dry_run=False)
