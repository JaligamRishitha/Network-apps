# Salesforce Clone

A full-stack Salesforce-like CRM application built with React (frontend) and FastAPI (backend).

## Features

### Core Objects
- **Contacts**: Manage customer contacts with account relationships
- **Accounts**: Track organizations and companies
- **Leads**: Capture and qualify potential customers with auto-assignment
- **Opportunities**: Track deals through sales pipeline
- **Cases**: Handle customer support tickets with SLA tracking

### Key Functionality
- **Dashboard**: Home page with personalized cards and recent records
- **List Views**: Sortable, searchable tables with pagination
- **Global Search**: Search across all objects from the top bar
- **Record Forms**: Create/edit modals with validation
- **Lead Conversion**: Convert leads to accounts, contacts, and opportunities
- **Case Escalation**: Automatic SLA tracking and escalation
- **Assignment Rules**: Auto-assign leads and cases to users
- **Activity Tracking**: Log activities against records
- **To-Do List**: Bottom tray task manager

### Pages
- Home (Dashboard)
- Contacts
- Accounts
- Sales (Leads, Opportunities, etc.)
- Service (Cases)
- Marketing
- Commerce
- Generative Canvas (gated feature)
- Your Account

## Tech Stack

### Frontend
- React 18 with Vite
- React Router for navigation
- Tailwind CSS for styling
- Axios for API calls
- React Hot Toast for notifications
- Heroicons for icons

### Backend
- FastAPI (Python)
- SQLAlchemy ORM
- SQLite database
- JWT authentication
- Pydantic for validation

## Project Structure

```
salesforce/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/           # Page components
│   │   ├── context/         # React context providers
│   │   ├── services/        # API services
│   │   └── App.jsx          # Main app with routing
│   ├── package.json
│   └── Dockerfile
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── routes/          # API routes per object
│   │   ├── main.py          # FastAPI app entry
│   │   ├── db_models.py     # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── crud.py          # Database operations
│   │   ├── services.py      # Business logic
│   │   ├── auth.py          # Authentication
│   │   └── database.py      # DB configuration
│   ├── seed.py              # Demo data seeder
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites
- Node.js 18+ (frontend)
- Python 3.10+ (backend)
- Docker & Docker Compose (optional)

### Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed the database with demo data
python seed.py

# Start the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000
- API docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:5173

### Production Deployment with Docker

```bash
# Build and start all services
docker-compose up -d --build

# Seed the database (first time only)
docker-compose --profile seed up seed

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at:
- Frontend: http://localhost
- Backend API: http://localhost:8000

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/register` - Register new user
- `GET /api/auth/me` - Get current user
- `GET /api/auth/users` - List all users

### Contacts
- `GET /api/contacts` - List contacts
- `GET /api/contacts/{id}` - Get contact
- `POST /api/contacts` - Create contact
- `PUT /api/contacts/{id}` - Update contact
- `DELETE /api/contacts/{id}` - Delete contact

### Accounts
- `GET /api/accounts` - List accounts
- `GET /api/accounts/{id}` - Get account
- `POST /api/accounts` - Create account
- `PUT /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Delete account

### Leads
- `GET /api/leads` - List leads
- `GET /api/leads/{id}` - Get lead
- `POST /api/leads` - Create lead (with auto-assignment)
- `PUT /api/leads/{id}` - Update lead
- `DELETE /api/leads/{id}` - Delete lead
- `POST /api/leads/{id}/convert` - Convert lead to account/contact/opportunity

### Opportunities
- `GET /api/opportunities` - List opportunities
- `GET /api/opportunities/{id}` - Get opportunity
- `POST /api/opportunities` - Create opportunity
- `PUT /api/opportunities/{id}` - Update opportunity
- `DELETE /api/opportunities/{id}` - Delete opportunity

### Cases
- `GET /api/cases` - List cases
- `GET /api/cases/{id}` - Get case
- `POST /api/cases` - Create case (with auto-assignment)
- `PUT /api/cases/{id}` - Update case
- `DELETE /api/cases/{id}` - Delete case
- `POST /api/cases/{id}/escalate` - Escalate case
- `POST /api/cases/merge` - Merge duplicate cases

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/recent-records` - Get recent records
- `GET /api/dashboard/search` - Global search

## Demo Credentials

After running the seed script:

| Username | Password     | Role  |
|----------|--------------|-------|
| admin    | admin123     | Admin |
| stalin   | password123  | User  |
| sarah    | password123  | User  |
| mike     | password123  | User  |

## Business Logic

### Lead Assignment Rules
- High score leads (>= 80) are assigned to top performers
- Default: Round-robin assignment among active users

### Lead Conversion
Creates linked Account, Contact, and Opportunity records from a lead.

### Case SLA
- Critical: 4 hours
- High: 8 hours
- Medium: 24 hours
- Low: 48 hours

Cases are automatically flagged for escalation when SLA is breached.

## Environment Variables

### Backend
- `DATABASE_URL` - SQLite connection string (default: `sqlite:///./data/app.db`)
- `SECRET_KEY` - JWT signing key (change in production!)

### Frontend
- `VITE_API_URL` - Backend API URL (default: `http://localhost:8000`)

## Component Mapping

| Screenshot Element | Component | Route |
|-------------------|-----------|-------|
| Left Nav | `LeftNav.jsx` | N/A |
| Top Bar | `TopBar.jsx` | N/A |
| Home Dashboard | `Home.jsx` | `/home` |
| Dashboard Cards | `DashboardCard.jsx` | N/A |
| Contact List | `Contacts.jsx` | `/contacts` |
| Account List | `Accounts.jsx` | `/accounts` |
| Sales (Leads) | `Sales.jsx` | `/sales` |
| Service (Cases) | `Service.jsx` | `/service` |
| Marketing | `Marketing.jsx` | `/marketing` |
| Commerce | `Commerce.jsx` | `/commerce` |
| Generative Canvas | `GenerativeCanvas.jsx` | `/generative` |
| Your Account | `YourAccount.jsx` | `/account` |
| Record Form | `RecordFormModal.jsx` | N/A |
| Empty State | `EmptyState.jsx` | N/A |

## License

MIT License
