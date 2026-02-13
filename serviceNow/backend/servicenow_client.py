"""
ServiceNow API Client
Based on MCP server patterns for ServiceNow integration
Supports mock mode when no real ServiceNow instance is configured
"""

import os
import json
import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import random
import string


@dataclass
class ServiceNowConfig:
    instance_url: str
    username: str
    password: str
    timeout: float = 30.0
    mock_mode: bool = False


class ServiceNowClient:
    """Client for interacting with ServiceNow REST API"""

    def __init__(self, config: Optional[ServiceNowConfig] = None):
        if config:
            self.config = config
        else:
            instance = os.getenv("SERVICENOW_INSTANCE", "")
            # Enable mock mode if no real instance is configured
            mock_mode = not instance or instance.startswith("https://dev12345") or "mock" in instance.lower()

            self.config = ServiceNowConfig(
                instance_url=instance,
                username=os.getenv("SERVICENOW_USER", ""),
                password=os.getenv("SERVICENOW_PASSWORD", ""),
                timeout=float(os.getenv("SERVICENOW_TIMEOUT", "30.0")),
                mock_mode=mock_mode
            )

        # Mock data storage (in-memory)
        self._mock_incidents: Dict[str, dict] = {}
        self._mock_changes: Dict[str, dict] = {}
        self._mock_problems: Dict[str, dict] = {}
        self._mock_requests: Dict[str, dict] = {}
        self._mock_users: Dict[str, dict] = {}
        self._mock_knowledge: Dict[str, dict] = {}
        self._mock_catalog: Dict[str, dict] = {}
        self._mock_approvals: Dict[str, dict] = {}
        self._mock_cmdb: Dict[str, dict] = {}

        # Initialize with sample data
        self._init_mock_data()

    def _generate_sys_id(self) -> str:
        """Generate a ServiceNow-style sys_id"""
        return ''.join(random.choices(string.hexdigits.lower(), k=32))

    def _generate_number(self, prefix: str) -> str:
        """Generate a ServiceNow-style record number"""
        return f"{prefix}{random.randint(1000000, 9999999)}"

    def _init_mock_data(self):
        """Initialize mock data for demo purposes"""
        # Sample users
        users = [
            {"sys_id": self._generate_sys_id(), "user_name": "admin", "email": "admin@company.com", "first_name": "Sally", "last_name": "Matthew", "active": "true", "title": "IT Administrator"},
            {"sys_id": self._generate_sys_id(), "user_name": "jsmith", "email": "jsmith@company.com", "first_name": "John", "last_name": "Smith", "active": "true", "title": "Software Engineer"},
            {"sys_id": self._generate_sys_id(), "user_name": "mjones", "email": "mjones@company.com", "first_name": "Mary", "last_name": "Jones", "active": "true", "title": "Project Manager"},
        ]
        for user in users:
            self._mock_users[user["sys_id"]] = user

        # Sample incidents
        incidents = [
            {"short_description": "Email server not responding", "description": "Users unable to send or receive emails since 9 AM", "priority": "1", "state": "2", "category": "Network", "impact": "1", "urgency": "1"},
            {"short_description": "VPN connection issues", "description": "Remote users experiencing intermittent VPN disconnections", "priority": "2", "state": "2", "category": "Network", "impact": "2", "urgency": "2"},
            {"short_description": "Printer offline in Building A", "description": "Main printer on 3rd floor showing offline status", "priority": "3", "state": "1", "category": "Hardware", "impact": "3", "urgency": "3"},
            {"short_description": "Software license expired", "description": "Microsoft Office license needs renewal for Finance team", "priority": "3", "state": "1", "category": "Software", "impact": "2", "urgency": "3"},
            {"short_description": "Password reset request", "description": "User locked out after multiple failed attempts", "priority": "4", "state": "6", "category": "Access", "impact": "3", "urgency": "3"},
        ]
        for inc in incidents:
            sys_id = self._generate_sys_id()
            inc["sys_id"] = sys_id
            inc["number"] = self._generate_number("INC")
            inc["opened_at"] = datetime.utcnow().isoformat() + "Z"
            inc["sys_created_on"] = datetime.utcnow().isoformat() + "Z"
            inc["caller_id"] = list(self._mock_users.keys())[0]
            self._mock_incidents[sys_id] = inc

        # Sample change requests
        changes = [
            {"short_description": "Upgrade database server", "description": "Upgrade PostgreSQL from 14 to 15", "type": "normal", "priority": "3", "state": "1", "risk": "moderate"},
            {"short_description": "Network switch replacement", "description": "Replace aging network switches in server room", "type": "normal", "priority": "2", "state": "2", "risk": "high"},
            {"short_description": "Security patch deployment", "description": "Deploy critical security patches to all servers", "type": "emergency", "priority": "1", "state": "3", "risk": "low"},
        ]
        for chg in changes:
            sys_id = self._generate_sys_id()
            chg["sys_id"] = sys_id
            chg["number"] = self._generate_number("CHG")
            chg["opened_at"] = datetime.utcnow().isoformat() + "Z"
            chg["sys_created_on"] = datetime.utcnow().isoformat() + "Z"
            self._mock_changes[sys_id] = chg

        # Sample problems
        problems = [
            {"short_description": "Recurring network latency", "description": "Network performance degrades every afternoon", "priority": "2", "state": "2", "impact": "2", "urgency": "2"},
            {"short_description": "Application memory leak", "description": "CRM application consuming excessive memory over time", "priority": "3", "state": "1", "impact": "3", "urgency": "3"},
        ]
        for prob in problems:
            sys_id = self._generate_sys_id()
            prob["sys_id"] = sys_id
            prob["number"] = self._generate_number("PRB")
            prob["opened_at"] = datetime.utcnow().isoformat() + "Z"
            prob["sys_created_on"] = datetime.utcnow().isoformat() + "Z"
            self._mock_problems[sys_id] = prob

        # Sample catalog items
        catalog_items = [
            {"name": "New Laptop Request", "short_description": "Request a new laptop", "category": "Hardware", "price": "1200.00", "active": "true"},
            {"name": "Software Installation", "short_description": "Install approved software", "category": "Software", "price": "0.00", "active": "true"},
            {"name": "Access Request", "short_description": "Request access to systems", "category": "Access", "price": "0.00", "active": "true"},
            {"name": "New Mobile Phone", "short_description": "Request a company mobile phone", "category": "Hardware", "price": "800.00", "active": "true"},
            {"name": "VPN Access", "short_description": "Request VPN access for remote work", "category": "Access", "price": "0.00", "active": "true"},
        ]
        for item in catalog_items:
            sys_id = self._generate_sys_id()
            item["sys_id"] = sys_id
            item["sys_created_on"] = datetime.utcnow().isoformat() + "Z"
            self._mock_catalog[sys_id] = item

        # Sample knowledge articles
        articles = [
            {"short_description": "How to reset your password", "text": "Step 1: Go to login page. Step 2: Click Forgot Password. Step 3: Enter your email.", "category": "Account Management", "kb_knowledge_base": "IT Knowledge Base"},
            {"short_description": "VPN Setup Guide", "text": "Complete guide to setting up VPN on Windows, Mac, and mobile devices.", "category": "Network", "kb_knowledge_base": "IT Knowledge Base"},
            {"short_description": "Printer Troubleshooting", "text": "Common printer issues and how to resolve them.", "category": "Hardware", "kb_knowledge_base": "IT Knowledge Base"},
        ]
        for article in articles:
            sys_id = self._generate_sys_id()
            article["sys_id"] = sys_id
            article["number"] = self._generate_number("KB")
            article["sys_created_on"] = datetime.utcnow().isoformat() + "Z"
            self._mock_knowledge[sys_id] = article

        # Sample CMDB items
        cmdb_items = [
            {"name": "Web Server 01", "sys_class_name": "cmdb_ci_server", "ip_address": "192.168.1.10", "operational_status": "1", "environment": "Production"},
            {"name": "Database Server 01", "sys_class_name": "cmdb_ci_server", "ip_address": "192.168.1.20", "operational_status": "1", "environment": "Production"},
            {"name": "Application Server 01", "sys_class_name": "cmdb_ci_server", "ip_address": "192.168.1.30", "operational_status": "1", "environment": "Production"},
            {"name": "Network Switch Core", "sys_class_name": "cmdb_ci_netgear", "ip_address": "192.168.1.1", "operational_status": "1", "environment": "Production"},
        ]
        for item in cmdb_items:
            sys_id = self._generate_sys_id()
            item["sys_id"] = sys_id
            item["sys_created_on"] = datetime.utcnow().isoformat() + "Z"
            self._mock_cmdb[sys_id] = item

    @property
    def is_configured(self) -> bool:
        """Check if ServiceNow is properly configured"""
        if self.config.mock_mode:
            return True
        return bool(
            self.config.instance_url and
            self.config.username and
            self.config.password
        )

    async def _api_call(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated API call to ServiceNow"""
        if self.config.mock_mode:
            return {"error": "Mock mode - use mock methods", "mock": True}

        if not self.is_configured:
            return {"error": "ServiceNow not configured", "details": "Missing credentials"}

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        url = f"{self.config.instance_url}/api/now{endpoint}"

        async with httpx.AsyncClient(
            timeout=self.config.timeout,
            auth=(self.config.username, self.config.password)
        ) as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    return {"error": f"Unsupported method: {method}"}

                if response.status_code >= 400:
                    return {
                        "error": f"ServiceNow API Error {response.status_code}",
                        "details": response.text,
                    }

                return response.json()
            except httpx.TimeoutException:
                return {"error": "Request timeout", "details": "ServiceNow API request timed out"}
            except httpx.RequestError as e:
                return {"error": "Connection error", "details": str(e)}

    def _paginate(self, data: Dict[str, dict], skip: int, limit: int) -> List[dict]:
        """Paginate mock data"""
        items = list(data.values())
        return items[skip:skip + limit]

    # ========================================================================
    # INCIDENT OPERATIONS
    # ========================================================================

    async def list_incidents(
        self,
        skip: int = 0,
        limit: int = 50,
        query: str = ""
    ) -> Dict[str, Any]:
        """List ServiceNow incidents"""
        if self.config.mock_mode:
            results = self._paginate(self._mock_incidents, skip, limit)
            if query:
                results = [r for r in results if query.lower() in r.get("short_description", "").lower()]
            return {"result": results}

        params = {"sysparm_offset": skip, "sysparm_limit": limit}
        if query:
            params["sysparm_query"] = query
        return await self._api_call("GET", "/table/incident", params=params)

    async def get_incident(self, incident_id: str) -> Dict[str, Any]:
        """Get ServiceNow incident by sys_id"""
        if self.config.mock_mode:
            if incident_id in self._mock_incidents:
                return {"result": self._mock_incidents[incident_id]}
            return {"error": "Incident not found"}

        return await self._api_call("GET", f"/table/incident/{incident_id}")

    async def get_incident_by_number(self, incident_number: str) -> Dict[str, Any]:
        """Get ServiceNow incident by number (e.g., INC0010001)"""
        if self.config.mock_mode:
            for inc in self._mock_incidents.values():
                if inc.get("number") == incident_number:
                    return {"result": [inc]}
            return {"result": []}

        params = {"sysparm_query": f"number={incident_number}", "sysparm_limit": 1}
        return await self._api_call("GET", "/table/incident", params=params)

    async def create_incident(
        self,
        short_description: str,
        description: str = "",
        priority: str = "3",
        urgency: str = "3",
        impact: str = "3",
        category: str = "",
        subcategory: str = "",
        assignment_group: str = "",
        caller_id: str = "",
    ) -> Dict[str, Any]:
        """Create a new ServiceNow incident"""
        if self.config.mock_mode:
            sys_id = self._generate_sys_id()
            incident = {
                "sys_id": sys_id,
                "number": self._generate_number("INC"),
                "short_description": short_description,
                "description": description,
                "priority": priority,
                "urgency": urgency,
                "impact": impact,
                "category": category,
                "subcategory": subcategory,
                "state": "1",  # New
                "opened_at": datetime.utcnow().isoformat() + "Z",
                "sys_created_on": datetime.utcnow().isoformat() + "Z",
            }
            if assignment_group:
                incident["assignment_group"] = assignment_group
            if caller_id:
                incident["caller_id"] = caller_id
            self._mock_incidents[sys_id] = incident
            return {"result": incident}

        data = {
            "short_description": short_description,
            "description": description,
            "priority": priority,
            "urgency": urgency,
            "impact": impact,
        }
        if category:
            data["category"] = category
        if subcategory:
            data["subcategory"] = subcategory
        if assignment_group:
            data["assignment_group"] = assignment_group
        if caller_id:
            data["caller_id"] = caller_id

        return await self._api_call("POST", "/table/incident", data)

    async def update_incident(
        self,
        incident_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a ServiceNow incident"""
        if self.config.mock_mode:
            if incident_id in self._mock_incidents:
                self._mock_incidents[incident_id].update(updates)
                self._mock_incidents[incident_id]["sys_updated_on"] = datetime.utcnow().isoformat() + "Z"
                return {"result": self._mock_incidents[incident_id]}
            return {"error": "Incident not found"}

        return await self._api_call("PUT", f"/table/incident/{incident_id}", updates)

    async def close_incident(
        self,
        incident_id: str,
        close_notes: str = "",
        close_code: str = "Solved (Permanently)"
    ) -> Dict[str, Any]:
        """Close a ServiceNow incident"""
        if self.config.mock_mode:
            if incident_id in self._mock_incidents:
                self._mock_incidents[incident_id]["state"] = "7"  # Closed
                self._mock_incidents[incident_id]["close_notes"] = close_notes
                self._mock_incidents[incident_id]["close_code"] = close_code
                self._mock_incidents[incident_id]["closed_at"] = datetime.utcnow().isoformat() + "Z"
                return {"result": self._mock_incidents[incident_id]}
            return {"error": "Incident not found"}

        data = {
            "state": "7",
            "close_notes": close_notes,
            "close_code": close_code,
        }
        return await self._api_call("PUT", f"/table/incident/{incident_id}", data)

    # ========================================================================
    # CHANGE REQUEST OPERATIONS
    # ========================================================================

    async def list_change_requests(
        self,
        skip: int = 0,
        limit: int = 50,
        query: str = ""
    ) -> Dict[str, Any]:
        """List ServiceNow change requests"""
        if self.config.mock_mode:
            results = self._paginate(self._mock_changes, skip, limit)
            return {"result": results}

        params = {"sysparm_offset": skip, "sysparm_limit": limit}
        if query:
            params["sysparm_query"] = query
        return await self._api_call("GET", "/table/change_request", params=params)

    async def get_change_request(self, change_id: str) -> Dict[str, Any]:
        """Get ServiceNow change request by sys_id"""
        if self.config.mock_mode:
            if change_id in self._mock_changes:
                return {"result": self._mock_changes[change_id]}
            return {"error": "Change request not found"}

        return await self._api_call("GET", f"/table/change_request/{change_id}")

    async def create_change_request(
        self,
        short_description: str,
        description: str = "",
        change_type: str = "normal",
        priority: str = "3",
        risk: str = "moderate",
        impact: str = "3",
        assignment_group: str = "",
    ) -> Dict[str, Any]:
        """Create a new ServiceNow change request"""
        if self.config.mock_mode:
            sys_id = self._generate_sys_id()
            change = {
                "sys_id": sys_id,
                "number": self._generate_number("CHG"),
                "short_description": short_description,
                "description": description,
                "type": change_type,
                "priority": priority,
                "risk": risk,
                "impact": impact,
                "state": "1",
                "opened_at": datetime.utcnow().isoformat() + "Z",
                "sys_created_on": datetime.utcnow().isoformat() + "Z",
            }
            if assignment_group:
                change["assignment_group"] = assignment_group
            self._mock_changes[sys_id] = change
            return {"result": change}

        data = {
            "short_description": short_description,
            "description": description,
            "type": change_type,
            "priority": priority,
            "risk": risk,
            "impact": impact,
        }
        if assignment_group:
            data["assignment_group"] = assignment_group

        return await self._api_call("POST", "/table/change_request", data)

    async def update_change_request(
        self,
        change_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a ServiceNow change request"""
        if self.config.mock_mode:
            if change_id in self._mock_changes:
                self._mock_changes[change_id].update(updates)
                return {"result": self._mock_changes[change_id]}
            return {"error": "Change request not found"}

        return await self._api_call("PUT", f"/table/change_request/{change_id}", updates)

    # ========================================================================
    # PROBLEM OPERATIONS
    # ========================================================================

    async def list_problems(
        self,
        skip: int = 0,
        limit: int = 50,
        query: str = ""
    ) -> Dict[str, Any]:
        """List ServiceNow problems"""
        if self.config.mock_mode:
            results = self._paginate(self._mock_problems, skip, limit)
            return {"result": results}

        params = {"sysparm_offset": skip, "sysparm_limit": limit}
        if query:
            params["sysparm_query"] = query
        return await self._api_call("GET", "/table/problem", params=params)

    async def get_problem(self, problem_id: str) -> Dict[str, Any]:
        """Get ServiceNow problem by sys_id"""
        if self.config.mock_mode:
            if problem_id in self._mock_problems:
                return {"result": self._mock_problems[problem_id]}
            return {"error": "Problem not found"}

        return await self._api_call("GET", f"/table/problem/{problem_id}")

    async def create_problem(
        self,
        short_description: str,
        description: str = "",
        priority: str = "3",
        impact: str = "3",
        urgency: str = "3",
    ) -> Dict[str, Any]:
        """Create a new ServiceNow problem"""
        if self.config.mock_mode:
            sys_id = self._generate_sys_id()
            problem = {
                "sys_id": sys_id,
                "number": self._generate_number("PRB"),
                "short_description": short_description,
                "description": description,
                "priority": priority,
                "impact": impact,
                "urgency": urgency,
                "state": "1",
                "opened_at": datetime.utcnow().isoformat() + "Z",
                "sys_created_on": datetime.utcnow().isoformat() + "Z",
            }
            self._mock_problems[sys_id] = problem
            return {"result": problem}

        data = {
            "short_description": short_description,
            "description": description,
            "priority": priority,
            "impact": impact,
            "urgency": urgency,
        }
        return await self._api_call("POST", "/table/problem", data)

    # ========================================================================
    # SERVICE REQUEST (RITM) OPERATIONS
    # ========================================================================

    async def list_service_requests(
        self,
        skip: int = 0,
        limit: int = 50,
        query: str = ""
    ) -> Dict[str, Any]:
        """List ServiceNow requested items (service requests)"""
        if self.config.mock_mode:
            results = self._paginate(self._mock_requests, skip, limit)
            return {"result": results}

        params = {"sysparm_offset": skip, "sysparm_limit": limit}
        if query:
            params["sysparm_query"] = query
        return await self._api_call("GET", "/table/sc_req_item", params=params)

    async def get_service_request(self, ritm_id: str) -> Dict[str, Any]:
        """Get ServiceNow requested item by sys_id"""
        if self.config.mock_mode:
            if ritm_id in self._mock_requests:
                return {"result": self._mock_requests[ritm_id]}
            return {"error": "Service request not found"}

        return await self._api_call("GET", f"/table/sc_req_item/{ritm_id}")

    async def create_service_request(
        self,
        short_description: str,
        description: str = "",
        priority: str = "3",
        requested_for: str = "",
        catalog_item: str = "",
    ) -> Dict[str, Any]:
        """Create a new ServiceNow requested item"""
        if self.config.mock_mode:
            sys_id = self._generate_sys_id()
            request = {
                "sys_id": sys_id,
                "number": self._generate_number("RITM"),
                "short_description": short_description,
                "description": description,
                "priority": priority,
                "state": "1",
                "opened_at": datetime.utcnow().isoformat() + "Z",
                "sys_created_on": datetime.utcnow().isoformat() + "Z",
            }
            if requested_for:
                request["requested_for"] = requested_for
            if catalog_item:
                request["cat_item"] = catalog_item
            self._mock_requests[sys_id] = request
            return {"result": request}

        data = {
            "short_description": short_description,
            "description": description,
            "priority": priority,
        }
        if requested_for:
            data["requested_for"] = requested_for
        if catalog_item:
            data["cat_item"] = catalog_item

        return await self._api_call("POST", "/table/sc_req_item", data)

    # ========================================================================
    # CONFIGURATION ITEM (CMDB) OPERATIONS
    # ========================================================================

    async def list_config_items(
        self,
        skip: int = 0,
        limit: int = 50,
        query: str = "",
        ci_class: str = "cmdb_ci"
    ) -> Dict[str, Any]:
        """List ServiceNow configuration items"""
        if self.config.mock_mode:
            results = self._paginate(self._mock_cmdb, skip, limit)
            return {"result": results}

        params = {"sysparm_offset": skip, "sysparm_limit": limit}
        if query:
            params["sysparm_query"] = query
        return await self._api_call("GET", f"/table/{ci_class}", params=params)

    async def get_config_item(self, ci_id: str, ci_class: str = "cmdb_ci") -> Dict[str, Any]:
        """Get ServiceNow configuration item by sys_id"""
        if self.config.mock_mode:
            if ci_id in self._mock_cmdb:
                return {"result": self._mock_cmdb[ci_id]}
            return {"error": "Configuration item not found"}

        return await self._api_call("GET", f"/table/{ci_class}/{ci_id}")

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        query: str = ""
    ) -> Dict[str, Any]:
        """List ServiceNow users"""
        if self.config.mock_mode:
            results = self._paginate(self._mock_users, skip, limit)
            return {"result": results}

        params = {"sysparm_offset": skip, "sysparm_limit": limit}
        if query:
            params["sysparm_query"] = query
        return await self._api_call("GET", "/table/sys_user", params=params)

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get ServiceNow user by sys_id"""
        if self.config.mock_mode:
            if user_id in self._mock_users:
                return {"result": self._mock_users[user_id]}
            return {"error": "User not found"}

        return await self._api_call("GET", f"/table/sys_user/{user_id}")

    async def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """Get ServiceNow user by email"""
        if self.config.mock_mode:
            for user in self._mock_users.values():
                if user.get("email") == email:
                    return {"result": [user]}
            return {"result": []}

        params = {"sysparm_query": f"email={email}", "sysparm_limit": 1}
        return await self._api_call("GET", "/table/sys_user", params=params)

    # ========================================================================
    # KNOWLEDGE BASE OPERATIONS
    # ========================================================================

    async def search_knowledge_base(
        self,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search ServiceNow knowledge base"""
        if self.config.mock_mode:
            results = []
            for article in self._mock_knowledge.values():
                if query.lower() in article.get("short_description", "").lower() or \
                   query.lower() in article.get("text", "").lower():
                    results.append(article)
                if len(results) >= limit:
                    break
            return {"result": results}

        params = {
            "sysparm_query": f"short_descriptionLIKE{query}^ORtextLIKE{query}",
            "sysparm_limit": limit
        }
        return await self._api_call("GET", "/table/kb_knowledge", params=params)

    async def get_knowledge_article(self, article_id: str) -> Dict[str, Any]:
        """Get ServiceNow knowledge article by sys_id"""
        if self.config.mock_mode:
            if article_id in self._mock_knowledge:
                return {"result": self._mock_knowledge[article_id]}
            return {"error": "Knowledge article not found"}

        return await self._api_call("GET", f"/table/kb_knowledge/{article_id}")

    # ========================================================================
    # SERVICE CATALOG OPERATIONS
    # ========================================================================

    async def list_catalog_items(
        self,
        skip: int = 0,
        limit: int = 50,
        category: str = ""
    ) -> Dict[str, Any]:
        """List ServiceNow service catalog items"""
        if self.config.mock_mode:
            results = list(self._mock_catalog.values())
            if category:
                results = [r for r in results if r.get("category") == category]
            return {"result": results[skip:skip + limit]}

        params = {"sysparm_offset": skip, "sysparm_limit": limit}
        if category:
            params["sysparm_query"] = f"category={category}"
        return await self._api_call("GET", "/table/sc_cat_item", params=params)

    async def get_catalog_item(self, item_id: str) -> Dict[str, Any]:
        """Get ServiceNow catalog item by sys_id"""
        if self.config.mock_mode:
            if item_id in self._mock_catalog:
                return {"result": self._mock_catalog[item_id]}
            return {"error": "Catalog item not found"}

        return await self._api_call("GET", f"/table/sc_cat_item/{item_id}")

    # ========================================================================
    # APPROVAL OPERATIONS
    # ========================================================================

    async def list_approvals(
        self,
        skip: int = 0,
        limit: int = 50,
        state: str = ""
    ) -> Dict[str, Any]:
        """List ServiceNow approvals"""
        if self.config.mock_mode:
            results = self._paginate(self._mock_approvals, skip, limit)
            if state:
                results = [r for r in results if r.get("state") == state]
            return {"result": results}

        params = {"sysparm_offset": skip, "sysparm_limit": limit}
        if state:
            params["sysparm_query"] = f"state={state}"
        return await self._api_call("GET", "/table/sysapproval_approver", params=params)

    async def approve_request(
        self,
        approval_id: str,
        comments: str = ""
    ) -> Dict[str, Any]:
        """Approve a ServiceNow approval request"""
        if self.config.mock_mode:
            if approval_id in self._mock_approvals:
                self._mock_approvals[approval_id]["state"] = "approved"
                self._mock_approvals[approval_id]["comments"] = comments
                self._mock_approvals[approval_id]["sys_updated_on"] = datetime.utcnow().isoformat() + "Z"
                return {"result": self._mock_approvals[approval_id]}
            return {"error": "Approval not found"}

        data = {
            "state": "approved",
            "comments": comments,
        }
        return await self._api_call("PUT", f"/table/sysapproval_approver/{approval_id}", data)

    async def reject_request(
        self,
        approval_id: str,
        comments: str = ""
    ) -> Dict[str, Any]:
        """Reject a ServiceNow approval request"""
        if self.config.mock_mode:
            if approval_id in self._mock_approvals:
                self._mock_approvals[approval_id]["state"] = "rejected"
                self._mock_approvals[approval_id]["comments"] = comments
                self._mock_approvals[approval_id]["sys_updated_on"] = datetime.utcnow().isoformat() + "Z"
                return {"result": self._mock_approvals[approval_id]}
            return {"error": "Approval not found"}

        data = {
            "state": "rejected",
            "comments": comments,
        }
        return await self._api_call("PUT", f"/table/sysapproval_approver/{approval_id}", data)

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check ServiceNow connectivity"""
        if self.config.mock_mode:
            return {
                "status": "healthy",
                "message": "Running in mock mode (no real ServiceNow instance)",
                "mode": "mock",
                "mock_data": {
                    "incidents": len(self._mock_incidents),
                    "changes": len(self._mock_changes),
                    "problems": len(self._mock_problems),
                    "users": len(self._mock_users),
                    "catalog_items": len(self._mock_catalog),
                    "knowledge_articles": len(self._mock_knowledge),
                    "cmdb_items": len(self._mock_cmdb),
                }
            }

        if not self.is_configured:
            return {
                "status": "unconfigured",
                "message": "ServiceNow credentials not configured"
            }

        try:
            result = await self._api_call(
                "GET",
                "/table/sys_user",
                params={"sysparm_limit": 1}
            )
            if "error" in result:
                return {
                    "status": "unhealthy",
                    "message": result.get("error"),
                    "details": result.get("details")
                }
            return {
                "status": "healthy",
                "message": "Connected to ServiceNow",
                "instance": self.config.instance_url
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e)
            }


# Global client instance
servicenow_client = ServiceNowClient()
