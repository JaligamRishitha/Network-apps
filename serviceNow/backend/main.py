from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from pydantic import BaseModel
import os
import hashlib
import httpx

from database import SessionLocal, engine, Base
from models import User, Incident, ServiceCatalogItem, KnowledgeArticle, Ticket, Approval, IncidentStatus, IncidentPriority, TicketStatus, ApprovalStatus
from schemas import (
    UserCreate, UserResponse, IncidentCreate, IncidentResponse,
    ServiceCatalogItemResponse, KnowledgeArticleCreate, KnowledgeArticleResponse,
    TicketCreate, TicketUpdate, TicketResponse, ApprovalCreate, ApprovalUpdate, ApprovalResponse,
    Token
)
from servicenow_client import servicenow_client, ServiceNowClient

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ServiceNow Clone API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health check endpoint for container orchestration and MuleSoft"""
    return {"status": "healthy", "service": "servicenow-backend", "timestamp": datetime.utcnow().isoformat() + "Z"}


# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")[:72]  # Truncate to 72 bytes for bcrypt
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Use a simpler password context to avoid bcrypt version issues
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == username).first()
    if user is None:
        raise credentials_exception
    return user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/incidents/", response_model=list[IncidentResponse])
def read_incidents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    incidents = db.query(Incident).offset(skip).limit(limit).all()
    return incidents

@app.post("/incidents/", response_model=IncidentResponse)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_incident = Incident(**incident.dict(), reporter_id=current_user.id)
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

@app.get("/debug/users")
def debug_users(db: Session = Depends(get_db)):
    """Debug endpoint to check users in database"""
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "role": u.role} for u in users]

@app.get("/debug/tickets")
def debug_tickets(db: Session = Depends(get_db)):
    """Debug endpoint to check tickets in database"""
    tickets = db.query(Ticket).all()
    return [{"id": t.id, "ticket_number": t.ticket_number, "title": t.title, "status": t.status, "requester_id": t.requester_id} for t in tickets]

@app.get("/debug/approvals")
def debug_approvals(db: Session = Depends(get_db)):
    """Debug endpoint to check approvals in database"""
    approvals = db.query(Approval).all()
    return [{"id": a.id, "ticket_id": a.ticket_id, "approver_id": a.approver_id, "status": a.status} for a in approvals]

@app.get("/service-catalog/", response_model=list[ServiceCatalogItemResponse])
def read_service_catalog(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(ServiceCatalogItem).all()
    return items

# Knowledge Base endpoints
@app.get("/knowledge-base/", response_model=list[KnowledgeArticleResponse])
def read_knowledge_articles(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    """Get knowledge base articles with optional filtering"""
    query = db.query(KnowledgeArticle)

    if category:
        query = query.filter(KnowledgeArticle.category == category)

    if search:
        query = query.filter(
            KnowledgeArticle.title.contains(search) |
            KnowledgeArticle.content.contains(search) |
            KnowledgeArticle.tags.contains(search)
        )

    articles = query.offset(skip).limit(limit).all()
    return articles

@app.get("/knowledge-base/categories/")
def get_knowledge_categories(db: Session = Depends(get_db)):
    """Get all knowledge base categories"""
    categories = db.query(KnowledgeArticle.category).distinct().all()
    return [{"name": cat[0]} for cat in categories if cat[0]]

@app.get("/knowledge-base/{article_id}", response_model=KnowledgeArticleResponse)
def read_knowledge_article(article_id: int, db: Session = Depends(get_db)):
    """Get a specific knowledge article and increment view count"""
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Increment view count
    article.views += 1
    db.commit()
    db.refresh(article)

    return article

@app.post("/knowledge-base/{article_id}/helpful")
def mark_article_helpful(article_id: int, db: Session = Depends(get_db)):
    """Mark an article as helpful"""
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.helpful_votes += 1
    db.commit()

    return {"message": "Thank you for your feedback!"}

# Ticket Management endpoints
@app.post("/tickets/", response_model=TicketResponse)
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new ticket"""
    import random
    import string
    
    # Generate unique ticket number
    ticket_number = f"TKT{random.randint(100000, 999999)}"
    
    db_ticket = Ticket(
        ticket_number=ticket_number,
        title=ticket.title,
        description=ticket.description,
        ticket_type=ticket.ticket_type,
        priority=ticket.priority,
        category=ticket.category,
        subcategory=ticket.subcategory,
        contact_number=ticket.contact_number,
        preferred_contact=ticket.preferred_contact,
        urgency=ticket.urgency,
        business_justification=ticket.business_justification,
        estimated_cost=ticket.estimated_cost,
        requester_id=current_user.id,
        # Salesforce integration fields
        correlation_id=ticket.correlation_id,
        source_system=ticket.source_system,
        source_request_id=ticket.source_request_id,
        source_request_type=ticket.source_request_type
    )
    
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    
    # Create approval if needed (for service requests over certain cost)
    if ticket.ticket_type == "service_request" and ticket.estimated_cost:
        try:
            cost_value = float(ticket.estimated_cost.replace('$', '').replace(',', ''))
            if cost_value > 500:  # Require approval for requests over $500
                # Find an admin user to approve
                admin_user = db.query(User).filter(User.role == "admin").first()
                if admin_user:
                    approval = Approval(
                        ticket_id=db_ticket.id,
                        approver_id=admin_user.id
                    )
                    db.add(approval)
                    db_ticket.status = "pending_approval"
                    db.commit()
        except:
            pass  # If cost parsing fails, continue without approval
    
    return db_ticket

@app.get("/tickets/", response_model=list[TicketResponse])
def read_tickets(
    skip: int = 0, 
    limit: int = 100, 
    status: str = None,
    ticket_type: str = None,
    my_tickets: bool = False,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Get tickets with optional filtering"""
    query = db.query(Ticket)
    
    if my_tickets:
        query = query.filter(Ticket.requester_id == current_user.id)
    
    if status:
        query = query.filter(Ticket.status == status)
    
    if ticket_type:
        query = query.filter(Ticket.ticket_type == ticket_type)
    
    tickets = query.offset(skip).limit(limit).all()
    
    # Add requester and assigned user names
    for ticket in tickets:
        if ticket.requester:
            ticket.requester_name = ticket.requester.full_name
        if ticket.assigned_to:
            ticket.assigned_to_name = ticket.assigned_to.full_name
    
    return tickets

@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
def read_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a specific ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Check if user can access this ticket
    if current_user.role == "user" and ticket.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Add names
    if ticket.requester:
        ticket.requester_name = ticket.requester.full_name
    if ticket.assigned_to:
        ticket.assigned_to_name = ticket.assigned_to.full_name

    return ticket


@app.get("/tickets/by-number/{ticket_number}", response_model=TicketResponse)
def read_ticket_by_number(ticket_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a specific ticket by ticket number (for MuleSoft integration)"""
    ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Add names
    if ticket.requester:
        ticket.requester_name = ticket.requester.full_name
    if ticket.assigned_to:
        ticket.assigned_to_name = ticket.assigned_to.full_name

    return ticket


@app.get("/tickets/by-correlation/{correlation_id}", response_model=TicketResponse)
def read_ticket_by_correlation(correlation_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a specific ticket by correlation ID (for Salesforce tracking)"""
    ticket = db.query(Ticket).filter(Ticket.correlation_id == correlation_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket not found with correlation ID: {correlation_id}")

    # Check if user can access this ticket
    if current_user.role == "user" and ticket.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Add names
    if ticket.requester:
        ticket.requester_name = ticket.requester.full_name
    if ticket.assigned_to:
        ticket.assigned_to_name = ticket.assigned_to.full_name

    return ticket


@app.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a ticket"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Check permissions
    if current_user.role == "user" and ticket.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Store old status to check if it changed
    old_status = ticket.status
    ticket_number = ticket.ticket_number

    # Update fields
    for field, value in ticket_update.dict(exclude_unset=True).items():
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)

    # Notify MuleSoft if status changed to approved or rejected
    new_status = ticket.status
    if new_status != old_status and new_status in ["approved", "rejected"]:
        try:
            await notify_mulesoft_approval_status(
                ticket_number=ticket_number,
                status=new_status,
                approval_id=0,  # No approval record, using ticket directly
                comments=ticket_update.resolution_notes
            )
        except Exception as e:
            print(f"MuleSoft notification error (non-blocking): {e}")

    return ticket

# Approval endpoints
@app.get("/approvals/", response_model=list[ApprovalResponse])
def read_approvals(
    skip: int = 0, 
    limit: int = 100, 
    status: str = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Get approvals for current user"""
    query = db.query(Approval).filter(Approval.approver_id == current_user.id)
    
    if status:
        query = query.filter(Approval.status == status)
    
    approvals = query.offset(skip).limit(limit).all()
    
    # Add ticket and requester information
    for approval in approvals:
        if approval.ticket:
            approval.ticket_title = approval.ticket.title
            approval.ticket_number = approval.ticket.ticket_number
            if approval.ticket.requester:
                approval.requester_name = approval.ticket.requester.full_name
    
    return approvals

async def notify_mulesoft_approval_status(ticket_number: str, status: str, approval_id: int, comments: str = None):
    """Notify MuleSoft about approval status change"""
    # Use MuleSoft Platform Backend (port 4797), not MCP (port 8091)
    mulesoft_url = os.getenv("MULESOFT_PLATFORM_URL", "http://149.102.158.71:4797")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            payload = {
                "ticket_number": ticket_number,
                "status": status,
                "approval_id": approval_id,
                "comments": comments,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "servicenow"
            }
            # Send to the correct MuleSoft webhook endpoint
            response = await client.post(
                f"{mulesoft_url}/api/webhooks/servicenow/approval-update",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"✅ MuleSoft webhook sent: {response.status_code} - Status: {status} for ticket {ticket_number}")
            return response.status_code in [200, 201, 202]
    except Exception as e:
        print(f"❌ Failed to notify MuleSoft: {e}")
        return False


@app.put("/approvals/{approval_id}", response_model=ApprovalResponse)
async def update_approval(
    approval_id: int,
    approval_update: ApprovalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject an approval request"""
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    # Check if current user is the approver
    if approval.approver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update approval
    approval.status = approval_update.status
    approval.comments = approval_update.comments
    if approval_update.status in ["approved", "rejected"]:
        approval.approved_at = datetime.utcnow()

    # Update ticket status based on approval
    ticket_number = None
    if approval.ticket:
        ticket_number = approval.ticket.ticket_number
        if approval_update.status == "approved":
            approval.ticket.status = "approved"
        elif approval_update.status == "rejected":
            approval.ticket.status = "rejected"

    db.commit()
    db.refresh(approval)

    # Notify MuleSoft about the approval status change (async, non-blocking)
    if ticket_number and approval_update.status in ["approved", "rejected"]:
        try:
            await notify_mulesoft_approval_status(
                ticket_number=ticket_number,
                status=approval_update.status,
                approval_id=approval_id,
                comments=approval_update.comments
            )
        except Exception as e:
            print(f"MuleSoft notification error (non-blocking): {e}")

    return approval

@app.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get optimized dashboard statistics in a single call"""
    try:
        # Get counts efficiently using database queries
        total_incidents = db.query(Incident).count()
        new_incidents = db.query(Incident).filter(Incident.status == IncidentStatus.new).count()
        in_progress_incidents = db.query(Incident).filter(Incident.status == IncidentStatus.in_progress).count()
        resolved_incidents = db.query(Incident).filter(Incident.status == IncidentStatus.resolved).count()
        
        total_tickets = db.query(Ticket).filter(Ticket.requester_id == current_user.id).count()
        open_tickets = db.query(Ticket).filter(
            Ticket.requester_id == current_user.id,
            Ticket.status.in_([TicketStatus.submitted, TicketStatus.pending_approval, TicketStatus.approved, TicketStatus.in_progress])
        ).count()
        resolved_tickets = db.query(Ticket).filter(
            Ticket.requester_id == current_user.id,
            Ticket.status.in_([TicketStatus.resolved, TicketStatus.closed])
        ).count()
        pending_approvals = db.query(Approval).filter(Approval.approver_id == current_user.id, Approval.status == ApprovalStatus.pending).count()
        
        # Get ticket status distribution
        ticket_status_counts = db.query(Ticket.status, func.count(Ticket.id)).filter(
            Ticket.requester_id == current_user.id
        ).group_by(Ticket.status).all()
        
        # Get priority distribution for both tickets and incidents
        ticket_priority_counts = db.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
        incident_priority_counts = db.query(Incident.priority, func.count(Incident.id)).group_by(Incident.priority).all()
        
        # Combine priority counts
        priority_totals = {}
        for priority, count in ticket_priority_counts + incident_priority_counts:
            priority_totals[priority.value] = priority_totals.get(priority.value, 0) + count
        
        return {
            "stats": {
                "totalIncidents": total_incidents,
                "newIncidents": new_incidents,
                "inProgressIncidents": in_progress_incidents,
                "resolvedIncidents": resolved_incidents,
                "totalTickets": total_tickets,
                "openTickets": open_tickets,
                "pendingApprovals": pending_approvals,
                "resolvedTickets": resolved_tickets
            },
            "ticketTrends": [
                {"name": "New", "value": next((count for status, count in ticket_status_counts if status == TicketStatus.submitted), 0)},
                {"name": "Pending Approval", "value": next((count for status, count in ticket_status_counts if status == TicketStatus.pending_approval), 0)},
                {"name": "Approved", "value": next((count for status, count in ticket_status_counts if status == TicketStatus.approved), 0)},
                {"name": "In Progress", "value": next((count for status, count in ticket_status_counts if status == TicketStatus.in_progress), 0)},
                {"name": "Resolved", "value": next((count for status, count in ticket_status_counts if status == TicketStatus.resolved), 0)}
            ],
            "priorityDistribution": [
                {"name": "Critical", "value": priority_totals.get("critical", 0), "color": "#f44336"},
                {"name": "High", "value": priority_totals.get("high", 0), "color": "#ff9800"},
                {"name": "Medium", "value": priority_totals.get("medium", 0), "color": "#2196f3"},
                {"name": "Low", "value": priority_totals.get("low", 0), "color": "#4caf50"}
            ]
        }
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard statistics")

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        # Create default admin user if not exists
        admin_user = db.query(User).filter(User.email == "admin@company.com").first()
        if not admin_user:
            admin_password = "admin123"
            hashed_password = get_password_hash(admin_password)
            admin_user = User(
                email="admin@company.com",
                full_name="System Administrator",
                role="admin",
                hashed_password=hashed_password
            )
            db.add(admin_user)
            db.commit()
            print(f"Created admin user: admin@company.com")
        
        # Create sample service catalog items
        if not db.query(ServiceCatalogItem).first():
            sample_items = [
                ServiceCatalogItem(name="New Laptop Request", description="Request a new laptop for employee", category="Hardware"),
                ServiceCatalogItem(name="Software Installation", description="Install new software on workstation", category="Software"),
                ServiceCatalogItem(name="Access Request", description="Request access to systems or applications", category="Access"),
            ]
            for item in sample_items:
                db.add(item)
            db.commit()
            print("Created sample service catalog items")
        
        # Create sample knowledge base articles
        if not db.query(KnowledgeArticle).first():
            sample_articles = [
                KnowledgeArticle(
                    title="How to Reset Your Password",
                    summary="Step-by-step guide to reset your password when you're locked out of your account.",
                    content="""# How to Reset Your Password

## Overview
If you've forgotten your password or are locked out of your account, follow these steps to reset it.

## Steps to Reset Password

### Method 1: Self-Service Password Reset
1. Go to the login page
2. Click "Forgot Password?" link
3. Enter your email address
4. Check your email for reset instructions
5. Click the reset link in the email
6. Create a new strong password

### Method 2: Contact IT Support
If self-service doesn't work:
1. Call IT Support: 02036602010 - Option 1
2. Provide your employee ID and full name
3. Answer security questions for verification
4. IT will reset your password temporarily
5. You'll be required to change it on first login

## Password Requirements
- Minimum 8 characters
- Must include uppercase and lowercase letters
- Must include at least one number
- Must include at least one special character
- Cannot be the same as your last 5 passwords

## Tips for Strong Passwords
- Use a passphrase with numbers and symbols
- Don't use personal information
- Consider using a password manager
- Enable two-factor authentication when available

## Need Help?
If you continue to have issues, contact the IT Service Desk at 02036602010 or submit a ticket through the portal.""",
                    category="Account Management",
                    tags="password,reset,login,account,security",
                    author_id=admin_user.id
                ),
                KnowledgeArticle(
                    title="Troubleshooting Slow Computer Performance",
                    summary="Common solutions for when your computer is running slowly or freezing.",
                    content="""# Troubleshooting Slow Computer Performance

## Overview
Is your computer running slowly? Here are the most common causes and solutions.

## Quick Fixes (Try These First)

### 1. Restart Your Computer
- Close all applications
- Click Start > Power > Restart
- Wait for complete restart
- This clears memory and temporary files

### 2. Check Available Storage
- Open File Explorer
- Click "This PC"
- Check if C: drive is more than 85% full
- If full, delete unnecessary files or contact IT

### 3. Close Unnecessary Programs
- Press Ctrl + Shift + Esc to open Task Manager
- Click "More details" if needed
- Look for programs using high CPU or Memory
- Right-click and "End task" for unnecessary programs

## Advanced Solutions

### Check for Malware
1. Run Windows Defender full scan
2. Go to Settings > Update & Security > Windows Security
3. Click "Virus & threat protection"
4. Run "Quick scan" or "Scan options" > "Full scan"

### Update Windows
1. Go to Settings > Update & Security
2. Click "Check for updates"
3. Install any available updates
4. Restart when prompted

### Disable Startup Programs
1. Press Ctrl + Shift + Esc for Task Manager
2. Click "Startup" tab
3. Right-click programs you don't need at startup
4. Select "Disable"

## When to Contact IT
Contact IT Support if:
- Computer is still slow after trying above steps
- You get error messages
- Programs crash frequently
- Computer takes more than 5 minutes to start

## Prevention Tips
- Restart your computer at least once a week
- Keep desktop clean (fewer than 20 icons)
- Don't install unauthorized software
- Run Windows updates regularly
- Use cloud storage for large files

## Contact Information
- IT Service Desk: 02036602010
- Email: itsupport@company.com
- Submit ticket through ServiceNow portal""",
                    category="Hardware & Performance",
                    tags="slow,performance,computer,troubleshooting,speed,memory",
                    author_id=admin_user.id
                ),
                KnowledgeArticle(
                    title="Microsoft Outlook Email Issues",
                    summary="Solutions for common Outlook problems including connection issues, missing emails, and sync problems.",
                    content="""# Microsoft Outlook Email Issues

## Overview
Common Outlook problems and their solutions.

## Connection Issues

### Outlook Won't Connect to Server
1. Check internet connection
2. Restart Outlook completely
3. Check if other Office apps work
4. Try Outlook Web App (OWA) in browser
5. If OWA works but Outlook doesn't, contact IT

### "Cannot Connect to Server" Error
1. Go to File > Account Settings > Account Settings
2. Select your email account
3. Click "Test Account Settings"
4. If test fails, contact IT for server settings

## Missing Emails

### Emails Not Appearing in Inbox
1. Check Junk/Spam folder
2. Check other folders (Sent, Drafts, etc.)
3. Use Search function (Ctrl + E)
4. Check if rules are moving emails automatically
5. Go to File > Options > Mail > Rules to review

### Sent Emails Not in Sent Folder
1. Go to File > Options > Mail
2. Check "Save copies of messages in Sent Items folder"
3. Click OK and restart Outlook

## Sync Issues

### Calendar/Contacts Not Syncing
1. Go to Send/Receive tab
2. Click "Send/Receive All Folders"
3. Check File > Account Settings for sync settings
4. If using mobile, check mobile sync settings

### Outlook Freezing or Crashing
1. Start Outlook in Safe Mode:
   - Press Windows + R
   - Type: outlook /safe
   - Press Enter
2. If it works in Safe Mode, disable add-ins:
   - Go to File > Options > Add-ins
   - Disable all add-ins
   - Restart normally

## Large Mailbox Issues

### Mailbox Full Warning
1. Delete old emails (older than 1 year)
2. Empty Deleted Items folder
3. Archive important emails to PST file
4. Contact IT if you need more storage

### Slow Outlook Performance
1. Compact your mailbox
2. Reduce number of folders
3. Archive old emails
4. Disable unnecessary add-ins

## Mobile Device Setup

### Setting Up Email on Phone/Tablet
1. Use Outlook mobile app (recommended)
2. Or use built-in email app with these settings:
   - Server: outlook.office365.com
   - Port: 993 (IMAP) or 995 (POP)
   - Security: SSL/TLS
3. Contact IT if you need specific server settings

## When to Contact IT
- Cannot access email for more than 30 minutes
- Getting authentication errors
- Need to set up email on new device
- Mailbox corruption errors
- Need email forwarding or distribution lists

## Quick Reference
- **Restart Outlook**: Close completely, wait 30 seconds, reopen
- **Safe Mode**: Windows + R, type "outlook /safe"
- **Test Connection**: File > Account Settings > Test Account Settings
- **Search All Folders**: Ctrl + E
- **IT Support**: 02036602010""",
                    category="Email & Communication",
                    tags="outlook,email,connection,sync,missing,mobile,setup",
                    author_id=admin_user.id
                ),
                KnowledgeArticle(
                    title="VPN Connection Problems",
                    summary="How to troubleshoot and fix VPN connection issues for remote work.",
                    content="""# VPN Connection Problems

## Overview
Virtual Private Network (VPN) allows secure remote access to company resources. Here's how to fix common issues.

## Cannot Connect to VPN

### Check Internet Connection First
1. Ensure you have stable internet
2. Try browsing to any website
3. If no internet, fix that first before VPN

### VPN Client Won't Start
1. Right-click VPN client icon
2. Select "Run as Administrator"
3. If still fails, restart computer
4. Try connecting again

### Authentication Failures
1. Double-check username and password
2. Ensure Caps Lock is OFF
3. Try typing password in notepad first, then copy/paste
4. If using token/2FA, ensure code is current
5. Contact IT if credentials are correct but still failing

## Slow VPN Performance

### Speed Issues
1. Try different VPN server location (if available)
2. Close unnecessary applications
3. Pause cloud backups (OneDrive, Google Drive)
4. Use wired connection instead of WiFi if possible

### Frequent Disconnections
1. Check power settings - disable "USB selective suspend"
2. Update VPN client software
3. Try different network (mobile hotspot test)
4. Contact IT if problem persists

## Specific Error Messages

### "The remote connection was denied"
- Check if your account is enabled for VPN access
- Contact IT to verify VPN permissions

### "Error 800: Unable to establish connection"
- Firewall or router blocking VPN
- Try from different network location
- Contact IT for firewall configuration

### "Error 691: Access denied"
- Username/password incorrect
- Account may be locked or expired
- Contact IT for account status

## Mobile VPN Setup

### iPhone/iPad
1. Go to Settings > General > VPN
2. Add VPN Configuration
3. Enter server details provided by IT
4. Test connection

### Android
1. Go to Settings > Network & Internet > VPN
2. Add VPN profile
3. Enter server details provided by IT
4. Test connection

## Best Practices

### Security Tips
- Always disconnect VPN when not needed
- Don't share VPN credentials
- Use company-approved VPN client only
- Report suspicious activity immediately

### Performance Tips
- Connect to nearest server location
- Close streaming services while on VPN
- Use VPN only when accessing company resources
- Restart VPN connection if slow

## Troubleshooting Steps

### Basic Troubleshooting
1. Disconnect and reconnect VPN
2. Restart VPN client application
3. Restart computer
4. Try different network connection
5. Update VPN client software

### Advanced Troubleshooting
1. Flush DNS: Open Command Prompt as admin, type "ipconfig /flushdns"
2. Reset network settings
3. Temporarily disable antivirus/firewall
4. Check Windows updates

## When to Contact IT
- Cannot connect after trying basic steps
- Need VPN access for new employee
- Frequent disconnections affecting work
- Need VPN on new device
- Suspicious VPN activity

## Contact Information
- **IT Helpdesk**: 02036602010
- **Emergency After Hours**: 02036602010 - Option 1
- **Email**: itsupport@company.com

## Quick Commands
- **Windows**: Windows + R, type "ncpa.cpl" to see network connections
- **Check IP**: Open Command Prompt, type "ipconfig"
- **Test Connection**: ping google.com""",
                    category="Network & Connectivity",
                    tags="vpn,remote,connection,network,authentication,slow,disconnection",
                    author_id=admin_user.id
                ),
                KnowledgeArticle(
                    title="Printer Setup and Troubleshooting",
                    summary="How to set up printers and resolve common printing issues.",
                    content="""# Printer Setup and Troubleshooting

## Overview
Guide for setting up network printers and solving common printing problems.

## Setting Up Network Printers

### Windows 10/11 Setup
1. Go to Settings > Devices > Printers & scanners
2. Click "Add a printer or scanner"
3. Wait for Windows to find network printers
4. Select your printer from the list
5. Follow installation prompts
6. Print test page to verify

### Manual Network Printer Setup
If printer not found automatically:
1. Click "The printer that I want isn't listed"
2. Select "Add a printer using TCP/IP address"
3. Enter printer IP address (get from IT)
4. Follow driver installation prompts

## Common Printing Problems

### Printer Not Responding
1. Check if printer is powered on
2. Verify network cable connections
3. Try printing from another computer
4. Restart print spooler service:
   - Press Windows + R
   - Type "services.msc"
   - Find "Print Spooler"
   - Right-click > Restart

### Print Jobs Stuck in Queue
1. Open Settings > Devices > Printers & scanners
2. Click on your printer
3. Click "Open queue"
4. Select stuck jobs and delete them
5. Try printing again

### Poor Print Quality

#### Faded or Light Printing
- Check toner/ink levels
- Run printer cleaning cycle
- Replace toner cartridge if low
- Contact IT for maintenance

#### Streaks or Lines on Paper
- Clean printer heads (use printer utility)
- Check for damaged toner cartridge
- Clean paper path
- Contact IT if problem persists

#### Paper Jams
1. Turn off printer
2. Open all printer doors/trays
3. Gently remove jammed paper (don't tear)
4. Check for small paper pieces
5. Close all doors and turn on printer
6. Try printing again

## Mobile Printing

### Print from iPhone/iPad
1. Ensure device on same WiFi as printer
2. Open document/photo to print
3. Tap Share button
4. Select Print
5. Choose printer and settings
6. Tap Print

### Print from Android
1. Install printer manufacturer's app
2. Or use Google Cloud Print (if supported)
3. Open document to print
4. Tap menu > Print
5. Select printer and print

## Printer Driver Issues

### Driver Not Found
1. Go to printer manufacturer's website
2. Download latest driver for your model
3. Run installer as administrator
4. Restart computer after installation

### Driver Conflicts
1. Uninstall old printer drivers
2. Go to Device Manager
3. Find printer under "Printers"
4. Right-click > Uninstall device
5. Reinstall with latest driver

## Network Printer Locations

### Common Office Printers
- **Reception Area**: HP LaserJet Pro (IP: 192.168.1.101)
- **Marketing Floor**: Canon ImageRunner (IP: 192.168.1.102)
- **Finance Department**: Brother MFC (IP: 192.168.1.103)
- **IT Department**: Xerox WorkCentre (IP: 192.168.1.104)

*Note: Contact IT for current printer locations and IP addresses*

## Printing Policies

### Color Printing
- Color printing requires manager approval
- Use color only for client presentations
- Default to black and white for internal documents

### Large Print Jobs
- Jobs over 50 pages require IT approval
- Consider digital alternatives first
- Use duplex (double-sided) printing when possible

## Troubleshooting Checklist

### Before Calling IT
- [ ] Printer powered on and connected
- [ ] Computer connected to network
- [ ] Tried printing from another application
- [ ] Checked printer queue for stuck jobs
- [ ] Restarted computer
- [ ] Checked toner/ink levels

### Information to Provide IT
- Printer model and location
- Error messages (exact text)
- What you were trying to print
- When the problem started
- If others have same issue

## Maintenance Tips

### Regular Maintenance
- Keep printer area clean and dust-free
- Don't touch toner cartridges unnecessarily
- Use recommended paper types
- Report low toner levels promptly

### Paper Guidelines
- Use standard 20lb copy paper
- Don't overfill paper trays
- Store paper in dry location
- Remove paper clips and staples

## When to Contact IT
- Printer completely unresponsive
- Network connectivity issues
- Need new printer installation
- Toner replacement needed
- Hardware malfunctions
- Print quality issues persist

## Contact Information
- **IT Support**: 02036602010
- **Printer Supplies**: ext. 1234
- **Maintenance Requests**: Submit ServiceNow ticket""",
                    category="Hardware & Peripherals",
                    tags="printer,printing,setup,network,driver,paper,jam,quality,mobile",
                    author_id=admin_user.id
                ),
                KnowledgeArticle(
                    title="Microsoft Teams Meeting Issues",
                    summary="Troubleshooting guide for Microsoft Teams audio, video, and connection problems.",
                    content="""# Microsoft Teams Meeting Issues

## Overview
Solutions for common Microsoft Teams problems during meetings and calls.

## Audio Issues

### Can't Hear Others
1. Check computer volume (not muted)
2. In Teams, click device settings (gear icon)
3. Test speaker under "Audio devices"
4. Try different audio device if available
5. Leave and rejoin meeting

### Others Can't Hear You
1. Check if microphone is muted in Teams
2. Click microphone icon to unmute
3. Check Windows microphone permissions:
   - Settings > Privacy > Microphone
   - Allow Teams access
4. Test microphone in Teams settings
5. Try different microphone if available

### Echo or Feedback
1. Use headphones instead of speakers
2. Ask others to mute when not speaking
3. Move away from speakers
4. Check for multiple devices connected
5. Use "Reduce background noise" in Teams settings

## Video Issues

### Camera Not Working
1. Check if camera is enabled in Teams
2. Click camera icon to turn on video
3. Check Windows camera permissions:
   - Settings > Privacy > Camera
   - Allow Teams access
4. Close other apps using camera (Skype, Zoom)
5. Restart Teams application

### Poor Video Quality
1. Check internet connection speed
2. Close unnecessary applications
3. Move closer to WiFi router
4. Turn off video of other participants
5. Use "Optimize for video" in meeting options

### Camera Shows Wrong Image
1. Check camera settings in Teams
2. Go to Settings > Devices > Camera
3. Select correct camera device
4. Test camera preview
5. Restart Teams if needed

## Connection Issues

### Can't Join Meeting
1. Check internet connection
2. Try joining via web browser instead of app
3. Use phone dial-in option as backup
4. Clear Teams cache:
   - Close Teams completely
   - Press Windows + R
   - Type: %appdata%\\Microsoft\\Teams
   - Delete contents of folder
   - Restart Teams

### Meeting Keeps Disconnecting
1. Check WiFi signal strength
2. Close bandwidth-heavy applications
3. Use ethernet cable instead of WiFi
4. Restart router/modem
5. Contact IT if problem persists

### Screen Sharing Not Working
1. Update Teams to latest version
2. Try sharing specific application instead of desktop
3. Check if admin permissions required
4. Close unnecessary applications
5. Restart Teams

## Mobile Teams Issues

### Teams App Problems on Phone
1. Update Teams app from app store
2. Check mobile data/WiFi connection
3. Restart Teams app
4. Restart phone if needed
5. Reinstall Teams app if problems persist

### Can't Access Files on Mobile
1. Ensure signed in with company account
2. Check internet connection
3. Try accessing via web browser
4. Sync files in desktop app first
5. Contact IT for file permissions

## Meeting Best Practices

### Before the Meeting
- Test audio/video 5 minutes early
- Join from quiet location
- Have phone backup ready
- Close unnecessary applications
- Charge device or plug in power

### During the Meeting
- Mute when not speaking
- Use "Raise hand" feature for questions
- Share specific applications, not entire screen
- Use chat for questions if audio issues
- Take notes in Teams or OneNote

## Performance Optimization

### Improve Teams Performance
1. Close other video applications
2. Update Teams regularly
3. Restart Teams daily
4. Clear Teams cache weekly
5. Use desktop app instead of web browser

### Bandwidth Management
- Turn off video when not needed
- Limit other internet usage during calls
- Use phone audio for large meetings
- Close cloud sync applications
- Ask others to mute video if connection poor

## Troubleshooting Steps

### Quick Fixes
1. Mute/unmute microphone
2. Turn video off and on
3. Leave and rejoin meeting
4. Restart Teams application
5. Check device settings

### Advanced Troubleshooting
1. Update Teams application
2. Clear Teams cache
3. Reset network settings
4. Update audio/video drivers
5. Contact IT support

## Common Error Messages

### "We're sorry - we've run into an issue"
- Clear Teams cache
- Restart application
- Try web version
- Contact IT if persists

### "Couldn't connect to media"
- Check firewall settings
- Try different network
- Use phone dial-in
- Contact IT for network configuration

## When to Contact IT
- Persistent audio/video issues
- Cannot join any meetings
- Teams won't start or crashes
- Need Teams installation on new device
- Network connectivity problems
- Account access issues

## Alternative Solutions
- Use phone dial-in for audio
- Join via web browser
- Use mobile Teams app as backup
- Switch to different meeting platform if approved
- Record meeting for those who can't join

## Contact Information
- **IT Helpdesk**: 02036602010
- **Teams Support**: Submit ServiceNow ticket
- **Emergency Meeting Support**: Call IT during business hours

## Quick Reference
- **Mute/Unmute**: Ctrl + Shift + M
- **Video On/Off**: Ctrl + Shift + O
- **Share Screen**: Ctrl + Shift + E
- **Raise Hand**: Ctrl + Shift + K
- **Leave Meeting**: Ctrl + Shift + H""",
                    category="Software & Applications",
                    tags="teams,meeting,audio,video,microphone,camera,connection,screen sharing",
                    author_id=admin_user.id
                )
            ]
            
            for article in sample_articles:
                db.add(article)
            db.commit()
            print("Created sample knowledge base articles")

        # No sample tickets or approvals - users will create their own
    except Exception as e:
        print(f"Startup error: {e}")
    finally:
        db.close()

# ============================================================================
# MULESOFT INTEGRATION
# ============================================================================

MULESOFT_URL = os.getenv("MULESOFT_BASE_URL", "http://149.102.158.71:8091")


@app.get("/api/mulesoft/health")
async def mulesoft_health_check():
    """Check MuleSoft connectivity"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{MULESOFT_URL}/api/health")
            if response.status_code == 200:
                return {"status": "healthy", "message": "Connected to MuleSoft", "url": MULESOFT_URL, "data": response.json()}
            return {"status": "unhealthy", "message": f"MuleSoft returned {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e), "url": MULESOFT_URL}


@app.get("/api/mulesoft/tickets")
async def get_mulesoft_tickets(current_user: User = Depends(get_current_user)):
    """Fetch cases/tickets from MuleSoft (via Salesforce connector)"""
    all_tickets = []

    try:
        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            # First, authenticate with MuleSoft
            auth_response = await client.post(
                f"{MULESOFT_URL}/api/auth/login",
                json={"email": "admin@example.com", "password": "admin123"}
            )
            if auth_response.status_code != 200:
                return {"error": "MuleSoft authentication failed", "tickets": []}

            token = auth_response.json().get("access_token", "")
            headers = {"Authorization": f"Bearer {token}"}

            # Get list of connectors
            connectors_response = await client.get(f"{MULESOFT_URL}/api/connectors", headers=headers)
            if connectors_response.status_code == 200:
                connectors = connectors_response.json()

                # For each Salesforce connector, fetch cases
                for connector in connectors:
                    if connector.get("connector_type") == "salesforce":
                        connector_id = connector.get("id")
                        cases_response = await client.get(
                            f"{MULESOFT_URL}/api/cases/external/cases",
                            params={"connector_id": connector_id},
                            headers=headers
                        )
                        if cases_response.status_code == 200:
                            data = cases_response.json()
                            # Handle both list and dict responses
                            if isinstance(data, list):
                                cases = data
                            else:
                                cases = data.get("cases", [])
                            for case in cases:
                                if not isinstance(case, dict):
                                    continue
                                all_tickets.append({
                                    "source": "mulesoft_salesforce",
                                    "connector_id": connector_id,
                                    "id": case.get("id") or case.get("caseId"),
                                    "ticket_number": case.get("caseNumber") or case.get("number"),
                                    "title": case.get("subject") or case.get("title"),
                                    "description": case.get("description"),
                                    "status": case.get("status"),
                                    "priority": case.get("priority"),
                                })

            return {"tickets": all_tickets, "count": len(all_tickets)}
    except Exception as e:
        return {"error": str(e), "tickets": []}


@app.get("/api/mulesoft/tickets/{ticket_number}")
async def get_mulesoft_ticket(ticket_number: str, current_user: User = Depends(get_current_user)):
    """Fetch a specific ticket status from MuleSoft/ServiceNow"""
    try:
        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            # Authenticate with MuleSoft
            auth_response = await client.post(
                f"{MULESOFT_URL}/api/auth/login",
                json={"email": "admin@example.com", "password": "admin123"}
            )
            if auth_response.status_code != 200:
                return {"error": "MuleSoft authentication failed"}

            token = auth_response.json().get("access_token", "")
            headers = {"Authorization": f"Bearer {token}"}

            # Get ticket status via MuleSoft
            response = await client.get(
                f"{MULESOFT_URL}/api/servicenow/ticket-status/{ticket_number}",
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Ticket not found or MuleSoft returned {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/mulesoft/connectors")
async def get_mulesoft_connectors(current_user: User = Depends(get_current_user)):
    """Get list of MuleSoft connectors"""
    try:
        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            # Authenticate with MuleSoft
            auth_response = await client.post(
                f"{MULESOFT_URL}/api/auth/login",
                json={"email": "admin@example.com", "password": "admin123"}
            )
            if auth_response.status_code != 200:
                return {"error": "MuleSoft authentication failed", "connectors": []}

            token = auth_response.json().get("access_token", "")
            headers = {"Authorization": f"Bearer {token}"}

            response = await client.get(f"{MULESOFT_URL}/api/connectors", headers=headers)
            if response.status_code == 200:
                return {"connectors": response.json()}
            return {"error": f"Failed to get connectors: {response.status_code}", "connectors": []}
    except Exception as e:
        return {"error": str(e), "connectors": []}


@app.post("/api/mulesoft/send-to-servicenow")
async def send_ticket_via_mulesoft(
    ticket_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Send a ticket to ServiceNow via MuleSoft"""
    try:
        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            # Authenticate with MuleSoft
            auth_response = await client.post(
                f"{MULESOFT_URL}/api/auth/login",
                json={"email": "admin@example.com", "password": "admin123"}
            )
            if auth_response.status_code != 200:
                return {"error": "MuleSoft authentication failed"}

            token = auth_response.json().get("access_token", "")
            headers = {"Authorization": f"Bearer {token}"}

            # Send ticket via MuleSoft to ServiceNow
            response = await client.post(
                f"{MULESOFT_URL}/api/servicenow/send-ticket-and-approval",
                headers=headers,
                json=ticket_data,
                params={"ticket_type": "incident", "approval_type": "service_request"}
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"MuleSoft returned {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/mulesoft/sync")
async def sync_from_mulesoft(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync tickets from MuleSoft to local database"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{MULESOFT_URL}/api/tickets")
            if response.status_code != 200:
                return {"error": f"Failed to fetch from MuleSoft: {response.status_code}", "synced": 0}

            mulesoft_tickets = response.json()
            if isinstance(mulesoft_tickets, dict):
                mulesoft_tickets = mulesoft_tickets.get("tickets", [])

            synced_count = 0
            for ms_ticket in mulesoft_tickets:
                ticket_number = ms_ticket.get("ticket_number") or ms_ticket.get("number")
                if not ticket_number:
                    continue

                # Check if ticket already exists
                existing = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()
                if existing:
                    # Update existing ticket
                    if ms_ticket.get("status"):
                        existing.status = ms_ticket["status"]
                    if ms_ticket.get("title"):
                        existing.title = ms_ticket["title"]
                    synced_count += 1
                else:
                    # Create new ticket from MuleSoft
                    new_ticket = Ticket(
                        ticket_number=ticket_number,
                        title=ms_ticket.get("title", "MuleSoft Ticket"),
                        description=ms_ticket.get("description", ""),
                        ticket_type=ms_ticket.get("ticket_type", "service_request"),
                        status=ms_ticket.get("status", "submitted"),
                        priority=ms_ticket.get("priority", "medium"),
                        category=ms_ticket.get("category"),
                        requester_id=current_user.id,
                        servicenow_number=ms_ticket.get("servicenow_number"),
                        servicenow_sys_id=ms_ticket.get("servicenow_sys_id")
                    )
                    db.add(new_ticket)
                    synced_count += 1

            db.commit()
            return {"message": "Sync completed", "synced": synced_count}
    except Exception as e:
        return {"error": str(e), "synced": 0}


# API endpoint for MuleSoft to create approvals
@app.post("/api/approvals")
async def create_approval_from_mulesoft(
    approval_data: dict,
    db: Session = Depends(get_db)
):
    """Create approval from MuleSoft integration"""
    try:
        import random

        # Find admin user for approval
        admin_user = db.query(User).filter(User.role == "admin").first()
        if not admin_user:
            admin_user = db.query(User).first()
        if not admin_user:
            raise HTTPException(status_code=500, detail="No users in system")

        approval_id = f"APR-{random.randint(100000, 999999)}"

        return {
            "approval_id": approval_id,
            "status": "pending",
            "message": "Approval request created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API endpoint for MuleSoft to get tickets (matches MuleSoft's expected endpoint)
@app.get("/api/tickets")
async def get_tickets_for_mulesoft(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    db: Session = Depends(get_db)
):
    """Get tickets for MuleSoft integration - no auth required for integration"""
    query = db.query(Ticket)
    
    if category:
        query = query.filter(Ticket.category == category)
    
    tickets = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "title": ticket.title,
            "description": ticket.description,
            "category": ticket.category,
            "subcategory": ticket.subcategory,
            "status": ticket.status,
            "priority": ticket.priority,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None
        }
        for ticket in tickets
    ]

# API endpoint for MuleSoft to create tickets (matches MuleSoft's expected endpoint)
@app.post("/api/tickets")
async def create_ticket_from_mulesoft(
    ticket_data: dict,
    db: Session = Depends(get_db)
):
    """Create ticket from MuleSoft integration"""
    try:
        import random

        # Find default user
        default_user = db.query(User).first()
        if not default_user:
            raise HTTPException(status_code=500, detail="No users in system")

        # Generate ticket number
        ticket_number = f"TKT{random.randint(100000, 999999)}"

        # Map priority from MuleSoft format (1-5) to our format
        raw_priority = ticket_data.get("priority", "3")
        priority_map = {"1": "critical", "2": "high", "3": "medium", "4": "low", "5": "low",
                        "Critical": "critical", "High": "high", "Medium": "medium", "Low": "low"}
        priority = priority_map.get(str(raw_priority), "medium")

        # Map MuleSoft fields to our schema
        # Set status to pending_approval so tickets require manual approval
        new_ticket = Ticket(
            ticket_number=ticket_number,
            title=ticket_data.get("short_description") or ticket_data.get("subject", "MuleSoft Ticket"),
            description=ticket_data.get("description", ""),
            ticket_type=ticket_data.get("ticket_type", "incident"),
            status="pending_approval",  # Requires manual approval
            priority=priority,
            category=ticket_data.get("category"),
            requester_id=default_user.id,
        )
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)

        return {
            "id": new_ticket.id,
            "ticket_number": new_ticket.ticket_number,
            "title": new_ticket.title,
            "status": new_ticket.status.value if hasattr(new_ticket.status, 'value') else new_ticket.status,
            "message": "Ticket created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Webhook endpoint for MuleSoft to push tickets
@app.post("/api/webhooks/mulesoft/ticket")
async def mulesoft_ticket_webhook(
    ticket_data: dict,
    db: Session = Depends(get_db)
):
    """Receive ticket updates from MuleSoft"""
    try:
        ticket_number = ticket_data.get("ticket_number") or ticket_data.get("number")
        if not ticket_number:
            raise HTTPException(status_code=400, detail="ticket_number is required")

        # Find or create ticket
        existing = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()

        if existing:
            # Update existing ticket
            if ticket_data.get("status"):
                existing.status = ticket_data["status"]
            if ticket_data.get("title"):
                existing.title = ticket_data["title"]
            if ticket_data.get("description"):
                existing.description = ticket_data["description"]
            if ticket_data.get("priority"):
                existing.priority = ticket_data["priority"]
            db.commit()
            return {"message": "Ticket updated", "ticket_number": ticket_number}
        else:
            # Find a default user for the ticket
            default_user = db.query(User).first()
            if not default_user:
                raise HTTPException(status_code=500, detail="No users in system")

            # Create new ticket
            import random
            new_ticket = Ticket(
                ticket_number=ticket_number,
                title=ticket_data.get("title", "MuleSoft Ticket"),
                description=ticket_data.get("description", ""),
                ticket_type=ticket_data.get("ticket_type", "service_request"),
                status=ticket_data.get("status", "submitted"),
                priority=ticket_data.get("priority", "medium"),
                category=ticket_data.get("category"),
                requester_id=default_user.id,
                servicenow_number=ticket_data.get("servicenow_number"),
                servicenow_sys_id=ticket_data.get("servicenow_sys_id")
            )
            db.add(new_ticket)
            db.commit()
            return {"message": "Ticket created", "ticket_number": ticket_number}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SERVICENOW MCP INTEGRATION ENDPOINTS
# ============================================================================

@app.get("/api/servicenow/health")
async def servicenow_health_check():
    """Check ServiceNow connectivity status"""
    return await servicenow_client.health_check()


@app.get("/api/all-tickets")
async def get_all_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tickets from all sources: Local DB, MuleSoft, and ServiceNow MCP"""
    all_tickets = []

    # 1. Get local database tickets
    local_tickets = db.query(Ticket).all()
    for ticket in local_tickets:
        all_tickets.append({
            "source": "local",
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status.value if hasattr(ticket.status, 'value') else ticket.status,
            "priority": ticket.priority.value if hasattr(ticket.priority, 'value') else ticket.priority,
            "ticket_type": ticket.ticket_type.value if hasattr(ticket.ticket_type, 'value') else ticket.ticket_type,
            "category": ticket.category,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "servicenow_number": ticket.servicenow_number,
            "servicenow_sys_id": ticket.servicenow_sys_id,
        })

    # 2. Get ServiceNow MCP incidents (mock data)
    snow_incidents = await servicenow_client.list_incidents()
    if "result" in snow_incidents:
        for inc in snow_incidents["result"]:
            # Check if not already in local tickets by servicenow_number
            if not any(t.get("servicenow_number") == inc.get("number") for t in all_tickets):
                all_tickets.append({
                    "source": "servicenow",
                    "id": inc.get("sys_id"),
                    "ticket_number": inc.get("number"),
                    "title": inc.get("short_description"),
                    "description": inc.get("description"),
                    "status": _map_snow_state(inc.get("state")),
                    "priority": _map_snow_priority(inc.get("priority")),
                    "ticket_type": "incident",
                    "category": inc.get("category"),
                    "created_at": inc.get("sys_created_on"),
                    "servicenow_number": inc.get("number"),
                    "servicenow_sys_id": inc.get("sys_id"),
                })

    # 3. Try to get MuleSoft tickets
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{MULESOFT_URL}/api/tickets")
            if response.status_code == 200:
                ms_data = response.json()
                ms_tickets = ms_data if isinstance(ms_data, list) else ms_data.get("tickets", [])
                for ms_ticket in ms_tickets:
                    ticket_num = ms_ticket.get("ticket_number") or ms_ticket.get("number")
                    # Check if not already in all_tickets
                    if ticket_num and not any(t.get("ticket_number") == ticket_num for t in all_tickets):
                        all_tickets.append({
                            "source": "mulesoft",
                            "id": ms_ticket.get("id"),
                            "ticket_number": ticket_num,
                            "title": ms_ticket.get("title") or ms_ticket.get("short_description"),
                            "description": ms_ticket.get("description"),
                            "status": ms_ticket.get("status", "submitted"),
                            "priority": ms_ticket.get("priority", "medium"),
                            "ticket_type": ms_ticket.get("ticket_type", "service_request"),
                            "category": ms_ticket.get("category"),
                            "created_at": ms_ticket.get("created_at"),
                            "servicenow_number": ms_ticket.get("servicenow_number"),
                            "servicenow_sys_id": ms_ticket.get("servicenow_sys_id"),
                        })
    except Exception as e:
        # MuleSoft not available, continue without it
        pass

    return {
        "tickets": all_tickets,
        "sources": {
            "local": len([t for t in all_tickets if t["source"] == "local"]),
            "servicenow": len([t for t in all_tickets if t["source"] == "servicenow"]),
            "mulesoft": len([t for t in all_tickets if t["source"] == "mulesoft"]),
        }
    }


def _map_snow_state(state: str) -> str:
    """Map ServiceNow state to local status"""
    state_map = {
        "1": "submitted",      # New
        "2": "in_progress",    # In Progress
        "3": "in_progress",    # On Hold
        "4": "pending_approval",
        "5": "pending_approval",
        "6": "resolved",       # Resolved
        "7": "closed",         # Closed
        "8": "cancelled",      # Cancelled
    }
    return state_map.get(str(state), "submitted")


def _map_snow_priority(priority: str) -> str:
    """Map ServiceNow priority to local priority"""
    priority_map = {
        "1": "critical",
        "2": "high",
        "3": "medium",
        "4": "low",
        "5": "low",
    }
    return priority_map.get(str(priority), "medium")


# ServiceNow Incident endpoints
@app.get("/api/servicenow/incidents")
async def list_servicenow_incidents(
    skip: int = 0,
    limit: int = 50,
    query: str = "",
    current_user: User = Depends(get_current_user)
):
    """List incidents from ServiceNow"""
    result = await servicenow_client.list_incidents(skip=skip, limit=limit, query=query)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/api/servicenow/incidents/{incident_id}")
async def get_servicenow_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific incident from ServiceNow"""
    result = await servicenow_client.get_incident(incident_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.post("/api/servicenow/incidents")
async def create_servicenow_incident(
    short_description: str,
    description: str = "",
    priority: str = "3",
    urgency: str = "3",
    impact: str = "3",
    category: str = "",
    assignment_group: str = "",
    current_user: User = Depends(get_current_user)
):
    """Create a new incident in ServiceNow"""
    result = await servicenow_client.create_incident(
        short_description=short_description,
        description=description,
        priority=priority,
        urgency=urgency,
        impact=impact,
        category=category,
        assignment_group=assignment_group
    )
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.put("/api/servicenow/incidents/{incident_id}")
async def update_servicenow_incident(
    incident_id: str,
    updates: dict,
    current_user: User = Depends(get_current_user)
):
    """Update an incident in ServiceNow"""
    result = await servicenow_client.update_incident(incident_id, updates)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.post("/api/servicenow/incidents/{incident_id}/close")
async def close_servicenow_incident(
    incident_id: str,
    close_notes: str = "",
    current_user: User = Depends(get_current_user)
):
    """Close an incident in ServiceNow"""
    result = await servicenow_client.close_incident(incident_id, close_notes=close_notes)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


# ServiceNow Change Request endpoints
@app.get("/api/servicenow/changes")
async def list_servicenow_changes(
    skip: int = 0,
    limit: int = 50,
    query: str = "",
    current_user: User = Depends(get_current_user)
):
    """List change requests from ServiceNow"""
    result = await servicenow_client.list_change_requests(skip=skip, limit=limit, query=query)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/api/servicenow/changes/{change_id}")
async def get_servicenow_change(
    change_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific change request from ServiceNow"""
    result = await servicenow_client.get_change_request(change_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.post("/api/servicenow/changes")
async def create_servicenow_change(
    short_description: str,
    description: str = "",
    change_type: str = "normal",
    priority: str = "3",
    current_user: User = Depends(get_current_user)
):
    """Create a new change request in ServiceNow"""
    result = await servicenow_client.create_change_request(
        short_description=short_description,
        description=description,
        change_type=change_type,
        priority=priority
    )
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


# ServiceNow Problem endpoints
@app.get("/api/servicenow/problems")
async def list_servicenow_problems(
    skip: int = 0,
    limit: int = 50,
    query: str = "",
    current_user: User = Depends(get_current_user)
):
    """List problems from ServiceNow"""
    result = await servicenow_client.list_problems(skip=skip, limit=limit, query=query)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/api/servicenow/problems/{problem_id}")
async def get_servicenow_problem(
    problem_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific problem from ServiceNow"""
    result = await servicenow_client.get_problem(problem_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.post("/api/servicenow/problems")
async def create_servicenow_problem(
    short_description: str,
    description: str = "",
    priority: str = "3",
    current_user: User = Depends(get_current_user)
):
    """Create a new problem in ServiceNow"""
    result = await servicenow_client.create_problem(
        short_description=short_description,
        description=description,
        priority=priority
    )
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


# ServiceNow Service Request endpoints
@app.get("/api/servicenow/requests")
async def list_servicenow_requests(
    skip: int = 0,
    limit: int = 50,
    query: str = "",
    current_user: User = Depends(get_current_user)
):
    """List service requests from ServiceNow"""
    result = await servicenow_client.list_service_requests(skip=skip, limit=limit, query=query)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/api/servicenow/requests/{request_id}")
async def get_servicenow_request(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific service request from ServiceNow"""
    result = await servicenow_client.get_service_request(request_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


# ServiceNow Config Items (CMDB) endpoints
@app.get("/api/servicenow/cmdb")
async def list_servicenow_config_items(
    skip: int = 0,
    limit: int = 50,
    query: str = "",
    ci_class: str = "cmdb_ci",
    current_user: User = Depends(get_current_user)
):
    """List configuration items from ServiceNow CMDB"""
    result = await servicenow_client.list_config_items(
        skip=skip, limit=limit, query=query, ci_class=ci_class
    )
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/api/servicenow/cmdb/{ci_id}")
async def get_servicenow_config_item(
    ci_id: str,
    ci_class: str = "cmdb_ci",
    current_user: User = Depends(get_current_user)
):
    """Get a specific configuration item from ServiceNow CMDB"""
    result = await servicenow_client.get_config_item(ci_id, ci_class=ci_class)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


# ServiceNow User endpoints
@app.get("/api/servicenow/users")
async def list_servicenow_users(
    skip: int = 0,
    limit: int = 50,
    query: str = "",
    current_user: User = Depends(get_current_user)
):
    """List users from ServiceNow"""
    result = await servicenow_client.list_users(skip=skip, limit=limit, query=query)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/api/servicenow/users/{user_id}")
async def get_servicenow_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific user from ServiceNow"""
    result = await servicenow_client.get_user(user_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


# ServiceNow Knowledge Base endpoints
@app.get("/api/servicenow/knowledge")
async def search_servicenow_knowledge(
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Search ServiceNow knowledge base"""
    result = await servicenow_client.search_knowledge_base(query=query, limit=limit)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/api/servicenow/knowledge/{article_id}")
async def get_servicenow_knowledge_article(
    article_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific knowledge article from ServiceNow"""
    result = await servicenow_client.get_knowledge_article(article_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


# ServiceNow Catalog endpoints
@app.get("/api/servicenow/catalog")
async def list_servicenow_catalog(
    skip: int = 0,
    limit: int = 50,
    category: str = "",
    current_user: User = Depends(get_current_user)
):
    """List service catalog items from ServiceNow"""
    result = await servicenow_client.list_catalog_items(
        skip=skip, limit=limit, category=category
    )
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/api/servicenow/catalog/{item_id}")
async def get_servicenow_catalog_item(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific catalog item from ServiceNow"""
    result = await servicenow_client.get_catalog_item(item_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


# ServiceNow Approval endpoints
@app.get("/api/servicenow/approvals")
async def list_servicenow_approvals(
    skip: int = 0,
    limit: int = 50,
    state: str = "",
    current_user: User = Depends(get_current_user)
):
    """List approvals from ServiceNow"""
    result = await servicenow_client.list_approvals(skip=skip, limit=limit, state=state)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.post("/api/servicenow/approvals/{approval_id}/approve")
async def approve_servicenow_request(
    approval_id: str,
    comments: str = "",
    current_user: User = Depends(get_current_user)
):
    """Approve a request in ServiceNow"""
    result = await servicenow_client.approve_request(approval_id, comments=comments)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


@app.post("/api/servicenow/approvals/{approval_id}/reject")
async def reject_servicenow_request(
    approval_id: str,
    comments: str = "",
    current_user: User = Depends(get_current_user)
):
    """Reject a request in ServiceNow"""
    result = await servicenow_client.reject_request(approval_id, comments=comments)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result)
    return result


# Sync endpoint to create ticket in both local DB and ServiceNow
@app.post("/api/tickets/sync-to-servicenow/{ticket_id}")
async def sync_ticket_to_servicenow(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync a local ticket to ServiceNow as an incident or service request"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Check if user can sync this ticket
    if current_user.role == "user" and ticket.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Map ticket type to ServiceNow record type
    if ticket.ticket_type == "incident":
        result = await servicenow_client.create_incident(
            short_description=ticket.title,
            description=ticket.description or "",
            priority=_map_priority(ticket.priority),
            category=ticket.category or "",
        )
    else:
        result = await servicenow_client.create_service_request(
            short_description=ticket.title,
            description=ticket.description or "",
            priority=_map_priority(ticket.priority),
        )

    if "error" in result:
        raise HTTPException(status_code=502, detail=result)

    # Store ServiceNow sys_id reference in ticket
    if "result" in result and result["result"]:
        snow_record = result["result"]
        ticket.servicenow_sys_id = snow_record.get("sys_id")
        ticket.servicenow_number = snow_record.get("number")
        db.commit()

    return {
        "message": "Ticket synced to ServiceNow",
        "servicenow_record": result.get("result", result)
    }


def _map_priority(priority) -> str:
    """Map local priority to ServiceNow priority"""
    priority_map = {
        "critical": "1",
        "high": "2",
        "medium": "3",
        "low": "4",
    }
    if hasattr(priority, 'value'):
        return priority_map.get(priority.value, "3")
    return priority_map.get(str(priority).lower(), "3")


# ============================================================================
# AUTOMATED TICKET CREATION & WORKFLOW ENDPOINTS
# ============================================================================

from schemas import (
    AutoCreateTicketRequest,
    AutoCreateTicketResponse,
    SLABreachResponse,
    NotificationResponse,
    AssignmentGroupResponse,
)
from categorization import categorize_event, detect_priority
from assignment_rules import (
    assign_by_category,
    create_default_groups,
    create_default_category_mappings,
    list_available_groups,
    get_group_workload,
)
from sla import (
    create_ticket_sla,
    check_sla_breaches,
    get_slas_approaching_breach,
    get_ticket_sla_status,
    mark_response_met,
    mark_resolution_met,
    create_all_default_sla_definitions,
)
from notifications import (
    notify_ticket_created,
    notify_ticket_assigned,
    notify_sla_warning,
    notify_sla_breach,
    get_pending_notifications,
    process_pending_notifications,
)
from models import (
    AssignmentGroup,
    AssignmentGroupMember,
    CategoryAssignmentMapping,
    SLADefinition,
    TicketSLA,
    Notification as NotificationModel,
)


@app.post("/api/tickets/auto-create", response_model=AutoCreateTicketResponse)
async def auto_create_ticket(
    request: AutoCreateTicketRequest,
    db: Session = Depends(get_db)
):
    """
    Auto-create a ticket from a system event with categorization, assignment, and SLA.

    This endpoint:
    1. Creates a ticket with proper categorization
    2. Assigns to appropriate group/agent based on category
    3. Sets up SLA timers based on priority
    4. Sends notifications

    Called by MuleSoft when capturing system events.
    """
    import random

    try:
        # Find or create default user for system-created tickets
        default_user = db.query(User).filter(User.email == "admin@company.com").first()
        if not default_user:
            default_user = db.query(User).first()
        if not default_user:
            raise HTTPException(status_code=500, detail="No users in system")

        # Auto-categorize if needed
        category, subcategory = categorize_event(
            event_type=request.event_type,
            title=request.title,
            description=request.description or "",
            category=request.category,
            subcategory=request.subcategory
        )

        # Detect priority if not explicitly set
        priority = request.priority
        if not priority or priority == "medium":
            detected_priority = detect_priority(
                f"{request.title} {request.description or ''}",
                default_priority=request.priority or "medium"
            )
            priority = detected_priority

        # Generate ticket number
        ticket_number = f"TKT{random.randint(100000, 999999)}"

        # Create the ticket
        new_ticket = Ticket(
            ticket_number=ticket_number,
            title=request.title,
            description=request.description or "",
            ticket_type=request.ticket_type,
            status="submitted" if not request.requires_approval else "pending_approval",
            priority=priority,
            category=category,
            subcategory=subcategory,
            requester_id=default_user.id,
        )
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)

        # Assign to group and agent
        assignment_result = assign_by_category(
            db=db,
            ticket_id=new_ticket.id,
            category=category,
            subcategory=subcategory,
            fallback_group=request.assignment_group,
            auto_assign_agent=request.auto_assign
        )

        # Refresh ticket to get assignment
        db.refresh(new_ticket)

        # Create SLA timer
        ticket_sla = create_ticket_sla(
            db=db,
            ticket_id=new_ticket.id,
            priority=priority,
            category=category,
            created_at=new_ticket.created_at
        )

        # Send notifications
        await notify_ticket_created(
            db=db,
            ticket_id=new_ticket.id,
            event_id=request.event_id,
            callback_url=request.callback_url
        )

        if new_ticket.assigned_to_id:
            await notify_ticket_assigned(
                db=db,
                ticket_id=new_ticket.id,
                assigned_to_id=new_ticket.assigned_to_id,
                assignment_group=assignment_result.get("group_name")
            )

        return AutoCreateTicketResponse(
            ticket_id=new_ticket.id,
            ticket_number=new_ticket.ticket_number,
            title=new_ticket.title,
            category=category,
            subcategory=subcategory,
            priority=priority,
            status=new_ticket.status.value if hasattr(new_ticket.status, 'value') else str(new_ticket.status),
            assignment_group=assignment_result.get("group_name", request.assignment_group),
            assigned_to_id=assignment_result.get("assigned_to_id"),
            assigned_to_name=assignment_result.get("assigned_to_name"),
            sla_response_due=ticket_sla.response_due_at if ticket_sla else None,
            sla_resolution_due=ticket_sla.resolution_due_at if ticket_sla else None,
            created_at=new_ticket.created_at,
            event_id=request.event_id,
            message=f"Ticket created and assigned to {assignment_result.get('group_name', 'IT Service Desk')}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sla/check-breaches")
async def check_sla_breaches_endpoint(db: Session = Depends(get_db)):
    """
    Check all active SLAs for breaches and send notifications.

    Returns list of breached SLAs.
    """
    breaches = check_sla_breaches(db)

    # Send breach notifications
    for breach in breaches:
        if not breach.get("notified"):
            await notify_sla_breach(
                db=db,
                ticket_id=breach["ticket_id"],
                sla_type=breach["sla_type"],
                minutes_overdue=breach["minutes_overdue"]
            )

    return {
        "breaches": breaches,
        "count": len(breaches),
        "checked_at": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/sla/warnings")
async def get_sla_warnings(
    threshold: int = 80,
    db: Session = Depends(get_db)
):
    """
    Get SLAs approaching breach threshold.

    Args:
        threshold: Percentage threshold for warnings (default 80%)
    """
    warnings = get_slas_approaching_breach(db, threshold_percent=threshold)

    # Send warning notifications
    for warning in warnings:
        await notify_sla_warning(
            db=db,
            ticket_id=warning["ticket_id"],
            sla_type=warning["sla_type"],
            percent_elapsed=warning["percent_elapsed"],
            minutes_remaining=warning["minutes_remaining"]
        )

    return {
        "warnings": warnings,
        "count": len(warnings),
        "threshold_percent": threshold,
        "checked_at": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/sla/ticket/{ticket_id}")
async def get_ticket_sla(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get SLA status for a specific ticket."""
    sla_status = get_ticket_sla_status(db, ticket_id)

    if not sla_status:
        raise HTTPException(status_code=404, detail="No SLA found for this ticket")

    return sla_status


@app.post("/api/sla/ticket/{ticket_id}/response-met")
async def mark_ticket_response_met(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark the response SLA as met for a ticket."""
    sla = mark_response_met(db, ticket_id)

    if not sla:
        raise HTTPException(status_code=404, detail="No active SLA found for this ticket")

    return {
        "message": "Response SLA marked as met",
        "response_met_at": sla.response_met_at.isoformat() if sla.response_met_at else None,
        "response_breached": sla.response_breached == "true"
    }


@app.get("/api/notifications/pending")
async def get_pending_notifications_endpoint(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get pending notifications that need to be sent."""
    notifications = get_pending_notifications(db, limit=limit)

    return {
        "notifications": notifications,
        "count": len(notifications)
    }


@app.post("/api/notifications/process")
async def process_notifications(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Process and send pending notifications."""
    results = await process_pending_notifications(db, limit=limit)

    return results


@app.get("/api/assignment-groups")
async def list_assignment_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all active assignment groups."""
    groups = list_available_groups(db)
    return {"groups": groups, "count": len(groups)}


@app.get("/api/assignment-groups/{group_id}/workload")
async def get_assignment_group_workload(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workload statistics for an assignment group."""
    workload = get_group_workload(db, group_id)

    if "error" in workload:
        raise HTTPException(status_code=404, detail=workload["error"])

    return workload


@app.post("/api/setup/seed-assignment-data")
async def seed_assignment_data(db: Session = Depends(get_db)):
    """
    Seed default assignment groups, category mappings, and SLA definitions.

    Call this endpoint to initialize the system with default data.
    """
    try:
        # Create default assignment groups
        groups = create_default_groups(db)

        # Create default category mappings
        mappings = create_default_category_mappings(db)

        # Create default SLA definitions
        sla_defs = create_all_default_sla_definitions(db)

        return {
            "message": "Assignment data seeded successfully",
            "groups_created": len(groups),
            "mappings_created": len(mappings),
            "sla_definitions_created": len(sla_defs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sla/definitions")
async def list_sla_definitions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all SLA definitions."""
    definitions = db.query(SLADefinition).filter(
        SLADefinition.is_active == "true"
    ).all()

    return {
        "definitions": [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "priority": d.priority,
                "category": d.category,
                "response_time_minutes": d.response_time_minutes,
                "resolution_time_hours": d.resolution_time_hours,
                "business_hours_only": d.business_hours_only == "true",
                "warning_threshold_percent": d.warning_threshold_percent,
            }
            for d in definitions
        ],
        "count": len(definitions)
    }


# Webhook endpoint for MuleSoft SLA notifications
@app.post("/api/webhooks/sla-notification")
async def receive_sla_notification(
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint to receive SLA notifications from MuleSoft.

    This is mainly for testing/logging purposes.
    """
    print(f"Received SLA notification: {payload}")

    return {
        "received": True,
        "event_type": payload.get("event_type"),
        "ticket_number": payload.get("ticket_number"),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# Webhook endpoint for ticket notifications
@app.post("/api/webhooks/ticket-notification")
async def receive_ticket_notification(
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint to receive ticket notifications.

    This is mainly for testing/logging purposes.
    """
    print(f"Received ticket notification: {payload}")

    return {
        "received": True,
        "event_type": payload.get("event_type"),
        "ticket_number": payload.get("ticket_number"),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# =============================================================================
# PASSWORD RESET FLOW (ServiceNow → MuleSoft → SAP)
# =============================================================================

MULESOFT_PASSWORD_RESET_URL = os.getenv("MULESOFT_URL", "http://mulesoft-backend:4797")


class PasswordResetTicketCreate(BaseModel):
    """Schema for creating password reset ticket"""
    username: str
    user_email: Optional[str] = None
    reason: Optional[str] = None
    priority: str = "medium"


class PasswordResetTicketResponse(BaseModel):
    """Response for password reset ticket"""
    ticket_number: str
    correlation_id: str
    sap_ticket_id: Optional[str] = None
    username: str
    status: str
    message: str
    created_at: str


@app.post("/api/password-reset/submit", response_model=PasswordResetTicketResponse)
async def submit_password_reset_ticket(
    request: PasswordResetTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a password reset ticket.

    Flow:
    1. Creates a local ticket in ServiceNow
    2. Sends ticket to MuleSoft
    3. MuleSoft forwards to SAP
    4. Returns tracking info
    """
    import random

    # Create local ticket (audit only - auto-approved, no manual approval needed)
    ticket_number = f"PWD{random.randint(100000, 999999)}"

    db_ticket = Ticket(
        ticket_number=ticket_number,
        title=f"Password Reset: {request.username}",
        description=f"Password reset requested for user: {request.username}\nReason: {request.reason or 'User requested password reset'}\n\n[AUTO-APPROVED] This ticket is for audit purposes only and does not require manual approval.",
        ticket_type="service_request",
        priority=request.priority,
        category="User Account",
        subcategory="Password Reset",
        requester_id=current_user.id,
        status="in_progress"  # Skip approval workflow - go directly to in_progress
    )

    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)

    # Send to MuleSoft
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{MULESOFT_PASSWORD_RESET_URL}/api/password-reset/from-servicenow",
                json={
                    "servicenow_ticket_id": ticket_number,
                    "username": request.username,
                    "user_email": request.user_email,
                    "requester_name": current_user.full_name,
                    "requester_email": current_user.email,
                    "reason": request.reason,
                    "priority": request.priority,
                    "correlation_id": correlation_id
                }
            )

            if response.status_code in [200, 201]:
                result = response.json()

                # Update ticket with SAP info (keep in_progress - auto-approved)
                db_ticket.external_ticket_id = result.get("sap_ticket_id")
                # Status remains "in_progress" - waiting for SAP admin
                db.commit()

                return PasswordResetTicketResponse(
                    ticket_number=ticket_number,
                    correlation_id=result.get("correlation_id", ""),
                    sap_ticket_id=result.get("sap_ticket_id"),
                    username=request.username,
                    status="in_progress",
                    message="Password reset ticket sent to SAP. Awaiting admin action.",
                    created_at=datetime.utcnow().isoformat() + "Z"
                )
            else:
                db_ticket.status = "cancelled"  # Failed to send
                db_ticket.resolution_notes = f"Failed to send to MuleSoft: {response.text}"
                db.commit()
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to send ticket to MuleSoft: {response.text}"
                )

    except httpx.RequestError as e:
        db_ticket.status = "cancelled"  # Connection failed
        db_ticket.resolution_notes = f"Could not connect to MuleSoft: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to MuleSoft: {str(e)}"
        )


@app.patch("/api/tickets/{ticket_number}/status")
async def update_ticket_status_from_sap(
    ticket_number: str,
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Update ticket status (callback from MuleSoft/SAP).

    This endpoint is called by MuleSoft when SAP updates the ticket status.
    Creates a ticket record if it doesn't exist (for integration scenarios).
    """
    ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()

    # Map status from SAP/MuleSoft format
    status_mapping = {
        "completed": "resolved",
        "closed": "resolved",
        "failed": "failed",
        "in_progress": "in_progress",
        "open": "open"
    }

    new_status = payload.get("status", "").lower()
    mapped_status = status_mapping.get(new_status, new_status)

    if not ticket:
        # Create ticket for integration scenarios (ticket originated from external system)
        # Get system user for integration-created tickets
        system_user = db.query(User).filter(User.email == "admin@servicenow.com").first()
        if not system_user:
            system_user = db.query(User).first()

        ticket = Ticket(
            ticket_number=ticket_number,
            title=f"Password Reset (External): {ticket_number}",
            description=f"Password reset ticket created via integration.\nSource: {payload.get('source', 'sap_integration')}",
            ticket_type="service_request",
            priority="medium",
            category="User Account",
            subcategory="Password Reset",
            requester_id=system_user.id if system_user else 1,
            status=mapped_status
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        old_status = "new"
        print(f"Ticket {ticket_number} created via integration with status: {mapped_status}")
    else:
        old_status = ticket.status
        ticket.status = mapped_status
        ticket.updated_at = datetime.utcnow()

        if payload.get("resolution_notes"):
            ticket.resolution_notes = payload.get("resolution_notes")

        db.commit()
        print(f"Ticket {ticket_number} status updated: {old_status} → {ticket.status}")

    return {
        "ticket_number": ticket_number,
        "old_status": old_status,
        "new_status": ticket.status,
        "message": "Status updated successfully",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/password-reset/tickets")
async def list_password_reset_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List password reset tickets for current user."""
    tickets = db.query(Ticket).filter(
        Ticket.category == "User Account",
        Ticket.subcategory == "Password Reset",
        Ticket.requester_id == current_user.id
    ).order_by(Ticket.created_at.desc()).limit(50).all()

    return {
        "tickets": [
            {
                "ticket_number": t.ticket_number,
                "title": t.title,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None
            }
            for t in tickets
        ],
        "total": len(tickets)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)