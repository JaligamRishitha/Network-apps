"""
SAP Database Models
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Index
from datetime import datetime
from backend.db.database import Base


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # Hashed password
    roles = Column(JSON, nullable=False)  # List of role strings
    is_active = Column(Boolean, default=True)
    password_expired = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Indexes already created by index=True on columns above


class PasswordResetTicket(Base):
    __tablename__ = "password_reset_tickets"

    id = Column(Integer, primary_key=True, index=True)
    sap_ticket_id = Column(String(255), unique=True, index=True)
    servicenow_ticket_id = Column(String(255), index=True)
    username = Column(String(255), index=True)
    user_email = Column(String(255))
    requester_name = Column(String(255))
    requester_email = Column(String(255))
    reason = Column(Text)
    priority = Column(String(50))
    status = Column(String(50))  # Open, In_Progress, Completed, Failed
    assigned_to = Column(String(255))
    correlation_id = Column(String(255), index=True)
    callback_url = Column(String(500))
    temp_password = Column(String(255))
    comments = Column(JSON, default=list)  # List of comments
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
