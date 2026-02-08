#!/usr/bin/env python3
"""
ServiceNow Auto-Forwarding Service
Continuously monitors ServiceNow backend API and auto-forwards new/updated tickets to orchestrator
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Set, Dict, List
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('servicenow_autoforward.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

SERVICENOW_BACKEND_URL = "http://207.180.217.117:4780"
ORCHESTRATOR_URL = "http://localhost:2486"

# Polling interval in seconds
POLL_INTERVAL = 10  # Check for new tickets every 10 seconds

# Track forwarded tickets to avoid duplicates
forwarded_tickets: Set[str] = set()
ticket_timestamps: Dict[str, str] = {}

# Service control
running = True

# ============================================================================
# SERVICENOW CLIENT
# ============================================================================

class ServiceNowBackendClient:
    """Client for ServiceNow backend API"""

    def __init__(self):
        self.base_url = SERVICENOW_BACKEND_URL
        self.token = None

    def login(self) -> bool:
        """Login to ServiceNow backend"""
        try:
            response = requests.post(
                f"{self.base_url}/token",
                data={
                    "username": "admin@company.com",
                    "password": "admin123"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )

            if response.status_code == 200:
                self.token = response.json().get("access_token")
                logger.info("Connected to ServiceNow backend")
                return True
            else:
                logger.warning("ServiceNow auth failed, will retry next poll...")
                return False

        except Exception as e:
            logger.warning(f"ServiceNow connection failed: {e}, will retry next poll...")
            return False

    def fetch_incidents(self, limit: int = 200) -> List[Dict]:
        """Fetch recent tickets from ServiceNow backend"""
        if not self.token:
            if not self.login():
                return []

        try:
            response = requests.get(
                f"{self.base_url}/api/tickets",
                params={"limit": limit, "skip": 0},
                timeout=15
            )

            if response.status_code == 401:
                logger.info("Token expired, re-authenticating...")
                self.token = None
                if self.login():
                    return self.fetch_incidents(limit)
                return []

            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "result" in data:
                return data["result"]
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to fetch incidents: {e}, will retry next poll...")
            self.token = None
            return []

# ============================================================================
# ORCHESTRATOR CLIENT
# ============================================================================

class OrchestratorClient:
    """Client for Ticket Orchestrator"""

    def __init__(self):
        self.base_url = ORCHESTRATOR_URL

    def forward_ticket(self, incident: Dict) -> bool:
        """Forward a ticket to orchestrator"""
        try:
            # Transform to orchestrator format
            # Handle both tickets API format and incidents API format
            ticket = {
                "sys_id": str(incident.get("sys_id") or incident.get("id", "unknown")),
                "number": incident.get("number") or incident.get("ticket_number") or f"INC{int(time.time())}",
                "short_description": incident.get("short_description") or incident.get("title") or "No title",
                "description": incident.get("description") or "No description provided",
                "priority": str(incident.get("priority", "3")),
                "state": incident.get("state") or incident.get("status") or "2",
                "assigned_to": incident.get("assigned_to") or "",
                "category": incident.get("category") or "",
                "subcategory": incident.get("subcategory") or ""
            }

            response = requests.post(
                f"{self.base_url}/api/webhook/servicenow",
                json=ticket,
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                ticket_number = ticket["number"]

                icon = "🤖" if result.get("auto_resolve") else "👤"
                logger.info(f"{icon} Forwarded {ticket_number}: {result.get('message', 'OK')}")
                return True
            else:
                error_detail = ""
                try:
                    error_detail = response.json()
                except:
                    error_detail = response.text
                logger.error(f"❌ Failed to forward {ticket['number']}: HTTP {response.status_code} - {error_detail}")
                return False

        except Exception as e:
            logger.error(f"❌ Exception forwarding ticket: {e}")
            return False

    def check_health(self) -> bool:
        """Check if orchestrator is running"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False

# ============================================================================
# AUTO-FORWARDING SERVICE
# ============================================================================

class AutoForwardingService:
    """Service that automatically forwards tickets from ServiceNow to Orchestrator"""

    def __init__(self):
        self.snow_client = ServiceNowBackendClient()
        self.orch_client = OrchestratorClient()
        self.forwarded_count = 0
        self.failed_count = 0

    def should_forward_ticket(self, incident: Dict) -> bool:
        """Determine if a ticket should be forwarded"""
        ticket_id = str(incident.get("sys_id") or incident.get("id") or incident.get("number") or incident.get("ticket_number", ""))

        if not ticket_id:
            return False

        # Check if already forwarded
        if ticket_id in forwarded_tickets:
            # Check if ticket was updated
            current_updated = incident.get("updated_at") or incident.get("sys_updated_on", "")
            last_updated = ticket_timestamps.get(ticket_id, "")

            if current_updated and current_updated != last_updated:
                ticket_num = incident.get('number') or incident.get('ticket_number', ticket_id)
                logger.info(f"📝 Ticket {ticket_num} was updated, re-forwarding...")
                return True

            return False

        return True

    def process_tickets(self):
        """Fetch and forward new tickets"""
        try:
            # Fetch incidents from ServiceNow
            incidents = self.snow_client.fetch_incidents()

            if not incidents:
                return

            new_tickets = 0

            for incident in incidents:
                if self.should_forward_ticket(incident):
                    if self.orch_client.forward_ticket(incident):
                        # Handle both ticket_number and number fields
                        ticket_id = str(incident.get("sys_id") or incident.get("id") or incident.get("number") or incident.get("ticket_number", ""))
                        forwarded_tickets.add(ticket_id)
                        ticket_timestamps[ticket_id] = incident.get("updated_at") or incident.get("sys_updated_on", "")
                        self.forwarded_count += 1
                        new_tickets += 1
                    else:
                        self.failed_count += 1

                    time.sleep(0.2)  # Small delay between forwards

            if new_tickets > 0:
                logger.info(f"📊 Forwarded {new_tickets} new tickets (Total: {self.forwarded_count}, Failed: {self.failed_count})")

        except Exception as e:
            logger.error(f"❌ Error processing tickets: {e}")

    def run(self):
        """Main service loop"""
        logger.info("=" * 70)
        logger.info("🚀 ServiceNow Auto-Forwarding Service Started")
        logger.info("=" * 70)
        logger.info(f"📡 ServiceNow Backend: {SERVICENOW_BACKEND_URL}")
        logger.info(f"🎯 Orchestrator: {ORCHESTRATOR_URL}")
        logger.info(f"⏱️  Poll Interval: {POLL_INTERVAL} seconds")
        logger.info("=" * 70)

        # Initial health check
        if not self.orch_client.check_health():
            logger.error("❌ Orchestrator not responding! Check if it's running on port 2486")
            logger.info("   Start orchestrator: python3 -m uvicorn ticket_orchestrator:app --host 0.0.0.0 --port 2486")
            return

        logger.info("✅ Orchestrator is healthy")

        # Connect to ServiceNow
        if not self.snow_client.login():
            logger.warning("⚠️  Could not connect to ServiceNow backend, will retry...")

        logger.info("")
        logger.info("🔄 Monitoring for new tickets... (Press Ctrl+C to stop)")
        logger.info("")

        try:
            while running:
                self.process_tickets()
                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("")
            logger.info("=" * 70)
            logger.info("🛑 Service stopped by user")
            logger.info(f"📊 Final Stats: Forwarded={self.forwarded_count}, Failed={self.failed_count}")
            logger.info("=" * 70)

# ============================================================================
# SIGNAL HANDLERS
# ============================================================================

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    logger.info("\n🛑 Shutdown signal received, stopping service...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    service = AutoForwardingService()
    service.run()
