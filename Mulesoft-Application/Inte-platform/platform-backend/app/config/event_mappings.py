"""
Event Mappings Configuration - Maps system events to ticket categories, priorities, and SLA settings.
"""

from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum


class EventType(str, Enum):
    """Supported event types from source systems"""
    USER_CREATION = "user_creation"
    PASSWORD_RESET = "password_reset"
    WORK_ORDER = "work_order"
    ACCESS_REQUEST = "access_request"
    SYSTEM_ALERT = "system_alert"
    HARDWARE_REQUEST = "hardware_request"
    SOFTWARE_REQUEST = "software_request"
    NETWORK_ISSUE = "network_issue"
    SECURITY_INCIDENT = "security_incident"


class Priority(str, Enum):
    """Ticket priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EventMapping:
    """Configuration for a single event type mapping"""
    category: str
    subcategory: str
    default_priority: Priority
    sla_hours: int
    assignment_group: str
    ticket_type: str = "incident"
    requires_approval: bool = False
    auto_assign: bool = True


# Event type to category/SLA mapping configuration
EVENT_MAPPINGS: Dict[str, EventMapping] = {
    EventType.USER_CREATION: EventMapping(
        category="User Account",
        subcategory="Account Creation",
        default_priority=Priority.MEDIUM,
        sla_hours=24,
        assignment_group="Identity Management",
        ticket_type="service_request",
        requires_approval=True
    ),
    EventType.PASSWORD_RESET: EventMapping(
        category="User Account",
        subcategory="Password Reset",
        default_priority=Priority.HIGH,
        sla_hours=4,
        assignment_group="IT Service Desk",
        ticket_type="incident"
    ),
    EventType.WORK_ORDER: EventMapping(
        category="Work Order",
        subcategory="General",
        default_priority=Priority.MEDIUM,
        sla_hours=48,
        assignment_group="Operations",
        ticket_type="service_request",
        requires_approval=True
    ),
    EventType.ACCESS_REQUEST: EventMapping(
        category="Access",
        subcategory="Access Request",
        default_priority=Priority.MEDIUM,
        sla_hours=24,
        assignment_group="Access Management",
        ticket_type="service_request",
        requires_approval=True
    ),
    EventType.SYSTEM_ALERT: EventMapping(
        category="System",
        subcategory="Alert",
        default_priority=Priority.HIGH,
        sla_hours=4,
        assignment_group="Infrastructure",
        ticket_type="incident"
    ),
    EventType.HARDWARE_REQUEST: EventMapping(
        category="Hardware",
        subcategory="Hardware Request",
        default_priority=Priority.LOW,
        sla_hours=72,
        assignment_group="IT Assets",
        ticket_type="service_request",
        requires_approval=True
    ),
    EventType.SOFTWARE_REQUEST: EventMapping(
        category="Software",
        subcategory="Software Installation",
        default_priority=Priority.MEDIUM,
        sla_hours=48,
        assignment_group="Desktop Support",
        ticket_type="service_request",
        requires_approval=True
    ),
    EventType.NETWORK_ISSUE: EventMapping(
        category="Network",
        subcategory="Connectivity",
        default_priority=Priority.HIGH,
        sla_hours=4,
        assignment_group="Network Operations",
        ticket_type="incident"
    ),
    EventType.SECURITY_INCIDENT: EventMapping(
        category="Security",
        subcategory="Security Incident",
        default_priority=Priority.CRITICAL,
        sla_hours=1,
        assignment_group="Security Operations",
        ticket_type="incident"
    ),
}

# SLA definitions by priority
SLA_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    Priority.CRITICAL: {
        "response_time_minutes": 30,
        "resolution_time_hours": 4,
        "business_hours_only": False,  # 24/7
        "escalation_levels": [
            {"level": 1, "after_minutes": 15, "notify": ["team_lead", "manager"]},
            {"level": 2, "after_minutes": 30, "notify": ["director"]},
            {"level": 3, "after_minutes": 60, "notify": ["vp", "cio"]},
        ]
    },
    Priority.HIGH: {
        "response_time_minutes": 60,
        "resolution_time_hours": 8,
        "business_hours_only": True,
        "escalation_levels": [
            {"level": 1, "after_minutes": 30, "notify": ["team_lead"]},
            {"level": 2, "after_minutes": 120, "notify": ["manager"]},
            {"level": 3, "after_minutes": 240, "notify": ["director"]},
        ]
    },
    Priority.MEDIUM: {
        "response_time_minutes": 240,
        "resolution_time_hours": 24,
        "business_hours_only": True,
        "escalation_levels": [
            {"level": 1, "after_minutes": 120, "notify": ["team_lead"]},
            {"level": 2, "after_minutes": 480, "notify": ["manager"]},
        ]
    },
    Priority.LOW: {
        "response_time_minutes": 480,
        "resolution_time_hours": 72,
        "business_hours_only": True,
        "escalation_levels": [
            {"level": 1, "after_minutes": 480, "notify": ["team_lead"]},
        ]
    },
}

# Keyword patterns for auto-categorization
KEYWORD_PATTERNS: Dict[str, Dict[str, list]] = {
    "User Account": {
        "keywords": ["user", "account", "login", "password", "credential", "authentication"],
        "subcategories": {
            "Account Creation": ["new user", "create account", "onboarding", "new employee"],
            "Password Reset": ["password", "reset", "forgot", "locked out", "unlock"],
            "Account Deactivation": ["deactivate", "disable", "offboarding", "terminate"],
        }
    },
    "Hardware": {
        "keywords": ["laptop", "computer", "monitor", "keyboard", "mouse", "printer", "hardware"],
        "subcategories": {
            "Hardware Request": ["new laptop", "request computer", "need monitor"],
            "Hardware Repair": ["broken", "not working", "repair", "fix", "replace"],
        }
    },
    "Software": {
        "keywords": ["software", "application", "install", "license", "program"],
        "subcategories": {
            "Software Installation": ["install", "setup", "configure"],
            "Software Issue": ["crash", "error", "not working", "bug"],
        }
    },
    "Network": {
        "keywords": ["network", "internet", "wifi", "vpn", "connection", "connectivity"],
        "subcategories": {
            "Connectivity": ["cannot connect", "slow", "intermittent", "down"],
            "VPN": ["vpn", "remote access", "tunnel"],
        }
    },
    "Security": {
        "keywords": ["security", "virus", "malware", "phishing", "breach", "suspicious"],
        "subcategories": {
            "Security Incident": ["breach", "attack", "compromised"],
            "Malware": ["virus", "malware", "ransomware"],
            "Phishing": ["phishing", "suspicious email", "scam"],
        }
    },
    "Access": {
        "keywords": ["access", "permission", "role", "group", "authorization"],
        "subcategories": {
            "Access Request": ["need access", "request permission", "grant access"],
            "Access Revocation": ["remove access", "revoke", "disable access"],
        }
    },
}

# Source system configurations
SOURCE_SYSTEMS: Dict[str, Dict[str, Any]] = {
    "salesforce": {
        "name": "Salesforce",
        "webhook_secret": "mulesoft-salesforce-shared-secret-2024",
        "default_priority": Priority.MEDIUM,
        "trusted": True,
    },
    "sap": {
        "name": "SAP",
        "webhook_secret": "mulesoft-sap-shared-secret-2024",
        "default_priority": Priority.MEDIUM,
        "trusted": True,
    },
    "monitoring": {
        "name": "Monitoring System",
        "webhook_secret": "mulesoft-monitoring-shared-secret-2024",
        "default_priority": Priority.HIGH,
        "trusted": True,
    },
    "email": {
        "name": "Email Gateway",
        "webhook_secret": None,
        "default_priority": Priority.MEDIUM,
        "trusted": False,
    },
}


def get_event_mapping(event_type: str) -> EventMapping:
    """Get the mapping configuration for an event type"""
    # Try exact match first
    if event_type in EVENT_MAPPINGS:
        return EVENT_MAPPINGS[event_type]

    # Try case-insensitive match
    for key, mapping in EVENT_MAPPINGS.items():
        if key.lower() == event_type.lower():
            return mapping

    # Return default mapping for unknown events
    return EventMapping(
        category="General",
        subcategory="Other",
        default_priority=Priority.MEDIUM,
        sla_hours=24,
        assignment_group="IT Service Desk",
        ticket_type="service_request"
    )


def get_sla_definition(priority: str) -> Dict[str, Any]:
    """Get SLA definition for a priority level"""
    return SLA_DEFINITIONS.get(priority, SLA_DEFINITIONS[Priority.MEDIUM])


def get_source_system_config(source: str) -> Dict[str, Any]:
    """Get configuration for a source system"""
    return SOURCE_SYSTEMS.get(source.lower(), {
        "name": source,
        "webhook_secret": None,
        "default_priority": Priority.MEDIUM,
        "trusted": False,
    })
