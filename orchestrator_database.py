#!/usr/bin/env python3
"""
Database layer for Ticket Orchestrator
Provides persistent storage using SQLite
"""

from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import List, Optional, Dict
import json as json_lib
from contextlib import contextmanager

# Database setup
DATABASE_URL = "sqlite:///./ticket_orchestrator.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================================================
# DATABASE MODELS
# ============================================================================

class TicketDB(Base):
    """Database model for orchestration tickets"""
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, index=True)  # ServiceNow ticket number
    servicenow_id = Column(String, index=True)  # sys_id
    servicenow_number = Column(String, index=True)
    title = Column(String)
    description = Column(Text)
    priority = Column(String)  # P1, P2, P3, P4
    category = Column(String)  # password_reset, user_creation, etc.
    status = Column(String, index=True)  # received, classified, in_progress, etc.
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    assigned_agent = Column(String, nullable=True)
    resolution_log = Column(JSON, default=list)  # Stored as JSON
    ticket_metadata = Column(JSON, default=dict)  # Stored as JSON (renamed from metadata)

# Create tables
Base.metadata.create_all(bind=engine)

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

@contextmanager
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_ticket(ticket_data: Dict) -> TicketDB:
    """Create a new ticket in database"""
    with get_db() as db:
        # Convert lists/dicts to JSON strings for SQLite
        ticket_data_copy = ticket_data.copy()
        if 'resolution_log' in ticket_data_copy and isinstance(ticket_data_copy['resolution_log'], list):
            ticket_data_copy['resolution_log'] = ticket_data_copy['resolution_log']
        if 'metadata' in ticket_data_copy and isinstance(ticket_data_copy['metadata'], dict):
            ticket_data_copy['ticket_metadata'] = ticket_data_copy.pop('metadata')

        # Convert datetime objects to strings if needed
        if 'created_at' in ticket_data_copy and isinstance(ticket_data_copy['created_at'], datetime):
            ticket_data_copy['created_at'] = ticket_data_copy['created_at']
        if 'updated_at' in ticket_data_copy and isinstance(ticket_data_copy['updated_at'], datetime):
            ticket_data_copy['updated_at'] = ticket_data_copy['updated_at']

        db_ticket = TicketDB(**ticket_data_copy)
        db.add(db_ticket)
        db.commit()
        db.refresh(db_ticket)
        return db_ticket

def get_ticket(ticket_id: str) -> Optional[TicketDB]:
    """Get a ticket by ID"""
    with get_db() as db:
        return db.query(TicketDB).filter(TicketDB.id == ticket_id).first()

def update_ticket(ticket_id: str, updates: Dict) -> Optional[TicketDB]:
    """Update a ticket"""
    with get_db() as db:
        db_ticket = db.query(TicketDB).filter(TicketDB.id == ticket_id).first()
        if not db_ticket:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(db_ticket, key):
                setattr(db_ticket, key, value)

        db_ticket.updated_at = datetime.now()
        db.commit()
        db.refresh(db_ticket)
        return db_ticket

def list_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[TicketDB]:
    """List tickets with optional filters"""
    with get_db() as db:
        query = db.query(TicketDB)

        if status:
            query = query.filter(TicketDB.status == status)
        if category:
            query = query.filter(TicketDB.category == category)

        return query.offset(skip).limit(limit).all()

def get_ticket_stats() -> Dict:
    """Get statistics about tickets"""
    with get_db() as db:
        total = db.query(TicketDB).count()

        # Count by status
        by_status = {}
        for status in ["received", "classified", "assigned_to_agent", "in_progress", "resolved", "failed", "requires_human"]:
            count = db.query(TicketDB).filter(TicketDB.status == status).count()
            by_status[status] = count

        # Count by category
        by_category = {}
        for category in ["password_reset", "user_creation", "user_deactivation", "integration_error", "data_sync_issue", "system_error", "manual"]:
            count = db.query(TicketDB).filter(TicketDB.category == category).count()
            by_category[category] = count

        return {
            "total_tickets": total,
            "by_status": by_status,
            "by_category": by_category,
            "auto_resolved": db.query(TicketDB).filter(TicketDB.status == "resolved").count(),
            "requires_human": db.query(TicketDB).filter(TicketDB.status == "requires_human").count(),
            "in_progress": db.query(TicketDB).filter(TicketDB.status == "in_progress").count()
        }

def ticket_exists(ticket_id: str) -> bool:
    """Check if a ticket already exists"""
    with get_db() as db:
        return db.query(TicketDB).filter(TicketDB.id == ticket_id).first() is not None

def delete_ticket(ticket_id: str) -> bool:
    """Delete a ticket"""
    with get_db() as db:
        db_ticket = db.query(TicketDB).filter(TicketDB.id == ticket_id).first()
        if db_ticket:
            db.delete(db_ticket)
            db.commit()
            return True
        return False

def ticket_to_dict(db_ticket: TicketDB) -> Dict:
    """Convert database ticket to dictionary"""
    return {
        "id": db_ticket.id,
        "servicenow_id": db_ticket.servicenow_id,
        "servicenow_number": db_ticket.servicenow_number,
        "title": db_ticket.title,
        "description": db_ticket.description,
        "priority": db_ticket.priority,
        "category": db_ticket.category,
        "status": db_ticket.status,
        "created_at": db_ticket.created_at.isoformat() if db_ticket.created_at else None,
        "updated_at": db_ticket.updated_at.isoformat() if db_ticket.updated_at else None,
        "assigned_agent": db_ticket.assigned_agent,
        "resolution_log": db_ticket.resolution_log if db_ticket.resolution_log else [],
        "metadata": db_ticket.ticket_metadata if db_ticket.ticket_metadata else {}
    }
