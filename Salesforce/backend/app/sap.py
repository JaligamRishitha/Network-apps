"""
SAP Integration Module
Handles integration with SAP backend for maintenance orders, work orders, and tickets
"""
import os
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SAPClient:
    """Client for SAP Backend API interactions"""

    def __init__(self):
        # SAP Backend configuration
        self.base_url = os.getenv("SAP_BACKEND_URL", "http://sap-backend:8080")
        self.api_version = "v1"
        self.username = os.getenv("SAP_USERNAME", "")
        self.password = os.getenv("SAP_PASSWORD", "")
        self.access_token = None
        self.refresh_token = None
        self.timeout = 30

    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with SAP backend and get access token

        Returns:
            Dict containing authentication status and tokens
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/{self.api_version}/auth/login",
                    json={
                        "username": self.username,
                        "password": self.password
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    self.access_token = result.get("access_token")
                    self.refresh_token = result.get("refresh_token")
                    logger.info("SAP authentication successful")
                    return {
                        "success": True,
                        "access_token": self.access_token,
                        "refresh_token": self.refresh_token
                    }
                else:
                    logger.error(f"SAP authentication failed: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Authentication failed: {response.status_code}"
                    }

        except Exception as e:
            logger.error(f"SAP authentication error: {str(e)}")
            return {
                "success": False,
                "error": f"Authentication error: {str(e)}"
            }

    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        if not self.access_token:
            auth_result = await self.authenticate()
            if not auth_result.get("success"):
                raise Exception("Failed to authenticate with SAP")

        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

    async def create_maintenance_order(
        self,
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a maintenance order in SAP PM module

        Args:
            order_data: Maintenance order details
            Example:
            {
                "order_type": "PM01",  # Maintenance order type
                "description": "Service Appointment",
                "equipment_id": "EQ-001",
                "priority": "3",
                "scheduled_start": "2026-02-05T10:00:00",
                "scheduled_end": "2026-02-05T12:00:00",
                "technician": "TECH001",
                "work_center": "WC01",
                "plant": "1000",
                "cost_center": "CC001",
                "notes": "Service appointment from Salesforce"
            }

        Returns:
            Dict containing maintenance order details
        """
        try:
            headers = await self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/{self.api_version}/pm/maintenance-orders",
                    json=order_data,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"SAP maintenance order created: {result.get('order_id')}")
                    return {
                        "success": True,
                        "order_id": result.get("order_id") or result.get("id"),
                        "order_number": result.get("order_number"),
                        "status": result.get("status"),
                        "response": result
                    }
                else:
                    logger.error(f"Failed to create maintenance order: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Failed to create maintenance order: {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error(f"SAP maintenance order error: {str(e)}")
            return {
                "success": False,
                "error": f"SAP maintenance order error: {str(e)}"
            }

    async def create_sales_order(
        self,
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a sales order in SAP (for service sales)

        Args:
            order_data: Sales order details
            Example:
            {
                "customer_id": "CUST001",
                "order_type": "ZOR",
                "sales_org": "1000",
                "distribution_channel": "10",
                "division": "00",
                "items": [
                    {
                        "material": "SERVICE-001",
                        "quantity": 1,
                        "unit": "EA",
                        "price": 1000.00
                    }
                ],
                "reference": "Salesforce Work Order WO-12345"
            }

        Returns:
            Dict containing sales order details
        """
        try:
            headers = await self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/sales/orders",
                    json=order_data,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"SAP sales order created: {result.get('order_id')}")
                    return {
                        "success": True,
                        "order_id": result.get("order_id") or result.get("id"),
                        "order_number": result.get("order_number"),
                        "status": result.get("status"),
                        "response": result
                    }
                else:
                    logger.error(f"Failed to create sales order: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Failed to create sales order: {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error(f"SAP sales order error: {str(e)}")
            return {
                "success": False,
                "error": f"SAP sales order error: {str(e)}"
            }

    async def update_order_status(
        self,
        order_id: str,
        status: str,
        order_type: str = "sales"
    ) -> Dict[str, Any]:
        """
        Update order status in SAP

        Args:
            order_id: Order ID
            status: New status
            order_type: "sales" or "maintenance"

        Returns:
            Dict containing update status
        """
        try:
            headers = await self._get_headers()

            endpoint = f"/api/sales/orders/{order_id}/status" if order_type == "sales" else None

            if not endpoint:
                return {
                    "success": False,
                    "error": "Invalid order type"
                }

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}{endpoint}",
                    json={"status": status},
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "response": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to update order: {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Order update error: {str(e)}"
            }

    async def create_incident(
        self,
        incident_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an incident in SAP PM module

        Args:
            incident_data: Incident details

        Returns:
            Dict containing incident details
        """
        try:
            headers = await self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/{self.api_version}/pm/incidents",
                    json=incident_data,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    return {
                        "success": True,
                        "incident_id": result.get("incident_id") or result.get("id"),
                        "response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to create incident: {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Incident creation error: {str(e)}"
            }

    async def create_ticket(
        self,
        ticket_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a ticket in SAP

        Args:
            ticket_data: Ticket details

        Returns:
            Dict containing ticket details
        """
        try:
            headers = await self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/{self.api_version}/tickets",
                    json=ticket_data,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    return {
                        "success": True,
                        "ticket_id": result.get("ticket_id") or result.get("id"),
                        "response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to create ticket: {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Ticket creation error: {str(e)}"
            }

    async def get_maintenance_orders(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get maintenance orders from SAP

        Args:
            filters: Optional filters

        Returns:
            List of maintenance orders
        """
        try:
            headers = await self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/{self.api_version}/pm/maintenance-orders",
                    params=filters or {},
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "orders": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to get orders: {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Get orders error: {str(e)}"
            }

    async def get_materials(
        self,
        material_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get materials/parts from SAP MM module

        Args:
            material_ids: Optional list of material IDs

        Returns:
            List of materials
        """
        try:
            headers = await self._get_headers()

            params = {}
            if material_ids:
                params["ids"] = ",".join(material_ids)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/{self.api_version}/mm/materials",
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "materials": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to get materials: {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Get materials error: {str(e)}"
            }

    async def create_cost_entry(
        self,
        cost_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a cost entry in SAP FI module

        Args:
            cost_data: Cost entry details

        Returns:
            Dict containing cost entry details
        """
        try:
            headers = await self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/{self.api_version}/fi/cost-entries",
                    json=cost_data,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code in [200, 201]:
                    return {
                        "success": True,
                        "cost_entry": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to create cost entry: {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Cost entry error: {str(e)}"
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check SAP backend health

        Returns:
            Dict containing health status
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=10
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "status": "healthy",
                        "response": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Health check failed: {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Health check error: {str(e)}"
            }


# Singleton instance
sap_client = SAPClient()


def get_sap_client() -> SAPClient:
    """Get SAP client instance"""
    return sap_client
