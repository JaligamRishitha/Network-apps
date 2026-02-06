# Detailed Workflow - Step by Step

## 🎯 Complete Sales & Service Workflow

---

## PHASE 1: INITIAL SETUP

### Step 1: Login to Application
```
URL: http://localhost:5173
Username: stalin
Password: password123
Click: Login
Result: Dashboard appears
```

### Step 2: View Dashboard
```
You see:
- Welcome message: "Welcome, Stalin"
- Key metrics (0 accounts, 0 leads, etc.)
- Recent records (empty)
- Quick action buttons
```

---

## PHASE 2: CREATE ACCOUNT (Company)

### Step 3: Navigate to Accounts
```
Left Sidebar → Click "Accounts"
Page shows: Empty list with "No records found"
Button: "+ New" (top right)
```

### Step 4: Create Account - UKPN
```
Click: "+ New" button
Form appears with fields:
  - Name: "UK Power Networks (UKPN)"
  - Industry: "Electricity Distribution"
  - Phone: "+44-20-7066-5000"
  - Website: "https://www.ukpowernetworks.co.uk"
  - Address: "Newington House, London, SE1 6SR"
  - Description: "Largest electricity distribution network in UK"

Click: "Save"
Result: Account created with ID = 1
```

### Step 5: View Created Account
```
Accounts list now shows:
  ID: 1
  Name: UK Power Networks (UKPN)
  Industry: Electricity Distribution
  Phone: +44-20-7066-5000
```

---

## PHASE 3: ADD CONTACTS (People at Company)

### Step 6: Navigate to Contacts
```
Left Sidebar → Click "Contacts"
Page shows: Empty list
Button: "+ New"
```

### Step 7: Create Contact 1 - John Smith
```
Click: "+ New"
Form appears:
  - First Name: "John"
  - Last Name: "Smith"
  - Title: "Head of Sales"
  - Email: "john.smith@ukpowernetworks.co.uk"
  - Phone: "+44-20-7066-5001"
  - Account: "UK Power Networks (UKPN)" (select from dropdown)

Click: "Save"
Result: Contact created with ID = 1
```

### Step 8: Create Contact 2 - Sarah Johnson
```
Click: "+ New"
Form appears:
  - First Name: "Sarah"
  - Last Name: "Johnson"
  - Title: "Operations Manager"
  - Email: "sarah.johnson@ukpowernetworks.co.uk"
  - Phone: "+44-20-7066-5002"
  - Account: "UK Power Networks (UKPN)"

Click: "Save"
Result: Contact created with ID = 2
```

### Step 9: Create Contact 3 - Michael Brown
```
Click: "+ New"
Form appears:
  - First Name: "Michael"
  - Last Name: "Brown"
  - Title: "IT Director"
  - Email: "michael.brown@ukpowernetworks.co.uk"
  - Phone: "+44-20-7066-5003"
  - Account: "UK Power Networks (UKPN)"

Click: "Save"
Result: Contact created with ID = 3
```

### Step 10: View Contacts List
```
Contacts now shows 3 records:
  1. John Smith - Head of Sales
  2. Sarah Johnson - Operations Manager
  3. Michael Brown - IT Director
```

---

## PHASE 4: CREATE LEADS (Sales Prospects)

### Step 11: Navigate to Sales
```
Left Sidebar → Click "Sales"
Shows: Leads tab (default)
Button: "+ New"
```

### Step 12: Create Lead 1 - Emma Wilson
```
Click: "+ New"
Form appears:
  - First Name: "Emma"
  - Last Name: "Wilson"
  - Company: "UKPN"
  - Title: "Procurement Manager"
  - Email: "emma.wilson@ukpowernetworks.co.uk"
  - Phone: "+44-20-7066-5004"
  - Status: "New"
  - Score: "85"
  - Source: "LinkedIn"
  - Region: "London"

Click: "Save"
Result: Lead created with ID = 1
Backend: Auto-assigns to "stalin" (round-robin)
```

### Step 13: Create Lead 2 - David Taylor
```
Click: "+ New"
Form appears:
  - First Name: "David"
  - Last Name: "Taylor"
  - Company: "UKPN"
  - Title: "Finance Manager"
  - Email: "david.taylor@ukpowernetworks.co.uk"
  - Phone: "+44-20-7066-5005"
  - Status: "New"
  - Score: "65"
  - Source: "Email Campaign"
  - Region: "Southeast"

Click: "Save"
Result: Lead created with ID = 2
Backend: Auto-assigns to "stalin"
```

### Step 14: View Leads List
```
Sales → Leads tab shows 2 records:
  1. Emma Wilson - Score: 85 - Status: New - Owner: stalin
  2. David Taylor - Score: 65 - Status: New - Owner: stalin
```

---

## PHASE 5: QUALIFY LEADS

### Step 15: Qualify Lead 1 - Emma Wilson
```
Click: Lead "Emma Wilson"
Detail page opens showing:
  - Name: Emma Wilson
  - Company: UKPN
  - Email: emma.wilson@ukpowernetworks.co.uk
  - Score: 85
  - Status: New

Click: "Edit" button
Form appears:
  - Status: Change from "New" to "Qualified"

Click: "Save"
Result: Lead status updated to "Qualified"
```

### Step 16: View Updated Lead
```
Lead now shows:
  - Status: Qualified
  - Score: 85 (high quality)
  - Ready for conversion
```

---

## PHASE 6: CONVERT LEAD TO ACCOUNT + CONTACT + OPPORTUNITY

### Step 17: Convert Lead - Emma Wilson
```
Click: Lead "Emma Wilson"
Detail page shows:
  - Button: "Convert Lead"

Click: "Convert Lead"
Conversion dialog appears:
  - Create Account: "UKPN" (already exists, link to existing)
  - Create Contact: "Emma Wilson" (auto-filled)
  - Create Opportunity: "UKPN - Procurement Project" (auto-filled)
  - Amount: "500000"

Click: "Convert"
Result: 
  - Account linked (ID = 1)
  - Contact created (ID = 4)
  - Opportunity created (ID = 1)
  - Lead marked as "Converted"
```

### Step 18: View Converted Records
```
Contacts list now shows 4 records:
  1. John Smith
  2. Sarah Johnson
  3. Michael Brown
  4. Emma Wilson (newly created from lead)

Sales → Opportunities tab shows 1 record:
  1. UKPN - Procurement Project
     - Amount: £500,000
     - Stage: Prospecting
     - Probability: 50%
```

---

## PHASE 7: MOVE OPPORTUNITY THROUGH SALES PIPELINE

### Step 19: Update Opportunity - Stage 1 (Prospecting)
```
Click: Opportunity "UKPN - Procurement Project"
Detail page shows:
  - Name: UKPN - Procurement Project
  - Amount: £500,000
  - Stage: Prospecting
  - Probability: 50%

Click: "Edit"
Form appears:
  - Stage: Change to "Qualification"
  - Probability: Change to "60%"

Click: "Save"
Result: Opportunity updated
```

### Step 20: Update Opportunity - Stage 2 (Qualification)
```
Click: Edit again
Form appears:
  - Stage: Change to "Proposal"
  - Probability: Change to "75%"

Click: "Save"
Result: Opportunity updated
```

### Step 21: Update Opportunity - Stage 3 (Proposal)
```
Click: Edit again
Form appears:
  - Stage: Change to "Negotiation"
  - Probability: Change to "85%"

Click: "Save"
Result: Opportunity updated
```

### Step 22: Update Opportunity - Stage 4 (Negotiation)
```
Click: Edit again
Form appears:
  - Stage: Change to "Closed Won"
  - Probability: Change to "100%"

Click: "Save"
Result: Opportunity marked as "Closed Won"
```

### Step 23: View Final Opportunity
```
Opportunity now shows:
  - Stage: Closed Won ✅
  - Probability: 100%
  - Amount: £500,000
  - Status: Deal won!
```

---

## PHASE 8: CREATE SERVICE ACCOUNT (Warranty/Support)

### Step 24: Navigate to Service Management
```
Left Sidebar → Click "Service Mgmt"
Shows: Quotations tab (default)
Tabs available:
  - Quotations
  - Invoices
  - Service Accounts
  - Warranty Extensions
  - SLAs
```

### Step 25: Create Service Account
```
Click: "Service Accounts" tab
Shows: Empty list
Click: "+ New"

Form appears:
  - Account ID: "1" (UKPN)
  - Warranty Status: "Active"
  - Service Level: "Gold"

Click: "Create"
Result: Service Account created with ID = 1
```

### Step 26: View Service Account
```
Service Accounts tab shows 1 record:
  ID: 1
  Account: 1 (UKPN)
  Service Level: Gold
  Warranty Status: Active
```

---

## PHASE 9: DEFINE SERVICE LEVEL AGREEMENT (SLA)

### Step 27: Create SLA - Premium Support
```
Click: "SLAs" tab
Shows: Empty list
Click: "+ New"

Form appears:
  - Service Account ID: "1"
  - SLA Name: "Premium Support"
  - Response Time: "4" (hours)
  - Resolution Time: "24" (hours)
  - Uptime: "99.9%"
  - Support Hours: "24/7"

Click: "Create"
Result: SLA created with ID = 1
```

### Step 28: View SLA
```
SLAs tab shows 1 record:
  ID: 1
  Name: Premium Support
  Response Time: 4 hours
  Resolution Time: 24 hours
```

---

## PHASE 10: CREATE QUOTATION (Price Quote)

### Step 29: Create Quotation
```
Click: "Quotations" tab
Shows: Empty list
Click: "+ New"

Form appears:
  - Account ID: "1" (UKPN)
  - Title: "Smart Meter Installation Project"
  - Amount: "500000"
  - Tax Amount: "100000"

Click: "Create"
Result: Quotation created
  - Quote #: QT-20260120190000 (auto-generated)
  - Total: £600,000 (500K + 100K tax)
  - Status: Draft
```

### Step 30: View Quotation
```
Quotations tab shows 1 record:
  Quote #: QT-20260120190000
  Amount: £500,000
  Tax: £100,000
  Total: £600,000
  Status: Draft
```

---

## PHASE 11: CREATE INVOICE (Bill Customer)

### Step 31: Create Invoice - Standard
```
Click: "Invoices" tab
Shows: Empty list
Click: "+ New"

Form appears:
  - Account ID: "1" (UKPN)
  - Description: "Smart Meter Installation - Year 1"
  - Type: "Standard"
  - Amount: "500000"
  - Tax Amount: "100000"

Click: "Create"
Result: Invoice created
  - Invoice #: INV-20260120190000 (auto-generated)
  - Total: £600,000
  - Status: Draft
```

### Step 32: View Invoice
```
Invoices tab shows 1 record:
  Invoice #: INV-20260120190000
  Amount: £500,000
  Tax: £100,000
  Total: £600,000
  Status: Draft
```

---

## PHASE 12: CREATE WARRANTY EXTENSION

### Step 33: Create Warranty Extension
```
Click: "Warranty Extensions" tab
Shows: Empty list
Click: "+ New"

Form appears:
  - Service Account ID: "1"
  - Start Date: "2026-01-20"
  - End Date: "2027-01-20"
  - Cost: "5000"

Click: "Create"
Result: Warranty Extension created
  - Period: 2026-01-20 to 2027-01-20 (1 year)
  - Cost: £5,000
  - Status: Active
```

### Step 34: View Warranty Extension
```
Warranty Extensions tab shows 1 record:
  Service Account: 1
  Start Date: 2026-01-20
  End Date: 2027-01-20
  Cost: £5,000
  Status: Active
```

---

## PHASE 13: CREATE SUPPORT CASE

### Step 35: Navigate to Service (Cases)
```
Left Sidebar → Click "Service"
Shows: Cases list (empty)
Button: "+ New"
```

### Step 36: Create Case - Critical Issue
```
Click: "+ New"
Form appears:
  - Subject: "Power Outage in Central London"
  - Description: "Customers reporting power outages in central London area"
  - Priority: "Critical"
  - Status: "Open"
  - Account: "UK Power Networks (UKPN)"
  - Contact: "John Smith"

Click: "Save"
Result: Case created
  - Case #: CS-20260120190000 (auto-generated)
  - Status: Open
  - Priority: Critical
  - SLA: 4 hours (from Premium Support SLA)
  - Auto-assigned to: stalin
```

### Step 37: View Case
```
Cases list shows 1 record:
  Case #: CS-20260120190000
  Subject: Power Outage in Central London
  Priority: Critical
  Status: Open
  Owner: stalin
```

---

## PHASE 14: WORK ON CASE

### Step 38: Update Case Status
```
Click: Case "CS-20260120190000"
Detail page shows:
  - Subject: Power Outage in Central London
  - Status: Open
  - Priority: Critical
  - SLA Due: 4 hours from creation

Click: "Edit"
Form appears:
  - Status: Change from "Open" to "In Progress"

Click: "Save"
Result: Case status updated
```

### Step 39: Log Activity on Case
```
Click: Case detail
Shows: Activity section
Click: "Add Activity"

Form appears:
  - Activity Type: "Call"
  - Subject: "Spoke with John Smith"
  - Details: "Discussed outage, investigating root cause"

Click: "Save"
Result: Activity logged
```

### Step 40: Resolve Case
```
Click: "Edit"
Form appears:
  - Status: Change from "In Progress" to "Resolved"

Click: "Save"
Result: Case marked as Resolved
```

---

## PHASE 15: VIEW DASHBOARD

### Step 41: Return to Dashboard
```
Left Sidebar → Click "Home"
Dashboard now shows:
  - Total Accounts: 1 (UKPN)
  - Total Contacts: 4 (John, Sarah, Michael, Emma)
  - Total Leads: 2 (Emma, David)
  - Total Opportunities: 1 (£500K deal - Closed Won)
  - Total Cases: 1 (Power Outage - Resolved)
  - Recent Records: All created records listed
```

---

## 📊 COMPLETE WORKFLOW SUMMARY

```
1. LOGIN
   ↓
2. CREATE ACCOUNT (UKPN)
   ↓
3. ADD CONTACTS (John, Sarah, Michael)
   ↓
4. CREATE LEADS (Emma, David)
   ↓
5. QUALIFY LEAD (Emma → Qualified)
   ↓
6. CONVERT LEAD (Emma → Account + Contact + Opportunity)
   ↓
7. MOVE OPPORTUNITY THROUGH PIPELINE
   Prospecting (50%) → Qualification (60%) → Proposal (75%) → 
   Negotiation (85%) → Closed Won (100%)
   ↓
8. CREATE SERVICE ACCOUNT (Gold level)
   ↓
9. DEFINE SLA (Premium Support - 4hr response)
   ↓
10. CREATE QUOTATION (£600K with tax)
   ↓
11. CREATE INVOICE (£600K bill)
   ↓
12. CREATE WARRANTY EXTENSION (1 year)
   ↓
13. CREATE CASE (Power Outage - Critical)
   ↓
14. WORK ON CASE (Log activity, update status)
   ↓
15. RESOLVE CASE
   ↓
16. VIEW DASHBOARD (All metrics updated)
```

---

## 💰 FINANCIAL SUMMARY

```
Deal Value: £500,000
Tax: £100,000
Total Invoice: £600,000
Warranty Extension: £5,000
Total Revenue: £605,000
```

---

## ⏱️ SLA TRACKING

```
Case Created: 2026-01-20 19:40:00
SLA Level: Critical (4 hours)
SLA Due: 2026-01-20 23:40:00
Status: Open → In Progress → Resolved
Result: SLA Met ✅
```

---

## 🎯 KEY METRICS

```
Accounts: 1
Contacts: 4
Leads: 2 (1 converted, 1 active)
Opportunities: 1 (Closed Won)
Cases: 1 (Resolved)
Revenue: £605,000
SLA Compliance: 100%
```

---

## ✅ WORKFLOW COMPLETE!

You've successfully:
- ✅ Created a company account
- ✅ Added team members (contacts)
- ✅ Identified sales prospects (leads)
- ✅ Converted leads to opportunities
- ✅ Closed a £500K deal
- ✅ Set up warranty and support
- ✅ Created quotations and invoices
- ✅ Handled customer support case
- ✅ Tracked SLA compliance

**This is how a real CRM works!**
