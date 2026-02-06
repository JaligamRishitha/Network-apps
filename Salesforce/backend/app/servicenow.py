"""
ServiceNow Integration Module - FIXED VERSION
Automatically creates ServiceNow tickets when Salesforce appointments are created
"""
import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ServiceNowClient:
    """Client for ServiceNow Backend API interactions - FIXED"""

    def __init__(self):
        # Use servicenow-backend container name for Docker networking
        # Falls back to external IP for local development
        self.base_url = os.getenv("SERVICENOW_BACKEND_URL", "http://servicenow-backend:4780")
        self.username = os.getenv("SERVICENOW_USERNAME", "admin@company.com")
        self.password = os.getenv("SERVICENOW_PASSWORD", "admin123")
        self.timeout = 30
        self._token = None

    async def _get_token(self) -> Optional[str]:
        """Get authentication token from ServiceNow"""
        if self._token:
            return self._token

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/token",
                    data={
                        "username": self.username,
                        "password": self.password
                    },
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    self._token = data.get("access_token")
                    logger.info("✅ ServiceNow authentication successful")
                    return self._token
                else:
                    logger.error(f"❌ ServiceNow authentication failed: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"❌ ServiceNow authentication error: {str(e)}")
            return None

    async def create_ticket(
        self,
        short_description: str,
        description: str,
        category: str = "inquiry",
        priority: str = "3",
        caller_id: Optional[str] = None,
        assignment_group: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a ticket in ServiceNow backend (TKT* numbers, not INC* incidents)
        Uses the /tickets/ endpoint to create tickets in the tickets table
        """
        try:
            # Get authentication token
            token = await self._get_token()
            if not token:
                return {
                    "success": False,
                    "error": "Failed to authenticate with ServiceNow"
                }

            # Map priority: 1=high, 2=medium, 3=low
            priority_map = {"1": "high", "2": "medium", "3": "low", "4": "low"}
            priority_str = priority_map.get(str(priority), "medium")

            # Prepare request body for tickets endpoint
            ticket_data = {
                "title": short_description,
                "description": description,
                "ticket_type": "service_request",
                "priority": priority_str,
                "category": category,
                "subcategory": custom_fields.get("u_request_type") if custom_fields else None,
                "urgency": "high" if priority_str == "high" else "medium",
                "preferred_contact": "email",
                # Salesforce integration fields
                "correlation_id": custom_fields.get("correlation_id") if custom_fields else None,
                "source_system": custom_fields.get("source_system") if custom_fields else None,
                "source_request_id": custom_fields.get("source_request_id") if custom_fields else None,
                "source_request_type": custom_fields.get("source_request_type") if custom_fields else None
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            logger.info(f"🎫 Creating ServiceNow ticket: {short_description}")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/tickets/",
                    json=ticket_data,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    ticket_number = result.get("ticket_number")

                    logger.info(f"✅ ServiceNow ticket created: {ticket_number}")

                    return {
                        "success": True,
                        "ticket_id": result.get("id"),
                        "ticket_number": ticket_number,
                        "state": result.get("status"),
                        "response": result
                    }
                else:
                    logger.error(f"❌ ServiceNow ticket creation failed: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Failed to create ticket: {response.status_code}",
                        "details": response.text
                    }

        except httpx.TimeoutException:
            logger.error("❌ ServiceNow API timeout")
            return {
                "success": False,
                "error": "ServiceNow Backend API timeout"
            }
        except Exception as e:
            logger.error(f"❌ ServiceNow integration error: {str(e)}")
            return {
                "success": False,
                "error": f"ServiceNow integration error: {str(e)}"
            }

    async def update_ticket(
        self,
        ticket_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing ServiceNow incident"""
        try:
            token = await self._get_token()
            if not token:
                return {"success": False, "error": "Authentication failed"}

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}"
            }

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/api/servicenow/incidents/{ticket_id}",
                    json=updates,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "ticket_number": result.get("number"),
                        "response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to update incident: {response.status_code}"
                    }

        except Exception as e:
            logger.error(f"ServiceNow update error: {str(e)}")
            return {
                "success": False,
                "error": f"ServiceNow update error: {str(e)}"
            }

    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Retrieve an incident from ServiceNow backend"""
        try:
            token = await self._get_token()
            if not token:
                return {"success": False, "error": "Authentication failed"}

            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {token}"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/servicenow/incidents/{ticket_id}",
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "ticket": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to retrieve incident: {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"ServiceNow retrieval error: {str(e)}"
            }

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to ServiceNow backend"""
        try:
            token = await self._get_token()
            if not token:
                return {
                    "success": False,
                    "error": "Authentication failed"
                }

            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "ServiceNow backend connection successful",
                        "response": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Connection test failed: {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Connection test error: {str(e)}"
            }


# Singleton instance
servicenow_client = ServiceNowClient()


def get_servicenow_client() -> ServiceNowClient:
    """Get ServiceNow client instance"""
    return servicenow_client
