"""
ServiceNow Integration Module
Handles ticket creation and status updates with ServiceNow
"""
import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ServiceNowClient:
    """Client for ServiceNow API interactions"""

    def __init__(self):
        # Configuration - can be moved to environment variables
        self.base_url = os.getenv("SERVICENOW_URL", "https://dev12345.service-now.com")
        self.username = os.getenv("SERVICENOW_USERNAME", "admin")
        self.password = os.getenv("SERVICENOW_PASSWORD", "password")
        self.timeout = 30

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
        Create a ticket in ServiceNow

        Args:
            short_description: Brief title of the ticket
            description: Detailed description
            category: Ticket category (inquiry, request, etc.)
            priority: Priority level (1-5, where 1 is highest)
            caller_id: ServiceNow user ID of the caller
            assignment_group: Group to assign the ticket to
            custom_fields: Additional fields to include

        Returns:
            Dict containing ticket details including sys_id and number
        """
        try:
            # Prepare ticket data
            ticket_data = {
                "short_description": short_description,
                "description": description,
                "category": category,
                "priority": priority,
                "state": "1",  # New
                "u_source": "Salesforce"  # Custom field to track source
            }

            if caller_id:
                ticket_data["caller_id"] = caller_id
            if assignment_group:
                ticket_data["assignment_group"] = assignment_group
            if custom_fields:
                ticket_data.update(custom_fields)

            # Make API call to ServiceNow
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/now/table/incident",
                    json=ticket_data,
                    auth=(self.username, self.password),
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                    timeout=self.timeout
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"ServiceNow ticket created: {result.get('result', {}).get('number')}")
                    return {
                        "success": True,
                        "ticket_id": result.get("result", {}).get("sys_id"),
                        "ticket_number": result.get("result", {}).get("number"),
                        "state": result.get("result", {}).get("state"),
                        "response": result
                    }
                else:
                    logger.error(f"ServiceNow ticket creation failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Failed to create ticket: {response.status_code}",
                        "details": response.text
                    }

        except httpx.TimeoutException:
            logger.error("ServiceNow API timeout")
            return {
                "success": False,
                "error": "ServiceNow API timeout"
            }
        except Exception as e:
            logger.error(f"ServiceNow integration error: {str(e)}")
            return {
                "success": False,
                "error": f"ServiceNow integration error: {str(e)}"
            }

    async def update_ticket(
        self,
        ticket_sys_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing ServiceNow ticket

        Args:
            ticket_sys_id: ServiceNow sys_id of the ticket
            updates: Dictionary of fields to update

        Returns:
            Dict containing update status
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/api/now/table/incident/{ticket_sys_id}",
                    json=updates,
                    auth=(self.username, self.password),
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "ticket_number": result.get("result", {}).get("number"),
                        "response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to update ticket: {response.status_code}"
                    }

        except Exception as e:
            logger.error(f"ServiceNow update error: {str(e)}")
            return {
                "success": False,
                "error": f"ServiceNow update error: {str(e)}"
            }

    async def get_ticket(self, ticket_sys_id: str) -> Dict[str, Any]:
        """
        Retrieve a ticket from ServiceNow

        Args:
            ticket_sys_id: ServiceNow sys_id of the ticket

        Returns:
            Dict containing ticket details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/now/table/incident/{ticket_sys_id}",
                    auth=(self.username, self.password),
                    headers={"Accept": "application/json"},
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "ticket": response.json().get("result", {})
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to retrieve ticket: {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"ServiceNow retrieval error: {str(e)}"
            }


# Singleton instance
servicenow_client = ServiceNowClient()


def get_servicenow_client() -> ServiceNowClient:
    """Get ServiceNow client instance"""
    return servicenow_client
