# Salesforce Clone - Complete Application Guide

## 🎯 What is This Application?

This is a **Customer Relationship Management (CRM) system** - similar to Salesforce. It helps businesses manage:
- Customer relationships
- Sales pipeline
- Support tickets
- Service contracts
- Invoicing

---

## 🏗️ Application Architecture

### Frontend (React)
- **Location:** `/frontend/src`
- **Purpose:** User interface
- **Technology:** React 18, Tailwind CSS, React Router
- **Port:** `http://localhost:5173`

### Backend (FastAPI)
- **Location:** `/backend/app`
- **Purpose:** API & business logic
- **Technology:** FastAPI, SQLAlchemy, SQLite
- **Port:** `http://localhost:8000`

### Database (SQLite)
- **Location:** `/backend/data/app.db`
- **Purpose:** Store all data
- **Tables:** 14 tables (users, accounts, contacts, leads, etc.)

---

## 📊 Core Data Model

```
User (Admin/User)
├── Owns Accounts (Companies)
│   ├── Has Contacts (People)
│   ├── Has Opportunities (Deals)
│   ├── Has Cases (Support Tickets)
│   └── Has Service Accounts (Warranty/Support)
│       ├── Has SLAs (Support Terms)
│       ├── Has Quotations (Price Quotes)
│       ├── Has Invoices (Bills)
│       └── Has Warranty Extensions
├── Owns Leads (Sales Prospects)
│   └── Converts to Account + Contact + Opportunity
└── Owns Activities (Calls, Emails, Meetings)
```

---

## 🔄 How the Application Works

### 1. **Authentication**
```
User Login
  ↓
Enter: username (stalin) + password (password123)
  ↓
Backend validates credentials
  ↓
Returns JWT token
  ↓
Token stored in browser
  ↓
All API requests include token
```

### 2. **Main Dashboard (Home)**
Shows:
- Welcome message
- Key metrics (total accounts, leads, opportunities)
- Recent records
- Quick actions

### 3. **Accounts Management**
```
Create Account
  ↓
Enter: Name, Industry, Phone, Website
  ↓
Saved to database
  ↓
Can add Contacts to this Account
  ↓
Can create Opportunities for this Account
```

**Example:** UKPN (electricity company)
- Industry: Electricity Distribution
- Phone: +44-20-7066-5000
- Website: https://www.ukpowernetworks.co.uk

### 4. **Contacts Management**
```
Create Contact
  ↓
Enter: First Name, Last Name, Email, Phone, Title
  ↓
Link to Account (UKPN)
  ↓
Assign to owner (user)
  ↓
Can log activities (calls, emails)
```

**Example:** John Smith (Head of Sales at UKPN)

### 5. **Leads Management**
```
Create Lead
  ↓
Enter: Name, Company, Email, Phone, Score
  ↓
Auto-assign to sales rep (round-robin)
  ↓
Qualify or Disqualify
  ↓
Convert to Account + Contact + Opportunity
```

**Example:** Emma Wilson (Procurement Manager at UKPN)
- Score: 85 (high quality lead)
- Status: Qualified
- Convert → Creates Account, Contact, Opportunity

### 6. **Opportunities (Sales Pipeline)**
```
Create Opportunity
  ↓
Enter: Name, Amount, Stage, Probability
  ↓
Track through stages:
  - Prospecting
  - Qualification
  - Proposal
  - Negotiation
  - Closed Won/Lost
  ↓
Update probability as deal progresses
```

**Example:** "UKPN - Smart Meter Installation"
- Amount: £500,000
- Stage: Proposal
- Probability: 60%

### 7. **Cases (Support Tickets)**
```
Create Case
  ↓
Enter: Subject, Description, Priority, Status
  ↓
Auto-assign to support team
  ↓
Track SLA (response/resolution time)
  ↓
Auto-escalate if overdue
  ↓
Resolve/Close
```

**Example:** "Power Outage in Central London"
- Priority: Critical
- SLA: 4 hours response
- Status: Open

### 8. **Service Management**

#### Service Accounts
```
Create Service Account
  ↓
Link to Account (UKPN)
  ↓
Set warranty status (Active/Expired/Extended)
  ↓
Set service level (Gold/Silver/Bronze)
```

#### SLAs (Service Level Agreements)
```
Define support terms
  ↓
Response time: 4 hours
  ↓
Resolution time: 24 hours
  ↓
Uptime: 99.9%
```

#### Quotations
```
Create Quote
  ↓
Enter: Title, Amount, Tax
  ↓
Auto-generate quote number (QT-20260120...)
  ↓
Send to customer
  ↓
Track status (Draft/Sent/Accepted/Rejected)
```

#### Invoices
```
Create Invoice
  ↓
Enter: Description, Amount, Type (Standard/Proforma/Credit Note)
  ↓
Auto-generate invoice number (INV-20260120...)
  ↓
Track status (Draft/Sent/Paid/Overdue)
  ↓
Mark as Paid
```

#### Warranty Extensions
```
Extend warranty
  ↓
Enter: Start Date, End Date, Cost
  ↓
Track extension period
  ↓
Bill customer
```

---

## 🔐 User Roles

### Admin
- Full access to all features
- Can manage users
- Can view all records

### User
- Can create/edit own records
- Can view assigned records
- Limited to their sales territory

**Demo User:** `stalin / password123`

---

## 📝 Key Features

### 1. **Auto-Assignment**
- New leads auto-assigned to sales reps (round-robin)
- New cases auto-assigned to support team
- Based on availability and workload

### 2. **Lead Conversion**
```
Lead → Convert
  ↓
Creates:
  - Account (company)
  - Contact (person)
  - Opportunity (deal)
  ↓
All linked together
```

### 3. **SLA Tracking**
- Monitors case response/resolution times
- Auto-escalates overdue cases
- Tracks compliance

### 4. **Duplicate Detection**
- Warns when creating duplicate leads/contacts
- Checks by email and phone
- Prevents data duplication

### 5. **Activity Logging**
- Log calls, emails, meetings
- Attach to any record
- Track customer interactions

### 6. **Global Search**
- Search across all objects
- Quick navigation
- Real-time results

### 7. **Logging System**
- Every action logged to file
- Tracks user, action, timestamp
- Auto-rotates at 100MB
- Useful for auditing

---

## 🔄 Typical Sales Workflow

```
1. Lead Created
   ↓
2. Lead Auto-Assigned to Sales Rep
   ↓
3. Sales Rep Qualifies Lead
   ↓
4. Lead Converted to:
   - Account (UKPN)
   - Contact (John Smith)
   - Opportunity (£500K deal)
   ↓
5. Opportunity Moves Through Stages:
   - Prospecting → Qualification → Proposal → Negotiation → Closed Won
   ↓
6. Deal Won!
   ↓
7. Create Service Account
   ↓
8. Define SLA
   ↓
9. Send Quotation
   ↓
10. Create Invoice
   ↓
11. Track Warranty Extension
```

---

## 🔄 Typical Support Workflow

```
1. Customer Reports Issue
   ↓
2. Case Created
   ↓
3. Case Auto-Assigned to Support Rep
   ↓
4. SLA Timer Starts (4 hours for critical)
   ↓
5. Support Rep Works on Issue
   ↓
6. Case Status: Open → In Progress → Resolved → Closed
   ↓
7. If SLA Breached → Auto-Escalate
   ↓
8. Log Activity (calls, emails)
   ↓
9. Close Case
```

---

## 📊 Database Tables

| Table | Purpose |
|-------|---------|
| users | User accounts |
| accounts | Companies/Organizations |
| contacts | People at companies |
| leads | Sales prospects |
| opportunities | Deals in pipeline |
| cases | Support tickets |
| activities | Calls, emails, meetings |
| service_accounts | Warranty/support contracts |
| service_level_agreements | Support terms |
| quotations | Price quotes |
| invoices | Bills |
| warranty_extensions | Extended warranties |
| audit_logs | Change tracking |
| recent_records | User history |

---

## 🚀 API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register
- `GET /api/auth/me` - Current user

### Accounts
- `GET /api/accounts` - List
- `POST /api/accounts` - Create
- `PUT /api/accounts/{id}` - Update
- `DELETE /api/accounts/{id}` - Delete

### Contacts, Leads, Opportunities, Cases
- Similar CRUD endpoints

### Service Management
- `GET /api/service/accounts` - List service accounts
- `POST /api/service/accounts` - Create
- `GET /api/service/quotations` - List quotations
- `POST /api/service/quotations` - Create
- `GET /api/service/invoices` - List invoices
- `POST /api/service/invoices` - Create
- `GET /api/service/slas` - List SLAs
- `POST /api/service/slas` - Create
- `GET /api/service/warranty-extensions` - List extensions
- `POST /api/service/warranty-extensions` - Create

---

## 📱 Frontend Pages

| Page | Purpose |
|------|---------|
| Login | Authentication |
| Home | Dashboard & metrics |
| Accounts | Manage companies |
| Contacts | Manage people |
| Sales | Leads & opportunities |
| Service | Support cases |
| Service Management | Warranties, SLAs, invoices |
| Marketing | Marketing campaigns |
| Commerce | E-commerce features |
| Your Account | User settings |

---

## 🔍 Example: Complete Sales Cycle

### Step 1: Create Lead
```
Name: Emma Wilson
Company: UKPN
Email: emma@ukpn.co.uk
Score: 85
Status: New
```

### Step 2: Auto-Assigned
```
Assigned to: stalin (sales rep)
```

### Step 3: Qualify Lead
```
Status: Qualified
```

### Step 4: Convert Lead
```
Creates:
- Account: UKPN
- Contact: Emma Wilson
- Opportunity: Smart Meter Project (£500K)
```

### Step 5: Move Opportunity Through Pipeline
```
Stage: Prospecting → Qualification → Proposal → Negotiation → Closed Won
Amount: £500,000
Probability: 60% → 75% → 90% → 100%
```

### Step 6: Create Service Account
```
Account: UKPN
Service Level: Gold
Warranty: Active until 2027
```

### Step 7: Define SLA
```
Name: Premium Support
Response: 4 hours
Resolution: 24 hours
```

### Step 8: Send Quotation
```
Quote #: QT-20260120190000
Amount: £50,000 (warranty extension)
Status: Sent
```

### Step 9: Create Invoice
```
Invoice #: INV-20260120190000
Amount: £50,000
Type: Standard
Status: Sent
```

### Step 10: Track Warranty
```
Extension: 2027-01-20 to 2028-01-20
Cost: £5,000
Status: Active
```

---

## 💡 Key Concepts

### Lead Scoring
- Higher score = better quality lead
- 80+ = High priority
- Auto-assigned to top performers

### SLA Compliance
- Critical: 4 hours response
- High: 8 hours response
- Medium: 24 hours response
- Low: 48 hours response

### Service Levels
- **Gold:** Premium support, 24/7, 4-hour response
- **Silver:** Standard support, 9-5, 8-hour response
- **Bronze:** Basic support, 9-5, 24-hour response

### Invoice Types
- **Standard:** Regular invoice
- **Proforma:** Preliminary invoice (not final)
- **Credit Note:** Refund/adjustment

---

## 🎯 Summary

This CRM application helps businesses:

1. **Manage Customers** - Track accounts, contacts, relationships
2. **Track Sales** - Leads → Opportunities → Closed Won
3. **Support Customers** - Cases, SLAs, escalation
4. **Manage Services** - Warranties, quotations, invoices
5. **Automate Workflows** - Auto-assignment, SLA tracking, escalation
6. **Track Activities** - Calls, emails, meetings
7. **Generate Revenue** - Quotations, invoices, warranty extensions

**The goal:** Increase sales, improve customer satisfaction, and streamline operations!

---

## 🚀 Getting Started

1. **Login:** `stalin / password123`
2. **Create Account:** UKPN (electricity company)
3. **Add Contacts:** John Smith, Sarah Johnson, Michael Brown
4. **Create Leads:** Emma Wilson, David Taylor
5. **Convert Leads:** Create opportunities
6. **Create Cases:** Support tickets
7. **Manage Services:** Quotations, invoices, SLAs

**That's it! You're now using a full CRM system!**
