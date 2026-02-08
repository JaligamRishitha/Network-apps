#!/usr/bin/env python3
"""
MCP Server for Salesforce Clone Backend
Provides tools to interact with all CRM objects and operations

Runs in HTTP mode by default for remote connections.
Use --stdio flag for local stdio mode.
"""

import json
import httpx
import asyncio
import os
from typing import Any, Optional
from mcp.server import Server
from mcp.types import TextContent, Tool

# Configuration from environment variables
API_BASE_URL = os.environ.get("API_BASE_URL", "http://207.180.217.117:4799")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8090"))
DEFAULT_TOKEN = None

server = Server("salesforce-crm")


def set_token(token: str):
    """Set authentication token for API calls"""
    global DEFAULT_TOKEN
    DEFAULT_TOKEN = token


async def api_call(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    token: Optional[str] = None,
    params: Optional[dict] = None,
) -> dict:
    """Make authenticated API call to backend"""
    headers = {"Content-Type": "application/json"}
    if token or DEFAULT_TOKEN:
        headers["Authorization"] = f"Bearer {token or DEFAULT_TOKEN}"

    url = f"{API_BASE_URL}{endpoint}"

    async with httpx.AsyncClient(timeout=30.0) as client:
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
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code >= 400:
            return {
                "error": f"API Error {response.status_code}",
                "details": response.text,
            }
        return response.json()


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

# --- Authentication ---

async def login_salesforce(username: str, password: str):
    result = await api_call("POST", "/api/auth/login", {"username": username, "password": password})
    if "access_token" in result:
        set_token(result["access_token"])
    return [TextContent(type="text", text=json.dumps(result))]


async def get_current_user():
    result = await api_call("GET", "/api/auth/me")
    return [TextContent(type="text", text=json.dumps(result))]


async def list_users():
    result = await api_call("GET", "/api/auth/users")
    return [TextContent(type="text", text=json.dumps(result))]


# --- Contacts ---

async def list_contacts(skip: int = 0, limit: int = 50, search: str = ""):
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("GET", "/api/contacts", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_contact(contact_id: int):
    result = await api_call("GET", f"/api/contacts/{contact_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def create_contact(first_name: str, last_name: str, email: str = "", phone: str = "", account_id: int = None):
    data = {"first_name": first_name, "last_name": last_name, "email": email, "phone": phone}
    if account_id:
        data["account_id"] = account_id
    result = await api_call("POST", "/api/contacts", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def update_contact(contact_id: int, **kwargs):
    result = await api_call("PUT", f"/api/contacts/{contact_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


async def delete_contact(contact_id: int):
    result = await api_call("DELETE", f"/api/contacts/{contact_id}")
    return [TextContent(type="text", text=json.dumps(result))]


# --- Accounts ---

async def list_accounts(skip: int = 0, limit: int = 50, search: str = ""):
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("GET", "/api/accounts", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_account(account_id: int):
    result = await api_call("GET", f"/api/accounts/{account_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def create_account(name: str, industry: str = "", revenue: float = None, employees: int = None):
    data = {"name": name, "industry": industry}
    if revenue:
        data["revenue"] = revenue
    if employees:
        data["employees"] = employees
    result = await api_call("POST", "/api/accounts", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def update_account(account_id: int, **kwargs):
    result = await api_call("PUT", f"/api/accounts/{account_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


async def delete_account(account_id: int):
    result = await api_call("DELETE", f"/api/accounts/{account_id}")
    return [TextContent(type="text", text=json.dumps(result))]


# --- Leads ---

async def list_leads(skip: int = 0, limit: int = 50, search: str = ""):
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("GET", "/api/leads", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_lead(lead_id: int):
    result = await api_call("GET", f"/api/leads/{lead_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def create_lead(first_name: str, last_name: str, company: str, email: str = "", phone: str = "", lead_score: int = 0):
    data = {"first_name": first_name, "last_name": last_name, "company": company, "email": email, "phone": phone, "lead_score": lead_score}
    result = await api_call("POST", "/api/leads", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def update_lead(lead_id: int, **kwargs):
    result = await api_call("PUT", f"/api/leads/{lead_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


async def delete_lead(lead_id: int):
    result = await api_call("DELETE", f"/api/leads/{lead_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def convert_lead(lead_id: int):
    result = await api_call("POST", f"/api/leads/{lead_id}/convert", {})
    return [TextContent(type="text", text=json.dumps(result))]


# --- Opportunities ---

async def list_opportunities(skip: int = 0, limit: int = 50, search: str = ""):
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("GET", "/api/opportunities", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_opportunity(opportunity_id: int):
    result = await api_call("GET", f"/api/opportunities/{opportunity_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def create_opportunity(name: str, account_id: int, amount: float, stage: str = "Prospecting", close_date: str = ""):
    data = {"name": name, "account_id": account_id, "amount": amount, "stage": stage}
    if close_date:
        data["close_date"] = close_date
    result = await api_call("POST", "/api/opportunities", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def update_opportunity(opportunity_id: int, **kwargs):
    result = await api_call("PUT", f"/api/opportunities/{opportunity_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


async def delete_opportunity(opportunity_id: int):
    result = await api_call("DELETE", f"/api/opportunities/{opportunity_id}")
    return [TextContent(type="text", text=json.dumps(result))]


# --- Cases ---

async def list_cases(skip: int = 0, limit: int = 50, search: str = ""):
    params = {"skip": skip, "limit": limit}
    if search:
        params["search"] = search
    result = await api_call("GET", "/api/cases", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_case(case_id: int):
    result = await api_call("GET", f"/api/cases/{case_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def create_case(subject: str, contact_id: int, priority: str = "Medium", status: str = "New", description: str = ""):
    data = {"subject": subject, "contact_id": contact_id, "priority": priority, "status": status, "description": description}
    result = await api_call("POST", "/api/cases", data)
    return [TextContent(type="text", text=json.dumps(result))]


async def update_case(case_id: int, **kwargs):
    result = await api_call("PUT", f"/api/cases/{case_id}", kwargs)
    return [TextContent(type="text", text=json.dumps(result))]


async def delete_case(case_id: int):
    result = await api_call("DELETE", f"/api/cases/{case_id}")
    return [TextContent(type="text", text=json.dumps(result))]


async def escalate_case(case_id: int):
    result = await api_call("POST", f"/api/cases/{case_id}/escalate", {})
    return [TextContent(type="text", text=json.dumps(result))]


async def merge_cases(case_id_1: int, case_id_2: int):
    result = await api_call("POST", "/api/cases/merge", {"case_id_1": case_id_1, "case_id_2": case_id_2})
    return [TextContent(type="text", text=json.dumps(result))]


# --- Dashboard ---

async def get_dashboard_stats():
    result = await api_call("GET", "/api/dashboard/stats")
    return [TextContent(type="text", text=json.dumps(result))]


async def get_recent_records():
    result = await api_call("GET", "/api/dashboard/recent-records")
    return [TextContent(type="text", text=json.dumps(result))]


async def global_search(query: str):
    result = await api_call("GET", "/api/dashboard/search", params={"q": query})
    return [TextContent(type="text", text=json.dumps(result))]


# --- Activities ---

async def list_activities(skip: int = 0, limit: int = 50):
    result = await api_call("GET", "/api/activities", params={"skip": skip, "limit": limit})
    return [TextContent(type="text", text=json.dumps(result))]


async def create_activity(activity_type: str, subject: str, related_object_type: str, related_object_id: int, description: str = ""):
    data = {"activity_type": activity_type, "subject": subject, "related_object_type": related_object_type, "related_object_id": related_object_id, "description": description}
    result = await api_call("POST", "/api/activities", data)
    return [TextContent(type="text", text=json.dumps(result))]


# --- Logs ---

async def get_logs(skip: int = 0, limit: int = 50):
    result = await api_call("GET", "/api/logs", params={"skip": skip, "limit": limit})
    return [TextContent(type="text", text=json.dumps(result))]


# --- Health ---

async def health_check():
    result = await api_call("GET", "/api/health")
    return [TextContent(type="text", text=json.dumps(result))]


# --- Account Creation Validation ---

async def validate_account_creation(account_name: str, email: str = "", first_name: str = "", last_name: str = "", phone: str = ""):
    account_name = account_name.strip()
    email = email.strip() if email else ""

    if not account_name:
        result = {"valid": False, "reason": "missing_required_fields", "missing_fields": ["account_name"], "message": "Missing required field: account_name"}
        return [TextContent(type="text", text=json.dumps(result))]

    accounts_result = await api_call("GET", "/api/accounts", params={"search": account_name, "limit": 50})
    if "error" not in accounts_result:
        accounts = accounts_result.get("accounts", accounts_result.get("data", []))
        if isinstance(accounts, list):
            for acct in accounts:
                existing_name = (acct.get("name") or acct.get("account_name") or "").lower()
                if existing_name == account_name.lower():
                    result = {"valid": False, "reason": "duplicate_account", "duplicate_type": "account", "existing_record": acct, "message": f"An account with name '{account_name}' already exists in Salesforce"}
                    return [TextContent(type="text", text=json.dumps(result))]

    if email:
        contacts_result = await api_call("GET", "/api/contacts", params={"search": email, "limit": 50})
        if "error" not in contacts_result:
            contacts = contacts_result.get("contacts", contacts_result.get("data", []))
            if isinstance(contacts, list):
                for contact in contacts:
                    existing_email = (contact.get("email") or "").lower()
                    if existing_email == email.lower():
                        result = {"valid": False, "reason": "duplicate_contact", "duplicate_type": "contact", "existing_record": contact, "message": f"A contact with email '{email}' already exists in Salesforce"}
                        return [TextContent(type="text", text=json.dumps(result))]

    result = {"valid": True, "reason": "all_checks_passed", "message": "Account creation validation passed - no duplicates found", "validated_fields": {"account_name": account_name, "email": email or "not provided", "first_name": first_name, "last_name": last_name, "phone": phone}}
    return [TextContent(type="text", text=json.dumps(result))]


# --- Client User Tools ---

async def sf_validate_client_user(email: str, account_name: str = ""):
    """Validate a client user request in Salesforce."""
    result = {}

    if account_name and account_name.strip():
        account_name = account_name.strip()
        accounts_result = await api_call("GET", "/api/accounts", params={"search": account_name, "limit": 50})
        matched_account = None
        if "error" not in accounts_result:
            accounts = accounts_result.get("accounts", accounts_result.get("data", []))
            if isinstance(accounts, list):
                for acct in accounts:
                    existing_name = (acct.get("name") or acct.get("account_name") or "").lower()
                    if existing_name == account_name.lower():
                        matched_account = acct
                        break

        if matched_account:
            result["account_valid"] = True
            result["account_id"] = matched_account.get("id")
            result["account_name"] = matched_account.get("name") or matched_account.get("account_name")
        else:
            result["account_valid"] = False
            result["account_name_searched"] = account_name
            result["message"] = f"No account found with name '{account_name}'. Cannot create user under a non-existent account."
            return [TextContent(type="text", text=json.dumps(result))]

    user_result = await api_call("POST", "/api/client-users/validate", {"email": email})
    raw_exists = user_result.get("exists", False)
    is_active = user_result.get("is_active", False)

    if raw_exists and not is_active:
        # User exists in DB but is inactive (pending activation) — not a duplicate
        result["user_exists"] = False
        result["pending_activation"] = True
        result["client_user_id"] = user_result.get("client_user_id")
        result["user_account_id"] = user_result.get("account_id")
        result["user_account_name"] = user_result.get("account_name")
        result["user_name"] = user_result.get("name")
        result["message"] = f"User '{user_result.get('name', email)}' is pending activation. Approve to activate."
    elif raw_exists and is_active:
        # Truly active user — duplicate
        result["user_exists"] = True
        result["client_user_id"] = user_result.get("client_user_id")
        result["user_account_id"] = user_result.get("account_id")
        result["user_account_name"] = user_result.get("account_name")
        result["is_active"] = True
        result["user_name"] = user_result.get("name")
        result["message"] = f"Client user with email '{email}' already exists and is active."
    else:
        result["user_exists"] = False
        result["message"] = "Validation passed. Account exists and email is available for new user creation."

    return [TextContent(type="text", text=json.dumps(result))]


async def sf_update_client_password(email: str, new_password: str):
    result = await api_call("PATCH", f"/api/client-users/{email}/password", {"new_password": new_password})
    return [TextContent(type="text", text=json.dumps(result))]


async def sf_activate_client_user(user_id: int):
    result = await api_call("PATCH", f"/api/client-users/{user_id}/activate", {})
    return [TextContent(type="text", text=json.dumps(result))]


async def list_client_users(account_id: int = None):
    params = {}
    if account_id:
        params["account_id"] = account_id
    result = await api_call("GET", "/api/client-users", params=params)
    return [TextContent(type="text", text=json.dumps(result))]


async def get_client_user(user_id: int):
    result = await api_call("GET", f"/api/client-users/{user_id}")
    return [TextContent(type="text", text=json.dumps(result))]


# ============================================================================
# TOOL DISPATCH MAP
# ============================================================================

TOOL_DISPATCH = {
    "login_salesforce": login_salesforce,
    "get_current_user": get_current_user,
    "list_users": list_users,
    "list_contacts": list_contacts,
    "get_contact": get_contact,
    "create_contact": create_contact,
    "update_contact": update_contact,
    "delete_contact": delete_contact,
    "list_accounts": list_accounts,
    "get_account": get_account,
    "create_account": create_account,
    "update_account": update_account,
    "delete_account": delete_account,
    "list_leads": list_leads,
    "get_lead": get_lead,
    "create_lead": create_lead,
    "update_lead": update_lead,
    "delete_lead": delete_lead,
    "convert_lead": convert_lead,
    "list_opportunities": list_opportunities,
    "get_opportunity": get_opportunity,
    "create_opportunity": create_opportunity,
    "update_opportunity": update_opportunity,
    "delete_opportunity": delete_opportunity,
    "list_cases": list_cases,
    "get_case": get_case,
    "create_case": create_case,
    "update_case": update_case,
    "delete_case": delete_case,
    "escalate_case": escalate_case,
    "merge_cases": merge_cases,
    "get_dashboard_stats": get_dashboard_stats,
    "get_recent_records": get_recent_records,
    "global_search": global_search,
    "list_activities": list_activities,
    "create_activity": create_activity,
    "get_logs": get_logs,
    "health_check": health_check,
    "validate_account_creation": validate_account_creation,
    "sf_validate_client_user": sf_validate_client_user,
    "sf_update_client_password": sf_update_client_password,
    "sf_activate_client_user": sf_activate_client_user,
    "list_client_users": list_client_users,
    "get_client_user": get_client_user,
}


# ============================================================================
# MCP TOOL REGISTRATION - list_tools and call_tool handlers
# ============================================================================

@server.list_tools()
async def handle_list_tools():
    """Return the list of available Salesforce tools"""
    return [
        # --- Authentication ---
        Tool(name="login_salesforce", description="Login to Salesforce and get JWT token", inputSchema={
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "Salesforce username"},
                "password": {"type": "string", "description": "Salesforce password"},
            },
            "required": ["username", "password"],
        }),
        Tool(name="get_current_user", description="Get current authenticated user", inputSchema={
            "type": "object", "properties": {}, "required": [],
        }),
        Tool(name="list_users", description="List all system users", inputSchema={
            "type": "object", "properties": {}, "required": [],
        }),
        # --- Contacts ---
        Tool(name="list_contacts", description="List contacts with optional search", inputSchema={
            "type": "object",
            "properties": {
                "skip": {"type": "integer", "description": "Number of records to skip", "default": 0},
                "limit": {"type": "integer", "description": "Max records to return", "default": 50},
                "search": {"type": "string", "description": "Search query", "default": ""},
            },
            "required": [],
        }),
        Tool(name="get_contact", description="Get contact by ID", inputSchema={
            "type": "object",
            "properties": {"contact_id": {"type": "integer", "description": "Contact ID"}},
            "required": ["contact_id"],
        }),
        Tool(name="create_contact", description="Create new contact", inputSchema={
            "type": "object",
            "properties": {
                "first_name": {"type": "string", "description": "First name"},
                "last_name": {"type": "string", "description": "Last name"},
                "email": {"type": "string", "description": "Email address", "default": ""},
                "phone": {"type": "string", "description": "Phone number", "default": ""},
                "account_id": {"type": "integer", "description": "Associated account ID"},
            },
            "required": ["first_name", "last_name"],
        }),
        Tool(name="update_contact", description="Update contact fields", inputSchema={
            "type": "object",
            "properties": {"contact_id": {"type": "integer", "description": "Contact ID"}},
            "required": ["contact_id"],
        }),
        Tool(name="delete_contact", description="Delete contact", inputSchema={
            "type": "object",
            "properties": {"contact_id": {"type": "integer", "description": "Contact ID"}},
            "required": ["contact_id"],
        }),
        # --- Accounts ---
        Tool(name="list_accounts", description="List accounts with optional search", inputSchema={
            "type": "object",
            "properties": {
                "skip": {"type": "integer", "description": "Number of records to skip", "default": 0},
                "limit": {"type": "integer", "description": "Max records to return", "default": 50},
                "search": {"type": "string", "description": "Search query", "default": ""},
            },
            "required": [],
        }),
        Tool(name="get_account", description="Get account by ID", inputSchema={
            "type": "object",
            "properties": {"account_id": {"type": "integer", "description": "Account ID"}},
            "required": ["account_id"],
        }),
        Tool(name="create_account", description="Create new account", inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Account name"},
                "industry": {"type": "string", "description": "Industry", "default": ""},
                "revenue": {"type": "number", "description": "Annual revenue"},
                "employees": {"type": "integer", "description": "Number of employees"},
            },
            "required": ["name"],
        }),
        Tool(name="update_account", description="Update account fields", inputSchema={
            "type": "object",
            "properties": {"account_id": {"type": "integer", "description": "Account ID"}},
            "required": ["account_id"],
        }),
        Tool(name="delete_account", description="Delete account", inputSchema={
            "type": "object",
            "properties": {"account_id": {"type": "integer", "description": "Account ID"}},
            "required": ["account_id"],
        }),
        # --- Leads ---
        Tool(name="list_leads", description="List leads with optional search", inputSchema={
            "type": "object",
            "properties": {
                "skip": {"type": "integer", "description": "Number of records to skip", "default": 0},
                "limit": {"type": "integer", "description": "Max records to return", "default": 50},
                "search": {"type": "string", "description": "Search query", "default": ""},
            },
            "required": [],
        }),
        Tool(name="get_lead", description="Get lead by ID", inputSchema={
            "type": "object",
            "properties": {"lead_id": {"type": "integer", "description": "Lead ID"}},
            "required": ["lead_id"],
        }),
        Tool(name="create_lead", description="Create new lead (auto-assigned)", inputSchema={
            "type": "object",
            "properties": {
                "first_name": {"type": "string", "description": "First name"},
                "last_name": {"type": "string", "description": "Last name"},
                "company": {"type": "string", "description": "Company name"},
                "email": {"type": "string", "description": "Email", "default": ""},
                "phone": {"type": "string", "description": "Phone", "default": ""},
                "lead_score": {"type": "integer", "description": "Lead score", "default": 0},
            },
            "required": ["first_name", "last_name", "company"],
        }),
        Tool(name="update_lead", description="Update lead fields", inputSchema={
            "type": "object",
            "properties": {"lead_id": {"type": "integer", "description": "Lead ID"}},
            "required": ["lead_id"],
        }),
        Tool(name="delete_lead", description="Delete lead", inputSchema={
            "type": "object",
            "properties": {"lead_id": {"type": "integer", "description": "Lead ID"}},
            "required": ["lead_id"],
        }),
        Tool(name="convert_lead", description="Convert lead to account, contact, and opportunity", inputSchema={
            "type": "object",
            "properties": {"lead_id": {"type": "integer", "description": "Lead ID"}},
            "required": ["lead_id"],
        }),
        # --- Opportunities ---
        Tool(name="list_opportunities", description="List opportunities with optional search", inputSchema={
            "type": "object",
            "properties": {
                "skip": {"type": "integer", "description": "Number of records to skip", "default": 0},
                "limit": {"type": "integer", "description": "Max records to return", "default": 50},
                "search": {"type": "string", "description": "Search query", "default": ""},
            },
            "required": [],
        }),
        Tool(name="get_opportunity", description="Get opportunity by ID", inputSchema={
            "type": "object",
            "properties": {"opportunity_id": {"type": "integer", "description": "Opportunity ID"}},
            "required": ["opportunity_id"],
        }),
        Tool(name="create_opportunity", description="Create new opportunity", inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Opportunity name"},
                "account_id": {"type": "integer", "description": "Account ID"},
                "amount": {"type": "number", "description": "Deal amount"},
                "stage": {"type": "string", "description": "Sales stage", "default": "Prospecting"},
                "close_date": {"type": "string", "description": "Expected close date", "default": ""},
            },
            "required": ["name", "account_id", "amount"],
        }),
        Tool(name="update_opportunity", description="Update opportunity fields", inputSchema={
            "type": "object",
            "properties": {"opportunity_id": {"type": "integer", "description": "Opportunity ID"}},
            "required": ["opportunity_id"],
        }),
        Tool(name="delete_opportunity", description="Delete opportunity", inputSchema={
            "type": "object",
            "properties": {"opportunity_id": {"type": "integer", "description": "Opportunity ID"}},
            "required": ["opportunity_id"],
        }),
        # --- Cases ---
        Tool(name="list_cases", description="List cases with optional search", inputSchema={
            "type": "object",
            "properties": {
                "skip": {"type": "integer", "description": "Number of records to skip", "default": 0},
                "limit": {"type": "integer", "description": "Max records to return", "default": 50},
                "search": {"type": "string", "description": "Search query", "default": ""},
            },
            "required": [],
        }),
        Tool(name="get_case", description="Get case by ID", inputSchema={
            "type": "object",
            "properties": {"case_id": {"type": "integer", "description": "Case ID"}},
            "required": ["case_id"],
        }),
        Tool(name="create_case", description="Create new case (auto-assigned)", inputSchema={
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Case subject"},
                "contact_id": {"type": "integer", "description": "Contact ID"},
                "priority": {"type": "string", "description": "Priority level", "default": "Medium"},
                "status": {"type": "string", "description": "Case status", "default": "New"},
                "description": {"type": "string", "description": "Case description", "default": ""},
            },
            "required": ["subject", "contact_id"],
        }),
        Tool(name="update_case", description="Update case fields", inputSchema={
            "type": "object",
            "properties": {"case_id": {"type": "integer", "description": "Case ID"}},
            "required": ["case_id"],
        }),
        Tool(name="delete_case", description="Delete case", inputSchema={
            "type": "object",
            "properties": {"case_id": {"type": "integer", "description": "Case ID"}},
            "required": ["case_id"],
        }),
        Tool(name="escalate_case", description="Escalate case priority", inputSchema={
            "type": "object",
            "properties": {"case_id": {"type": "integer", "description": "Case ID"}},
            "required": ["case_id"],
        }),
        Tool(name="merge_cases", description="Merge duplicate cases", inputSchema={
            "type": "object",
            "properties": {
                "case_id_1": {"type": "integer", "description": "First case ID"},
                "case_id_2": {"type": "integer", "description": "Second case ID"},
            },
            "required": ["case_id_1", "case_id_2"],
        }),
        # --- Dashboard ---
        Tool(name="get_dashboard_stats", description="Get dashboard statistics", inputSchema={
            "type": "object", "properties": {}, "required": [],
        }),
        Tool(name="get_recent_records", description="Get recent records", inputSchema={
            "type": "object", "properties": {}, "required": [],
        }),
        Tool(name="global_search", description="Global search across all objects", inputSchema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        }),
        # --- Activities ---
        Tool(name="list_activities", description="List activities", inputSchema={
            "type": "object",
            "properties": {
                "skip": {"type": "integer", "description": "Records to skip", "default": 0},
                "limit": {"type": "integer", "description": "Max records", "default": 50},
            },
            "required": [],
        }),
        Tool(name="create_activity", description="Create activity log entry", inputSchema={
            "type": "object",
            "properties": {
                "activity_type": {"type": "string", "description": "Type of activity"},
                "subject": {"type": "string", "description": "Activity subject"},
                "related_object_type": {"type": "string", "description": "Related object type"},
                "related_object_id": {"type": "integer", "description": "Related object ID"},
                "description": {"type": "string", "description": "Activity description", "default": ""},
            },
            "required": ["activity_type", "subject", "related_object_type", "related_object_id"],
        }),
        # --- Logs ---
        Tool(name="get_logs", description="Get system logs", inputSchema={
            "type": "object",
            "properties": {
                "skip": {"type": "integer", "description": "Records to skip", "default": 0},
                "limit": {"type": "integer", "description": "Max records", "default": 50},
            },
            "required": [],
        }),
        # --- Health ---
        Tool(name="health_check", description="Check Salesforce API health", inputSchema={
            "type": "object", "properties": {}, "required": [],
        }),
        # --- Account Creation Validation ---
        Tool(name="validate_account_creation", description="Validate account/client creation request - checks for duplicate accounts and contacts", inputSchema={
            "type": "object",
            "properties": {
                "account_name": {"type": "string", "description": "Account name to validate"},
                "email": {"type": "string", "description": "Contact email to check for duplicates", "default": ""},
                "first_name": {"type": "string", "description": "Contact first name", "default": ""},
                "last_name": {"type": "string", "description": "Contact last name", "default": ""},
                "phone": {"type": "string", "description": "Contact phone", "default": ""},
            },
            "required": ["account_name"],
        }),
        # --- Client User Tools ---
        Tool(name="sf_validate_client_user", description="Validate a client user by email. Checks if the email is already registered as an active user. Only email is required. account_name is optional.", inputSchema={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Client user email to validate"},
                "account_name": {"type": "string", "description": "Optional - account name to check existence", "default": ""},
            },
            "required": ["email"],
        }),
        Tool(name="sf_update_client_password", description="Update a client user's password by email", inputSchema={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Client user email"},
                "new_password": {"type": "string", "description": "New password to set"},
            },
            "required": ["email", "new_password"],
        }),
        Tool(name="sf_activate_client_user", description="Activate a client user account by user ID", inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "Client user ID to activate"},
            },
            "required": ["user_id"],
        }),
        Tool(name="list_client_users", description="List client users, optionally filtered by account ID", inputSchema={
            "type": "object",
            "properties": {
                "account_id": {"type": "integer", "description": "Filter by account ID"},
            },
            "required": [],
        }),
        Tool(name="get_client_user", description="Get a specific client user by ID", inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "Client user ID"},
            },
            "required": ["user_id"],
        }),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Dispatch tool calls to the correct function by name"""
    if name not in TOOL_DISPATCH:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    func = TOOL_DISPATCH[name]

    # Handle tools that accept **kwargs (update tools)
    if name in ("update_contact", "update_account", "update_lead", "update_opportunity", "update_case"):
        id_key = list(arguments.keys())[0] if arguments else None
        if id_key:
            id_val = arguments.pop(id_key)
            return await func(id_val, **arguments)

    return await func(**arguments)


# ============================================================================
# SERVER STARTUP
# ============================================================================

def run_http_server():
    """Run MCP server in HTTP/SSE mode for remote connections"""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    import uvicorn

    # SSE transport for HTTP-based MCP connections
    sse = SseServerTransport("/messages")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    # CORS middleware for cross-origin requests
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ],
        middleware=middleware,
    )

    print(f"Starting MCP server in HTTP mode")
    print(f"  Host: {MCP_HOST}")
    print(f"  Port: {MCP_PORT}")
    print(f"  API Backend: {API_BASE_URL}")
    print(f"  SSE Endpoint: http://{MCP_HOST}:{MCP_PORT}/sse")
    print(f"  Tools registered: {len(TOOL_DISPATCH)}")
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)


def run_stdio_server():
    """Run MCP server in stdio mode for local use"""
    print("Starting MCP server in stdio mode")
    server.run()


if __name__ == "__main__":
    import sys

    # Default to HTTP mode, use --stdio for local mode
    if "--stdio" in sys.argv:
        run_stdio_server()
    else:
        run_http_server()
