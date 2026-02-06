"""
Categorization Engine - Auto-categorizes tickets based on event type and content.
"""

from typing import Optional, Tuple, Dict, List
from sqlalchemy.orm import Session
import re


# Keyword patterns for auto-categorization
CATEGORY_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "User Account": {
        "keywords": ["user", "account", "login", "password", "credential", "authentication", "sso", "mfa"],
        "subcategories": {
            "Account Creation": ["new user", "create account", "onboarding", "new employee", "provision"],
            "Password Reset": ["password", "reset", "forgot", "locked out", "unlock", "expired password"],
            "Account Deactivation": ["deactivate", "disable", "offboarding", "terminate", "revoke"],
            "Account Modification": ["modify", "update account", "change email", "change name"],
        }
    },
    "Hardware": {
        "keywords": ["laptop", "computer", "monitor", "keyboard", "mouse", "printer", "hardware", "device", "workstation"],
        "subcategories": {
            "Hardware Request": ["new laptop", "request computer", "need monitor", "order", "procurement"],
            "Hardware Repair": ["broken", "not working", "repair", "fix", "replace", "damaged", "malfunction"],
            "Hardware Return": ["return", "decommission", "dispose", "recycle"],
        }
    },
    "Software": {
        "keywords": ["software", "application", "install", "license", "program", "app", "tool"],
        "subcategories": {
            "Software Installation": ["install", "setup", "configure", "deploy"],
            "Software Issue": ["crash", "error", "not working", "bug", "freeze", "slow"],
            "Software License": ["license", "subscription", "renewal", "activation"],
            "Software Removal": ["uninstall", "remove", "delete"],
        }
    },
    "Network": {
        "keywords": ["network", "internet", "wifi", "vpn", "connection", "connectivity", "lan", "wan"],
        "subcategories": {
            "Connectivity": ["cannot connect", "slow connection", "intermittent", "down", "outage"],
            "VPN": ["vpn", "remote access", "tunnel", "ssl vpn"],
            "Wireless": ["wifi", "wireless", "wlan", "access point"],
        }
    },
    "Security": {
        "keywords": ["security", "virus", "malware", "phishing", "breach", "suspicious", "threat", "vulnerability"],
        "subcategories": {
            "Security Incident": ["breach", "attack", "compromised", "unauthorized access", "data leak"],
            "Malware": ["virus", "malware", "ransomware", "trojan", "worm", "spyware"],
            "Phishing": ["phishing", "suspicious email", "scam", "spoofing"],
            "Vulnerability": ["vulnerability", "patch", "cve", "exploit"],
        }
    },
    "Access": {
        "keywords": ["access", "permission", "role", "group", "authorization", "privilege"],
        "subcategories": {
            "Access Request": ["need access", "request permission", "grant access", "add to group"],
            "Access Revocation": ["remove access", "revoke", "disable access", "remove from group"],
            "Access Review": ["review access", "audit", "recertification"],
        }
    },
    "Email": {
        "keywords": ["email", "outlook", "mailbox", "calendar", "teams", "exchange"],
        "subcategories": {
            "Email Configuration": ["configure email", "setup outlook", "email settings"],
            "Email Issue": ["cannot send", "cannot receive", "email not working", "mailbox full"],
            "Distribution List": ["distribution list", "mailing list", "group email"],
        }
    },
    "System": {
        "keywords": ["system", "server", "database", "alert", "monitoring", "performance"],
        "subcategories": {
            "Alert": ["alert", "warning", "critical", "threshold", "monitoring"],
            "Performance": ["slow", "performance", "latency", "response time"],
            "Outage": ["outage", "down", "unavailable", "offline"],
        }
    },
    "Work Order": {
        "keywords": ["work order", "task", "project", "maintenance", "change"],
        "subcategories": {
            "General": ["general", "task", "work order"],
            "Maintenance": ["maintenance", "scheduled", "preventive"],
            "Project Work": ["project", "implementation", "deployment"],
        }
    },
}

# Priority keywords
PRIORITY_KEYWORDS: Dict[str, List[str]] = {
    "critical": ["critical", "emergency", "urgent", "production down", "major outage", "security breach", "ceo", "executive"],
    "high": ["high priority", "important", "asap", "immediate", "blocking", "major issue"],
    "medium": ["medium", "normal", "standard"],
    "low": ["low priority", "when possible", "minor", "cosmetic", "nice to have"],
}


def categorize_by_keywords(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Categorize text based on keyword matching.

    Returns:
        Tuple of (category, subcategory)
    """
    text_lower = text.lower()
    best_category = None
    best_subcategory = None
    best_score = 0

    for category, config in CATEGORY_KEYWORDS.items():
        # Check main category keywords
        category_score = sum(1 for kw in config["keywords"] if kw in text_lower)

        if category_score > 0:
            # Check subcategory keywords
            for subcategory, keywords in config.get("subcategories", {}).items():
                subcategory_score = sum(1 for kw in keywords if kw in text_lower)
                total_score = category_score + subcategory_score * 2  # Weight subcategory matches higher

                if total_score > best_score:
                    best_score = total_score
                    best_category = category
                    best_subcategory = subcategory

            # If no subcategory matched, still use the category
            if best_category != category and category_score > best_score:
                best_score = category_score
                best_category = category
                best_subcategory = list(config.get("subcategories", {}).keys())[0] if config.get("subcategories") else "General"

    return best_category, best_subcategory


def detect_priority(text: str, default_priority: str = "medium") -> str:
    """
    Detect priority from text content.

    Args:
        text: The text to analyze
        default_priority: Default priority if none detected

    Returns:
        Priority string (critical, high, medium, low)
    """
    text_lower = text.lower()

    # Check in order of priority (highest first)
    for priority in ["critical", "high", "low", "medium"]:
        keywords = PRIORITY_KEYWORDS.get(priority, [])
        if any(kw in text_lower for kw in keywords):
            return priority

    return default_priority


def categorize_event(
    event_type: str,
    title: str,
    description: str = "",
    category: Optional[str] = None,
    subcategory: Optional[str] = None
) -> Tuple[str, str]:
    """
    Categorize an event based on type and content.

    Args:
        event_type: The type of system event
        title: Event title
        description: Event description
        category: Pre-assigned category (if any)
        subcategory: Pre-assigned subcategory (if any)

    Returns:
        Tuple of (category, subcategory)
    """
    # If category is already provided, use it
    if category and subcategory:
        return category, subcategory

    # Event type to category mapping
    EVENT_TYPE_MAPPING = {
        "user_creation": ("User Account", "Account Creation"),
        "password_reset": ("User Account", "Password Reset"),
        "work_order": ("Work Order", "General"),
        "access_request": ("Access", "Access Request"),
        "system_alert": ("System", "Alert"),
        "hardware_request": ("Hardware", "Hardware Request"),
        "software_request": ("Software", "Software Installation"),
        "network_issue": ("Network", "Connectivity"),
        "security_incident": ("Security", "Security Incident"),
    }

    # Try event type mapping first
    if event_type in EVENT_TYPE_MAPPING:
        mapped_cat, mapped_sub = EVENT_TYPE_MAPPING[event_type]
        if not category:
            category = mapped_cat
        if not subcategory:
            subcategory = mapped_sub

    # If still not categorized, use keyword analysis
    if not category or not subcategory:
        combined_text = f"{title} {description}"
        detected_cat, detected_sub = categorize_by_keywords(combined_text)

        if detected_cat and not category:
            category = detected_cat
        if detected_sub and not subcategory:
            subcategory = detected_sub

    # Fallback to General category
    return category or "General", subcategory or "Other"


def get_assignment_group_for_category(
    db: Session,
    category: str,
    subcategory: Optional[str] = None
) -> Optional[Tuple[int, str]]:
    """
    Get the assignment group for a category.

    Args:
        db: Database session
        category: Ticket category
        subcategory: Ticket subcategory

    Returns:
        Tuple of (group_id, group_name) or None
    """
    from models import CategoryAssignmentMapping, AssignmentGroup

    # Try to find exact match with subcategory
    if subcategory:
        mapping = db.query(CategoryAssignmentMapping).filter(
            CategoryAssignmentMapping.category == category,
            CategoryAssignmentMapping.subcategory == subcategory
        ).first()

        if mapping:
            group = db.query(AssignmentGroup).filter(
                AssignmentGroup.id == mapping.group_id
            ).first()
            if group:
                return group.id, group.name

    # Try category-only match
    mapping = db.query(CategoryAssignmentMapping).filter(
        CategoryAssignmentMapping.category == category,
        CategoryAssignmentMapping.subcategory.is_(None)
    ).first()

    if mapping:
        group = db.query(AssignmentGroup).filter(
            AssignmentGroup.id == mapping.group_id
        ).first()
        if group:
            return group.id, group.name

    # Fallback: find any group with matching name
    group = db.query(AssignmentGroup).filter(
        AssignmentGroup.name.ilike(f"%{category}%")
    ).first()

    if group:
        return group.id, group.name

    # Last resort: return IT Service Desk if it exists
    group = db.query(AssignmentGroup).filter(
        AssignmentGroup.name == "IT Service Desk"
    ).first()

    if group:
        return group.id, group.name

    return None


def extract_affected_entities(text: str) -> Dict[str, Optional[str]]:
    """
    Extract affected user and CI from text.

    Returns:
        Dict with 'user' and 'ci' keys
    """
    result = {"user": None, "ci": None}

    # Extract email addresses (potential affected user)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        result["user"] = emails[0]

    # Extract hostnames/server names (potential CI)
    hostname_pattern = r'\b(?:server|host|vm|ci)[:\s-]*([a-zA-Z0-9][-a-zA-Z0-9]*)\b'
    hostnames = re.findall(hostname_pattern, text, re.IGNORECASE)
    if hostnames:
        result["ci"] = hostnames[0]

    # Extract IP addresses (potential CI)
    if not result["ci"]:
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, text)
        if ips:
            result["ci"] = ips[0]

    return result
