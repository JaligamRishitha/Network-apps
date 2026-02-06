"""
Notification Service - SLA warnings, breach alerts, and MuleSoft webhook callbacks.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import httpx
import json
import os

from models import (
    Notification,
    NotificationType,
    NotificationStatus,
    Ticket,
    TicketSLA,
    User,
    AssignmentGroup,
    AssignmentGroupMember,
)


# MuleSoft URL for callbacks
MULESOFT_URL = os.getenv("MULESOFT_URL", "http://mulesoft-backend:4797")


def send_webhook_sync(
    url: str,
    payload: Dict[str, Any],
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Send a webhook POST request (sync version for Docker container compatibility).

    Args:
        url: Webhook URL
        payload: JSON payload to send
        max_retries: Maximum retry attempts

    Returns:
        Dict with success status and response details
    """
    result = {
        "success": False,
        "status_code": None,
        "response": None,
        "error": None
    }

    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=10) as client:  # Shorter timeout to avoid blocking
                response = client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                result["status_code"] = response.status_code
                result["response"] = response.text[:500]  # Truncate response

                if response.status_code in [200, 201, 202]:
                    result["success"] = True
                    return result

        except Exception as e:
            result["error"] = str(e)

    return result


async def send_webhook(
    url: str,
    payload: Dict[str, Any],
    max_retries: int = 3
) -> Dict[str, Any]:
    """Async wrapper for send_webhook_sync."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        send_webhook_sync,
        url,
        payload,
        max_retries
    )


def create_notification(
    db: Session,
    notification_type: NotificationType,
    subject: str,
    message: str,
    recipient_id: Optional[int] = None,
    recipient_email: Optional[str] = None,
    recipient_group_id: Optional[int] = None,
    ticket_id: Optional[int] = None,
    sla_id: Optional[int] = None,
    webhook_url: Optional[str] = None,
    webhook_payload: Optional[Dict[str, Any]] = None
) -> Notification:
    """
    Create a notification record.

    Args:
        db: Database session
        notification_type: Type of notification
        subject: Notification subject
        message: Notification message body
        recipient_id: User ID to notify
        recipient_email: Email address to notify
        recipient_group_id: Assignment group to notify
        ticket_id: Related ticket ID
        sla_id: Related SLA ID
        webhook_url: URL for webhook callback
        webhook_payload: Payload for webhook

    Returns:
        Created Notification object
    """
    notification = Notification(
        notification_type=notification_type,
        subject=subject,
        message=message,
        recipient_id=recipient_id,
        recipient_email=recipient_email,
        recipient_group_id=recipient_group_id,
        ticket_id=ticket_id,
        sla_id=sla_id,
        webhook_url=webhook_url,
        webhook_payload=json.dumps(webhook_payload) if webhook_payload else None,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


async def send_notification(
    db: Session,
    notification_id: int
) -> Dict[str, Any]:
    """
    Send a notification (email and/or webhook).

    Args:
        db: Database session
        notification_id: ID of notification to send

    Returns:
        Dict with send status
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()

    if not notification:
        return {"success": False, "error": "Notification not found"}

    result = {"success": True, "email_sent": False, "webhook_sent": False}

    # Send webhook if configured
    if notification.webhook_url:
        payload = json.loads(notification.webhook_payload) if notification.webhook_payload else {}
        webhook_result = await send_webhook(notification.webhook_url, payload)

        notification.webhook_response = json.dumps(webhook_result)

        if webhook_result["success"]:
            result["webhook_sent"] = True
        else:
            result["webhook_error"] = webhook_result.get("error")

    # Note: Email sending would be implemented here with an email service
    # For now, we just mark as sent for email recipients
    if notification.recipient_email or notification.recipient_id:
        result["email_sent"] = True  # Placeholder

    # Update notification status
    if result.get("webhook_sent") or result.get("email_sent"):
        notification.status = NotificationStatus.sent
        notification.sent_at = datetime.utcnow()
    else:
        notification.status = NotificationStatus.failed
        notification.error_message = result.get("webhook_error", "Failed to send")
        notification.retry_count += 1

    db.commit()
    return result


async def notify_sla_warning(
    db: Session,
    ticket_id: int,
    sla_type: str,
    percent_elapsed: float,
    minutes_remaining: int
) -> Optional[Notification]:
    """
    Send SLA warning notification.

    Args:
        db: Database session
        ticket_id: Ticket ID
        sla_type: 'response' or 'resolution'
        percent_elapsed: Percentage of SLA time elapsed
        minutes_remaining: Minutes until breach

    Returns:
        Created notification or None
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return None

    sla = db.query(TicketSLA).filter(
        TicketSLA.ticket_id == ticket_id
    ).first()

    subject = f"SLA Warning: {ticket.ticket_number} - {sla_type.title()} SLA at {percent_elapsed:.0f}%"
    message = f"""
SLA Warning for Ticket {ticket.ticket_number}

Title: {ticket.title}
Priority: {ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority}
Category: {ticket.category}

SLA Type: {sla_type.title()}
Time Elapsed: {percent_elapsed:.0f}%
Minutes Remaining: {minutes_remaining}

Please take action to prevent SLA breach.
"""

    # Determine recipient
    recipient_id = ticket.assigned_to_id

    # Prepare webhook payload for MuleSoft
    webhook_payload = {
        "event_type": "sla_warning",
        "ticket_number": ticket.ticket_number,
        "ticket_id": ticket_id,
        "sla_type": sla_type,
        "percent_elapsed": percent_elapsed,
        "minutes_remaining": minutes_remaining,
        "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority),
        "category": ticket.category,
        "assigned_to_id": ticket.assigned_to_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    notification = create_notification(
        db=db,
        notification_type=NotificationType.sla_warning,
        subject=subject,
        message=message,
        recipient_id=recipient_id,
        ticket_id=ticket_id,
        sla_id=sla.id if sla else None,
        webhook_url=f"{MULESOFT_URL}/api/webhooks/sla-notification",
        webhook_payload=webhook_payload
    )

    # Mark SLA warning as sent
    if sla:
        sla.warning_sent = "true"
        db.commit()

    # Send the notification
    await send_notification(db, notification.id)

    return notification


async def notify_sla_breach(
    db: Session,
    ticket_id: int,
    sla_type: str,
    minutes_overdue: int
) -> Optional[Notification]:
    """
    Send SLA breach notification.

    Args:
        db: Database session
        ticket_id: Ticket ID
        sla_type: 'response' or 'resolution'
        minutes_overdue: Minutes past SLA

    Returns:
        Created notification or None
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return None

    sla = db.query(TicketSLA).filter(
        TicketSLA.ticket_id == ticket_id
    ).first()

    subject = f"SLA BREACH: {ticket.ticket_number} - {sla_type.title()} SLA breached"
    message = f"""
*** SLA BREACH ALERT ***

Ticket {ticket.ticket_number} has breached its {sla_type} SLA.

Title: {ticket.title}
Priority: {ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority}
Category: {ticket.category}

SLA Type: {sla_type.title()}
Time Overdue: {minutes_overdue} minutes

Immediate action required!
"""

    # Notify assigned agent and manager
    recipient_id = ticket.assigned_to_id

    # Prepare webhook payload
    webhook_payload = {
        "event_type": "sla_breach",
        "ticket_number": ticket.ticket_number,
        "ticket_id": ticket_id,
        "sla_type": sla_type,
        "minutes_overdue": minutes_overdue,
        "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority),
        "category": ticket.category,
        "assigned_to_id": ticket.assigned_to_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    notification = create_notification(
        db=db,
        notification_type=NotificationType.sla_breach,
        subject=subject,
        message=message,
        recipient_id=recipient_id,
        ticket_id=ticket_id,
        sla_id=sla.id if sla else None,
        webhook_url=f"{MULESOFT_URL}/api/webhooks/sla-notification",
        webhook_payload=webhook_payload
    )

    # Mark breach as notified
    if sla:
        sla.breach_notified = "true"
        db.commit()

    # Send the notification
    await send_notification(db, notification.id)

    return notification


async def notify_ticket_assigned(
    db: Session,
    ticket_id: int,
    assigned_to_id: int,
    assignment_group: Optional[str] = None
) -> Optional[Notification]:
    """
    Send notification when ticket is assigned.

    Args:
        db: Database session
        ticket_id: Ticket ID
        assigned_to_id: User ID ticket is assigned to
        assignment_group: Name of assignment group

    Returns:
        Created notification or None
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return None

    user = db.query(User).filter(User.id == assigned_to_id).first()
    if not user:
        return None

    subject = f"Ticket Assigned: {ticket.ticket_number}"
    message = f"""
You have been assigned a new ticket.

Ticket Number: {ticket.ticket_number}
Title: {ticket.title}
Priority: {ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority}
Category: {ticket.category}

Description:
{ticket.description or 'No description provided.'}

Please review and begin working on this ticket.
"""

    webhook_payload = {
        "event_type": "ticket_assigned",
        "ticket_number": ticket.ticket_number,
        "ticket_id": ticket_id,
        "assigned_to_id": assigned_to_id,
        "assigned_to_name": user.full_name,
        "assignment_group": assignment_group,
        "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    notification = create_notification(
        db=db,
        notification_type=NotificationType.ticket_assigned,
        subject=subject,
        message=message,
        recipient_id=assigned_to_id,
        recipient_email=user.email,
        ticket_id=ticket_id,
        webhook_url=f"{MULESOFT_URL}/api/webhooks/ticket-notification",
        webhook_payload=webhook_payload
    )

    await send_notification(db, notification.id)
    return notification


async def notify_ticket_created(
    db: Session,
    ticket_id: int,
    event_id: Optional[str] = None,
    callback_url: Optional[str] = None
) -> Optional[Notification]:
    """
    Send notification when ticket is created (especially for auto-created tickets).

    Args:
        db: Database session
        ticket_id: Ticket ID
        event_id: Original event ID (if from auto-create)
        callback_url: URL to call back (if provided)

    Returns:
        Created notification or None
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return None

    sla = db.query(TicketSLA).filter(TicketSLA.ticket_id == ticket_id).first()

    subject = f"Ticket Created: {ticket.ticket_number}"
    message = f"Ticket {ticket.ticket_number} has been created successfully."

    webhook_payload = {
        "event_type": "ticket_created",
        "event_id": event_id,
        "ticket_number": ticket.ticket_number,
        "ticket_id": ticket_id,
        "title": ticket.title,
        "category": ticket.category,
        "subcategory": ticket.subcategory,
        "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority),
        "status": ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status),
        "assigned_to_id": ticket.assigned_to_id,
        "sla_response_due": sla.response_due_at.isoformat() if sla else None,
        "sla_resolution_due": sla.resolution_due_at.isoformat() if sla else None,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    # Use callback URL if provided, otherwise use default MuleSoft endpoint
    webhook_url = callback_url or f"{MULESOFT_URL}/api/webhooks/ticket-notification"

    notification = create_notification(
        db=db,
        notification_type=NotificationType.ticket_updated,
        subject=subject,
        message=message,
        ticket_id=ticket_id,
        webhook_url=webhook_url,
        webhook_payload=webhook_payload
    )

    await send_notification(db, notification.id)
    return notification


async def notify_ticket_resolved(
    db: Session,
    ticket_id: int
) -> Optional[Notification]:
    """
    Send notification when ticket is resolved.

    Args:
        db: Database session
        ticket_id: Ticket ID

    Returns:
        Created notification or None
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return None

    subject = f"Ticket Resolved: {ticket.ticket_number}"
    message = f"""
Your ticket has been resolved.

Ticket Number: {ticket.ticket_number}
Title: {ticket.title}

Resolution Notes:
{ticket.resolution_notes or 'No notes provided.'}

If you have any questions, please contact IT Support.
"""

    webhook_payload = {
        "event_type": "ticket_resolved",
        "ticket_number": ticket.ticket_number,
        "ticket_id": ticket_id,
        "resolution_notes": ticket.resolution_notes,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    notification = create_notification(
        db=db,
        notification_type=NotificationType.ticket_resolved,
        subject=subject,
        message=message,
        recipient_id=ticket.requester_id,
        ticket_id=ticket_id,
        webhook_url=f"{MULESOFT_URL}/api/webhooks/ticket-notification",
        webhook_payload=webhook_payload
    )

    await send_notification(db, notification.id)
    return notification


def get_pending_notifications(
    db: Session,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get pending notifications that need to be sent."""
    notifications = db.query(Notification).filter(
        Notification.status == NotificationStatus.pending
    ).order_by(Notification.created_at.asc()).limit(limit).all()

    return [
        {
            "id": n.id,
            "type": n.notification_type.value,
            "subject": n.subject,
            "recipient_email": n.recipient_email,
            "ticket_id": n.ticket_id,
            "webhook_url": n.webhook_url,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]


async def process_pending_notifications(db: Session, limit: int = 10) -> Dict[str, Any]:
    """
    Process and send pending notifications.

    Args:
        db: Database session
        limit: Maximum notifications to process

    Returns:
        Dict with processing results
    """
    pending = db.query(Notification).filter(
        Notification.status == NotificationStatus.pending
    ).order_by(Notification.created_at.asc()).limit(limit).all()

    results = {
        "processed": 0,
        "success": 0,
        "failed": 0,
        "errors": []
    }

    for notification in pending:
        result = await send_notification(db, notification.id)
        results["processed"] += 1

        if result.get("success") or result.get("webhook_sent") or result.get("email_sent"):
            results["success"] += 1
        else:
            results["failed"] += 1
            if result.get("error"):
                results["errors"].append({
                    "notification_id": notification.id,
                    "error": result.get("error")
                })

    return results
