"""
ServiceNow Integration Module - FIXED VERSION
Updated to use query parameters instead of JSON body
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
        # ServiceNow Backend URL
        self.base_url = os.getenv("SERVICENOW_BACKEND_URL", "http://149.102.158.71:4780")
        # ServiceNow credentials
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
                    logger.info("ServiceNow authentication successful")
                    return self._token
                else:
                    logger.error(f"ServiceNow authentication failed: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"ServiceNow authentication error: {str(e)}")
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
        Create an incident ticket in ServiceNow backend - FIXED VERSION
        Uses query parameters instead of JSON body
        """
        try:
            # Get authentication token
            token = await self._get_token()
            if not token:
                return {
                    "success": False,
                    "error": "Failed to authenticate with ServiceNow"
                }

            # Prepare query parameters (not JSON body!)
            params = {
                "short_description": short_description,
                "description": description,
                "category": category,
                "priority": priority
            }

            # Note: custom_fields are NOT supported in query params
            # You would need to modify ServiceNow backend to accept them

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/servicenow/incidents",
                    params=params,  # Use params, not json!
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code in [200, 201]:
                    result = response.json()

                    # Extract ticket number from response
                    ticket_data = result.get("result", {})
                    ticket_number = ticket_data.get("number")

                    logger.info(f"ServiceNow incident created: {ticket_number}")
                    return {
                        "success": True,
                        "ticket_id": ticket_data.get("sys_id"),
                        "ticket_number": ticket_number,
                        "state": ticket_data.get("state"),
                        "response": result
                    }
                else:
                    logger.error(f"ServiceNow incident creation failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Failed to create incident: {response.status_code}",
                        "details": response.text
                    }

        except httpx.TimeoutException:
            logger.error("ServiceNow Backend API timeout")
            return {
                "success": False,
                "error": "ServiceNow Backend API timeout"
            }
        except Exception as e:
            logger.error(f"ServiceNow integration error: {str(e)}")
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
